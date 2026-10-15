# 方法与数据标准文献核查记录（C01—C12）

已收录12篇独立论文。11篇保存期刊全文或期刊作者副本，1篇（C12）保存同题同作者的对应工作论文。全部PDF已核查题名与作者；C06、C07为扫描版，证据页已OCR核对。没有仅凭元数据列入的条目。

## [C01] Categorical data analysis: Away from ANOVAs (transformation or not) and towards logit mixed models

T. Florian Jaeger. (2008). *Categorical data analysis: Away from ANOVAs (transformation or not) and towards logit mixed models*. *Journal of Memory and Language*, 59(4), 434-446. https://doi.org/10.1016/j.jml.2007.11.007

本文比较比例数据的方差分析、逻辑回归和混合逻辑回归，展示比例变换仍可能造成误导性主效应或交互，并说明二元结果的建模尺度。

将共享词形编码为二元结果，明确加性是在 logit 尺度上定义；语言内重复配对需要相应的依赖处理。

全文：[PDF](/workspace/kinship_research/literature/C/C01.pdf)；[来源](https://garstats.wordpress.com/wp-content/uploads/2016/08/jaeger-jml-2008.pdf)。

- 二元结果适合逻辑回归；混合逻辑回归能联合处理交叉的分组差异。（第434页摘要；第442—443页，Mixed logit models）
- 对比例直接作方差分析，即使使用反正弦平方根变换，也可能得到与逻辑模型不同的交互结论。（第438—440页，例示数据与ANOVA比较）

## [C02] Random effects structure for confirmatory hypothesis testing: Keep it maximal

Dale J. Barr; Roger Levy; Christoph Scheepers; Harry J. Tily. (2013). *Random effects structure for confirmatory hypothesis testing: Keep it maximal*. *Journal of Memory and Language*, 68(3), 255-278. https://doi.org/10.1016/j.jml.2012.11.001

利用模拟讨论确认性检验的随机效应结构与推广范围，强调由研究设计支持的随机斜率，而不仅是随机截距。

语系之间可能存在特征效应差异，不能把语系随机截距等同于对所有谱系依赖的完整处理；本研究可用语系分层与留语系验证检验可推广性。

全文：[PDF](/workspace/kinship_research/literature/C/C02.pdf)；[来源](https://www.mit.edu/~rplevy/papers/barr-etal-2013-jml.pdf)。

- 随机效应结构表达抽样单位之间的差异及研究结论的推广假设。（第255页摘要；第257—260页，模型结构与随机斜率）
- 在其模拟的重复测量设计中，忽略存在的随机斜率会提高第一类错误率。（第257页研究发现概述；第260—262页）

## [C03] Fitting Linear Mixed-Effects Models Using lme4

Douglas Bates; Martin Mächler; Benjamin M. Bolker; Steven C. Walker. (2015). *Fitting Linear Mixed-Effects Models Using lme4*. *Journal of Statistical Software*, 67(1), None. https://doi.org/10.18637/jss.v067.i01

介绍 lme4 中线性混合模型的公式表示、最大似然及限制最大似然估计、稀疏矩阵计算与优化。

为计划中的层级模型提供实现与诊断背景；若实际采用Python惩罚逻辑回归，不将该论文列作已执行软件的依据。

全文：[PDF](/workspace/kinship_research/literature/C/C03.pdf)；[来源](https://www.jstatsoft.org/article/view/v067i01/v67i01.pdf)。

- lme4 用公式联合指定固定与随机效应；本文详细阐述的是线性混合模型。（第1页摘要与引言；第2页说明广义和非线性模型将另文讨论）
- 模型参数化和优化需容许随机效应协方差出现奇异或边界情形。（第13页式10；第18页；第24—25页优化讨论）

作者姓名按PDF首页核对，使用Benjamin M. Bolker、Steven C. Walker，而非Crossref简写Ben、Steve。

## [C04] Cross‐validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure

David R. Roberts; Volker Bahn; Simone Ciuti; Mark S. Boyce; Jane Elith; Gurutzeta Guillera‐Arroita; Severin Hauenstein; José J. Lahoz‐Monfort; Boris Schröder; Wilfried Thuiller; David I. Warton; Brendan A. Wintle; Florian Hartig; Carsten F. Dormann. (2017). *Cross‐validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure*. *Ecography*, 40(8), 913-929. https://doi.org/10.1111/ecog.02881

综述有时间、空间、层级或系统发育结构的数据验证方法，并以模拟和案例比较随机与分块交叉验证。

主要结果按语系整组留出、至少按语言整组留出；与训练语系相关的新语言预测和全新语系预测属于不同推广目标。

全文：[PDF](/workspace/kinship_research/literature/C/C04.pdf)；[来源](https://www.biometrie.uni-freiburg.de/mitarbeiter/dormann/roberts-et-al-2017-ecography.pdf/at_download/file)。

- 忽略依赖结构的随机交叉验证常低估预测误差，使用混合模型也不自动解决这一问题。（第913页摘要；第914页；第915页，分块验证讨论）
- 分块方式应对应推广目标，并检查其是否引入预测变量范围的外推。（第913页摘要；第914页表1；第925—927页讨论）

参考文献年份采用正式卷期2017；2016为接受稿上线年份。最终PDF采用作者所在大学提供的公开文件。

## [C05] A weakly informative default prior distribution for logistic and other regression models

Andrew Gelman; Aleks Jakulin; Maria Grazia Pittau; Yu-Sung Su. (2008). *A weakly informative default prior distribution for logistic and other regression models*. *The Annals of Applied Statistics*, 2(4), 1360-1383. https://doi.org/10.1214/08-AOAS191

提出缩放预测变量后对逻辑回归系数使用弱信息 Student-t 先验，默认Cauchy先验能够稳定稀疏或分离数据中的估计，并收缩高阶交互。

记录分离和稀疏单元；预先固定正则化策略，对主效应和交互模型采用相同训练程序。Cauchy先验与L2惩罚是不同估计方法。

全文：[PDF](/workspace/kinship_research/literature/C/C05.pdf)；[来源](https://arxiv.org/pdf/0901.4011)。

- 完全分离会使普通逻辑回归估计不稳定；合适的弱信息先验可产生稳定的正则化估计。（期刊第1360—1362页；arXiv重印PDF第1—3页）
- 论文默认建议非二元变量先缩放到均值0、标准差0.5，再使用中心0、尺度2.5的Cauchy先验。（期刊第1360页摘要；重印PDF第1页）

公开PDF为arXiv存档的期刊重印版；正文分页与期刊版可能不同，证据定位同时注明两个版本。

## [C06] Bias reduction of maximum likelihood estimates

David Firth. (1993). *Bias reduction of maximum likelihood estimates*. *Biometrika*, 80(1), 27-38. https://doi.org/10.1093/biomet/80.1.27

在一般参数模型中修改得分方程以去除最大似然估计的一阶渐近偏差；在规范参数化指数族中，对应Jeffreys先验惩罚。

将Firth偏差减少列为稀疏逻辑模型的备选估计方法，明确其与L2正则化及贝叶斯弱信息先验的区别。

全文：[PDF](/workspace/kinship_research/literature/C/C06.pdf)；[来源](https://www2.stat.duke.edu/~sschmid/Courses/Stat376/Papers/GibbsFieldEst/BiasReductionMLE.pdf)。

- 修改得分函数可去除最大似然估计的一阶偏差；规范指数族中的调整可写成Jeffreys先验惩罚。（第27页Summary；第28页Introduction，OCR已核查）
- 作者针对小中样本中最大似然估计可能为无穷大的情形，发展不依赖原估计有限性的调整。（第28页Introduction，OCR已核查）

扫描PDF；已对题名、作者、摘要及所引用页作OCR核查。

## [C07] Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing

Yoav Benjamini; Yosef Hochberg. (1995). *Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing*. *Journal of the Royal Statistical Society Series B: Statistical Methodology*, 57(1), 289-300. https://doi.org/10.1111/j.2517-6161.1995.tb02031.x

将错误发现率定义为被拒绝假设中错误拒绝比例的期望，提出控制该率的逐步程序，并讨论其功效。

只对预先列出的探索性系数族报告多重检验校正，同时保留效应量和区间；本研究依赖检验的适用条件须单独评估。

全文：[PDF](/workspace/kinship_research/literature/C/C07.pdf)；[来源](https://www.math.tau.ac.il/~ybenja/MyPapers/benjamini_hochberg1995.pdf)。

- 错误发现率衡量被拒绝假设中错误拒绝比例的期望。（第289页Summary，扫描PDF第2页，OCR已核查）
- 原论文给出的控制证明以独立检验统计量为条件。（第289页Summary，扫描PDF第2页，OCR已核查）

扫描PDF；已对题名、作者、摘要及所引用页作OCR核查。

## [C08] Mixed effect models for genetic and areal dependencies in linguistic typology

T. Florian Jaeger; Peter Graff; William Croft; Daniel Pontillo. (2011). *Mixed effect models for genetic and areal dependencies in linguistic typology*. *Linguistic Typology*, 15(2), None. https://doi.org/10.1515/lity.2011.021

以跨语言音系多样性研究为案例，介绍混合模型控制语系、次级谱系和地域关系，并讨论随机斜率、稀疏抽样和模型选择带来的推断问题。

直接支撑语系与地域依赖控制；在语系内和语系间分别检查效应，并用整组验证评估可推广性。

全文：[PDF](/workspace/kinship_research/literature/C/C08.pdf)；[来源](https://www.researchgate.net/profile/T-Florian-Jaeger/publication/229079011_Mixed_effect_models_for_genetic_and_areal_dependencies_in_linguistic_typology/links/0912f500d7d933761e000000/Mixed-effect-models-for-genetic-and-areal-dependencies-in-linguistic-typology.pdf)。

- 语系随机截距能够处理部分谱系相关，但语系间效应斜率差异需要进一步建模或检验。（第285页；第287—289页，式E3与后续讨论）
- 作者展示如何扩展混合模型以纳入语言接触和地域依赖。（第285页概述；第290—296页地域控制讨论）

作者在ResearchGate公开上传的39页作者副本；该评论文章无独立摘要，不将开头正文误标为abstract。

## [C09] Evolved structure of language shows lineage-specific trends in word-order universals

Michael Dunn; Simon J. Greenhill; Stephen C. Levinson; Russell D. Gray. (2011). *Evolved structure of language shows lineage-specific trends in word-order universals*. *Nature*, 473(7345), 79-82. https://doi.org/10.1038/nature09923

在四个有可用谱系树的大语系中，用系统发育方法比较语序特征的独立与依赖演化，指出所观察到的特征依赖具有谱系差异。

将语系层面的异质性作为亲属语义交互的解释维度；语序研究结论提供方法参照，不作为亲属称谓交互的直接证据。

全文：[PDF](/workspace/kinship_research/literature/C/C09.pdf)；[来源](https://pure.mpg.de/rest/items/item_95245_23/component/file_894565/content)。

- 论文在所研究的语序特征中发现许多依赖关系具有谱系特异性。（第79页摘要；第81—82页结果与讨论）
- 共同继承会影响类型学相关的解释；本文通过语系内演化比较处理共同祖先的影响。（第79页正文；补充材料S1与S1.4）

MPI官方页面公开提供论文及补充材料；主文为file_894565，补充材料为file_852605，已按内容核查。额外保存补充材料C09_supplement.pdf，不额外计文献数量。

## [C10] D-PLACE: A Global Database of Cultural, Linguistic and Environmental Diversity

Kathryn R. Kirby; Russell D. Gray; Simon J. Greenhill; Fiona M. Jordan; Stephanie Gomes-Ng; Hans-Jörg Bibiko; Damián E. Blasi; Carlos A. Botero; Claire Bowern; Carol R. Ember; Dan Leehr; Bobbi S. Low; Joe McCarter; William Divale; Michael C. Gavin. (2016). *D-PLACE: A Global Database of Cultural, Linguistic and Environmental Diversity*. *PLOS ONE*, 11(7), e0158391. https://doi.org/10.1371/journal.pone.0158391

D-PLACE联结文化变量、语言分类与谱系树、地理位置及环境数据，支持检验文化多样性的历史与空间结构。

为语系与地域信息的连接和非独立性控制提供数据库方法背景；社会/文化附加变量只在明确可对应的扩展分析中使用。

全文：[PDF](/workspace/kinship_research/literature/C/C10.pdf)；[来源](https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0158391&type=printable)。

- 文化组之间的空间与谱系非独立性分别关联Tobler规律和Galton问题。（PDF第2页，引言）
- 数据库通过语言分类、谱系树和地理坐标把不同类型数据联系起来。（PDF第3页图1；第8—10页，Language classifications and phylogenies）

## [C11] Cross-Linguistic Data Formats, advancing data sharing and re-use in comparative linguistics

Robert Forkel; Johann-Mattis List; Simon J. Greenhill; Christoph Rzymski; Sebastian Bank; Michael Cysouw; Harald Hammarström; Martin Haspelmath; Gereon A. Kaiping; Russell D. Gray. (2018). *Cross-Linguistic Data Formats, advancing data sharing and re-use in comparative linguistics*. *Scientific Data*, 5(1), None. https://doi.org/10.1038/sdata.2018.205

CLDF规定可机器读取的跨语言数据结构，以语言、比较概念、观测值和来源为核心对象，并用CSVW元数据描述表间关系。

保留Kinbank的语言、关系类别、词形与来源标识；冻结数据版本并保存可复现的表格、元数据和原始来源，减少跨语言合并误配。

全文：[PDF](/workspace/kinship_research/literature/C/C11.pdf)；[来源](https://www.nature.com/articles/sdata2018205.pdf)。

- CLDF区分语言、参数/比较概念、值和来源，支持显式描述表格关系。（PDF第3—5页，数据模型与The CLDF Specification；图2）
- 标准目录标识符能够连接Glottolog语言标识与Concepticon概念标识。（PDF第6页，数据标识与目录连接讨论）

## [C12] Bootstrap-Based Improvements for Inference with Clustered Errors

A. Colin Cameron; Jonah B. Gelbach; Douglas L. Miller. (2008). *Bootstrap-Based Improvements for Inference with Clustered Errors*. *Review of Economics and Statistics*, 90(3), 414-427. https://doi.org/10.1162/rest.90.3.414

研究聚类误差下的bootstrap推断，以OLS和有限聚类数的模拟为重点，比较整组重抽样及wild cluster bootstrap等方法。

对样本外损失差的区间估计以语系为重抽样单位，保留每个语系内全部语言与配对；本文为结构依据，非对本研究具体估计量的已证明有限样本保证。

全文：[PDF](/workspace/kinship_research/literature/C/C12.pdf)；[来源](https://www.nber.org/papers/t0344.pdf)。

- 整组pairs cluster bootstrap重抽样整个聚类，保持聚类内部的相关结构。（所下载NBER2007工作论文第12页，PDF第14页，§3.1）
- 少量聚类会影响常规聚类稳健推断的表现，论文比较bootstrap修正。（工作论文第2—4页，PDF第4—6页；正式版摘要）

正式书目为2008年Review of Economics and Statistics论文；下载的是同题同作者NBER Technical Working Paper344（2007年9月）对应工作论文，不能称为已获得2008年排版全文。正式版下载失败。
