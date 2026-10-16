# 补充分析S2结果

本分析写于冻结结果、S1和评审核查结果已知之后；最终协议独立提交6ba7afb早于实测。全部模型、口径及失败诊断保留，不把事后补充称为预注册。

# 补充分析S2：划分层面P1–P5

## 运行前指定的结果

最终协议提交`6ba7afba369d3d15446ea7571eabd2117b7e8c74`，SHA-256 `61874a1c28ab37758670a61d12e08b6097af07f7922f63cfd76da5dacfcef8be`。本分析为已知冻结结果与S1后的补充分析，不能解释为预注册。主样本939个记录系统，D3为625个系统、108个谱系组。

### P1：四特征任意合取主定义

共有22个D3系统含非合取词项。系统等权与谱系等权、两个精确随机参照如下；区间均为5000次整谱系重抽样的95%百分位区间。

|参照|权重|观测非合取比例|观测−参照|差值95%区间|率比|
|---|---|---:|---:|---|---:|
|uniform_all_partitions|family_equal|2.8%|-0.9090|[-0.9318, -0.8776]|0.0301|
|uniform_all_partitions|system_equal|3.5%|-0.9020|[-0.9188, -0.8896]|0.0376|
|fixed_block_sizes|family_equal|2.8%|-0.8009|[-0.8330, -0.7638]|0.0340|
|fixed_block_sizes|system_equal|3.5%|-0.7937|[-0.8259, -0.7632]|0.0425|

依协议两参照同时判断，P1主方向得到支持。该结果描述固定词形测量下的记录，不等于所有语言的普遍语义约束。三／四／六特征、任意合取与单叶递归树、区域及去除两个大型谱系的全部结果见JSON和CSV。

### P2–P4：严格结构方向

|预测|预测侧系统|相反侧系统|预测侧多数谱系|相反侧多数谱系|平局谱系|原始单侧p|Bonferroni p|
|---|---:|---:|---:|---:|---:|---:|---:|
|P2|51|6|21|3|0|0.000138581|0.000415742|
|P3|17|5|11|3|1|0.0286865|0.0860596|
|P4|81|1|17|1|0|7.24792e-05|0.000217438|

主判定同时要求目标最小对恰两条且同侧、父根与目标子根不切开词项，以及完整单叶递归见证。未过滤边侧和父特征四边代理完整并报；它们不能替代主结构判定。平局谱系不进入精确二项分母。区域与大型谱系剔除的结果均为预先指定的边界检查。

### P5：四特征合法树的存在性

- `compatible`：600个系统。
- `outside_single_leaf_tree_domain`：22个系统。
- `incompatible_all_trees_require_early_feature`：3个系统。

无树者不再算独立P5违例；兼容树存在只说明表示上可兼容。全部树、兼容树、深度集合及具体见证按结构模板存入partition_systems.json。明确不兼容记录须结合原始字段审查，不能直接宣称发现真实语言的心理或语义普遍律反例。

### 旧84项描述与D3核对

在原939系统上精确重现旧描述84项；其中47项进入625系统D3，37项因每类并非单一词形被排除。D3严格P2预测侧为51项；规则差异对应ID清单已保存。四条额外记录均允许年长一性别内部的参照者三级细分，严格树见证保留此细分，旧精确七单元签名不容纳它；若微小转写差异造成该细分，须在原始字段审查中说明。

### 违例字段与抽查接口

全体列出定义的违例共178个不同系统，保留1444行原始ID、Value、Form、Comment、Source。按Glottocode与Language_ID固定顺序选择20个系统交字段复核；不能把未确定的测量解释填写为已证实的语义事实。

## 运行后观察

本节不追加未指定的假设检验。字段抽查分类由独立数据复核输出提供；此报告不代填尚未完成的人工核查结果。

## 验证与范围

类别名称按KINTYPES明确对齐；每个主系统八类、28对及原始共享指标均复算一致。P5全部树的独立列表与纯理论模块计数一致。所有输入与输出哈希、协议提交、开始结束时间及随机种子保存于结果JSON。原冻结分析和S1未改写。

# S2交叉预测结果

## 运行前指定的结果

20测量×估计×权重条件，各运行3种验证；区间为固定折外预测的5000次谱系整组自助95%百分位区间。

| 条件 | 系统 | M0 | M1 | M2 | M3 | M4 | M2−M4增益及95%区间 |
|---|---:|---:|---:|---:|---:|---:|---|
| D1_MLE_family_family | 939 | 0.5088 | 0.5020 | 0.4961 | 0.4944 | 0.4943 | 0.0018 [-0.0005, 0.0039] |
| D1_MLE_family_area | 909 | 0.5326 | 0.5410 | 0.5400 | 0.5407 | 0.5405 | -0.0005 [-0.0031, 0.0021] |
| D1_MLE_family_language | 939 | 0.5074 | 0.5003 | 0.4958 | 0.4928 | 0.4926 | 0.0031 [0.0007, 0.0054] |
| D1_MLE_language_family | 939 | 0.5855 | 0.5826 | 0.5750 | 0.5747 | 0.5744 | 0.0007 [-0.0015, 0.0044] |
| D1_MLE_language_area | 909 | 0.6182 | 0.6229 | 0.6121 | 0.6153 | 0.6151 | -0.0029 [-0.0068, 0.0026] |
| D1_MLE_language_language | 939 | 0.5440 | 0.5364 | 0.5320 | 0.5287 | 0.5288 | 0.0031 [0.0010, 0.0063] |
| D1_C1_family_family | 939 | 0.5085 | 0.5019 | 0.4999 | 0.4965 | 0.4986 | 0.0013 [-0.0007, 0.0033] |
| D1_C1_family_area | 909 | 0.5269 | 0.5367 | 0.5356 | 0.5253 | 0.5366 | -0.0010 [-0.0038, 0.0018] |
| D1_C1_family_language | 939 | 0.5074 | 0.5003 | 0.4989 | 0.4951 | 0.4965 | 0.0023 [0.0003, 0.0044] |
| D1_C1_language_family | 939 | 0.5810 | 0.5785 | 0.5766 | 0.5660 | 0.5765 | 0.0001 [-0.0032, 0.0051] |
| D1_C1_language_area | 909 | 0.6035 | 0.6102 | 0.6097 | 0.5862 | 0.6118 | -0.0021 [-0.0063, 0.0039] |
| D1_C1_language_language | 939 | 0.5441 | 0.5366 | 0.5351 | 0.5316 | 0.5327 | 0.0023 [-0.0002, 0.0068] |
| D2_MLE_family_family | 939 | 0.4518 | 0.4418 | 0.4367 | 0.4351 | 0.4349 | 0.0018 [-0.0010, 0.0045] |
| D2_MLE_family_area | 909 | 0.4900 | 0.4968 | 0.4938 | 0.4953 | 0.4948 | -0.0010 [-0.0035, 0.0017] |
| D2_MLE_family_language | 939 | 0.4460 | 0.4351 | 0.4318 | 0.4279 | 0.4277 | 0.0041 [0.0015, 0.0067] |
| D2_MLE_language_family | 939 | 0.5158 | 0.5106 | 0.5061 | 0.5057 | 0.5052 | 0.0009 [-0.0008, 0.0040] |
| D2_MLE_language_area | 909 | 0.5505 | 0.5525 | 0.5443 | 0.5477 | 0.5474 | -0.0031 [-0.0069, 0.0023] |
| D2_MLE_language_language | 939 | 0.4776 | 0.4680 | 0.4652 | 0.4618 | 0.4618 | 0.0033 [0.0012, 0.0055] |
| D2_C1_family_family | 939 | 0.4508 | 0.4411 | 0.4425 | 0.4368 | 0.4409 | 0.0016 [-0.0007, 0.0037] |
| D2_C1_family_area | 909 | 0.4778 | 0.4872 | 0.4889 | 0.4712 | 0.4884 | 0.0005 [-0.0021, 0.0032] |
| D2_C1_family_language | 939 | 0.4461 | 0.4355 | 0.4369 | 0.4327 | 0.4339 | 0.0030 [0.0008, 0.0052] |
| D2_C1_language_family | 939 | 0.5105 | 0.5058 | 0.5078 | 0.4977 | 0.5075 | 0.0003 [-0.0024, 0.0046] |
| D2_C1_language_area | 909 | 0.5318 | 0.5367 | 0.5412 | 0.5162 | 0.5429 | -0.0016 [-0.0055, 0.0037] |
| D2_C1_language_language | 939 | 0.4778 | 0.4684 | 0.4693 | 0.4668 | 0.4669 | 0.0024 [0.0004, 0.0059] |
| D3_MLE_family_family | 625 | 0.4595 | 0.4508 | 0.4438 | 0.4437 | 0.4432 | 0.0007 [-0.0023, 0.0034] |
| D3_MLE_family_area | 602 | 0.4920 | 0.5020 | 0.4980 | 0.4995 | 0.4984 | -0.0004 [-0.0030, 0.0024] |
| D3_MLE_family_language | 625 | 0.4524 | 0.4426 | 0.4383 | 0.4351 | 0.4346 | 0.0037 [0.0010, 0.0065] |
| D3_MLE_language_family | 625 | 0.5506 | 0.5433 | 0.5402 | 0.5400 | 0.5396 | 0.0007 [-0.0009, 0.0038] |
| D3_MLE_language_area | 602 | 0.5780 | 0.5785 | 0.5727 | 0.5750 | 0.5745 | -0.0019 [-0.0044, 0.0026] |
| D3_MLE_language_language | 625 | 0.5128 | 0.5010 | 0.4987 | 0.4953 | 0.4953 | 0.0034 [0.0011, 0.0056] |
| D3_C1_family_family | 625 | 0.4584 | 0.4498 | 0.4506 | 0.4474 | 0.4498 | 0.0008 [-0.0017, 0.0031] |
| D3_C1_family_area | 602 | 0.4772 | 0.4910 | 0.4893 | 0.4743 | 0.4889 | 0.0003 [-0.0024, 0.0032] |
| D3_C1_family_language | 625 | 0.4525 | 0.4434 | 0.4442 | 0.4419 | 0.4415 | 0.0027 [0.0005, 0.0050] |
| D3_C1_language_family | 625 | 0.5453 | 0.5385 | 0.5420 | 0.5328 | 0.5421 | -0.0001 [-0.0025, 0.0040] |
| D3_C1_language_area | 602 | 0.5600 | 0.5638 | 0.5687 | 0.5468 | 0.5701 | -0.0014 [-0.0044, 0.0035] |
| D3_C1_language_language | 625 | 0.5130 | 0.5015 | 0.5036 | 0.5022 | 0.5015 | 0.0021 [0.0004, 0.0057] |
| D4_MLE_family_family | 760 | 0.5262 | 0.5185 | 0.5137 | 0.5118 | 0.5117 | 0.0020 [-0.0006, 0.0046] |
| D4_MLE_family_area | 736 | 0.5470 | 0.5555 | 0.5552 | 0.5557 | 0.5555 | -0.0002 [-0.0034, 0.0029] |
| D4_MLE_family_language | 760 | 0.5264 | 0.5188 | 0.5153 | 0.5117 | 0.5115 | 0.0038 [0.0011, 0.0064] |
| D4_MLE_language_family | 760 | 0.6079 | 0.6039 | 0.5987 | 0.5987 | 0.5985 | 0.0002 [-0.0031, 0.0055] |
| D4_MLE_language_area | 736 | 0.6374 | 0.6418 | 0.6347 | 0.6402 | 0.6399 | -0.0052 [-0.0113, 0.0032] |
| D4_MLE_language_language | 760 | 0.5670 | 0.5578 | 0.5545 | 0.5507 | 0.5508 | 0.0037 [0.0011, 0.0082] |
| D4_C1_family_family | 760 | 0.5260 | 0.5185 | 0.5177 | 0.5145 | 0.5160 | 0.0017 [-0.0007, 0.0041] |
| D4_C1_family_area | 736 | 0.5418 | 0.5515 | 0.5507 | 0.5410 | 0.5513 | -0.0005 [-0.0038, 0.0028] |
| D4_C1_family_language | 760 | 0.5265 | 0.5189 | 0.5186 | 0.5147 | 0.5156 | 0.0029 [0.0005, 0.0055] |
| D4_C1_language_family | 760 | 0.6037 | 0.6000 | 0.6002 | 0.5897 | 0.6003 | -0.0001 [-0.0046, 0.0066] |
| D4_C1_language_area | 736 | 0.6235 | 0.6299 | 0.6315 | 0.6089 | 0.6351 | -0.0035 [-0.0096, 0.0048] |
| D4_C1_language_language | 760 | 0.5671 | 0.5581 | 0.5578 | 0.5542 | 0.5549 | 0.0030 [-0.0005, 0.0090] |
| D5_MLE_family_family | 939 | 0.5635 | 0.5568 | 0.5531 | 0.5506 | 0.5505 | 0.0027 [-0.0002, 0.0053] |
| D5_MLE_family_area | 909 | 0.5775 | 0.5859 | 0.5893 | 0.5894 | 0.5893 | 0.0001 [-0.0031, 0.0032] |
| D5_MLE_family_language | 939 | 0.5619 | 0.5548 | 0.5520 | 0.5479 | 0.5478 | 0.0042 [0.0013, 0.0071] |
| D5_MLE_language_family | 939 | 0.6187 | 0.6160 | 0.6142 | 0.6134 | 0.6132 | 0.0009 [-0.0018, 0.0055] |
| D5_MLE_language_area | 909 | 0.6388 | 0.6436 | 0.6441 | 0.6467 | 0.6464 | -0.0023 [-0.0067, 0.0040] |
| D5_MLE_language_language | 939 | 0.5911 | 0.5834 | 0.5814 | 0.5778 | 0.5779 | 0.0035 [0.0013, 0.0074] |
| D5_C1_family_family | 939 | 0.5633 | 0.5567 | 0.5555 | 0.5517 | 0.5531 | 0.0024 [-0.0002, 0.0050] |
| D5_C1_family_area | 909 | 0.5752 | 0.5840 | 0.5849 | 0.5772 | 0.5852 | -0.0003 [-0.0036, 0.0030] |
| D5_C1_family_language | 939 | 0.5619 | 0.5549 | 0.5544 | 0.5498 | 0.5508 | 0.0036 [0.0009, 0.0063] |
| D5_C1_language_family | 939 | 0.6165 | 0.6140 | 0.6145 | 0.6070 | 0.6142 | 0.0003 [-0.0037, 0.0063] |
| D5_C1_language_area | 909 | 0.6319 | 0.6376 | 0.6397 | 0.6241 | 0.6422 | -0.0025 [-0.0079, 0.0049] |
| D5_C1_language_language | 939 | 0.5912 | 0.5836 | 0.5835 | 0.5801 | 0.5805 | 0.0029 [-0.0001, 0.0079] |

