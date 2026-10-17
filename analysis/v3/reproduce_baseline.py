"""仅执行T0：从锁定原始数据重建和重拟合已有基线，不执行T1–T7。"""
from __future__ import annotations

from collections import defaultdict
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback

import numpy as np
import pandas as pd
from scipy.special import expit

ROOT=Path(__file__).resolve().parents[2]
S2=ROOT/'analysis/supplementary_s2'
OUT=ROOT/'results/baseline'
SEED=20261016
BOOTSTRAP_REPLICATES=5000
LOSS_TOLERANCE=1e-4
INTERVAL_TOLERANCE=2e-3
sys.path.insert(0,str(ROOT/'analysis'))
sys.path.insert(0,str(S2))
sys.dont_write_bytecode=True

import audit
import analyze
import partition_analysis as partition
import run_s2 as s2_pure
from s2_models import MODELS,COMPARISONS,build_design,fit_aggregated,logloss
from design_rank import M4_COLUMNS


def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')


def source_manifest():
    paths=[p for p in (ROOT/'analysis').rglob('*') if p.is_file() and 'v3' not in p.relative_to(ROOT/'analysis').parts and '__pycache__' not in p.parts]
    paths += [p for p in (ROOT/'data').rglob('*') if p.is_file()]
    return {str(p.relative_to(ROOT)):{'sha256':digest(p),'mtime_ns':p.stat().st_mtime_ns} for p in sorted(paths)}


def record_run(status,metrics,commit):
    path=ROOT/'results/run_log.csv';path.parent.mkdir(parents=True,exist_ok=True)
    columns=['time','task','spec','metrics','commit']
    exists=path.exists()
    with path.open('a',encoding='utf-8',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=columns)
        if not exists:writer.writeheader()
        writer.writerow({'time':now(),'task':'T0','spec':json.dumps({'scope':'仅基线复现','seed':SEED,'folds':'沿用冻结分折','weighting':'已有谱系等权训练及评分','estimator':'已有MLE/Firth实现','status':status},ensure_ascii=False),
                         'metrics':json.dumps(metrics,ensure_ascii=False),'commit':commit})


def check_row(rows,label,paper,recomputed,old_exact=None,tolerance=0.0,round_percent=False):
    difference=float(recomputed)-float(paper)
    passed=round(100*float(recomputed),1)==round(100*float(paper),1) if round_percent else abs(difference)<=tolerance
    row={'label':label,'paper_value':paper,'recomputed_value':recomputed,'difference_from_paper':difference,
         'old_exact_value':old_exact,'difference_from_old_exact':None if old_exact is None else float(recomputed)-float(old_exact),
         'tolerance':tolerance,'comparison':'按一位百分数核对显示值' if round_percent else '绝对差', 'passed':bool(passed)}
    rows.append(row)
    if not passed:raise RuntimeError('T0差异：'+json.dumps(row,ensure_ascii=False))


def reconstruct():
    raw,sibling,valid,available,selected,glot=audit.load_data()
    chosen=valid[valid.Language_ID.isin(selected.ID)].copy()
    pairs,categories=analyze.gen_pairs(chosen,selected)
    old=pd.read_csv(ROOT/'analysis/pairs_primary.csv',keep_default_na=False,dtype={'pattern':str})
    key=['Language_ID','category_a','category_b']
    joined=pairs.merge(old,on=key,suffixes=('_new','_old'),validate='one_to_one')
    if len(joined)!=len(pairs) or len(joined)!=len(old):raise RuntimeError('原始重建配对的覆盖与冻结表不一致。')
    for c in ['Glottocode','family_group','shared_form','Dr','Da','De','Drelative','pattern']:
        if not joined[c+'_new'].eq(joined[c+'_old']).all():raise RuntimeError('原始重建不一致列：'+c)
    metadata={}
    for lid,frame in pairs.groupby('Language_ID',sort=False):
        first=frame.iloc[0]
        metadata[lid]={c:first[c] for c in ['Language_ID','Glottocode','Name','family_group','family_name','family_status','Macroarea']}
        metadata[lid]['macroarea_raw']=first.Macroarea
        metadata[lid]['macroarea']=first.Macroarea.split(';')[0].strip() or 'Unknown'
    forms=defaultdict(dict)
    for row in categories.itertuples(index=False):forms[row.Language_ID][row.Parameter_ID]=tuple(sorted(set(json.loads(row.forms_json))))
    raw_records=defaultdict(list)
    for row in chosen[chosen.Language_ID.isin(metadata)].itertuples(index=False):
        raw_records[row.Language_ID].append({c:getattr(row,c) for c in ['ID','Language_ID','Parameter_ID','Value','Form','Comment','Source']})
    systems,catalogue=partition.prepare_systems(forms,metadata,raw_records)
    return pairs,systems,catalogue


