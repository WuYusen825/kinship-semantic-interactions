"""补充分析S1：嵌套调参、经典模型编码依赖与类别对层面结构。协议见 protocol_s1.md。

运行（仓库根目录）：python analysis/supplementary_s1/run_s1.py
本脚本只读冻结输出，不修改 analysis/ 下任何已有文件。
"""
from pathlib import Path
import datetime, hashlib, json, sys, warnings
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.exceptions import ConvergenceWarning

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE.parent
SEED = 20261014
GRID = [0.01, 0.1, 1, 10, 100, 1000]
MODELS = ['M0','M1','M1p','M2','M3']
ZH = {'M0':'原始加性','M1':'经典加性（相对性别编码）','M1p':'经典加性（乘积编码）','M2':'两两交互','M3':'类别对饱和'}
COMPARISONS = [('M0','M2'),('M1','M2'),('M0','M1'),('M1','M1p'),('M2','M3'),('M1','M3')]
PAIR_TYPES = None

def design(frame, model):
    d = frame[['Dr','Da','De']].to_numpy(dtype=float)
    if model == 'M0':
        return d
    if model == 'M1':
        return np.c_[d, np.logical_xor(d[:,0], d[:,2]).astype(float)]
    if model == 'M1p':
        return np.c_[d, d[:,0]*d[:,2]]
    if model == 'M2':
        return np.c_[d, d[:,0]*d[:,1], d[:,0]*d[:,2], d[:,1]*d[:,2]]
    if model == 'M3':
        key = (frame.category_a + '|' + frame.category_b).to_numpy()
        return (key[:,None] == PAIR_TYPES[None,:]).astype(float)
    raise ValueError(model)

def language_weights(frame):
    return frame.Glottocode.map(1/frame.Glottocode.value_counts()).to_numpy()

def fit_predict(train, test, model, C, log=None):
    est = LogisticRegression(C=C, l1_ratio=0, solver='lbfgs', tol=1e-9, max_iter=5000)
    xt = design(train, model)
    with warnings.catch_warnings(record=True) as ws:
        warnings.simplefilter('always')
        est.fit(xt, train.shared_form.to_numpy(), sample_weight=language_weights(train))
    converged = not any(issubclass(w.category, ConvergenceWarning) for w in ws)
    if log is not None:
        log.update({'converged':converged,'iterations':int(est.n_iter_[0]),
                    'design_rank':int(np.linalg.matrix_rank(np.c_[np.ones(len(xt)), xt]))})
    return est.predict_proba(design(test, model))[:,1]

def logloss(y, p):
    p = np.clip(p, 1e-15, 1-1e-15)
    return -(y*np.log(p) + (1-y)*np.log(1-p))

def language_equal_loss(frame, p):
    return pd.Series(logloss(frame.shared_form.to_numpy(), p), index=frame.index).groupby(frame.Glottocode).mean().mean()

def bootstrap(scores, col, n=5000):
    grouped = scores.groupby('family_group')[col].agg(['sum','count'])
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, len(grouped), size=(n, len(grouped)))
    est = grouped['sum'].to_numpy()[idx].sum(axis=1) / grouped['count'].to_numpy()[idx].sum(axis=1)
    return [float(x) for x in np.quantile(est, [.025, .975])]

