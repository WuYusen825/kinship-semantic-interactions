"""T4新位置配置对照；沿用旧严格P2–P4，不改写其定义。

运行须通过已提交分析计划、T0与T1执行门。统计对象为严格八类划分。
"""
from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
import json

import numpy as np
import pandas as pd
from scipy.stats import binomtest

from common import (ATOMS, BOOTSTRAP_REPLICATES, RESULTS, SEED, git_commit,
                    load_system_mapping, logged_run, save_json, sha256,
                    utc_now, verify_analysis_plan)
from partitions import strict_direction_vector


AGE_CONFIGS = ("MM", "MF", "FM", "FF")
GENDER_CONFIGS = ("ME", "MY", "FE", "FY")
CONTRAST_IDS = ("A_i", "A_ii", "A_iii", "A_iv", "G_male_ego", "G_female_ego")
CONTRAST_LABELS = {
    "A_i": "仅同性配置／仅异性配置", "A_ii": "仅男男／仅女女",
    "A_iii": "仅女男／仅男女", "A_iv": "仅男性所指者／仅女性所指者",
    "G_male_ego": "男性参照者：年长侧／年幼侧性别区分",
    "G_female_ego": "女性参照者：年长侧／年幼侧性别区分",
}
EQUIVALENCE_MARGIN = .15
OUT = RESULTS / "t4"


def _label_lookup(labels, atoms=ATOMS):
    if len(labels) != 8 or len(atoms) != 8 or len(set(atoms)) != 8:
        raise ValueError("需八个标签与八个不同(s,a,r)坐标")
    if set(atoms) != set(ATOMS):
        raise ValueError("坐标必须覆盖完整三维二元立方体")
    return {tuple(atom): label for atom, label in zip(atoms, labels)}


def age_distinction_set(labels, atoms=ATOMS):
    """新的A集合：同ego/referent配置中，长幼是否落入不同词项。"""
    lookup = _label_lookup(labels, atoms)
    return frozenset("MF"[s] + "MF"[r] for s in (0, 1) for r in (0, 1)
                     if lookup[(s, 0, r)] != lookup[(s, 1, r)])


def gender_distinction_set(labels, atoms=ATOMS):
    """新的G集合：固定ego/长幼，男女所指者是否落入不同词项。"""
    lookup = _label_lookup(labels, atoms)
    return frozenset("MF"[s] + "EY"[a] for s in (0, 1) for a in (0, 1)
                     if lookup[(s, a, 0)] != lookup[(s, a, 1)])


def partial_types(configurations):
    return tuple(frozenset(subset) for size in (1, 2, 3)
                 for subset in combinations(configurations, size))


def type_key(values, configurations=AGE_CONFIGS):
    return "+".join(value for value in configurations if value in values) or "none"


def configuration_contrast(age_set, gender_set, contrast):
    """新对照的+1/−1分别为标题左／右；0排除，不与旧P方向混同。"""
    age_set, gender_set = frozenset(age_set), frozenset(gender_set)
    if contrast == "A_i":
        left = bool(age_set) and age_set <= {"MM", "FF"}
        right = bool(age_set) and age_set <= {"MF", "FM"}
    elif contrast == "A_ii":
        left, right = age_set == {"MM"}, age_set == {"FF"}
    elif contrast == "A_iii":
        left, right = age_set == {"FM"}, age_set == {"MF"}
    elif contrast == "A_iv":
        left = bool(age_set) and age_set <= {"MM", "FM"}
        right = bool(age_set) and age_set <= {"MF", "FF"}
    elif contrast in ("G_male_ego", "G_female_ego"):
        prefix = "M" if contrast == "G_male_ego" else "F"
        elder, younger = prefix + "E" in gender_set, prefix + "Y" in gender_set
        left, right = elder and not younger, younger and not elder
    else:
        raise ValueError("未知预先设定对照：" + contrast)
    if left and right:
        raise AssertionError("同一对照左右必须互斥")
    return 1 if left else -1 if right else 0


def family_modal_partial_type(sets):
    """先对全部14种偏性A取唯一众数；无partial、多众数分开保留。"""
    counts = Counter(frozenset(values) for values in sets if 0 < len(values) < 4)
    if not counts:
        return {"status": "no_partial_age_systems", "modal_type": None,
                "modal_count": 0, "tied_types": [], "partial_systems": 0}
    maximum = max(counts.values())
    winners = sorted((values for values, count in counts.items() if count == maximum), key=type_key)
    return {"status": "unique_modal_type" if len(winners) == 1 else "multiple_modal_types",
            "modal_type": winners[0] if len(winners) == 1 else None,
            "modal_count": maximum, "tied_types": [type_key(values) for values in winners],
            "partial_systems": sum(counts.values())}


