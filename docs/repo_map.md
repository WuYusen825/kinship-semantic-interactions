# 第三版仓库与数据流地图

## 固定入口与版本

仓库根目录为`/workspace/kinship-semantic-interactions-github`，修订分支为`codex/major-revision`。第三版任务书原件及提取文本见`notes/v3/`。上一正式阅读版本是`outputs/论文_中文正式稿.md`，第三版另存，历史文件不覆盖。

Kinbank固定于`925cc0e702ae5481cfe0088aaa0e69c3991000f3`，Glottolog CLDF固定于`072ca0d0410039fb8b779be8fc165bac575d2cda`；来源及校验见`analysis/provenance.json`。`data/kinbank/kinbank/cldf/forms.csv`是词形表，`languages.csv`、`parameters.csv`保存语言与亲属位置；`data/glottolog_languages.csv`提供谱系与宏观地域。

## 既有分析层次

1. `analysis/fetch_data.py`：按固定版本获取数据，不在本轮自动更新。
2. `analysis/audit.py`、`analysis/analyze.py`：原始整理与C=1冻结分析；第三版只读复用，不向其输出写入。
3. `analysis/category_forms_primary.csv`：逐系统、逐亲属位置的标准化词形集合。`analysis/pairs_primary.csv`：八位置两两组合，D1为集合交集非空。`analysis/oof_predictions.csv`提供最早五折分配核对。
4. `analysis/supplementary_s1/`：历史敏感性分析，冻结保留。
5. `analysis/supplementary_s2/structural_enumeration.py`：八位置位序、无标签划分枚举、`is_conjunctive`、`strict_prediction_directions`。第三版P2–P4必须调用这里的严格方向函数。
6. `analysis/supplementary_s2/partition_analysis.py`：`load_inputs`检查逐对词形共享，`prepare_systems`选择625个单词形系统，旧方向与随机参照计算在此。
7. `analysis/supplementary_s2/measurement_analysis.py`：`load_measurement_data`建立D1–D5五种既有共享口径。
8. `analysis/supplementary_s2/s2_models.py`：`build_design`固定M0–M4设计；`fit_aggregated`执行无惩罚MLE及预置Firth替代；`fit_c1_rows`保持C=1数值实现。
9. `analysis/supplementary_s2/run_s2.py`：`row_weights`定义训练权重，`score_value`定义谱系/语言评分，既有分组五折和60规格可读参照。整体脚本会重写S2，因此本轮不直接执行。
10. `analysis/supplementary_s2/uncertainty_results.json`：既有5000次谱系整组系数重拟合；失败的交叉GLMM仅保留，不重跑。

## 第三版新增层

`analysis/v3/`只写新增代码；`docs/analysis_plan.md`在T2–T7结果运行前单独提交；`results/baseline/`保存T0复现；后续`results/t1/`至`results/t5/`保存新计算及图表。`results/run_log.csv`追加每次运行规格、状态、指标和提交。新计划不追认旧结果为事先未知。

`analysis/export_forum_documents.py`可接受独立输入与名称，沿用`notes/format/中文模板_格式规则.json`导出第三版Word、PDF、TXT及摘要。`notes/formal_references.json`保存42项现有已取得全文的规范参考文献，`literature/`为PDF/TXT来源；新增理论引用同样必须有可核对全文。