def main():
    global PAIR_TYPES
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    data = pd.read_csv(ANALYSIS/'pairs_primary.csv', dtype={'pattern':str})
    PAIR_TYPES = np.array(sorted(set(data.category_a + '|' + data.category_b)))
    assert len(PAIR_TYPES) == 28 and len(data) == 26292
    frozen = json.loads((ANALYSIS/'results.json').read_text())
    primary = next(a for a in frozen['analyses'] if a['variant']=='primary' and a['cv_grouping']=='family')

    # 外层折：与冻结分析相同，并逐对核对折号
    outer = list(GroupKFold(n_splits=5).split(data, groups=data.family_group))
    data['fold'] = -1
    for k, (_, ite) in enumerate(outer):
        data.loc[data.index[ite], 'fold'] = k
    oof = pd.read_csv(ANALYSIS/'oof_predictions.csv', usecols=['variant','cv_grouping','Language_ID','category_a','category_b','fold'])
    oof = oof[(oof.variant=='primary') & (oof.cv_grouping=='family')]
    merged = data.merge(oof, on=['Language_ID','category_a','category_b'], suffixes=('','_frozen'))
    assert len(merged) == len(data) and (merged.fold == merged.fold_frozen).all(), '外层折与冻结分析不一致'

    selection = []
    preds = {f'{m}_{s}': np.full(len(data), np.nan) for m in MODELS for s in ['nested','C1']}
    for k, (itr, ite) in enumerate(outer):
        train, test = data.iloc[itr], data.iloc[ite]
        assert not set(train.family_group) & set(test.family_group)
        inner = list(GroupKFold(n_splits=5).split(train, groups=train.family_group))
        for model in MODELS:
            inner_scores = {}
            for C in GRID:
                p = np.full(len(train), np.nan)
                for jtr, jte in inner:
                    p[jte] = fit_predict(train.iloc[jtr], train.iloc[jte], model, C)
                inner_scores[C] = float(language_equal_loss(train, p))
            best = min(GRID, key=lambda c: (round(inner_scores[c], 12), c))
            log = {}
            preds[f'{model}_nested'][ite] = fit_predict(train, test, model, best, log)
            log1 = {}
            preds[f'{model}_C1'][ite] = fit_predict(train, test, model, 1, log1)
            selection.append({'outer_fold':k,'model':model,'selected_C':best,
                              'train_families':int(train.family_group.nunique()),'test_families':int(test.family_group.nunique()),
                              'converged_nested':log['converged'],'converged_C1':log1['converged'],
                              'design_rank':log['design_rank'],
                              **{f'inner_loss_C{c}':inner_scores[c] for c in GRID}})
            print(f'外层折{k} {model}: 选中C={best}', flush=True)

    y = data.shared_form.to_numpy()
    scores = data[['Glottocode','Language_ID','family_group','family_name']].drop_duplicates('Glottocode').set_index('Glottocode')
    for key, p in preds.items():
        assert not np.isnan(p).any()
        s = pd.DataFrame({'Glottocode':data.Glottocode, 'loss':logloss(y, p), 'brier':(p-y)**2}).groupby('Glottocode').mean()
        scores['loss_'+key] = s['loss']; scores['brier_'+key] = s['brier']
    scores = scores.reset_index()

    # 固定C=1的M0、M1、M2须重现冻结主分析
    check = {'M0':'raw_additive','M1':'classical_additive','M2':'pairwise'}
    reproduction = {m: abs(scores['loss_'+m+'_C1'].mean() - primary['language_equal_logloss'][f]) for m, f in check.items()}
    assert max(reproduction.values()) < 1e-9, reproduction

    results = {'protocol':'protocol_s1.md',
               'protocol_sha256':hashlib.sha256((HERE/'protocol_s1.md').read_bytes()).hexdigest(),
               'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'started_utc':started,'python':sys.version.split()[0],
               'languages':int(data.Glottocode.nunique()),'family_groups':int(data.family_group.nunique()),'pairs':len(data),
               'reproduction_of_frozen_C1_max_abs_error':max(reproduction.values()),
               'grid':GRID,'settings':{}}
    largest = scores.family_group.value_counts().idxmax()
    for setting in ['nested','C1']:
        block = {'language_equal_logloss':{m: float(scores[f'loss_{m}_{setting}'].mean()) for m in MODELS},
                 'language_equal_brier':{m: float(scores[f'brier_{m}_{setting}'].mean()) for m in MODELS},
                 'comparisons':{}}
        for base, alt in COMPARISONS:
            col = f'gain_{base}_minus_{alt}_{setting}'
            scores[col] = scores[f'loss_{base}_{setting}'] - scores[f'loss_{alt}_{setting}']
            fam = scores.groupby('family_group')[col].mean()
            block['comparisons'][f'{base}-{alt}'] = {
                'gain':float(scores[col].mean()),'family_cluster_bootstrap_95ci':bootstrap(scores, col),
                'gain_excluding_largest_family':float(scores.loc[scores.family_group!=largest, col].mean()),
                'families_positive':int((fam>0).sum()),'families_negative':int((fam<0).sum())}
        results['settings'][setting] = block
    results['largest_family'] = largest
    sel = pd.DataFrame(selection)
    results['selected_C'] = {m: sel.loc[sel.model==m, 'selected_C'].tolist() for m in MODELS}
    results['all_fits_converged'] = bool(sel.converged_nested.all() and sel.converged_C1.all())
    results['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    sel.to_csv(HERE/'s1_fold_selection.csv', index=False)
    scores.to_csv(HERE/'s1_language_scores.csv', index=False)
    (HERE/'s1_results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2))
    write_report(results)
    print(json.dumps(results['settings'], ensure_ascii=False, indent=1))

def write_report(r):
    lines = ['# 补充分析S1结果', '',
             f'协议：`protocol_s1.md`（SHA-256 `{r["protocol_sha256"][:16]}…`），运行开始 {r["started_utc"]}。本分析写于冻结结果已知之后，属补充分析，不替代冻结的 `C=1` 主比较。', '',
             f'主样本 {r["languages"]} 个系统、{r["family_groups"]} 个谱系组、{r["pairs"]:,} 个类别对；外层折与冻结分析逐对一致；固定 `C=1` 时 M0、M1、M2 重现冻结损失，最大误差 {r["reproduction_of_frozen_C1_max_abs_error"]:.1e}。全部拟合收敛：{r["all_fits_converged"]}。', '',
             '## 各外层折选中的惩罚', '', '| 模型 | 折0–4选中的C |', '|---|---|']
    for m in MODELS:
        lines.append(f'| {ZH[m]} | {", ".join(str(c) for c in r["selected_C"][m])} |')
    for setting, title in [('nested','嵌套调参'),('C1','固定 C=1')]:
        b = r['settings'][setting]
        lines += ['', f'## {title}', '', '| 模型 | 语言等权对数损失 | Brier |', '|---|---:|---:|']
        for m in MODELS:
            lines.append(f'| {ZH[m]} | {b["language_equal_logloss"][m]:.6f} | {b["language_equal_brier"][m]:.6f} |')
        lines += ['', '| 比较（基准−比较模型） | 增益 | 95%谱系区间 | 去除最大组 | 正／负谱系组 |', '|---|---:|---|---:|---|']
        for k, v in b['comparisons'].items():
            lo, hi = v['family_cluster_bootstrap_95ci']
            lines.append(f'| {k} | {v["gain"]:.6f} | [{lo:.6f}, {hi:.6f}] | {v["gain_excluding_largest_family"]:.6f} | {v["families_positive"]}／{v["families_negative"]} |')
    lines += ['', '区间按谱系组整组重采样固定折外预测得到，不含重训与重新划折的不确定性。M2−M3 衡量七差异单元之外的类别对层面结构所能带来的样本外预测改善，不解释其来源。', '']
    (HERE/'s1_report.md').write_text('\n'.join(lines))

if __name__ == '__main__':
    main()
