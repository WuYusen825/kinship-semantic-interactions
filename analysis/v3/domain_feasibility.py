"""T6第一步：只审计跨域编码、词形与来源覆盖，不计算结构指标或关联。"""
from __future__ import annotations

from collections import Counter, defaultdict
from itertools import product
from pathlib import Path
import json
import re
import unicodedata

import pandas as pd

from common import ROOT, RESULTS, logged_run, save_json, sha256, utc_now, verify_analysis_plan


RAW = ROOT / "data/kinbank/kinbank/cldf"
OUT = RESULTS / "t6"
INVALID = {"", "?", "-"}


def normalize_form(value):
    return " ".join(unicodedata.normalize("NFC", str(value)).split())


def source_ids(value):
    return frozenset(clean for part in str(value).split(";")
                     if (clean := re.sub(r"\[[^\]]*\]", "", part).strip()))


def domain_registry():
    """显式ego前缀与实际编码；不从generic、另一ID或年龄亚类补格。"""
    return {
        "cousins16": [{"Parameter_ID": e+p+c+r, "s": s, "p": side,
                       "c": link, "r": sex}
                      for (s,e),(side,p),(link,c),(sex,r) in product(
                          enumerate("mf"), enumerate("FM"), enumerate("BZ"), enumerate("SD"))],
        "parent_siblings_age16": [{"Parameter_ID": e+p+a+r, "s": s, "p": side,
                                  "a_parent": age, "r": sex}
                                 for (s,e),(side,p),(age,a),(sex,r) in product(
                                     enumerate("mf"), enumerate("FM"), enumerate("ey"), enumerate("BZ"))],
        "parent_siblings_generic8": [{"Parameter_ID": e+p+r, "s": s, "p": side, "r": sex}
                                    for (s,e),(side,p),(sex,r) in product(
                                        enumerate("mf"), enumerate("FM"), enumerate("BZ"))],
    }


def collect_cells(frame, language_ids, parameter_ids):
    """保留原始行；同ID/参数的有效Form按原主规则取集合。"""
    cells = defaultdict(lambda: {"forms": set(), "sources": set(), "source_forms": defaultdict(set),
                                 "rows": [], "invalid_rows": 0, "missing_source_rows": 0})
    for row in frame[frame.Language_ID.isin(language_ids) & frame.Parameter_ID.isin(parameter_ids)].to_dict("records"):
        cell = cells[(row["Language_ID"], row["Parameter_ID"])]
        form = normalize_form(row["Form"])
        row = {**row, "normalized_form": form}
        cell["rows"].append(row)
        if form in INVALID:
            cell["invalid_rows"] += 1
            continue
        cell["forms"].add(form)
        sources = source_ids(row["Source"])
        cell["sources"].update(sources)
        cell["missing_source_rows"] += int(not sources)
        for source in sources:
            cell["source_forms"][source].add(form)
    return cells


def coverage_for_system(language_id, codes, cells):
    found = [cells.get((language_id, code), {}) for code in codes]
    counts = [len(cell.get("forms", ())) for cell in found]
    source_sets = [cell.get("sources", set()) for cell in found]
    common = set.intersection(*(set(sources) for sources in source_sets)) if source_sets else set()
    common_singleton = [source for source in sorted(common)
                        if all(len(cell.get("source_forms", {}).get(source, ())) == 1 for cell in found)]
    return {"required_cells": len(codes), "valid_cells": sum(count > 0 for count in counts),
            "singleton_cells": sum(count == 1 for count in counts),
            "complete": all(count > 0 for count in counts), "complete_singleton": all(count == 1 for count in counts),
            "missing_codes": [code for code,count in zip(codes,counts) if not count],
            "multiple_form_codes": [code for code,count in zip(codes,counts) if count > 1],
            "common_sources": sorted(common), "common_singleton_sources": common_singleton,
            "has_common_source_complete": bool(common), "has_common_source_singleton": bool(common_singleton),
            "missing_source_valid_rows": sum(cell.get("missing_source_rows", 0) for cell in found),
            "invalid_rows": sum(cell.get("invalid_rows", 0) for cell in found)}