完整七项比较（60设定×7=420行）见[s2_crossed_comparisons.csv](s2_crossed_comparisons.csv)，逐单元校准见[s2_cell_calibration.csv](s2_cell_calibration.csv)。

## 运行后观察

全部比较、逐系统分数、分区域结果和拟合诊断保留JSON/CSV，不因方向而删去条件。

# S2违例原字段抽查

按最终协议检查Glottocode顺序前20个不同系统；可供抽查的违例系统共178个。保留全部168条八类相关原始记录，见`violation_audit.json`。

四类候选解释允许并存。以下只记录程序形式违例、空格／注释线索、展开线索、来源／转写字段；仅凭这些字段不能确认真实语义违例。所有系统的语义总评均为“无法判断”，不是已确认的普遍律反例。

汇总只描述这组按固定字典顺序取得的字段抽查，不能外推为全部违例的原因比例；全部八类原始形式集合都与分析输入逐项一致。

| 序号 | Glottocode／系统 | 语系 | 空格行 | 重复词元行 | 无来源行 | 来源数 | Value/Form不同的行 | 总评 |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 1 | akla1241／p_aklanonakla1241 | Austronesian | 0 | 0 | 0 | 1 | 0 | 无法判断真实语义解释 |
| 2 | anut1237／p_anutaanut1237 | Austronesian | 0 | 0 | 0 | 1 | 0 | 无法判断真实语义解释 |
| 3 | area1240／p_arearearea1240 | Austronesian | 0 | 0 | 0 | 1 | 0 | 无法判断真实语义解释 |
| 4 | auuu1241／p_auauuu1241 | Nuclear Torricelli | 2 | 0 | 0 | 1 | 0 | 无法判断真实语义解释 |
| 5 | awap1236／v_awaawap1236 | Nuclear Trans New Guinea | 0 | 0 | 0 | 1 | 0 | 无法判断真实语义解释 |
| 6 | baca1243／p_bacanesemalaybacanbaca1243 | Austronesian | 6 | 0 | 0 | 1 | 0 | 无法判断真实语义解释 |
| 7 | baff1241／p_morgan1871baffininuktituteskimonorthumberlandinletbaff1241 | Eskimo-Aleut | 0 | 0 | 0 | 1 | 0 | 无法判断真实语义解释 |
| 8 | baro1253／p_barokkarubaro1253 | Austronesian | 0 | 0 | 0 | 1 | 0 | 无法判断真实语义解释 |
| 9 | bign1238／p_bignambasbign1238 | Austronesian | 2 | 0 | 0 | 1 | 0 | 无法判断真实语义解释 |
| 10 | blag1240／p_blagarblag1240 | Timor-Alor-Pantar | 0 | 0 | 0 | 1 | 0 | 无法判断真实语义解释 |
| 11 | boun1245／p_boungboun1245 | Nuclear Trans New Guinea | 0 | 0 | 0 | 1 | 0 | 无法判断真实语义解释 |
| 12 | buli1256／p_bulibuli1256 | Austronesian | 4 | 0 | 0 | 1 | 0 | 无法判断真实语义解释 |
| 13 | buru1303／p_buruindonesiaburu1303 | Austronesian | 0 | 0 | 0 | 1 | 0 | 无法判断真实语义解释 |
| 14 | chek1238／p_chekeholochek1238 | Austronesian | 0 | 0 | 0 | 1 | 0 | 无法判断真实语义解释 |
| 15 | cher1273／p_morgan1871cherokeecher1273 | Iroquoian | 0 | 0 | 0 | 1 | 0 | 无法判断真实语义解释 |
| 16 | chic1270／p_morgan1871chickasachic1270 | Muskogean | 0 | 0 | 0 | 1 | 0 | 无法判断真实语义解释 |
| 17 | choc1276／p_morgan1871choctaw1choc1276 | Muskogean | 0 | 0 | 0 | 1 | 0 | 无法判断真实语义解释 |
| 18 | chok1245／v_chokwechok1245 | Atlantic-Congo | 0 | 0 | 0 | 1 | 0 | 无法判断真实语义解释 |
| 19 | cogu1240／p_kogicogu1240 | Chibchan | 0 | 0 | 0 | 1 | 0 | 无法判断真实语义解释 |
| 20 | copp1244／v_copp1244 | Eskimo-Aleut | 0 | 0 | 0 | 1 | 0 | 无法判断真实语义解释 |

## 各系统的全部原始字段

固定前20中，四特征主定义或P2–P5有关违例为2个，其余18个仅属三特征参照。不能将后者改称主定义反例。

结果生成后补查全部22个四特征A不合取系统及3个P5明确不兼容系统，去重为25个，保存202条目标行；它们不替换预先固定的前20，另列为“运行后补充质量核查”。两组审查合计覆盖43个不同系统。

### 1. akla1241：p_aklanonakla1241

谱系：Austronesian；区域：Papunesia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_four, P1_A_six, P1_A_three, P1_B_four, P1_B_six, P1_B_three。

逐字段复核说明：逐行记录中manghod与igmánghod并存；注释空且同一来源。字符差别不构成误拼证据，不自行合并。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_aklanonakla1241-meB-1 | meB | manong | manong | 〔空〕 | SalasReyes1968 |
| p_aklanonakla1241-myB-1 | myB | manghod | manghod | 〔空〕 | SalasReyes1968 |
| p_aklanonakla1241-feB-1 | feB | manong | manong | 〔空〕 | SalasReyes1968 |
| p_aklanonakla1241-fyB-1 | fyB | igmánghod | igmánghod | 〔空〕 | SalasReyes1968 |
| p_aklanonakla1241-meZ-1 | meZ | igmánghod | igmánghod | 〔空〕 | SalasReyes1968 |
| p_aklanonakla1241-myZ-1 | myZ | manghod | manghod | 〔空〕 | SalasReyes1968 |
| p_aklanonakla1241-feZ-1 | feZ | igmánghod | igmánghod | 〔空〕 | SalasReyes1968 |
| p_aklanonakla1241-fyZ-1 | fyZ | manghod | manghod | 〔空〕 | SalasReyes1968 |

### 2. anut1237：p_anutaanut1237

谱系：Austronesian；区域：Papunesia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_three, P1_B_three。

逐字段复核说明：原表按两种形式分布，八类均同一来源且无解释性注释；这里只违反三特征参照，不能称四特征主定义违例。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_anutaanut1237-meB-1 | meB | taina | taina | 〔空〕 | Marck1996 |
| p_anutaanut1237-myB-1 | myB | taina | taina | 〔空〕 | Marck1996 |
| p_anutaanut1237-feB-1 | feB | kave | kave | 〔空〕 | Marck1996 |
| p_anutaanut1237-fyB-1 | fyB | kave | kave | 〔空〕 | Marck1996 |
| p_anutaanut1237-meZ-1 | meZ | kave | kave | 〔空〕 | Marck1996 |
| p_anutaanut1237-myZ-1 | myZ | kave | kave | 〔空〕 | Marck1996 |
| p_anutaanut1237-feZ-1 | feZ | taina | taina | 〔空〕 | Marck1996 |
| p_anutaanut1237-fyZ-1 | fyZ | taina | taina | 〔空〕 | Marck1996 |

