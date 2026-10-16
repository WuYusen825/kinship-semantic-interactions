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


## 2026-10-15：作者定义选择、最终协议与S2实测

- 作者答复“采用”，选择任意合取为主、单叶递归树并列。最终协议单独提交为`6ba7afba369d3d15446ea7571eabd2117b7e8c74`（08:48:55 UTC，提交信息`Add pre-run protocol for supplementary analysis S2`），协议SHA-256为`61874a1c28ab37758670a61d12e08b6097af07f7922f63cfd76da5dacfcef8be`。该提交不含实测脚本或结果；全部S2实测晚于它。
- 实际入口运行`python analysis/supplementary_s2/verify_s2_entry.py`，15次C=1衔接拟合与原三模型主损失最大误差0。随后`python analysis/supplementary_s2/run_s2.py --phase predictions`退出0；并行组件由`partition_analysis.py`、`measurement_analysis.py`、`uncertainty_analysis.py --task glmm`及`--task bootstrap`运行。组件最终用`run_s2.py --phase assemble`合并。
- 20个测量×估计×权重条件、三种验证、五模型，共1600次折内预测拟合和20次全样本校准拟合，全部报告；420项模型对比CSV保存。5000次M4系数谱系重拟合均成功。P1/P2/P4获方向支持，P3/P6整体未支持，P5有3个数据库表示不兼容但真实语义仍未确认。
- 地域缺失30系统；地域验证及GLMM为909系统、123谱系组、25452对。三GLMM各按2000/10000上限作两次预置尝试，均precision loss未达收敛，未放宽判据或将近似后验作为稳定推断。
- 实际过程偏差：地域说明提交`b3640d9336e3dfd98673ff8f7a31ff1cc835a1cc`（08:54:19）晚于并行GLMM于08:53:48启动，不能说该说明提交在拟合前；说明文件已纠正原要求未实际实现，执行源码快照证明从首次运行就使用909完整个案。最终总协议仍早于全部S2实测。
- 预定前20个违例系统的字段抽查保留168条目标行；后续明确标为事后的补审覆盖全部22主四特征A违例及3个P5记录，共25系统202行；去重后总43系统354行。只读取原字段，真实语义解释全部仍为无法判断。
- 第三轮独立审计已通过S2主要实现和数值核查，包含独立重建D1–D5、105折模型复算、320折隔离、所有5000系数抽样及指定区间复算；具体范围见round3。它不等于最终整稿通过，也不把GLMM失败改成成功。

## 2026-10-15：v2全文与实际导出初检

- 结果后向作者展示推荐题目和部分支持的贡献表述，作者再次指示“继续”；据此完成可评审工作稿《合取偏好与层级约束的边界：兄弟姐妹称谓的跨语言检验》，不记录为作者逐字选择题目或批准投稿。
- `python analysis/export_forum_documents.py --input outputs/forum/论坛稿_v2.md`已实际执行，生成独立_v2 DOCX/PDF/摘要，旧稿文件未变。首版目视发现Pandoc主题字体覆盖显式Noto导致中文主节漏显，移除主题字体属性后重导出，六主节正常，PDF18页；图1全局曲线重复与分区点口径、图2图例均目视核对。
- `python analysis/audit_revision_artifacts.py`已执行：正文含标题表图5917汉字（纯正文5518），摘要227，42项参考、4表2图；LibreOffice更新的兼容Word统计正文7149、全稿8519。环境无Microsoft Word，不声称实际运行其计数器；ODT导入缓存页数不作实际页数，PDF实际18。若后续必要措辞修订，须以最终artifact报告更新。
- 54基线清单中51项内容不变，3个必要维护例外为导出接口/字体、文献validator、资料包动态数量；冻结估计、结果、协议、S1、旧稿及导出均保持原内容。第三项维护只避免资料包写死旧文献数量，不改分析。
- 实际`python analysis/validate_literature_update.py`退出0：51完整来源、57PDF/57TXT、1834页、241页已有OCR；文件完整性不等于逐页人工精读。D03作者稿页码封面偏移已纠正，PDF/TXT本身未改。
- 最终逐数字精确JSON pointer与逐页引文核对、独立第四轮整稿复审正在进行；这些未完成项不记通过。后续提交SHA、PR、镜像与ZIP实际终检另记。

