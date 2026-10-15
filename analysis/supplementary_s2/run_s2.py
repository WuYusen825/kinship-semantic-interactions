"""S2：协议门、20×3交叉预测、完整组件汇总；不改冻结文件。"""
from pathlib import Path
import argparse, datetime, hashlib, json, subprocess, sys
import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.model_selection import GroupKFold
from s2_models import MODELS, COMPARISONS, build_design, fit_aggregated, fit_c1_rows, logloss
from verify_s2_entry import verify_protocol, reproduce_frozen

HERE=Path(__file__).resolve().parent
SEED=20261014

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save_json(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False))

def row_weights(frame, weighting):
    n=frame.Glottocode.nunique()
    counts=frame.groupby('family_group').Glottocode.nunique()
    if weighting=='language':return np.full(len(frame),1/28)
    return n/(len(counts)*frame.family_group.map(counts).to_numpy()*28)

def score_value(scores, column, weighting):
    return float(scores.groupby('family_group')[column].mean().mean() if weighting=='family' else scores[column].mean())

def bootstrap_comparisons(scores,weighting):
    columns=['gain_'+a+'_'+b for a,b in COMPARISONS]
    group=scores.groupby('family_group')[columns].agg(['sum','mean','count'])
    n=len(group);idx=np.random.default_rng(SEED).integers(0,n,size=(5000,n))
    result={}
    for (a,b),col in zip(COMPARISONS,columns):
        if weighting=='family':samples=group[(col,'mean')].to_numpy()[idx].mean(axis=1)
        else:samples=group[(col,'sum')].to_numpy()[idx].sum(axis=1)/group[(col,'count')].to_numpy()[idx].sum(axis=1)
        gain=score_value(scores,col,weighting)
        means=scores.groupby('family_group')[col].mean()
        excluded={}
        for family in ['Austronesian','Pama-Nyungan']:
            subset=scores[~scores.family_name.eq(family)]
            excluded[family]={'gain':score_value(subset,col,weighting),'excluded_systems':len(scores)-len(subset),'refitted':False}
        result[a+'-'+b]={'gain':gain,'family_cluster_bootstrap_95ci':np.quantile(samples,[.025,.975]).tolist(),
                         'mean_system_loglikelihood_ratio':28*gain,'mean_system_loglikelihood_ratio_95ci':(28*np.quantile(samples,[.025,.975])).tolist(),
                         'families_positive':int((means>0).sum()),'families_negative':int((means<0).sum()),'families_tied':int((means==0).sum()),
                         'fixed_prediction_exclusions':excluded}
    return result

def cell_calibration(frame,pred,weighting):
    records=[]
    for area in ['全部']+sorted(frame.Macroarea_first.fillna('').unique()):
        sub=frame if area=='全部' else frame[frame.Macroarea_first.fillna('')==area]
        for pattern,cell in sub.groupby('pattern'):
            weights=row_weights(cell,weighting) # 每系统此格四对；固定分母28只差共同常数。
            weights=weights/weights.sum()
            obs=float(weights@cell.shared_form.to_numpy())
            for j,m in enumerate(MODELS):
                fit=float(weights@pred[cell.index.to_numpy(),j])
                records.append({'area':area or '未知','pattern':str(pattern),'model':m,'observed':obs,'predicted':fit,
                                'calibration_error':fit-obs,'absolute_calibration_error':abs(fit-obs),
                                'systems':int(cell.Glottocode.nunique())})
    return records

def fit_predict(train,test,designs,model,estimator,weighting,logs):
    X=designs[model];itr=train.pair_index.to_numpy();ite=test.pair_index.to_numpy()
    weights=row_weights(train,weighting)
    if estimator=='C1':beta,diag=fit_c1_rows(X[itr],train.shared_form.to_numpy(),weights,model)
    else:
        total=np.bincount(itr,weights=weights,minlength=28)
        success=np.bincount(itr,weights=weights*train.shared_form.to_numpy(),minlength=28)
        beta,diag=fit_aggregated(X,success,total)
    logs.update(diag)
    if not diag['converged']:raise RuntimeError('预设拟合未收敛：'+str(logs))
    return expit(X[ite]@beta)