### 3. area1240：p_arearearea1240

谱系：Austronesian；区域：Papunesia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_three, P1_B_three。

逐字段复核说明：a加组合长音的规范编码会经NFC合成，原始Value与Form相同；这不证明其他不同拼写应合并。违例仅属三特征参照。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_arearearea1240-meB-1 | meB | 'āsi-na | 'āsi-na | 〔空〕 | Geerts1970 |
| p_arearearea1240-myB-1 | myB | 'āsi-na | 'āsi-na | 〔空〕 | Geerts1970 |
| p_arearearea1240-feB-1 | feB | hahone-na | hahone-na | 〔空〕 | Geerts1970 |
| p_arearearea1240-fyB-1 | fyB | hahone-na | hahone-na | 〔空〕 | Geerts1970 |
| p_arearearea1240-meZ-1 | meZ | hahone-na | hahone-na | 〔空〕 | Geerts1970 |
| p_arearearea1240-myZ-1 | myZ | hahone-na | hahone-na | 〔空〕 | Geerts1970 |
| p_arearearea1240-feZ-1 | feZ | 'āsi-na | 'āsi-na | 〔空〕 | Geerts1970 |
| p_arearearea1240-fyZ-1 | fyZ | 'āsi-na | 'āsi-na | 〔空〕 | Geerts1970 |

### 4. auuu1241：p_auauuu1241

谱系：Nuclear Torricelli；区域：Papunesia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_three, P1_B_three。

逐字段复核说明：hei iue含空格，其他形式没有同一空格结构；没有注释说明词界或语义组成，故不标为已确认描述短语。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_auauuu1241-meB-1 | meB | hei iue | hei iue | 〔空〕 | shaw1974kinship |
| p_auauuu1241-myB-1 | myB | nikiik | nikiik | 〔空〕 | shaw1974kinship |
| p_auauuu1241-feB-1 | feB | yantan | yantan | 〔空〕 | shaw1974kinship |
| p_auauuu1241-fyB-1 | fyB | yantan | yantan | 〔空〕 | shaw1974kinship |
| p_auauuu1241-meZ-1 | meZ | yantan | yantan | 〔空〕 | shaw1974kinship |
| p_auauuu1241-myZ-1 | myZ | yantan | yantan | 〔空〕 | shaw1974kinship |
| p_auauuu1241-feZ-1 | feZ | hei iue | hei iue | 〔空〕 | shaw1974kinship |
| p_auauuu1241-fyZ-1 | fyZ | nikiik | nikiik | 〔空〕 | shaw1974kinship |

### 5. awap1236：v_awaawap1236

谱系：Nuclear Trans New Guinea；区域：Papunesia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_four, P1_A_six, P1_A_three, P1_B_four, P1_B_six, P1_B_three。

逐字段复核说明：八类单词形在不同参照者／年龄位置分布不一；来源一致、注释空，无法仅凭形式排除来源或编码问题。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| v_awaawap1236-meB-1 | meB | awahwa | awahwa | 〔空〕 | Loving_1974 |
| v_awaawap1236-myB-1 | myB | abaqkawa | abaqkawa | 〔空〕 | Loving_1974 |
| v_awaawap1236-meZ-1 | meZ | anahnowa | anahnowa | 〔空〕 | Loving_1974 |
| v_awaawap1236-myZ-1 | myZ | anahnowa | anahnowa | 〔空〕 | Loving_1974 |
| v_awaawap1236-feB-1 | feB | ayoqkawa | ayoqkawa | 〔空〕 | Loving_1974 |
| v_awaawap1236-fyB-1 | fyB | ayoqkawa | ayoqkawa | 〔空〕 | Loving_1974 |
| v_awaawap1236-feZ-1 | feZ | anahnowa | anahnowa | 〔空〕 | Loving_1974 |
| v_awaawap1236-fyZ-1 | fyZ | onanahwa | onanahwa | 〔空〕 | Loving_1974 |

### 6. baca1243：p_bacanesemalaybacanbaca1243

谱系：Austronesian；区域：Papunesia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_three, P1_B_three。

逐字段复核说明：dantjanak jang toeana、dantjanak laki、dantjanak bini均含空格；没有注释证明其词素或修饰关系，保留机械空格线索。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_bacanesemalaybacanbaca1243-meB-1 | meB | dantjanak jang toeana | dantjanak jang toeana | 〔空〕 | Holle1980v2 |
| p_bacanesemalaybacanbaca1243-myB-1 | myB | adi | adi | 〔空〕 | Holle1980v2 |
| p_bacanesemalaybacanbaca1243-feB-1 | feB | dantjanak laki | dantjanak laki | 〔空〕 | Holle1980v2 |
| p_bacanesemalaybacanbaca1243-fyB-1 | fyB | dantjanak laki | dantjanak laki | 〔空〕 | Holle1980v2 |
| p_bacanesemalaybacanbaca1243-meZ-1 | meZ | dantjanak bini | dantjanak bini | 〔空〕 | Holle1980v2 |
| p_bacanesemalaybacanbaca1243-myZ-1 | myZ | dantjanak bini | dantjanak bini | 〔空〕 | Holle1980v2 |
| p_bacanesemalaybacanbaca1243-feZ-1 | feZ | dantjanak jang toeana | dantjanak jang toeana | 〔空〕 | Holle1980v2 |
| p_bacanesemalaybacanbaca1243-fyZ-1 | fyZ | adi | adi | 〔空〕 | Holle1980v2 |

### 7. baff1241：p_morgan1871baffininuktituteskimonorthumberlandinletbaff1241

谱系：Eskimo-Aleut；区域：North America。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_three, P1_B_three。

逐字段复核说明：naʼ-yǎ与na-yǎʼ的符号位置不同；只记录原始字符串差异，不推断是异写、拼写错误或真实年龄区别。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_morgan1871baffininuktituteskimonorthumberlandinletbaff1241-myB-1 | myB | nuʼ-kä | nuʼ-kä | 〔空〕 | Morgan1871 |
| p_morgan1871baffininuktituteskimonorthumberlandinletbaff1241-fyB-1 | fyB | nuʼ-kä | nuʼ-kä | 〔空〕 | Morgan1871 |
| p_morgan1871baffininuktituteskimonorthumberlandinletbaff1241-fyZ-1 | fyZ | nu-käʼ-hä | nu-käʼ-hä | 〔空〕 | Morgan1871 |
| p_morgan1871baffininuktituteskimonorthumberlandinletbaff1241-myZ-1 | myZ | naʼ-yǎ | naʼ-yǎ | 〔空〕 | Morgan1871 |
| p_morgan1871baffininuktituteskimonorthumberlandinletbaff1241-meZ-1 | meZ | na-yǎʼ | na-yǎʼ | 〔空〕 | Morgan1871 |
| p_morgan1871baffininuktituteskimonorthumberlandinletbaff1241-feB-1 | feB | au-ningʼ-ä | au-ningʼ-ä | 〔空〕 | Morgan1871 |
| p_morgan1871baffininuktituteskimonorthumberlandinletbaff1241-meB-1 | meB | ang-a-yuʼ-ä | ang-a-yuʼ-ä | 〔空〕 | Morgan1871 |
| p_morgan1871baffininuktituteskimonorthumberlandinletbaff1241-feZ-1 | feZ | ang-a-yuʼ-ä | ang-a-yuʼ-ä | 〔空〕 | Morgan1871 |

### 8. baro1253：p_barokkarubaro1253

谱系：Austronesian；区域：Papunesia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_three, P1_B_three。

逐字段复核说明：rok与sagok的八格记录同源、注释空；程序违例属于三特征参照，缺少原来源语境不能确认语义反例。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_barokkarubaro1253-meB-1 | meB | rok | rok | 〔空〕 | Chinnery1930 |
| p_barokkarubaro1253-myB-1 | myB | rok | rok | 〔空〕 | Chinnery1930 |
| p_barokkarubaro1253-feB-1 | feB | sagok | sagok | 〔空〕 | Chinnery1930 |
| p_barokkarubaro1253-fyB-1 | fyB | sagok | sagok | 〔空〕 | Chinnery1930 |
| p_barokkarubaro1253-meZ-1 | meZ | sagok | sagok | 〔空〕 | Chinnery1930 |
| p_barokkarubaro1253-myZ-1 | myZ | sagok | sagok | 〔空〕 | Chinnery1930 |
| p_barokkarubaro1253-feZ-1 | feZ | rok | rok | 〔空〕 | Chinnery1930 |
| p_barokkarubaro1253-fyZ-1 | fyZ | rok | rok | 〔空〕 | Chinnery1930 |

### 9. bign1238：p_bignambasbign1238

谱系：Austronesian；区域：Papunesia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_three, P1_B_three。

逐字段复核说明：tivalök nöngk含空格而tivalök不含；未有注释解释两者关系，不把形式包含关系自动标为形态或描述构式。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_bignambasbign1238-meB-1 | meB | tivalök | tivalök | 〔空〕 | Deacon1934 |
| p_bignambasbign1238-myB-1 | myB | tivalök nöngk | tivalök nöngk | 〔空〕 | Deacon1934 |
| p_bignambasbign1238-feB-1 | feB | manök | manök | 〔空〕 | Deacon1934 |
| p_bignambasbign1238-fyB-1 | fyB | manök | manök | 〔空〕 | Deacon1934 |
| p_bignambasbign1238-meZ-1 | meZ | evünök | evünök | 〔空〕 | Deacon1934 |
| p_bignambasbign1238-myZ-1 | myZ | evünök | evünök | 〔空〕 | Deacon1934 |
| p_bignambasbign1238-feZ-1 | feZ | tivalök | tivalök | 〔空〕 | Deacon1934 |
| p_bignambasbign1238-fyZ-1 | fyZ | tivalök nöngk | tivalök nöngk | 〔空〕 | Deacon1934 |

### 10. blag1240：p_blagarblag1240

谱系：Timor-Alor-Pantar；区域：Papunesia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_three, P1_B_three。

逐字段复核说明：-kaku与-edi的前导连字符保留；它们不等于单独的缺失标记“-”，不据连字符自动删除或切词。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_blagarblag1240-meB-1 | meB | -kaku | -kaku | 〔空〕 | Holton2017 |
| p_blagarblag1240-myB-1 | myB | -kaku | -kaku | 〔空〕 | Holton2017 |
| p_blagarblag1240-feB-1 | feB | -edi | -edi | 〔空〕 | Holton2017 |
| p_blagarblag1240-fyB-1 | fyB | -edi | -edi | 〔空〕 | Holton2017 |
| p_blagarblag1240-meZ-1 | meZ | -edi | -edi | 〔空〕 | Holton2017 |
| p_blagarblag1240-myZ-1 | myZ | -edi | -edi | 〔空〕 | Holton2017 |
| p_blagarblag1240-feZ-1 | feZ | -kaku | -kaku | 〔空〕 | Holton2017 |
| p_blagarblag1240-fyZ-1 | fyZ | -kaku | -kaku | 〔空〕 | Holton2017 |

