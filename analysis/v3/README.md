# 第三版分析复现

本目录仅向`results/`和第三版报告写入新结果。入口不执行会写回冻结S1/S2的旧主程序。T0重建原始数据并重拟合已有结果；随后使用新种子`20261016`，全部规定的自助重复保持5000次。原语言／谱系分折逐系统继承，地域验证排除地域缺失记录。

## 安装与完整执行

实测环境为Linux、CPython 3.12.14。运行依赖及递归依赖版本分别固定于`requirements.txt`与`environment.lock.txt`，后者是pip约束文件。无需R、外部数据库或在线下载新数据。

中文图形使用系统Noto CJK字体；字体不属于Python包，其他机器需另安装可显示中文的字体。字形和PDF预览的字体替代不改变数据表中的统计值。

在仓库根目录运行：

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r analysis/v3/requirements.txt
make all PYTHON=.venv/bin/python
make check PYTHON=.venv/bin/python
```

依赖安装需要可访问所用Python包源；分析使用仓库内已经锁定的Kinbank、Glottolog和分类树数据。必须保留Git历史、`baseline-v1`标签与锁定协议提交，不能仅下载不含Git对象的源码压缩包代替仓库。执行门会检验协议当前SHA、提交对象内容及其为HEAD祖先，并检查T0/T1通过标记。第一次执行请使用完整克隆。

`make all`失败时立即停止，日志见`results/reproducibility/pipeline_logs/`，阶段及环境清单见同级`pipeline_manifest.json`。缺失入口会在执行任何分析前报错。每次实际运行另追加`results/run_log.csv`；不会清空既有日志。固定BLAS／OpenMP单线程、`PYTHONHASHSEED=20261016`及无界面绘图环境，由统一入口传给所有子进程。

## 阶段与依赖

```text
T0 → T1 → T2原求解器主条件(cv/full) → T2精化(cv/full) → T3 → T4
   → T5(strict/full/独立核查) → T2(compare) → T6可行性 → T6关联 → T7 → T8汇总
