"""T8: bind every reported numeric leaf to a result file, script and function."""
from __future__ import annotations
import json,math
from pathlib import Path
from common import ROOT,RESULTS,SEED,BOOTSTRAP_REPLICATES,save_json,logged_run,verify_analysis_plan

SOURCES={
 'baseline':('results/baseline/reproduction_results.json','analysis/v3/reproduce_baseline.py','reconstruct / check_row / reproduce_models'),
 'partitions':('results/t1/build_manifest.json','analysis/v3/build_t1.py','make_catalogue / observed_language_summary'),
 'partition_models':('results/t2/t2_results.json','analysis/v3/run_t2.py','run_cv / run_full / comparisons_from_scores / coefficient_bootstrap / run_pair_comparisons'),
 'basis':('results/t3/t3_results.json','analysis/v3/basis_enrichment.py','summarize_features / description_cost_comparison / shape_reference'),
 'positions':('results/t4/position_results.json','analysis/v3/position_tests.py','contrast_statistics / equivalence_ii_statistics / analyse_subset'),
 'pairs':('results/t5/t5_results.json','analysis/v3/run_t5.py','specification_phase / calibration_phase / dependence_phase'),
 'strict_pairs':('results/t5/strict_results.json','analysis/v3/run_t5.py','strict_phase'),
 'domain_coverage':('results/t6/coverage_results.json','analysis/v3/domain_feasibility.py','coverage_for_system / cohort_summary'),
 'cross_domain':('results/t6/association_results.json','analysis/v3/cross_domain.py','relative_metrics / fit_conditional / exact_stratum_permutation'),
 'trees':('results/t7/feasibility.json','analysis/v3/tree_feasibility.py','inspect'),
}
METADATA={'started_utc','finished_utc','completed_utc','verified_utc','started_at','completed_at','time','commit','git_commit',
 'plan','guard','baseline','configuration','input_sha256','source_sha256','script_sha256','runner_sha256','pair_models_sha256',
 'S2_fitter_sha256','input_pairs_sha256','files','source_protection','source_manifest','output_sha256','execution_gate',
 'family_rows','family_diagnostics','weighted_family_scores','strata','family_modal_partial_types',
 'numerical_refinement','script','producer','script_mtime_utc','plan_commit_time','plan_commit','plan_sha256'}
def stable(value):
 if isinstance(value,dict):return {k:stable(v) for k,v in value.items() if k not in METADATA and not k.endswith('_sha256')}
 if isinstance(value,list):return [stable(x) for x in value]
 return value

def select_data(name, original):
 # Keep paper-facing results; exhaustive tables and prediction arrays stay in their task files.
 if name=='partition_models':
  keep={k:original[k] for k in ['seed','bootstrap_replicates','analysis_status','solver_profile','completeness']}
  keep['cv']={}
  for setting,v in original['cv'].items():
   keys=['setting','systems','families','selected_models','selected_comparisons','fits','failed_fits']
   keep['cv'][setting]={k:v[k] for k in keys if k in v}
  keep['full']={}
  for setting,v in original['full'].items():
   keys=['setting','systems','families','selected_base','selected_A7','models','empirical_seven_cells','empirical_M2_contrast','contrasts','coefficient_bootstrap','fits','failed_fits']
   keep['full'][setting]={k:v[k] for k in keys if k in v}
   if setting=='strict_family':keep['full'][setting]['predictive_checks']=v['predictive_checks']
  keep['pair_comparisons']={k:v for k,v in original['pair_comparisons'].items() if k!='comparisons'}
  # Preserve original list positions for exact source-pointer traceability.
  keep['pair_comparisons']['comparisons']=original['pair_comparisons']['comparisons']
  return stable(keep)
 if name=='basis':
  return stable({k:original[k] for k in ['q_check_passed','q','absolute_baseline','symmetry_counts','description_cost','ranking']})
 if name=='positions':
  keep={k:original[k] for k in ['specification','analysis_status']}
  keep['subsets']={k:v for k,v in original['subsets'].items() if k in ['overall','excluding_austronesian','excluding_pama_nyungan']}
  return stable(keep)
 return stable(original)

def escape(value):return str(value).replace('~','~0').replace('/','~1')
def numeric_leaves(value,pointer=''):
 if isinstance(value,dict):
  for key in sorted(value):yield from numeric_leaves(value[key],pointer+'/'+escape(key))
 elif isinstance(value,list):
  for key,item in enumerate(value):yield from numeric_leaves(item,pointer+'/'+str(key))
 elif isinstance(value,(int,float)) and not isinstance(value,bool):
  if not math.isfinite(value):raise ValueError('Nonfinite summary metric '+pointer)
  yield pointer,value