def prediction_analysis():
    from measurement_analysis import load_measurement_data
    gate=reproduce_frozen()
    definitions,metadata,forms=load_measurement_data()
    base=definitions['D1'].reset_index(drop=True)
    pair_types=sorted(set(base.category_a+'|'+base.category_b));assert len(pair_types)==28
    designs={m:build_design(pair_types,m) for m in MODELS}
    assert [np.linalg.matrix_rank(designs[m]) for m in MODELS]==[4,5,7,28,14]
    pair_lookup={p:i for i,p in enumerate(pair_types)}
    base['fold_family']=-1;base['fold_language']=-1
    for cv,col in [('family','family_group'),('language','Glottocode')]:
        for k,(_,ite) in enumerate(GroupKFold(5).split(base,groups=base[col])):base.loc[ite,'fold_'+cv]=k
    old=pd.read_csv(HERE.parent/'oof_predictions.csv',usecols=['variant','cv_grouping','Glottocode','category_a','category_b','fold'])
    old=old[(old.variant=='primary')&(old.cv_grouping=='family')]
    merged=base.merge(old,on=['Glottocode','category_a','category_b'])
    assert len(merged)==len(base) and (merged.fold_family==merged.fold).all()
    maps={cv:base.groupby('Glottocode')['fold_'+cv].first() for cv in ['family','language']}
    results={**verify_protocol(),'started_utc':now(),'seed':SEED,'bootstrap_replicates':5000,'main_setting':'D1_MLE_family_family',
             'frozen_C1_reproduction':gate,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'pair_types':pair_types,'model_ranks':{m:int(np.linalg.matrix_rank(designs[m])) for m in MODELS},
             'settings':{},'full_sample_calibration':{}}
    language_outputs=[];fold_outputs=[];fit_outputs=[]
    for definition in ['D1','D2','D3','D4','D5']:
        frame=definitions[definition].reset_index(drop=True)
        frame['pair_index']=(frame.category_a+'|'+frame.category_b).map(pair_lookup)
        for estimator in ['MLE','C1']:
            for weighting in ['family','language']:
                for cv in ['family','area','language']:
                    data=frame[frame.Macroarea_first.fillna('')!=''].reset_index(drop=True) if cv=='area' else frame.copy()
                    data=data.reset_index(drop=True)
                    folds=sorted(data.Macroarea_first.unique()) if cv=='area' else range(5)
                    pred=np.full((len(data),len(MODELS)),np.nan)
                    setting=f'{definition}_{estimator}_{weighting}_{cv}'
                    for fold in folds:
                        test_mask=(data.Macroarea_first.eq(fold).to_numpy() if cv=='area' else data.Glottocode.map(maps[cv]).eq(fold).to_numpy())
                        train=data.loc[~test_mask];test=data.loc[test_mask]
                        if len(test)==0:continue
                        assert len(train)>0
                        if cv=='family':assert not set(train.family_group)&set(test.family_group)
                        if cv=='language':assert not set(train.Glottocode)&set(test.Glottocode)
                        if cv=='area':assert not set(train.Macroarea_first)&set(test.Macroarea_first)
                        fold_outputs.append({'setting':setting,'fold':str(fold),'train_systems':int(train.Glottocode.nunique()),'test_systems':int(test.Glottocode.nunique()),
                                             'train_families':int(train.family_group.nunique()),'test_families':int(test.family_group.nunique()),
                                             'test_glottocodes':json.dumps(sorted(test.Glottocode.unique().tolist())),
                                             'train_family_ids':json.dumps(sorted(train.family_group.unique().tolist())),
                                             'test_family_ids':json.dumps(sorted(test.family_group.unique().tolist()))})
                        for j,model in enumerate(MODELS):
                            log={'setting':setting,'fold':str(fold),'model':model}
                            pred[test.index,j]=fit_predict(train,test,designs,model,estimator,weighting,log)
                            fit_outputs.append(log)
                    assert np.isfinite(pred).all()
                    score=pd.DataFrame({'Glottocode':data.Glottocode})
                    y=data.shared_form.to_numpy()
                    for j,m in enumerate(MODELS):score['loss_'+m]=logloss(y,pred[:,j]);score['brier_'+m]=(y-pred[:,j])**2
                    score=score.groupby('Glottocode').mean().reset_index().merge(data[['Glottocode','Language_ID','family_group','family_name','Macroarea_first']].drop_duplicates('Glottocode'),on='Glottocode')
                    for a,b in COMPARISONS:
                        score['gain_'+a+'_'+b]=score['loss_'+a]-score['loss_'+b]
                        score['system_llr_'+a+'_'+b]=28*score['gain_'+a+'_'+b]
                    block={'measurement':definition,'estimator':estimator,'weighting':weighting,'validation':cv,'systems':len(score),'families':int(score.family_group.nunique()),
                           'logloss':{m:score_value(score,'loss_'+m,weighting) for m in MODELS},
                           'brier':{m:score_value(score,'brier_'+m,weighting) for m in MODELS},'comparisons':bootstrap_comparisons(score,weighting),
                           'areas':{},'cell_calibration':cell_calibration(data,pred,weighting)}
                    for area,group in score.groupby('Macroarea_first',dropna=False):
                        name=area if isinstance(area,str) and area else '未知'
                        block['areas'][name]={'systems':len(group),'families':int(group.family_group.nunique()),'logloss':{m:score_value(group,'loss_'+m,weighting) for m in MODELS},
                                              'comparisons':{a+'-'+b:score_value(group,'gain_'+a+'_'+b,weighting) for a,b in COMPARISONS}}
                    results['settings'][setting]=block
                    score.insert(0,'setting',setting);language_outputs.append(score)
                    save_json(HERE/'prediction_results.json',results)
                    print(now(),setting,'M2-M4',block['comparisons']['M2-M4']['gain'],flush=True)
    # 描述性全样本拟合，与折外校准明确分开。
    for weighting in ['family','language']:
        frame=definitions['D1'].reset_index(drop=True);frame['pair_index']=(frame.category_a+'|'+frame.category_b).map(pair_lookup)
        for estimator in ['MLE','C1']:
            pred=np.zeros((len(frame),len(MODELS)))
            for j,model in enumerate(MODELS):
                log={'setting':f'full_D1_{estimator}_{weighting}','fold':'full','model':model}
                pred[:,j]=fit_predict(frame,frame,designs,model,estimator,weighting,log);fit_outputs.append(log)
            results['full_sample_calibration'][f'D1_{estimator}_{weighting}']=cell_calibration(frame,pred,weighting)
    results.update(finished_utc=now(),fit_count=len(fit_outputs),all_fits_converged=all(r['converged'] for r in fit_outputs),
                   firth_fit_count=sum(r['method']=='Firth' for r in fit_outputs),settings_count=len(results['settings']))
    results['cv_fit_count']=sum(v['fold']!='full' for v in fit_outputs)
    results['full_sample_fit_count']=sum(v['fold']=='full' for v in fit_outputs)
    results['score_blocks']=len(results['settings'])*len(MODELS)
    results['crossed_conditions']=len({(v['measurement'],v['estimator'],v['weighting']) for v in results['settings'].values()})
    results['calibration_summary']={key:{'M2_max_absolute_error':max(v['absolute_calibration_error'] for v in rows if v['area']=='全部' and v['model']=='M2')} for key,rows in results['full_sample_calibration'].items()}
    assert results['settings_count']==60
    pd.concat(language_outputs,ignore_index=True).to_csv(HERE/'s2_language_scores.csv',index=False)
    pd.DataFrame(fold_outputs).to_csv(HERE/'s2_fold_info.csv',index=False)
    pd.DataFrame(fit_outputs).to_json(HERE/'s2_fit_diagnostics.json',orient='records',force_ascii=False,indent=2)
    save_json(HERE/'prediction_results.json',results)
    write_crossed_tables(results)
    write_prediction_report(results)
    return results

