# 正式论文体例与引用修订记录

日期：2026年10月16日。依据作者要求，正式论文应采用学术摘要、连贯正文与统一引文格式，不混入下载时间等工程信息。此次沿用既有数据和估计，不运行新的统计比较。

## 已执行

- 新增`outputs/论文_中文正式稿.md`，重编六节正文与摘要；旧中文工作稿及论坛v2保留。正式摘要235汉字，仅保留样本规模939；正文6350汉字（含标题表图）。下载与执行时间、协议提交标识及审计过程移至`formal_reproducibility.md`。
- 42项书目采用GB/T 7714—2015著者出版年格式，含40篇期刊、1篇书章及1篇会议论文；39个已知DOI逐项核对，不为3个缺DOI来源编造标识。作者稿和Early View页码留在证据对照中，正文转述不强行套用正式印刷页。
- 正式稿53处文中引用、30处附页上标与42项来源对应；专属数字映射631处实际通过，94结果数值或实算设计秩、537逐项依据，mismatches为空。旧v2、旧claims及旧781报告SHA保护通过。
- 独立审读提出并修正：数据库注释不写成已验证释义；明确三种未加权二项VB混合模型；Firth触发包含分离或未收敛；保留NFC与权重归一化；空格形式不直接认定多词表达；摘要不把历史机制写成直接检验结论；交互项表述明确为附加系数；图2代码与表2对应。参照者性别限制补491页，D04补充页证据修为正文1–5加书目信息页。

## 实际命令

```bash
python analysis/map_formal_manuscript_numbers.py --check
python analysis/export_forum_documents.py --input outputs/论文_中文正式稿.md --name 论文_中文正式稿 --abstract-name 正式论文_摘要 --page-numbers
python analysis/audit_revision_artifacts.py --input outputs/论文_中文正式稿.md --name 论文_中文正式稿 --abstract-name 正式论文_摘要 --output notes/formal_artifact_check.json
pdftotext -layout outputs/论文_中文正式稿.pdf outputs/论文_中文正式稿.txt
```

数字命令退出0，631/631验证；artifact退出0，18页、4表2图、42书目，DOCX/PDF的6688个汉字顺序一致，六节完整。Word兼容统计正文7430、全稿8775，系LibreOffice刷新，不声称运行Microsoft Word。最新稿SHA为`35f78f0daaf3eeb0a3ad50a8af87fc4462f07f7c6ecbdfa94caf0a70a0be9b83`。

## 验收与交付

专属独立评审`notes/review/formal_paper_review.md`已给出正式稿范围通过结论，覆盖最后两变化页、631数字及53引用/42书目/30附页；原稿和原统计保持。最终Git提交后同步研究镜像和ZIP并生成外部实际哈希收据，不把旧601文件核验冒称当前快照。形式规范化不改变探索性定位、区间解释或混合模型未收敛事实。
