# 当前全文来源与证据位置

2026年10月15日更新。主要PDF与TXT以文献登记表为准；未取得全文者不进入正式引用。

## C01 Categorical data analysis: Away from ANOVAs (transformation or not) and towards logit mixed models

[PDF](../../literature/C/C01_Jaeger_2008_Categorical_data_analysis_Away_from_ANOVAs_transformation_or_not_and_towards_logit_mixed.pdf)｜[TXT](../../literature/C/C01_Jaeger_2008_Categorical_data_analysis_Away_from_ANOVAs_transformation_or_not_and_towards_logit_mixed.txt)

本文比较比例数据的方差分析、逻辑回归和混合逻辑回归，展示比例变换仍可能造成误导性主效应或交互，并说明二元结果的建模尺度。

- 二元结果适合逻辑回归；混合逻辑回归能联合处理交叉的分组差异。（第434页摘要；第442—443页，Mixed logit models）。
- 对比例直接作方差分析，即使使用反正弦平方根变换，也可能得到与逻辑模型不同的交互结论。（第438—440页，例示数据与ANOVA比较）。

## C02 Random effects structure for confirmatory hypothesis testing: Keep it maximal

[PDF](../../literature/C/C02_Barr_2013_Random_effects_structure_for_confirmatory_hypothesis_testing_Keep_it_maximal.pdf)｜[TXT](../../literature/C/C02_Barr_2013_Random_effects_structure_for_confirmatory_hypothesis_testing_Keep_it_maximal.txt)

利用模拟讨论确认性检验的随机效应结构与推广范围，强调由研究设计支持的随机斜率，而不仅是随机截距。

- 随机效应结构表达抽样单位之间的差异及研究结论的推广假设。（第255页摘要；第257—260页，模型结构与随机斜率）。
- 在其模拟的重复测量设计中，忽略存在的随机斜率会提高第一类错误率。（第257页研究发现概述；第260—262页）。

## C03 Fitting Linear Mixed-Effects Models Using lme4

[PDF](../../literature/C/C03_Bates_2015_Fitting_Linear_Mixed_Effects_Models_Using_lme4.pdf)｜[TXT](../../literature/C/C03_Bates_2015_Fitting_Linear_Mixed_Effects_Models_Using_lme4.txt)

介绍 lme4 中线性混合模型的公式表示、最大似然及限制最大似然估计、稀疏矩阵计算与优化。

- lme4 用公式联合指定固定与随机效应；本文详细阐述的是线性混合模型。（第1页摘要与引言；第2页说明广义和非线性模型将另文讨论）。
- 模型参数化和优化需容许随机效应协方差出现奇异或边界情形。（第13页式10；第18页；第24—25页优化讨论）。

## C04 Cross‐validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure

[PDF](../../literature/C/C04_Roberts_2017_Crossvalidation_strategies_for_data_with_temporal_spatial_hierarchical_or_phylogenetic_s.pdf)｜[TXT](../../literature/C/C04_Roberts_2017_Crossvalidation_strategies_for_data_with_temporal_spatial_hierarchical_or_phylogenetic_s.txt)

综述有时间、空间、层级或系统发育结构的数据验证方法，并以模拟和案例比较随机与分块交叉验证。

- 忽略依赖结构的随机交叉验证常低估预测误差，使用混合模型也不自动解决这一问题。（第913页摘要；第914页；第915页，分块验证讨论）。
- 分块方式应对应推广目标，并检查其是否引入预测变量范围的外推。（第913页摘要；第914页表1；第925—927页讨论）。

## C05 A weakly informative default prior distribution for logistic and other regression models

[PDF](../../literature/C/C05_Gelman_2008_A_weakly_informative_default_prior_distribution_for_logistic_and_other_regression_models.pdf)｜[TXT](../../literature/C/C05_Gelman_2008_A_weakly_informative_default_prior_distribution_for_logistic_and_other_regression_models.txt)

提出缩放预测变量后对逻辑回归系数使用弱信息 Student-t 先验，默认Cauchy先验能够稳定稀疏或分离数据中的估计，并收缩高阶交互。

- 完全分离会使普通逻辑回归估计不稳定；合适的弱信息先验可产生稳定的正则化估计。（期刊第1360—1362页；arXiv重印PDF第1—3页）。
- 论文默认建议非二元变量先缩放到均值0、标准差0.5，再使用中心0、尺度2.5的Cauchy先验。（期刊第1360页摘要；重印PDF第1页）。

## C06 Bias reduction of maximum likelihood estimates

[PDF](../../literature/C/C06_Firth_1993_Bias_reduction_of_maximum_likelihood_estimates.pdf)｜[TXT](../../literature/C/C06_Firth_1993_Bias_reduction_of_maximum_likelihood_estimates.txt)

在一般参数模型中修改得分方程以去除最大似然估计的一阶渐近偏差；在规范参数化指数族中，对应Jeffreys先验惩罚。

- 修改得分函数可去除最大似然估计的一阶偏差；规范指数族中的调整可写成Jeffreys先验惩罚。（第27页Summary；第28页Introduction，OCR已核查）。
- 作者针对小中样本中最大似然估计可能为无穷大的情形，发展不依赖原估计有限性的调整。（第28页Introduction，OCR已核查）。