def write_crossed_tables(r):
    comparisons=[];calibration=[]
    for setting,block in r['settings'].items():
        for name,value in block['comparisons'].items():
            lo,hi=value['family_cluster_bootstrap_95ci']
            comparisons.append({'setting':setting,'measurement':block['measurement'],'estimator':block['estimator'],
                                'weighting':block['weighting'],'validation':block['validation'],'systems':block['systems'],
                                'families':block['families'],'comparison':name,'gain':value['gain'],'ci95_low':lo,'ci95_high':hi,
                                'mean_system_loglikelihood_ratio':value['mean_system_loglikelihood_ratio'],
                                'interval_type':'固定折外预测，谱系整组自助5000次，95%百分位'})
        calibration.extend({'setting':setting,'sample':'折外预测',**row} for row in block['cell_calibration'])
    for setting,rows in r['full_sample_calibration'].items():
        calibration.extend({'setting':setting,'sample':'全样本描述拟合',**row} for row in rows)
    assert len(comparisons)==420
    pd.DataFrame(comparisons).to_csv(HERE/'s2_crossed_comparisons.csv',index=False)
    pd.DataFrame(calibration).to_csv(HERE/'s2_cell_calibration.csv',index=False)

def write_prediction_report(r):
    lines=['# S2交叉预测结果','','## 运行前指定的结果','','20测量×估计×权重条件，各运行3种验证；区间为固定折外预测的5000次谱系整组自助95%百分位区间。','','| 条件 | 系统 | M0 | M1 | M2 | M3 | M4 | M2−M4增益及95%区间 |','|---|---:|---:|---:|---:|---:|---:|---|']
    for key,v in r['settings'].items():
        c=v['comparisons']['M2-M4'];lo,hi=c['family_cluster_bootstrap_95ci']
        lines.append('| '+key+' | '+str(v['systems'])+' | '+' | '.join(f'{v["logloss"][m]:.4f}' for m in MODELS)+f' | {c["gain"]:.4f} [{lo:.4f}, {hi:.4f}] |')
    lines+=['','完整七项比较（60设定×7=420行）见[s2_crossed_comparisons.csv](s2_crossed_comparisons.csv)，逐单元校准见[s2_cell_calibration.csv](s2_cell_calibration.csv)。',
            '','## 运行后观察','','全部比较、逐系统分数、分区域结果和拟合诊断保留JSON/CSV，不因方向而删去条件。']
    (HERE/'prediction_report.md').write_text('\n'.join(lines)+'\n')