def bootstrap_fixed_scores(scores):
    cols=['gain_'+a+'_'+b for a,b in COMPARISONS]
    means=scores.groupby('family_group')[cols].mean()
    idx=np.random.default_rng(SEED).integers(0,len(means),size=(BOOTSTRAP_REPLICATES,len(means)))
    result={}
    for a,b in COMPARISONS:
        values=means['gain_'+a+'_'+b].to_numpy();draws=values[idx].mean(axis=1)
        result[a+'-'+b]={'gain':float(values.mean()),'family_cluster_bootstrap_95ci':np.quantile(draws,[.025,.975]).tolist()}
    return result


def reproduce_models(pairs):
    frame=pairs.copy()
    frame['Macroarea_first']=frame.Macroarea.str.split(';').str[0].str.strip()
    frame['pair_type']=frame.category_a+'|'+frame.category_b
    pair_types=sorted(frame.pair_type.unique())
    lookup={k:i for i,k in enumerate(pair_types)}
    frame['pair_index']=frame.pair_type.map(lookup)
    designs={m:build_design(pair_types,m) for m in MODELS}
    old_folds=pd.read_csv(ROOT/'analysis/oof_predictions.csv',usecols=['variant','cv_grouping','Language_ID','category_a','category_b','fold'])
    old_folds=old_folds[old_folds.variant.eq('primary')&old_folds.cv_grouping.eq('family')]
    frame=frame.merge(old_folds[['Language_ID','category_a','category_b','fold']],on=['Language_ID','category_a','category_b'],validate='one_to_one',sort=False)
    if not frame.groupby('family_group').fold.nunique().eq(1).all():raise RuntimeError('旧语系分折不满足隔离。')
    all_scores=[];fits=[];results={}
    for validation in ['family','area']:
        data=frame[frame.Macroarea_first.ne('')].reset_index(drop=True) if validation=='area' else frame.copy().reset_index(drop=True)
        folds=sorted(data.Macroarea_first.unique()) if validation=='area' else sorted(data.fold.unique())
        predictions=np.full((len(data),5),np.nan)
        for fold in folds:
            mask=data.Macroarea_first.eq(fold).to_numpy() if validation=='area' else data.fold.eq(fold).to_numpy()
            train=data.loc[~mask];test=data.loc[mask]
            group='Macroarea_first' if validation=='area' else 'family_group'
            if set(train[group])&set(test[group]):raise RuntimeError('留出分组泄漏。')
            weights=s2_pure.row_weights(train,'family')
            itr=train.pair_index.to_numpy();ite=test.pair_index.to_numpy()
            total=np.bincount(itr,weights=weights,minlength=28)
            success=np.bincount(itr,weights=weights*train.shared_form.to_numpy(),minlength=28)
            for j,model in enumerate(MODELS):
                beta,diagnostics=fit_aggregated(designs[model],success,total)
                fits.append({'validation':validation,'fold':str(fold),'model':model,'train_systems':int(train.Glottocode.nunique()),'test_systems':int(test.Glottocode.nunique()),'coefficients':beta.tolist(),**diagnostics})
                if not diagnostics['converged']:raise RuntimeError('T0拟合未收敛，不进入推断。')
                predictions[test.index,j]=expit(designs[model][ite]@beta)
        if not np.isfinite(predictions).all():raise RuntimeError('基线预测缺失。')
        scores=data[['Glottocode','Language_ID','family_group','family_name','Macroarea_first']].copy()
        for j,model in enumerate(MODELS):scores['loss_'+model]=logloss(data.shared_form.to_numpy(),predictions[:,j])
        scores=scores.groupby(['Glottocode','Language_ID','family_group','family_name','Macroarea_first'],as_index=False).mean()
        for a,b in COMPARISONS:scores['gain_'+a+'_'+b]=scores['loss_'+a]-scores['loss_'+b]
        results[validation]={'systems':len(scores),'families':int(scores.family_group.nunique()),'pairs':len(data),
                             'logloss':{m:s2_pure.score_value(scores,'loss_'+m,'family') for m in MODELS},
                             'comparisons':bootstrap_fixed_scores(scores),'folds':[str(f) for f in folds]}
        scores.insert(0,'validation',validation);all_scores.append(scores)
    weights=s2_pure.row_weights(frame,'family');idx=frame.pair_index.to_numpy()
    total=np.bincount(idx,weights=weights,minlength=28);success=np.bincount(idx,weights=weights*frame.shared_form.to_numpy(),minlength=28)
    beta,diag=fit_aggregated(designs['M4'],success,total)
    if not diag['converged']:raise RuntimeError('全样本主M4未收敛。')
    coefficients=dict(zip(M4_COLUMNS,map(float,beta)))
    pd.concat(all_scores,ignore_index=True).to_csv(OUT/'recomputed_language_scores.csv',index=False)
    return results,coefficients,diag,fits