```

T2的模型拟合先完成，再以T5严格样本的同系统配对预测完成跨模型比较。T5的strict输出由full阶段验证哈希后复用。T3／T4理论上可并行，统一复现命令采用顺序执行，避免同时追加日志或消耗内存。

| 阶段 | 实际入口 | 主要输出 |
|---|---|---|
| T0 | `reproduce_baseline.py` | `results/baseline/`原始字段重建、既有数值复现与保护核查 |
| T1 | `build_t1.py` | `results/t1/`全部4140划分、四语言精确DNF成本、625/939/939映射、Parquet往返检查 |
| T2 initial | `run_t2.py --solver-profile planned`，分别`--phase cv/full --sample strict --weighting family`，cv另加`--validation family` | `results/t2/initial_solver/`原求解器主条件失败与NA诊断 |
| T2 cv | `run_t2.py --phase cv` | 三样本×两权重×三验证的精确归一化模型 |
| T2 full | `run_t2.py --phase full` | 全样本估计、5000次预测检验与主条件系数重抽 |
| T3 | `basis_enrichment.py` | `results/t3/`特征富集、形状参照及描述语言比较 |
| T4 | `position_tests.py` | `results/t4/`位置对照、±.15等价判定与14型表 |
| T5 strict | `run_t5.py --phase strict` | 同625系统、旧分折、两权重及三验证的配对模型预测 |
| T5 full | `run_t5.py --phase full` | `results/t5/`全部规格、地域校准、sandwich与VB诊断 |
| T5 verify | `verify_t5_outputs.py` | 从已导出值独立重算loss、180区间、地域AUC及协方差门 |
| T2 compare | `run_t2.py --phase compare` | 同系统、同折、同评分单位的模型比较 |
| T6 feasibility | `domain_feasibility.py` | 原类别覆盖、词形及来源可行性 |
| T6 association | `cross_domain.py --phase all` | 冻结操作化对应的跨域关联 |
| T7 | `tree_feasibility.py` | `results/t7/`固定分类树覆盖及状态稀疏性；本轮不拟合Mk |
| T8 | `summarize.py` | 正式汇总文件；只读取已生成的结果 |

T2数值精化仅按单独保存的`docs/numerical_refinement_v3.md`执行同一求解器的更严停止精度；原未达梯度门的尝试和诊断保留。原分析计划不覆盖、不回写为事先未知结果。

可用`make list`列出确切命令。中断后，确认上游输出及SHA完整，再限定执行区间：

```bash
.venv/bin/python analysis/v3/run_all.py --from t5_strict --through t2_compare
```

区间运行不会宣称重新完成未执行的上游步骤。`make documents`单独导出／核查正式文稿；它不属于干净数值复现所需的分析步骤，也不重复拟合。

## 独立环境实际复现

下面是一条创建隔离环境、复制源码和固定输入、移除副本内全部已有新结果、实际运行`make all`与`make check`、再比较输出的命令：

```bash
python analysis/v3/clean_reproduce.py --workspace /tmp/kinship-v3-clean
```

该建环境入口只导入Python标准库，宿主无须预装numpy或pandas。统计比较也由新venv的解释器执行；不依靠宿主包完成Parquet读取。

目录须在本仓库外，源码快照目录尚不存在。它使用有独立文件的本地Git克隆，再覆盖当前工作树内容；因此尚未提交的新脚本也在快照内。`clean_venv`明确关闭`system-site-packages`，用固定依赖实际安装并执行`pip check`。原结果单独复制为只读比较参考，复现仓库的`results/`先完全移除，不链接或共享原结果目录。快照前后另核查源码／固定输入SHA，复制期间变化则停止。

全部证据留在该临时目录：`install.log`、`pip_freeze.txt`、`pip_check.log`、`snapshot_manifest.json`、`make_all.log`、`make_check.log`、`comparison.json/.md`和副本内逐阶段日志。关键日志另复制到主仓库`results/reproducibility/clean_run_logs/`，安装预检日志在`environment_install_logs/`，无需依赖临时目录永久保留。只测试依赖安装而不锁定尚在修改的源码时，可先加`--prepare-only`，它不会标记完整复现通过。

已有独立运行目录可再次只读核查：

```bash
make compare REPLICA=/tmp/kinship-v3-clean/repo
```

比较器逐项解析JSON、JSONL、CSV（含gzip）和Parquet，不以压缩包或图像字节相同代替统计复现。整数计数／编号精确一致；浮点默认绝对与相对容差均为`1e-8`。行序和列序亦需一致。运行时间、运行commit、解释器路径和派生SHA等元数据差异单列保留；实际源码与固定数据SHA仍独立严格一致。缺文件、多文件或缺阶段均不能通过。图像与报告文本的字体、日期或压缩字节差异不参与数值判定，图表含义由其数据表核对。

首次失败运行的`initial_solver/archive_manifest.json`为手工历史清单，另列来源而不要求当前CLI伪造重生成。原始统计量仍与planned重算逐项比。新版为planned诊断附加的`ftol=1e-12`、`gtol=1e-8`、`solver_profile=planned`以及汇总完整性说明单列并核对预期值，既不回填旧归档，也不把新增字段当作结果变化。T0保护清单长度随新增固定树文件变化，也仅作为执行元数据；“旧文件是否改变”和实际文件SHA继续严格核查。

## 解释范围

固定折外预测的5000次整谱系重抽只包含现有预测分数的不确定性，不含重训或重新划折；系数重拟合与预测检验分别保存。VB未满足收敛门时保留诊断并排除其推断，不用可选近似产生确认结论。T7只有分类拓扑和人为单位枝长，本轮明确不拟合Mk。测量定义、集合相等／连通分量与D1共享关系、八位置位序见`docs/cell_coding.md`；共同接口见`common.py`。
