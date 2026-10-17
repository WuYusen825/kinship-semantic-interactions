#!/usr/bin/env python3
"""第三版人工审定数字映射的可复跑构建器；不搜索同值，不批准未知结果。"""
from __future__ import annotations
from collections import Counter
import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'analysis'))
from audit_manuscript_numbers import base as audit

MANUSCRIPT = ROOT / 'outputs/论文_中文第三版.md'
EXPECTED_MANUSCRIPT_SHA256 = 'ed7d19b6a403792879cbd69d54f7d596b25bc133a6437f7c9e6f3a94e2b8cc09'
if audit.sha256(MANUSCRIPT.read_bytes()) != EXPECTED_MANUSCRIPT_SHA256:
    raise SystemExit('第三版正文已变化：先逐处重审变化行，不得按旧行号重新批准数字。')
CLAIMS = ROOT / 'notes/v3/manuscript_number_claims.json'
SUMMARY = json.loads((ROOT / 'results/summary.json').read_text())
OLD = json.loads((ROOT / 'notes/formal_manuscript_number_claims.json').read_text())
REFS = json.loads((ROOT / 'notes/formal_references.json').read_text())
REGISTRY = json.loads((ROOT / 'outputs/文献登记表.json').read_text())
mapping = audit.synchronize(MANUSCRIPT, {}, ROOT)
claims = mapping['claims']
lines = MANUSCRIPT.read_text().splitlines()


def at(line, index):
    matches = [c for c in claims if c['anchor']['line'] == line and c['anchor']['numeric_index_on_line'] == index]
    if len(matches) != 1:
        raise ValueError((line, index, len(matches)))
    return matches[0]


def white(c, category, reason, evidence):
    c.update(kind='whitelist', label=reason, source=None, format=None,
             whitelist={'category': category, 'expected_token': c['anchor']['token'],
                        'reason': reason, 'evidence': evidence})


def structural(c, category, reason):
    white(c, category, reason, {'type': 'document_structure', 'explanation': reason})


def theoretical(line, index, reason, evidence_file=None, quote=None, category='theoretical_constant'):
    c = at(line, index)
    white(c, category, reason, {'file': evidence_file or 'outputs/论文_中文第三版.md',
                              'quote': quote or c['anchor']['line_text']})


def result(line, index, artifact, pointer, label, places=None, metric=None, guards=None):
    c = at(line, index)
    full = f'/artifacts/{artifact}/data{pointer}'
    audit.pointer_get(SUMMARY, full)  # 定位失败立即停止；不在其他位置寻找同值。
    source = {'file': 'results/summary.json', 'pointer': full,
              'sha256': audit.sha256((ROOT / 'results/summary.json').read_bytes())}
    if artifact == 'partition_models':
        guards = [*(guards or []), ('/solver_profile', 'refined')]
    if guards:
        source['guards'] = [{'pointer': f'/artifacts/{artifact}/data{p}', 'equals': v} for p, v in guards]
    c.update(kind='result', label=label, source=source,
             format={'kind': 'integer'} if places is None else {'kind': 'fixed', 'places': places},
             metric=metric or ('count' if places is None else 'estimate'))
    c.pop('whitelist', None)


def calculation(line, index, artifact, pointers, operation, label, places=None):
    c = at(line, index)
    c.update(kind='result', label=label, source=None,
             calculation={'operation': operation,
                          'operands': [{'file': 'results/summary.json',
                                        'pointer': f'/artifacts/{artifact}/data{p}'} for p in pointers]},
             calculation_reason=label,
             format={'kind': 'integer'} if places is None else {'kind': 'fixed', 'places': places},
             metric='count' if places is None else 'estimate')
    c.pop('whitelist', None)


# 只按整行、行内序号、字符串完全相同迁移旧非经验映射；绝不迁移旧结果值。
old_exact = {(c['anchor']['line_text'], c['anchor']['numeric_index_on_line'], c['anchor']['token']): c
             for c in OLD['claims'] if c['kind'] == 'whitelist'}
retained = 0
for c in claims:
    a = c['anchor']; old = old_exact.get((a['line_text'], a['numeric_index_on_line'], a['token']))
    if old:
        anchor, ident = c['anchor'], c['occurrence_id']
        c.update(copy.deepcopy(old)); c.update(anchor=anchor, occurrence_id=ident)
        c['v3_revalidation'] = '仅完整行及该行数字次序完全一致时迁移非经验依据；不迁移旧结果或旧通过状态。'
        retained += 1