### 11. boun1245：p_boungboun1245

谱系：Nuclear Trans New Guinea；区域：Papunesia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_three, P1_B_three。

逐字段复核说明：Comment直接写same-sex sibling与opposite-sex sibling，与相对性别记录有关；不能将缺少q的三特征参照违例误作主定义违例。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_boungboun1245-meB-1 | meB | angin | angin | same-sex sibling | rumsey-2016 |
| p_boungboun1245-myB-1 | myB | angin | angin | same-sex sibling | rumsey-2016 |
| p_boungboun1245-feB-1 | feB | kimul | kimul | opposite-sex sibling | rumsey-2016 |
| p_boungboun1245-fyB-1 | fyB | kimul | kimul | opposite-sex sibling | rumsey-2016 |
| p_boungboun1245-meZ-1 | meZ | kimul | kimul | opposite-sex sibling | rumsey-2016 |
| p_boungboun1245-myZ-1 | myZ | kimul | kimul | opposite-sex sibling | rumsey-2016 |
| p_boungboun1245-feZ-1 | feZ | angin | angin | same-sex sibling | rumsey-2016 |
| p_boungboun1245-fyZ-1 | fyZ | angin | angin | same-sex sibling | rumsey-2016 |

### 12. buli1256：p_bulibuli1256

谱系：Austronesian；区域：Papunesia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_three, P1_B_three。

逐字段复核说明：teno taoeati与teno tawawai含空格；同一来源且无解释性注释，无法确认空格所对应的语言结构。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_bulibuli1256-meB-1 | meB | teno taoeati | teno taoeati | 〔空〕 | Holle1980v2 |
| p_bulibuli1256-myB-1 | myB | teno tawawai | teno tawawai | 〔空〕 | Holle1980v2 |
| p_bulibuli1256-feB-1 | feB | rama | rama | 〔空〕 | Holle1980v2 |
| p_bulibuli1256-fyB-1 | fyB | rama | rama | 〔空〕 | Holle1980v2 |
| p_bulibuli1256-meZ-1 | meZ | rama | rama | 〔空〕 | Holle1980v2 |
| p_bulibuli1256-myZ-1 | myZ | rama | rama | 〔空〕 | Holle1980v2 |
| p_bulibuli1256-feZ-1 | feZ | teno taoeati | teno taoeati | 〔空〕 | Holle1980v2 |
| p_bulibuli1256-fyZ-1 | fyZ | teno tawawai | teno tawawai | 〔空〕 | Holle1980v2 |

### 13. buru1303：p_buruindonesiaburu1303

谱系：Austronesian；区域：Papunesia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_three, P1_B_three。

逐字段复核说明：kaka、wai、feta、naha按八类分布，来源统一而注释空；仅据该表不能解释差异来源。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_buruindonesiaburu1303-meB-1 | meB | kaka | kaka | 〔空〕 | Grimes1991 |
| p_buruindonesiaburu1303-myB-1 | myB | wai | wai | 〔空〕 | Grimes1991 |
| p_buruindonesiaburu1303-feB-1 | feB | feta | feta | 〔空〕 | Grimes1991 |
| p_buruindonesiaburu1303-fyB-1 | fyB | feta | feta | 〔空〕 | Grimes1991 |
| p_buruindonesiaburu1303-meZ-1 | meZ | naha | naha | 〔空〕 | Grimes1991 |
| p_buruindonesiaburu1303-myZ-1 | myZ | naha | naha | 〔空〕 | Grimes1991 |
| p_buruindonesiaburu1303-feZ-1 | feZ | kaka | kaka | 〔空〕 | Grimes1991 |
| p_buruindonesiaburu1303-fyZ-1 | fyZ | wai | wai | 〔空〕 | Grimes1991 |

### 14. chek1238：p_chekeholochek1238

谱系：Austronesian；区域：Papunesia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_three, P1_B_three。

逐字段复核说明：g加组合长音等字符按NFC处理；保留原始Value/Form和规范化后Form，未进行音系匹配或纠音。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_chekeholochek1238-meB-1 | meB | tigagna | tigagna | 〔空〕 | White1988 |
| p_chekeholochek1238-myB-1 | myB | tahigna | tahigna | 〔空〕 | White1988 |
| p_chekeholochek1238-feB-1 | feB | ḡregagna | ḡregagna | 〔空〕 | White1988 |
| p_chekeholochek1238-fyB-1 | fyB | ḡregagna | ḡregagna | 〔空〕 | White1988 |
| p_chekeholochek1238-meZ-1 | meZ | ḡregagna | ḡregagna | 〔空〕 | White1988 |
| p_chekeholochek1238-myZ-1 | myZ | ḡregagna | ḡregagna | 〔空〕 | White1988 |
| p_chekeholochek1238-feZ-1 | feZ | tigagna | tigagna | 〔空〕 | White1988 |
| p_chekeholochek1238-fyZ-1 | fyZ | tahigna | tahigna | 〔空〕 | White1988 |

### 15. cher1273：p_morgan1871cherokeecher1273

谱系：Iroquoian；区域：North America。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_three, P1_B_three。

逐字段复核说明：带组合变音和连字符的形式按原记录保留；NFC只改变规范编码，不把不同形式认作同词。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_morgan1871cherokeecher1273-myB-1 | myB | un̤-gǐ-nun̤ʼ-tlǐ | un̤-gǐ-nun̤ʼ-tlǐ | 〔空〕 | Morgan1871 |
| p_morgan1871cherokeecher1273-meB-1 | meB | un̤-gǐ-nǐ-lǐ | un̤-gǐ-nǐ-lǐ | 〔空〕 | Morgan1871 |
| p_morgan1871cherokeecher1273-feZ-1 | feZ | un̤-gǐ-lun̤ʼ-ǐ | un̤-gǐ-lun̤ʼ-ǐ | 〔空〕 | Morgan1871 |
| p_morgan1871cherokeecher1273-fyZ-1 | fyZ | un̤-gǐ-lun̤ʼ-ǐ | un̤-gǐ-lun̤ʼ-ǐ | 〔空〕 | Morgan1871 |
| p_morgan1871cherokeecher1273-feB-1 | feB | un̤-gǐ-dauʼ | un̤-gǐ-dauʼ | 〔空〕 | Morgan1871 |
| p_morgan1871cherokeecher1273-meZ-1 | meZ | un̤-gǐ-dauʼ | un̤-gǐ-dauʼ | 〔空〕 | Morgan1871 |
| p_morgan1871cherokeecher1273-fyB-1 | fyB | un̤-gǐ-dauʼ | un̤-gǐ-dauʼ | 〔空〕 | Morgan1871 |
| p_morgan1871cherokeecher1273-myZ-1 | myZ | un̤-gǐ-dauʼ | un̤-gǐ-dauʼ | 〔空〕 | Morgan1871 |

### 16. chic1270：p_morgan1871chickasachic1270

谱系：Muskogean；区域：North America。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_three, P1_B_three。

逐字段复核说明：较长形式中的字母与变音符号位置不同；没有注释允许纠错，故不凭外观接近修正原表。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_morgan1871chickasachic1270-myB-1 | myB | sä-näkʼ-fish | sä-näkʼ-fish | 〔空〕 | Morgan1871 |
| p_morgan1871chickasachic1270-fyZ-1 | fyZ | sä-näkʼ-fish | sä-näkʼ-fish | 〔空〕 | Morgan1871 |
| p_morgan1871chickasachic1270-meB-1 | meB | au-tikʼ-bä | au-tikʼ-bä | 〔空〕 | Morgan1871 |
| p_morgan1871chickasachic1270-feZ-1 | feZ | anʼ-tikʼ-bä | anʼ-tikʼ-bä | 〔空〕 | Morgan1871 |
| p_morgan1871chickasachic1270-meZ-1 | meZ | anʼ-take | anʼ-take | 〔空〕 | Morgan1871 |
| p_morgan1871chickasachic1270-myZ-1 | myZ | anʼ-take | anʼ-take | 〔空〕 | Morgan1871 |
| p_morgan1871chickasachic1270-feB-1 | feB | a-näkʼ-fǐ | a-näkʼ-fǐ | 〔空〕 | Morgan1871 |
| p_morgan1871chickasachic1270-fyB-1 | fyB | a-näkʼ-fǐ | a-näkʼ-fǐ | 〔空〕 | Morgan1871 |

### 17. choc1276：p_morgan1871choctaw1choc1276

谱系：Muskogean；区域：North America。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_three, P1_B_three。

逐字段复核说明：feB的a-näkʼ-fǐ与fyB的a-nakʼ-fǐ保留原差异；是否转写差异尚无字段证据，不能把去变音当作清洗。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_morgan1871choctaw1choc1276-meB-1 | meB | um-unʼ-nǐ | um-unʼ-nǐ | 〔空〕 | Morgan1871 |
| p_morgan1871choctaw1choc1276-feZ-1 | feZ | um-unʼ-nǐ | um-unʼ-nǐ | 〔空〕 | Morgan1871 |
| p_morgan1871choctaw1choc1276-myB-1 | myB | suh-näkʼ-fish | suh-näkʼ-fish | 〔空〕 | Morgan1871 |
| p_morgan1871choctaw1choc1276-fyZ-1 | fyZ | suh-näkʼ-fish | suh-näkʼ-fish | 〔空〕 | Morgan1871 |
| p_morgan1871choctaw1choc1276-meZ-1 | meZ | anʼ-take | anʼ-take | 〔空〕 | Morgan1871 |
| p_morgan1871choctaw1choc1276-myZ-1 | myZ | anʼ-take | anʼ-take | 〔空〕 | Morgan1871 |
| p_morgan1871choctaw1choc1276-feB-1 | feB | a-näkʼ-fǐ | a-näkʼ-fǐ | 〔空〕 | Morgan1871 |
| p_morgan1871choctaw1choc1276-fyB-1 | fyB | a-nakʼ-fǐ | a-nakʼ-fǐ | 〔空〕 | Morgan1871 |

### 18. chok1245：v_chokwechok1245

谱系：Atlantic-Congo；区域：Africa。候选粗类展开解释：有显式展开／推断／自动填入注释字面线索，待核对所指；真实语义解释：无法判断。

所涉程序命题：P1_A_three, P1_B_three。

