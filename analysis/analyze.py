"""执行固定协议，生成真实样本外预测及中文报告。运行：python analyze.py。"""
from pathlib import Path
from itertools import combinations
import datetime, hashlib, json, math, re, warnings
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.exceptions import ConvergenceWarning
from audit import BASE, OUT, CATEGORIES, norm, load_data, matrix

SEED = 20261014
MODELS = ['raw_additive','classical_additive','pairwise']
ZH_MODELS = {'raw_additive':'原始加性','classical_additive':'经典加性','pairwise':'两两交互'}
FEATURE_NAMES = {
    'raw_additive':['Dr','Da','De'],
    'classical_additive':['Dr','Da','De','Drelative'],
    'pairwise':['Dr','Da','De','Dr_Da','Dr_De','Da_De']}

def sources(text):
    return [re.sub(r'\[[^\]]*\]', '', s).strip() for s in str(text).split(';') if re.sub(r'\[[^\]]*\]', '', s).strip()]

def save_json(obj, file):
    (OUT/file).write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False))

def gen_pairs(frame, selected, minimum=8, definition='overlap', singleton=False):
    sets = frame.groupby(['Language_ID','Parameter_ID']).normalized_form.agg(lambda v:set(v))
    rows=[]; cats=[]
    for lang in selected.itertuples(index=False):
        found = {cat:sets.loc[(lang.ID,cat)] for cat in CATEGORIES if (lang.ID,cat) in sets.index}
        if len(found)<minimum or not lang.family_group:
            continue
        if singleton and any(len(s)!=1 for s in found.values()):
            continue
        for cat,items in found.items():
            cats.append({'Language_ID':lang.ID,'Glottocode':lang.Glottocode,'Parameter_ID':cat,'forms_json':json.dumps(sorted(items),ensure_ascii=False),'n_forms':len(items)})
        for a,b in combinations(found,2):
            sa,sb=found[a],found[b]
            dr=int(a[2]!=b[2]);da=int(a[1]!=b[1]);de=int(a[0]!=b[0])
            rows.append({'Language_ID':lang.ID,'Glottocode':lang.Glottocode,'Name':lang.Name,
                         'family_group':lang.family_group,'family_name':lang.family_name,
                         'family_status':lang.family_status,'Macroarea':lang.Macroarea,
                         'category_a':a,'category_b':b,'n_categories':len(found),
                         'forms_a':len(sa),'forms_b':len(sb),'shared_forms':len(sa&sb),
                         'Dr':dr,'Da':da,'De':de,'Drelative':int(dr!=de),
                         'pattern':str(dr)+str(da)+str(de),
                         'shared_form':int(bool(sa&sb)) if definition=='overlap' else int(sa==sb)})
    return pd.DataFrame(rows),pd.DataFrame(cats)

def source_shared_audit(frame,pairs):
    source_by_form={}
    for row in frame.itertuples(index=False):
        key=(row.Language_ID,row.Parameter_ID,row.normalized_form)
        source_by_form.setdefault(key,set()).update(sources(row.Source))
    cat_forms={}
    for (lid,cat,form),src in source_by_form.items():
        cat_forms.setdefault((lid,cat),{})[form]=src
    positive=pairs[pairs.shared_form==1]
    supported=0;has_missing=0
    for row in positive.itertuples(index=False):
        a=cat_forms[(row.Language_ID,row.category_a)]
        b=cat_forms[(row.Language_ID,row.category_b)]
        common=set(a)&set(b)
        supported+=int(any(a[f]&b[f] for f in common))
        has_missing+=int(any(not a[f] or not b[f] for f in common))
    return {'primary_shared_pairs':len(positive),
            'primary_shared_pairs_with_same_source_support':supported,
            'primary_shared_pairs_without_same_source_support':len(positive)-supported,
            'primary_shared_pairs_with_missing_source_on_shared_forms':has_missing}