# 模型/图号/标题编号仅在明确的语法位置识别，不把游离数字归为标识。
for c in claims:
    if c['kind'] != 'unresolved':
        continue
    a = c['anchor']; text = a['line_text']; start = a['column'] - 1
    left, right = text[:start], text[start + len(a['token']):]
    heading = re.match(r'^\s*#{1,6}\s*[（(]?([一二三四五六七八九十]+)[、）)]', text)
    if heading and start == heading.start(1) and a['token'] == heading.group(1):
        structural(c, 'ordinal', '第三版章、节的顺序编号；非样本量或模型估计。')
    elif re.search(r'(?:[AMP]|L)[~_{}]*$', left) and a['token'].isdigit():
        structural(c, 'model_identifier' if not left.endswith('P') else 'hypothesis_identifier',
                   '本处数字附着模型或预列方向符号，仅为该模型/方向的标识。')
    elif re.search(r'(?:图|表)$', left) and a['token'].isdigit():
        structural(c, 'ordinal', '本处是当前文稿图、表的编号或交叉指引，不是研究结果。')
    elif '../results/' in text and text[:start].count('](') > text[:start].count(')'):
        structural(c, 'definition_identifier', '插图相对路径内的任务/图号标识；对应已有图文件。')
    elif text.startswith('研究数据、完整分析规格') and 'https://' in text:
        white(c, 'url', '研究仓库URL内的用户名数字，非实测数值。',
              {'file': 'outputs/论文_中文第三版.md', 'quote': 'https://github.com/WuYusen825/kinship-semantic-interactions'})

# 参考文献整条与规范登记逐字相同，所有年份/卷期/页码/DOI数字绑定该唯一条目。
for c in claims:
    a = c['anchor']
    if a['line'] <= lines.index('## 参考文献') + 1:
        continue
    found = [(i, r) for i, r in enumerate(REFS) if r['entry'] == a['line_text']]
    if len(found) != 1:
        raise ValueError('书目未逐条匹配规范登记：' + a['line_text'])
    i, ref = found[0]
    white(c, 'bibliographic_number', f"参考文献{ref['id']}整条与已核规范书目一致；本处为该条的年份、卷期页或DOI数字。",
          {'file': 'notes/formal_references.json', 'pointer': f'/{i}/entry', 'expected_value': ref['entry'],
           'guards': [{'pointer': f'/{i}/id', 'equals': ref['id']}]})

# 作者—年份定位：作者串和a/b标签必须共同唯一匹配，不按年份同值搜索。
author_map = {'Kroeber':'A01','Goodenough':'A03','Lounsbury':'A04','Kronenfeld1974':'A06',
              'Kronenfeld2006':'A17','Hage1997':'A19','Hage2001':'A07','Faris':'A20',
              'Jordan':'A10','Pericliev':'A16','Rácz':'A12','Passmore & Jordan':'A13',
              'Guillon & Mace':'A11','Jones':'A14','Read':'A15','Hallam2025a':'B02',
              'Hallam2025b':'B03','Kemp & Regier':'B01','Kemp et al.':'B05','Kemp2012':'B10',
              'Kemp2026':'B04','Carr':'B12','Culbertson & Kirby':'B13','Mollica & Piantadosi':'B14',
              'Mollica et al.':'B15','Regier':'B08','Gibson':'B11','Zaslavsky2018':'B06','Zaslavsky2019':'B16',
              'François':'D01','Rzymski':'D02','Brochhagen & Boleda':'D03','Jackson':'D04','Xu':'D05',
              'Karjus':'D06','Forkel':'C11','Roberts':'C04','Cameron':'C12','Firth':'C06','Jaeger':'C01',
              'Passmore2023':'A09','Passmore2021':'A18'}


def work_id(author, year):
    author = author.strip()
    key = re.sub(r' et al\.$', '', author)
    combined = key + year
    if combined in author_map:
        return author_map[combined]
    if author in author_map:
        return author_map[author]
    return author_map[key]


for c in claims:
    if c['kind'] != 'unresolved':
        continue
    a = c['anchor']; start = a['column'] - 1
    for match in re.finditer(r'([^（；]+?)，(\d{4}[ab]?)', a['line_text']):
        if match.start(2) == start:
            author = match.group(1).split('。')[-1].split('（')[-1].strip()
            ident = work_id(author, match.group(2))
            entries = [(i, r) for i, r in enumerate(REGISTRY) if r['id'] == ident]
            if len(entries) != 1:
                raise ValueError((author, ident))
            i, r = entries[0]
            white(c, 'citation_year', f'按作者串及年份标签定位作品{ident}；本处是出版年，不是结果。',
                  {'file': 'outputs/文献登记表.json', 'pointer': f'/{i}/year', 'expected_value': r['year'],
                   'guards': [{'pointer': f'/{i}/id', 'equals': ident}]})
            break

