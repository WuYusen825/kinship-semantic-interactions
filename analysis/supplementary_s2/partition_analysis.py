"""按已冻结S2协议执行D3划分分析P1–P5，保留原始字段与结构见证。

只写本脚本负责的补充输出；不修改冻结分析、S1或纯理论代码。
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from functools import lru_cache
from itertools import product
from pathlib import Path
import argparse
import csv
import hashlib
import json
from math import comb
import subprocess
import unicodedata

import numpy as np
from scipy.stats import binomtest

from structural_enumeration import (
    BASIS_RAW, BASIS_RELATIVE, FEATURES, FEATURES_FOUR, FEATURES_SIX,
    KINTYPES, UNIVERSE, block_shape, enumerate_partitions,
    evaluate_partition, feature_tree_depth_options, is_conjunctive,
    labels_to_partition, partition_codes, partition_to_labels,
    select_bases, strict_prediction_directions, tree_partitions,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis/supplementary_s2"
PROTOCOL = OUT / "protocol_s2.md"
PROTOCOL_SHA256 = "61874a1c28ab37758670a61d12e08b6097af07f7922f63cfd76da5dacfcef8be"
PROTOCOL_COMMIT = "6ba7afba369d3d15446ea7571eabd2117b7e8c74"
SEED = 20261014
BOOTSTRAP_REPLICATES = 5000
FAMILY_REMOVALS = {"excluding_austronesian": "aust1307", "excluding_pama_nyungan": "pama1250"}
FEATURE_SETS = {"three": BASIS_RAW, "four": FEATURES_FOUR, "six": FEATURES_SIX}
CATEGORY_BY_CODE = {code: code[0] + code[-1] + ("B" if code[2] == "m" else "Z") for code in KINTYPES}
CATEGORY_ORDER = tuple(CATEGORY_BY_CODE[code] for code in KINTYPES)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_git(*arguments):
    return subprocess.check_output(["git", *arguments], cwd=ROOT).decode().strip()


def protocol_guard():
    current_hash = sha256(PROTOCOL)
    if current_hash != PROTOCOL_SHA256:
        raise RuntimeError("最终S2协议SHA-256不匹配，停止运行")
    committed_bytes = subprocess.check_output(["git", "show", f"{PROTOCOL_COMMIT}:analysis/supplementary_s2/protocol_s2.md"], cwd=ROOT)
    if hashlib.sha256(committed_bytes).hexdigest() != PROTOCOL_SHA256:
        raise RuntimeError("协议独立提交的内容与已确认SHA不符")
    subprocess.run(["git", "merge-base", "--is-ancestor", PROTOCOL_COMMIT, "HEAD"], cwd=ROOT, check=True)
    commit_message = run_git("show", "-s", "--format=%s", PROTOCOL_COMMIT)
    if "pre-run protocol" not in commit_message.lower():
        raise RuntimeError("协议提交标题不含pre-run protocol")
    commit_epoch = int(run_git("show", "-s", "--format=%ct", PROTOCOL_COMMIT))
    if Path(__file__).stat().st_mtime < commit_epoch:
        raise RuntimeError("实测脚本文件时间早于最终协议提交，须核查时间线")
    return {"protocol_sha256": current_hash, "protocol_commit": PROTOCOL_COMMIT,
            "protocol_commit_message": commit_message,
            "protocol_commit_time": run_git("show", "-s", "--format=%cI", PROTOCOL_COMMIT),
            "script_mtime_utc": datetime.fromtimestamp(Path(__file__).stat().st_mtime, timezone.utc).isoformat(),
            "script_sha256": sha256(__file__), "head_at_run": run_git("rev-parse", "HEAD")}


def read_csv(path):
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def norm(value):
    return " ".join(unicodedata.normalize("NFC", str(value)).split())


def load_inputs():
    pairs = defaultdict(list)
    for row in read_csv(ROOT / "analysis/pairs_primary.csv"):
        pairs[row["Language_ID"]].append(row)
    forms = defaultdict(dict)
    for row in read_csv(ROOT / "analysis/category_forms_primary.csv"):
        if row["Language_ID"] in pairs:
            values = json.loads(row["forms_json"])
            if len(set(values)) != int(row["n_forms"]):
                raise ValueError("类别词形计数不一致")
            forms[row["Language_ID"]][row["Parameter_ID"]] = tuple(sorted(set(values)))
    if len(pairs) != 939 or sum(map(len, pairs.values())) != 26292:
        raise ValueError("主样本系统数或类别对数与协议不一致")
    metadata = {}
    for language_id, rows in pairs.items():
        if len(rows) != 28 or set(forms[language_id]) != set(CATEGORY_ORDER):
            raise ValueError("主样本不满足完整八类、28对")
        first = rows[0]
        metadata[language_id] = {key: first[key] for key in ("Language_ID", "Glottocode", "Name", "family_group", "family_name", "family_status", "Macroarea")}
        metadata[language_id]["macroarea_raw"] = first["Macroarea"]
        metadata[language_id]["macroarea"] = first["Macroarea"].split(";")[0].strip() or "Unknown"
        for row in rows:
            recomputed = bool(set(forms[language_id][row["category_a"]]) & set(forms[language_id][row["category_b"]]))
            if recomputed != bool(int(row["shared_form"])):
                raise ValueError("类别词形与冻结共享对不一致")
    if len({value["family_group"] for value in metadata.values()}) != 125:
        raise ValueError("谱系数与协议不一致")
    raw_records = defaultdict(list)
    for row in read_csv(ROOT / "data/kinbank/kinbank/cldf/forms.csv"):
        language_id, category = row["Language_ID"], row["Parameter_ID"]
        if language_id in forms and category in forms[language_id] and norm(row["Form"]) in forms[language_id][category]:
            raw_records[language_id].append({key: row[key] for key in ("ID", "Language_ID", "Parameter_ID", "Value", "Form", "Comment", "Source")})
    return pairs, forms, metadata, raw_records


@lru_cache(None)
def all_single_leaf_trees(partition, mask=UNIVERSE):
    """保存全部四特征合法树，独立核对纯模块的计数与P5限制。"""
    if mask in partition:
        return (("leaf", mask),)
    output = []
    for name in FEATURES_FOUR:
        zero = mask & sum(1 << i for i, value in enumerate(FEATURES[name]) if value == 0)
        one = mask ^ zero
        if not zero or not one or any(block & zero and block & one for block in partition):
            continue
        for left in all_single_leaf_trees(partition, zero):
            for right in all_single_leaf_trees(partition, one):
                output.append((name, left, right))
    return tuple(output)


def p5_tree_compatible(tree, depth=0):
    if tree[0] == "leaf":
        return True
    return (tree[0] != "s" or depth >= 2) and p5_tree_compatible(tree[1], depth + 1) and p5_tree_compatible(tree[2], depth + 1)


def diagnostics_for_partition(partition):
    labels = partition_to_labels(partition)
    structure = strict_prediction_directions(labels)
    trees = all_single_leaf_trees(partition)
    compatible = [tree for tree in trees if p5_tree_compatible(tree)]
    p5 = structure["P5_tree_depth_options"]
    if len(trees) != p5["total_tree_representation_count"] or len(compatible) != p5["compatible_tree_representation_count"]:
        raise RuntimeError("独立列出全部树与纯结构模块的P5树计数不一致")
    return {"partition_masks": list(partition), "partition_codes": partition_codes(partition),
            "shape": list(block_shape(partition)), "n_terms": len(partition),
            "indicators": {f"{definition}_{feature_set}": bool(is_conjunctive(partition, features) if definition == "A" else partition in tree_partitions(tuple(features))) for feature_set, features in FEATURE_SETS.items() for definition in ("A", "B")},
            "strict_directions": {name: structure[name] for name in ("P2", "P3", "P4")},
            "secondary_diagnostics": structure["secondary_diagnostics"], "P5": p5,
            "P5_edge_proxy": {"status": structure["P5_edge_proxy"], "separated_counts": structure["P5_separated_counts"]},
            "basis_choices": select_bases(labels),
            "edge_profiles_raw": evaluate_partition(labels, BASIS_RAW),
            "edge_profiles_relative": evaluate_partition(labels, BASIS_RELATIVE),
            "all_four_feature_single_leaf_trees": trees,
            "compatible_four_feature_P5_trees": compatible}


def prepare_systems(forms, metadata, raw_records):
    systems, catalogue = [], {}
    for language_id in sorted(forms, key=lambda key: (metadata[key]["Glottocode"], key)):
        if not all(len(forms[language_id][category]) == 1 for category in CATEGORY_ORDER):
            continue
        labels = tuple(forms[language_id][category][0] for category in CATEGORY_ORDER)
        partition = labels_to_partition(labels)
        key = "-".join(map(str, partition))
        if key not in catalogue:
            catalogue[key] = diagnostics_for_partition(partition)
        diagnostics = catalogue[key]
        violations = []
        for feature_set in FEATURE_SETS:
            for definition in ("A", "B"):
                indicator_key = f"{definition}_{feature_set}"
                if not diagnostics["indicators"][indicator_key]:
                    reason = "至少一个词项不能由指定特征合取定义" if definition == "A" else "不存在每词项恰为一个叶的指定特征递归划分树"
                    violations.append({"proposition": f"P1_{indicator_key}", "feature": feature_set,
                                       "reason": reason, "primary": indicator_key == "A_four"})
        for prediction, direction in diagnostics["strict_directions"].items():
            if direction == "opposite_side":
                violations.append({"proposition": prediction, "feature": {"P2": "a→r", "P3": "r→a", "P4": "q→a"}[prediction], "reason": "严格根与子根兼容的次级区分只位于预测相反侧", "primary": True})
        if diagnostics["P5"]["status"] == "incompatible_all_trees_require_early_feature":
            violations.append({"proposition": "P5", "feature": "s", "reason": "存在四特征单叶树，但所有树均需参照者性别在根或二级出现", "primary": True})
        systems.append({**metadata[language_id], "structure_key": key,
                        "forms": {category: forms[language_id][category][0] for category in CATEGORY_ORDER},
                        "violations": violations, "raw_records": raw_records[language_id]})
    if len(systems) != 625:
        raise ValueError("D3子样本不等于冻结的625系统")
    return systems, catalogue


def exact_nulls():
    partitions = enumerate_partitions()
    shape_totals = Counter(block_shape(partition) for partition in partitions)
    nulls = {}
    for feature_set, features in FEATURE_SETS.items():
        for definition in ("A", "B"):
            accepted = {p for p in partitions if is_conjunctive(p, features)} if definition == "A" else set(tree_partitions(tuple(features)))
            by_shape = Counter(block_shape(partition) for partition in accepted)
            nulls[f"{definition}_{feature_set}"] = {
                "uniform_violation_probability": (len(partitions) - len(accepted)) / len(partitions),
                "accepted_partitions": len(accepted), "all_partitions": len(partitions),
                "shape_violation_probability": {shape: (count - by_shape[shape]) / count for shape, count in shape_totals.items()},
                "shape_total": dict(shape_totals)}
    return nulls


def grouped_bootstrap(systems, observed, reference):
    groups = defaultdict(list)
    for index, system in enumerate(systems):
        groups[system["family_group"]].append(index)
    family_ids = sorted(groups)
    counts = np.array([len(groups[family]) for family in family_ids], dtype=float)
    observed_means = np.array([np.mean([observed[i] for i in groups[family]]) for family in family_ids])
    reference_means = np.array([np.mean([reference[i] for i in groups[family]]) for family in family_ids])
    rng = np.random.default_rng(SEED)
    draws = rng.integers(0, len(family_ids), size=(BOOTSTRAP_REPLICATES, len(family_ids)))
    estimates = {}
    for weighting in ("family_equal", "system_equal"):
        if weighting == "family_equal":
            observed_point = float(observed_means.mean())
            reference_point = float(reference_means.mean())
            boot_observed = observed_means[draws].mean(axis=1)
            boot_reference = reference_means[draws].mean(axis=1)
        else:
            observed_point = float(np.average(observed_means, weights=counts))
            reference_point = float(np.average(reference_means, weights=counts))
            denominator = counts[draws].sum(axis=1)
            boot_observed = (observed_means[draws] * counts[draws]).sum(axis=1) / denominator
            boot_reference = (reference_means[draws] * counts[draws]).sum(axis=1) / denominator
        estimates[weighting] = {"observed_violation_rate": observed_point,
                               "observed_ci95": [float(x) for x in np.quantile(boot_observed, [.025, .975])],
                               "reference_violation_rate": reference_point,
                               "observed_minus_reference": observed_point - reference_point,
                               "difference_ci95": [float(x) for x in np.quantile(boot_observed - boot_reference, [.025, .975])],
                               "violation_rate_ratio": observed_point / reference_point if reference_point else None}
    return estimates


def subset_definitions(systems):
    subsets = {"overall": systems}
    subsets.update({name: [system for system in systems if system["family_group"] != family] for name, family in FAMILY_REMOVALS.items()})
    subsets.update({("missing_macroarea" if area == "Unknown" else "macroarea:" + area): [system for system in systems if system["macroarea"] == area] for area in sorted({system["macroarea"] for system in systems})})
    return subsets


def p1_analysis(systems, catalogue, nulls, table_rows):
    results = {}
    for indicator_key, null in nulls.items():
        feature_set, definition = indicator_key.split("_")[1], indicator_key.split("_")[0]
        variants = {}
        for subset_name, subset in subset_definitions(systems).items():
            observed = [int(not catalogue[system["structure_key"]]["indicators"][indicator_key]) for system in subset]
            conditioned = [null["shape_violation_probability"][tuple(catalogue[system["structure_key"]]["shape"])] for system in subset]
            uniform = [null["uniform_violation_probability"]] * len(subset)
            baseline_results = {"uniform_all_partitions": grouped_bootstrap(subset, observed, uniform), "fixed_block_sizes": grouped_bootstrap(subset, observed, conditioned)}
            supports = all(result["family_equal"]["difference_ci95"][1] < 0 for result in baseline_results.values())
            variants[subset_name] = {"n_systems": len(subset), "n_families": len({system["family_group"] for system in subset}),
                                     "violating_systems": int(sum(observed)), "baselines": baseline_results,
                                     "two_baseline_family_equal_direction_supported": supports}
            for baseline_name, estimates in baseline_results.items():
                for weighting, estimates_one in estimates.items():
                    table_rows.append({"prediction": "P1", "definition": definition, "feature_set": feature_set, "metric": "violation_rate", "method": baseline_name, "weighting": weighting, "subset": subset_name, "n_systems": len(subset), "n_families": variants[subset_name]["n_families"], "estimate": estimates_one["observed_violation_rate"], "ci_low": estimates_one["observed_ci95"][0], "ci_high": estimates_one["observed_ci95"][1], "reference": estimates_one["reference_violation_rate"], "difference": estimates_one["observed_minus_reference"], "difference_ci_low": estimates_one["difference_ci95"][0], "difference_ci_high": estimates_one["difference_ci95"][1], "rate_ratio": estimates_one["violation_rate_ratio"]})
        results[indicator_key] = {"definition": definition, "feature_set": feature_set,
                                  "primary": indicator_key == "A_four", "null_accepted_partitions": null["accepted_partitions"],
                                  "subsets": variants}
    return results


def direction_value(diagnostics, prediction, method):
    return diagnostics["secondary_diagnostics"][prediction][method]


def direction_summary(systems, catalogue, prediction, method):
    family_directions = defaultdict(Counter)
    area_directions = defaultdict(Counter)
    counts = Counter()
    ambiguous_trees = []
    for system in systems:
        diagnosis = catalogue[system["structure_key"]]
        direction = direction_value(diagnosis, prediction, method)
        counts[direction] += 1
        if diagnosis["secondary_diagnostics"][prediction]["tree_direction_ambiguous_without_edge_filter"]:
            ambiguous_trees.append(system["Language_ID"])
        if direction in ("predicted_side", "opposite_side"):
            family_directions[system["family_group"]][direction] += 1
            area_directions[system["macroarea"]][direction] += 1
    votes, ties = Counter(), []
    family_rows = []
    for family, counter in sorted(family_directions.items()):
        predicted, opposite = counter["predicted_side"], counter["opposite_side"]
        direction = "predicted_majority" if predicted > opposite else "opposite_majority" if opposite > predicted else "tie"
        votes[direction] += 1
        if direction == "tie":
            ties.append(family)
        family_rows.append({"family_group": family, "predicted_systems": predicted, "opposite_systems": opposite, "majority": direction})
    trials = votes["predicted_majority"] + votes["opposite_majority"]
    successes = votes["predicted_majority"]
    pvalue = float(binomtest(successes, trials, .5, alternative="greater").pvalue) if trials else None
    adjusted = min(1., 3 * pvalue) if pvalue is not None else None
    areas = []
    for area, counter in sorted(area_directions.items()):
        predicted, opposite = counter["predicted_side"], counter["opposite_side"]
        areas.append({"macroarea": area, "predicted_systems": predicted, "opposite_systems": opposite,
                      "majority": "predicted" if predicted > opposite else "opposite" if opposite > predicted else "tie"})
    named_areas = [row for row in areas if row["macroarea"] != "Unknown"]
    return {"n_systems": len(systems), "n_families_total": len({s["family_group"] for s in systems}),
            "systems_predicted": counts["predicted_side"], "systems_opposite": counts["opposite_side"],
            "systems_not_applicable": counts["not_applicable"], "systems_structurally_ambiguous_main": 0,
            "systems_with_multiple_tree_sides_before_edge_filter": len(ambiguous_trees),
            "ambiguous_tree_system_ids": ambiguous_trees,
            "relevant_families_including_ties": len(family_directions), "family_ties": len(ties),
            "family_tie_ids": ties, "families_predicted_majority": successes,
            "families_opposite_majority": votes["opposite_majority"], "binomial_trials": trials,
            "predicted_family_proportion": successes / trials if trials else None,
            "exact_binomial_p_one_sided": pvalue, "bonferroni_three_p": adjusted,
            "direction_supported": adjusted is not None and adjusted < .05 and successes / trials > .5,
            "family_direction_rows": family_rows, "macroarea_directions": named_areas,
            "unknown_macroarea_direction": next((row for row in areas if row["macroarea"] == "Unknown"), None),
            "macroareas_with_related_systems": len(named_areas),
            "macroareas_predicted_majority": sum(row["majority"] == "predicted" for row in named_areas),
            "macroareas_opposite_majority": sum(row["majority"] == "opposite" for row in named_areas),
            "macroareas_tied": sum(row["majority"] == "tie" for row in named_areas)}


def p2_p4_analysis(systems, catalogue, table_rows):
    methods = ("strict_direction", "unfiltered_edge_direction", "parent_filtered_edge_direction")
    results = {}
    for prediction in ("P2", "P3", "P4"):
        results[prediction] = {}
        for method in methods:
            subsets = {}
            for subset_name, subset in subset_definitions(systems).items():
                result = direction_summary(subset, catalogue, prediction, method)
                subsets[subset_name] = result
                table_rows.append({"prediction": prediction, "definition": "strict_structure" if method == "strict_direction" else "edge_proxy", "feature_set": "four", "metric": "direction", "method": method, "weighting": "family_majority", "subset": subset_name,
                                   "n_systems": len(subset), "n_families": result["n_families_total"],
                                   "predicted_systems": result["systems_predicted"], "opposite_systems": result["systems_opposite"],
                                   "predicted_families": result["families_predicted_majority"], "opposite_families": result["families_opposite_majority"],
                                   "family_ties": result["family_ties"], "binomial_trials": result["binomial_trials"],
                                   "p_one_sided": result["exact_binomial_p_one_sided"], "p_bonferroni": result["bonferroni_three_p"], "supported": result["direction_supported"]})
            results[prediction][method] = subsets
    return results


def p5_analysis(systems, catalogue, table_rows):
    result = {}
    for subset_name, subset in subset_definitions(systems).items():
        statuses = Counter(catalogue[system["structure_key"]]["P5"]["status"] for system in subset)
        result[subset_name] = {"n_systems": len(subset), "status_counts": dict(statuses),
                               "families_by_status": {status: len({s["family_group"] for s in subset if catalogue[s["structure_key"]]["P5"]["status"] == status}) for status in statuses},
                               "systems_with_representation_ambiguity": sum(catalogue[s["structure_key"]]["P5"]["representation_ambiguous"] for s in subset),
                               "incompatible_system_ids": [s["Language_ID"] for s in subset if catalogue[s["structure_key"]]["P5"]["status"] == "incompatible_all_trees_require_early_feature"],
                               "strict_database_universal_compatible_with_all_tree_applicable_records": statuses["incompatible_all_trees_require_early_feature"] == 0,
                               "interpretation": "无树者单列不适用；兼容表示存在不说明实际心理表示，明确不兼容仍需原始字段复核。"}
        for status, count in statuses.items():
            table_rows.append({"prediction": "P5", "definition": "B", "feature_set": "four", "metric": "tree_compatibility_status", "method": "all_legal_tree_search", "weighting": "system_count", "subset": subset_name,
                               "n_systems": len(subset), "n_families": len({s["family_group"] for s in subset}),
                               "tree_status": status, "status_systems": count,
                               "status_families": result[subset_name]["families_by_status"][status]})
    return result


def old_secondary_check(pairs, systems, catalogue):
    cells = ("001", "010", "011", "100", "101", "110", "111")
    signature = (4, 0, 0, 2, 2, 0, 0)
    full_old = set()
    for language_id, rows in pairs.items():
        counts = Counter()
        for row in rows:
            counts[row["pattern"]] += int(row["shared_form"])
        if tuple(counts[cell] for cell in cells) == signature:
            shared_ages = {row["category_a"][1] for row in rows if row["pattern"] == "100" and row["shared_form"] == "1"}
            if shared_ages == {"y"}:
                full_old.add(language_id)
    d3_ids = {system["Language_ID"] for system in systems}
    strict_d3 = {system["Language_ID"] for system in systems if catalogue[system["structure_key"]]["strict_directions"]["P2"] == "predicted_side"}
    original = json.loads((ROOT / "analysis/forum_descriptives.json").read_text())
    stored = original["secondary_distinctions"]["sex_distinguished_for_elder_only"]["languages"]
    if len(full_old) != stored or stored != 84:
        raise RuntimeError("旧939系统84项描述统计未精确复现")
    return {"old_full_sample_systems": len(pairs), "stored_old_count": stored, "recomputed_old_count": len(full_old),
            "old_signature_in_D3": len(full_old & d3_ids), "old_signature_excluded_by_D3": len(full_old - d3_ids),
            "strict_P2_predicted_in_D3": len(strict_d3),
            "old_D3_but_not_strict_ids": sorted((full_old & d3_ids) - strict_d3),
            "strict_but_not_old_signature_ids": sorted(strict_d3 - full_old),
            "extra_strict_system_explanation": "四条额外记录均允许年长一性别内部的参照者三级细分，严格树见证保留此细分，旧精确七单元签名不容纳它；若微小转写差异造成该细分，须在原始字段审查中说明。",
            "explanation": "84基于全部939系统的特定七单元共享签名；S2限制625个单词形系统并要求根与子根兼容，样本和规则均须逐项对照。"}


def write_violations(systems):
    rows = []
    violating_systems = [system for system in systems if system["violations"]]
    audit_sample = violating_systems[:20]
    chosen = {system["Language_ID"] for system in audit_sample}
    for system in violating_systems:
        propositions = ";".join(violation["proposition"] for violation in system["violations"])
        reasons = {violation["proposition"]: violation["reason"] for violation in system["violations"]}
        features = {violation["proposition"]: violation["feature"] for violation in system["violations"]}
        for raw in system["raw_records"]:
            rows.append({"Language_ID": system["Language_ID"], "Glottocode": system["Glottocode"], "Name": system["Name"],
                         "family_group": system["family_group"], "family_name": system["family_name"], "Macroarea": system["macroarea"],
                         "proposition": propositions, "category": raw["Parameter_ID"], "feature": json.dumps(features, ensure_ascii=False),
                         "violation_reason": json.dumps(reasons, ensure_ascii=False), "selected_for_field_audit": system["Language_ID"] in chosen,
                         **raw})
    fieldnames = ["Language_ID", "Glottocode", "Name", "family_group", "family_name", "Macroarea", "proposition", "category", "feature", "violation_reason", "selected_for_field_audit", "ID", "Parameter_ID", "Value", "Form", "Comment", "Source"]
    with (OUT / "s2_violations.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return {"violating_systems_any_listed_definition": len(violating_systems), "source_record_rows": len(rows),
            "audit_selection_rule": "全体列出的违例按Glottocode、Language_ID固定顺序取前20个不同系统；含主、敏感性与三特征参照定义，具体命题逐项保留。",
            "selected_audit_systems": [{key: system[key] for key in ("Language_ID", "Glottocode", "family_group", "family_name", "macroarea", "violations")} for system in audit_sample]}


def write_table(rows):
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with (OUT / "s2_partition_tests.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def independent_checks(systems, catalogue, p1, directions, p5):
    """以闭包、树列表与二项组合尾和独立核查主要实现。"""
    block_checks, direction_checks, pvalue_checks = 0, 0, 0
    for system in systems:
        diagnosis = catalogue[system["structure_key"]]
        partition = diagnosis["partition_masks"]
        for feature_set, names in FEATURE_SETS.items():
            acceptable = True
            for block in partition:
                indices = [i for i in range(8) if block & (1 << i)]
                constants = [(name, FEATURES[name][indices[0]]) for name in names if len({FEATURES[name][i] for i in indices}) == 1]
                closure = sum(1 << i for i in range(8) if all(FEATURES[name][i] == value for name, value in constants))
                acceptable &= closure == block
                block_checks += 1
            if acceptable != diagnosis["indicators"][f"A_{feature_set}"]:
                raise RuntimeError("独立特征常量闭包与合取穷举不一致")
        for prediction, parent, target in (("P2", "a", "r"), ("P3", "r", "a"), ("P4", "q", "a")):
            current = diagnosis["secondary_diagnostics"][prediction]
            edge_side = current["edge_secondary_side"]
            def contains_target(tree):
                return tree[0] != "leaf" and (tree[0] == target or contains_target(tree[1]) or contains_target(tree[2]))
            matching = []
            if edge_side is not None:
                for tree in diagnosis["all_four_feature_single_leaf_trees"]:
                    if tree[0] != parent:
                        continue
                    branch, opposite = tree[1 + edge_side], tree[2 - edge_side]
                    if branch[0] == target and not contains_target(opposite):
                        matching.append(tree)
            expected = "predicted_side" if matching and edge_side == 0 else "opposite_side" if matching and edge_side == 1 else "not_applicable"
            if expected != diagnosis["strict_directions"][prediction]:
                raise RuntimeError("全部树列表与严格方向见证不一致")
            direction_checks += 1
    for prediction in ("P2", "P3", "P4"):
        for method, subsets in directions[prediction].items():
            for value in subsets.values():
                trials, successes = value["binomial_trials"], value["families_predicted_majority"]
                if trials:
                    tail = sum(comb(trials, k) for k in range(successes, trials + 1)) / 2**trials
                    if abs(tail - value["exact_binomial_p_one_sided"]) > 1e-14:
                        raise RuntimeError("组合尾和与精确二项p不一致")
                    pvalue_checks += 1
    for value in p1.values():
        for subset in value["subsets"].values():
            for weighting, estimate in subset["baselines"]["uniform_all_partitions"].items():
                reference = estimate["reference_violation_rate"]
                if max(abs((observed - reference) - difference) for observed, difference in zip(estimate["observed_ci95"], estimate["difference_ci95"])) > 1e-12:
                    raise RuntimeError("固定均匀基准的bootstrap区间平移关系不一致")
    if sum(p5["overall"]["status_counts"].values()) != len(systems):
        raise RuntimeError("P5状态计数未覆盖所有D3系统")
    return {"passed": True, "independent_block_closure_checks": block_checks,
            "all_tree_strict_direction_checks": direction_checks, "binomial_tail_sum_checks": pvalue_checks,
            "constant_null_interval_translation": True, "P5_full_state_coverage": True}


def percent(value):
    return f"{100 * value:.1f}%"


def write_report(result):
    p1 = result["P1"]["A_four"]["subsets"]["overall"]
    text = ["# 补充分析S2：划分层面P1–P5", "", "## 运行前指定的结果", "",
            f"最终协议提交`{PROTOCOL_COMMIT}`，SHA-256 `{PROTOCOL_SHA256}`。本分析为已知冻结结果与S1后的补充分析，不能解释为预注册。主样本{result['sample']['full_systems']}个记录系统，D3为{result['sample']['D3_systems']}个系统、{result['sample']['D3_families']}个谱系组。",
            "", "### P1：四特征任意合取主定义", "",
            f"共有{p1['violating_systems']}个D3系统含非合取词项。系统等权与谱系等权、两个精确随机参照如下；区间均为5000次整谱系重抽样的95%百分位区间。", "",
            "|参照|权重|观测非合取比例|观测−参照|差值95%区间|率比|", "|---|---|---:|---:|---|---:|"]
    for baseline, values in p1["baselines"].items():
        for weighting, value in values.items():
            ci = value["difference_ci95"]
            ratio = "未定义" if value["violation_rate_ratio"] is None else f"{value['violation_rate_ratio']:.4f}"
            text.append(f"|{baseline}|{weighting}|{percent(value['observed_violation_rate'])}|{value['observed_minus_reference']:.4f}|[{ci[0]:.4f}, {ci[1]:.4f}]|{ratio}|")
    text.extend(["", f"依协议两参照同时判断，P1主方向{'得到支持' if p1['two_baseline_family_equal_direction_supported'] else '未得到整体支持'}。该结果描述固定词形测量下的记录，不等于所有语言的普遍语义约束。三／四／六特征、任意合取与单叶递归树、区域及去除两个大型谱系的全部结果见JSON和CSV。", "", "### P2–P4：严格结构方向", "", "|预测|预测侧系统|相反侧系统|预测侧多数谱系|相反侧多数谱系|平局谱系|原始单侧p|Bonferroni p|", "|---|---:|---:|---:|---:|---:|---:|---:|"])
    for prediction in ("P2", "P3", "P4"):
        value = result["P2_P4"][prediction]["strict_direction"]["overall"]
        p = "未定义" if value["exact_binomial_p_one_sided"] is None else f"{value['exact_binomial_p_one_sided']:.6g}"
        adjusted = "未定义" if value["bonferroni_three_p"] is None else f"{value['bonferroni_three_p']:.6g}"
        text.append(f"|{prediction}|{value['systems_predicted']}|{value['systems_opposite']}|{value['families_predicted_majority']}|{value['families_opposite_majority']}|{value['family_ties']}|{p}|{adjusted}|")
    text.extend(["", "主判定同时要求目标最小对恰两条且同侧、父根与目标子根不切开词项，以及完整单叶递归见证。未过滤边侧和父特征四边代理完整并报；它们不能替代主结构判定。平局谱系不进入精确二项分母。区域与大型谱系剔除的结果均为预先指定的边界检查。", "", "### P5：四特征合法树的存在性", ""])
    p5 = result["P5"]["overall"]
    for status, count in p5["status_counts"].items():
        text.append(f"- `{status}`：{count}个系统。")
    text.extend(["", "无树者不再算独立P5违例；兼容树存在只说明表示上可兼容。全部树、兼容树、深度集合及具体见证按结构模板存入partition_systems.json。明确不兼容记录须结合原始字段审查，不能直接宣称发现真实语言的心理或语义普遍律反例。", "", "### 旧84项描述与D3核对", ""])
    old = result["old_84_consistency"]
    text.append(f"在原939系统上精确重现旧描述{old['recomputed_old_count']}项；其中{old['old_signature_in_D3']}项进入625系统D3，{old['old_signature_excluded_by_D3']}项因每类并非单一词形被排除。D3严格P2预测侧为{old['strict_P2_predicted_in_D3']}项；规则差异对应ID清单已保存。{old['extra_strict_system_explanation']}")
    text.extend(["", "### 违例字段与抽查接口", "", f"全体列出定义的违例共{result['violation_audit_selection']['violating_systems_any_listed_definition']}个不同系统，保留{result['violation_audit_selection']['source_record_rows']}行原始ID、Value、Form、Comment、Source。按Glottocode与Language_ID固定顺序选择{len(result['violation_audit_selection']['selected_audit_systems'])}个系统交字段复核；不能把未确定的测量解释填写为已证实的语义事实。", "", "## 运行后观察", "", "本节不追加未指定的假设检验。字段抽查分类由独立数据复核输出提供；此报告不代填尚未完成的人工核查结果。", "", "## 验证与范围", "", "类别名称按KINTYPES明确对齐；每个主系统八类、28对及原始共享指标均复算一致。P5全部树的独立列表与纯理论模块计数一致。所有输入与输出哈希、协议提交、开始结束时间及随机种子保存于结果JSON。原冻结分析和S1未改写。"])
    (OUT / "partition_report.md").write_text("\n".join(text) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze-reproduction", type=Path, required=True, help="root提供的冻结复现passed=true JSON")
    arguments = parser.parse_args()
    guard = protocol_guard()
    preflight = json.loads(arguments.freeze_reproduction.read_text())
    if preflight.get("passed") is not True:
        raise RuntimeError("冻结复现前置记录未明确passed=true，停止运行")
    if preflight.get("protocol_commit") != PROTOCOL_COMMIT or preflight.get("protocol_sha256") != PROTOCOL_SHA256:
        raise RuntimeError("冻结复现记录未关联最终协议")
    started = utc_now()
    pairs, forms, metadata, raw_records = load_inputs()
    systems, catalogue = prepare_systems(forms, metadata, raw_records)
    print(f"D3 {len(systems)} systems; {len(catalogue)} distinct partitions", flush=True)
    audit = write_violations(systems)
    system_output = {"protocol": guard, "category_order": list(CATEGORY_ORDER), "kintype_order": list(KINTYPES),
                     "systems": systems, "structure_catalogue": catalogue, "violation_audit_selection": audit}
    (OUT / "partition_systems.json").write_text(json.dumps(system_output, ensure_ascii=False, indent=2), encoding="utf-8")
    print("原始字段违例CSV与前20系统名单已保存", flush=True)
    table_rows = []
    nulls = exact_nulls()
    p1 = p1_analysis(systems, catalogue, nulls, table_rows)
    directions = p2_p4_analysis(systems, catalogue, table_rows)
    p5 = p5_analysis(systems, catalogue, table_rows)
    old = old_secondary_check(pairs, systems, catalogue)
    validation = independent_checks(systems, catalogue, p1, directions, p5)
    inputs = [ROOT / "analysis/pairs_primary.csv", ROOT / "analysis/category_forms_primary.csv", ROOT / "data/kinbank/kinbank/cldf/forms.csv"]
    result = {"analysis": "S2_D3_partition_P1_P5", "posthoc_supplement": True, "protocol": guard,
              "freeze_reproduction_record": str(arguments.freeze_reproduction), "freeze_reproduction_sha256": sha256(arguments.freeze_reproduction),
              "started_at": started, "completed_at": utc_now(), "seed": SEED, "bootstrap_replicates": BOOTSTRAP_REPLICATES,
              "sample": {"full_systems": len(pairs), "full_families": len({m['family_group'] for m in metadata.values()}),
                         "D3_systems": len(systems), "D3_families": len({s['family_group'] for s in systems}),
                         "D3_macroarea_counts": dict(Counter(s['macroarea'] for s in systems)),
                         "full_unknown_macroarea_systems": sum(m['macroarea'] == 'Unknown' for m in metadata.values()),
                         "multi_macroarea_system_ids": [m['Language_ID'] for m in metadata.values() if ';' in m['macroarea_raw']]},
              "P1": p1, "P2_P4": directions, "P5": p5, "old_84_consistency": old,
              "independent_implementation_checks": validation,
              "violation_audit_selection": audit, "input_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in inputs},
              "interpretation": "谱系整组区间条件于固定数据库与测量定义；区域接触和源记录测量误差仍需保留。"}
    write_table(table_rows)
    (OUT / "partition_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(result)
    print(json.dumps({"D3_systems": len(systems), "D3_families": result['sample']['D3_families'], "P1_primary": p1['A_four']['subsets']['overall'], "P2_P4_strict": {p: directions[p]['strict_direction']['overall'] for p in ('P2','P3','P4')}, "P5": p5['overall'], "old_84": old}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
