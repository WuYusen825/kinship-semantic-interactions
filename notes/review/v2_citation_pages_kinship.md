# 论坛稿 v2：A 系列逐处引文与页码核查

核查对象：`outputs/forum/论坛稿_v2.md`。本表实际回读正文已使用的 **17 份 A 系列全文、26 处作者—年份引文**，不把登记表或候选证据库等同于核查完成。26 处中，20 处正文带定位页码，6 处为无定位页的概括性引用。正文参考文献中的重复书目信息不计为新的命题引用。

已检查的正文快照 SHA-256：`038a137480b962b77d68322b1e200595b023b739aa4dc1d8469bb85ddf5bd59b`。核查日期：2026-10-15。正文若增删引用，应在最终交付前重核新增处；本表不自动覆盖未来修订。

## 核查方法与页码约定

逐处对照正文命题与本地 PDF 的实际文字；用 PyMuPDF 直接读取原 PDF 对应页，并在必要处回看页面图像，未仅搜索标题、摘要数据库或文献登记表。本次另实际渲染回看了 A06 的 PDF 9、A12 的 PDF 12、A17 的 PDF 15、A18 的 PDF 13，图像留在 `notes/review/page_images_kinship/`。其页头／页脚分别确认为印页 496、Early View 第 11 页、印页 216、印页 188。

以下“PDF 页”均从文件第一页起按 1 计数；“正文引用页”沿用所读版本印出的页码。A12 的来源是带机构封面的 2019 Early View 1–22 页版本，正文已明确标注 Early View；参考文献所列 2020 正式卷期 744–765 不是本次定位页码。A15 是作者稿页码，不能以简单加减自动换算为正式印页。

## 逐处命题检查