# 页码依附的作者—年份和实际已核来源页定位，页码本身不能按同值迁移。
page_ledger = json.loads((ROOT / 'notes/discussion_expansion_20261016/expanded_citation_occurrences.json').read_text())
for c in claims:
    if c['kind'] != 'unresolved':
        continue
    a = c['anchor']; start = a['column'] - 1; text = a['line_text']
    if text[:start].count('^') % 2 != 1:
        continue
    before = text[:text.rfind('^', 0, start)]
    cite = re.search(r'（([^（）]+)）$', before)
    if not cite:
        continue
    author, year = cite.group(1).split('，')
    ident = work_id(author, year)
    page = int(a['token'])
    ledger_rows = [(i, r) for i, r in enumerate(page_ledger) if r['source_id'] == ident
                   and page in [int(v) for v in re.findall(r'\d+', str(r.get('printed_locator','')))]]
    if not ledger_rows:
        raise ValueError(('新页码尚无实物核验定位', ident, page))
    i, record = ledger_rows[0]
    white(c, 'citation_page', f'当前转述附着作品{ident}的已核印刷页；依作者身份与完整页范围匹配既有实际PDF页证据。',
          {'file': 'notes/discussion_expansion_20261016/expanded_citation_occurrences.json',
           'pointer': f'/{i}/printed_locator', 'expected_value': record['printed_locator'],
           'guards': [{'pointer': f'/{i}/source_id', 'equals': ident},
                      {'pointer': f'/{i}/review_status', 'equals': 'actual_clause_and_version_checked'}]})

# 下方为逐行人工核对过的结果角色；下标是该行的数字次序，不能按值重新配对。
result(8,1,'partitions','/samples/strict/systems','摘要主严格单词形划分系统数')
for line,index,pointer,label in [
    (60,4,'/samples/equal_sets/systems','主八类齐全记录系统数'),
    (60,6,'/samples/equal_sets/families','主资料谱系组数'),
    (62,2,'/samples/strict/systems','严格单词形系统数'),
    (62,3,'/samples/strict/families','严格单词形谱系组数'),
    (62,8,'/partition_count','八位置无标签划分空间大小'),
    (64,1,'/samples/equal_sets/systems','两种全样本映射各自覆盖的原系统数'),
    (72,4,'/samples/strict/systems','候选富集度的观测系统分母'),
    (72,5,'/partition_count','候选富集度的理论划分分母'),
    (80,2,'/partition_count','A0均匀分布覆盖的全部划分数'),
    (102,1,'/samples/strict/systems','非合取统计的严格系统分母'),
    (102,2,'/observed_checks/abs_nonconjunctive','绝对基底非合取系统数'),
    (102,4,'/observed_checks/all_nonconjunctive','四特征基底非合取系统数')]:
    result(line,index,'partitions',pointer,label)
calculation(60,7,'baseline',['/checks/2/recomputed_value','/checks/0/recomputed_value'],'ratio','每系统无序类别对数=总类别对数/主系统数')
result(102,6,'baseline','/checks/9/recomputed_value','六特征扩展下非合取系统数',guards=[('/checks/9/label','非合取系统：six')])

for line,language,row_index in [(108,'abs',16),(109,'rel_r',17),(110,'rel_s',18),(111,'all',19)]:
    offset = 1 if line != 111 else 2
    result(line,offset,'partitions',f'/observed_language_summary/{language}/conjunctive_systems',f'{language}基底合取系统计数')
    result(line,offset+1,'basis',f'/description_cost/rows/{row_index}/mean_DL',f'{language}基底谱系等权平均最小描述长度',4,
           guards=[(f'/description_cost/rows/{row_index}/weighting','family'),(f'/description_cost/rows/{row_index}/language',language),(f'/description_cost/rows/{row_index}/lambda',0)])