def bootstrap(frame, col, n=5000):
    grouped = frame.groupby('family_group')[col].agg(['sum','count'])
    rng=np.random.default_rng(SEED)
    idx=rng.integers(0,len(grouped),size=(n,len(grouped)))
    totals=grouped['sum'].to_numpy()[idx].sum(axis=1)
    counts=grouped['count'].to_numpy()[idx].sum(axis=1)
    estimate=totals/counts
    return [float(x) for x in np.quantile(estimate,[.025,.975])]

def cv_run(data, variant, grouping, C, fits, coefs):
    groups=data['family_group'] if grouping=='family' else data['Glottocode']
    cv=GroupKFold(n_splits=5)
    pred=data[['Language_ID','Glottocode','family_group','family_name','family_status','pattern','category_a','category_b','shared_form']].copy()
    pred['variant']=variant;pred['cv_grouping']=grouping;pred['fold']=-1
    for model in MODELS:pred['p_'+model]=np.nan
    for fold,(itr,ite) in enumerate(cv.split(data,groups=groups)):
        train,test=data.iloc[itr],data.iloc[ite]
        assert not set(groups.iloc[itr]) & set(groups.iloc[ite])
        assert not set(train.Glottocode) & set(test.Glottocode)
        weights=train.Glottocode.map(1/train.Glottocode.value_counts()).to_numpy()
        for model in MODELS:
            xt=matrix(train[['Dr','Da','De']],model);xe=matrix(test[['Dr','Da','De']],model)
            cells=train.groupby('pattern').shared_form.agg(['sum','count'])
            nonseparated=bool(((cells['sum']>0)&(cells['sum']<cells['count'])).all() and len(cells)==7)
            if C is None and not nonseparated:
                raise RuntimeError('无惩罚敏感性存在单元分离；该项不应进行稳定比较。')
            estimator=LogisticRegression(C=np.inf if C is None else C,l1_ratio=0,solver='lbfgs',tol=1e-9,max_iter=2000)
            with warnings.catch_warnings(record=True) as ws:
                warnings.simplefilter('always')
                estimator.fit(xt,train.shared_form.to_numpy(),sample_weight=weights)
            prob=estimator.predict_proba(xe)[:,1]
            pred.loc[pred.index[ite],'p_'+model]=prob
            pred.loc[pred.index[ite],'fold']=fold
            fits.append({'variant':variant,'cv_grouping':grouping,'fold':fold,'model':model,
                         'C':C,'train_languages':int(train.Glottocode.nunique()),'test_languages':int(test.Glottocode.nunique()),
                         'train_families':int(train.family_group.nunique()),'test_families':int(test.family_group.nunique()),
                         'design_rank':int(np.linalg.matrix_rank(np.c_[np.ones(len(xt)),xt])),
                         'iterations':int(estimator.n_iter_[0]),'converged':not any(issubclass(w.category,ConvergenceWarning) for w in ws),
                         'train_seven_cells_both_outcomes':nonseparated,'prediction_min':float(prob.min()),'prediction_max':float(prob.max())})
            coefs.append({'variant':variant,'cv_grouping':grouping,'fold':fold,'model':model,
                          'intercept':float(estimator.intercept_[0]),**dict(zip(FEATURE_NAMES[model],map(float,estimator.coef_[0])))})
    assert not pred.filter(like='p_').isna().any().any()
    for model in MODELS:
        p=np.clip(pred['p_'+model].to_numpy(),1e-15,1-1e-15);y=pred.shared_form.to_numpy()
        pred['loss_'+model]=-(y*np.log(p)+(1-y)*np.log(1-p))
        pred['brier_'+model]=(p-y)**2
    scores=pred.groupby(['Glottocode','Language_ID','family_group','family_name','family_status'],as_index=False).agg(
        n_pairs=('shared_form','size'),
        **{col:(col,'mean') for col in pred.columns if col.startswith('loss_') or col.startswith('brier_')})
    scores['variant']=variant;scores['cv_grouping']=grouping
    scores['gain_raw']=scores.loss_raw_additive-scores.loss_pairwise
    scores['gain_classical']=scores.loss_classical_additive-scores.loss_pairwise
    scores['gain_classical_over_raw']=scores.loss_raw_additive-scores.loss_classical_additive
    metric={
        'variant':variant,'cv_grouping':grouping,'C':C,'languages':int(data.Glottocode.nunique()),
        'family_groups':int(data.family_group.nunique()),'pairs':len(data),
        'shared_form_prevalence':float(data.shared_form.mean()),
        'language_equal_logloss':{m:float(scores['loss_'+m].mean()) for m in MODELS},
        'pair_equal_logloss':{m:float(pred['loss_'+m].mean()) for m in MODELS},
        'language_equal_brier':{m:float(scores['brier_'+m].mean()) for m in MODELS},
        'comparisons':{}}
    for comp in ['raw','classical','classical_over_raw']:
        col='gain_'+comp
        family=scores.groupby('family_group')[col].agg(['mean','sum','count']).sort_values('count',ascending=False)
        biggest=family.index[0]
        metric['comparisons'][comp]={
            'language_equal_gain':float(scores[col].mean()),'family_cluster_bootstrap_95ci':bootstrap(scores,col),
            'family_equal_gain':float(family['mean'].mean()),
            'largest_family':biggest,'largest_family_languages':int(family.iloc[0]['count']),
            'gain_excluding_largest_family_fixed_predictions':float(scores[scores.family_group!=biggest][col].mean()),
            'families_with_positive_gain':int((family['mean']>0).sum()),
            'families_with_negative_gain':int((family['mean']<0).sum())}
    return pred,scores,metric