| 编号 | 正文位置及命题 | 来源 | 正文引用页；实际 PDF 页 | 实读证据及判定 |
|---|---|---|---|---|
| AK01 | 引言：性别、代际、长幼等维度早已用于亲属分类 | A01 Kroeber 1909 | 未标页；印页 78＝PDF 3 | 作者列出 eight categories，其中包括 generation、age within one generation、sex of relative、sex of speaker。支持所引概括。未把文中的早期历史判断当作本文新增发现。 |
| AK02 | 引言：合取、层级及次级区分侧向的经典要求 | A06 Kronenfeld 1974 | 490–491；PDF 3–4 | 490 定义八类及 neat partition，491 列出四个特征、primary/secondary/tertiary 及五项附加假说。支持。此为 Kronenfeld 对 Nerlove 与 Romney 的转述及讨论，未读取到 A02 全文。 |
| AK03 | 引言：约束排序解释术语组织 | A14 Jones 2010 | 未标页；印页 367–368＝PDF 1–2 | 摘要写不同语言来自 universal constraints 的不同 rankings；368 解释严格支配及约束冲突。支持。此处仅引 Jones 本文，不使用同一 PDF 后附评论。 |
| AK04 | 引言：术语生成运算解释体系 | A15 Read 2007 | 未标页；作者稿 1＝PDF 2 | 摘要明确区分 genealogical tracing 与 kin term products 的逻辑，并讨论 generative logic。支持。来源为机构封面加作者稿，不把作者稿第 1 页误标为正式 329 页。 |
| AK05 | 引言：数据库词形记录受来源影响 | A09 Passmore et al. 2023 | 未标页；文章 6–7＝PDF 6–7 | 第 6 页区分 true absence 与 source uncertainty；第 7 页交代来源粒度较粗时复制至各细类、保留来源转写及其跨来源不一致。修订后措辞直接受支持。 |
| AK06 | 引言：术语分类模式带有谱系结构 | A16 Pericliev 2017 | 未标页；文章 1、7–8＝PDF 1、7–8 | 检验单位是 kin term patterns，1 页摘要称其为 genetic affiliation 的 strong indicators，7–8 页给出语系区分结果。正文已从“亲属形式带有谱系信息”收紧为“术语分类模式……谱系结构”，支持。不能据此声称该研究检验了词形相似或同源词。 |
| AK07 | 综述（一）：同一用法有多种概念方案 | A03 Goodenough 1956 | 211–213；PDF 18–20 | §7.5 “Alternative concepts and structures” 明示 Paradigms 1、3、4 均能预测相同 denotata，并比较变量数与同音异义分析的取舍。支持。 |
| AK08 | 综述（一）：无独立语音形式不表示语义对立不存在 | A04 Lounsbury 1956 | 161–162；PDF 5–6 | 161 区分 overtly 与 covertly recognized semantic features；162 明示对比是否具有 segmental correlates 不妨碍成分结构分析。支持。没有把这里改述成多套替代概念方案。 |
| AK09 | 综述（一）：一、二、三级作用域及次级侧向 | A06 Kronenfeld 1974 | 491；PDF 4 | 本页定义 8→4、4→2、2→1 的范围，列出 sex under age 在 elder 侧、age under sex 在 male 侧、age under relative sex 在 same-sex 侧。支持。 |
| AK10 | 综述（一）：Fanti 合取词项重叠，合取不等于整套无重叠划分 | A06 Kronenfeld 1974 | 501；PDF 14 | 作者写 Fanti “preserving conjunctivity—even at the price of having overlapping terms”，并明确其不属于 neat partition 的 4140 宇宙。支持。 |
| AK11 | 综述（一）：Nuba 男性侧条件区分与多义重分析 | A20 Faris 1969 | 483–484；PDF 3–4 | 483 写 cross-sex/parallel-sex distinction “exclusive to male speakers”；484 将 polysemic morpheme 视为两个 homonyms 后获得合取系统。支持。正文没有把初步表面析取当作已经确认的析取语义。 |
| AK12 | 综述（一）：标记、历史及年龄标记非恒定 | A19 Hage 1997 | 662–663；PDF 11–12 | 662 的历史替换顺序把 male、younger、parallel 视为未标记；663 说明 elder 在许多 Malayo-Polynesian 语言为 marked，并将合取表达为倾向及分析目标。支持。 |
| AK13 | 综述（一）：年龄标记并非文化上恒定 | A07 Hage 2001 | 204–205；PDF 8–9 | 204 直接写 seniority “is not marked on a universal basis”；205 说明 younger parallel sibling 在年龄对立中和时替代 elder，并强调 given culture or epoch。支持。 |
| AK14 | 综述（一）：Kronenfeld 后来改为可省略参照者性别 | A06 Kronenfeld 1974 | 498–499；PDF 11–12 | 498 说明所有 sex-of-speaker 的三级区分可由 sex-of-relative 或 relative-sex 替代；499 因而主张 “can be dispensed with” 并替换原第五项假说。支持，已区分于原“只作三级”。 |
| AK15 | 综述（二）：分别追踪年龄和相对性别历史，把共同变化留待后续 | A10 Jordan 2011 | 302、315–316；PDF 7、20–21 | 302 提出分别追踪 distinction；315 说明模型追踪 independent histories；316 把 meaning–meaning coevolution 及 age/sex tightly coupled 留为后续可检验对象。支持。 |
| AK16 | 综述（二）：跨三个语系未支持单一普遍演化路径 | A11 Passmore & Jordan 2020 | 3–5；PDF 3–5 | 3 明确三语系 Austronesian、Bantu、Uto-Aztecan；5 比较六状态转换，存在共享子路径但各系有不同转换与可逆性。支持，正文未把结果扩展到所有语言。 |
| AK17 | 综述（二）：堂表亲类型复杂度与社会实践及共享历史相关 | A12 Rácz et al. 2020 | Early View 7–11；PDF 8–12 | 7–10 定义 cousin-term complexity、社会实践及语系／地域分组；11 的结果报告语言家族与区域、descent 和 cousin marriage 的关联。正文已经用“相关”替换“受……影响”，与观察设计相符。支持。 |
| AK18 | 综述（二）：班图亲属类型与社会组织共同演化的证据有限 | A13 Guillon & Mace 2016 | 1；PDF 1 | 本页完整摘要直接报告 phylogenetic co-evolution hypothesis 仅获 limited support；对象是 Bantu cousin terminology、descent 与 residence。支持。该处虽定位摘要，但实际全文 PDF 可得，不属于未下载清单。 |
| AK19 | 综述（二）：跨代共选发现大量混合类型 | A18 Passmore et al. 2021 | 182–184；PDF 7–9 | 183 显示多数非对角组合有记录，184 判定内部共选存在但非强、确定性的关系。支持。正文没有把“混合”误写为所有内部关系都无结构。 |
| AK20 | 综述（二）：共选研究以连续词形距离构造体系空间 | A18 Passmore et al. 2021 | 187–188；PDF 12–13 | 187 的二元串是示意；实际研究在 188 对 40 类词项用 Optimal String Alignment 得连续匹配，构造 780 特征，再作 HDBSCAN 与 UMAP。支持，正文已与二元共享形式区分。 |
| AK21 | 综述（四）：修饰语、词素与词项须区别处理 | A17 Kronenfeld 2006 | 216；PDF 15 | Typological Base 6 比较 English brother/sister、Spanish herman-o/-a 与 Fanti nua 加一般性别修饰词，并问 typological analysis 应计算何种单位。支持。 |
| AK22 | 方法（一）：Kinbank 来源、语言、关系与词形的资料关联 | A09 Passmore et al. 2023 | 未标页；文章 6–7＝PDF 6–7 | 第 7 页说明每条记录附 source reference、notes 及 CLDF 数据格式。支持数据库说明；锁定提交号、筛选样本量属本研究出处／结果，由数值核查单独验证，不由该文证明。 |
| AK23 | 方法（二）：经典 236／442 及现代精确枚举不一致的透明报告 | A06 Kronenfeld 1974 | 502–503；PDF 15–16 | 503 Table 2 分别列 442 conjunctively defined、去除 sex-of-elder/younger 后 236；502 表注说明层级分配存在顺序与歧义处理。支持引用的经典数字。本文 260／518 等为新算法结果，不能由此引文背书。 |
| AK24 | 方法（二）：P5 针对原三级限制，与随后可省略 s 的修订分开 | A06 Kronenfeld 1974 | 491、498–499；PDF 4、11–12 | 前者是转述原第五项，后者提出替换。支持。合法树存在性与本文递归树定义由协议另证，不冒充原文逐字算法。 |
| AK25 | 讨论（一）：侧向假说概括为未标记侧，male／elder 为未标记 | A06 Kronenfeld 1974 | 496；PDF 9 | 本页将原假说 2、3 合并为 secondary features 在 unmarked side，并明说 “Male and elder are assumed to be unmarked”。修订后的具体表述受支持。原“方向假设与修订不完全一致”已撤换。 |
| AK26 | 讨论（一）：Hage 的年龄标记非普遍及大洋洲 younger 未标记 | A07 Hage 2001 | 204–205；PDF 8–9 | 与 AK13 相同实际页面；205 的中和及历史替换支持 younger 项的未标记地位。支持，不声称所有文化均以 younger 未标记。 |