for index,pointer,label,places in [
    (3,'/q/N_system','q覆盖系统数',None),(4,'/q/C','q理论合取划分数',None),
    (5,'/q/E_system','q系统等权富集度',4),(6,'/q/rank_E_system_candidates','q在127候选中的系统富集排名',None),
    (7,'/absolute_baseline/C','绝对基底理论合取划分数',None),(8,'/absolute_baseline/E_system','绝对基底系统富集度',4),
    (10,'/q/shape_reference_expected_N','保持块大小参照下q覆盖系统数的精确期望',2),
    (12,'/q/shape_reference_N_pi95_low','q块大小参照95%预测区间下端',2),
    (13,'/q/shape_reference_N_pi95_high','q块大小参照95%预测区间上端',2),
    (14,'/symmetry_counts/value_preserving','全局性别互换后值保持的候选数',None),
    (16,'/symmetry_counts/block_swapping','全局性别互换后两块交换的候选数',None),
    (18,'/symmetry_counts/unlabeled_stable','两种无标签稳定候选的合计数',None)]:
    result(113,index,'basis',pointer,label,places)
result(119,5,'basis','/description_cost/crossings/10/lambda_crossing','谱系等权rel_r与all的库存成本交点',4,
       guards=[('/description_cost/crossings/10/weighting','family'),('/description_cost/crossings/10/left','rel_r'),('/description_cost/crossings/10/right','all')])

for line,model,index in [(125,'A0',2),(126,'A1',3),(127,'A2',2),(128,'A3r',2),(129,'A3s',2),
                         (130,'A4',2),(131,'A5r',2),(132,'A5s',2),(133,'A6',3),(134,'A7',2)]:
    result(line,index,'partition_models',f'/cv/strict_family_family/selected_models/{model}/mean_log_probability',
           f'严格625谱系等权谱系留出{model}的内层选择后每系统平均log概率',4)
base_cv='/cv/strict_family_family/selected_comparisons/'
for index,comp,key in [(1,'A3r-A2','gain'),(3,'A3r-A2','ci95/0'),(4,'A3r-A2','ci95/1'),
                       (5,'A5r-A4','gain'),(6,'A5r-A4','ci95/0'),(7,'A5r-A4','ci95/1'),
                       (8,'A3s-A2','gain'),(9,'A5s-A4','gain')]:
    result(138,index,'partition_models',base_cv+comp+'/'+key,f'主规格{comp}的留出增益及固定OOF谱系区间：{key}',4)
result(138,12,'partitions','/samples/equal_sets/systems','两种全样本映射各自系统量')
result(138,15,'partition_models','/completeness/cv_settings','实际完成全部3样本2权重3验证规格数')

for index,term,direction in [(1,'P2','predicted'),(2,'P2','opposite'),(3,'P3','predicted'),(4,'P3','opposite'),(5,'P4','predicted'),(6,'P4','opposite')]:
    result(142,index,'baseline',f'/directions/{term}/systems_{direction}',f'严格层级{term}的{direction}方向系统计数，非宽配置口径')
result(142,7,'positions','/subsets/overall/A_types/n_partial_systems','偏性年龄系统数')
result(142,8,'positions','/subsets/overall/G_types/n_partial_systems','偏性性别系统数')
for line,contrast in [(148,'A_i'),(149,'A_ii'),(150,'A_iii'),(151,'A_iv'),(152,'G_male_ego'),(153,'G_female_ego')]:
    for index,level,side in [(1,'system','left'),(2,'system','right'),(3,'family_contrast_majority','left'),(4,'family_contrast_majority','right')]:
        result(line,index,'positions',f'/subsets/overall/contrasts/{level}/{contrast}/{side}',f'{contrast}的{level}口径{side}计数')
    if line != 150:
        result(line,5,'positions',f'/subsets/overall/contrasts/family_contrast_majority/{contrast}/p_holm_six',f'{contrast}谱系方向多数的六项Holm p',4,'p_value')
result(155,2,'positions','/subsets/overall/contrasts/family_contrast_majority/A_iv/p_holm_six','仅男性/女性所指者对照的谱系Holm p',4,'p_value')
eq='/subsets/overall/equivalence_ii/family_direction_majority_primary/'
for i,key in [(3,'estimate'),(5,'ci95/0'),(6,'ci95/1')]:
    result(155,i,'positions',eq+key,'MM/FF主谱系方向差及其整谱系区间：'+key,2)

for index,key in [(2,'gain'),(4,'ci95/0'),(5,'ci95/1')]:
    result(157,index,'partition_models',base_cv+'A7-BASE/'+key,'主A7相对同折训练内选择基底的增益及固定OOF区间：'+key,4)
for index,term in [(9,'P2'),(10,'P3'),(11,'P4')]:
    result(157,index,'partition_models','/full/strict_family/models/A7/raw_coefficients/'+term,'主全样本A7原始坐标'+term+'系数',4)
