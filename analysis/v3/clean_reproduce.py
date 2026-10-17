"""在独立源码副本和无system-site-packages的venv中实际执行完整复现。"""
from __future__ import annotations

import argparse
import ast
import csv
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import venv

from verify_reproduction import digest, source_files

# Bootstrap must run on a standard-library-only Python before installing numpy/pandas.
ROOT=Path(__file__).resolve().parents[2]
RESULTS=ROOT/'results'


def utc_now():return dt.datetime.now(dt.timezone.utc).isoformat()


def save_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def log_run(task,spec,metrics,status):
    path=RESULTS/'run_log.csv';path.parent.mkdir(parents=True,exist_ok=True)
    fields=['time','task','spec','metrics','commit']
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    with path.open('a+',newline='',encoding='utf-8') as handle:
        fcntl.flock(handle.fileno(),fcntl.LOCK_EX)
        handle.seek(0);header=handle.readline().strip()
        if header and next(csv.reader([header]))!=fields:raise RuntimeError('运行日志列名不匹配。')
        handle.seek(0,os.SEEK_END);writer=csv.DictWriter(handle,fieldnames=fields)
        if not header:writer.writeheader()
        writer.writerow({'time':utc_now(),'task':task,
          'spec':json.dumps({**spec,'status':status},ensure_ascii=False),
          'metrics':json.dumps(metrics,ensure_ascii=False),'commit':commit})
        handle.flush();os.fsync(handle.fileno());fcntl.flock(handle.fileno(),fcntl.LOCK_UN)


def child_environment():
    env=os.environ.copy()
    for key in ('PYTHONPATH','PYTHONHOME'):env.pop(key,None)
    for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
        env[key]='1'
    env.update(PYTHONHASHSEED='20261016',MPLBACKEND='Agg',PYTHONDONTWRITEBYTECODE='1')
    return env


def pipeline_scripts():
    """Read the single authoritative literal stage list without importing scientific packages."""
    tree=ast.parse((ROOT/'analysis/v3/run_all.py').read_text())
    assignment=next(node for node in tree.body if isinstance(node,ast.Assign)
                    and any(isinstance(target,ast.Name) and target.id=='STAGES' for target in node.targets))
    if not isinstance(assignment.value,ast.Tuple):raise RuntimeError('STAGES必须为显式元组。')
    scripts=[]
    for entry in assignment.value.elts:
        if not isinstance(entry,ast.Call) or not isinstance(entry.func,ast.Name) or entry.func.id!='Stage':
            raise RuntimeError('无法从显式Stage读取流水线。')
        script=ast.literal_eval(entry.args[1])
        if not isinstance(script,str):raise RuntimeError('Stage脚本名必须是字面字符串。')
        scripts.append(script)
    return scripts


def command_run(command, cwd, logfile, env=None, allow_failure=False):
    started = time.monotonic()
    print("执行：" + " ".join(map(str, command)), flush=True)
    with Path(logfile).open("w", encoding="utf-8") as handle:
        handle.write(json.dumps({"command": list(map(str, command)), "cwd": str(cwd),
                                 "started_utc": utc_now()}, ensure_ascii=False)+"\n")
        handle.flush()
        run = subprocess.run(command, cwd=cwd, stdout=handle, stderr=subprocess.STDOUT,
                             text=True, env=env, check=False)
    record = {"command": list(map(str, command)), "cwd": str(cwd), "log": str(logfile),
              "returncode": run.returncode, "elapsed_seconds": time.monotonic()-started}
    if run.returncode and not allow_failure:
        raise RuntimeError("命令失败；查看日志："+str(logfile))
    return record


def install_environment(workspace):
    environment = workspace / "clean_venv"
    if not environment.exists():
        venv.EnvBuilder(with_pip=True, system_site_packages=False).create(environment)
    config = (environment / "pyvenv.cfg").read_text().lower()
    if "include-system-site-packages = false" not in config:
        raise RuntimeError("现有venv并非隔离环境，拒绝继续。")
    python = environment / "bin/python"
    command_run([str(python), "-m", "pip", "install", "-r", str(ROOT / "analysis/v3/requirements.txt")],
                ROOT, workspace / "install.log", child_environment())
    freeze = subprocess.check_output([str(python), "-m", "pip", "freeze"], text=True)
    (workspace / "pip_freeze.txt").write_text(freeze)
    command_run([str(python), "-m", "pip", "check"], ROOT, workspace / "pip_check.log")
    expected={line.split('==',1)[0].lower().replace('_','-'):line.split('==',1)[1]
              for raw in (ROOT/'analysis/v3/environment.lock.txt').read_text().splitlines()
              if (line:=raw.strip()) and not line.startswith('#')}
    installed=json.loads(subprocess.check_output([str(python),'-m','pip','list','--format=json'],text=True))
    actual={item['name'].lower().replace('_','-'):item['version'] for item in installed}
    mismatches={name:{'expected':version,'installed':actual.get(name)}
                for name,version in expected.items() if actual.get(name)!=version}
    if mismatches:raise RuntimeError('安装版本未满足固定环境：'+json.dumps(mismatches,ensure_ascii=False))
    return python


def overlay_snapshot(destination):
    def ignore(directory, names):
        return [name for name in names if name in {".git", ".cache", "__pycache__", ".venv", "venv", "results"}
                or name.endswith((".pyc", ".pyo"))]
    shutil.copytree(ROOT, destination, dirs_exist_ok=True, ignore=ignore)