def cohort_summary(rows):
    full = [row for row in rows if row["complete"]]
    singleton = [row for row in rows if row["complete_singleton"]]
    families = Counter(row["family_group"] for row in singleton if row["family_group"])
    return {"systems": len(rows), "families": len({row["family_group"] for row in rows if row["family_group"]}),
            "complete_systems": len(full), "complete_singleton_systems": len(singleton),
            "complete_singleton_families": len(families),
            "families_with_at_least_two_complete_singleton_systems": sum(count >= 2 for count in families.values()),
            "systems_in_repeated_complete_singleton_families": sum(count for count in families.values() if count >= 2),
            "complete_singleton_common_source_systems": sum(row["has_common_source_complete"] for row in singleton),
            "any_common_source_complete_systems": sum(row["has_common_source_complete"] for row in rows),
            "any_common_source_singleton_systems": sum(row["has_common_source_singleton"] for row in rows),
            "valid_cell_count_distribution": dict(sorted(Counter(row["valid_cells"] for row in rows).items())),
            "singleton_cell_count_distribution": dict(sorted(Counter(row["singleton_cells"] for row in rows).items())),
            "missing_macroarea_complete_singleton_systems": sum(not row["macroarea"] for row in singleton),
            "complete_singleton_by_macroarea": dict(sorted(Counter(row["macroarea"] or "missing" for row in singleton).items()))}