- S2实现与第三轮独立审计实际提交：`d8d2e21a12fb0a3236f2b4010485d4c1e0741bd0`，提交信息`Execute S2 structural and predictive analyses with independent audit`。该提交早于最终v2数字/引文验收，不将其当作全稿通过。

- 第四轮提出摘要需说明指标，已将“改善0.0145”修为“对数损失降低0.0145”，MD SHA更新为`6d782b6897d0ba3751cb75e4b2c04e449163146d498a7fd5cf18e0ce04c3bb94`。按相同命令重新导出并执行artifact核验：正文5917汉字、摘要232、全稿Word兼容统计8524；18页PDF与DOCX的6267汉字顺序完全一致，六主节均存在。
- 仅对`outputs/PDF无法下载清单.md`定向Pandoc/XeLaTeX导出，更新对应PDF/TXT，使51完整来源、Murdock1968失败及C08缺页状态与MD一致；没有运行会覆盖旧稿的批量build/export脚本。
- S2提交`d8d2e21a12fb0a3236f2b4010485d4c1e0741bd0`已推送，远程分支SHA实际核对一致。最终v2与数字引文验收仍待后续提交。

- 最终引文回读发现B16的“独立贡献”过强，按原文改为“知觉结构之外的交际需要迹象”；MD最终SHA为`d5e4c09b6adfd361af74ade6d2c4ef263553bd4ef6905ac1aa4077792e8eeb35`。重导出并执行artifact后：正文5919汉字（纯正文5520）、摘要232、Word兼容正文7151/全稿8526，42参考/4表2图，18页PDF与DOCX6269汉字顺序完全一致。
- 最终`python analysis/check_manuscript_numbers.py --check`实际退出0，781/781映射验证、mismatches=[]、无未覆盖数字字符；120结果项、661逐处依据。初版767含3个“百分点”词素误报，改后764，再补17处明确中文数词到781；没有删除经验结果数。独立复核指出的两代、六特征、实际六区依据均已直接回锚。
- 最终引文主表完成42来源、53次正文作者年引用及37附页上标；5个方法来源补核及高风险B16修订记录均在表内。第四轮保留F01/F02当时未完成的历史，第五轮独立复查正按最终稿和报告进行。

## 2026-10-15：第五轮独立复查通过

- 独立agent未参与正文、估计实现或映射修改，仅写review；第五轮实际复跑781处数字与负向自测、53引用/37附页逐行对应、42来源准入及最终实物变更复核，通过论文和研究材料范围验收，无待返修项。第四轮未完成状态作为历史保留，F01–F05在第五轮闭环。
- 最后一次正文修改仅B16证据强度，实际PDF第14页目视通过，其余17页与前版像素一致；Markdown到DOCX去空白16451字符完全一致，DOCX到PDF6269汉字顺序一致。最终artifact四文件哈希与当前实物相同。
- 三GLMM未收敛、P3/P6未支持、P5真实语义未知及未执行后续研究均保留；通过的是修改计划下证据一致和论文交付要求，不将这些未成功项目改记成功。最终远程提交/PR/镜像与ZIP核验随后实际记录。

## 2026-10-15：最终稿提交、PR及payload同步

- 最终稿与数字/引文核验、第四/第五轮报告实际提交`04254e0c8fe4b0891854b3b504acb30ff24c5f94`，已推送；GitHub实际PR head也核对为该SHA。
- 对该payload的600个Git跟踪文件执行copy2至`/workspace/kinship_research`，逐文件SHA-256不匹配为0，实际记录见revision_delivery_sync.json。
- 首次完整ZIP为600文件、177.8 MiB，testzip通过。交付元数据加入后将按相同命令重建ZIP及manifest；最终归档SHA与整分支同步收据另存工作区，避免把自含清单的哈希写成递归依赖。
- gh的GraphQL创建PR返回401；保留已推送成果，改用已连接GitHub的结构化create_pull_request成功建立草稿PR #2： https://github.com/WuYusen825/kinship-semantic-interactions/pull/2 。实际base为`claude/finish-forum-paper-rio1ke`，head为`codex/major-revision`，draft=true；未合并。
- 当前日志及同步报告本身属于随后交付元数据提交，payload证书不把它们冒称为早已核验的600文件内容。最终整分支、远程及归档证书在这些文件定稿后另行实际生成。
