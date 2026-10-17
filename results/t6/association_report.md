# T6：相对性别指标的跨领域关联（探索性）

按独立提交的补充方案实施。X和Y均为固定rel_r相对abs节省文字的二元指示；绝对非合取、连续差、rescue及rel_s完整描述并报，不替换主指标。

|领域／样本|系统／谱系|Y有变化谱系／系统|条件logit状态|OR及95%t区间|主β Holm2 p|置换有效层／系统|置换p／Holm2 p|
|---|---:|---:|---|---|---:|---:|---:|
|cousins16／all_complete_singleton|192／43|5／135|estimated|1079.66 [0.03117,3.73971e+07]|0.274323|3／17|0.00419916／0.00839832|
|cousins16／same_source_sensitivity|179／42|5／126|estimated|745.007 [0.151062,3.67422e+06]|NA|3／17|0.00419916／NA|
|parent_siblings_age16／all_complete_singleton|351／80|0／0|not_estimable_no_within_family_outcome_variation|NA|NA|0／0|NA／NA|
|parent_siblings_age16／same_source_sensitivity|333／78|0／0|not_estimable_no_within_family_outcome_variation|NA|NA|0／0|NA／NA|
|parent_siblings_generic8／all_complete_singleton|96／35|0／0|not_estimable_no_within_family_outcome_variation|NA|NA|0／0|NA／NA|
|parent_siblings_generic8／same_source_sensitivity|85／33|0／0|not_estimable_no_within_family_outcome_variation|NA|NA|0／0|NA／NA|

主条件模型消去谱系截距，各族条件似然除该族配对系统数，再对有效族平均。双k控制不删除；秩不足、分离或未通过收敛门的模型均不提供推断。合格模型的CR1 sandwich使用加权族score，并用实际贡献族数减1的t分布构造区间。

两个16格领域的主β、一般logit敏感性p和精确分层置换p分别形成三个独立Holm2校正族；generic8和跨域同来源子集不混入主校正族。敏感性行未标Holm2不能视作另一个主检验。

## 一般logit敏感性

|领域／样本|状态|OR及95%t区间|原始p／主两域Holm2 p|
|---|---|---|---:|
|cousins16／all_complete_singleton|estimated|119.74 [11.3262,1265.88]|0.000187912／0.000375823|
|cousins16／same_source_sensitivity|estimated|96.517 [11.5442,806.945]|8.92198e-05／NA|
|parent_siblings_age16／all_complete_singleton|not_estimable_separation|NA|NA／NA|
|parent_siblings_age16／same_source_sensitivity|not_estimable_separation|NA|NA／NA|
|parent_siblings_generic8／all_complete_singleton|not_estimable_separation|NA|NA／NA|
|parent_siblings_generic8／same_source_sensitivity|not_estimable_separation|NA|NA／NA|

一般logit仅将依赖纳入标准误，没有消去共享谱系的混淆；其可估计或较小p不替代主条件模型。

## 数据范围与解释

来源敏感性要求兄弟姐妹八格与目标域全部格点具有同一个共同Source键，而非两个领域分别有不同的完整来源。它仍不能证明原始文献独立调查每个编码格点。

置换层严格固定为谱系与两个k相同，统计为层内中心化X、Y的协方差和。5000次层内洗牌不能扩大有效层数量；无同时变化的X/Y层时记不可识别，不返回p=1。该零假设与条件logit线性控制的β不同。

无法估计或阴性不能证明两领域独立；观察到关联也只涉及固定描述语言的结构节约，不证明说话者实际复用q或存在特定历史传播路径。父母同胞领域的长幼相对父／母，堂表亲p⊕c与ego/referent的q不同。

逐系统指标及所有描述性敏感性保存在cross_domain_indicators.csv；family_model_diagnostics.csv与permutation_strata.csv保留有效及排除单位。完整优化尝试、分离LP、输入哈希和置换统计分布见association_results.json。

## 主指标与有效信息范围

|主样本领域|X=1系统／总数|Y=1系统／总数|置换有效谱系|不同置换统计值数|
|---|---:|---:|---:|---:|
|cousins16|45／192|32／192|2|6|
|parent_siblings_age16|77／351|0／351|0|0|
|parent_siblings_generic8|7／96|0／96|0|0|

置换的小p不能缩窄条件模型在少数信息谱系下的宽区间，也不能证明未出现正指标的其他领域同样有关联。完整有效层的谱系和系统ID均保留，不把5000次洗牌当作5000个独立谱系。
