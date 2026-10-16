# T6：跨领域编码与覆盖可行性

本阶段仅审计覆盖，未计算领域划分的q指标、跨领域关联、回归或置换结果。

|领域|样本层|完整／单词形系统|单词形谱系|至少2个单词形系统的谱系|单词形且全域同一来源系统|
|---|---|---:|---:|---:|---:|
|cousins16|original_selected|427／270|55|18|264|
|cousins16|main939|383／247|48|16|241|
|cousins16|strict625|254／192|43|14|186|
|parent_siblings_age16|original_selected|802／483|91|38|462|
|parent_siblings_age16|main939|730／434|86|35|418|
|parent_siblings_age16|strict625|496／351|80|29|337|
|parent_siblings_generic8|original_selected|315／161|43|21|150|
|parent_siblings_generic8|main939|259／118|37|18|109|
|parent_siblings_generic8|strict625|154／96|35|13|89|

完整仅指每个固定目标编码至少一有效词形；单词形要求每格有效词形集合恰含一项。全域同一来源要求每格至少一个有效Form获得相同Source键支持。该规则不证明来源确曾独立调查全部细格。

三领域不互相补格；无ego前缀代码不复制至m/f，长幼亚类不合并成generic，也不从同一Glottocode的另一Language_ID拼接。年龄16格中的长幼相对父／母，不能称为所指者相对ego的年龄。

cousins16的父母侧p和中介兄妹性别c可组成cross/parallel p⊕c，与ego／referent相对性别q=s⊕r不同。绝对非合取不是q使用的专属指标。

后续精确定义见docs/t6_operationalization.md；关联结果须在单独补充计划冻结后运行。来源、原始Value/Form/Comment/Source和全部空格均保留供核查。
