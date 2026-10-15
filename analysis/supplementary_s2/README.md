# 补充分析S2复现入口

本目录是已知冻结结果、S1和评审核查结果后的事后补充分析，不是预注册。最终协议独立提交`6ba7afba369d3d15446ea7571eabd2117b7e8c74`，早于全部S2实测；协议SHA-256为`61874a1c28ab37758670a61d12e08b6097af07f7922f63cfd76da5dacfcef8be`。原分析、S1和旧论文保留。

在包含Git历史的仓库根目录运行（完整资料包没有`.git`，须先克隆仓库以复核协议提交）：

```bash
python -m pip install -r analysis/supplementary_s2/requirements.txt
python analysis/supplementary_s2/test_partitions.py
python analysis/supplementary_s2/design_rank.py
python analysis/supplementary_s2/run_s2.py --phase all
```

使用Python 3.12.14；绘图需Noto CJK字体。完整运行会重新写入本目录的S2输出，包含1620次预测/校准拟合、5000次系数整谱系重拟合，以及三模型GLMM的预置尝试。建议在独立克隆中执行，保留已归档的原始执行日志。`--phase predictions`只运行预测，`--phase assemble`仅合并已有组件及重建汇总表；`plot_s2.py`只从已有结果绘图，不拟合模型。

## 阅读顺序

1. [协议](protocol_s2.md)与[纯结构计数](structural_theory.md)：任意合取为主，单叶递归树并列；经典命题来自Kronenfeld直接全文。
2. [中文结果报告](s2_report.md)与[合并JSON](s2_results.json)：含全部20个测量×估计×权重条件及三种验证。
3. [全部420项比较](s2_crossed_comparisons.csv)、[逐系统分数](s2_language_scores.csv)、[折信息](s2_fold_info.csv)、[单元校准](s2_cell_calibration.csv)。损失差为基准减替代模型，正值利于后者。
4. [划分检验](s2_partition_tests.csv)、[全部违例](s2_violations.csv)、[字段审计](s2_violation_audit.md)。数据库字段核查不等于已确认真实语义反例。
5. [系数重拟合](uncertainty_results.json)、[5000次系数](coefficient_bootstrap.csv)和[GLMM诊断](glmm_results.json)。固定折外预测区间与包含重拟合的系数区间是不同估计对象。

## 适用范围

主设定为D1、无惩罚最大似然、训练和评分均谱系组等权、语系整组留出。C=1和语言等权完整保留。地域缺失30个系统；地域验证及地域GLMM使用909个已知地域系统，其他验证保留全部适用记录。

P1、P2、P4得到支持；P3与P6整体未得到支持。P5有3个数据库表示不兼容记录，但其真实语义归因仍无法判断。三个GLMM均未达到预定收敛标准，其近似后验只供失败诊断，不能当作稳定模型化推断。地域澄清提交晚于并行GLMM启动的实际偏差见[时序说明](implementation_missing_area_before_glmm.md)。独立数值审计范围见[第三轮报告](../../notes/review/independent_revision_review_round3.md)。

执行源码快照、输入哈希、随机种子、迭代诊断与失败记录均保留。后来新增的汇总和绘图不被描述为原始拟合时已经执行的步骤。