逐字段复核说明：八类各有重复原始行，均标Inferred; NA，同源粗类背景也存在；这是明确的推断注释线索，但无法确定每格展开的具体依据。集合去重未增加词项。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| v_chokwechok1245-meB-1 | meB | pangi | pangi | Inferred; NA | mcculloch_southern_1951 |
| v_chokwechok1245-meB-2 | meB | pangi | pangi | Inferred; NA | mcculloch_southern_1951 |
| v_chokwechok1245-myB-1 | myB | pangi | pangi | Inferred; NA | mcculloch_southern_1951 |
| v_chokwechok1245-myB-2 | myB | pangi | pangi | Inferred; NA | mcculloch_southern_1951 |
| v_chokwechok1245-meZ-1 | meZ | ndumbu | ndumbu | Inferred; NA | mcculloch_southern_1951 |
| v_chokwechok1245-meZ-2 | meZ | ndumbu | ndumbu | Inferred; NA | mcculloch_southern_1951 |
| v_chokwechok1245-myZ-1 | myZ | ndumbu | ndumbu | Inferred; NA | mcculloch_southern_1951 |
| v_chokwechok1245-myZ-2 | myZ | ndumbu | ndumbu | Inferred; NA | mcculloch_southern_1951 |
| v_chokwechok1245-feB-1 | feB | ndumbu | ndumbu | Inferred; NA | mcculloch_southern_1951 |
| v_chokwechok1245-feB-2 | feB | ndumbu | ndumbu | Inferred; NA | mcculloch_southern_1951 |
| v_chokwechok1245-fyB-1 | fyB | ndumbu | ndumbu | Inferred; NA | mcculloch_southern_1951 |
| v_chokwechok1245-fyB-2 | fyB | ndumbu | ndumbu | Inferred; NA | mcculloch_southern_1951 |
| v_chokwechok1245-feZ-1 | feZ | pangi | pangi | Inferred; NA | mcculloch_southern_1951 |
| v_chokwechok1245-feZ-2 | feZ | pangi | pangi | Inferred; NA | mcculloch_southern_1951 |
| v_chokwechok1245-fyZ-1 | fyZ | pangi | pangi | Inferred; NA | mcculloch_southern_1951 |
| v_chokwechok1245-fyZ-2 | fyZ | pangi | pangi | Inferred; NA | mcculloch_southern_1951 |

相关粗类别／未区分所指者性别的背景行（不加入八类分析）：

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| v_chokwechok1245-mB-1 | mB | pangi | pangi | 〔空〕 | mcculloch_southern_1951 |
| v_chokwechok1245-mB-2 | mB | pangi | pangi | 〔空〕 | mcculloch_southern_1951 |
| v_chokwechok1245-mZ-1 | mZ | ndumbu | ndumbu | 〔空〕 | mcculloch_southern_1951 |
| v_chokwechok1245-mZ-2 | mZ | ndumbu | ndumbu | 〔空〕 | mcculloch_southern_1951 |
| v_chokwechok1245-fB-1 | fB | ndumbu | ndumbu | 〔空〕 | mcculloch_southern_1951 |
| v_chokwechok1245-fB-2 | fB | ndumbu | ndumbu | 〔空〕 | mcculloch_southern_1951 |
| v_chokwechok1245-fZ-1 | fZ | pangi | pangi | 〔空〕 | mcculloch_southern_1951 |
| v_chokwechok1245-fZ-2 | fZ | pangi | pangi | 〔空〕 | mcculloch_southern_1951 |

### 19. cogu1240：p_kogicogu1240

谱系：Chibchan；区域：South America。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_three, P1_B_three。

逐字段复核说明：部分注释说明unpossessed形式及same/opposite-sex；这些是来源已有说明，不把未给出的语境自动补入实际词形。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_kogicogu1240-meB-1 | meB | naˈtwe | naˈtwe | unpossessed dwe ‘mister’ as a generic noun or form of address | BergqvistPC |
| p_kogicogu1240-myB-1 | myB | naˈɮaɲi | naˈɮaɲi | younger sibling of same sex | BergqvistPC |
| p_kogicogu1240-feB-1 | feB | naˈtwe | naˈtwe | 〔空〕 | BergqvistPC |
| p_kogicogu1240-fyB-1 | fyB | naˈhasɨ | naˈhasɨ | younger sibling of opposite sex | BergqvistPC |
| p_kogicogu1240-meZ-1 | meZ | naˈɮu | naˈɮu | unpossessed nu ‘lady, Mrs.’ as a generic noun or form of address | BergqvistPC |
| p_kogicogu1240-myZ-1 | myZ | naˈhasɨ | naˈhasɨ | younger sibling of opposite sex | BergqvistPC |
| p_kogicogu1240-feZ-1 | feZ | naˈɮu | naˈɮu | 〔空〕 | BergqvistPC |
| p_kogicogu1240-fyZ-1 | fyZ | naˈɮaɲi | naˈɮaɲi | younger sibling of same sex | BergqvistPC |

### 20. copp1244：v_copp1244

谱系：Eskimo-Aleut；区域：North America。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_three, P1_B_three。

逐字段复核说明：八类来源为Damas_1975且注释空；保持全部字符串，无法依据未见异常认定原语义已获验证。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| v_copp1244-meB-1 | meB | angayuk | angayuk | 〔空〕 | Damas_1975 |
| v_copp1244-myB-1 | myB | nukaq | nukaq | 〔空〕 | Damas_1975 |
| v_copp1244-meZ-1 | meZ | aliqa | aliqa | 〔空〕 | Damas_1975 |
| v_copp1244-myZ-1 | myZ | nayak | nayak | 〔空〕 | Damas_1975 |
| v_copp1244-feB-1 | feB | ani | ani | 〔空〕 | Damas_1975 |
| v_copp1244-fyB-1 | fyB | aqqaluaq | aqqaluaq | 〔空〕 | Damas_1975 |
| v_copp1244-feZ-1 | feZ | angayuk | angayuk | 〔空〕 | Damas_1975 |
| v_copp1244-fyZ-1 | fyZ | nukaq | nukaq | 〔空〕 | Damas_1975 |

### 补充1. akla1241：p_aklanonakla1241

谱系：Austronesian；区域：Papunesia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_four, P1_A_six, P1_A_three, P1_B_four, P1_B_six, P1_B_three。

逐字段复核说明：逐行记录中manghod与igmánghod并存；注释空且同一来源。字符差别不构成误拼证据，不自行合并。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_aklanonakla1241-meB-1 | meB | manong | manong | 〔空〕 | SalasReyes1968 |
| p_aklanonakla1241-myB-1 | myB | manghod | manghod | 〔空〕 | SalasReyes1968 |
| p_aklanonakla1241-feB-1 | feB | manong | manong | 〔空〕 | SalasReyes1968 |
| p_aklanonakla1241-fyB-1 | fyB | igmánghod | igmánghod | 〔空〕 | SalasReyes1968 |
| p_aklanonakla1241-meZ-1 | meZ | igmánghod | igmánghod | 〔空〕 | SalasReyes1968 |
| p_aklanonakla1241-myZ-1 | myZ | manghod | manghod | 〔空〕 | SalasReyes1968 |
| p_aklanonakla1241-feZ-1 | feZ | igmánghod | igmánghod | 〔空〕 | SalasReyes1968 |
| p_aklanonakla1241-fyZ-1 | fyZ | manghod | manghod | 〔空〕 | SalasReyes1968 |

### 补充2. awap1236：v_awaawap1236

谱系：Nuclear Trans New Guinea；区域：Papunesia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_four, P1_A_six, P1_A_three, P1_B_four, P1_B_six, P1_B_three。

逐字段复核说明：八类单词形在不同参照者／年龄位置分布不一；来源一致、注释空，无法仅凭形式排除来源或编码问题。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| v_awaawap1236-meB-1 | meB | awahwa | awahwa | 〔空〕 | Loving_1974 |
| v_awaawap1236-myB-1 | myB | abaqkawa | abaqkawa | 〔空〕 | Loving_1974 |
| v_awaawap1236-meZ-1 | meZ | anahnowa | anahnowa | 〔空〕 | Loving_1974 |
| v_awaawap1236-myZ-1 | myZ | anahnowa | anahnowa | 〔空〕 | Loving_1974 |
| v_awaawap1236-feB-1 | feB | ayoqkawa | ayoqkawa | 〔空〕 | Loving_1974 |
| v_awaawap1236-fyB-1 | fyB | ayoqkawa | ayoqkawa | 〔空〕 | Loving_1974 |
| v_awaawap1236-feZ-1 | feZ | anahnowa | anahnowa | 〔空〕 | Loving_1974 |
| v_awaawap1236-fyZ-1 | fyZ | onanahwa | onanahwa | 〔空〕 | Loving_1974 |

### 补充3. dhuw1248：p_dhuwaldhuwalayolngudhuw1248

谱系：Pama-Nyungan；区域：。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_four, P1_A_six, P1_A_three, P1_B_four, P1_B_six, P1_B_three。

逐字段复核说明：八类均来自Keen2018，Value=Form而注释空；wäwa/yukuyuku/yapa的同形分布可复查，无法补推未记录的使用语境。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_dhuwaldhuwalayolngudhuw1248-meB-1 | meB | wäwa | wäwa | 〔空〕 | Keen2018 |
| p_dhuwaldhuwalayolngudhuw1248-myB-1 | myB | yukuyuku | yukuyuku | 〔空〕 | Keen2018 |
| p_dhuwaldhuwalayolngudhuw1248-feB-1 | feB | wäwa | wäwa | 〔空〕 | Keen2018 |
| p_dhuwaldhuwalayolngudhuw1248-fyB-1 | fyB | yukuyuku | yukuyuku | 〔空〕 | Keen2018 |
| p_dhuwaldhuwalayolngudhuw1248-meZ-1 | meZ | yapa | yapa | 〔空〕 | Keen2018 |
| p_dhuwaldhuwalayolngudhuw1248-myZ-1 | myZ | yapa | yapa | 〔空〕 | Keen2018 |
| p_dhuwaldhuwalayolngudhuw1248-feZ-1 | feZ | yapa | yapa | 〔空〕 | Keen2018 |
| p_dhuwaldhuwalayolngudhuw1248-fyZ-1 | fyZ | yukuyuku | yukuyuku | 〔空〕 | Keen2018 |

### 补充4. fort1240：p_fortsenalkiaifort1240

谱系：Austronesian；区域：Papunesia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_four, P1_A_six, P1_A_three, P1_B_four, P1_B_six, P1_B_three。

逐字段复核说明：toa-、tasi-、mane-、vavine-的尾连字符均原样保留；不把连接符自动解释为可删词缀，未见展开说明。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_fortsenalkiaifort1240-meB-1 | meB | toa- | toa- | 〔空〕 | Ludvigson1989 |
| p_fortsenalkiaifort1240-myB-1 | myB | tasi- | tasi- | 〔空〕 | Ludvigson1989 |
| p_fortsenalkiaifort1240-feB-1 | feB | mane- | mane- | 〔空〕 | Ludvigson1989 |
| p_fortsenalkiaifort1240-fyB-1 | fyB | tasi- | tasi- | 〔空〕 | Ludvigson1989 |
| p_fortsenalkiaifort1240-meZ-1 | meZ | mane- | mane- | 〔空〕 | Ludvigson1989 |
| p_fortsenalkiaifort1240-myZ-1 | myZ | vavine- | vavine- | 〔空〕 | Ludvigson1989 |
| p_fortsenalkiaifort1240-feZ-1 | feZ | tasi- | tasi- | 〔空〕 | Ludvigson1989 |
| p_fortsenalkiaifort1240-fyZ-1 | fyZ | tasi- | tasi- | 〔空〕 | Ludvigson1989 |

