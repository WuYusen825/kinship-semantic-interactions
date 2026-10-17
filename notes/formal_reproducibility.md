# 正式论文的补充说明与复现入口

本文件保存与研究复现有关、但不属于论文正文的工程记录。正式稿为`outputs/论文_中文正式稿.md`；此前工作稿、论坛稿及已审核数值原样保留。本轮在已有结果上扩展理论解释，按用户要求将正文调整到约1万—1.5万汉字、讨论约占一半；方法与结果区块保持原字节，不重新估计模型。理论解释是本次提出的综合框架，其依据、竞争解释与预测见[回溯台账](discussion_expansion_20261016/research_ledger.md)。

## 一、数据版本与时间信息

Kinbank采用提交`925cc0e702ae5481cfe0088aaa0e69c3991000f3`，Glottolog CLDF采用提交`072ca0d0410039fb8b779be8fc165bac575d2cda`。原始数据来源、许可、文件校验值及获取记录见[provenance.json](../analysis/provenance.json)、`data/`及文献登记表。下载日期、执行时间和请求状态属于溯源记录，不进入正式论文。

原分析、S1及S2的完整时间线见[修订日志](revision_log.md)。S2最终协议独立提交为`6ba7afba369d3d15446ea7571eabd2117b7e8c74`，协议哈希及运行前后关系保存在[协议](../analysis/supplementary_s2/protocol_s2.md)和[执行入口](../analysis/supplementary_s2/verify_s2_entry.py)。这些标识不作为论文论证内容。

## 二、探索性地位与完整分析路径

S2写于原冻结结果、S1和评审核查结果已知之后，属于探索性补充分析，不是预注册。选择无惩罚MLE与谱系等权时，旧无惩罚结果较好及谱系汇总增益较大已经知晓；此前C=1与语言等权结果完整保留。正式稿在方法中保留探索性定位，完整选择背景在本文件及原协议中公开。

三种交叉随机截距模型按预定两次尝试均未达到收敛标准。地域澄清提交晚于并行GLMM启动的实际偏差，见[时序说明](../analysis/supplementary_s2/implementation_missing_area_before_glmm.md)。首次执行已经使用909个地域完整个案；该过程偏差不改写为事前完成的提交。

全部20个测量×估计×权重条件、三种验证、420项模型比较、系统累积对数似然比、单元校准、预测及拟合诊断见[S2目录](../analysis/supplementary_s2/README.md)。固定预测的整谱系自助区间不含重新训练和重新划折，条件系数区间则包含整谱系重拟合；二者不互相替代。

## 三、结构表示和资料核查

八类关系的4140个理论划分，以及任意合取、单叶递归树与Kronenfeld计数的逐格差异，见[纯结构说明](../analysis/supplementary_s2/structural_theory.md)。原始八类别代码、特征编码、M0—M4设计矩阵与秩、严格方向判定及树搜索均在S2协议和代码中保留。

资料核查保留预定前20系统和事后补查全部22主四特征非合取系统及3个P5对象的不同地位，去重43系统、354条目标原始行。具体Value、Form、Comment、Source及候选解释见[字段审计](../analysis/supplementary_s2/s2_violation_audit.md)，不能据字段核查就确认真实语义反例。

## 四、引用版本与页码

正式稿采用著者—出版年制，文末英文书目按用户提供模板示例整理（此前GB/T格式保留于格式前快照）。具有核实印刷页的重点命题保留页码上标；对作者稿或在线先行版本的转述，正文只列作者年份，不把作者稿页码当作正式期刊页码。全部实际PDF页序、作者稿自标页及原文定位仍保存于[逐处证据台账](revision_citation_check.md)及正式稿专属核对记录。

例如Kemp等2018、Carr等2020、Xu等2020、Brochhagen与Boleda2022使用的作者稿页码，以及Rácz等2020所据Early View页码，均在补充证据中注明版本。正文删除版本标签与转述页码，并不改变实际阅读来源。引用42项完整全文来源，A02、A05、C08和未取得全文的Murdock1968继续排除。

## 五、导出与检查

正式稿的Markdown、Word、PDF及TXT采用一致名称。导出命令为：

```bash
python analysis/export_forum_documents.py --input outputs/论文_中文正式稿.md --name 论文_中文正式稿 --abstract-name 正式论文_摘要 --page-numbers --format-profile notes/format/中文模板_格式规则.json
python analysis/audit_revision_artifacts.py --input outputs/论文_中文正式稿.md --name 论文_中文正式稿 --abstract-name 正式论文_摘要 --output notes/formal_artifact_check.json --body-han-min 10000 --body-han-max 15000 --discussion-min-share 0.45
```

数字和引文核对为正式稿另立记录，不覆盖论坛稿的781处历史核查。引用格式调整与正文重编后的实际检查结果，见正式稿专属核验文件。字体、行距、模板未涵盖项及PDF预览的字体替代说明见[模板应用说明](format/中文模板_应用说明.md)。