def assemble():
    verify_protocol()
    paths={'prediction':'prediction_results.json','partition':'partition_results.json','measurement':'measurement_results.json','uncertainty':'uncertainty_results.json','violation_audit':'violation_audit.json','glmm':'glmm_results.json','figures':'s2_figure_data.json'}
    result={**verify_protocol(),'assembled_utc':now(),'status':'事后补充分析，非预注册','components':{}}
    for key,name in paths.items():
        assert (HERE/name).exists(),f'等待组件：{name}'
        result[key]=json.loads((HERE/name).read_text());result['components'][name]=hashlib.sha256((HERE/name).read_bytes()).hexdigest()
    main=result['prediction']['settings']['D1_MLE_family_family']
    p6_gain0=main['comparisons']['M0-M4']['family_cluster_bootstrap_95ci'][0]>0
    p6_gain2=main['comparisons']['M2-M4']['family_cluster_bootstrap_95ci'][0]>0
    p6_coeff=bool(result['uncertainty']['all_three_pointwise_intervals_below_zero'])
    result['hypothesis_decisions']={
        'P1':bool(result['partition']['P1']['A_four']['subsets']['overall']['two_baseline_family_equal_direction_supported']),
        **{h:bool(result['partition']['P2_P4'][h]['strict_direction']['overall']['direction_supported']) for h in ['P2','P3','P4']},
        'P5_database_universal_compatible':bool(result['partition']['P5']['overall']['strict_database_universal_compatible_with_all_tree_applicable_records']),
        'P6':bool(p6_gain0 and p6_gain2 and p6_coeff),
        'P6_conditions':{'M0_to_M4_positive_interval':bool(p6_gain0),'M2_to_M4_positive_interval':bool(p6_gain2),'all_three_coefficients_negative_intervals':p6_coeff},
        'glmm_all_models_converged':bool(result['glmm']['all_models_converged'])}
    write_crossed_tables(result['prediction'])
    write_prediction_report(result['prediction'])
    save_json(HERE/'s2_results.json',result)
    parts=['# 补充分析S2结果','','本分析写于冻结结果、S1和评审核查结果已知之后；最终协议独立提交6ba7afb早于实测。全部模型、口径及失败诊断保留，不把事后补充称为预注册。','']
    for name in ['partition_report.md','prediction_report.md','s2_violation_audit.md']:
        if (HERE/name).exists():parts.append((HERE/name).read_text())
    parts+=['','## 模型化不确定性与拟合状态','','主M4的5000次谱系整组系数重拟合全部成功；三个GLMM分别按2000/10000次上限作两次预置尝试，均因precision loss未达到预定收敛标准。GLMM实际使用909个系统、123个谱系组、25452对；不将这些近似后验作为稳定推断。全部近似参数、梯度、警告、时间与失败状态见uncertainty_results.json和glmm_results.json。','',
            '## 运行后观察与适用范围','','地域缺失系统不补猜；语系/语言验证保留全部记录，地域验证及地域GLMM使用地域已知完整个案。M4不强制合取或传递划分，预测增益与结构兼容性是两个层次。']
    (HERE/'s2_report.md').write_text('\n'.join(parts)+'\n')
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['predictions','assemble','all'],default='all');args=ap.parse_args()
    if args.phase in ['predictions','all']:prediction_analysis()
    if args.phase=='all':
        for script in ['partition_analysis.py','measurement_analysis.py','uncertainty_analysis.py']:
            subprocess.run([sys.executable,str(HERE/script)],check=True,cwd=HERE.parents[1])
        subprocess.run([sys.executable,str(HERE/'measurement_analysis.py'),'--audit'],check=True,cwd=HERE.parents[1])
        subprocess.run([sys.executable,str(HERE/'plot_s2.py')],check=True,cwd=HERE.parents[1])
    if args.phase in ['assemble','all']:assemble()
if __name__=='__main__':main()