### 补充5. imbo1238：p_imbonguimbo1238

谱系：Nuclear Trans New Guinea；区域：Papunesia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_four, P1_A_six, P1_A_three, P1_B_four, P1_B_six, P1_B_three。

逐字段复核说明：awahwa、abaqkawa、ayoqkawa、anahnowa、onanahwa的八类位置均同源且无注释；与其他语言形式相近不构成转写错误证据。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_imbonguimbo1238-meB-1 | meB | awahwa | awahwa | 〔空〕 | shaw1974kinship |
| p_imbonguimbo1238-myB-1 | myB | abaqkawa | abaqkawa | 〔空〕 | shaw1974kinship |
| p_imbonguimbo1238-feB-1 | feB | ayoqkawa | ayoqkawa | 〔空〕 | shaw1974kinship |
| p_imbonguimbo1238-fyB-1 | fyB | ayoqkawa | ayoqkawa | 〔空〕 | shaw1974kinship |
| p_imbonguimbo1238-meZ-1 | meZ | anahnowa | anahnowa | 〔空〕 | shaw1974kinship |
| p_imbonguimbo1238-myZ-1 | myZ | anahnowa | anahnowa | 〔空〕 | shaw1974kinship |
| p_imbonguimbo1238-feZ-1 | feZ | anahnowa | anahnowa | 〔空〕 | shaw1974kinship |
| p_imbonguimbo1238-fyZ-1 | fyZ | onanahwa | onanahwa | 〔空〕 | shaw1974kinship |

### 补充6. jing1260：p_jinghpawjing1260

谱系：Sino-Tibetan；区域：。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_four, P1_A_six, P1_A_three, P1_B_four, P1_B_six, P1_B_three。

逐字段复核说明：phù带组合声调而naw不带；NFC正规化不删声调，单一来源KurabePC未附词项范围说明。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_jinghpawjing1260-meB-1 | meB | phù | phù | 〔空〕 | KurabePC |
| p_jinghpawjing1260-myB-1 | myB | naw | naw | 〔空〕 | KurabePC |
| p_jinghpawjing1260-feB-1 | feB | phù | phù | 〔空〕 | KurabePC |
| p_jinghpawjing1260-fyB-1 | fyB | naw | naw | 〔空〕 | KurabePC |
| p_jinghpawjing1260-meZ-1 | meZ | naw | naw | 〔空〕 | KurabePC |
| p_jinghpawjing1260-myZ-1 | myZ | naw | naw | 〔空〕 | KurabePC |
| p_jinghpawjing1260-feZ-1 | feZ | naw | naw | 〔空〕 | KurabePC |
| p_jinghpawjing1260-fyZ-1 | fyZ | naw | naw | 〔空〕 | KurabePC |

### 补充7. lard1243：p_lardillard1243

谱系：Tangkic；区域：Australia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_four, P1_A_six, P1_A_three, P1_B_four, P1_B_six, P1_B_three。

逐字段复核说明：meZ/myZ的Comment含bunjikarnan = honorific，记录形式仍为kuu；保留来源已有语体线索，不人工划分礼貌语义。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_lardillard1243-meB-1 | meB | kuu | kuu | 〔空〕 | McKnight1999 |
| p_lardillard1243-myB-1 | myB | kuu | kuu | 〔空〕 | McKnight1999 |
| p_lardillard1243-feB-1 | feB | kungku | kungku | 〔空〕 | McKnight1999 |
| p_lardillard1243-fyB-1 | fyB | kungku | kungku | 〔空〕 | McKnight1999 |
| p_lardillard1243-meZ-1 | meZ | kuu | kuu | bunjikarnan = honorific | McKnight1999 |
| p_lardillard1243-myZ-1 | myZ | kuu | kuu | bunjikarnan = honorific | McKnight1999 |
| p_lardillard1243-feZ-1 | feZ | yaku | yaku | 〔空〕 | McKnight1999 |
| p_lardillard1243-fyZ-1 | fyZ | kungku | kungku | 〔空〕 | McKnight1999 |

### 补充8. luba1250：v_lubakatangaluba1250

谱系：Atlantic-Congo；区域：Africa。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_four, P1_A_six, P1_A_three, P1_B_four, P1_B_six, P1_B_three。

逐字段复核说明：myB/fyB的nkasa各有Jenniges与Yukawa两条来源记录，去重后仍为单词形；没有字段证明其他格应补入同义词。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| v_lubakatangaluba1250-meB-1 | meB | mukulu | mukulu | 〔空〕 | jenniges_dictionnaire_1909 |
| v_lubakatangaluba1250-meZ-1 | meZ | nkolo | nkolo | 〔空〕 | jenniges_dictionnaire_1909 |
| v_lubakatangaluba1250-myZ-1 | myZ | nyenga | nyenga | 〔空〕 | jenniges_dictionnaire_1909 |
| v_lubakatangaluba1250-feB-1 | feB | nkolo | nkolo | 〔空〕 | jenniges_dictionnaire_1909 |
| v_lubakatangaluba1250-feZ-1 | feZ | nkolo | nkolo | 〔空〕 | jenniges_dictionnaire_1909 |
| v_lubakatangaluba1250-fyZ-1 | fyZ | nkasa | nkasa | 〔空〕 | jenniges_dictionnaire_1909 |
| v_lubakatangaluba1250-myB-1 | myB | nkasa | nkasa | 〔空〕 | jenniges_dictionnaire_1909 |
| v_lubakatangaluba1250-fyB-1 | fyB | nkasa | nkasa | 〔空〕 | jenniges_dictionnaire_1909 |
| v_lubakatangaluba1250-myB-2 | myB | nkasa | nkasa | 〔空〕 | yukawa_classified_1992 |
| v_lubakatangaluba1250-fyB-2 | fyB | nkasa | nkasa | 〔空〕 | yukawa_classified_1992 |

相关粗类别／未区分所指者性别的背景行（不加入八类分析）：

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| v_lubakatangaluba1250-mZ-1 | mZ | yaaya | yaaya | 〔空〕 | yukawa_classified_1992 |
| v_lubakatangaluba1250-fB-1 | fB | tuutu | tuutu | 〔空〕 | yukawa_classified_1992 |

### 补充9. maba1278：p_mabaindonesiamaba1278

谱系：Austronesian；区域：Papunesia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_four, P1_A_six, P1_A_three, P1_B_four, P1_B_six, P1_B_three。

逐字段复核说明：rimori tamoni与rimori mpinte含空格，其余有tenoe/remo；只记录完整形式和空格，不据外观作词素或描述构式标注。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_mabaindonesiamaba1278-meB-1 | meB | tenoe | tenoe | 〔空〕 | Holle1980v2 |
| p_mabaindonesiamaba1278-myB-1 | myB | rimori tamoni | rimori tamoni | 〔空〕 | Holle1980v2 |
| p_mabaindonesiamaba1278-feB-1 | feB | rimori tamoni | rimori tamoni | 〔空〕 | Holle1980v2 |
| p_mabaindonesiamaba1278-fyB-1 | fyB | rimori tamoni | rimori tamoni | 〔空〕 | Holle1980v2 |
| p_mabaindonesiamaba1278-meZ-1 | meZ | rimori mpinte | rimori mpinte | 〔空〕 | Holle1980v2 |
| p_mabaindonesiamaba1278-myZ-1 | myZ | rimori mpinte | rimori mpinte | 〔空〕 | Holle1980v2 |
| p_mabaindonesiamaba1278-feZ-1 | feZ | remo | remo | 〔空〕 | Holle1980v2 |
| p_mabaindonesiamaba1278-fyZ-1 | fyZ | rimori mpinte | rimori mpinte | 〔空〕 | Holle1980v2 |

### 补充10. mand1446：p_morgan1871mandanmand1446

谱系：Siouan；区域：North America。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_four, P1_A_six, P1_A_three, P1_B_four, P1_B_six, P1_B_three。

逐字段复核说明：所有八类均来自Morgan1871，连字符与撇号保留；无注释说明异写或推广，不能把相似片段自行合并。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_morgan1871mandanmand1446-meZ-1 | meZ | p-tä-meʼ-ha | p-tä-meʼ-ha | 〔空〕 | Morgan1871 |
| p_morgan1871mandanmand1446-myZ-1 | myZ | p-tä-meʼ-ha | p-tä-meʼ-ha | 〔空〕 | Morgan1871 |
| p_morgan1871mandanmand1446-meB-1 | meB | mooʼ-kä | mooʼ-kä | 〔空〕 | Morgan1871 |
| p_morgan1871mandanmand1446-feB-1 | feB | me-shoʼ-kä | me-shoʼ-kä | 〔空〕 | Morgan1871 |
| p_morgan1871mandanmand1446-myB-1 | myB | me-shoʼ-kä | me-shoʼ-kä | 〔空〕 | Morgan1871 |
| p_morgan1871mandanmand1446-fyB-1 | fyB | me-shoʼ-kä | me-shoʼ-kä | 〔空〕 | Morgan1871 |
| p_morgan1871mandanmand1446-feZ-1 | feZ | me-noʼ-ka | me-noʼ-ka | 〔空〕 | Morgan1871 |
| p_morgan1871mandanmand1446-fyZ-1 | fyZ | me-noʼ-ka | me-noʼ-ka | 〔空〕 | Morgan1871 |

### 补充11. nali1244：p_naliklukuramaunali1244

谱系：Austronesian；区域：Papunesia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_four, P1_A_six, P1_A_three, P1_B_four, P1_B_six, P1_B_three。

逐字段复核说明：meZ/myZ的dimafingu被Comment标为taboo，其余多为diagu；这是来源已有使用限制线索，不能据此单独改写称谓类别。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_naliklukuramaunali1244-meB-1 | meB | diagu | diagu | 〔空〕 | Chinnery1930 |
| p_naliklukuramaunali1244-myB-1 | myB | diagu | diagu | 〔空〕 | Chinnery1930 |
| p_naliklukuramaunali1244-feB-1 | feB | diagu | diagu | 〔空〕 | Chinnery1930 |
| p_naliklukuramaunali1244-fyB-1 | fyB | diagu | diagu | 〔空〕 | Chinnery1930 |
| p_naliklukuramaunali1244-meZ-1 | meZ | dimafingu | dimafingu | taboo | Chinnery1930 |
| p_naliklukuramaunali1244-myZ-1 | myZ | dimafingu | dimafingu | taboo | Chinnery1930 |
| p_naliklukuramaunali1244-feZ-1 | feZ | diagu | diagu | 〔空〕 | Chinnery1930 |
| p_naliklukuramaunali1244-fyZ-1 | fyZ | diagu | diagu | 〔空〕 | Chinnery1930 |

### 补充12. nese1235：p_nesenese1235

谱系：Austronesian；区域：Papunesia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_four, P1_A_six, P1_A_three, P1_B_four, P1_B_six, P1_B_three。

