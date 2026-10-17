"""第三版完整分析入口；按依赖顺序执行，任何未就绪或失败均停止。"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

from common import ROOT, RESULTS, SEED, git_commit, log_run, save_json, sha256, utc_now


@dataclass(frozen=True)
class Stage:
    name: str
    script: str
    args: tuple[str, ...] = ()
    description: str = ""


STAGES = (
    Stage("t0", "reproduce_baseline.py", description="从原始字段重算冻结基线"),
    Stage("t1", "build_t1.py", description="4140划分、三种系统映射与基础测试"),
    Stage("t2_initial_cv", "run_t2.py", ("--phase", "cv", "--sample", "strict", "--weighting", "family",
          "--validation", "family", "--solver-profile", "planned"), "保留原求解器主条件交叉验证的首次失败诊断"),
    Stage("t2_initial_full", "run_t2.py", ("--phase", "full", "--sample", "strict", "--weighting", "family",
          "--solver-profile", "planned"), "保留原求解器主条件全样本结果，不强制失败系数重抽"),
    Stage("t2_cv", "run_t2.py", ("--phase", "cv", "--solver-profile", "refined"), "精确归一化模型的全部交叉验证"),
    Stage("t2_full", "run_t2.py", ("--phase", "full", "--solver-profile", "refined"), "全样本估计、预测检验与系数重抽"),
    Stage("t3", "basis_enrichment.py", description="127候选特征、描述成本及形状参照"),
    Stage("t4", "position_tests.py", description="位置对照、等价判定及14型表"),
    Stage("t5_strict", "run_t5.py", ("--phase", "strict"), "T2配对比较需要的严格样本基准"),
    Stage("t5_full", "run_t5.py", ("--phase", "full"), "全部配对规格、地域校准与依赖敏感性"),
    Stage("t5_verify", "verify_t5_outputs.py", description="独立重算T5导出值与全部180区间"),
    Stage("t2_compare", "run_t2.py", ("--phase", "compare", "--solver-profile", "refined"), "划分模型与配对模型的同系统比较"),
    Stage("t6_feasibility", "domain_feasibility.py", description="按固定原始类别核查跨域覆盖"),
    Stage("t6", "cross_domain.py", ("--phase", "all"), "跨域补充分析或明确的可行性结论"),
    Stage("t7", "tree_feasibility.py", description="固定分类树的谱系分析可行性，不拟合Mk"),
    Stage("t8", "summarize.py", description="汇总已完成分析，不重新拟合"),
)


def selected_stages(first=None, last=None):
    names = [stage.name for stage in STAGES]
    start = names.index(first) if first else 0
    stop = names.index(last) + 1 if last else len(STAGES)
    if start >= stop:
        raise ValueError("起始阶段必须位于终止阶段之前或与其相同。")
    return STAGES[start:stop]


def child_environment():
    env = os.environ.copy()
    for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
                     "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        env[variable] = "1"
    env.update(PYTHONHASHSEED=str(SEED), MPLBACKEND="Agg", PYTHONDONTWRITEBYTECODE="1")
    return env


def environment_info():
    packages = ("numpy", "pandas", "scipy", "scikit-learn", "matplotlib", "statsmodels",
                "patsy", "pyarrow", "python-docx")
    versions = {}
    for name in packages:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return {"python": sys.version, "executable": sys.executable, "platform": platform.platform(),
            "packages": versions, "threads": 1, "PYTHONHASHSEED": SEED}


def run_stage(stage, logdir, env):
    script = ROOT / "analysis/v3" / stage.script
    command = [sys.executable, str(script.relative_to(ROOT)), *stage.args]
    record = {"stage": stage.name, "description": stage.description, "command": command,
              "script_sha256": sha256(script), "started_utc": utc_now(),
              "log": str((logdir / (stage.name + ".log")).relative_to(ROOT))
                     if logdir.is_relative_to(ROOT) else str(logdir / (stage.name + ".log"))}
    print(f"[{stage.name}] {stage.description}", flush=True)
    log_run("T8_stage", {"stage":stage.name,"command":command}, {}, "started")
    started = time.monotonic()
    with (logdir / (stage.name + ".log")).open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()
        process = subprocess.run(command, cwd=ROOT, env=env, stdout=handle,
                                 stderr=subprocess.STDOUT, text=True, check=False)
    record.update(finished_utc=utc_now(), elapsed_seconds=time.monotonic()-started,
                  returncode=process.returncode, passed=process.returncode == 0)
    log_run("T8_stage", {"stage":stage.name,"command":command},
            {"passed":record["passed"],"returncode":record["returncode"],"log":record["log"]},
            "completed" if record["passed"] else "failed")
    print(f"[{stage.name}] {'通过' if record['passed'] else '失败'}；日志 {record['log']}", flush=True)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="仅列出阶段及命令，不计算")
    parser.add_argument("--from", dest="first", choices=[s.name for s in STAGES])
    parser.add_argument("--through", dest="last", choices=[s.name for s in STAGES])
    parser.add_argument("--logdir", type=Path, default=RESULTS / "reproducibility/pipeline_logs")
    args = parser.parse_args()
    stages = selected_stages(args.first, args.last)
    if args.list:
        for stage in stages:
            print(stage.name + ": " + " ".join(["python", "analysis/v3/" + stage.script, *stage.args]))
        return
    missing = [stage.script for stage in stages if not (ROOT / "analysis/v3" / stage.script).is_file()]
    if missing:
        raise SystemExit("分析入口尚未齐备，未启动任何阶段：" + ", ".join(missing))
    logdir = args.logdir.resolve()
    logdir.mkdir(parents=True, exist_ok=True)
    manifest = {"task": "T8_pipeline", "started_utc": utc_now(), "commit": git_commit(),
                "seed": SEED, "bootstrap_replicates": 5000, "environment": environment_info(),
                "selected_stages": [stage.name for stage in stages], "stages": [], "passed": False}
    path = logdir.parent / "pipeline_manifest.json"
    log_run("T8_pipeline", {"stages": manifest["selected_stages"]}, {}, "started")
    env = child_environment()
    try:
        for stage in stages:
            result = run_stage(stage, logdir, env)
            manifest["stages"].append(result)
            save_json(path, manifest)
            if not result["passed"]:
                raise RuntimeError(f"阶段{stage.name}失败；查看{result['log']}。")
        manifest["passed"] = True
    except Exception as exc:
        manifest["error"] = str(exc)
        raise
    finally:
        manifest["finished_utc"] = utc_now()
        save_json(path, manifest)
        log_run("T8_pipeline", {"stages": manifest["selected_stages"]},
                {"passed": manifest["passed"], "manifest": str(path)},
                "completed" if manifest["passed"] else "failed")


if __name__ == "__main__":
    main()
