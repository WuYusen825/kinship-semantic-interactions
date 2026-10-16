"""T1：建立共同划分／描述成本／系统映射并实际运行基础设施单测。"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import traceback

import numpy as np
import pandas as pd

from common import (ATOMS,CATEGORY_ORDER,FEATURES,KINTYPES,RESULTS,ROOT,SEED,
                    git_commit,load_base_data,log_run,pair_design_metadata,
                    save_json,sha256,utc_now,verify_t0)
from languages import LANGUAGES,conjunction_extents,is_conjunctive,minimum_dnf,minimum_dnf_witness,partition_dl
from partitions import (blocks_to_rgs,canonical_rgs,enumerate_rgs,partition_catalogue,
                        partition_id_map,rgs_string,rgs_to_blocks)
from structural_enumeration import enumerate_partitions,is_conjunctive as old_is_conjunctive

OUT=RESULTS/'t1'
DEFINITIONS={
 'strict':'每个目标类别恰有一个词形；相同词形的八个位置构成划分。',
 'equal_sets':'全部939系统；两个位置的完整规范化词形集合相等时属于同类。',
 'components':'全部939系统；以D1词形集合交集边构图，取共享图连通分量。不是原D1关系本身。'}
FILES={'strict':'systems_to_partition.csv','equal_sets':'systems_set_equal.csv','components':'systems_components.csv'}


def make_catalogue():
    records=[];old_blocks=set(enumerate_partitions());cross=0
    for row in partition_catalogue():
        row=dict(row);blocks=row['blocks']
        if blocks not in old_blocks:raise RuntimeError('RGS枚举出现旧4140支持外的划分。')
        if sum(int(row[p]!=0) for p in ['P2','P3','P4'])>1:
            raise RuntimeError('旧严格P2–P4非零支持并非互斥，须报告定义冲突。')
        for language,features in LANGUAGES.items():
            row['conj_'+language]=is_conjunctive(blocks,language)
            old=old_is_conjunctive(blocks,features)
            if row['conj_'+language]!=old:raise RuntimeError('新旧合取函数不一致。')
            cross+=1;row['DL_'+language]=partition_dl(blocks,language)
        records.append(row)
    if len(records)!=4140 or {r['blocks'] for r in records}!=old_blocks:raise RuntimeError('划分支持未完整重现4140。')
    return records,cross


def serialize_catalogue(records):
    flat=[]
    for record in records:
        row={k:v for k,v in record.items() if k not in ['blocks','labels','s2_labels','shape']}
        for name in ['blocks','labels','s2_labels','shape']:row[name+'_json']=json.dumps(record[name])
        flat.append(row)
    return pd.DataFrame(flat)


def connected_labels(formsets):
    parent=list(range(8))
    def find(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i in range(8):
        for j in range(i+1,8):
            if formsets[i]&formsets[j]:parent[find(j)]=find(i)
    return canonical_rgs(tuple(find(i) for i in range(8)))


def make_system_mappings(base):
    mapping={name:[] for name in FILES};ids=partition_id_map();forms=base['forms']
    for meta in base['systems'].sort_values(['Glottocode','Language_ID']).to_dict('records'):
        lid=meta['Language_ID'];sets=tuple(forms[(lid,c)] for c in CATEGORY_ORDER)
        if any(not fs for fs in sets):raise RuntimeError('主样本存在空目标词形集合。')
        partitions={'equal_sets':canonical_rgs(sets),'components':connected_labels(sets)}
        if all(len(fs)==1 for fs in sets):partitions['strict']=canonical_rgs(tuple(next(iter(fs)) for fs in sets))
        form_record={c:sorted(fs) for c,fs in zip(CATEGORY_ORDER,sets)}
        for sample,rgs in partitions.items():
            blocks=rgs_to_blocks(rgs)
            mapping[sample].append({**meta,'system_id':lid,'family':meta['family_group'],
                  'sample':sample,'definition':DEFINITIONS[sample],
                  'forms_json':json.dumps(form_record,ensure_ascii=False,sort_keys=True),
                  'partition_id':ids[rgs],'rgs':rgs_string(rgs),'k':max(rgs)+1,
                  'labels_json':json.dumps(rgs),'blocks_json':json.dumps(blocks),
                  'shape_json':json.dumps(sorted(b.bit_count() for b in blocks))})
    tables={name:pd.DataFrame(rows) for name,rows in mapping.items()}
    for name,expected in [('strict',625),('equal_sets',939),('components',939)]:
        if len(tables[name])!=expected:raise RuntimeError('映射样本数不符：'+name)
        if not tables[name].groupby('family_group').fold_family.nunique().eq(1).all():raise RuntimeError('映射中的旧谱系折被改变。')
    if tables['strict'].family_group.nunique()!=108:raise RuntimeError('严格样本谱系组不是108。')
    by_pair={(r.Language_ID,r.category_a,r.category_b):bool(r.shared_form) for r in base['pairs'].itertuples(index=False)}
    for (lid,a,b),shared in by_pair.items():
        if bool(forms[(lid,a)]&forms[(lid,b)])!=shared:raise RuntimeError('主类别集合与冻结D1不一致。')
    return tables


def write_cell_coding():
    lines=['# 八位置、划分编码与描述成本','',
           '以下位序完整沿用S2的`ATOMS`与`KINTYPES`。s/a/r的0依次表示男性参照者、所指者年长、男性所指者；q=s XOR r，q=0表示同性。mask中的第i位为位置i。数据表的排列次序不作为逻辑位置次序。','',
           '| 位置i | s | a | r | q | Kinbank类别 | S2类别 |','|---:|---:|---:|---:|---:|---|---|']
    for i,((s,a,r),category,oldcode) in enumerate(zip(ATOMS,CATEGORY_ORDER,KINTYPES)):
        lines.append(f'| {i} | {s} | {a} | {r} | {s^r} | {category} | {oldcode} |')
    lines+=['','## 划分ID与块表示','',
            'RGS按首次出现的块依次编号0、1、…，以八位字符串保存；全部合法RGS按字典序分配partition_id=0–4139。块mask按整数升序保存，因而与S2的canonical_partition一致；labels为上述位序的RGS，s2_labels另保存旧函数按mask升序编号的类标签。两种标签的数字名称可以不同，同类关系完全相同。读取CSV应强制rgs为字符串，保留前导零。','',
            '例：仅按所指者性别区分的RGS为01010101，块mask为85与170；仅按同性／异性区分的RGS为01011010，块mask为90与165。不要将RGS中的类编号误作亲属属性。','',
            '## 四种描述语言和成本','',
            'L_abs={s,a,r}；L_rel_r={q,a,r}；L_rel_s={q,a,s}；L_all={s,a,r,q}。精确DL为各词项块最短DNF的文字数之和；真式即全集的文字数为0。合取项允许重叠，文字成本按每项的特征取值数相加，不另给括号、连接符或词项名称计费。该DNF成本与旧S2最小分类树边数是不同指标。','',
            '## 三种系统映射与分折','',
            'strict是625个每类单词形系统；equal_sets对939系统取完整词形集合相等的等价类；components对939系统取D1共享图的连通分量。后两者都不是把非传递D1关系直接当作划分。每行保留按类别存储的forms_json、定义文本与来源样本标识。','',
            'fold_family和fold_language从原939系统的冻结primary预测读取并逐系统继承，不对625子样本重新平衡。macroarea/Macroarea_first均为首个原始宏观区域，缺失保持空串；Macroarea与macroarea_raw保存原字段。地域缺失系统只从地域验证排除。','',
            '类别对索引见results/t1/pair_design_metadata.csv，其pair_index按旧pair_type字符串排序；atom_i/atom_j连接本表位置。旧七差异单元的位次仍为Dr、Da、De，M2列仍为intercept、Dr、Da、De、DrDa、DrDe、DaDe。','']
    path=ROOT/'docs/cell_coding.md';path.parent.mkdir(parents=True,exist_ok=True);path.write_text('\n'.join(lines),encoding='utf-8')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    spec={'scope':'T1共同基础库','seed':SEED,'DNF':'精确集合覆盖文字数，全集0','samples':['strict','equal_sets','components']}
    log_run('T1',spec,{},'started')
    result={'task':'T1','started_utc':utc_now(),'passed':False,'commit':git_commit()}
    save_json(OUT/'build_manifest.json',result)
    try:
        result['baseline']=verify_t0()
        catalogue,crosschecks=make_catalogue();table=serialize_catalogue(catalogue)
        table.to_csv(OUT/'partitions.csv',index=False)
        save_json(OUT/'partitions.json',catalogue)
        parquet_available=importlib.util.find_spec('pyarrow') is not None
        if parquet_available:
            parquet=table.copy()
            for name in ['blocks','labels','s2_labels','shape']:parquet[name]=[list(r[name]) for r in catalogue]
            parquet.to_parquet(OUT/'partitions.parquet',index=False,engine='pyarrow')
        result['parquet_written']=parquet_available
        base=load_base_data();mappings=make_system_mappings(base)
        sample_metrics={}
        for sample,mapping in mappings.items():
            mapping.to_csv(OUT/FILES[sample],index=False)
            sample_metrics[sample]={'systems':len(mapping),'families':int(mapping.family_group.nunique()),
                                   'missing_macroarea_systems':int(mapping.macroarea.eq('').sum()),
                                   'unique_partitions':int(mapping.partition_id.nunique())}
        pair_design_metadata().to_csv(OUT/'pair_design_metadata.csv',index=False)
        subsets=[]
        for language in LANGUAGES:
            extents=conjunction_extents(language)
            for mask in range(1,256):
                subsets.append({'language':language,'mask':mask,'conjunctive':mask in extents,
                                'minimum_dnf_literals':minimum_dnf(mask,language),
                                'witness_terms':minimum_dnf_witness(mask,language)})
        save_json(OUT/'subset_description_costs.json',subsets)
        write_cell_coding()
        strict=mappings['strict'].merge(table[['partition_id','conj_abs','conj_all']],on='partition_id',validate='many_to_one')
        observed={'abs_nonconjunctive':int((~strict.conj_abs).sum()),'all_nonconjunctive':int((~strict.conj_all).sum())}
        if observed!={'abs_nonconjunctive':163,'all_nonconjunctive':22}:raise RuntimeError('T1观测合取基线不符。')
        command=[sys.executable,'-m','unittest','discover','-s','tests','-p','test_v3_infrastructure.py','-v']
        log_run('T1_tests',{'command':command},{},'started')
        test=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
        (OUT/'infrastructure_tests.log').write_text(test.stdout+test.stderr,encoding='utf-8')
        log_run('T1_tests',{'command':command},{'exit_code':test.returncode,'log':'results/t1/infrastructure_tests.log'},'passed' if test.returncode==0 else 'failed')
        if test.returncode:raise RuntimeError('基础设施单元测试未通过，见infrastructure_tests.log。')
        result.update(passed=True,partition_count=len(table),old_conjunction_crosschecks=crosschecks,
                      direction_supports_nonzero_mutually_exclusive=True,samples=sample_metrics,observed_checks=observed,
                      tests_passed=True,tests_command=command,
                      parquet_status='已生成Parquet' if parquet_available else '未安装pyarrow；CSV/JSON和全部检查已完成，Parquet待统一依赖安装后补')
    except Exception as exc:
        result['error']=str(exc);result['traceback']=traceback.format_exc()
    finally:
        result['finished_utc']=utc_now()
        result['source_sha256']={name:sha256(Path(__file__).parent/name) for name in ['common.py','partitions.py','languages.py','build_t1.py']}
        result['output_sha256']={p.name:sha256(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='build_manifest.json'}
        save_json(OUT/'build_manifest.json',result)
        log_run('T1',spec,{k:result.get(k) for k in ['passed','partition_count','samples','observed_checks','parquet_written','error']},'passed' if result['passed'] else 'failed')
    print(json.dumps({k:result.get(k) for k in ['passed','partition_count','samples','observed_checks','parquet_written','error']},ensure_ascii=False,indent=2))
    if not result['passed']:raise SystemExit(1)


if __name__=='__main__':main()