逐字段复核说明：tua-、tas-、jokhos-的尾连接符保留，来源Nese2006且注释空；不推断其必需词缀或补全形式。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_nesenese1235-meB-1 | meB | tua- | tua- | 〔空〕 | Nese2006 |
| p_nesenese1235-myB-1 | myB | tas- | tas- | 〔空〕 | Nese2006 |
| p_nesenese1235-feB-1 | feB | tua- | tua- | 〔空〕 | Nese2006 |
| p_nesenese1235-fyB-1 | fyB | tua- | tua- | 〔空〕 | Nese2006 |
| p_nesenese1235-meZ-1 | meZ | jokhos- | jokhos- | 〔空〕 | Nese2006 |
| p_nesenese1235-myZ-1 | myZ | jokhos- | jokhos- | 〔空〕 | Nese2006 |
| p_nesenese1235-feZ-1 | feZ | tua- | tua- | 〔空〕 | Nese2006 |
| p_nesenese1235-fyZ-1 | fyZ | tas- | tas- | 〔空〕 | Nese2006 |

### 补充13. ngal1292：p_dalabonngal1292

谱系：Gunwinyguan；区域：Australia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_four, P1_A_six, P1_A_three, P1_B_four, P1_B_six, P1_B_three。

逐字段复核说明：meZ的来源注释明确建议标address term，并描述该用法；因此存在指称／称呼用法混合的字段线索，但不能单凭注释重标整个系统。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_dalabonngal1292-meB-1 | meB | wawuɖ | wawuɖ | 〔空〕 | Evans2016 |
| p_dalabonngal1292-myB-1 | myB | wulkɨn | wulkɨn | 〔空〕 | Evans2016 |
| p_dalabonngal1292-feB-1 | feB | wulkɨn | wulkɨn | 〔空〕 | Evans2016 |
| p_dalabonngal1292-fyB-1 | fyB | wulkɨn | wulkɨn | 〔空〕 | Evans2016 |
| p_dalabonngal1292-meZ-1 | meZ | jabok | jabok | I suggest we just say 'address' term: this actually means 'no good person', and is part of a system widespread in Australia where men should use a highly negative word to address their sister, as a type of incest avoidenace. Also, for consistency shouldn't we also ask for the IPA version of this type of kin term as well (which would be bijweʔ | Evans2016 |
| p_dalabonngal1292-myZ-1 | myZ | jabok | jabok | 〔空〕 | Evans2016 |
| p_dalabonngal1292-feZ-1 | feZ | jabok | jabok | 〔空〕 | Evans2016 |
| p_dalabonngal1292-fyZ-1 | fyZ | wulkɨncan | wulkɨncan | 〔空〕 | Evans2016 |

### 补充14. nort2839：p_northambrymnort2839

谱系：Austronesian；区域：Papunesia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_four, P1_A_six, P1_A_three, P1_B_four, P1_B_six, P1_B_three。

逐字段复核说明：taovjen与talang均来自rio2007a，注释空；保留八格分布，没有来源字段证明其由粗类复制。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_northambrymnort2839-meB-1 | meB | taovjen | taovjen | 〔空〕 | rio2007a |
| p_northambrymnort2839-myB-1 | myB | taovjen | taovjen | 〔空〕 | rio2007a |
| p_northambrymnort2839-feB-1 | feB | talang | talang | 〔空〕 | rio2007a |
| p_northambrymnort2839-fyB-1 | fyB | talang | talang | 〔空〕 | rio2007a |
| p_northambrymnort2839-meZ-1 | meZ | talang | talang | 〔空〕 | rio2007a |
| p_northambrymnort2839-myZ-1 | myZ | talang | talang | 〔空〕 | rio2007a |
| p_northambrymnort2839-feZ-1 | feZ | talang | talang | 〔空〕 | rio2007a |
| p_northambrymnort2839-fyZ-1 | fyZ | talang | talang | 〔空〕 | rio2007a |

### 补充15. nort2961：v_northernojibwanort2961

谱系：Algic；区域：North America。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_four, P1_A_six, P1_A_three, P1_B_four, P1_B_six, P1_B_three。

逐字段复核说明：feZ/fyZ注释称女性说话者不按年龄区分女性同胞，而Form两格同为nimises；保留这项原文注释，不自动校正其他男性格。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| v_northernojibwanort2961-meB-1 | meB | nishikwese | nishikwese | 〔空〕 | godelier_metamorphoses_2011 |
| v_northernojibwanort2961-myB-1 | myB | nijimish | nijimish | 〔空〕 | godelier_metamorphoses_2011 |
| v_northernojibwanort2961-meZ-1 | meZ | nidawema | nidawema | 〔空〕 | godelier_metamorphoses_2011 |
| v_northernojibwanort2961-myZ-1 | myZ | nijimish | nijimish | 〔空〕 | godelier_metamorphoses_2011 |
| v_northernojibwanort2961-feB-1 | feB | nishimes | nishimes | 〔空〕 | godelier_metamorphoses_2011 |
| v_northernojibwanort2961-fyB-1 | fyB | nijimish | nijimish | 〔空〕 | godelier_metamorphoses_2011 |
| v_northernojibwanort2961-feZ-1 | feZ | nimises | nimises | unlike male speakers, female speakers do not have different terms for female siblings/paralell cousins based on age.  | godelier_metamorphoses_2011 |
| v_northernojibwanort2961-fyZ-1 | fyZ | nimises | nimises | unlike male speakers, female speakers do not have different terms for female siblings/paralell cousins based on age.  | godelier_metamorphoses_2011 |

### 补充16. olal1237：p_olalolal1237

谱系：Austronesian；区域：Papunesia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_four, P1_A_six, P1_A_three, P1_B_four, P1_B_six, P1_B_three。

逐字段复核说明：taling/maningeri均来自Lane1958且注释空；形式违例可定位，不能推断说话者条件是误录或心理机制。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_olalolal1237-meB-1 | meB | taling | taling | 〔空〕 | Lane1958 |
| p_olalolal1237-myB-1 | myB | taling | taling | 〔空〕 | Lane1958 |
| p_olalolal1237-feB-1 | feB | maningeri | maningeri | 〔空〕 | Lane1958 |
| p_olalolal1237-fyB-1 | fyB | maningeri | maningeri | 〔空〕 | Lane1958 |
| p_olalolal1237-meZ-1 | meZ | taling | taling | 〔空〕 | Lane1958 |
| p_olalolal1237-myZ-1 | myZ | taling | taling | 〔空〕 | Lane1958 |
| p_olalolal1237-feZ-1 | feZ | taling | taling | 〔空〕 | Lane1958 |
| p_olalolal1237-fyZ-1 | fyZ | taling | taling | 〔空〕 | Lane1958 |

### 补充17. osag1243：p_morgan1871osageosag1243

谱系：Siouan；区域：North America。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_four, P1_A_six, P1_A_three, P1_B_four, P1_B_six, P1_B_three。

逐字段复核说明：Morgan1871八格有数种带连接符与变音的形式；保持字符差别，没有记录支持音系归并。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_morgan1871osageosag1243-meZ-1 | meZ | we-tunʼ-ka | we-tunʼ-ka | 〔空〕 | Morgan1871 |
| p_morgan1871osageosag1243-myZ-1 | myZ | we-tunʼ-ka | we-tunʼ-ka | 〔空〕 | Morgan1871 |
| p_morgan1871osageosag1243-fyZ-1 | fyZ | we-tunʼ-ka | we-tunʼ-ka | 〔空〕 | Morgan1871 |
| p_morgan1871osageosag1243-myB-1 | myB | we-sonʼ-kä | we-sonʼ-kä | 〔空〕 | Morgan1871 |
| p_morgan1871osageosag1243-fyB-1 | fyB | we-sonʼ-kä | we-sonʼ-kä | 〔空〕 | Morgan1871 |
| p_morgan1871osageosag1243-feZ-1 | feZ | we-shoʼ-la | we-shoʼ-la | 〔空〕 | Morgan1871 |
| p_morgan1871osageosag1243-meB-1 | meB | we-sheʼ-lä | we-sheʼ-lä | 〔空〕 | Morgan1871 |
| p_morgan1871osageosag1243-feB-1 | feB | we-chinʼ-to | we-chinʼ-to | 〔空〕 | Morgan1871 |

### 补充18. pawn1254：p_morgan1871grandpawneepawn1254

谱系：Caddoan；区域：North America。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_four, P1_A_three, P1_B_four, P1_B_three。

逐字段复核说明：a-täʼ-ke与a-täʼ-he等形式差异按原表保留；该系统四特征下违例而扩展六特征下并非同一结果，不能混称所有特征集均不合取。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_morgan1871grandpawneepawn1254-feB-1 | feB | ta-läʼ-lik-tis | ta-läʼ-lik-tis | 〔空〕 | Morgan1871 |
| p_morgan1871grandpawneepawn1254-fyB-1 | fyB | käʼ-we-ta | käʼ-we-ta | 〔空〕 | Morgan1871 |
| p_morgan1871grandpawneepawn1254-myZ-1 | myZ | a-täʼ-ke | a-täʼ-ke | 〔空〕 | Morgan1871 |
| p_morgan1871grandpawneepawn1254-meZ-1 | meZ | a-täʼ-he | a-täʼ-he | 〔空〕 | Morgan1871 |
| p_morgan1871grandpawneepawn1254-feZ-1 | feZ | a-täʼ-he | a-täʼ-he | 〔空〕 | Morgan1871 |
| p_morgan1871grandpawneepawn1254-fyZ-1 | fyZ | a-täʼ-he | a-täʼ-he | 〔空〕 | Morgan1871 |
| p_morgan1871grandpawneepawn1254-meB-1 | meB | a-däʼ-de | a-däʼ-de | 〔空〕 | Morgan1871 |
| p_morgan1871grandpawneepawn1254-myB-1 | myB | a-däʼ-de | a-däʼ-de | 〔空〕 | Morgan1871 |

### 补充19. rovi1238：p_rovianarovi1238

谱系：Austronesian；区域：Papunesia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_four, P1_A_six, P1_A_three, P1_B_four, P1_B_six, P1_B_three。

逐字段复核说明：tasi-na和vavene-na同源、注释空；仅凭共同后缀外观不做新增形态切分。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_rovianarovi1238-meB-1 | meB | tasi-na | tasi-na | 〔空〕 | WaterhouseJones1949 |
| p_rovianarovi1238-myB-1 | myB | tasi-na | tasi-na | 〔空〕 | WaterhouseJones1949 |
| p_rovianarovi1238-feB-1 | feB | tasi-na | tasi-na | 〔空〕 | WaterhouseJones1949 |
| p_rovianarovi1238-fyB-1 | fyB | tasi-na | tasi-na | 〔空〕 | WaterhouseJones1949 |
| p_rovianarovi1238-meZ-1 | meZ | vavene-na | vavene-na | 〔空〕 | WaterhouseJones1949 |
| p_rovianarovi1238-myZ-1 | myZ | vavene-na | vavene-na | 〔空〕 | WaterhouseJones1949 |
| p_rovianarovi1238-feZ-1 | feZ | tasi-na | tasi-na | 〔空〕 | WaterhouseJones1949 |
| p_rovianarovi1238-fyZ-1 | fyZ | tasi-na | tasi-na | 〔空〕 | WaterhouseJones1949 |

