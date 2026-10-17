"""只读比较两套第三版结果；统计差异与运行元数据差异分开记录。"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path
import re


NUMERIC = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
INTEGER = re.compile(r"^[+-]?\d+$")
METADATA_KEYS = {
    "started_utc", "finished_utc", "completed_utc", "created_utc", "generated_utc",
    "started_at", "completed_at", "created_at", "finished_at", "generated_at", "timestamp", "time",
    "commit", "git_commit", "run_commit", "plan_commit_time",
    "elapsed_seconds", "elapsed_s", "duration_seconds", "duration", "seconds", "wall_time",
    "script_sha256", "runner_sha256", "model_sha256", "pair_models_sha256", "S2_fitter_sha256",
    "baseline_result_sha256", "source_sha256", "output_sha256", "input_sha256", "files",
    "tests_command", "executable", "mtime_ns",
}
RESULT_DIRS = ("baseline", "t1", "t2", "t3", "t4", "t5", "t6", "t7")
NUMERIC_SUFFIXES = (".json", ".csv", ".csv.gz", ".jsonl", ".jsonl.gz", ".parquet")
HISTORICAL_ONLY_FILES = {"results/t2/initial_solver/archive_manifest.json"}


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def statistical_files(root):
    base = Path(root) / "results"
    paths = []
    for name in RESULT_DIRS:
        directory = base / name
        if directory.exists():
            paths.extend(p for p in directory.rglob("*") if p.is_file()
                         and p.name.endswith(NUMERIC_SUFFIXES))
    if (base / "summary.json").is_file():
        paths.append(base / "summary.json")
    return {str(p.relative_to(root)): p for p in paths if str(p.relative_to(root)) not in HISTORICAL_ONLY_FILES}


def source_files(root):
    """核对实际代码和固定输入；不以剔除元数据掩盖输入/实现变化。"""
    root = Path(root)
    result = {}
    for folder in ("analysis", "data", "tests"):
        for path in (root / folder).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                result[str(path.relative_to(root))] = digest(path)
    for name in ("Makefile", "docs/analysis_plan.md", "docs/analysis_plan_lock.json",
                 "docs/analysis_plan_addendum_v3.md", "docs/t6_operationalization.md",
                 "docs/t6_association_plan.md", "docs/numerical_refinement_v3.md"):
        if (root / name).is_file():
            result[name] = digest(root / name)
    return result


class Comparison:
    def __init__(self, atol=1e-8, rtol=1e-8):
        self.atol, self.rtol = atol, rtol
        self.checked = 0
        self.numeric_checked = 0
        self.metadata_fields = 0
        self.max_absolute_difference = 0.0
        self.max_difference_location = None
        self.differences = []
        self.metadata_differences = []
        self.total_differences = 0

    def difference(self, location, left, right, kind="value"):
        self.total_differences += 1
        if len(self.differences) < 50:
            self.differences.append({"location": location, "reference": left, "replica": right,
                                     "kind": kind})

    def metadata(self, location, left, right):
        self.metadata_fields += 1
        if left != right:
            # Preserve the exact values in the output report; never call them statistical failures.
            self.metadata_differences.append({"location": location, "reference": left, "replica": right})

    def scalar(self, left, right, location):
        self.checked += 1
        if isinstance(left,bool) != isinstance(right,bool):
            self.difference(location,left,right,"boolean_type")
            return
        if left == right:
            if isinstance(left, (int, float)) and not isinstance(left, bool):
                self.numeric_checked += 1
            return
        if isinstance(left, bool) or isinstance(right, bool):
            self.difference(location, left, right)
            return
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            self.numeric_checked += 1
            if math.isnan(left) and math.isnan(right):
                return
            if math.isfinite(left) and math.isfinite(right):
                delta = abs(left - right)
                if delta > self.max_absolute_difference:
                    self.max_absolute_difference, self.max_difference_location = delta, location
                # Integer counts, IDs and iteration counts are exact; only floating results use tolerance.
                if isinstance(left, int) and isinstance(right, int):
                    self.difference(location, left, right, "integer_exact")
                elif not math.isclose(left, right, abs_tol=self.atol, rel_tol=self.rtol):
                    self.difference(location, left, right, "float_tolerance")
                return
        self.difference(location, left, right)

    def object(self, left, right, location=""):
        if isinstance(left, dict) and isinstance(right, dict):
            for key in sorted(set(left) | set(right)):
                where = location + "/" + key
                historical_expected={'solver_profile':'planned','numerical_refinement':None,
                  'completeness':{'cv_settings':1,'expected_cv_settings':18,'full_settings':1,
                                  'expected_full_settings':6,'pair_comparison_completed':False}}
                if (location.startswith('results/t2/initial_solver/') and key in historical_expected
                        and (key not in left or key not in right)):
                    expected=historical_expected[key]
                    self.metadata(where,left.get(key),right.get(key))
                    if left.get(key,expected)!=expected or right.get(key,expected)!=expected:
                        self.difference(where,left.get(key),right.get(key),'historical_schema_expected_value')
                elif (location.startswith('results/t2/initial_solver/') and '/attempts/' in location
                        and key in {'ftol','gtol'} and (key not in left or key not in right)):
                    expected={'ftol':1e-12,'gtol':1e-8}[key]
                    self.metadata(where,left.get(key),right.get(key))
                    if left.get(key,expected)!=expected or right.get(key,expected)!=expected:
                        self.difference(where,left.get(key),right.get(key),'planned_solver_setting')
                elif key in METADATA_KEYS or key.endswith("_sha256") or (key == "file_count" and location.endswith("/source_protection")):
                    self.metadata(where, left.get(key), right.get(key))
                elif key not in left or key not in right:
                    self.difference(where, left.get(key), right.get(key), "missing_key")
                else:
                    self.object(left[key], right[key], where)
        elif isinstance(left, (tuple, list)) and isinstance(right, (tuple, list)):
            if len(left) != len(right):
                self.difference(location + "/length", len(left), len(right), "length")
            for index, (a, b) in enumerate(zip(left, right)):
                self.object(a, b, f"{location}/{index}")
        else:
            self.scalar(left, right, location)

    def csv_cell(self, left, right, location):
        if left == right:
            self.checked += 1
            if left and NUMERIC.fullmatch(left):
                self.numeric_checked += 1
            return
        if left is None or right is None:
            self.difference(location, left, right, "missing_cell")
        elif (INTEGER.fullmatch(left) and len(left.lstrip('+-'))>1 and left.lstrip('+-').startswith('0')) or \
             (INTEGER.fullmatch(right) and len(right.lstrip('+-'))>1 and right.lstrip('+-').startswith('0')):
            self.scalar(left,right,location)
        elif NUMERIC.fullmatch(left) and NUMERIC.fullmatch(right):
            a = int(left) if INTEGER.fullmatch(left) else float(left)
            b = int(right) if INTEGER.fullmatch(right) else float(right)
            self.scalar(a, b, location)
        elif left in ("nan", "NaN") and right in ("nan", "NaN"):
            self.checked += 1
        elif left[:1] in ("[", "{") and right[:1] in ("[", "{"):
            try:
                self.object(json.loads(left), json.loads(right), location)
            except (ValueError, TypeError):
                self.scalar(left, right, location)
        else:
            self.scalar(left, right, location)

    def file(self, left, right, relative):
        before = self.total_differences
        opener = gzip.open if left.name.endswith(".gz") else open
        if left.name.endswith(".json"):
            self.object(json.loads(left.read_text()), json.loads(right.read_text()), relative)
        elif left.name.endswith((".jsonl", ".jsonl.gz")):
            with opener(left, "rt", encoding="utf-8") as a, opener(right, "rt", encoding="utf-8") as b:
                for index, pair in enumerate(itertools.zip_longest(a, b)):
                    x, y = pair
                    if x is None or y is None:
                        self.difference(relative + f"/line{index+1}", x, y, "line_count")
                    else:
                        self.object(json.loads(x), json.loads(y), relative + f"/line{index+1}")
        elif left.name.endswith(".parquet"):
            import pandas as pd
            # JSON conversion retains nested array values and finite numbers without numpy scalar types.
            a, b = pd.read_parquet(left), pd.read_parquet(right)
            self.object(list(a.columns), list(b.columns), relative + "/columns")
            self.object(json.loads(a.to_json(orient="values", double_precision=15)),
                        json.loads(b.to_json(orient="values", double_precision=15)), relative)
        else:
            with opener(left, "rt", encoding="utf-8", newline="") as a, opener(right, "rt", encoding="utf-8", newline="") as b:
                ca, cb = csv.reader(a), csv.reader(b)
                for index, pair in enumerate(itertools.zip_longest(ca, cb)):
                    x, y = pair
                    if x is None or y is None:
                        self.difference(relative + f"/row{index+1}", x, y, "row_count")
                        continue
                    if len(x) != len(y):
                        self.difference(relative + f"/row{index+1}/columns", len(x), len(y), "column_count")
                    for col, (first, second) in enumerate(zip(x, y)):
                        self.csv_cell(first, second, f"{relative}/row{index+1}/col{col+1}")
        return self.total_differences == before


def compare_roots(reference, replica, atol=1e-8, rtol=1e-8, require_all=True):
    reference, replica = Path(reference).resolve(), Path(replica).resolve()
    left, right = statistical_files(reference), statistical_files(replica)
    comparator = Comparison(atol, rtol)
    missing, extra = sorted(set(left)-set(right)), sorted(set(right)-set(left))
    source_a, source_b = source_files(reference), source_files(replica)
    source_differences = [{"path": key, "reference": source_a.get(key), "replica": source_b.get(key)}
                          for key in sorted(set(source_a) | set(source_b))
                          if source_a.get(key) != source_b.get(key)]
    absent_stages = [name for name in RESULT_DIRS if not any(p.startswith("results/"+name+"/") for p in right)] if require_all else []
    files = []
    for key in sorted(set(left) & set(right)):
        passed = comparator.file(left[key], right[key], key)
        files.append({"path": key, "passed": passed, "byte_identical": digest(left[key]) == digest(right[key])})
    historical=[{'path':name,'reference_sha256':digest(reference/name) if (reference/name).is_file() else None,
                 'replica_sha256':digest(replica/name) if (replica/name).is_file() else None,
                 'reason':'历史手工归档清单；由当时原始运行保留，不由当前CLI重生成；不含待重算统计量'}
                for name in sorted(HISTORICAL_ONLY_FILES)]
    return {"passed": not (missing or extra or source_differences or absent_stages or comparator.total_differences),
            "reference": str(reference), "replica": str(replica),
            "float_absolute_tolerance": atol, "float_relative_tolerance": rtol,
            "integer_rule": "整数计数及编号精确一致", "files_checked": len(files), "files": files,
            "missing_statistical_files": missing, "extra_statistical_files": extra,
            "absent_required_stages": absent_stages, "source_files_checked": len(source_a),
            "source_differences": source_differences, "values_checked": comparator.checked,
            "numeric_values_checked": comparator.numeric_checked,
            "max_absolute_difference": comparator.max_absolute_difference,
            "max_difference_location": comparator.max_difference_location,
            "statistical_differences_count": comparator.total_differences,
            "statistical_differences_first50": comparator.differences,
            "metadata_fields_separated": comparator.metadata_fields,
            "metadata_differences": comparator.metadata_differences,
            "historical_provenance_files":historical,
            "metadata_policy": sorted(METADATA_KEYS)+["*/source_protection/file_count（执行时保护清单长度；changed_files与unchanged仍严格比较）", "*_sha256",
                "initial_solver/**/attempts新增ftol/gtol字段单列，并分别严格核对1e-12/1e-8；原始其余诊断不排除",
                "initial_solver新增solver_profile/planned、numerical_refinement/null及completeness(1CV/1full/无compare)单列并严格核对固定值"],
            "scope": "逐文件解析JSON/JSONL/CSV/Parquet；保留行序；数值比较不使用图像二进制或报告文本的字节差异。代码和固定数据SHA另作严格核对。"}


def write_report(result, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+"\n")
    lines = ["# 独立环境复现核查", "", "判定：" + ("通过" if result["passed"] else "未通过") + "。", "",
             f"共核对{result['files_checked']}份统计文件、{result['numeric_values_checked']}个数值；最大绝对差{result['max_absolute_difference']:.12g}。",
             f"浮点绝对/相对容差均为{result['float_absolute_tolerance']:g}；整数精确一致。实现与固定输入另核对{result['source_files_checked']}份文件的SHA。", "",
             f"统计差异{result['statistical_differences_count']}项；源码/固定输入差异{len(result['source_differences'])}项；缺文件{len(result['missing_statistical_files'])}份，额外文件{len(result['extra_statistical_files'])}份。",
             f"时间、运行commit、解释器路径和派生文件SHA等元数据差异{len(result['metadata_differences'])}项单列在JSON，不改写统计值或原文件。", "",
             result["scope"], "", f"参考目录：`{result['reference']}`", f"独立目录：`{result['replica']}`", ""]
    if not result["passed"]:
        lines += ["首次差异：", "", "```json", json.dumps({key: result[key] for key in
                  ("absent_required_stages", "missing_statistical_files", "extra_statistical_files", "source_differences", "statistical_differences_first50")},
                   ensure_ascii=False, indent=2), "```", ""]
    output.with_suffix(".md").write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--replica", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("results/reproducibility/comparison.json"))
    parser.add_argument("--atol", type=float, default=1e-8)
    parser.add_argument("--rtol", type=float, default=1e-8)
    parser.add_argument("--allow-partial", action="store_true", help="仅供开发核查，不作为完整复现通过标记")
    args = parser.parse_args()
    result = compare_roots(args.reference, args.replica, args.atol, args.rtol, not args.allow_partial)
    write_report(result, args.output)
    print(json.dumps({key: result[key] for key in ("passed", "files_checked", "statistical_differences_count", "max_absolute_difference")}, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