## 本次发现与已落实修订

1. A16 研究的是类别划分模式与语系，原“亲属形式……带有谱系信息”超出其具体分析单位。现改为词形受来源影响、术语分类模式有谱系结构，分别对应 A09 与 A16。
2. A12 为观察性跨文化模型，原“受……影响”容易带出因果。现改为“与社会实践及共享历史相关”。引用的 Early View 7–11 页正确，不能改写成正式印页 7–11。
3. A06 496 页的标记性修订扩展／概括两项方向假说，并没有把 male／elder 方向倒置。现已把笼统“不完全一致”改为具体的未标记侧概括，再与 Hage 的文化和历史差异相对话。

以上三项已在所列快照中实际确认。未发现尚待修复的 A 系列错页或超出上述范围的主要命题错配。

## 来源覆盖与书目边界

实际检查的来源为 A01、A03、A04、A06、A07、A09、A10、A11、A12、A13、A14、A15、A16、A17、A18、A19、A20。均使用 `outputs/文献登记表.json` 指向的实际本地 PDF；除 A15 的作者稿及 A12 明示的 Early View 外，定位页采用印出的文章页。

A02、A05 未进入本轮正文引文；A08 没有在当前正文引用，未计入已核查的 17 份来源。正文对 Nerlove 与 Romney 的命题由实际读到的 A06 二手转述支撑，不伪装成已读 A02。A06 的 4140、236、442 仅说明经典严格划分分析的计数范围；不把同义词导致的重叠外延强制当作该范围内的严格划分。