def holm_six(pvalues):
    """固定六对照；无可检验分母的p视为1参与排序，但输出仍为空。"""
    if len(pvalues) != 6:
        raise ValueError("Holm校正族必须恰含六个预先设定对照")
    order = sorted(range(6), key=lambda index: 1. if pvalues[index] is None else pvalues[index])
    adjusted, running = [None] * 6, 0.
    for rank, index in enumerate(order):
        value = 1. if pvalues[index] is None else float(pvalues[index])
        running = max(running, min(1., (6 - rank) * value))
        if pvalues[index] is not None:
            adjusted[index] = running
    return adjusted


def bootstrap_ratio(family_counts, weighting, replicates=BOOTSTRAP_REPLICATES, seed=SEED):
    """族整组重抽；保留族内系统数与抽中次数，不重新平衡系统。"""
    values = np.asarray(family_counts, dtype=float)
    if values.size == 0:
        return {"estimate": None, "ci95": None, "families": 0,
                "valid_replicates": 0, "empty_denominator_replicates": replicates,
                "replicates": replicates, "seed": seed}
    if values.ndim != 2 or values.shape[1] != 2 or np.any(values < 0):
        raise ValueError("族计数应为非负[左数,右数]")
    denominator = values.sum(axis=1)
    if weighting == "continuous_family_equal":
        values = values[denominator > 0]
        denominator = values.sum(axis=1)
        if not len(values):
            return bootstrap_ratio([], weighting, replicates, seed)
        per_family = (values[:, 0] - values[:, 1]) / denominator
        estimate = float(per_family.mean())
        indices = np.random.default_rng(seed).integers(0, len(values), size=(replicates, len(values)))
        draws = per_family[indices].mean(axis=1)
        valid = np.ones(replicates, dtype=bool)
    elif weighting in ("system_ratio", "majority_family_ratio", "modal_family_ratio"):
        total = values.sum()
        estimate = float((values[:, 0].sum() - values[:, 1].sum()) / total) if total else None
        indices = np.random.default_rng(seed).integers(0, len(values), size=(replicates, len(values)))
        totals = values[indices].sum(axis=1)
        denominators = totals.sum(axis=1)
        valid = denominators > 0
        draws = np.full(replicates, np.nan)
        draws[valid] = (totals[valid, 0] - totals[valid, 1]) / denominators[valid]
    else:
        raise ValueError(weighting)
    return {"estimate": estimate, "ci95": np.quantile(draws[valid], [.025, .975]).tolist() if valid.any() else None,
            "families": len(values), "valid_replicates": int(valid.sum()),
            "empty_denominator_replicates": int((~valid).sum()), "replicates": replicates, "seed": seed,
            "weighting": weighting, "scope": "固定系统及类型判定后的整谱系重抽；不包含测量或语义重分析。"}


def equivalence_decision(bootstrap_result, margin=EQUIVALENCE_MARGIN):
    interval = bootstrap_result["ci95"]
    if interval is None or bootstrap_result["empty_denominator_replicates"]:
        return {"margin": margin, "supported": False, "status": "not_assessable_empty_denominator"}
    supported = interval[0] > -margin and interval[1] < margin
    return {"margin": margin, "supported": bool(supported),
            "status": "equivalence_supported" if supported else "equivalence_not_established"}


def _family_records(records):
    grouped = defaultdict(list)
    for row in records:
        grouped[row["family_group"]].append(row)
    return dict(sorted(grouped.items()))


def _binomial_summary(left, right):
    total = left + right
    return {"left": left, "right": right, "denominator": total,
            "delta": (left - right) / total if total else None,
            "p_exact_two_sided": float(binomtest(left, total, .5, alternative="two-sided").pvalue) if total else None,
            "direction": "left" if left > right else "right" if right > left else "tie" if total else "no_eligible_units"}