def main():
    guard = verify_analysis_plan(require_t1=True)
    specification = {"stage": "feasibility_only", "no_structural_metrics": True, "no_cross_domain_associations": True,
                     "selection": "冻结原selected Language_ID，另列main939及strict625交集",
                     "form_rule": "Form的NFC及空白规范化，排除空、问号、连字符；同ID有效集合并集",
                     "source_rule": "仅移除Source方括号定位并按分号拆分；来源交集另列，不改主并集词形"}
    with logged_run("T6_feasibility", specification) as metrics:
        OUT.mkdir(parents=True, exist_ok=True)
        parameters = pd.read_csv(RAW / "parameters.csv", keep_default_na=False)
        frame = pd.read_csv(RAW / "forms.csv", keep_default_na=False)
        selected = pd.read_csv(ROOT / "analysis/selected_languages_structural.csv", keep_default_na=False).rename(columns={"ID": "Language_ID"})
        main_ids = set(pd.read_csv(ROOT / "analysis/pairs_primary.csv", usecols=["Language_ID"]).Language_ID)
        strict_ids = set(pd.read_csv(RESULTS / "t1/systems_to_partition.csv", usecols=["Language_ID"]).Language_ID)
        selected_ids = set(selected.Language_ID)
        if not strict_ids <= main_ids <= selected_ids or len(main_ids) != 939 or len(strict_ids) != 625:
            raise RuntimeError("冻结样本ID关系或规模不符")
        cohorts = {"original_selected": selected_ids, "main939": main_ids, "strict625": strict_ids}
        registry = domain_registry()
        needed = {row["Parameter_ID"] for rows in registry.values() for row in rows}
        if not needed <= set(parameters.ID):
            raise RuntimeError("候选域存在未登记参数，不能补格")
        cells = collect_cells(frame, selected_ids, needed)
        systems, raw_rows, cell_rows, registry_rows = [], [], [], []
        for domain, entries in registry.items():
            codes = [row["Parameter_ID"] for row in entries]
            for entry in entries:
                registry_rows.append({"domain": domain, **entry,
                                      "Name": parameters.set_index("ID").loc[entry["Parameter_ID"], "Name"]})
            for row in selected.to_dict("records"):
                lid = row["Language_ID"]
                macroarea = str(row.get("Macroarea", "")).split(";")[0].strip()
                systems.append({"domain": domain, "Language_ID": lid, "Glottocode": row["Glottocode"],
                                "family_group": row["family_group"], "family_name": row["family_name"],
                                "macroarea": macroarea, "main939": lid in main_ids, "strict625": lid in strict_ids,
                                **coverage_for_system(lid, codes, cells)})
                for entry in entries:
                    cell = cells.get((lid, entry["Parameter_ID"]), {})
                    cell_rows.append({"domain": domain, "Language_ID": lid, "Glottocode": row["Glottocode"],
                                      **entry, "n_forms": len(cell.get("forms", ())),
                                      "forms_json": json.dumps(sorted(cell.get("forms", ())), ensure_ascii=False),
                                      "sources_json": json.dumps(sorted(cell.get("sources", ())), ensure_ascii=False),
                                      "raw_row_ids_json": json.dumps([v["ID"] for v in cell.get("rows", ())])})
                    raw_rows.extend({"domain": domain, "Glottocode": row["Glottocode"], **raw}
                                    for raw in cell.get("rows", ()))
        summaries = {domain: {cohort: cohort_summary([row for row in systems if row["domain"] == domain and row["Language_ID"] in ids])
                              for cohort, ids in cohorts.items()} for domain in registry}
        sources = [RAW / "parameters.csv", RAW / "forms.csv", ROOT / "analysis/selected_languages_structural.csv",
                   ROOT / "analysis/pairs_primary.csv", RESULTS / "t1/systems_to_partition.csv"]
        result = {"task": "T6_feasibility", "created_at": utc_now(), "guard": guard, "specification": specification,
                  "parameter_count": len(parameters), "cohort_sizes": {key: len(ids) for key,ids in cohorts.items()},
                  "domains": summaries, "registry": registry,
                  "input_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in sources},
                  "interpretation": "覆盖仅指数据库目标代码和单词形齐全；不证明原文献独立调查各ego、年龄和性别格，不构成q使用或跨域可复用性证据。"}
        save_json(OUT / "coverage_results.json", result)
        pd.DataFrame([{**row, **{key: json.dumps(row[key], ensure_ascii=False) for key in
                                ("missing_codes", "multiple_form_codes", "common_sources", "common_singleton_sources")}}
                      for row in systems]).to_csv(OUT / "coverage_systems.csv", index=False)
        pd.DataFrame(cell_rows).to_csv(OUT / "coverage_cells.csv", index=False)
        pd.DataFrame(raw_rows).to_csv(OUT / "coverage_raw_records.csv", index=False)
        pd.DataFrame(registry_rows).to_csv(OUT / "domain_cell_coding.csv", index=False)
        lines = ["# T6：跨领域编码与覆盖可行性", "", "本阶段仅审计覆盖，未计算领域划分的q指标、跨领域关联、回归或置换结果。", "",
                 "|领域|样本层|完整／单词形系统|单词形谱系|至少2个单词形系统的谱系|单词形且全域同一来源系统|", "|---|---|---:|---:|---:|---:|"]
        for domain, layers in summaries.items():
            for cohort, value in layers.items():
                lines.append(f"|{domain}|{cohort}|{value['complete_systems']}／{value['complete_singleton_systems']}|{value['complete_singleton_families']}|{value['families_with_at_least_two_complete_singleton_systems']}|{value['complete_singleton_common_source_systems']}|")
        lines.extend(["", "完整仅指每个固定目标编码至少一有效词形；单词形要求每格有效词形集合恰含一项。全域同一来源要求每格至少一个有效Form获得相同Source键支持。该规则不证明来源确曾独立调查全部细格。", "", "三领域不互相补格；无ego前缀代码不复制至m/f，长幼亚类不合并成generic，也不从同一Glottocode的另一Language_ID拼接。年龄16格中的长幼相对父／母，不能称为所指者相对ego的年龄。", "", "cousins16的父母侧p和中介兄妹性别c可组成cross/parallel p⊕c，与ego／referent相对性别q=s⊕r不同。绝对非合取不是q使用的专属指标。", "", "后续精确定义见docs/t6_operationalization.md；关联结果须在单独补充计划冻结后运行。来源、原始Value/Form/Comment/Source和全部空格均保留供核查。"])
        (OUT / "feasibility_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        metrics.update({"cohort_sizes": result["cohort_sizes"], "complete_singleton_strict":
                        {domain: layers["strict625"]["complete_singleton_systems"] for domain,layers in summaries.items()},
                        "association_run": False})
        print(json.dumps(metrics, ensure_ascii=False))


if __name__ == "__main__":
    main()