### 补充20. sons1242：p_sonsorolsons1242

谱系：Austronesian；区域：Papunesia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P1_A_four, P1_A_six, P1_A_three, P1_B_four, P1_B_six, P1_B_three。

逐字段复核说明：keinapa、widi、meaŋa-i同源、注释空；保留各类形式，不据共同串推断另一个未记录类别。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_sonsorolsons1242-meB-1 | meB | keinapa | keinapa | 〔空〕 | Capell1969 |
| p_sonsorolsons1242-myB-1 | myB | widi | widi | 〔空〕 | Capell1969 |
| p_sonsorolsons1242-feB-1 | feB | meaŋa-i | meaŋa-i | 〔空〕 | Capell1969 |
| p_sonsorolsons1242-fyB-1 | fyB | meaŋa-i | meaŋa-i | 〔空〕 | Capell1969 |
| p_sonsorolsons1242-meZ-1 | meZ | meaŋa-i | meaŋa-i | 〔空〕 | Capell1969 |
| p_sonsorolsons1242-myZ-1 | myZ | meaŋa-i | meaŋa-i | 〔空〕 | Capell1969 |
| p_sonsorolsons1242-feZ-1 | feZ | meaŋa-i | meaŋa-i | 〔空〕 | Capell1969 |
| p_sonsorolsons1242-fyZ-1 | fyZ | meaŋa-i | meaŋa-i | 〔空〕 | Capell1969 |

### 补充21. umbu1257：v_umbunduumbu1257

谱系：Atlantic-Congo；区域：Africa。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P5。

逐字段复核说明：八行均为gibson_social_1952，Value=Form且注释空；P5不兼容是程序对该表的判定，原始语境与采集展开过程无法由这八行确认。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| v_umbunduumbu1257-meB-1 | meB | huvange | huvange | 〔空〕 | gibson_social_1952 |
| v_umbunduumbu1257-myB-1 | myB | manjange | manjange | 〔空〕 | gibson_social_1952 |
| v_umbunduumbu1257-meZ-1 | meZ | huvange | huvange | 〔空〕 | gibson_social_1952 |
| v_umbunduumbu1257-myZ-1 | myZ | manjange | manjange | 〔空〕 | gibson_social_1952 |
| v_umbunduumbu1257-feB-1 | feB | mume | mume | 〔空〕 | gibson_social_1952 |
| v_umbunduumbu1257-fyB-1 | fyB | mume | mume | 〔空〕 | gibson_social_1952 |
| v_umbunduumbu1257-feZ-1 | feZ | mbuale | mbuale | 〔空〕 | gibson_social_1952 |
| v_umbunduumbu1257-fyZ-1 | fyZ | mbuale | mbuale | 〔空〕 | gibson_social_1952 |

相关粗类别／未区分所指者性别的背景行（不加入八类分析）：

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| v_umbunduumbu1257-mB-1 | mB | mume | mume | 〔空〕 | gibson_social_1952 |
| v_umbunduumbu1257-mZ-1 | mZ | mukāi | mukāi | 〔空〕 | gibson_social_1952 |
| v_umbunduumbu1257-fB-1 | fB | mume | mume | 〔空〕 | gibson_social_1952 |
| v_umbunduumbu1257-fZ-1 | fZ | mbuale | mbuale | 〔空〕 | gibson_social_1952 |

### 补充22. umpi1239：v_umpilaumpi1239

谱系：Pama-Nyungan；区域：Australia。候选粗类展开解释：有显式展开／推断／自动填入注释字面线索，待核对所指；真实语义解释：无法判断。

所涉程序命题：P1_A_four, P1_A_six, P1_A_three, P1_B_four, P1_B_six, P1_B_three。

逐字段复核说明：全部八类Comment为Autofilled from CB Austkin data，确认存在上游自动填入注释；不能由此确定每格是粗类别展开或判断原语义错误。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| v_umpilaumpi1239-meB-1 | meB | yapu | yapu | Autofilled from CB Austkin data | bowern_austkin_nodate |
| v_umpilaumpi1239-myB-1 | myB | ya'a | ya'a | Autofilled from CB Austkin data | bowern_austkin_nodate |
| v_umpilaumpi1239-meZ-1 | meZ | ya'a | ya'a | Autofilled from CB Austkin data | bowern_austkin_nodate |
| v_umpilaumpi1239-myZ-1 | myZ | ya'a | ya'a | Autofilled from CB Austkin data | bowern_austkin_nodate |
| v_umpilaumpi1239-feB-1 | feB | yapu | yapu | Autofilled from CB Austkin data | bowern_austkin_nodate |
| v_umpilaumpi1239-fyB-1 | fyB | ya'a | ya'a | Autofilled from CB Austkin data | bowern_austkin_nodate |
| v_umpilaumpi1239-feZ-1 | feZ | ya'a | ya'a | Autofilled from CB Austkin data | bowern_austkin_nodate |
| v_umpilaumpi1239-fyZ-1 | fyZ | ya'a | ya'a | Autofilled from CB Austkin data | bowern_austkin_nodate |

### 补充23. urak1238：p_uraklawoiurak1238

谱系：Austronesian；区域：Eurasia。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P5。

逐字段复核说明：ca、adi、kaka均为Hogan1988UrakLawo且注释空；没有字段直接解释参照者条件和词项范围，P5的真实语言解释仍未确认。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_uraklawoiurak1238-meB-1 | meB | ca | ca | 〔空〕 | Hogan1988UrakLawo |
| p_uraklawoiurak1238-myB-1 | myB | adi | adi | 〔空〕 | Hogan1988UrakLawo |
| p_uraklawoiurak1238-feB-1 | feB | kaka | kaka | 〔空〕 | Hogan1988UrakLawo |
| p_uraklawoiurak1238-fyB-1 | fyB | adi | adi | 〔空〕 | Hogan1988UrakLawo |
| p_uraklawoiurak1238-meZ-1 | meZ | ca | ca | 〔空〕 | Hogan1988UrakLawo |
| p_uraklawoiurak1238-myZ-1 | myZ | adi | adi | 〔空〕 | Hogan1988UrakLawo |
| p_uraklawoiurak1238-feZ-1 | feZ | kaka | kaka | 〔空〕 | Hogan1988UrakLawo |
| p_uraklawoiurak1238-fyZ-1 | fyZ | adi | adi | 〔空〕 | Hogan1988UrakLawo |

### 补充24. yomb1244：v_yombeyomb1244

谱系：Atlantic-Congo；区域：Africa。候选粗类展开解释：有显式展开／推断／自动填入注释字面线索，待核对所指；真实语义解释：无法判断。

所涉程序命题：P1_A_four, P1_A_six, P1_A_three, P1_B_four, P1_B_six, P1_B_three。

逐字段复核说明：女性／男性姐妹相关行有Inferred; NA注释，其他行注释空；确认推断标记存在，不把它直接判作已证实的粗类展开。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| v_yombeyomb1244-meB-1 | meB | bakhomba | bakhomba | 〔空〕 | mbadu_kumbu_du_2012 |
| v_yombeyomb1244-myB-1 | myB | baphangi | baphangi | 〔空〕 | mbadu_kumbu_du_2012 |
| v_yombeyomb1244-meZ-1 | meZ | bakhomba | bakhomba | Inferred; NA | mbadu_kumbu_du_2012 |
| v_yombeyomb1244-myZ-1 | myZ | bakhomba | bakhomba | Inferred; NA | mbadu_kumbu_du_2012 |
| v_yombeyomb1244-feB-1 | feB | bakhomba | bakhomba | 〔空〕 | mbadu_kumbu_du_2012 |
| v_yombeyomb1244-fyB-1 | fyB | baphangi | baphangi | 〔空〕 | mbadu_kumbu_du_2012 |
| v_yombeyomb1244-feZ-1 | feZ | bakhomba | bakhomba | Inferred; NA | mbadu_kumbu_du_2012 |
| v_yombeyomb1244-fyZ-1 | fyZ | bakhomba | bakhomba | Inferred; NA | mbadu_kumbu_du_2012 |

相关粗类别／未区分所指者性别的背景行（不加入八类分析）：

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| v_yombeyomb1244-mB-1 | mB | bakhomba | bakhomba | 〔空〕 | mbadu_kumbu_du_2012 |
| v_yombeyomb1244-mZ-1 | mZ | bakhomba | bakhomba | 〔空〕 | mbadu_kumbu_du_2012 |
| v_yombeyomb1244-fB-1 | fB | bakhomba | bakhomba | 〔空〕 | mbadu_kumbu_du_2012 |
| v_yombeyomb1244-fZ-1 | fZ | bakhomba | bakhomba | 〔空〕 | mbadu_kumbu_du_2012 |

### 补充25. yura1255：p_yuracareyura1255

谱系：Yuracaré；区域：South America。候选粗类展开解释：无法判断；真实语义解释：无法判断。

所涉程序命题：P5。

逐字段复核说明：pii、paa、pipi、dyama、yee、neshu均为Hirtzel2010且注释空；不因pii/pipi形式接近就合并或作叠音语义分析。

| 记录ID | 类别 | Value | Form | Comment | Source |
|---|---|---|---|---|---|
| p_yuracareyura1255-meB-1 | meB | pii | pii | 〔空〕 | Hirtzel2010 |
| p_yuracareyura1255-myB-1 | myB | paa | paa | 〔空〕 | Hirtzel2010 |
| p_yuracareyura1255-feB-1 | feB | pipi | pipi | 〔空〕 | Hirtzel2010 |
| p_yuracareyura1255-fyB-1 | fyB | dyama | dyama | 〔空〕 | Hirtzel2010 |
| p_yuracareyura1255-meZ-1 | meZ | yee | yee | 〔空〕 | Hirtzel2010 |
| p_yuracareyura1255-myZ-1 | myZ | yee | yee | 〔空〕 | Hirtzel2010 |
| p_yuracareyura1255-feZ-1 | feZ | neshu | neshu | 〔空〕 | Hirtzel2010 |
| p_yuracareyura1255-fyZ-1 | fyZ | dyama | dyama | 〔空〕 | Hirtzel2010 |

抽查未修改任何原始记录或S2共享结果。空格与Value/Form差异可能来自书写方式或上游预处理；缺少相关线索也不能证明原语义数据无误。


## 模型化不确定性与拟合状态

主M4的5000次谱系整组系数重拟合全部成功；三个GLMM分别按2000/10000次上限作两次预置尝试，均因precision loss未达到预定收敛标准。GLMM实际使用909个系统、123个谱系组、25452对；不将这些近似后验作为稳定推断。全部近似参数、梯度、警告、时间与失败状态见uncertainty_results.json和glmm_results.json。

## 运行后观察与适用范围

地域缺失系统不补猜；语系/语言验证保留全部记录，地域验证及地域GLMM使用地域已知完整个案。M4不强制合取或传递划分，预测增益与结构兼容性是两个层次。