## 附录：讨论新增四项颜色研究的实际全文复核

追加核查 B06、B08、B11、B16，共 **4 份实际 PDF、4 处无定位页概括引文**。连同上述 A 系列，本报告覆盖 21 份来源、30 处正文命题引文。此处不把颜色证据直接外推为兄弟姐妹术语的因果机制；正文将其作为待进一步检验的解释候选。

| 编号 | 当前概括命题 | 实际阅读范围及版本 | 支持程度 |
|---|---|---|---|
| BK01 | Regier et al. 2007：非均匀知觉颜色空间中的优化解释类别 | B08 PDF 1–3，印页 1436–1438 | 1436 明示 irregularly shaped perceptual color space；1437 将刺激映入不规则的 CIELAB 空间，并定义类内相似大、类间相似小的 well-formedness 优化。支持当前概括。该文采用 hard mode-map partitions，不能倒述为本就采用软边界。 |
| BK02 | Zaslavsky et al. 2018：信息瓶颈容纳软边界 | B06 PDF 1–3、5，来源为标有 “PNAS Latest Articles / n of 6”的 6 页在线全文 | 第 1 页摘要、第 3 页式 7 及第 5 页结果／讨论直接说明有限信息损失下有效编码可产生 soft categories、低一致命名，并比较复杂度—准确性权衡。支持。这里没有引用最终卷期印页，不能未经核对将在线 PDF 页码当作 7937 起的定位页。 |
| BK03 | Gibson et al. 2017：颜色用途资料强调交际需要 | B11 PDF 2、3、5–6；机构封面后 PDF 2＝正式印页 10785，PDF 5＝10788，PDF 6＝10789 | 10785 摘要和 significance 直接提出 use／communicative needs；10788 实际比较自然图像中的对象／背景颜色、不同人群的颜色用词及人工／自然物体。支持当前“强调”表述。本文不把原作者的因果解释措辞当作本研究已经识别的因果机制。 |
| BK04 | Zaslavsky et al. 2019：交际需要超出知觉结构单独预测的迹象 | B16 PDF／Early View 1、4–6、8–11；PDF 标头为 2018 Early View 1–13，正式书目为 2019、207–219 | 4–6 页显示暖冷不对称可能同由知觉空间产生；8–10 页比较 WCS-CAP、KM-CAP 和独立取得的显著性加权先验，第 10 页给出 need beyond what perceptual factors predict 的证据；第 11 页又指出两者可能共同适应于自然统计。因此，“独立贡献”容易暗示已证明机制独立，应改为“后续分析又发现知觉结构之外的交际需要迹象”。修订通知已发给正文作者；待实际复查落实后关闭此项。 |

B16 待改项是在正文快照 `ec30ab0146e8e8595d1cdeb14866ad3de4ff3f33f56d870edf3adaa0b53a2392` 中实际发现，并非假定存在的风险。其余三项未发现命题或来源不配。四项当前均未指定正文定位页，本附录记录所读版本与证据页以便复查，未替作者自动增加页码。