def prepare_snapshots(workspace):
    replica, reference = workspace / "repo", workspace / "reference"
    if replica.exists() or reference.exists():
        raise RuntimeError("workspace已有源码快照；为避免覆盖证据，请选择新的空workspace。")
    before = source_files(ROOT)
    command_run(["git", "clone", "--no-hardlinks", "--local", str(ROOT), str(replica)],
                workspace, workspace / "clone.log")
    overlay_snapshot(replica)
    if (replica / "results").exists():
        shutil.rmtree(replica / "results")
    (replica / "results").mkdir()
    reference.mkdir()
    # Statistical reference is copied, never symlinked to the actively edited repository.
    shutil.copytree(ROOT / "results", reference / "results", ignore=shutil.ignore_patterns("reproducibility"))
    for relative in before:
        path = reference / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, path)
    after = source_files(ROOT)
    if before != after:
        raise RuntimeError("复制期间源码/固定输入发生变化；本次快照未锁定，请在源码稳定后使用新workspace。")
    if before != source_files(replica) or before != source_files(reference):
        raise RuntimeError("独立副本或参考快照与源文件SHA不一致。")
    save_json(workspace / "snapshot_manifest.json", {"source": str(ROOT), "created_utc": utc_now(),
              "files": before, "results_copied": "数值参考单独保存；待运行目录results已完全移除"})
    return replica, reference


def archive_logs(workspace, target):
    """使关键日志随仓库交付，而非仅依赖临时目录仍然存在。"""
    target.mkdir(parents=True, exist_ok=True)
    names=("install.log", "pip_freeze.txt", "pip_check.log", "clone.log", "snapshot_manifest.json",
           "make_all.log", "make_check.log", "comparison.log", "comparison.json", "comparison.md")
    for name in names:
        if (workspace / name).is_file():shutil.copy2(workspace / name, target / name)
    pipeline=workspace / "repo/results/reproducibility"
    if (pipeline / "pipeline_manifest.json").is_file():
        shutil.copy2(pipeline / "pipeline_manifest.json", target / "pipeline_manifest.json")
    if (pipeline / "pipeline_logs").is_dir():
        shutil.copytree(pipeline / "pipeline_logs", target / "pipeline_logs",dirs_exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, help="空目录，或只含--prepare-only创建的clean_venv")
    parser.add_argument("--prepare-only", action="store_true", help="仅实测安装隔离环境；不锁定尚在修改的源码")
    args = parser.parse_args()
    workspace = args.workspace.resolve() if args.workspace else Path(tempfile.mkdtemp(prefix="kinship-v3-clean-"))
    if workspace == ROOT or workspace.is_relative_to(ROOT):
        raise SystemExit("独立复现目录须位于项目仓库之外。")
    workspace.mkdir(parents=True, exist_ok=True)
    record = {"task": "T8_clean_reproduction", "workspace": str(workspace), "started_utc": utc_now(),
              "prepare_only": args.prepare_only, "passed": False, "full_reproduction_passed":False}
    report = RESULTS / "reproducibility/clean_environment.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    log_run("T8_clean_reproduction", {"workspace": str(workspace), "prepare_only": args.prepare_only}, {}, "started")
    try:
        python = install_environment(workspace)
        record.update(venv_python=str(python), system_site_packages=False,
                      pip_freeze=(workspace / "pip_freeze.txt").read_text(),
                      requirements_sha256=digest(ROOT / "analysis/v3/requirements.txt"),
                      constraints_sha256=digest(ROOT / "analysis/v3/environment.lock.txt"))
        if args.prepare_only:
            record.update(passed=True, status="仅环境安装通过；尚未执行完整分析，不能称完整复现通过")
            return
        missing = [script for script in pipeline_scripts() if not (ROOT / "analysis/v3" / script).is_file()]
        if missing:
            raise RuntimeError("入口尚未齐备，未复制或执行分析："+", ".join(missing))
        replica, reference = prepare_snapshots(workspace)
        record["snapshot_manifest"] = str(workspace / "snapshot_manifest.json")
        env = child_environment()
        record["analysis_run"] = command_run(["make", "all", "PYTHON="+str(python)], replica,
                                             workspace / "make_all.log", env)
        record["tests_run"] = command_run(["make", "check", "PYTHON="+str(python)], replica,
                                          workspace / "make_check.log", env)
        record['comparison_run']=command_run([str(python),str(replica/'analysis/v3/verify_reproduction.py'),
          '--reference',str(reference),'--replica',str(replica),'--output',str(workspace/'comparison.json')],
          replica,workspace/'comparison.log',env,allow_failure=True)
        result=json.loads((workspace/'comparison.json').read_text())
        for name in ('comparison.json','comparison.md'):shutil.copy2(workspace/name,report.parent/name)
        record.update(passed=result["passed"], full_reproduction_passed=result["passed"],
                      status="完整实际复现通过" if result["passed"] else "统计核查未通过",
                      comparison_json=str(workspace / "comparison.json"),
                      files_checked=result["files_checked"], statistical_differences_count=result["statistical_differences_count"],
                      max_absolute_difference=result["max_absolute_difference"])
        if not result["passed"]:
            raise RuntimeError("完整运行结束但复现核查未通过；见comparison.json，未修改原值。")
    except Exception as exc:
        record["error"] = str(exc)
        raise
    finally:
        record["finished_utc"] = utc_now()
        archive=report.parent / ("environment_install_logs" if args.prepare_only else "clean_run_logs")
        archive_logs(workspace,archive)
        record["archived_logs"]=str(archive.relative_to(ROOT))
        save_json(report, record)
        save_json(workspace / "clean_environment.json", record)
        log_run("T8_clean_reproduction", {"workspace": str(workspace), "prepare_only": args.prepare_only},
                {"passed": record["passed"], "report": str(report), "status": record.get("status"), "error": record.get("error")},
                "completed" if record["passed"] else "failed")
        print(json.dumps({"workspace": str(workspace), "passed": record["passed"], "prepare_only": args.prepare_only,
                          "report": str(report)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