def contrast_statistics(records, contrast, aggregation="system"):
    families = _family_records(records)
    family_rows = []
    counts = Counter()
    all_system_counts = []
    votes = []
    mode_status = Counter()
    for family, members in families.items():
        directions = [configuration_contrast(row["A"], row["G"], contrast) for row in members]
        n_left, n_right = directions.count(1), directions.count(-1)
        all_system_counts.append((n_left, n_right))
        if aggregation == "system":
            counts[1] += n_left; counts[-1] += n_right
            vote = None
        elif aggregation == "family_contrast_majority" or (aggregation == "family_modal_partial_type_sensitivity" and contrast.startswith("G_")):
            vote = 1 if n_left > n_right else -1 if n_right > n_left else 0
            counts[vote] += 1
            mode_status["family_tie" if n_left == n_right and n_left else "no_related_systems" if not n_left + n_right else "determined_majority"] += 1
            if vote:
                votes.append((int(vote == 1), int(vote == -1)))
        elif aggregation == "family_modal_partial_type_sensitivity":
            mode = family_modal_partial_type([row["A"] for row in members])
            mode_status[mode["status"]] += 1
            vote = configuration_contrast(mode["modal_type"], (), contrast) if mode["modal_type"] is not None else 0
            if mode["status"] == "unique_modal_type" and not vote:
                mode_status["unique_modal_type_outside_contrast"] += 1
            counts[vote] += 1
            if vote:
                votes.append((int(vote == 1), int(vote == -1)))
        else:
            raise ValueError(aggregation)
        family_rows.append({"family_group": family, "systems_total": len(members),
                            "left_systems": n_left, "right_systems": n_right,
                            "excluded_systems": len(members) - n_left - n_right,
                            "vote": vote})
    result = _binomial_summary(counts[1], counts[-1])
    result.update({"contrast": contrast, "aggregation": aggregation,
                   "aggregation_detail": "D2仍沿用对照内谱系多数，未新增G众数口径" if aggregation == "family_modal_partial_type_sensitivity" and contrast.startswith("G_") else aggregation,
                   "n_systems": len(records), "n_families": len(families),
                   "eligible_systems": sum(a + b for a, b in all_system_counts),
                   "excluded_systems": sum(len(families[row['family_group']]) - row['left_systems'] - row['right_systems'] for row in family_rows),
                   "excluded_families": len(families) - len(votes) if aggregation != "system" else None,
                   "family_exclusion_status": dict(mode_status), "family_rows": family_rows})
    if aggregation == "system":
        result["bootstrap"] = bootstrap_ratio(all_system_counts, "system_ratio")
    else:
        result["bootstrap"] = bootstrap_ratio(votes, "majority_family_ratio" if aggregation == "family_contrast_majority" else "modal_family_ratio")
    return result


def equivalence_ii_statistics(records):
    majority = contrast_statistics(records, "A_ii", "family_contrast_majority")
    system = contrast_statistics(records, "A_ii", "system")
    continuous = bootstrap_ratio([(row["left_systems"], row["right_systems"]) for row in system["family_rows"]], "continuous_family_equal")
    summaries = {"family_direction_majority_primary": majority["bootstrap"],
                 "system_ratio_sensitivity": system["bootstrap"],
                 "continuous_family_equal_sensitivity": continuous}
    return {name: {**value, **equivalence_decision(value), "primary": name == "family_direction_majority_primary"} for name, value in summaries.items()}


def type_frequencies(records, kind):
    configurations = AGE_CONFIGS if kind == "A" else GENDER_CONFIGS
    families = _family_records(records)
    counts = Counter(row[kind] for row in records)
    rows = []
    for partial in partial_types(configurations):
        family_proportions = [sum(row[kind] == partial for row in members) / len(members) for members in families.values()]
        rows.append({"set_kind": kind, "type": type_key(partial, configurations), "size": len(partial),
                     "systems": counts[partial], "system_fraction_all": counts[partial] / len(records) if records else None,
                     "families_present": sum(any(row[kind] == partial for row in members) for members in families.values()),
                     "family_equal_fraction_all": float(np.mean(family_proportions)) if family_proportions else None})
    return {"n_systems": len(records), "n_partial_systems": sum(0 < len(row[kind]) < 4 for row in records),
            "no_distinction_systems": counts[frozenset()], "full_distinction_systems": counts[frozenset(configurations)],
            "types": rows}