def report(result):
    lines=['# T0基线复现报告','',
           '本次只复现任务书T0所列既有数字，不执行T1–T7。主样本从锁定原始数据重新完成有效词形、来源ID选择、谱系连接和无序配对，严格划分及方向沿用原结构函数，预测与系数实际重新拟合。未调用会覆写旧输出的分析入口。','',
           f'运行提交：`{result["commit"]}`；全局种子：{SEED}；固定预测自助重抽{BOOTSTRAP_REPLICATES}次。训练与评分沿用谱系组等权，语系折逐对取旧冻结折；地域留出排除原有30个地域缺失系统。','',
           '| 数字／对象 | 任务书／论文值 | 数据复算值 | 差值 | 原JSON精确值 | 与原精确值差 | 判定 |',
           '|---|---:|---:|---:|---:|---:|---|']
    for r in result['checks']:
        fmt=lambda x:'—' if x is None else format(x,'.12g')
        lines.append('| '+ ' | '.join([r['label'],fmt(r['paper_value']),fmt(r['recomputed_value']),fmt(r['difference_from_paper']),fmt(r['old_exact_value']),fmt(r['difference_from_old_exact']),'通过' if r['passed'] else '不一致'])+' |')
    lines+=['','计数要求精确一致；对数损失及表4四位系数以1e-4容差核对，另给原JSON未四舍五入值以区分显示精度。3.5%／2.8%按论文一位百分数核对，不将正常四舍五入当作改动定义。','',
            '## 固定折外预测区间的附加数值核查','',
            '只使用本次重新拟合得到的折外预测；谱系等权整群重抽5000次。任务书指定新种子20261016，旧S2使用20261014，因此区间端点允许2e-3差异。此处不重新拟合5000次系数自助，也不声称已复现未列入T0数值清单的系数区间。','',
            '| 验证 | 比较 | 旧95%区间 | 新种子复算95%区间 | 端点最大差 | 判定 |','|---|---|---|---|---:|---|']
    for r in result.get('interval_checks',[]):
        lines.append(f'| {r["validation"]} | {r["comparison"]} | {r["old_interval"]} | {r["recomputed_interval"]} | {r["max_absolute_difference"]:.8g} | {"通过" if r["passed"] else "不一致"} |')
    lines+=['','## 文件与结果保护','',
            f'既有分析和数据的保护清单含{result["source_protection"]["file_count"]}个文件；内容与mtime的运行前后差异：{result["source_protection"]["changed_files"]}。',
            '', '中间文件：`reproduction_results.json`、`recomputed_strict_systems.json`、`recomputed_model_fits.json`、`recomputed_language_scores.csv`。每次运行另追加`results/run_log.csv`，包括失败或中止。',
            '', '**总体判定：'+('T0所列数字全部通过；没有未解释差异。' if result.get('passed') else '存在差异或未完成项；必须向作者报告，不能继续新增任务。')+'**','']
    if result.get('error'):lines+=['运行错误：`'+result['error']+'`','']
    (OUT/'reproduction_report.md').write_text('\n'.join(lines),encoding='utf-8')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    before=source_manifest();result={'task':'T0','started_utc':now(),'commit':commit,'seed':SEED,'checks':[],'passed':False}
    rows=result['checks'];status='failed'
    try:
        pairs,systems,catalogue=reconstruct()
        oldp=json.loads((S2/'partition_results.json').read_text())
        oldm=json.loads((S2/'prediction_results.json').read_text())
        oldu=json.loads((S2/'uncertainty_results.json').read_text())
        for label,expected,value in [('主样本系统数',939,pairs.Glottocode.nunique()),('主样本谱系组',125,pairs.family_group.nunique()),('无序类别对',26292,len(pairs)),('严格划分系统',625,len(systems)),('严格划分谱系组',108,len({s['family_group'] for s in systems}))]:check_row(rows,label,expected,int(value),expected)
        records=[]
        for s in systems:
            d=catalogue[s['structure_key']]
            records.append({k:s[k] for k in ['Language_ID','Glottocode','family_group','macroarea','structure_key']}|{'indicators':d['indicators'],'strict_directions':d['strict_directions'],'partition_masks':d['partition_masks']})
        write_json(OUT/'recomputed_strict_systems.json',records)
        for name,expected in [('three',163),('four',22),('six',21)]:
            values=np.array([not catalogue[s['structure_key']]['indicators']['A_'+name] for s in systems],dtype=float)
            check_row(rows,'非合取系统：'+name,expected,int(values.sum()),oldp['P1']['A_'+name]['subsets']['overall']['violating_systems'])
            if name=='four':
                family=pd.DataFrame({'family':[s['family_group'] for s in systems],'violation':values}).groupby('family').violation.mean()
                check_row(rows,'四特征非合取比例（系统）',.035,float(values.mean()),.0352,round_percent=True)
                check_row(rows,'四特征非合取比例（谱系等权）',.028,float(family.mean()),oldp['P1']['A_four']['subsets']['overall']['baselines']['uniform_all_partitions']['family_equal']['observed_violation_rate'],round_percent=True)
        result['directions']={}
        expected_directions={'P2':(51,6,21,3),'P3':(17,5,11,3),'P4':(81,1,17,1)}
        names=['systems_predicted','systems_opposite','families_predicted_majority','families_opposite_majority']
        for prediction,expected in expected_directions.items():
            summary=partition.direction_summary(systems,catalogue,prediction,'strict_direction')
            result['directions'][prediction]=summary
            for field,target in zip(names,expected):check_row(rows,prediction+' '+field,target,summary[field],oldp['P2_P4'][prediction]['strict_direction']['overall'][field])
        models,coefficients,full_diagnostic,fits=reproduce_models(pairs)
        result['recomputed_models']=models;result['full_M4_coefficients']=coefficients;result['full_M4_diagnostics']=full_diagnostic
        write_json(OUT/'recomputed_model_fits.json',fits)
        expectations={'family':[.5088,.5020,.4961,.4944,.4943],'area':[.5326,.5410,.5400,.5407,.5405]}
        for validation,targets in expectations.items():
            previous=oldm['settings']['D1_MLE_family_'+validation]
            check_row(rows,validation+' 验证系统数',939 if validation=='family' else 909,models[validation]['systems'],previous['systems'])
            for m,target in zip(MODELS,targets):check_row(rows,validation+' '+m+' log loss',target,models[validation]['logloss'][m],previous['logloss'][m],LOSS_TOLERANCE)
        for term,target in [('DrE',-.4578),('DaB',-.1195),('DaS',-.6558)]:check_row(rows,'主全样本M4 '+term,target,coefficients[term],oldu['full_sample_coefficients'][term],LOSS_TOLERANCE)
        result['interval_checks']=[]
        for validation in ['family','area']:
            previous=oldm['settings']['D1_MLE_family_'+validation]
            for comparison,new in models[validation]['comparisons'].items():
                old=previous['comparisons'][comparison]['family_cluster_bootstrap_95ci'];newci=new['family_cluster_bootstrap_95ci']
                delta=float(np.max(np.abs(np.array(newci)-np.array(old))))
                record={'validation':validation,'comparison':comparison,'old_interval':old,'recomputed_interval':newci,'max_absolute_difference':delta,'tolerance':INTERVAL_TOLERANCE,'passed':delta<=INTERVAL_TOLERANCE}
                result['interval_checks'].append(record)
                if not record['passed']:raise RuntimeError('T0区间差异：'+json.dumps(record,ensure_ascii=False))
        result['passed']=True;status='passed'
    except Exception as exc:
        result['error']=str(exc);result['traceback']=traceback.format_exc()
    finally:
        after=source_manifest();changed=[p for p in before if after.get(p)!=before[p]]
        result['source_protection']={'file_count':len(before),'changed_files':changed,'unchanged':not changed}
        if changed:result['passed']=False;result['error']='旧文件保护核验失败：'+str(changed);status='failed'
        result['finished_utc']=now();result['script_sha256']=digest(__file__)
        result['input_sha256']={str(p.relative_to(ROOT)):digest(p) for p in [ROOT/'data/kinbank/kinbank/cldf/forms.csv',ROOT/'data/kinbank/kinbank/cldf/languages.csv',ROOT/'data/kinbank/kinbank/cldf/parameters.csv',ROOT/'data/glottolog_languages.csv']}
        write_json(OUT/'reproduction_results.json',result);report(result)
        record_run(status,{'passed':result['passed'],'checks':len(rows),'interval_checks':len(result.get('interval_checks',[])),'error':result.get('error'),'report':'results/baseline/reproduction_report.md'},commit)
    print(json.dumps({'passed':result['passed'],'checks':len(rows),'interval_checks':len(result.get('interval_checks',[])),'error':result.get('error'),'report':'results/baseline/reproduction_report.md'},ensure_ascii=False,indent=2))
    if not result['passed']:raise SystemExit(1)


if __name__=='__main__':main()
