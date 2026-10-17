# 兄弟姐妹称谓的合取偏好与条件区分

本仓库保存中文正式论文、公开数据库分析、文献全文和可复现结果，并提供研究与复查交接。

大修分支为`codex/major-revision`。S2最终协议于实测前单独提交（`6ba7afb`）；它写于原结果已知之后，属于事后补充分析。旧稿、冻结结果和S1保留。v2已完成并通过第五轮独立复查，逐处数字、引文及独立全稿核查记录单列；第三版按新任务书另作完整补充分析，以下提供各版本的独立入口。

研究考察兄弟姐妹称谓的合取偏好、次级区分与跨群组预测，并以关系表征、局部区分需要及历史传承解释这些现象。划分结构、类别对概率与表达实现分别判断，理论提案与已执行分析明确对应。

本轮第三版及此前理论扩写见[草稿PR #3](https://github.com/WuYusen825/kinship-semantic-interactions/pull/3)，目标为`claude/finish-forum-paper-rio1ke`。此前正式稿[PR #2](https://github.com/WuYusen825/kinship-semantic-interactions/pull/2)已合并；旧payload同步证据保留于[历史记录](notes/revision_delivery_sync.json)。

## 第三版（当前修订版本）

- [中文第三版](outputs/论文_中文第三版.md)｜[Word](outputs/论文_中文第三版.docx)｜[PDF预览](outputs/论文_中文第三版.pdf)｜[TXT](outputs/论文_中文第三版.txt)｜[摘要](outputs/第三版_摘要.txt)。第二版及旧论坛稿单独保留。
- 正文12161汉字，讨论5727汉字（47.1%），摘要288汉字；42项参考文献、4张表、2幅图，PDF共30页。统计口径见[导出核验](notes/v3/artifact_check.json)。
- 新版以625个严格系统为主，在4140种划分上精确建模；新增基底、位置与跨领域对照。保留所指者性别的相对基底具有预测优势，另一相对坐标反而更差；位置增量区间含零，类型分布只复现部分总体交互，生成检查与类别对预测的不足均保留。
- 讨论围绕表征锚点、合取与库存成本、局部排序、类型混合、地域历史及表达层次展开。参考文献继续仅用已取得完整全文的来源；模板字体、1.5倍行距、著者—年份与页码上标沿用。Word指定模板字体，PDF为替代字体预览。
- [任务总报告](results/report.md)｜[逐数值来源](results/summary.json)｜[运行前计划](docs/analysis_plan.md)｜[数值精化附录](docs/numerical_refinement_v3.md)｜[跨领域操作化与计划](docs/t6_association_plan.md)｜[谱系树可行性](docs/t7_feasibility.md)。
- [Claude矛盾与决定文档](CLAUDE_DECISIONS_V3.md)集中记录7/15两种不变性、两种相对坐标、库存成本抵消、等价检验、T6估计对象差异及未拟合可选Mk的理由。
- [独立分析评审](notes/review/v3_analysis_review_round1.md)｜[独立全文评审](notes/review/v3_manuscript_review_round1.md)｜[独立最终实物复核](notes/review/v3_final_review.md)。[829处数字核验](notes/v3/number_check.json)、[83次引文及42项全文核对](notes/v3/citation_check.md)与导出报告均绑定第三版实际文件，不沿用旧稿的通过记录。
- [完整干净环境复现](results/reproducibility/clean_environment.json)：16阶段、115项关键测试通过；320份统计文件、8945243项数值比较无差异，166份实现及固定输入SHA一致。具体范围及单列元数据差异见[比较报告](results/reproducibility/comparison.md)。

第三版一条命令复现全部分析：

```bash
python -S analysis/v3/clean_reproduce.py --workspace /tmp/kinship-v3-reproduction
```

也可在已安装[环境依赖](analysis/v3/requirements.txt)的仓库中运行`make all`，用`make check`执行关键单测、`make documents`导出第三版。环境与独立副本说明见[分析入口](analysis/v3/README.md)。

## 第二版正式论文（历史阅读版本）

- [中文正式稿](outputs/论文_中文正式稿.md)｜[Word](outputs/论文_中文正式稿.docx)｜[PDF预览](outputs/论文_中文正式稿.pdf)｜[TXT](outputs/论文_中文正式稿.txt)｜[摘要](outputs/正式论文_摘要.txt)。
- 摘要仅保留样本规模，正文按研究问题、理论背景、方法、结果与讨论组织。下载时间、执行时间、提交编号及文件校验信息集中于[复现说明](notes/formal_reproducibility.md)。
- 正文采用著者—出版年引注与页码上标，42项英文参考文献按用户模板示例整理，规范条目及来源说明见[引用格式记录](notes/formal_references.md)。字体与1.5倍行距见[模板应用说明](notes/format/中文模板_应用说明.md)；Word使用模板字体名，PDF为替代字体预览。
- 正文11563汉字，讨论六节5778汉字、约占一半。综述以理论分歧组织，讨论从实测结果出发解释关系压缩、局部标记、总体非加性及推广差异；摘要277汉字，只保留一项样本规模。
- 理论解释经独立首轮评审后局部修订，第二轮内容和最终29页导出实物均已通过；原方法、结果区块逐字节保持，不重新拟合模型。
- [理论回溯台账](notes/discussion_expansion_20261016/research_ledger.md)｜[学习、效率及共词化证据](notes/discussion_expansion_20261016/semantic_explanation_evidence.md)｜[标记、角色及历史证据](notes/discussion_expansion_20261016/kinship_explanation_evidence.md)。
- [正式稿数字核验](notes/formal_manuscript_number_check.json)｜[引文核对](notes/formal_citation_check.md)｜[排版核验](notes/formal_artifact_check.json)｜[第二轮独立评审](notes/review/theory_expansion_review_round2.md)｜[首轮修改意见](notes/review/theory_expansion_review_round1.md)。旧快照通过记录不作为新版验收。

## S2与论坛稿v2

- [v2中文稿](outputs/forum/论坛稿_v2.md)｜[v2 Word](outputs/forum/词与世界论坛-英语-吴雨森、瞿唯艺_v2.docx)｜[v2 PDF](outputs/forum/词与世界论坛-英语-吴雨森、瞿唯艺_v2.pdf)｜[v2摘要](outputs/forum/中文摘要_提交用_v2.txt)。
- [运行前协议](analysis/supplementary_s2/protocol_s2.md)｜[S2报告](analysis/supplementary_s2/s2_report.md)｜[完整结果JSON](analysis/supplementary_s2/s2_results.json)。
- [全部420项交叉比较](analysis/supplementary_s2/s2_crossed_comparisons.csv)｜[交叉敏感性图](analysis/supplementary_s2/s2_multiverse_forest.png)｜[逐系统分数](analysis/supplementary_s2/s2_language_scores.csv)。
- [数字逐处核验](notes/manuscript_number_check.json)｜[引文页码核对](notes/revision_citation_check.md)｜[导出与冻结核验](notes/revision_artifact_check.json)。
- [文献综合矩阵](outputs/文献综合矩阵.md)｜[理论约束](outputs/理论约束对照表.md)｜[测量复核](outputs/数据测量复核.md)｜[独立S2审计](notes/review/independent_revision_review_round3.md)｜[最终整稿复审](notes/review/independent_revision_review_round5.md)。

主样本仍为939个系统、125个谱系组。625个单词形系统中，主四特征定义下有22个非合取系统；年长侧与同性侧的次级区分方向得到支持，男性侧方向未通过调整后的检验。条件模型相对原始加性有正增益，相对七差异单元交互模型的区间包含零；未见地域验证没有支持其优势。

| 主语系留出、无惩罚、谱系等权 | 对数损失增益 | 固定折外预测的谱系自助95%区间 |
|---|---:|---|
| 条件模型相对原始加性 | 0.0145 | [0.0076, 0.0219] |
| 条件模型相对七单元交互 | 0.0018 | [-0.0005, 0.0039] |

20组测量×估计×权重条件、三种验证及5000次系数重拟合均保存。地域缺失30个系统，地域验证和GLMM使用909个已知地域系统；三个GLMM均未达到预定收敛标准，保留失败诊断，不作稳定的模型化不确定性推断。其余预测和结构结论不使用这些失败近似后验。

## 原冻结分析：C=1历史参照

主样本包含 **939个语言记录系统、125个谱系组、26,292个无序类别对**。研究以Kinbank词形记录为基础，使用Glottolog官方分类整组留出语系，比较三个模型：

| 模型 | 语义编码 | 设计秩 |
|---|---|---:|
| 原始加性 | 所指者性别、年龄、参照者性别差异 | 4 |
| 经典加性 | 原始差异加传统相对性别 | 5 |
| 完整两两交互 | 原始差异及其全部两两乘积 | 7 |

完整两两交互对七种非零差异组合具有饱和表达能力。主设定为固定岭惩罚 `C=1`，以未见谱系组上的语言等权平均对数损失衡量预测表现：

| 完整交互相对的基准 | 对数损失增益 | 95%谱系重采样区间 |
|---|---:|---|
| 原始加性 | 0.004423 | [-0.000510, 0.008205] |
| 经典加性 | 0.001843 | [-0.000604, 0.006120] |

正值表示完整交互的损失更低。主结果为小幅点估计改善，两项区间均包含零；传统相对性别之后的剩余增益随词形定义和惩罚设定变化。这里测量的是跨语言总体词形共享的预测结构，全部预设敏感性结果随论文和代码保存。

![预设条件下的样本外预测增益](analysis/robustness_gain.png)

## 文献与阅读材料

当前可用的正式全文文献为 **51项独立学术著作，全部具有PDF全文和同名TXT**。A02、A05仍无全文；独立复查另发现C08副本缺末页320，公开源未能补齐，暂排除新版引用。旧稿保留历史文献范围。文献库共保存 **57个源PDF及57个TXT**；额外5个文件是早期版本或补充材料，不重复计数。

2026年10月15日大修准备新增6项共词化研究全文，D03、D05使用完整作者稿，版本单列；既有研究计划和旧论文保留原来的46项文献范围。

2026年10月15日收到用户补充8份PDF，已核对题名、作者与版本，并统一命名为“编号_第一作者_年份_题名”。B03与C12现以正式期刊PDF为主要依据；旧预印本、工作论文保留在`earlier_versions/`。其余作者稿和在线先行版本按登记表明确说明。

- [51项完整全文与来源状态入口](literature/README.md)
- [全部PDF／TXT索引](literature/TXT索引.md)
- [逐页转换及OCR报告](literature/pdf_text_conversion_report.json)｜[文本质量与8个低文字页复核](literature/文本质量说明.md)
- [用户补充PDF与重命名校验](literature/uploaded_pdf_manifest.json)

TXT保留PDF文件页序；扫描或低文本页已尝试OCR。图表、公式、音标及低文字页需结合原PDF核对。全文文件齐备和自动转换完成，不等于已逐页精读和人工校对。

## 成果导航

- **研究计划：** [Markdown](outputs/研究计划_完善版.md)｜[PDF](outputs/研究计划_完善版.pdf)｜[Word](outputs/研究计划_完善版.docx)。
- **早期中文实证工作稿（历史版本）：** [Markdown](outputs/论文_中文实证稿.md)｜[PDF](outputs/论文_中文实证稿.pdf)｜[Word](outputs/论文_中文实证稿.docx)。
- **论坛投稿稿（第六届“词与世界”本科生论坛，2026年10月15日）：** [Markdown](outputs/forum/论坛稿.md)｜[Word](outputs/forum/词与世界论坛-英语-吴雨森、瞿唯艺.docx)｜[PDF](outputs/forum/词与世界论坛-英语-吴雨森、瞿唯艺.pdf)｜[提交用摘要](outputs/forum/中文摘要_提交用.txt)。由`python analysis/export_forum_documents.py`生成。
- **补充分析S1（结果已知后写定协议、提交后运行）：** [协议](analysis/supplementary_s1/protocol_s1.md)｜[结果](analysis/supplementary_s1/s1_report.md)：嵌套调参、经典模型编码依赖、28类别对饱和模型；不替代冻结的C=1主比较。论坛稿表1、表2的描述统计见`analysis/forum_descriptives.py`。
- **文献综述与证据台账：** [Markdown](outputs/文献综述与证据台账.md)｜[PDF](outputs/文献综述与证据台账.pdf)。
- **全文补充与排除清单：** [Markdown](outputs/PDF无法下载清单.md)｜[PDF](outputs/PDF无法下载清单.pdf)。
- **结构化书目：** [CSV](outputs/文献登记表.csv)｜[JSON](outputs/文献登记表.json)。
- [复现说明](analysis/README.md)：数据版本、运行环境、输出字段和核验方法。

`literature/`按A亲属研究、B语义范畴与效率、C统计与数据方法、D共词化研究保存PDF和登记表；`data/`保存锁定版本的必要原始表；`analysis/`保存脚本、协议、配对数据、折外预测与图表；`notes/`保存摘要、阅读证据和独立核验记录。

## Claude交接

- [Claude入口](CLAUDE.md)：当前状态、文件优先级和引用范围。
- [待完成清单](CLAUDE_TODO.md)：理论约束、创新定位、后续估计设计与成稿任务。
- [复查清单](CLAUDE_REVIEW_CHECKLIST.md)：文献、OCR、模型、数值、文件及同步检查。

2026年10月14日的冻结统计结果保持原内容；新增全文用于v2论证，S2另存并已实际执行。

## 复现

```bash
git clone --branch codex/major-revision https://github.com/WuYusen825/kinship-semantic-interactions.git
cd kinship-semantic-interactions
```


使用Python 3.12，S2复现方式见[目录说明](analysis/supplementary_s2/README.md)。在独立克隆的仓库根目录运行：

```bash
python -m pip install -r analysis/supplementary_s2/requirements.txt
python analysis/supplementary_s2/test_partitions.py
python analysis/supplementary_s2/run_s2.py --phase all
```

以下命令用于重建原冻结分析，会写入历史结果目录；需要执行时请使用另一个独立克隆：

```bash
python -m pip install -r analysis/requirements.txt
python analysis/audit.py
python analysis/analyze.py
python analysis/verify_results_independent.py
```

完整资料已保留分析所需数据。需要重新获取原始文件时，可运行`python analysis/fetch_data.py`，按锁定commit下载并核对核心文件SHA-256。绘图字体配置及其他环境说明见[分析目录说明](analysis/README.md)。

原始数据来自[Kinbank](https://github.com/kinbank/kinbank)和[Glottolog CLDF](https://github.com/glottolog/glottolog-cldf)。版本、许可及文件校验值保存在[provenance.json](analysis/provenance.json)；文献与数据沿用各自来源的引用和许可要求。

## 数据版本与研究记录

| 项目 | 固定版本／时间 |
|---|---|
| Kinbank | `925cc0e702ae5481cfe0088aaa0e69c3991000f3` |
| Glottolog CLDF | `072ca0d0410039fb8b779be8fc165bac575d2cda` |
| 原分析执行日期 | 2026年10月14日 |
| 仓库整理日期 | 2026年10月15日 |

事前分析协议见[主协议](analysis/protocol_frozen.md)及[结果生成前的补充协议](analysis/protocol_addendum_before_outcomes.md)。完整数值见[results.json](analysis/results.json)，独立复算记录见[independent_verification.json](notes/independent_verification.json)。研究原计划同时保留在[original_research_plan.md](original_research_plan.md)。

本仓库为研究工作稿与复现材料。原始数据和第三方文献保留各自来源、版本及许可；不以仓库整体的单一许可覆盖这些材料。

## 文献维护

先安装`poppler-utils`、`tesseract-ocr`及英语识别模型；Python文本工具依赖单列于`analysis/requirements_text.txt`。然后运行：

```bash
python -m pip install -r analysis/requirements_text.txt
python analysis/convert_literature_pdf_to_txt.py --workers 3 --dpi 200
python analysis/validate_literature_update.py
```

转换脚本仅生成TXT和质量报告，不改写PDF。旧`build_documents.py`会重建旧稿，本次v2使用`export_forum_documents.py --input outputs/forum/论坛稿_v2.md`。源码、引用和材料校验的当前结果见[本轮更新核验](outputs/本轮文献更新核验.json)。PDF／Word排版说明见`analysis/export_documents.py`，还需Pandoc、XeLaTeX和中文字体。