def analyse_subset(records):
    contrasts = {}
    for aggregation in ("system", "family_contrast_majority", "family_modal_partial_type_sensitivity"):
        rows = [contrast_statistics(records, contrast, aggregation) for contrast in CONTRAST_IDS]
        corrected = holm_six([row["p_exact_two_sided"] for row in rows])
        for row, value in zip(rows, corrected):
            row["p_holm_six"] = value
            row["difference_supported_holm"] = value is not None and value < .05
            row["holm_scope"] = "six_predefined_contrasts"
        contrasts[aggregation] = dict(zip(CONTRAST_IDS, rows))
    modal = []
    for family, members in _family_records(records).items():
        value = family_modal_partial_type([row["A"] for row in members])
        value["modal_type"] = type_key(value["modal_type"]) if value["modal_type"] is not None else None
        modal.append({"family_group": family, **value})
    return {"n_systems": len(records), "n_families": len(_family_records(records)),
            "A_types": type_frequencies(records, "A"), "G_types": type_frequencies(records, "G"),
            "contrasts": contrasts, "equivalence_ii": equivalence_ii_statistics(records),
            "family_modal_partial_types": modal}


def _subsets(records):
    result = {"overall": records,
              "excluding_austronesian": [row for row in records if row["family_group"] != "aust1307"],
              "excluding_pama_nyungan": [row for row in records if row["family_group"] != "pama1250"]}
    for area in sorted({row["macroarea"] for row in records}):
        result["macroarea:" + area if area else "missing_macroarea"] = [row for row in records if row["macroarea"] == area]
    return result


def _write_tables(result, records):
    pd.DataFrame([{**{key: value for key, value in row.items() if key not in ("A", "G")},
                   "A": type_key(row["A"]), "G": type_key(row["G"], GENDER_CONFIGS),
                   "A_partial": 0 < len(row["A"]) < 4, "G_partial": 0 < len(row["G"]) < 4} for row in records]).to_csv(OUT / "system_positions.csv", index=False)
    contrast_rows, family_rows, types, modes, equivalence = [], [], [], [], []
    for subset, analysis in result["subsets"].items():
        for kind in ("A", "G"):
            types.extend({"subset": subset, **row} for row in analysis[kind + "_types"]["types"])
        modes.extend({"subset": subset, **row} for row in analysis["family_modal_partial_types"])
        for aggregation, rows in analysis["contrasts"].items():
            for contrast, row in rows.items():
                flat = {key: value for key, value in row.items() if key not in ("family_rows", "family_exclusion_status", "bootstrap")}
                flat.update({"subset": subset, "bootstrap_estimate": row["bootstrap"]["estimate"],
                             "bootstrap_ci95": json.dumps(row["bootstrap"]["ci95"]),
                             "empty_denominator_replicates": row["bootstrap"]["empty_denominator_replicates"],
                             "family_exclusion_status_json": json.dumps(row["family_exclusion_status"], ensure_ascii=False)})
                contrast_rows.append(flat)
                family_rows.extend({"subset": subset, "contrast": contrast, "aggregation": aggregation, **family} for family in row["family_rows"])
        equivalence.extend({"subset": subset, "estimand": estimand, **row} for estimand, row in analysis["equivalence_ii"].items())
    for name, rows in (("contrasts", contrast_rows), ("family_votes", family_rows), ("type_frequencies", types), ("family_modal_partial_types", modes), ("equivalence_ii", equivalence)):
        pd.DataFrame(rows).to_csv(OUT / (name + ".csv"), index=False)


def _make_figures(result):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    fonts = {font.name for font in font_manager.fontManager.ttflist}
    for font in ("Noto Sans CJK SC", "Noto Sans CJK JP", "WenQuanYi Zen Hei"):
        if font in fonts:
            plt.rcParams["font.family"] = font
            break
    plt.rcParams["axes.unicode_minus"] = False
    overall = result["subsets"]["overall"]
    fig, ax = plt.subplots(figsize=(9, 5))
    for offset, aggregation, label, color in ((-.10, "system", "系统差（整谱系区间）", "#777777"), (.10, "family_contrast_majority", "谱系方向多数差", "#176b87")):
        for index, contrast in enumerate(CONTRAST_IDS):
            row = overall["contrasts"][aggregation][contrast]
            value, interval = row["bootstrap"]["estimate"], row["bootstrap"]["ci95"]
            if interval is not None:
                ax.plot(interval, [index + offset] * 2, color=color, lw=1.6)
                ax.scatter([value], [index + offset], color=color, label=label if index == 0 else None, s=24)
    ax.axvline(0, color="black", lw=.7)
    ax.axvspan(-EQUIVALENCE_MARGIN, EQUIVALENCE_MARGIN, color="#e7c471", alpha=.2, label="相当性边界±0.15（用于ii）")
    ax.set_yticks(range(6), [CONTRAST_LABELS[key] for key in CONTRAST_IDS])
    ax.invert_yaxis(); ax.set_xlim(-1.04, 1.04)
    ax.set_xlabel("左侧比例－右侧比例；95%整谱系自助区间")
    for index, contrast in enumerate(CONTRAST_IDS):
        if not overall["contrasts"]["system"][contrast]["denominator"]:
            ax.text(0, index, "无适用系统／谱系", color="#777777", fontsize=8,
                    ha="center", va="center")
    handles, legend_labels = ax.get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="lower center", ncol=1, fontsize=8,
               bbox_to_anchor=(.68, -.005))
    fig.tight_layout(rect=(0, .15, 1, 1))
    for suffix in ("png", "pdf"):
        fig.savefig(OUT / ("Fx_position_contrasts." + suffix), dpi=180)
    plt.close(fig)
    rows = overall["A_types"]["types"]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(range(14), [row["systems"] for row in rows], color="#176b87")
    ax.set_xticks(range(14), [row["type"] for row in rows], rotation=55, ha="right")
    ax.set_ylabel("记录系统数"); ax.set_xlabel("年龄区分集合A的全部14种偏性类型（含零频）")
    fig.tight_layout()
    for suffix in ("png", "pdf"):
        fig.savefig(OUT / ("Fx_age_partial_types." + suffix), dpi=180)
    plt.close(fig)


