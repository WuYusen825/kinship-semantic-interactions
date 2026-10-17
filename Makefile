PYTHON ?= python

.PHONY: all list check documents compare clean-reproduce t6-feasibility

# 全部实际分析；保留5000次重抽，不调用旧的写回式S1/S2入口。
all:
	$(PYTHON) analysis/v3/run_all.py

list:
	$(PYTHON) analysis/v3/run_all.py --list

check:
	OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 $(PYTHON) -m unittest discover -s tests -p 'test_v3_*.py' -v

# 文档导出入口由正式稿维护者提供，缺失时明确失败。
documents:
	$(PYTHON) analysis/v3/export_documents.py

# 例：make compare REPLICA=/tmp/kinship-v3-clean/repo
compare:
	@test -n "$(REPLICA)" || (echo '请设置REPLICA为独立复现仓库路径。'; exit 2)
	$(PYTHON) analysis/v3/verify_reproduction.py --reference . --replica "$(REPLICA)"

# 创建独立副本及真正隔离的venv，然后执行make all与数值比较。
clean-reproduce:
	$(PYTHON) analysis/v3/clean_reproduce.py

t6-feasibility:
	$(PYTHON) analysis/v3/domain_feasibility.py