for index,term,end in [(13,'P2',0),(14,'P2',1),(15,'P3',0),(16,'P3',1),(17,'P4',0),(18,'P4',1)]:
    result(157,index,'partition_models',f'/full/strict_family/coefficient_bootstrap/intervals/{term}/ci95/{end}',f'主A7固定基底惩罚5000重拟合{term}的95%区间端{end}',4)

# Q4的生成项按模型及具名交互查找行；索引来自该语义条件，非数值搜索。
gamma_rows=SUMMARY['artifacts']['partition_models']['data']['pair_comparisons']['mixture_reference_comparisons']['rows']
def gamma(line,index,model,term,field,label,places=4):
    matches=[i for i,r in enumerate(gamma_rows) if r['model']==model and r['term']==term
             and r['sample']=='strict' and r['weighting']=='family']
    if len(matches)!=1: raise ValueError((model,term,matches))
    result(line,index,'partition_models',f'/pair_comparisons/mixture_reference_comparisons/rows/{matches[0]}/{field}',label,places)

for idx,model,term,field,label in [
    (2,'A5r','DrDe','generated_gamma','A5r生成所指者性别×参照者性别交互'),
    (4,'A5r','DrDe','strict_M2_gamma','严格样本M2所指者性别×参照者性别交互'),
    (6,'A5r','DaDe','generated_gamma','A5r生成年龄×参照者性别交互'),
    (7,'A5r','DrDa','strict_M2_gamma','严格M2所指者性别×年龄交互'),
    (8,'A5r','DaDe','strict_M2_gamma','严格M2年龄×参照者性别交互'),
    (11,'A7','DrDa','generated_gamma','A7生成所指者性别×年龄交互'),
    (12,'A7','DaDe','generated_gamma','A7生成年龄×参照者性别交互')]:
    gamma(161,idx,model,term,field,label)
gamma(161,5,'A5r','DrDa','generated_gamma','A5r生成所指者性别×年龄交互按约为整数零表示',0)
ppc=SUMMARY['artifacts']['partition_models']['data']['full']['strict_family']['predictive_checks']
ppc_index=next(i for i,r in enumerate(ppc) if r['model']=='A7' and r['statistic']=='k_4')
for index,field in [(2,'observed'),(3,'model_expected')]:
    result(167,index,'partition_models',f'/full/strict_family/predictive_checks/{ppc_index}/{field}','四词项系统谱系等权比例的'+field,4)
for index,comp,field in [(7,'A7-M2','loss_difference'),(8,'A7-M2','ci95/0'),(9,'A7-M2','ci95/1'),
                         (11,'A7-M4','loss_difference'),(12,'A7-M4','ci95/0'),(13,'A7-M4','ci95/1')]:
    result(167,index,'partition_models',f'/pair_comparisons/primary/{comp}/{field}','主严格同折同权重'+comp+'导出类别对损失差/区间：'+field,4,'log_loss_gain' if field=='loss_difference' else 'log_loss_ci')

result(175,1,'strict_pairs','/systems','表4严格类别对谱系留出系统数')
for line,model in [(177,'M0'),(178,'M2'),(179,'M4')]:
    result(line,2,'pairs','/specifications/settings/24/logloss/'+model,'严格单词形D3/MLE/谱系等权/谱系CV的'+model+'留出损失',4,'log_loss',
           guards=[('/specifications/settings/24/systems',625),('/specifications/settings/24/measurement','D3'),
                   ('/specifications/settings/24/estimator','MLE'),('/specifications/settings/24/weighting','family'),
                   ('/specifications/settings/24/validation','family')])
    for index,field in [(3,'raw_logloss'),(4,'calibrated_diagnostic_logloss'),(5,'auc')]:
        result(line,index,'pairs',f'/regional_calibration/region_macro_average/{model}/{field}',f'六地域宏平均{model}的{field}',4,'log_loss' if field!='auc' else 'auc')
result(183,1,'pairs','/specifications/settings_count','实际类别对敏感性规格数')
result(183,2,'pairs','/specifications/contrast_rows','全部类别对增益区间数')
calculation(183,4,'pairs',['/family_only_glmm/converged_models'],'count_items','实际仅谱系随机截距VB收敛模型列表长度')

