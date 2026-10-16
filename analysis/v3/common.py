"""第三版共享路径、执行门、锁定日志、原数据和固定折；不写旧分析。"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime,timezone
import csv
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
S2=ROOT/'analysis/supplementary_s2'
RESULTS=ROOT/'results'
SEED=20261016
BOOTSTRAP_REPLICATES=5000
PLAN_PATH=ROOT/'docs/analysis_plan.md'
PLAN_LOCK_PATH=ROOT/'docs/analysis_plan_lock.json'
if str(S2) not in sys.path:sys.path.insert(0,str(S2))
from structural_enumeration import ATOMS,KINTYPES,FEATURES

CATEGORY_ORDER=tuple('mf'[s]+'ey'[a]+'BZ'[r] for s,a,r in ATOMS)
CATEGORY_INDEX={name:i for i,name in enumerate(CATEGORY_ORDER)}
SAMPLE_FILES={'strict':'systems_to_partition.csv','equal_sets':'systems_set_equal.csv','components':'systems_components.csv'}


def utc_now():return datetime.now(timezone.utc).isoformat()
def sha256(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def git_commit():return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()


def json_default(value):
    if isinstance(value,(np.integer,)):return int(value)
    if isinstance(value,(np.floating,)):return float(value)
    if isinstance(value,(np.bool_,)):return bool(value)
    if isinstance(value,(np.ndarray,)):return value.tolist()
    if isinstance(value,Path):return str(value)
    raise TypeError(type(value).__name__)


def save_json(path,value):
    target=Path(path);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=json_default,allow_nan=False),encoding='utf-8')


def log_run(task,spec,metrics,status=None):
    """使用进程级文件锁追加；与既有T0日志五列保持兼容。"""
    path=RESULTS/'run_log.csv';path.parent.mkdir(parents=True,exist_ok=True)
    specification=dict(spec) if isinstance(spec,dict) else {'specification':spec}
    if status is not None:specification['status']=status
    row={'time':utc_now(),'task':task,'spec':json.dumps(specification,ensure_ascii=False,default=json_default,allow_nan=False),
         'metrics':json.dumps(metrics,ensure_ascii=False,default=json_default,allow_nan=False),'commit':git_commit()}
    columns=['time','task','spec','metrics','commit']
    with path.open('a+',encoding='utf-8',newline='') as handle:
        fcntl.flock(handle.fileno(),fcntl.LOCK_EX)
        handle.seek(0);first=handle.readline()
        if first and next(csv.reader([first]))!=columns:raise RuntimeError('运行日志列名不匹配，拒绝覆盖。')
        handle.seek(0,os.SEEK_END);writer=csv.DictWriter(handle,fieldnames=columns)
        if not first:writer.writeheader()
        writer.writerow(row);handle.flush();os.fsync(handle.fileno())
        fcntl.flock(handle.fileno(),fcntl.LOCK_UN)


@contextmanager
def logged_run(task,spec):
    metrics={};log_run(task,spec,{},'started')
    try:
        yield metrics
    except Exception as exc:
        metrics['error']=str(exc);log_run(task,spec,metrics,'failed');raise
    else:log_run(task,spec,metrics,'completed')


def verify_t0():
    data=json.loads((RESULTS/'baseline/reproduction_results.json').read_text())
    if data.get('passed') is not True:raise RuntimeError('T0未通过，不能进入新增任务。')
    subprocess.run(['git','rev-parse','--verify','refs/tags/baseline-v1'],cwd=ROOT,check=True,capture_output=True)
    return {'T0_passed':True,'baseline_result_sha256':sha256(RESULTS/'baseline/reproduction_results.json'),
            'baseline_tag_commit':subprocess.check_output(['git','rev-list','-n','1','baseline-v1'],cwd=ROOT,text=True).strip()}


def verify_analysis_plan(require_t1=True):
    """T2–T7入口：须有根代理在计划独立提交后写定的commit/SHA锁文件。"""
    baseline=verify_t0()
    if not PLAN_LOCK_PATH.exists():raise RuntimeError('缺少docs/analysis_plan_lock.json；不能开始T2–T7。')
    lock=json.loads(PLAN_LOCK_PATH.read_text())
    commit=lock.get('commit',lock.get('plan_commit'))
    expected=lock.get('sha256',lock.get('plan_sha256'))
    if not commit or not expected:raise RuntimeError('计划锁文件缺少commit或sha256。')
    observed=sha256(PLAN_PATH)
    if observed!=expected:raise RuntimeError('当前分析计划与已锁定SHA不符。')
    payload=subprocess.check_output(['git','show',f'{commit}:docs/analysis_plan.md'],cwd=ROOT)
    if hashlib.sha256(payload).hexdigest()!=expected:raise RuntimeError('计划提交对象内容不符。')
    subprocess.run(['git','merge-base','--is-ancestor',commit,'HEAD'],cwd=ROOT,check=True,capture_output=True)
    if require_t1:
        t1=json.loads((RESULTS/'t1/build_manifest.json').read_text())
        if t1.get('passed') is not True:raise RuntimeError('T1建库检查尚未通过。')
    return {**baseline,'plan_commit':commit,'plan_sha256':observed,'plan_commit_time':subprocess.check_output(['git','show','-s','--format=%cI',commit],cwd=ROOT,text=True).strip()}


def load_base_data():
    pairs=pd.read_csv(ROOT/'analysis/pairs_primary.csv',keep_default_na=False,dtype={'pattern':str})
    categories=pd.read_csv(ROOT/'analysis/category_forms_primary.csv',keep_default_na=False)
    forms={(r.Language_ID,r.Parameter_ID):frozenset(json.loads(r.forms_json)) for r in categories.itertuples(index=False)}
    keys=['Language_ID','Glottocode','Name','family_group','family_name','family_status','Macroarea']
    systems=pairs[keys].drop_duplicates().reset_index(drop=True)
    if len(systems)!=939 or len(pairs)!=26292 or systems.family_group.nunique()!=125:raise RuntimeError('主样本规模与T0不一致。')
    systems['macroarea_raw']=systems.Macroarea
    systems['macroarea']=systems.Macroarea.str.split(';').str[0].str.strip()
    systems['Macroarea_first']=systems.macroarea
    old=pd.read_csv(ROOT/'analysis/oof_predictions.csv',usecols=['variant','cv_grouping','Language_ID','fold'])
    for mode in ['family','language']:
        mapping=old[old.variant.eq('primary')&old.cv_grouping.eq(mode)][['Language_ID','fold']].drop_duplicates()
        if mapping.Language_ID.duplicated().any():raise RuntimeError('旧分折含同系统多个测试折。')
        systems['fold_'+mode]=systems.Language_ID.map(mapping.set_index('Language_ID').fold)
        if systems['fold_'+mode].isna().any():raise RuntimeError('旧分折映射缺少系统。')
        systems['fold_'+mode]=systems['fold_'+mode].astype(int)
    if not systems.groupby('family_group').fold_family.nunique().eq(1).all():raise RuntimeError('旧语系折不满足谱系隔离。')
    if not set(systems.fold_family)==set(range(5)) or not set(systems.fold_language)==set(range(5)):raise RuntimeError('主样本没有完整五折。')
    pairs['atom_i']=pairs.category_a.map(CATEGORY_INDEX);pairs['atom_j']=pairs.category_b.map(CATEGORY_INDEX)
    return {'pairs':pairs,'systems':systems,'forms':forms}


def load_partition_table():
    table=pd.read_csv(RESULTS/'t1/partitions.csv',dtype={'rgs':str})
    for col in ['blocks','labels','s2_labels','shape']:
        table[col]=table[col+'_json'].map(lambda v:tuple(json.loads(v)))
    return table


def load_system_mapping(sample='strict'):
    aliases={'D3':'strict','D2':'equal_sets','set_equal':'equal_sets','connected_components':'components'}
    name=aliases.get(sample,sample)
    if name not in SAMPLE_FILES:raise ValueError('未知系统划分样本：'+str(sample))
    result=pd.read_csv(RESULTS/'t1'/SAMPLE_FILES[name],keep_default_na=False,dtype={'rgs':str})
    result['partition_id']=result.partition_id.astype(int)
    return result


def system_weights(systems,weighting='family'):
    """返回和为1的系统级权重，适用于加权平均目标与评分。"""
    n=len(systems)
    if not n:raise ValueError('不能给空系统表加权。')
    if weighting in ['language','system','system_equal','unweighted','none']:
        return np.full(n,1/n)
    if weighting not in ['family','family_equal']:raise ValueError('未知权重：'+weighting)
    groups=systems.family_group
    counts=groups.value_counts()
    if groups.eq('').any() or groups.isna().any():raise ValueError('谱系权重缺少分组。')
    return 1/(len(counts)*groups.map(counts).to_numpy(dtype=float))


def bootstrap_grouped(values,groups,weighting='family',replicates=BOOTSTRAP_REPLICATES,seed=SEED):
    frame=pd.DataFrame({'value':np.asarray(values,dtype=float),'group':np.asarray(groups)})
    if not len(frame) or not np.isfinite(frame.value).all():raise ValueError('自助输入为空或含无效数值。')
    group=frame.groupby('group').value.agg(['mean','sum','count'])
    idx=np.random.default_rng(seed).integers(0,len(group),size=(replicates,len(group)))
    if weighting in ['family','family_equal']:
        draws=group['mean'].to_numpy()[idx].mean(axis=1);estimate=group['mean'].mean()
    elif weighting in ['language','system','system_equal','unweighted','none']:
        draws=group['sum'].to_numpy()[idx].sum(axis=1)/group['count'].to_numpy()[idx].sum(axis=1);estimate=frame.value.mean()
    else:raise ValueError('未知自助权重。')
    return {'estimate':float(estimate),'ci95':np.quantile(draws,[.025,.975]).tolist(),'replicates':replicates,'seed':seed,
            'groups':len(group),'scope':'条件于现有分数的整谱系重抽，不包含模型重训或划折变化。'}


def pair_design_metadata():
    pairs=load_base_data()['pairs']
    table=pairs[['category_a','category_b','atom_i','atom_j','Dr','Da','De','pattern']].drop_duplicates().copy()
    table['pair_type']=table.category_a+'|'+table.category_b
    table=table.sort_values('pair_type').reset_index(drop=True)
    table.insert(0,'pair_index',np.arange(len(table)))
    table['intercept']=1
    table['DrDa']=table.Dr*table.Da;table['DrDe']=table.Dr*table.De;table['DaDe']=table.Da*table.De
    if len(table)!=28:raise RuntimeError('类别对设计表不等于28行。')
    return table