def main():
    protocol=OUT/'protocol_frozen.md';prov=json.loads((OUT/'provenance.json').read_text())
    assert hashlib.sha256(protocol.read_bytes()).hexdigest()==prov['protocol_sha256']
    forms,sibling,valid,available,selected,glot=load_data()
    excluded=selected[selected.family_group==''][['ID','Name','Glottocode','n_categories','family_status']]
    excluded.to_csv(OUT/'excluded_genealogy.csv',index=False)
    chosen=valid[valid.Language_ID.isin(selected.ID)].copy()
    chosen[['ID','Language_ID','Parameter_ID','Value','Form','normalized_form','Source']].to_csv(OUT/'sibling_records_selected.csv',index=False)
    chosen['sources']=chosen.Source.map(sources)
    ex=chosen.explode('sources');ex=ex[ex.sources.notna() & (ex.sources!='')]
    cat_src=ex.groupby(['Language_ID','Parameter_ID']).sources.nunique()
    lang_src=ex.groupby('Language_ID').sources.nunique()
    source_audit={'selected_records':len(chosen),'selected_language_ids':len(selected),
                  'records_without_source':int(chosen.sources.map(len).eq(0).sum()),
                  'categories_with_multiple_sources':int((cat_src>1).sum()),'categories_with_source':len(cat_src),
                  'languages_with_multiple_sources':int((lang_src>1).sum()),
                  'maximum_category_sources':int(cat_src.max()),'maximum_language_sources':int(lang_src.max())}
    # 选择一个文献来源，全部只按覆盖率与来源标识排序。
    source_cov=ex.groupby(['Language_ID','sources']).Parameter_ID.nunique().reset_index(name='n_categories')
    best=source_cov.sort_values(['Language_ID','n_categories','sources'],ascending=[True,False,True]).drop_duplicates('Language_ID')
    best.to_csv(OUT/'preferred_sources.csv',index=False)
    single_source=ex.merge(best[['Language_ID','sources']],on=['Language_ID','sources'])
    primary,cats=gen_pairs(chosen,selected)
    source_audit.update(source_shared_audit(chosen,primary))
    primary.to_csv(OUT/'pairs_primary.csv',index=False);cats.to_csv(OUT/'category_forms_primary.csv',index=False)
    coverage,_=gen_pairs(chosen,selected,minimum=6)
    equalsets,_=gen_pairs(chosen,selected,definition='equal')
    singleton,_=gen_pairs(chosen,selected,singleton=True)
    single,_=gen_pairs(single_source,selected)
    variants=[('primary',primary,1),('coverage75',coverage,1),('equal_sets',equalsets,1),('singleton_only',singleton,1),('single_source',single,1),('C0.1',primary,.1),('C10',primary,10),('unpenalized',primary,None)]
    preds=[];scores=[];metrics=[];fits=[];coefs=[]
    for name,data,C in variants:
        print(f'执行 {name}：{data.Glottocode.nunique()} 语言，{len(data)} 类别对',flush=True)
        data.to_csv(OUT/f'pairs_{name}.csv',index=False)
        pred,score,metric=cv_run(data,name,'family',C,fits,coefs)
        preds.append(pred);scores.append(score);metrics.append(metric)
    pred,score,metric=cv_run(primary,'primary','language',1,fits,coefs)
    preds.append(pred);scores.append(score);metrics.append(metric)
    allpred=pd.concat(preds,ignore_index=True);allscores=pd.concat(scores,ignore_index=True)
    allpred.to_csv(OUT/'oof_predictions.csv',index=False)
    allscores.to_csv(OUT/'language_oof_scores.csv',index=False)
    pd.DataFrame(fits).to_csv(OUT/'cv_fit_diagnostics.csv',index=False)
    pd.DataFrame(coefs).to_csv(OUT/'cv_coefficients.csv',index=False)
    cells=primary.groupby(['Dr','Da','De','pattern'],as_index=False).agg(n_pairs=('shared_form','size'),shared_pairs=('shared_form','sum'),share_rate=('shared_form','mean'),n_languages=('Glottocode','nunique'))
    patterns=cells[['Dr','Da','De']].to_numpy()
    weights=primary.Glottocode.map(1/primary.Glottocode.value_counts()).to_numpy()
    fullcoefs=[]
    for model in MODELS:
        for C in [1,None]:
            estimator=LogisticRegression(C=np.inf if C is None else C,l1_ratio=0,solver='lbfgs',tol=1e-9,max_iter=2000).fit(matrix(primary[['Dr','Da','De']],model),primary.shared_form,sample_weight=weights)
            suffix='ridge' if C else 'mle'
            cells['p_'+model+'_'+suffix]=estimator.predict_proba(matrix(patterns,model))[:,1]
            fullcoefs.append({'model':model,'C':C,'intercept':float(estimator.intercept_[0]),**dict(zip(FEATURE_NAMES[model],map(float,estimator.coef_[0])))})
    cells.to_csv(OUT/'seven_cell_probabilities.csv',index=False)
    pd.DataFrame(fullcoefs).to_csv(OUT/'fullfit_coefficients.csv',index=False)
    assert np.max(np.abs(cells.p_pairwise_mle-cells.share_rate))<1e-4
    # 二维扩展在男参照者内描述；不把可识别性不足的交互估计作结果。
    extension=[]
    normforms=forms.copy();normforms['normalized_form']=normforms.Form.map(norm)
    normforms=normforms[~normforms.normalized_form.isin(['','?','-'])]
    for domain,categories in [('grandparent',['mFF','mFM','mMF','mMM']),('parental_sibling',['mFB','mFZ','mMB','mMZ'])]:
        sf=normforms[normforms.Parameter_ID.isin(categories)&normforms.Language_ID.isin(selected.ID)]
        ds=sf.groupby(['Language_ID','Parameter_ID']).normalized_form.agg(lambda v:set(v))
        for lang in selected.itertuples(index=False):
            found={c:ds.loc[(lang.ID,c)] for c in categories if (lang.ID,c) in ds.index}
            if len(found)!=4 or not lang.family_group:continue
            for a,b in combinations(found,2):
                extension.append({'domain':domain,'Glottocode':lang.Glottocode,'Language_ID':lang.ID,'family_group':lang.family_group,'category_a':a,'category_b':b,'Dr':int(a[2]!=b[2]),'Dc':int(a[1]!=b[1]),'shared_form':int(bool(found[a]&found[b]))})
    ext=pd.DataFrame(extension);ext.to_csv(OUT/'extension_pairs_descriptive.csv',index=False)
    extsumm=ext.groupby(['domain','Dr','Dc'],as_index=False).agg(pairs=('shared_form','size'),languages=('Glottocode','nunique'),share_rate=('shared_form','mean'))
    extsumm.to_csv(OUT/'extension_descriptive_summary.csv',index=False)
    results={'execution_time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'structural_audit':json.loads((OUT/'structural_audit.json').read_text()),
             'source_audit':source_audit,'excluded_genealogy':excluded.to_dict('records'),
             'analyses':metrics,'full_fit_max_unpenalized_saturated_rate_error':float(np.max(np.abs(cells.p_pairwise_mle-cells.share_rate))),
             'all_cv_fits_converged':bool(all(d['converged'] for d in fits)),
             'cv_fits_count':len(fits),'minimum_training_rank':{m:min(d['design_rank'] for d in fits if d['model']==m) for m in MODELS},
             'seven_cells':cells.to_dict('records'),'extension_descriptive_summary':extsumm.to_dict('records')}
    save_json(results,'results.json')
    make_report(results)
    make_figures(cells,metrics)
    prov['execution_completed_utc']=results['execution_time_utc'];prov['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();save_json(prov,'provenance.json')
    print(json.dumps(metrics[0],indent=2,ensure_ascii=False),flush=True)

def make_report(r):
    a=r['analyses'][0];comp=a['comparisons'];raw=comp['raw'];cl=comp['classical'];st=r['structural_audit'];sa=r['source_audit']
    lines=[
        '# Kinbank 实际执行结果',
        '',
        f'本次确实执行了锁定版本的数据清洗、无序配对、固定惩罚 logistic 回归、五折语系整组留出、语言整组留出和语系簇 bootstrap。分析协议在结果生成前冻结，脚本为 `analyze.py`。',
        '',
        '## 样本与质量',
        '',
        f'锁定 Kinbank commit `925cc0e702ae5481cfe0088aaa0e69c3991000f3`，原表共 {st["forms_records"]:,} 条词形记录、{st["language_ids_total"]:,} 个语言资料 ID、{st["parameters_total"]:,} 个参数。兄弟姐妹目标八类拥有 {st["sibling_records"]:,} 条记录、{st["sibling_language_ids"]:,} 个资料 ID。按 Glottocode 去重移除 {st["duplicate_source_ids_removed"]} 个重复来源 ID，保留 {st["sibling_glottocodes_selected"]:,} 个 Glottocode。',
        '',
        f'去重后八类齐全的记录系统为 {st["coverage_after_dedup"]["8"]} 个；排除 {len(r["excluded_genealogy"])} 个未解决谱系分类的记录，主分析为 {a["languages"]} 个语言／语言变体记录系统、{a["family_groups"]} 个谱系组（孤立语言单列）、{a["pairs"]:,} 个无序类别对。样本含历史语言，不能解释为仅代表当代在世语言。原始 Family 空缺的 {st["original_missing_family_selected"]} 个已选资料 ID 经官方 Glottolog 补联，不把这些对象全部当作孤立语言。',
        '',
        f'NFC 与空白处理改变 {st["normalization_changed_records"]} 条目标记录；数据库列出的缺失标记在目标记录中为 {st["invalid_form_records"]} 条。仅采用数据库既有 Form；其上游切词与括号处理并非本研究新增。原始粗类别可能被数据库展开至年龄和参照者性别较细类别，因此八类齐全不表示原文献独立调查八个区分。',
        '',
        f'已选 {sa["selected_language_ids"]} 个 ID 的 {sa["selected_records"]:,} 条目标记录中，{sa["records_without_source"]} 条没有来源；{sa["languages_with_multiple_sources"]} 个语言资料 ID、{sa["categories_with_multiple_sources"]} 个类别含多个来源（类别最大 {sa["maximum_category_sources"]} 个来源）。主定义对同一 ID 的有效同义词取并集；单来源敏感性重新限定至结构覆盖最佳的一篇文献。',
        '',
        f'主样本 {sa["primary_shared_pairs"]:,} 个共享类别对中，{sa["primary_shared_pairs_with_same_source_support"]:,} 对至少有一个共享词形获得同一文献来源支持，{sa["primary_shared_pairs_without_same_source_support"]} 对未获得这种支持；这后一数字同时包含跨来源形成的共享与来源字段缺失，不能全部解释为资料矛盾。',
        '',
        '未纳入主要谱系分析的对象：',
        '',
        '| 资料 ID | 名称 | Glottocode | 原因 |',
        '|---|---|---|---|']
    for e in r['excluded_genealogy']:lines.append(f'| {e["ID"]} | {e["Name"]} | {e["Glottocode"]} | {e["family_status"]} |')
    lines += ['', '## 模型识别与主比较','',
              '原始加性、经典加性、两两交互设计秩依次为 4、5、7。七个非零差异单元均存在；两两交互在差异单元层面饱和。由于 `Drelative = Dr + De − 2DrDe`，性别×参照者性别的表示可直接对应传统同／异性兄弟姐妹区分；三阶交互无法独立估计。经典与单交互五列模型空间相同，岭惩罚下不同编码并不保证同样预测。',
              '',
              '主模型为固定效应岭 logistic 回归、`C=1`，训练语言内总权重为 1；没有拟合或声称拟合 GLMM。语系五折留出严格阻断同一谱系组进入两边。正增益为基准 log loss 减去两两交互 log loss，单位为自然对数。',
              '', '| 模型 | 语言等权 log loss | Brier score |','|---|---:|---:|']
    for m in MODELS:lines.append(f'| {ZH_MODELS[m]} | {a["language_equal_logloss"][m]:.6f} | {a["language_equal_brier"][m]:.6f} |')
    lines+=['',f'原始加性→两两交互的平均增益为 **{raw["language_equal_gain"]:.6f}**，语系簇 bootstrap 95% 区间为 **[{raw["family_cluster_bootstrap_95ci"][0]:.6f}, {raw["family_cluster_bootstrap_95ci"][1]:.6f}]**。',
            '',f'经典加性→两两交互的剩余平均增益为 **{cl["language_equal_gain"]:.6f}**，95% 区间为 **[{cl["family_cluster_bootstrap_95ci"][0]:.6f}, {cl["family_cluster_bootstrap_95ci"][1]:.6f}]**。',
            '', '置信区间基于已完成的折外预测，在谱系组层面抽样 5,000 次；不包含重新训练或更换划折的不确定性，也没有把类别对当作独立样本计算显著性。',
            '', '## 完整敏感性结果','',
            '| 条件 | 验证分组 | 语言数 | 原始加性损失 | 经典加性损失 | 交互损失 | 原始增益（95%区间） | 经典剩余增益（95%区间） |',
            '|---|---|---:|---:|---:|---:|---:|---:|']
    names={'primary':'主分析','coverage75':'至少75%覆盖','equal_sets':'词形集合完全相同','singleton_only':'每类仅一词形','single_source':'单一文献来源','C0.1':'C=0.1','C10':'C=10','unpenalized':'无惩罚最大似然'}
    for t in r['analyses']:
        x=t['comparisons']['raw'];y=t['comparisons']['classical'];l=t['language_equal_logloss']
        lines.append(f'| {names[t["variant"]]} | {"语系" if t["cv_grouping"]=="family" else "语言"} | {t["languages"]} | {l["raw_additive"]:.6f} | {l["classical_additive"]:.6f} | {l["pairwise"]:.6f} | {x["language_equal_gain"]:.6f} [{x["family_cluster_bootstrap_95ci"][0]:.6f}, {x["family_cluster_bootstrap_95ci"][1]:.6f}] | {y["language_equal_gain"]:.6f} [{y["family_cluster_bootstrap_95ci"][0]:.6f}, {y["family_cluster_bootstrap_95ci"][1]:.6f}] |')
    lines+=['',f'按语系等权而非语言等权时，原始增益为 {raw["family_equal_gain"]:.6f}，经典剩余增益为 {cl["family_equal_gain"]:.6f}。最大组 `{raw["largest_family"]}` 含 {raw["largest_family_languages"]} 个主样本系统；在既有折外预测中移除该组后，两项增益依次为 {raw["gain_excluding_largest_family_fixed_predictions"]:.6f} 与 {cl["gain_excluding_largest_family_fixed_predictions"]:.6f}。这里仅改变评分样本，没有重训模型。',
            '', '主方案的区间均包含零，不能据此认定两两交互在新语系上有稳定增益。严格词形集合与单词形子样本下，超过经典基准的点估计变为负；较弱惩罚及无惩罚的敏感性则显示较大正增益。由此得到的是依赖词形处理和惩罚强度的证据，而非已经确立的普遍规律；不能事后把正向的无惩罚分析替换成主检验。',
            '', '本轮估计对象是合并语言系统之后、向新谱系推广的边际共享词形概率。即使每个语言内的条件 logit 都是加性的，混合不同截距／斜率也可能产生边际非加性。整组交叉验证检验跨谱系预测，不能单独判定典型语言内部的语义表征需要交互；若要回答该问题，须另构造具有充分变异的分层或完整类别划分模型。',
            '', '## 七单元结构','',
            '位次为所指者性别差异、年龄差异、参照者性别差异。以下拟合值为全样本描述，不用于替代上面的样本外证据。','',
            '| 差异组合 | 类别对数 | 共享比例 | 原始加性预测 | 经典加性预测 | 交互预测 |','|---|---:|---:|---:|---:|---:|']
    for c in r['seven_cells']:lines.append(f'| {c["pattern"]} | {c["n_pairs"]} | {c["share_rate"]:.4f} | {c["p_raw_additive_ridge"]:.4f} | {c["p_classical_additive_ridge"]:.4f} | {c["p_pairwise_ridge"]:.4f} |')
    lines+=['','## 二维扩展描述','',
            '为保持原方案的二维比较，扩展限定男参照者，祖辈比较所指性别与连接亲属性别，父母兄弟姐妹同理。截距加两主效应已经覆盖三种非零差异组合，加入交互仍为秩 3，故本次仅描述，不给出独立交互证据。','',
            '| 领域 | 所指性别差异 | 连接性别差异 | 语言数 | 类别对数 | 共享比例 |','|---|---:|---:|---:|---:|---:|']
    for e in r['extension_descriptive_summary']:lines.append(f'| {"祖辈" if e["domain"]=="grandparent" else "父母的兄弟姐妹"} | {e["Dr"]} | {e["Dc"]} | {e["languages"]} | {e["pairs"]} | {e["share_rate"]:.4f} |')
    lines+=['','## 核验与证据台账','',
            f'全部 {r["cv_fits_count"]} 次折内模型拟合的收敛状态为 {r["all_cv_fits_converged"]}；最低训练矩阵秩保持 4、5、7。无惩罚七单元饱和全样本预测与实际共享比例的最大误差为 {r["full_fit_max_unpenalized_saturated_rate_error"]:.2e}，符合其饱和性质。脚本验证每折没有同谱系／同 Glottocode 泄漏。',
            '', '| 证据项 | 支持的事实 | 可复查文件 |','|---|---|---|',
            '| F1 | 原始字段、版本、记录数和去重 | structural_audit.json；provenance.json |',
            '| F2 | 无序类别对与实际共享关系 | pairs_primary.csv；category_forms_primary.csv |',
            '| F3 | 每折训练、预测、收敛与谱系隔离 | cv_fit_diagnostics.csv；oof_predictions.csv |',
            '| F4 | 语言等权与语系簇区间 | language_oof_scores.csv；results.json |',
            '| F5 | 传统同／异性区分、矩阵识别限制 | protocol_frozen.md；audit.py；seven_cell_probabilities.csv |',
            '', '范围与对象限定：删去未解决谱系的两个对象；将二维扩展限定为描述；没有新增人工语义标注。所有计划敏感性均报告。主要预测结论仅适用于本次版本、来源选择、同形操作定义和新谱系评分方式；谱系分组不控制地理接触，语言内类别对相关性也没有被生成式划分模型直接表示。',
            '', '未解决事项：语系与区域采样偏倚、上游粗类别展开、跨来源语体变体与偶然同形、真正心理语义表征、类别划分的传递性约束。当前数据支持预测关系，不能独立鉴别这些机制。','']
    (OUT/'analysis_report.md').write_text('\n'.join(lines))

def make_figures(cells,metrics):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    font_file='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    font_manager.fontManager.addfont(font_file)
    plt.rcParams['font.family']=font_manager.FontProperties(fname=font_file).get_name()
    plt.rcParams['axes.unicode_minus']=False
    fig,ax=plt.subplots(figsize=(9,4.8))
    x=np.arange(7)
    ax.plot(x,cells.share_rate,'ko-',label='实际共享词形比例')
    for m,style in [('raw_additive','s--'),('classical_additive','^--'),('pairwise','d:')]:
        ax.plot(x,cells['p_'+m+'_ridge'],style,label=ZH_MODELS[m])
    ax.set_xticks(x,cells.pattern);ax.set_xlabel('差异组合：所指者性别／相对年龄／参照者性别');ax.set_ylabel('共享词形概率');ax.set_ylim(0,1);ax.legend(fontsize=9);ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(OUT/'seven_cell_fit.png',dpi=180);fig.savefig(OUT/'seven_cell_fit.svg');plt.close(fig)
    data=[m for m in metrics if m['cv_grouping']=='family']
    fig,ax=plt.subplots(figsize=(9,5))
    for j,key in enumerate(['raw','classical']):
        vals=np.array([m['comparisons'][key]['language_equal_gain'] for m in data]);ci=np.array([m['comparisons'][key]['family_cluster_bootstrap_95ci'] for m in data])
        y=np.arange(len(data))+(.12 if j else -.12)
        # 百分位区间不必围绕均值，用水平线与点分别画。
        for k in range(len(data)):ax.plot(ci[k], [y[k],y[k]],color=['#3b6db5','#cf6739'][j])
        ax.plot(vals,y,'o',color=['#3b6db5','#cf6739'][j],label=['相对原始加性的增益','相对经典加性的剩余增益'][j])
    names={'primary':'主分析','coverage75':'至少75%覆盖','equal_sets':'词形集合完全相同','singleton_only':'每类仅一词形','single_source':'单一文献来源','C0.1':'C=0.1','C10':'C=10','unpenalized':'无惩罚最大似然'}
    ax.set_yticks(np.arange(len(data)),[names[m['variant']] for m in data]);ax.axvline(0,color='grey',linestyle='--');ax.set_xlabel('语系留出 log loss 增益（基准损失减去交互损失）');ax.legend(fontsize=9);ax.grid(axis='x',alpha=.2)
    fig.tight_layout();fig.savefig(OUT/'robustness_gain.png',dpi=180);fig.savefig(OUT/'robustness_gain.svg');plt.close(fig)

if __name__=='__main__':main()