cd='/domains/cousins16/all_complete_singleton/'
for index,pointer,label,places in [
    (1,'systems','堂表亲完整配对系统数',None),(2,'families','堂表亲完整配对谱系组数',None),
    (4,'conditional_logit/contributing_families','主条件logit实际贡献信息谱系',None),
    (5,'conditional_logit/contributing_systems','主条件logit实际贡献系统',None),
    (6,'conditional_logit/or','主条件logit关系压缩收益优势比',2),
    (8,'conditional_logit/or_ci95_t/0','主条件logit优势比95%区间下端',4),
    (9,'conditional_logit/or_ci95_t/1','主条件logit优势比95%区间上端',2),
    (10,'conditional_logit/p_holm_two','主条件logit跨两个有效领域Holm p',4),
    (12,'exact_stratum_permutation/informative_strata','精确层置换可贡献信息层数',None),
    (13,'exact_stratum_permutation/informative_systems','精确层置换可贡献信息系统',None),
    (14,'exact_stratum_permutation/p_holm_two','精确层置换Holm p',4),
    (15,'exact_stratum_permutation/informative_families','精确层置换实际谱系数',None)]:
    result(185,index,'cross_domain',cd+pointer,label,places,'p_value' if 'p_holm' in pointer else None)
calculation(185,3,'cross_domain',[cd+'joint_XY_counts/0,1',cd+'joint_XY_counts/1,1'],'sum','堂表亲Y=1即相对r压缩收益系统总数，与兄弟姐妹X=1区分')
for index,domain in [(16,'parent_siblings_age16'),(17,'parent_siblings_generic8')]:
    result(185,index,'cross_domain',f'/domains/{domain}/all_complete_singleton/systems','对应父母同胞领域完整配对系统量')
calculation(185,18,'cross_domain',[
    f'/domains/{d}/all_complete_singleton/joint_XY_counts/{cell}'
    for d in ['parent_siblings_age16','parent_siblings_generic8'] for cell in ['0,1','1,1']],
    'sum','两父母同胞领域Y=1的系统计数各非负且合计为零，故两领域均无主要压缩收益系统')

