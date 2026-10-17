# 第三版完整资料包

GitHub发布版本：`v3-materials-20261017`。附件名：`kinship-research-v3-complete.zip`；同页提供SHA-256校验文件。资料包内的`资料包版本.json`记录准确提交、Git历史包校验值及文件范围。此版本为研究工作稿的资料交付，不代表期刊发表。

## 材料范围

- `outputs/论文_中文第三版.*`和`outputs/第三版_摘要.txt`：当前论文的Markdown、Word、PDF、TXT和摘要；Word保留用户模板字体设置，PDF为替代字体预览。
- `literature/`：51项准入完整全文来源；共57份源PDF及对应TXT，另含不完整副本、早期版本和补充文件。未取得完整全文的来源不进入新版引用；版本及排除状态以登记表为准。
- `data/`、`analysis/`、`tests/`、`Makefile`：锁定数据、第三版及历史分析实现、固定环境依赖和必要测试。
- `results/`、`notes/`、`docs/`：实际结果、逐数字来源、运行前计划及后续附录、数字与引文核查、独立评审、用户格式模板、干净环境复现证据。
- `CLAUDE.md`、`CLAUDE_TODO.md`、`CLAUDE_REVIEW_CHECKLIST.md`、`CLAUDE_DECISIONS_V3.md`：阅读入口、后续研究、复查清单和矛盾决定。
- 第二版及更早材料保留为历史参照；当前版本入口以根目录README和第三版文件名为准。
- `仓库历史.bundle`：交付提交的完整祖先历史及`baseline-v1`、本次发布标签；不包含工作区凭据或本地Git配置。

## 解压与阅读

解压后进入`kinship_research/`，先读README，再打开`outputs/论文_中文第三版.docx`。仅阅读论文与文献无需安装Python。

`outputs/资料包文件清单.json`列出交付提交内的材料路径、字节数及SHA-256（清单自身除外）。ZIP另附`仓库历史.bundle`和`资料包版本.json`，其来源与校验关系在版本文件中说明。GitHub Release的SHA-256文件校验整个ZIP。

## 恢复可复现仓库

科学分析的运行门会核对协议提交及祖先关系，直接解压的文件目录没有Git对象。请在解压目录内运行以下命令，以历史包创建完整仓库；此步骤无需连接GitHub：

```bash
git clone --branch codex/major-revision ./仓库历史.bundle ../kinship-reproduction
cd ../kinship-reproduction
git tag --list
python -S analysis/v3/clean_reproduce.py --workspace /tmp/kinship-v3-reproduction
```

前两步恢复资料包对应的完整提交。最后一条命令需要Python 3.12和可用的包源，以安装固定依赖后实际执行全部分析和测试；它不会把已保存结果当成重新计算。系统字体和论文导出工具另见`analysis/v3/README.md`及导出说明。也可使用普通GitHub完整克隆；无需在解压文件上手工`git init`或重建协议历史。

论文、结果、代码和既有审核的科学内容未因这次打包而改动。数据和第三方文献仍保留各自来源、版本及许可说明。
