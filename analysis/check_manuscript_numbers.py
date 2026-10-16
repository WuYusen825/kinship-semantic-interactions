#!/usr/bin/env python3
"""逐处核对论文数字；未映射数字、过期定位和错误来源均失败关闭。

用法：
  python analysis/check_manuscript_numbers.py --init-claims
  python analysis/check_manuscript_numbers.py --sync-claims
  python analysis/check_manuscript_numbers.py --check
  python analysis/check_manuscript_numbers.py --self-test

init/sync仅列举数字，不推断来源、不自动白名单。每项须人工指定result或
whitelist。result必须指向允许的结果JSON中的具体RFC6901 pointer，可显式
组合多个已定位数值；不搜索同值。行文本+本行数字序号完全相同时才保留旧映射。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
import unicodedata
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANUSCRIPT = "outputs/forum/论坛稿_v2.md"
DEFAULT_CLAIMS = "notes/manuscript_number_claims.json"
DEFAULT_REPORT = "notes/manuscript_number_check.json"
RESULT_FILES = {
    "analysis/results.json",
    "analysis/supplementary_s1/s1_results.json",
    "analysis/supplementary_s2/s2_results.json",
    "analysis/forum_descriptives.json",
}
WHITE_CATEGORIES = {
    "citation_year", "citation_page", "bibliographic_number", "literature_number",
    "model_identifier", "hypothesis_identifier", "definition_identifier", "ordinal",
    "design_constant", "theoretical_constant", "version", "date", "doi", "url",
    "linguistic_example", "software_setting", "repository_identifier",
    "layout_setting",
}
CN_DIGITS = "零〇一二三四五六七八九十百千万亿两"
NUMBER_RE = re.compile(
    r"(?P<hash>(?<![A-Za-z0-9])(?=[0-9a-fA-F]{7,64}(?![A-Za-z0-9]))"
    r"(?=[0-9a-fA-F]*\d)[0-9a-fA-F]{7,64}(?![A-Za-z0-9]))"
    r"|(?P<arabic>[+−-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
    r"(?:[eE][+−-]?\d+)?(?:[ \t]?[%％])?)"
    r"|(?P<super>[⁰¹²³⁴⁵⁶⁷⁸⁹]+)"
    r"|(?P<chinese>[" + CN_DIGITS + r"]+)"
)
CN_UNITS = re.compile(
    r"^(?:个|项|种|类|次|位|对|条|组|折|层|侧|代|篇|份|元|分|级|维|页|年|月|日|"
    r"小时|分钟|秒|特征|模型|系统|语言|谱系|区域|条件|参数|基准|定义|结果|预测|假设|"
    r"幅|张|套|端|列|行|段|点|例|倍|成|部分|方向|阶段|版本|语种|单元|估计|权重|区|叶|大型谱系)"
)
CN_VALUES = dict(zip("零〇一二三四五六七八九两", [0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 2]))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cn_value(text: str) -> int:
    total, section, number = 0, 0, 0
    for ch in text:
        if ch in CN_VALUES:
            number = CN_VALUES[ch]
        elif ch in "十百千":
            section += (number or 1) * {"十": 10, "百": 100, "千": 1000}[ch]
            number = 0
        elif ch in "万亿":
            total += (section + number) * {"万": 10_000, "亿": 100_000_000}[ch]
            section, number = 0, 0
    return total + section + number


def decimal_token(token: str) -> Decimal:
    normalized = unicodedata.normalize("NFKC", token).replace("−", "-")
    normalized = normalized.replace(",", "").strip().rstrip("%％").strip()
    if normalized and all(ch in CN_DIGITS for ch in normalized):
        return Decimal(cn_value(normalized))
    return Decimal(normalized)


def extract_numbers(text: str) -> list[dict[str, Any]]:
    """覆盖全部阿拉伯数字/上标数字；中文数字按明确计数/序号语境提取。"""
    occurrences: list[dict[str, Any]] = []
    absolute = 0
    for line_no, line_with_ending in enumerate(text.splitlines(keepends=True), 1):
        line = line_with_ending.rstrip("\r\n")
        line_numeric_index = 0
        pieces = []
        for match in NUMBER_RE.finditer(line):
            token, start, end, kind = match.group(), *match.span(), match.lastgroup
            # Pandoc superscripts use commas as page separators, not thousands:
            # ^302,315-316^ contains three page numbers, whereas 26,292 is one count.
            if kind == "arabic" and "," in token and line[:start].count("^") % 2:
                pieces.extend((m.group(), start + m.start(), start + m.end(), kind)
                              for m in re.finditer(r"[+−-]?\d+(?:\.\d+)?", token))
            else:
                pieces.append((token, start, end, kind))
        for token, start, end, kind in pieces:
            if kind == "chinese":
                left, right = line[:start], line[end:]
                is_heading = bool(re.search(r"(?:^\s*#{1,6}\s*|[（(第])$", left))
                is_ordinal = bool(re.search(r"第$", left))
                is_count = bool(CN_UNITS.match(right))
                if token == "零" or (token == "一" and (
                    left.endswith("留") and right.startswith("宏观区域")
                    or left.endswith("单") and right.startswith("词形")
                )):
                    is_count = True
                if token == "百" and right.startswith(("分位", "分点")):
                    is_count = False  # 百分位/百分点 are statistical terms, not counts of 100.
                if not (is_heading or is_ordinal or is_count):
                    continue
                # lexical 一致/一般/同一 do not satisfy a counting unit above.
            if kind == "arabic" and token.startswith(("-", "+", "−")):
                # In 491-493 or YYYY-MM-DD the separator is not a negative sign.
                if start > 0 and (re.match(r"[A-Za-z0-9]", line[start - 1]) or line[start - 1] in "~}"):
                    token, start = token[1:], start + 1
            line_numeric_index += 1
            occurrences.append({
                "occurrence_id": f"N{len(occurrences) + 1:05d}",
                "line": line_no, "column": start + 1, "start": absolute + start,
                "end": absolute + end, "token": token, "numeric_kind": kind,
                "numeric_index_on_line": line_numeric_index, "line_text": line,
                "context_sha256": sha256(line.encode()),
            })
        absolute += len(line_with_ending)
    return occurrences


def pointer_get(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise ValueError("JSON pointer必须为空或以/开头")
    value = document
    for escaped in pointer[1:].split("/"):
        part = escaped.replace("~1", "/").replace("~0", "~")
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def read_json_source(source: dict, root: Path, cache: dict, result_only: bool) -> Any:
    relative = source.get("file")
    pointer = source.get("pointer")
    if not isinstance(relative, str) or not isinstance(pointer, str):
        raise ValueError("source必须包含file和精确pointer")
    if result_only and relative not in RESULT_FILES:
        raise ValueError(f"结果源不在允许清单：{relative}")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("来源路径越出仓库")
    if relative not in cache:
        raw = path.read_bytes()
        cache[relative] = {"json": json.loads(raw), "sha256": sha256(raw)}
    entry = cache[relative]
    if source.get("sha256") and source["sha256"] != entry["sha256"]:
        raise ValueError("来源SHA-256已变化")
    for guard in source.get("guards", []):
        if pointer_get(entry["json"], guard["pointer"]) != guard["equals"]:
            raise ValueError(f"来源语境guard不匹配：{guard['pointer']}")
    return pointer_get(entry["json"], pointer)


def calculate(claim: dict, root: Path, cache: dict) -> Decimal:
    if "source" in claim and claim["source"] is not None:
        raw = read_json_source(claim["source"], root, cache, True)
        if isinstance(raw, bool) or not isinstance(raw, (int, float, str)):
            raise ValueError("结果pointer没有指向一个标量数值")
        return Decimal(str(raw))
    calculation = claim.get("calculation")
    if not isinstance(calculation, dict) or not claim.get("calculation_reason"):
        raise ValueError("结果缺少source或有明确理由的calculation")
    operands = []
    for src in calculation.get("operands", []):
        raw = read_json_source(src, root, cache, True)
        if isinstance(raw, bool):
            raise ValueError("不能把布尔值当作结果数")
        operands.append(Decimal(str(raw)))
    op = calculation.get("operation")
    if op == "sum" and operands:
        return sum(operands)
    if op == "difference" and len(operands) == 2:
        return operands[0] - operands[1]
    if op == "ratio" and len(operands) == 2:
        return operands[0] / operands[1]
    if op == "product" and operands:
        value = Decimal(1)
        for item in operands:
            value *= item
        return value
    if op == "complement" and len(operands) == 1:
        return Decimal(1) - operands[0]
    if op == "count_nonnegative" and operands:
        return Decimal(sum(value >= 0 for value in operands))
    raise ValueError(f"不支持的运算或参数数目：{op}")


def format_value(value: Decimal, spec: dict) -> str:
    kind = spec.get("kind")
    places = spec.get("places")
    rounding = {"half_up": ROUND_HALF_UP, "half_even": ROUND_HALF_EVEN}.get(
        spec.get("rounding", "half_up")
    )
    if rounding is None or not value.is_finite():
        raise ValueError("舍入模式无效或结果非有限")
    if kind == "integer":
        if value != value.to_integral_value():
            raise ValueError("非整数源不能格式化为计数")
        return f"{int(value):,}" if spec.get("grouping") == "comma" else str(int(value))
    if kind in {"fixed", "percent", "percentage_points"}:
        if not isinstance(places, int) or places < 0:
            raise ValueError("fixed/percent需要明确非负小数位")
        if kind in {"percent", "percentage_points"}:
            value *= 100
        rounded = value.quantize(Decimal(1).scaleb(-places), rounding=rounding)
        if rounded == 0:
            rounded = abs(rounded)
        return f"{rounded:.{places}f}" + ("%" if kind == "percent" else "")
    if kind == "scientific":
        if not isinstance(places, int):
            raise ValueError("科学计数需要明确小数位")
        return f"{value:.{places}E}"
    if kind == "exact_numeric":
        return str(value)
    raise ValueError("必须指定integer/fixed/percent/scientific/exact_numeric格式")


def validate_whitelist(claim: dict, occurrence: dict, root: Path, cache: dict) -> dict:
    white = claim.get("whitelist")
    if not isinstance(white, dict):
        raise ValueError("白名单缺少逐处说明")
    if white.get("category") not in WHITE_CATEGORIES:
        raise ValueError("白名单分类未知")
    if white.get("expected_token") != occurrence["token"]:
        raise ValueError("白名单不是当前精确数字字符串")
    if not isinstance(white.get("reason"), str) or len(white["reason"].strip()) < 6:
        raise ValueError("白名单缺少实质理由")
    evidence = white.get("evidence")
    if not isinstance(evidence, dict):
        raise ValueError("白名单须注明可复查依据")
    if "pointer" in evidence:
        raw = read_json_source(evidence, root, cache, False)
        if "expected_value" not in evidence or raw != evidence["expected_value"]:
            raise ValueError("白名单JSON依据值不匹配")
    elif evidence.get("file") and evidence.get("quote"):
        p = (root / evidence["file"]).resolve()
        if not p.is_relative_to(root.resolve()):
            raise ValueError("白名单依据路径越出仓库")
        if evidence["quote"] not in p.read_text(encoding="utf8"):
            raise ValueError("白名单引文不在指定依据文件")
    elif evidence.get("type") == "document_structure":
        if white["category"] not in {"ordinal", "model_identifier", "hypothesis_identifier", "definition_identifier", "layout_setting"}:
            raise ValueError("文档结构依据不能豁免经验数字")
        if not evidence.get("explanation"):
            raise ValueError("文档结构依据缺少说明")
    else:
        raise ValueError("白名单依据须为JSON pointer、文件原文或明确文档结构")
    return {"category": white["category"], "reason": white["reason"], "evidence": evidence}


def run_check(manuscript: Path, mapping: dict, root: Path) -> dict:
    report: dict[str, Any] = {
        "schema_version": 1, "manuscript": str(manuscript.relative_to(root)),
        "passed": False, "status": "checking", "mismatches": [], "occurrences": [],
        "scope": "entire_markdown_including_frontmatter_tables_captions_and_references",
        "extraction": "Arabic numerals, numeric superscripts, and Chinese numerals in explicit counting/ordinal contexts",
    }
    errors = report["mismatches"]
    if not manuscript.exists():
        report.update(status="awaiting_manuscript", coverage={"total": 0, "mapped": 0, "validated": 0, "all_numeric_occurrences": False})
        errors.append({"type": "missing_manuscript", "detail": str(manuscript)})
        return report
    raw = manuscript.read_bytes()
    text = raw.decode("utf8")
    report["manuscript_sha256"] = sha256(raw)
    if mapping.get("manuscript_sha256") != report["manuscript_sha256"]:
        errors.append({"type": "manuscript_changed", "detail": "先sync后逐处复核变化项；不接受旧版本映射"})
    occurrences = extract_numbers(text)
    claim_list = mapping.get("claims", [])
    counts = Counter(c.get("occurrence_id") for c in claim_list)
    for ident, count in counts.items():
        if count > 1:
            errors.append({"type": "duplicate_claim", "occurrence_id": ident})
    claims = {c.get("occurrence_id"): c for c in claim_list}
    cache: dict[str, Any] = {}
    mapped = valid = 0
    actual_ids = {o["occurrence_id"] for o in occurrences}
    for ident in claims.keys() - actual_ids:
        errors.append({"type": "stale_claim", "occurrence_id": ident})
    for occurrence in occurrences:
        row = dict(occurrence)
        claim = claims.get(occurrence["occurrence_id"])
        row["passed"] = False
        if claim is None:
            row["error"] = "unmapped_numeric_occurrence"
        else:
            mapped += claim.get("kind") in {"result", "whitelist"}
            row.update(kind=claim.get("kind"), label=claim.get("label"), source=claim.get("source"), calculation=claim.get("calculation"), format=claim.get("format"))
            try:
                if not claim.get("label"):
                    raise ValueError("缺少数字对应的明确命题标签")
                anchor = claim.get("anchor", {})
                for key in ["token", "line_text", "numeric_index_on_line"]:
                    if anchor.get(key) != occurrence[key]:
                        raise ValueError(f"数字位置/语境已变化：{key}")
                if claim.get("kind") == "result":
                    spec = claim.get("format") or {}
                    metric = claim.get("metric")
                    if metric in {"log_loss", "log_loss_gain", "log_loss_ci"} and (spec.get("kind"), spec.get("places")) != ("fixed", 4):
                        raise ValueError("对数损失及其差/区间须保留四位小数")
                    if metric in {"proportion", "proportion_ci"} and (spec.get("kind"), spec.get("places")) != ("percent", 1):
                        raise ValueError("比例及其区间须用一位小数百分数")
                    if metric == "percentage_points" and (spec.get("kind"), spec.get("places")) != ("percentage_points", 1):
                        raise ValueError("百分点须乘100后保留一位小数、不附百分号")
                    value = calculate(claim, root, cache)
                    bound = claim.get("bound")
                    displayed_value = value
                    if bound is not None:
                        if metric != "p_value" or not isinstance(bound, dict):
                            raise ValueError("不等号上界只允许明确的p_value命题")
                        threshold = Decimal(str(bound["threshold"]))
                        relation = bound.get("relation")
                        relations = {"<": value < threshold, "<=": value <= threshold,
                                     ">": value > threshold, ">=": value >= threshold}
                        if relation not in relations or not relations[relation]:
                            raise ValueError("来源p值不满足指定阈值关系")
                        prefix = occurrence["line_text"][:occurrence["column"] - 1]
                        literal = {"<": "<", "<=": "≤", ">": ">", ">=": "≥"}[relation]
                        if not prefix.rstrip().endswith(literal):
                            raise ValueError("正文p值阈值前缺指定不等号")
                        displayed_value = threshold
                    expected = format_value(displayed_value, spec)
                    observed = unicodedata.normalize("NFKC", occurrence["token"]).replace("−", "-").replace(" ", "")
                    if occurrence["numeric_kind"] == "chinese":
                        observed = str(cn_value(occurrence["token"]))
                    row.update(source_value=str(value), expected_token=expected, bound=bound)
                    if spec.get("kind") == "exact_numeric":
                        if decimal_token(observed) != value:
                            raise ValueError(f"数值不符：应为{expected}，实为{observed}")
                    elif observed != expected:
                        raise ValueError(f"数值或舍入不符：应为{expected}，实为{observed}")
                elif claim.get("kind") == "whitelist":
                    row["whitelist"] = validate_whitelist(claim, occurrence, root, cache)
                else:
                    raise ValueError("尚未人工映射为result或逐处whitelist")
                row["passed"] = True
                valid += 1
            except (ValueError, KeyError, IndexError, TypeError, OSError, InvalidOperation, ArithmeticError) as exc:
                row["error"] = str(exc)
        if not row["passed"]:
            errors.append({"type": "numeric_occurrence_failed", "occurrence_id": occurrence["occurrence_id"], "line": occurrence["line"], "column": occurrence["column"], "token": occurrence["token"], "detail": row["error"]})
        report["occurrences"].append(row)
    # Every Arabic/superscript numeral character must belong to a token.
    occupied = {p for o in occurrences for p in range(o["start"], o["end"])}
    uncovered = [i for i, ch in enumerate(text) if (ch.isdecimal() or ch in "⁰¹²³⁴⁵⁶⁷⁸⁹") and i not in occupied]
    if uncovered:
        errors.append({"type": "extractor_uncovered_digits", "offsets": uncovered})
    report["coverage"] = {"total": len(occurrences), "mapped": mapped, "validated": valid,
                          "all_numeric_occurrences": mapped == len(occurrences) and not uncovered,
                          "all_validated": valid == len(occurrences) and not uncovered,
                          "uncovered_digit_offsets": uncovered}
    report["sources"] = {name: {"sha256": item["sha256"]} for name, item in sorted(cache.items())}
    report["passed"] = not errors and bool(occurrences)
    report["status"] = "passed" if report["passed"] else "failed"
    return report


def synchronize(manuscript: Path, previous: dict, root: Path) -> dict:
    existing = defaultdict(list)
    for claim in previous.get("claims", []):
        a = claim.get("anchor", {})
        existing[(a.get("line_text"), a.get("numeric_index_on_line"), a.get("token"))].append(claim)
    if not manuscript.exists():
        return {"schema_version": 1, "status": "awaiting_manuscript", "manuscript": str(manuscript.relative_to(root)), "manuscript_sha256": None, "instructions_zh": "文稿出现后运行--sync-claims；每处数字须人工指定精确结果pointer或有依据的白名单。", "claims": []}
    raw = manuscript.read_bytes()
    tokens = extract_numbers(raw.decode("utf8"))
    key_counts = Counter((o["line_text"], o["numeric_index_on_line"], o["token"]) for o in tokens)
    result = []
    retained = 0
    for o in tokens:
        key = (o["line_text"], o["numeric_index_on_line"], o["token"])
        candidates = existing.get(key, [])
        if len(candidates) == 1 and key_counts[key] == 1:
            claim = dict(candidates[0])
            retained += claim.get("kind") in {"result", "whitelist"}
        else:
            claim = {"kind": "unresolved", "label": "", "source": None, "format": None}
        claim["occurrence_id"] = o["occurrence_id"]
        claim["anchor"] = {k: o[k] for k in ["token", "line", "column", "line_text", "numeric_index_on_line", "context_sha256"]}
        result.append(claim)
    return {"schema_version": 1, "status": "mapping_required", "manuscript": str(manuscript.relative_to(root)), "manuscript_sha256": sha256(raw), "retained_exact_context_mappings": retained, "instructions_zh": "未知数字不会自动白名单；result须精确JSON pointer；计数用integer，损失用fixed4，比例用percent1。", "claims": result}


def self_test() -> None:
    """验证同值搜索不能替代pointer、未映射数字及错误舍入一定失败。"""
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        (root / "analysis").mkdir()
        p = root / "manuscript.md"
        p.write_text("损失0.1235，比例25.0%，样本八个。\n", encoding="utf8")
        (root / "analysis/results.json").write_text(json.dumps({"loss": .123456, "share": .25, "n": 8, "wrong": .2}))
        mapping = synchronize(p, {}, root)
        for claim, pointer, spec, metric in zip(mapping["claims"], ["/loss", "/share", "/n"], [{"kind": "fixed", "places": 4}, {"kind": "percent", "places": 1}, {"kind": "integer"}], ["log_loss", "proportion", "count"]):
            claim.update(kind="result", label="测试中明确指定的数值", source={"file": "analysis/results.json", "pointer": pointer}, format=spec, metric=metric)
        assert run_check(p, mapping, root)["passed"]
        mapping["claims"][0]["source"]["pointer"] = "/wrong"
        assert not run_check(p, mapping, root)["passed"]
        mapping["claims"][0]["source"]["pointer"] = "/loss"
        removed = mapping["claims"].pop()
        assert not run_check(p, mapping, root)["passed"]
        mapping["claims"].append(removed)
        mapping["claims"][0]["format"]["places"] = 3
        assert not run_check(p, mapping, root)["passed"]
        mapping["claims"][0]["format"]["places"] = 4
        p.write_text("损失0.1234，比例25.0%，样本八个。\n", encoding="utf8")
        assert not run_check(p, mapping, root)["passed"]
        extra = extract_numbers("M~0~—M~4~，p=1e−9，2026-10-15，26,292，95%，二元，第一节；一致。")
        assert [o["token"] for o in extra] == ["0", "4", "1e−9", "2026", "10", "15", "26,292", "95%", "二", "一"]
        assert [o["token"] for o in extract_numbers("页^302,315-316^，百分位95%区间。 ")] == ["302", "315", "316", "95%"]
        assert [o["token"] for o in extract_numbers("分别为−90.9和−80.1，为−0.0079，491-493。")] == ["−90.9", "−80.1", "−0.0079", "491", "493"]
        assert format_value(Decimal("-.90888"), {"kind": "percentage_points", "places": 1}) == "-90.9"
        p.write_text("p<0.0001\n", encoding="utf8")
        mapping = synchronize(p, {}, root)
        mapping["claims"][0].update(kind="result", label="明确上界的精确检验p值",
            metric="p_value", source={"file": "analysis/results.json", "pointer": "/loss"},
            bound={"relation": "<", "threshold": "0.0001"}, format={"kind": "fixed", "places": 4})
        assert not run_check(p, mapping, root)["passed"]  # .123456 is not < .0001.
        mapping["claims"][0]["bound"]["threshold"] = "0.2000"
        p.write_text("p<0.2000\n", encoding="utf8")
        mapping = synchronize(p, mapping, root)
        mapping["claims"][0].update(kind="result", label="明确上界的精确检验p值",
            metric="p_value", source={"file": "analysis/results.json", "pointer": "/loss"},
            bound={"relation": "<", "threshold": "0.2000"}, format={"kind": "fixed", "places": 4})
        assert run_check(p, mapping, root)["passed"]
        # An arbitrary whitelist cannot exempt an empirical result through structural metadata.
        mapping["claims"][0].update(kind="whitelist", whitelist={"category": "design_constant",
            "expected_token": "0.2000", "reason": "这一理由没有来源支持",
            "evidence": {"type": "document_structure", "explanation": "任意数字"}})
        assert not run_check(p, mapping, root)["passed"]
    print("self_test_passed=true：逐处映射、错误pointer、未知数字、舍入与版本变化检查通过")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manuscript", default=DEFAULT_MANUSCRIPT)
    parser.add_argument("--claims", default=DEFAULT_CLAIMS)
    parser.add_argument("--output", default=DEFAULT_REPORT)
    parser.add_argument("--init-claims", action="store_true")
    parser.add_argument("--sync-claims", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    manuscript, claim_path, report_path = (ROOT / args.manuscript, ROOT / args.claims, ROOT / args.output)
    previous = json.loads(claim_path.read_text()) if claim_path.exists() else {}
    if args.init_claims or args.sync_claims:
        if args.init_claims and claim_path.exists() and previous.get("claims"):
            raise SystemExit("映射已存在；使用--sync-claims保留完全匹配的既有映射")
        mapping = synchronize(manuscript, previous, ROOT)
        claim_path.parent.mkdir(parents=True, exist_ok=True)
        claim_path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"status": mapping["status"], "numeric_occurrences": len(mapping["claims"]), "claims": str(claim_path.relative_to(ROOT)), "retained": mapping.get("retained_exact_context_mappings", 0)}, ensure_ascii=False))
        return 0
    report = run_check(manuscript, previous, ROOT)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "status": report["status"], "coverage": report["coverage"], "mismatch_count": len(report["mismatches"]), "report": str(report_path.relative_to(ROOT))}, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