# 明确的理论/方法数字逐处列举，不对未解决数字设置兜底白名单。
THEORY = {
  40:{5:'一个无条件模型是理论批评的单项指代，不是实测模型数。'},
  18:{3:'这里两个关系类别是共享词形定义的两个比较对象。',4:'同一系统是分析单位的同一性限定。',5:'同一语言是类别对依赖范围的限定。'},
  20:{1:'同一称谓套系为理论上的分析对象。',2:'同一划分为等价关系的结构限定。'},
  22:{1:'研究问题明确列为基底预测、配置方向、分布及推广三组。'},
  32:{3:'随后明确列举简洁表达、一致结构、可观察生成三个理论层次。'},
  60:{1:'在保持同一分析单位的条件下是单位同一性表述。',5:'原主资料要求兄弟姐妹八种位置齐全，非估计得到的类别数量。',8:'同一资料ID指记录单位的同一性。'},
  62:{1:'严格样本的每类只有一个词形是事先定义。',4:'三个二元关系变量组合成2^3=8个理论位置。',5:'二元编码0的预设定义，s=男性、a=年长、r=男性。',6:'相对性别q=0表示同性，是异或编码定义。',7:'理论位置数为2^3=8，非观测词项数。'},
  68:{1:'三个二元变量组成八个理论位置。',2:'明确列举保留r与保留s的两种相对坐标。',3:'L_all明确含s,a,r,q四个特征。'},
  70:{1:'一个文字的定义为一个带正负极性的特征。',2:'一个特征是最小文字单位的定义。',3:'全集可由常真式表示，定义文字成本为零。',4:'一个明确逻辑语言是当前描述语言的限定。',7:'库存成本扫描预列lambda=0。',8:'库存成本扫描预列lambda=1。',9:'库存成本扫描预列lambda=2。',10:'库存成本扫描预列lambda=3。',11:'同一语言内附加常数抵消是归一化恒等式。'},
  72:{1:'全部候选特征定义在八个理论位置。',2:'非平凡二分按互补去重，数量=(2^8-2)/2=127。',3:'二分指两个非空互补块，是特征的定义。',6:'二分两侧是特征取值的两块。',7:'两侧交换是稳定性分类的定义。'},
  78:{1:'Pi_8下标为理论八位置集合。'},
  80:{4:'k^2为类别数平方项，指数2是模型定义。',7:'A3的两个版本就是保留r和保留s。',11:'四特征描述语言固定含s,a,r,q。',13:'A7预列P2/P3/P4三个方向项。',14:'预期方向编码为+1。',15:'相反方向编码为−1。',16:'不适用方向编码为0。'},
  82:{1:'预设谱系整组五折，继承旧折。',2:'留一宏观区域为验证设计。',3:'预设语言五折验证。',5:'内层谱系三折为选择设计。',6:'L2中2标示二次正则化。',8:'预列alpha网格起点0。',9:'预列alpha网格0.01。',10:'预列alpha网格0.1。',11:'预列alpha网格终点1。'},
  84:{4:'两类区间明确为固定OOF重抽与重拟合，定义不同。'},
  86:{4:'M0的三个差异为Dr、Da、De。',8:'M3区分全部C(8,2)=28个无序类别对，是模型设计维数。'},
  90:{1:'0<|A|为排除无长幼区分系统的定义边界。',2:'|A|<4排除四配置全面区分，四个配置已逐项列明。',3:'六个预设配置方向为A_i/A_ii/A_iii/A_iv及男女参照者两个G对照。'},
  92:{1:'MM/FF等价界0.15为分析前固定的判定标准。',2:'95%为预设整谱系区间的名义覆盖率。'},
  94:{1:'一个截距偏移为校准诊断设计，并非估计参数值。',4:'三项模型增益预列为M2-M0、M2-M1、M4-M2。'},
  96:{1:'两个类别数控制项预列为兄弟姐妹k与目标领域k。',2:'预设5000次蒙特卡洛层内置换。'},
  102:{3:'四特征基底固定由s,a,r,q构成。',5:'六特征扩展按冻结旧定义含三个原始及三两两关系特征。',7:'两种相对坐标为rel_r/rel_s。',8:'各相对坐标含三特征。'},
  104:{2:'表1比较abs、rel_r、rel_s、all四种预列语言。'},
  111:{1:'四特征为L_all语言标识所含特征数。'},
  113:{1:'候选数127=(2^8-2)/2，是穷举定义。',2:'第四特征指追加在绝对三特征之后的f。',11:'95%是合成参照区间的名义覆盖率。',15:'二分指无标签两块集合划分。',17:'两类明确为value_preserving和block_swapping。',19:'二分是待比较的特征类型定义。'},
  115:{2:'第四特征指在绝对三特征后添加的候选。'},
  117:{1:'每一点表示一个候选二分，是图形编码定义。',2:'二分指候选特征的两个互补取值块。',3:'两面板明确为系统与谱系等权两种口径。'},
  119:{1:'四特征指L_all的固定特征库存。',2:'lambda=1是预设库存成本扫描值。',3:'lambda=3是预设库存成本扫描端点。',4:'rel_r含q,a,r三个特征。'},
  126:{2:'k平方的指数2属于A1模型定义。'},
  133:{2:'四特征为L_all固定语言名称。'},
  138:{2:'95%是固定OOF谱系区间的名义覆盖率。',10:'零是判断增益正负的理论参照。',11:'两种939映射预列为集合完全相等、图连通分量。',13:'两种权重预列为谱系等权、语言等权。',14:'三种验证目标预列为谱系、地域、语言。',16:'两项增益预列为相对合取与相对描述长度比较。'},
  142:{9:'六项配置对照为预列的六个方向检验。'},
  155:{1:'六项Holm校正的检验集合事先预列。',4:'95%是主谱系方向差区间的名义覆盖率。',7:'等价边界0.15是预设阈值。'},
  157:{3:'95%为预设固定OOF区间名义覆盖率。',12:'95%为系数重拟合区间的名义覆盖率。',19:'这一条件关联的这一为单项指代，不是经验计数。'},
  161:{10:'后两项明确指DrDa、DaDe两个年龄相关交互。'},
  167:{4:'95%是合成样本检查区间的名义覆盖率。'},
  173:{2:'六地域见实际地域模型regions计数；在结果映射单独处理。'},
  183:{3:'跨零指区间包含理论零点，不是额外实测估计。'},
  185:{7:'95%为优势比区间的预设名义覆盖率。',11:'两个类别数控制/分层因子为兄弟姐妹k、领域k。'},
}
for line, spec in THEORY.items():
    for index, reason in spec.items():
        if at(line,index)['kind'] == 'unresolved':
            theoretical(line,index,reason)

# 实际地域数量绑定当前六区域宏平均的记录，而非预期六区的协议。
for line,index in [(94,2),(171,4),(173,2)]:
    result(line,index,'pairs','/regional_calibration/region_macro_average/M2/regions','实际地域宏平均包含的宏观区域数量')
result(94,3,'pairs','/specifications/settings_count','实际完成的类别对全规格数')
result(84,1,'partition_models','/bootstrap_replicates','实际执行的固定OOF谱系重抽次数')
result(84,3,'partition_models','/full/strict_family/coefficient_bootstrap/replicates','主全样本A7实际谱系系数重拟合次数')
result(96,2,'cross_domain','/domains/cousins16/all_complete_singleton/exact_stratum_permutation/permutations','实际执行的固定层内蒙特卡洛置换次数')

