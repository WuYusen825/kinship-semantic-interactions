# 实际分析的复现说明

本目录包含已经执行的分析，不只是待运行方案。中文摘要见 `analysis_report.md`，数值的机器可读版本见 `results.json`；原始版本、校验值、事前固定协议时间和环境见 `provenance.json`。

## 数据版本

- Kinbank：`925cc0e702ae5481cfe0088aaa0e69c3991000f3`，本次仓库许可为 CC BY 4.0。引用 Passmore 等人的数据库论文及此 commit，不把旧论文样本数当作当前文件样本数。
- Glottolog CLDF：`072ca0d0410039fb8b779be8fc165bac575d2cda`，官方版本 Glottolog 5.3（2026），CC BY 4.0。引用 Hammarström、Forkel、Haspelmath 与 Bank（2026）。

原始文件在相邻 `../data/`，处理结果没有覆盖原文件。`sibling_records_selected.csv` 同时保存原始 `Value`、数据库 `Form`、本次标准化词形和引用来源。`excluded_genealogy.csv` 列出没有解决谱系分类的两个对象。

## 运行

使用 Python 3.12。依赖的实际版本见 `requirements.txt`。若原始数据镜像没有随包提供，先运行 `python fetch_data.py` 下载锁定版本的必要公开文件；该脚本核对分析所用四个核心表的 SHA-256。随后依次运行：

```bash
python audit.py
python analyze.py
```

脚本路径相对于本文件确定，在完整 `kinship_research/analysis`、`kinship_research/data` 目录结构中可复现。原冻结协议及补充协议须保留，主脚本核对原协议 SHA-256，不另造事前时间。绘图使用 Noto CJK 字体；数据拟合不依赖字体，其他系统可安装 Noto 字体并在 `make_figures()` 内设置其路径。

## 输出字段与解释

`pairs_primary.csv` 每行是一个语言资料 ID 内的无序类别对，共 26,292 行；`category_a/category_b` 不重复反向配对。`Dr/Da/De` 依次表示所指者性别、相对年龄、参照者性别差异。`pattern` 是三位字符串，例如 `001`；使用 pandas 读取时应指定 `dtype={'pattern':str}`，否则自动数值转换会丢失前导零。

`oof_predictions.csv` 保存 8 种预先固定条件的语系五折留出及主样本语言五折留出，共 9 组验证；同一类别对在不同验证条件中重复出现是为了保存每次预测。`p_*` 为折外概率，`loss_*` 为自然对数 log loss，`brier_*` 为 Brier score。`language_oof_scores.csv` 已先在每个语言内平均，每个语言均权；`results.json` 的区间按谱系簇抽样，不将类别对视为独立样本。

主比较使用固定 `C=1` 的岭 logistic 回归，原始加性、经典加性和两两交互设计秩为 4、5、7。本轮估计跨语言混合后的共享词形边际概率，没有拟合语言随机效应 GLMM。无惩罚分析只是事前补充的敏感性，不能替换主要结果。两两交互在七个差异单元上饱和，`seven_cell_probabilities.csv` 的全样本拟合值属于结构描述，主要证据仍是折外评分。

## 核验

脚本已断言：各折训练／测试 Glottocode 与谱系组不重叠、每个预测有效、主设计保持秩、七单元饱和最大似然恢复实际共享率。独立设计审计另从原始词形重建所有主结果，并验证全部九组损失、Brier score、语言权重和 bootstrap 区间。具体审计见相邻 `../notes/design_audit.md`。

可直接使用的中文图为 `seven_cell_fit.png/svg`、`robustness_gain.png/svg`。
