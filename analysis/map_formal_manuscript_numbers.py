#!/usr/bin/env python3
"""正式稿独立数字核验：只提议精确表格行迁移，不搜索同值或自动豁免。

  python analysis/map_formal_manuscript_numbers.py --prepare
  python analysis/map_formal_manuscript_numbers.py --propose-tables
  python analysis/map_formal_manuscript_numbers.py --apply-approved
  python analysis/map_formal_manuscript_numbers.py --check

迁移审批须逐处列出新旧occurrence_id及表头/指标语义复核说明。改写段落及
变更表格行均保持unresolved，另行指定结果pointer。旧v2及781处报告只读。
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
import tempfile

import check_manuscript_numbers as checker


ROOT = Path(__file__).resolve().parents[1]
OLD_MD = "outputs/forum/论坛稿_v2.md"
OLD_CLAIMS = "notes/manuscript_number_claims.json"
OLD_REPORT = "notes/manuscript_number_check.json"
FORMAL_MD = "outputs/论文_中文正式稿.md"
FORMAL_CLAIMS = "notes/formal_manuscript_number_claims.json"
FORMAL_REPORT = "notes/formal_manuscript_number_check.json"
PROPOSALS = "notes/formal_number_table_proposals.json"
APPROVALS = "notes/formal_number_migration_approvals.json"
BASELINE = "notes/formal_number_migration_baseline.json"
PROTECTED = {OLD_MD, OLD_CLAIMS, OLD_REPORT}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf8"))


def write_json(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


def file_hash(path: Path) -> str:
    return checker.sha256(path.read_bytes())


def guard_output_paths(root: Path, paths: list[Path]) -> None:
    """在任何写入发生前解析路径别名，防止覆盖只读的旧稿快照。"""
    protected = {(root / name).resolve() for name in PROTECTED}
    for path in paths:
        resolved = path.resolve()
        same_file = path.exists() and any(old.exists() and path.samefile(old) for old in protected)
        if resolved in protected or same_file:
            raise ValueError("正式稿工具不得覆盖旧稿或旧核验记录（包括路径别名）")
        if not resolved.is_relative_to(root.resolve()):
            raise ValueError("正式稿核验输出必须留在仓库内")


def table_contexts(text: str) -> dict[int, dict]:
    """关联物理行与完整表格；表头只展示，不替代人工语义复核。"""
    lines = text.splitlines()
    result: dict[int, dict] = {}
    index = 0
    while index < len(lines):
        if not lines[index].lstrip().startswith("|"):
            index += 1
            continue
        start = index
        while index < len(lines) and lines[index].lstrip().startswith("|"):
            index += 1
        block = lines[start:index]
        if len(block) < 2 or not re.fullmatch(r"[|:\-\s]+", block[1]):
            continue
        caption = next((line for line in reversed(lines[:start]) if line.strip()), "")
        context = {
            "start_line": start + 1,
            "header": block[0],
            "separator": block[1],
            "caption": caption,
            "table_sha256": checker.sha256("\n".join(block).encode()),
        }
        for line_number in range(start + 1, index + 1):
            result[line_number] = context
    return result


def propose_tables(old_text: str, old_mapping: dict, new_text: str,
                   new_mapping: dict) -> list[dict]:
    old_tables, new_tables = table_contexts(old_text), table_contexts(new_text)
    old_by_key: dict[tuple, list] = {}
    for claim in old_mapping.get("claims", []):
        anchor = claim.get("anchor", {})
        if anchor.get("line") not in old_tables or claim.get("kind") not in {"result", "whitelist"}:
            continue
        key = (anchor.get("line_text"), anchor.get("numeric_index_on_line"), anchor.get("token"))
        old_by_key.setdefault(key, []).append(claim)
    proposals = []
    for claim in new_mapping.get("claims", []):
        anchor = claim.get("anchor", {})
        if anchor.get("line") not in new_tables or claim.get("kind") != "unresolved":
            continue
        key = (anchor.get("line_text"), anchor.get("numeric_index_on_line"), anchor.get("token"))
        candidates = old_by_key.get(key, [])
        if len(candidates) != 1:
            continue
        old = candidates[0]
        proposals.append({
            "source_occurrence_id": old["occurrence_id"],
            "target_occurrence_id": claim["occurrence_id"],
            "token": anchor["token"],
            "exact_row": anchor["line_text"],
            "source_label": old.get("label"),
            "source_kind": old.get("kind"),
            "source_table": old_tables[old["anchor"]["line"]],
            "target_table": new_tables[anchor["line"]],
            "status": "requires_explicit_context_review",
        })
    return proposals


def apply_approved(old_text: str, old_mapping: dict, new_text: str,
                   new_mapping: dict, approval: dict) -> dict:
    if approval.get("source_manuscript_sha256") != checker.sha256(old_text.encode()):
        raise ValueError("迁移审批中的旧稿SHA不匹配")
    if approval.get("target_manuscript_sha256") != checker.sha256(new_text.encode()):
        raise ValueError("迁移审批中的正式稿SHA不匹配；须重新复核")
    proposals = {
        (p["source_occurrence_id"], p["target_occurrence_id"]): p
        for p in propose_tables(old_text, old_mapping, new_text, new_mapping)
    }
    source_claims = {c["occurrence_id"]: c for c in old_mapping["claims"]}
    result = deepcopy(new_mapping)
    target_claims = {c["occurrence_id"]: c for c in result["claims"]}
    seen = set()
    for item in approval.get("approved", []):
        key = (item.get("source_occurrence_id"), item.get("target_occurrence_id"))
        reason = item.get("context_verified_zh", "").strip()
        if key not in proposals or len(reason) < 12:
            raise ValueError("仅可批准精确表格候选，且须说明具体表头、指标及估计对象")
        if key[1] in seen:
            raise ValueError("同一正式稿数字重复批准")
        seen.add(key[1])
        target = target_claims[key[1]]
        migrated = deepcopy(source_claims[key[0]])
        migrated.update(occurrence_id=key[1], anchor=deepcopy(target["anchor"]))
        migrated["migration_review"] = {
            "source_manuscript": OLD_MD,
            "source_occurrence_id": key[0],
            "source_manuscript_sha256": approval["source_manuscript_sha256"],
            "target_manuscript_sha256": approval["target_manuscript_sha256"],
            "context_verified_zh": reason,
        }
        target.clear()
        target.update(migrated)
    result["approved_table_migrations"] = len(seen)
    return result


def synchronize_formal(manuscript: Path, previous: dict, root: Path) -> dict:
    mapping = checker.synchronize(manuscript, previous, root)
    current_sha = mapping.get("manuscript_sha256")
    invalidated = 0
    for claim in mapping["claims"]:
        review = claim.get("migration_review")
        if review and review.get("target_manuscript_sha256") != current_sha:
            # Even an unchanged numeric row can acquire a different meaning from an
            # edited table header. Approval is deliberately specific to one manuscript.
            anchor, ident = claim["anchor"], claim["occurrence_id"]
            claim.clear()
            claim.update(occurrence_id=ident, anchor=anchor, kind="unresolved", label="",
                         source=None, format=None,
                         invalidation_reason_zh="正式稿SHA已改变；旧表格迁移审批失效，须重新核对表头和指标。")
            invalidated += 1
    mapping["invalidated_table_migrations"] = invalidated
    return mapping


def guard_old_files(root: Path) -> dict:
    old_report = read_json(root / OLD_REPORT)
    old_claims = read_json(root / OLD_CLAIMS)
    old_sha = file_hash(root / OLD_MD)
    if not old_report.get("passed") or old_report.get("manuscript_sha256") != old_sha:
        raise ValueError("旧稿通过记录与旧稿实际SHA不一致")
    if old_claims.get("manuscript_sha256") != old_sha:
        raise ValueError("旧稿映射不是已核验的同一快照")
    current = {name: file_hash(root / name) for name in sorted(PROTECTED)}
    baseline_path = root / BASELINE
    if baseline_path.exists():
        baseline = read_json(baseline_path)
        if baseline.get("protected_sha256") != current:
            raise ValueError("旧稿或旧核验记录已改变；本工具不更新其冻结基线")
    else:
        write_json(baseline_path, {
            "status": "read_only_old_v2_snapshot",
            "protected_sha256": current,
            "old_numeric_occurrences": old_report["coverage"]["total"],
            "instructions_zh": "正式稿独立核验不得覆盖以上旧稿及其通过记录。",
        })
    return current


def self_test() -> None:
    old = "旧结果表\n\n|模型|损失|\n|---|---:|\n|M0|0.1234|\n\n旧结果0.1234。\n"
    new = "新结果表\n\n|模型|损失|\n|---|---:|\n|M0|0.1234|\n\n改写段仍为0.1234。\n"
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        a, b = root / "old.md", root / "new.md"
        a.write_text(old)
        b.write_text(new)
        om, nm = checker.synchronize(a, {}, root), checker.synchronize(b, {}, root)
        for claim in om["claims"]:
            claim.update(kind="result", label="测试：指定损失", metric="log_loss",
                         source={"file": "analysis/results.json", "pointer": "/loss"},
                         format={"kind": "fixed", "places": 4})
        proposals = propose_tables(old, om, new, nm)
        assert len(proposals) == 2  # table M0 identifier plus its numeric cell; never prose.
        approval = {"source_manuscript_sha256": checker.sha256(old.encode()),
                    "target_manuscript_sha256": checker.sha256(new.encode()), "approved": []}
        assert all(c["kind"] == "unresolved" for c in apply_approved(old, om, new, nm, approval)["claims"])
        p = proposals[1]
        approval["approved"] = [{"source_occurrence_id": p["source_occurrence_id"],
                                  "target_occurrence_id": p["target_occurrence_id"],
                                  "context_verified_zh": "已核对相同表头均为同一主设定M0折外对数损失。"}]
        migrated = apply_approved(old, om, new, nm, approval)
        assert sum(c["kind"] == "result" for c in migrated["claims"]) == 1
        assert migrated["claims"][-1]["kind"] == "unresolved"
        b.write_text(new.replace("|模型|损失|", "|模型|训练损失|"))
        resynced = synchronize_formal(b, migrated, root)
        assert all(c["kind"] == "unresolved" for c in resynced["claims"])
        approval["target_manuscript_sha256"] = "stale"
        try:
            apply_approved(old, om, new, nm, approval)
        except ValueError:
            pass
        else:
            raise AssertionError("旧SHA审批被接受")
        for alias in [root / "./notes/manuscript_number_claims.json",
                      (root / OLD_REPORT).absolute()]:
            try:
                guard_output_paths(root, [alias])
            except ValueError:
                pass
            else:
                raise AssertionError("旧文件路径别名未被阻断")
    print("formal_migration_self_test_passed=true")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manuscript", default=FORMAL_MD)
    parser.add_argument("--claims", default=FORMAL_CLAIMS)
    parser.add_argument("--output", default=FORMAL_REPORT)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--propose-tables", action="store_true")
    parser.add_argument("--apply-approved", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    guard_output_paths(ROOT, [ROOT / name for name in
                            [args.manuscript, args.claims, args.output, BASELINE, PROPOSALS]])
    baseline = guard_old_files(ROOT)
    manuscript, claim_path = ROOT / args.manuscript, ROOT / args.claims
    previous = read_json(claim_path) if claim_path.exists() else {}
    if args.prepare:
        mapping = synchronize_formal(manuscript, previous, ROOT)
        mapping["scope_zh"] = "正式稿独立数字映射；不继承改写段落的旧稿数字角色。"
        write_json(claim_path, mapping)
        print(json.dumps({"status": mapping["status"], "occurrences": len(mapping["claims"])}, ensure_ascii=False))
    elif args.propose_tables:
        if not manuscript.exists():
            raise ValueError("正式稿尚未落盘")
        old_text = (ROOT / OLD_MD).read_text()
        new_text = manuscript.read_text()
        mapping = synchronize_formal(manuscript, previous, ROOT)
        write_json(claim_path, mapping)
        proposals = propose_tables(old_text, read_json(ROOT / OLD_CLAIMS), new_text, mapping)
        write_json(ROOT / PROPOSALS, {
            "source_manuscript_sha256": checker.sha256(old_text.encode()),
            "target_manuscript_sha256": checker.sha256(new_text.encode()),
            "instructions_zh": "候选仅含精确相同行；须逐表核对表头/指标/估计对象，不能因同值批准。改写段落不提议迁移。",
            "proposals": proposals,
        })
        print(json.dumps({"table_proposals": len(proposals), "automatically_applied": 0}))
    elif args.apply_approved:
        result = apply_approved((ROOT / OLD_MD).read_text(), read_json(ROOT / OLD_CLAIMS),
                                manuscript.read_text(), previous, read_json(ROOT / APPROVALS))
        write_json(claim_path, result)
        print(json.dumps({"approved_table_migrations": result["approved_table_migrations"]}))
    else:
        report = checker.run_check(manuscript, previous, ROOT)
        write_json(ROOT / args.output, report)
        print(json.dumps({"passed": report["passed"], "coverage": report["coverage"],
                          "mismatch_count": len(report["mismatches"])}, ensure_ascii=False))
        if not report["passed"]:
            return 1
    if baseline != {name: file_hash(ROOT / name) for name in sorted(PROTECTED)}:
        raise ValueError("旧稿保护文件在运行过程中改变")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