# 讨论中的明确计数/单项指代逐处以实际句义记录，不包括未定位的实测数字。
DISCUSSION = {
 191:{1:'两项指标明确为平均描述长度和留出划分概率，不是另估计的类别数。',2:'三种完备坐标为abs、rel_r、rel_s。',3:'一个固定属性为被否定的理论假定。'},
 193:{1:'同一个解释问题指理论议题同一性。',5:'两种性别匹配配置为(s,r)=(男,男)或(女,女)，属于逻辑真值枚举。'},
 195:{3:'前一种锚点回指确定所指者身份。',4:'后一种配置回指参照者与所指者的相对关系。',5:'这一分工回指r与q两种表征角色，非经验数量。'},
 201:{1:'一个附加特征为表达能力变化的理论操作。',2:'两种指标明确为覆盖与富集。'},
 203:{1:'三维指各基底的固定维数。',2:'三套坐标为abs、rel_r、rel_s。',3:'八位置为理论关系空间大小2^3。'},
 207:{1:'一个条件指全局性别互换下q的逻辑取值。',2:'后一层次回指允许两块标签交换的结构对称性定义。'},
 209:{1:'四特征指预定义L_all。',2:'一个较小收费为库存成本的理论示例。',3:'三特征指预定义rel_r。',4:'同一语言限定库存成本抵消的归一化范围。'},
 213:{1:'一个解释为候选机制的单项指代。',2:'另一种角色差别指异性配置，非样本量。',3:'一个维度指年龄这一待解释区分。',4:'这一侧回指同性配置，非新计数。'},
 215:{3:'一个关系类别为角色排序解释的理论单位。'},
 217:{1:'另一种表达指标记性理论。',8:'两种参照者性别为预列男性、女性两个编码值。'},
 219:{1:'两种解释为同性关系排序与男性优先。',2:'两个同性配置为MM和FF。',3:'两个同性配置仍指MM和FF的预列直接对照。',4:'这一结果回指前述对照推断，非新计数。'},
 221:{8:'一组预测指文献局部条件转化的当前检验集合，非实测总数。',10:'两个解释问题指系数方向和独立预测贡献，句内明确并列。'},
 225:{1:'一个来源指类型分布作为总体交互的候选解释。',2:'一套合法类别是划分模型的理论分析单位。',3:'这一部分回指性别相关非加性，非定量比例。',4:'一个总体交互为统计量的理论单项。'},
 227:{1:'一个宽泛可能性指体系混合假说。',2:'一部分未量化的长幼组织不充当100%或样本计数。',3:'一个复杂性参数为被否定的理论压缩方式。'},
 231:{1:'这一分工回指表征与规则权重的理论角色分化。'},
 235:{1:'两类机制按该段明确讨论的结构与需要区分。'},
 239:{1:'同一模型指排序与损失诊断对应同一模型身份。'},
 241:{1:'单一基准率为统一截距解释的定义。',2:'一个粗分组指宏观区域这一分析单位。'},
 243:{1:'一个类型标签为历史变化解释的理论单位。'},
 251:{1:'一个有条件命题指跨领域复用这一假说。',2:'一侧指连接父母的父方/母方条件位置。'},
 253:{3:'一种观点指局部扩展假说。',4:'一个领域为局部学习迁移的理论单位。',6:'同一种纯类型为被排除的必要条件。'},
 259:{1:'一个综合解释为作者提炼的理论结构。',2:'一个笼统规律为研究对象的单项指代。',3:'同一类现象为跨证据比较的对象。'},
 265:{1:'一个解释框架为作者提出的理论结构，非经验总数。'},
}
for line, spec in DISCUSSION.items():
    for index, reason in spec.items():
        if at(line,index)['kind'] == 'unresolved': theoretical(line,index,reason)

mapping.update(status='mapped' if all(c['kind']!='unresolved' for c in claims) else 'mapping_required',
               retained_exact_context_whitelists=retained,
               rules_zh='经验数值逐处绑定results/summary.json具体artifact指标；仅白名单可整行精确迁移；不存在同值搜索或未知数字自动白名单。')
CLAIMS.parent.mkdir(parents=True, exist_ok=True)
CLAIMS.write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'total':len(claims),'kinds':Counter(c['kind'] for c in claims),'retained_exact_whites':retained},ensure_ascii=False))
for c in claims:
    if c['kind']=='unresolved':
        print(c['occurrence_id'],c['anchor']['line'],c['anchor']['numeric_index_on_line'],c['anchor']['token'],c['anchor']['line_text'])
