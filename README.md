# 亲属称谓的语义组合：跨语言兄弟姐妹词形共享研究

本仓库保存一项已完成的公开数据库研究，包括中文研究计划、文献综述、实证论文，以及可复现的数据、代码和结果。

研究的问题是：所指者性别、相对年龄和参照者性别的独立贡献，能否预测两个兄弟姐妹类别是否共享词形？加入传统“同性／异性兄弟姐妹”特征之后，进一步的组合项还能带来多少跨语系预测增益？

## 研究与主要结果

主样本包含 **939个语言记录系统、125个谱系组、26,292个无序类别对**。研究以Kinbank词形记录为基础，使用Glottolog官方分类整组留出语系，比较三个模型：

| 模型 | 语义编码 | 设计秩 |
|---|---|---:|
| 原始加性 | 所指者性别、年龄、参照者性别差异 | 4 |
| 经典加性 | 原始差异加传统相对性别 | 5 |
| 完整两两交互 | 原始差异及其全部两两乘积 | 7 |

完整两两交互对七种非零差异组合具有饱和表达能力。主设定为固定岭惩罚 `C=1`，以未见谱系组上的语言等权平均对数损失衡量预测表现：

| 完整交互相对的基准 | 对数损失增益 | 95%谱系重采样区间 |
|---|---:|---|
| 原始加性 | 0.004423 | [-0.000510, 0.008205] |
| 经典加性 | 0.001843 | [-0.000604, 0.006120] |

正值表示完整交互的损失更低。主结果为小幅点估计改善，两项区间均包含零；传统相对性别之后的剩余增益随词形定义和惩罚设定变化。这里测量的是跨语言总体词形共享的预测结构，全部预设敏感性结果随论文和代码保存。

![预设条件下的样本外预测增益](analysis/robustness_gain.png)

## 文献与阅读材料

正式文献包括 **45项独立学术著作：40项取得全文PDF，5项取得真实摘要**。另存2项出版商开篇预览及1项仅书目资料，分别标示。40项PDF包含正式期刊版、作者稿、预印本或对应工作论文；补充材料和同一著作的早期版本不重复计数。

其中B03保存作者预印本PDF，并以正式全文XML核对731种语言等发现；C12引用2008年正式期刊论文，所获PDF为2007年同题同作者NBER工作论文。逐项访问状态、所读版本、证据位置与下载尝试见文献台账和无法下载清单。

## 成果导航

- **研究计划：** [Markdown](outputs/研究计划_完善版.md)｜[PDF](outputs/研究计划_完善版.pdf)｜[Word](outputs/研究计划_完善版.docx)。
- **中文论文：** [Markdown](outputs/论文_中文实证稿.md)｜[PDF](outputs/论文_中文实证稿.pdf)｜[Word](outputs/论文_中文实证稿.docx)。
- **文献综述与证据台账：** [Markdown](outputs/文献综述与证据台账.md)｜[PDF](outputs/文献综述与证据台账.pdf)。
- **PDF无法下载及版本替代清单：** [Markdown](outputs/PDF无法下载清单.md)｜[PDF](outputs/PDF无法下载清单.pdf)。
- **结构化书目：** [CSV](outputs/文献登记表.csv)｜[JSON](outputs/文献登记表.json)。
- [复现说明](analysis/README.md)：数据版本、运行环境、输出字段和核验方法。

`literature/`按A亲属研究、B语义范畴与效率、C统计与数据方法保存PDF和登记表；`data/`保存锁定版本的必要原始表；`analysis/`保存脚本、协议、配对数据、折外预测与图表；`notes/`保存摘要、阅读证据和独立核验记录。

## 复现

```bash
git clone https://github.com/WuYusen825/kinship-semantic-interactions.git
cd kinship-semantic-interactions
```


使用Python 3.12，在仓库根目录运行：

```bash
python -m pip install -r analysis/requirements.txt
python analysis/audit.py
python analysis/analyze.py
python analysis/verify_results_independent.py
```

完整资料已保留分析所需数据。需要重新获取原始文件时，可运行`python analysis/fetch_data.py`，按锁定commit下载并核对核心文件SHA-256。绘图字体配置及其他环境说明见[分析目录说明](analysis/README.md)。

原始数据来自[Kinbank](https://github.com/kinbank/kinbank)和[Glottolog CLDF](https://github.com/glottolog/glottolog-cldf)。版本、许可及文件校验值保存在[provenance.json](analysis/provenance.json)；文献与数据沿用各自来源的引用和许可要求。

## 数据版本与研究记录

| 项目 | 固定版本／时间 |
|---|---|
| Kinbank | `925cc0e702ae5481cfe0088aaa0e69c3991000f3` |
| Glottolog CLDF | `072ca0d0410039fb8b779be8fc165bac575d2cda` |
| 原分析执行日期 | 2026年10月14日 |
| 仓库整理日期 | 2026年10月15日 |

事前分析协议见[主协议](analysis/protocol_frozen.md)及[结果生成前的补充协议](analysis/protocol_addendum_before_outcomes.md)。完整数值见[results.json](analysis/results.json)，独立复算记录见[independent_verification.json](notes/independent_verification.json)。研究原计划同时保留在[original_research_plan.md](original_research_plan.md)。

本仓库为研究工作稿与复现材料。原始数据和第三方文献保留各自来源、版本及许可；不以仓库整体的单一许可覆盖这些材料。
