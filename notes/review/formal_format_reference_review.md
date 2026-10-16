# 正式稿参考文献模板格式修订独立复核

复核日期：2026年10月16日。结论：本轮书目格式修订通过；下述一处有来源依据的姓名分段更正已单列说明。此次只读检查正文、书目JSON、修订前快照、既存Crossref记录及相关PDF署名页，仅写本记录；未修改正文、数字claims、冻结文件，未运行或重跑统计分析。本记录不替代主数字核验。

## 核验快照与正文保全

- 新稿：`outputs/论文_中文正式稿.md`，34,419字节，SHA-256为`de25060b979292611b332e93da671f9ae455aa14f5f67738f8a108cc2b38c342`。
- 旧稿：`notes/formal_format_revision_20261016/pre_format/论文_中文正式稿.md`，32,604字节，SHA-256为`35f78f0daaf3eeb0a3ad50a8af87fc4462f07f7c6ecbdfa94caf0a70a0be9b83`。
- 自文件首字节至“`## 参考文献`”标题末字节（包含标题）的前25,108字节逐字节相同；其SHA-256均为`9aef7ec1ad3df75667aa48d28f2964bfc896ae8b6083390e0ebe86cfe7982116`。因此，本次书目修订未改变题名、摘要、正文、表图或正文引注。
- 本次书目依据`notes/formal_references.json`，其SHA-256为`3c3d497c5b7fcabb6bf6cff96bfbb6db8dccd7ab878a22d7b78b4c921099c3ca`。正文参考文献标题之后的全部内容，恰好等于42个`entry`按两个换行符连接的全文；每个条目在该稿出现一次，没有额外条目或遗漏条目。

## 范围、格式与源事实

42项作品及顺序与修订前JSON完全相同，含40篇期刊论文、1篇书章、1篇会议论文。逐项比较`id`、`author_year`、`year_label`、`document_type`、`title`、`doi`、`metadata`及三个来源路径字段，均无差异；旧`entry`、`authors_displayed`和`authors_normalized`分别完整保存在本轮对应的`*_gbt7714_snapshot`字段。旧规范化姓名与现行姓名不是逐字相同，不能将姓名格式转换误记为字段原样保留。

实际读取用户模板的Word正文XML，英文示例采用自然大小写姓氏、带点缩写、括号年份、末位作者前的“&”及DOI URL。本稿42条作者—年份—题名首部均按现行JSON正确生成；40条期刊书目均与“斜体刊名、卷(期)、页码或文章号、DOI URL”的既定模板格式逐字对应。D01按书章列单名作者、编者、斜体书名、页码、Amsterdam及出版社；B02按会议论文列四名作者、四名编者、斜体文集名及页码，未将知识库的47(0)展示值带入条目，未添加未知出版者。

39条已知DOI均保留原值并改为`https://doi.org/`形式；B02、A17、A15仍无DOI。Hallam的2025a与2025b继续对应各自原题名。刊名、卷期、页码或文章号字段无变化。A16继续保留期号17、文章号1374，未构造卷号。A02、A05、C08均未进入书目。

## 作者姓名与顺序核对

42条现行`authors_displayed`、`authors_normalized`及`authors_template_style`逐项相等，共176次作者列示（按作品累计，同一作者可重复）。39条有DOI文献的作者人数和顺序均对照本地Crossref作者数组；其中38条在忽略大小写、点号、空格及连字符字形之后，姓氏和所有名字首字母逐位相同。A16依据PDF自身署名及推荐引文处理，见下。无DOI的B02、A15、A17分别对照PDF第2页的完整署名。

