# 大修执行记录

## 2026-10-15：准备与分工

- 基线：`d32e7d369103d92df6466da2dfe4c8bff2a48bab`，来源分支 `origin/claude/finish-forum-paper-rio1ke`；工作分支 `codex/major-revision`。
- 已执行：`git fetch origin`、`git checkout -b codex/major-revision origin/claude/finish-forum-paper-rio1ke`、`gh pr view 1 --json title,headRefName,baseRefName,headRefOid,url`。指定起点与PR #1一致。
- 完整修改计划归档为 `notes/revision_plan_received.md`。依计划阅读交接入口、README、待办与复查清单、冻结协议、原补充协议、S1协议和报告、论坛稿。
- 用户明确要求多代理协作；理论枚举、文献补充、方法设计、基线核验、引文核查由分工代理处理。最终评审将交给未参与本轮修改的独立代理。
- 安装：`python -m pip install 'statsmodels>=0.14.6' patsy`；`BinomialBayesMixedGLM` 已成功导入，版本0.15.0。S2仅选择该实现，R未安装。
- 已执行代码语法检查：`python -m py_compile analysis/export_forum_documents.py analysis/validate_literature_update.py`，通过。导出脚本新增指定输入和后缀，避免覆盖旧稿产物；全文核验脚本兼容新增文献，并保留旧稿历史文献集合。
- 未解决：按修改计划第7节，已向作者提交合取定义选择：任意合取、递归特征树、或两者并列。收到决定并完成协议独立提交之前，不编写或运行读取共享结果的S2分析代码。
- 本阶段尚未提交；后续提交后补记实际提交号，不把预期提交写成已完成。

## 2026-10-15：文献、结构与第一轮独立核查

- 新增D01–D06共6项完整研究文本及159页逐页TXT；合并登记表、转换报告和索引后，`python analysis/validate_literature_update.py`实际通过：52项主要来源、57份源PDF/TXT、1834页、241页既有OCR。文件完整性检查不等于逐页人工阅读。
- 文献维护脚本的改动仅使D组可登记核验、动态统计文件量，并显式保留原46项文献集合检查；它不属于冻结估计代码。与导出CLI一并列为维护例外，其余冻结分析/S1/旧稿仍保持基线。
- Murdock1968实际取得Crossref元数据，JSTOR PDF地址返回HTML，OpenAlex没有仓储PDF，未取得全文、不引用；记录见`revision_murdock1968_access.json`。A02未尝试，A05维持无全文排除。
- `python analysis/supplementary_s2/test_partitions.py`最终已执行22项纯理论测试并通过；`python analysis/supplementary_s2/design_rank.py`通过，秩为4/5/7/28/14。未读取新增实测共享结果。
- 独立评审提出边覆盖不等于合法二级结构、两个三维基底不能直接判经典P5；理论实现已补根/分支兼容见证及完整四特征树的P5存在性搜索，新增反例测试。独立复审仍在进行，不记整体验收通过。
- 独立评审已实际测试导出CLI：临时v2夹具生成DOCX/PDF/摘要，旧名哨兵未变；这只是接口smoke，不是尚不存在的v2论文排版验收。
- C08作者副本缺少可能的末页320参考文献；撤回由末页319倒推正式书目范围的错误，保留来源首页281–320，正在尝试获取完整副本，版本状态待核实。
- 作者合取定义选择仍未收到，协议保持草案，S2未运行，论文v2未形成。

- C08补全尝试已结束但未成功，现将其从新版引用准入排除（`excluded_incomplete_pdf`），登记、CSV、转换质量说明、入口和候选证据库同步。最终实际validator输出为51项完整全文、C08单列、57份源PDF/TXT；此前52项为发现缺页前的历史状态。源PDF及TXT本身未被伪造补页。
- 当前准备快照不是最终运行前协议冻结；合取定义尚待作者选择，必须随后单独完成含`pre-run protocol`的最终协议提交，方能编写或运行S2实测代码。本次暂存草案不能替代该提交。

## 2026-10-15：第二轮独立复审与准备快照

- 独立评审未参与本轮实现，仅写两轮报告。第二轮结论为“准备材料可接受，R1–R5已修复”；明确整体修订仍未完成。报告见`notes/review/independent_revision_review_round2.md`。
- 独立代理实际复跑22项纯测试，核对实时纯枚举JSON，并对4140个划分的P5树存在性、计数和见证作完整复核，均通过；实际文献validator通过51项完整来源、57份PDF/TXT、399相对链接。
- 54项旧analysis/旧稿清单中，只有导出接口与文献核验两项维护脚本变化；其余核心冻结/S1/旧稿保持原内容。源码与文献维护语法检查通过。
- 准备材料将保存为可审阅的分支快照；本快照不是S2运行前协议冻结，不建立新实测结论或声称v2已经完成。作者合取定义仍待选择；结果之后的题目/贡献作者门也继续保留。

- 准备快照实际提交：`621c6d346a4d4a24dde7156bcf42666671d357af`（`Prepare reviewed revision materials pending author definition choice`），已推送`origin/codex/major-revision`。`git ls-remote origin refs/heads/codex/major-revision`核对一致。该提交含明确标草案的protocol，不是正式pre-run冻结。
- 本地研究镜像`/workspace/kinship_research`已同步此准备快照的533个Git跟踪文件，逐文件SHA-256差异为0，记录见`revision_preparation_sync.json`。本记录及日志随后一并同步；完整论文、S2实测与最终草稿PR仍未完成。
