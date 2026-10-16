"""T7: inspect fixed classification trees and state coverage, without fitting Mk."""
from __future__ import annotations
import re
from dataclasses import dataclass,field
from pathlib import Path
import pandas as pd
from common import ROOT,RESULTS,load_system_mapping,save_json,logged_run,verify_analysis_plan

@dataclass
class Node:
    name: str=''
    length: float|None=None
    children: list=field(default_factory=list)

def parse_newick(text):
    tokens=re.findall(r"[A-Za-z0-9_.+\-]+|[(),:;]",text);pos=0
    def parse():
        nonlocal pos
        children=[]
        if tokens[pos]=='(':
            pos+=1
            while True:
                children.append(parse())
                if tokens[pos]==',':pos+=1;continue
                if tokens[pos]!=')':raise ValueError('Unbalanced tree')
                pos+=1;break
        name=''
        if pos<len(tokens) and tokens[pos] not in ',):;':name=tokens[pos];pos+=1
        length=None
        if pos<len(tokens) and tokens[pos]==':':pos+=1;length=float(tokens[pos]);pos+=1
        return Node(name,length,children)
    tree=parse()
    if pos!=len(tokens)-1 or tokens[pos]!=';':raise ValueError('Trailing tree input')
    return tree

def walk(node):
    yield node
    for child in node.children:yield from walk(child)

def inspect():
    gate=verify_analysis_plan()
    with logged_run('T7',{'phase':'feasibility_only','Mk_fitted':False,'source':'fixed_Glottolog_classification'},) as metrics:
        text=(ROOT/'data/v3/classification.nex').read_text()
        trees={name:parse_newick(newick.strip()) for name,newick in re.findall(r'tree\s+(\w+)\s*=\s*\[&R\]\s*(.*?;)',text,re.I)}
        meta=pd.read_csv(ROOT/'data/v3/trees.csv',keep_default_na=False)
        systems=load_system_mapping('strict');catalogue=pd.read_csv(RESULTS/'t1/partitions.csv')
        byid=catalogue.set_index('partition_id')
        systems['nonconj_all']=systems.partition_id.map(1-byid.conj_all.astype(int))
        systems['k']=systems.partition_id.map(byid.k)
        systems['k_bin']=pd.cut(systems.k,[0,2,4,8],labels=['1–2','3–4','5–8']).astype(str)
        systems['coarse_state']=systems.nonconj_all.map({0:'合取',1:'非合取'})+'_'+systems.k_bin
        state_counts=systems.coarse_state.value_counts().to_dict()
        lengths=[n.length for root in trees.values() for n in walk(root) if n.length is not None]
        coverage=[]
        for family,g in systems.groupby('family_group'):
            root=trees.get(family);nodes={n.name:n for n in walk(root)} if root else {}
            matched=[code for code in g.Glottocode if code in nodes]
            coverage.append({'family_group':family,'family_name':g.family_name.iloc[0],
                'strict_systems':len(g),'matched_tree_nodes':len(matched),'matched_internal_nodes':sum(bool(nodes[c].children) for c in matched),
                'nonconj_systems':int(g.nonconj_all.sum()),'states':g.coarse_state.value_counts().to_dict(),
                'tree_available':root is not None})
        result={'gate':gate,'trees':len(trees),'metadata_trees':len(meta),'branch_lengths':len(lengths),
            'unique_branch_lengths':sorted(set(lengths)),'branch_length_units':meta.Tree_Branch_Length_Unit.value_counts().to_dict(),
            'strict_systems':len(systems),'strict_families':systems.family_group.nunique(),
            'state_coarsening':'conj_all × k bins [1–2,3–4,5–8], at most 6 states','state_counts':state_counts,
            'coverage':coverage,'Mk_fitted':False,
            'decision':'本轮T7仅完成可行性：固定来源只有分类拓扑及人为单位枝长，未取得可匹配的可靠时间标定树；非合取状态稀少且多族缺少变化，不把可选Mk拟合作为第三版的历史机制证据。',
            'approximations':['保留原拓扑单位枝长；只解释每分类边的相对速率','按采样叶数Grafen高度（ρ=.5/1/2）生成近似枝长；检验拓扑与取样敏感性'],
            'followup':'先取得可追溯的时间标定语系树并解决内部节点语言与方言取样；之后另行固定根状态/速率参数、状态合并及比较ER/ARD/受限模型，未在本轮运行或报告AIC。'}
        out=RESULTS/'t7';out.mkdir(exist_ok=True)
        save_json(out/'feasibility.json',result)
        pd.DataFrame([{**x,'states':str(x['states'])} for x in coverage]).to_csv(out/'family_coverage.csv',index=False)
        systems[['Language_ID','Glottocode','family_group','k','nonconj_all','coarse_state']].to_csv(out/'proposed_states.csv',index=False)
        usable=[x for x in coverage if x['strict_systems']>=10 and x['nonconj_systems']>0]
        lines=['# T7谱系分析可行性与本轮决定','','用户已授权自主处理决策点。本报告完成输入核查，不拟合Mk，不产生或筛选AIC。','',
          f'固定版本Glottolog含{len(trees)}棵分类树；文件明确标作classification。全部{len(lengths)}个已写枝长均为1，Tree_Branch_Length_Unit全缺失。`:1`是分类边的单位编码，不是已测年代。',
          '',f'严格样本为{len(systems)}系统、{systems.family_group.nunique()}谱系组。暂拟“合取/非合取×k的1–2、3–4、5–8层”最多六态：{state_counts}。其中非合取仅22系统，可能造成多态全异速率参数极不稳定。至少10系统且含非合取的谱系组共{len(usable)}个；完整覆盖含内部节点匹配数见results/t7/family_coverage.csv。',
          '', '## 可行近似与后续设计','','单位枝长及Grafen枝长均可构造，后者可预设ρ=.5/1/2。应分别修剪到真实采样语言、保留多分叉、处理被采语言同时是内部节点的情形，并在六态过稀时采用事先固定的二态方案；根状态固定为平稳或自由参数需事先选择。近似所得速率只以人为树尺度计量。',
          '', '## 本轮决定','','本轮不运行可选Mk：现有固定输入无法提供可靠演化时间，且稀有非合取状态使多态速率缺乏信息。第三版只把历史传承作为由文献支持、尚待本数据直接检验的解释，不能以本可行性报告支持方向性转移结论。若Claude决定继续近似Mk，须将其明确标为拓扑假设下的探索性敏感性；更优路径是先取得可追溯时间标定树及其不确定性样本，再执行ER/ARD/转入非合取受限模型比较。',
          '', '来源：data/v3/source_manifest.json记录固定commit、下载URL和逐文件SHA，原数据与旧分析未覆盖。']
        (ROOT/'docs/t7_feasibility.md').write_text('\n'.join(lines)+'\n')
        metrics.update(trees=len(trees),unique_lengths=sorted(set(lengths)),Mk_fitted=False)
    return result

if __name__=='__main__':inspect()