| ID | 列示作者数 | 顺序与姓名依据 | 现稿全文与JSON、原出版字段 |
|---|---:|---|---|
| D03 | 2 | `literature/D_colexification/D03_crossref.json` | 相同、未变 |
| C12 | 3 | `notes/C/C12_crossref.json` | 相同、未变 |
| B12 | 4 | `notes/B/B12.json` | 相同、未变 |
| B13 | 2 | `notes/B/B13.json` | 相同、未变 |
| A20 | 1 | `notes/A/A20_crossref.json` | 相同、未变 |
| C06 | 1 | `notes/C/C06_crossref.json` | 相同、未变 |
| C11 | 10 | `notes/C/C11_crossref.json` | 相同、未变 |
| D01 | 1 | `literature/D_colexification/D01_crossref.json`及PDF首页 | 相同、未变 |
| B11 | 9 | `notes/B/B11.json` | 相同、未变 |
| A03 | 1 | `notes/A/A03_crossref.json` | 相同、未变 |
| A13 | 2 | `notes/A/A13_crossref.json` | 相同、未变 |
| A19 | 1 | `notes/A/A19_crossref.json` | 相同、未变 |
| A07 | 1 | `notes/A/A07_crossref.json` | 相同、未变 |
| B02 | 4 | PDF第2页，印刷5831页，完整署名与页脚编者 | 相同、未变 |
| B03 | 4 | `notes/B/B03.json` | 相同、未变 |
| D04 | 9 | `literature/D_colexification/helper/crossref_Jackson.json` | 相同、未变 |
| C01 | 1 | `notes/C/C01_crossref.json` | 相同、未变 |
| A14 | 1 | `notes/A/A14_crossref.json` | 相同、未变 |
| A10 | 1 | `notes/A/A10_crossref.json` | 相同、未变 |
| D06 | 5 | `literature/D_colexification/helper/crossref_Karjus.json` | 相同、未变 |
| B10 | 1 | `notes/B/B10.json` | 相同、未变 |
| B01 | 2 | `notes/B/B01.json` | 相同、未变 |
| B05 | 3 | `notes/B/B05.json` | 相同、未变 |
| B04 | 1 | `notes/B/B04.json` | 相同、未变 |
| A01 | 1 | `notes/A/A01_crossref.json` | 相同、未变 |
| A06 | 1 | `notes/A/A06_crossref.json` | 相同、未变 |
| A17 | 1 | PDF第2页，印刷203页，David B. Kronenfeld | 相同、未变 |
| A04 | 1 | `notes/A/A04_crossref.json` | 相同、未变 |
| B15 | 6 | `notes/B/B15.json` | 相同、未变 |
| B14 | 2 | `notes/B/B14.json` | 相同、未变 |
| A11 | 2 | `notes/A/A11_crossref.json` | 相同、未变 |
| A18 | 6 | `notes/A/A18_crossref.json` | 相同、未变 |
| A09 | 24 | `notes/A/A09_crossref.json`及PDF首页 | 相同、未变 |
| A16 | 1 | PDF首页署名及其推荐Citation；Crossref补充核对 | 相同、未变 |
| A12 | 3 | `notes/A/A12_crossref.json` | 相同、未变 |
| A15 | 1 | PDF第2页，作者稿第1页，Dwight W. Read | 相同、未变 |
| B08 | 3 | `notes/B/B08.json` | 相同、未变 |
| C04 | 14 | `notes/C/C04_crossref.json`及PDF首页 | 相同、未变 |
| D02 | 27 | `literature/D_colexification/D02_crossref.json`及PDF首页 | 相同、未变 |
| D05 | 5 | `literature/D_colexification/helper/crossref_Xu.json` | 相同、未变 |
| B06 | 4 | `notes/B/B06.json` | 相同、未变 |
| B16 | 4 | `notes/B/B16.json` | 相同、未变 |

重点三条的完整作者数组分别为：A09的`/author/0`至`/author/23`（24人）；D02的`/author/0`至`/author/26`（27人）；C04的`/message/author/0`至`/message/author/13`（14人）。现稿按原作者顺序全列，不再使用“et al.”截断。

### 姓名分段更正与来源展示差异

1. **D02第19作者。**旧规范化字段为`EPPS B V`，新条目为`Van Epps, B.`。`literature/D_colexification/D02_crossref.json`的`/author/18/family`明确为`Van Epps`，`/author/18/given`为`Briana`；对应PDF第1页完整作者名单中，Briana Van Epps位于Mariann Proos之后、Ingrid Blanco之前。新写法纠正复合姓氏与名字的拆分，作者身份和第19位顺序均未变。这不是纯大小写转换，已向主核验代理报告。其余175次姓名列示与旧完整规范化名单逐位比较，仅有大小写、空格、点号或连字符的排版转换，没有其他姓名分段或作者次序变化。
2. **A16已有来源展示差异。**`notes/A/A16_crossref.json`的`/author/0/given`为`Vladimir Borissov`，而PDF第1页正式署名为`VLADIMIR PERICLIEV`，同页推荐Citation明确写`Pericliev, V. (2017)`。现稿`Pericliev, V.`沿用旧稿`PERICLIEV V`并遵从该PDF的实际署名和推荐缩写；本轮没有增删首字母。

## 新增数字检查与本记录边界

新旧参考文献区提取的342个阿拉伯数字组逐个、按原顺序完全相同；176次作者姓名中均无阿拉伯数字。扩展作者名单未带入PDF脚注编号、机构编号或ORCID数字。因此，本轮书目没有新增数值或作者名中的未解释数字。主代理仍需按最终全文SHA重新执行数字claims核验，本记录不冒称已经执行该步骤。

本次核验未发现阻止交付的书目内容问题；唯一超出纯字形转换的D02姓名分段更正有双来源依据，已明确保留旧快照并单列披露。