def _report(result):
    overall = result["subsets"]["overall"]
    lines = ["# T4：位置配置的直接对照", "", "本分析按冻结计划实施。新增A/G配置集合与旧P2–P4严格层级方向分别命名，后者不作改写。记录系统和谱系并非独立心理实验。", "",
             f"严格样本{overall['n_systems']}个系统、{overall['n_families']}个谱系组；偏性年龄系统{overall['A_types']['n_partial_systems']}个，偏性性别系统{overall['G_types']['n_partial_systems']}个。A和G各14种偏性类型均完整保存，包括零频类型。", "",
             "## 六项预先设定对照", "", "|对照|系统左／右|系统Holm p|谱系多数左／右|谱系Holm p|", "|---|---:|---:|---:|---:|"]
    def pformat(value): return "不可评估" if value is None else f"{value:.6g}"
    for contrast in CONTRAST_IDS:
        system = overall["contrasts"]["system"][contrast]
        family = overall["contrasts"]["family_contrast_majority"][contrast]
        lines.append(f"|{CONTRAST_LABELS[contrast]}|{system['left']}／{system['right']}|{pformat(system['p_holm_six'])}|{family['left']}／{family['right']}|{pformat(family['p_holm_six'])}|")
    lines.extend(["", "左／右对应各对照固定标题；精确双侧二项p在系统口径与谱系口径分别按六项Holm校正。谱系主口径仅在该对照的有关系统中取方向多数，平局和不适用者单列。系统二项p只是同样本的描述性检验，不能替代谱系控制。", "", "## ii：男男与女女的相当性", "", "|估计对象|差值|95%整谱系区间|结论|", "|---|---:|---|---|"])
    for estimand, row in overall["equivalence_ii"].items():
        interval = row["ci95"]
        estimate = "未定义" if row["estimate"] is None else f"{row['estimate']:.4f}"
        ci = "不可评估" if interval is None else f"[{interval[0]:.4f}, {interval[1]:.4f}]"
        conclusion = "相当性得到支持" if row["supported"] else "相当性未获证实" if row["status"] != "not_assessable_empty_denominator" else "空分母，不能评估"
        lines.append(f"|{estimand}|{estimate}|{ci}|{conclusion}|")
    lines.extend(["", "主量为已确定方向多数的相关谱系差，系统差及连续谱系均值差为不同估计对象。只有区间完整严格落入±0.15才支持相当性；区间含零或二项检验不显著均不能替代这一条件。空分母副本数量逐项记录，不补填零。", "", "## 敏感性与范围", "", "family_modal_partial_type先在谱系内全部偏性A的14种精确类型中取唯一众数，再投入四项A对照。多众数、不相关类型和没有partial系统分别保留。该敏感性六项校正中，四项A改为众数口径，两项G仍使用原对照内方向多数；每行已标记，未新增G众数定义。", "", "|子样本／聚合|系统／谱系|i 同性／异性谱系|ii 男男／女女谱系|iv 男性／女性所指者谱系|G男性ego年长／年幼谱系|G女性ego年长／年幼谱系|", "|---|---:|---:|---:|---:|---:|---:|"])
    for subset, analysis in result["subsets"].items():
        rows = analysis["contrasts"]["family_contrast_majority"]
        cells = [f"{rows[key]['left']}／{rows[key]['right']}" for key in ("A_i", "A_ii", "A_iv", "G_male_ego", "G_female_ego")]
        lines.append(f"|{subset}|{analysis['n_systems']}／{analysis['n_families']}|" + "|".join(cells) + "|")
    modes = overall["contrasts"]["family_modal_partial_type_sensitivity"]
    lines.extend(["", "|众数敏感性对照|谱系左／右|Holm p|", "|---|---:|---:|"])
    for contrast in CONTRAST_IDS:
        row = modes[contrast]
        lines.append(f"|{CONTRAST_LABELS[contrast]}|{row['left']}／{row['right']}|{pformat(row['p_holm_six'])}|")
    lines.extend(["", "地域缺失系统在总体分析保留，单独列为缺失地域层，不作为第七个宏观区域。完整区间、平局、排除数与校正p见CSV和JSON；每个子样本分别维持固定六项校正，不把区域层合并为额外主检验。", "", "## 解释边界", "", "同性配置相对异性配置的集中程度、男性与女性所指者配置的差异，以及男男与女女是否相当，是不同命题。i的差异不能代替ii的相当性检验。iii若无合格系统，只能记为不可估计；iv的系统级差异也不能代替谱系级六项校正后的判断。各区域方向须分别阅读，不能把总体趋势称为逐区域普遍规律。两种理论的比较不能越过这些可识别范围，也不能由本数据库的结构计数直接推出心理因果。", "", "## 图表与复现", "", "- Fx_position_contrasts.png／.pdf：六项对照的两种估计对象与区间。", "- Fx_age_partial_types.png／.pdf：全部14种年龄偏性类型。", "- contrasts.csv、equivalence_ii.csv、type_frequencies.csv、family_votes.csv、family_modal_partial_types.csv和system_positions.csv提供逐项审计。", "", "运行入口、计划哈希、T1输入哈希、随机种子及执行规格保存于position_results.json；运行日志追加至results/run_log.csv。"])
    (OUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    guard = verify_analysis_plan(require_t1=True)
    specification = {"sample": "strict625", "contrasts": list(CONTRAST_IDS), "holm_family_size": 6,
                     "equivalence_primary": "within_contrast_majority_family_delta", "equivalence_margin": EQUIVALENCE_MARGIN,
                     "bootstrap_replicates": BOOTSTRAP_REPLICATES, "seed": SEED,
                     "modal_sensitivity": "four_A_modal_types_plus_two_G_unchanged_family_majority"}
    with logged_run("T4", specification) as metrics:
        started = utc_now()
        mapping = load_system_mapping("strict")
        if len(mapping) != 625 or mapping.family_group.nunique() != 108:
            raise RuntimeError("T1严格样本规模不一致")
        records = []
        for row in mapping.to_dict("records"):
            labels = tuple(int(value) for value in row["rgs"])
            old = strict_direction_vector(labels)
            records.append({**row, "A": age_distinction_set(labels), "G": gender_distinction_set(labels),
                            **dict(zip(("old_P2", "old_P3", "old_P4"), old))})
        analyses = {name: analyse_subset(subset) for name, subset in _subsets(records).items()}
        OUT.mkdir(parents=True, exist_ok=True)
        result = {"task": "T4", "analysis_status": "预先设定的补充分析，既有探索结果已知", "guard": guard,
                  "specification": specification, "started_at": started, "completed_at": utc_now(),
                  "input_sha256": {"results/t1/systems_to_partition.csv": sha256(RESULTS / "t1/systems_to_partition.csv")},
                  "subsets": analyses, "script": "analysis/v3/position_tests.py", "git_commit": git_commit(),
                  "execution_definition_notes": ["modal敏感性仅替换四项A聚合，两项G保持原谱系方向多数；仍按六项Holm独立校正。", "系统差自助整组重抽全部该子样本谱系，空分母副本单列；主相当性只重抽已有确定方向多数的相关谱系。"]}
        save_json(OUT / "position_results.json", result)
        _write_tables(result, records)
        _make_figures(result)
        _report(result)
        main_ii = analyses["overall"]["equivalence_ii"]["family_direction_majority_primary"]
        metrics.update({"systems": len(records), "families": 108,
                        "ii_primary_delta": main_ii["estimate"], "ii_ci95": main_ii["ci95"],
                        "ii_equivalence_supported": main_ii["supported"], "contrasts": 6})
        print(json.dumps(metrics, ensure_ascii=False))


if __name__ == "__main__":
    main()
