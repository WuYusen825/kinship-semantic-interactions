#!/usr/bin/env python3
"""从631项通过快照准备扩写稿候选映射；不写当前formal或旧v2记录。

运行必须显式给出root确认的定稿SHA。仅迁移方法+结果的相同完整区块、
相同语境白名单，以及身份/元数据/数字角色次序均未改变的42条书目。
摘要和改写正文中的结果均不自动迁移；未解释项留待人工核对。
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import re

import check_manuscript_numbers as checker
import map_formal_manuscript_numbers as formal


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "notes/formal_format_revision_20261016/pre_format"
WORK = ROOT / "notes/discussion_expansion_20261016"
MANUSCRIPT = ROOT / formal.FORMAL_MD


def read(path: Path):
    return json.loads(path.read_text(encoding="utf8"))


def save(path: Path, value) -> None:
    formal.guard_output_paths(ROOT, [path])
    if path.resolve() in {(ROOT / formal.FORMAL_CLAIMS).resolve(),
                          (ROOT / formal.FORMAL_REPORT).resolve()}:
        raise ValueError("准备工具仅写独立候选，不覆盖当前正式映射和报告")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


def block(text: str) -> tuple[int, int, str]:
    starts = list(re.finditer(r"^## 三、数据与方法\s*$", text, re.M))
    ends = list(re.finditer(r"^## 五、讨论\s*$", text, re.M))
    if len(starts) != 1 or len(ends) != 1 or starts[0].start() >= ends[0].start():
        raise ValueError("方法/结果完整区块边界不唯一；须人工重新界定")
    a, b = starts[0].start(), ends[0].start()
    return a, b, text[a:b]


def key(occurrence: dict) -> tuple:
    return (occurrence["line_text"], occurrence["numeric_index_on_line"], occurrence["token"])


def migrated(old: dict, new: dict, receipt: dict) -> dict:
    result = deepcopy(old)
    result.update(occurrence_id=new["occurrence_id"], anchor=deepcopy(new["anchor"]))
    # A prior approval was specific to its old whole-manuscript SHA.  Record the
    # newly verified block/entry instead of presenting that approval as current.
    result.pop("migration_review", None)
    result["expansion_revalidation"] = receipt
    return result


def prepare(expected_sha: str) -> tuple[dict, dict]:
    old_frozen = formal.guard_old_files(ROOT)
    bmd = BASE / "论文_中文正式稿.md"
    bc, br = read(BASE / "formal_manuscript_number_claims.json"), read(BASE / "formal_manuscript_number_check.json")
    old_text, new_text = bmd.read_text(encoding="utf8"), MANUSCRIPT.read_text(encoding="utf8")
    old_sha, new_sha = checker.sha256(bmd.read_bytes()), checker.sha256(MANUSCRIPT.read_bytes())
    if new_sha != expected_sha:
        raise ValueError("当前MD与明确指定的定稿SHA不符；未生成候选")
    if not br.get("passed") or br.get("coverage", {}).get("validated") != 631:
        raise ValueError("基线不是631项通过快照")
    if bc.get("manuscript_sha256") != old_sha or br.get("manuscript_sha256") != old_sha:
        raise ValueError("631基线SHA不一致")
    for name, evidence in br["sources"].items():
        if name in checker.RESULT_FILES and checker.sha256((ROOT / name).read_bytes()) != evidence["sha256"]:
            raise ValueError(f"已核结果源改变：{name}")

    mapping = checker.synchronize(MANUSCRIPT, {}, ROOT)
    old_occ, new_occ = checker.extract_numbers(old_text), checker.extract_numbers(new_text)
    old_claims = {c["occurrence_id"]: c for c in bc["claims"]}
    new_claims = {c["occurrence_id"]: c for c in mapping["claims"]}
    old_a, old_b, old_block = block(old_text)
    new_a, new_b, new_block = block(new_text)
    if old_block.encode() != new_block.encode():
        raise ValueError("方法+结果区块字节改变；禁止自动继承其中统计数字")
    receipt = {
        "baseline_manuscript_sha256": old_sha, "target_manuscript_sha256": new_sha,
        "methods_results_block_sha256": checker.sha256(old_block.encode()),
        "methods_results_bytes": len(old_block.encode()),
        "protected_old_v2_sha256": old_frozen,
        "policy_zh": "整块字节相同后按区块相对位置迁移，不搜索同值；摘要改写需独立人工复核。",
    }
    old_relative = {o["start"] - old_a: o for o in old_occ if old_a <= o["start"] < old_b}
    block_results = 0
    for o in new_occ:
        if new_a <= o["start"] < new_b:
            previous = old_relative[o["start"] - new_a]
            if key(o) != key(previous):
                raise ValueError("完整区块内数字语境发生变化")
            old = old_claims[previous["occurrence_id"]]
            new_claims[o["occurrence_id"]].update(migrated(old, new_claims[o["occurrence_id"]],
                {**receipt, "basis_zh": "方法和结果整个区块逐字节不变，数字角色和表头由同一完整上下文固定。"}))
            block_results += old["kind"] == "result"

    # Unchanged complete prose lines can retain only their non-result mappings.
    # Statistical occurrences outside the verified block always remain unresolved.
    old_keys, new_counts = {}, Counter(key(o) for o in new_occ)
    for o in old_occ:
        old_keys.setdefault(key(o), []).append(old_claims[o["occurrence_id"]])
    for o in new_occ:
        c = new_claims[o["occurrence_id"]]
        choices = old_keys.get(key(o), [])
        if c["kind"] == "unresolved" and len(choices) == 1 and new_counts[key(o)] == 1 and choices[0]["kind"] == "whitelist":
            c.update(migrated(choices[0], c,
                {**receipt, "basis_zh": "完整行文本及本行数字次序均相同；只保留非经验结果的既有具体证据。"}))

    old_refs, refs = read(BASE / "formal_references.json"), read(ROOT / "notes/formal_references.json")
    old_by_id = {r["id"]: r for r in old_refs}
    if len(old_by_id) != 42 or {r["id"] for r in refs} != set(old_by_id):
        raise ValueError("42来源身份集合改变；须另做书目核验")
    old_occ_by_line, new_occ_by_line = {}, {}
    for o in old_occ:
        old_occ_by_line.setdefault(o["line_text"], []).append(o)
    for o in new_occ:
        new_occ_by_line.setdefault(o["line_text"], []).append(o)
    ref_receipts = []
    for r in refs:
        prior = old_by_id[r["id"]]
        for fact in ["id", "year_label", "metadata", "doi", "title", "document_type"]:
            if r[fact] != prior[fact]:
                raise ValueError(f"书目{r['id']}的事实字段{fact}改变")
        if old_text.splitlines().count(prior["entry"]) != 1 or new_text.splitlines().count(r["entry"]) != 1:
            raise ValueError(f"书目{r['id']}未精确出现一次")
        previous, current = old_occ_by_line.get(prior["entry"], []), new_occ_by_line.get(r["entry"], [])
        if [o["token"] for o in previous] != [o["token"] for o in current]:
            raise ValueError(f"书目{r['id']}数字角色序列改变，须逐字段人工重建")
        old_fields = [old_claims[o["occurrence_id"]] for o in previous]
        if any(c["kind"] != "whitelist" or c["whitelist"]["category"] not in
               {"citation_year", "bibliographic_number", "doi", "url"} for c in old_fields):
            raise ValueError("旧书目数字含非书目角色；禁止迁移")
        item = {"source_id": r["id"], "fact_fields_equal": True,
                "old_entry_sha256": checker.sha256(prior["entry"].encode()),
                "new_entry_sha256": checker.sha256(r["entry"].encode()),
                "numeric_occurrences": len(current)}
        ref_receipts.append(item)
        for old, o in zip(old_fields, current):
            c = new_claims[o["occurrence_id"]]
            c.update(migrated(old, c,
                {**receipt, **item, "basis_zh": "按来源ID核对题名、年份后缀、载体、完整卷期页/文章号和DOI均未变；仅书目格式改变，数字角色顺序相同。"}))

    receipt.update(block_results_migrated=block_results,
                   results_outside_verified_block_not_automatically_migrated=True,
                   references=ref_receipts,
                   counts=dict(Counter(c["kind"] for c in mapping["claims"])))
    mapping["expansion_revalidation_receipt"] = receipt
    return mapping, receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha", required=True)
    args = parser.parse_args()
    mapping, receipt = prepare(args.expected_sha)
    save(WORK / "expanded_number_claims_candidate.json", mapping)
    save(WORK / "expanded_number_revalidation_receipt.json", receipt)
    print(json.dumps({"target_sha256": args.expected_sha, "counts": receipt["counts"],
                      "block_results": receipt["block_results_migrated"],
                      "status": "candidate_requires_manual_remaining_mapping"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