def main():
 verify_analysis_plan()
 with logged_run('T8_summary',{'seed':SEED,'scope':'all completed tasks; numeric provenance; no model refits'}) as metrics:
  artifacts={};index=[]
  for name,(relative,script,function) in SOURCES.items():
   path=ROOT/relative
   if not path.exists():raise RuntimeError('Missing completed task: '+relative)
   original=json.loads(path.read_text());data=select_data(name,original)
   if name=='partition_models':
    completeness=original['completeness']
    if completeness.get('cv_settings')!=18 or completeness.get('full_settings')!=6 or not completeness.get('pair_comparison_completed'):raise RuntimeError('T2 not complete')
   if name=='pairs' and (original['specifications']['settings_count']!=60 or original['specifications']['contrast_rows']!=180):raise RuntimeError('T5 specifications not complete')
   artifacts[name]={'source_file':relative,'producer_script':script,'producer_function':function,'data':data}
   for pointer,value in numeric_leaves(data):
    index.append([name,pointer,value])
  result={'schema_version':1,'status':'第三版完整补充分析；T6探索性，T7完成可行性未拟合Mk',
    'analysis_plan':'docs/analysis_plan.md','numerical_amendment':'docs/numerical_refinement_v3.md',
    'cross_domain_plan':'docs/t6_association_plan.md','conflict_register':'CLAUDE_DECISIONS_V3.md',
    'seed':SEED,'bootstrap_replicates':BOOTSTRAP_REPLICATES,
    'provenance_note':'artifacts内每个数值继承其来源文件、脚本和函数；numeric_index按列名逐叶给出所属artifact、来源文件内路径和值；对应summary路径为/artifacts/{artifact}/data{source_pointer}。正文数字审核另绑定出现位置，不以同值搜索替代来源。',
    'artifacts':artifacts,'numeric_index_columns':['artifact','source_pointer','value'],'numeric_index':index}
  save_json(RESULTS/'summary.json',result)
  lines=['# 第三版补充分析总报告','','本报告依据完整结果生成；模型规格在本轮结果前写定，数值精化在停止诊断出现后单独追加。全部尝试及阴性结果保留。','',
   '|任务|交付与主要结论|完整入口|','|---|---|---|',
   '|T0|37项点估计与14组固定预测区间复现通过；baseline-v1保留旧定义|baseline/reproduction_report.md|',
   '|T1|4140划分、精确DNF、三种样本映射与旧方向交叉核对通过|t1/build_manifest.json|',
   '|T2|rel_r提高留出划分概率，rel_s降低；位置增量区间含零；pair预测弱于M2/M4；类型分布只复现部分交互|t2/report.md|',
   '|T3|q观测覆盖第1、富集第48；两个相对坐标不同；特征库存成本改变跨语言排序|t3/report.md|',
   '|T4|同性配置偏好明确；MM/FF等价未确立；男性所指者方向在谱系Holm后未达.05|t4/report.md|',
   '|T5|全部60规格及180区间保留；AUC改善而原始/截距校准损失仍较差；5个仅谱系VB收敛|t5/report.md|',
   '|T6|堂表亲存在局部关联线索，但有效条件谱系很少、OR区间极宽；父母同胞指标无变化，关联不可估计|t6/association_report.md|',
   '|T7|固定分类树所有枝长为人为单位1，完成可行性与六态粗化；本轮不拟合可选Mk|../docs/t7_feasibility.md|',
   '', '## 与第二版的实质变化','',
   '由类别对工作似然扩展到完整划分分布，并在同一框架控制类别数、比较基底与位置特征。原有计数与系数已实际复现而非沿用通过标记。第三版把“相对基底优势”限定为保留所指者性别的坐标，保留其余坐标的相反结果；没有将q覆盖最广改称富集最强。',
   '', '原先关于男女同性配置相当与全面跨领域复用的解释接受直接检验，现按实际信息范围收窄。位置系数的全样本方向与折外增量分别报告；类型分布产生部分非加性，也明确暴露年龄相关交互的解释缺口。地域排序与概率标定拆开，不能将偏差仅归于共享基准率。',
   '', '## 数字、图表和运行','',
   f'`summary.json`包含{len(index)}个数值叶的脚本/函数与来源路径；正文使用的具体出现位置另见notes/v3数字审核。各任务的Fx_图保留于对应目录，正式论文的图表选择和编号见下表。',
   '', '|论文图表|资料文件／指标|','|---|---|',
   '|表1|t1四语言合取量及t3描述长度|',
   '|表2|t2严格样本谱系五折模型阶梯|',
   '|表3|t4六项配置对照|',
   '|表4|t5严格样本损失与地域宏平均诊断|',
   '|正文图与补充Fx_图|以第三版实际插图路径为准；各任务全部图完整保留|',
   '', '`make all`按依赖拓扑运行全部分析；`make check`运行关键单测；`make documents`导出第三版。独立环境实跑证据见results/reproducibility，独立agent评审见notes/review/v3_*。尚在生成的评审不能视作已通过。',
   '', '## 决定与限制','',
   '用户授权自主处理决策点。数学歧义、原数值门失败及精化、两种多数口径、T6的估计对象差异和T7未拟合决定集中于根目录CLAUDE_DECISIONS_V3.md，供Claude进一步决定；未覆盖原冻结计划或第二版。']
  (RESULTS/'report.md').write_text('\n'.join(lines)+'\n')
  metrics.update(numeric_leaves=len(index),artifacts=len(artifacts),T2_settings=18,T5_specifications=60)
  return result
if __name__=='__main__':main()