## C07 Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing

[PDF](../../literature/C/C07_Benjamini_1995_Controlling_the_False_Discovery_Rate_A_Practical_and_Powerful_Approach_to_Multiple_Testi.pdf)｜[TXT](../../literature/C/C07_Benjamini_1995_Controlling_the_False_Discovery_Rate_A_Practical_and_Powerful_Approach_to_Multiple_Testi.txt)

将错误发现率定义为被拒绝假设中错误拒绝比例的期望，提出控制该率的逐步程序，并讨论其功效。

- 错误发现率衡量被拒绝假设中错误拒绝比例的期望。（第289页Summary，扫描PDF第2页，OCR已核查）。
- 原论文给出的控制证明以独立检验统计量为条件。（第289页Summary，扫描PDF第2页，OCR已核查）。

## C08 Mixed effect models for genetic and areal dependencies in linguistic typology

[PDF](../../literature/C/C08_Jaeger_2011_Mixed_effect_models_for_genetic_and_areal_dependencies_in_linguistic_typology.pdf)｜[TXT](../../literature/C/C08_Jaeger_2011_Mixed_effect_models_for_genetic_and_areal_dependencies_in_linguistic_typology.txt)

以跨语言音系多样性研究为案例，介绍混合模型控制语系、次级谱系和地域关系，并讨论随机斜率、稀疏抽样和模型选择带来的推断问题。

- 语系随机截距能够处理部分谱系相关，但语系间效应斜率差异需要进一步建模或检验。（第285页；第287—289页，式E3与后续讨论）。
- 作者展示如何扩展混合模型以纳入语言接触和地域依赖。（第285页概述；第290—296页地域控制讨论）。

## C09 Evolved structure of language shows lineage-specific trends in word-order universals

[PDF](../../literature/C/C09_Dunn_2011_Evolved_structure_of_language_shows_lineage_specific_trends_in_word_order_universals.pdf)｜[TXT](../../literature/C/C09_Dunn_2011_Evolved_structure_of_language_shows_lineage_specific_trends_in_word_order_universals.txt)

在四个有可用谱系树的大语系中，用系统发育方法比较语序特征的独立与依赖演化，指出所观察到的特征依赖具有谱系差异。

- 论文在所研究的语序特征中发现许多依赖关系具有谱系特异性。（第79页摘要；第81—82页结果与讨论）。
- 共同继承会影响类型学相关的解释；本文通过语系内演化比较处理共同祖先的影响。（第79页正文；补充材料S1与S1.4）。

## C10 D-PLACE: A Global Database of Cultural, Linguistic and Environmental Diversity

[PDF](../../literature/C/C10_Kirby_2016_D_PLACE_A_Global_Database_of_Cultural_Linguistic_and_Environmental_Diversity.pdf)｜[TXT](../../literature/C/C10_Kirby_2016_D_PLACE_A_Global_Database_of_Cultural_Linguistic_and_Environmental_Diversity.txt)

D-PLACE联结文化变量、语言分类与谱系树、地理位置及环境数据，支持检验文化多样性的历史与空间结构。

- 文化组之间的空间与谱系非独立性分别关联Tobler规律和Galton问题。（PDF第2页，引言）。
- 数据库通过语言分类、谱系树和地理坐标把不同类型数据联系起来。（PDF第3页图1；第8—10页，Language classifications and phylogenies）。

## C11 Cross-Linguistic Data Formats, advancing data sharing and re-use in comparative linguistics

[PDF](../../literature/C/C11_Forkel_2018_Cross_Linguistic_Data_Formats_advancing_data_sharing_and_re_use_in_comparative_linguisti.pdf)｜[TXT](../../literature/C/C11_Forkel_2018_Cross_Linguistic_Data_Formats_advancing_data_sharing_and_re_use_in_comparative_linguisti.txt)

CLDF规定可机器读取的跨语言数据结构，以语言、比较概念、观测值和来源为核心对象，并用CSVW元数据描述表间关系。

- CLDF区分语言、参数/比较概念、值和来源，支持显式描述表格关系。（PDF第3—5页，数据模型与The CLDF Specification；图2）。
- 标准目录标识符能够连接Glottolog语言标识与Concepticon概念标识。（PDF第6页，数据标识与目录连接讨论）。

## C12 Bootstrap-Based Improvements for Inference with Clustered Errors

[PDF](../../literature/C/C12_Cameron_2008_Bootstrap_Based_Improvements_for_Inference_with_Clustered_Errors.pdf)｜[TXT](../../literature/C/C12_Cameron_2008_Bootstrap_Based_Improvements_for_Inference_with_Clustered_Errors.txt)

正式期刊版讨论聚类误差下的bootstrap推断，比较pairs、residual及wild cluster方案，重点考察有限聚类数下的bootstrap-t。

- pairs cluster bootstrap从原样本中整组、有放回抽取聚类。（正式PDF第3页，印刷第416页，§III.A Pairs Cluster Bootstrap-se and Bootstrap-t。）。
- 论文的主要目标包含对小聚类数下bootstrap-t推断的比较。（正式PDF第1页，印刷第414页，Abstract及Introduction。）。
