"""T3：候选第四特征、对称性及带库存成本的描述语言比较。

纯函数可用人工例子测试；main必须通过已提交计划、T0及T1三道执行门。
新增输出仅写results/t3；不修改旧S2或旧论文。
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from fractions import Fraction
from itertools import combinations, product
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from common import (ATOMS, FEATURES, CATEGORY_ORDER, ROOT, SEED,
                    BOOTSTRAP_REPLICATES, load_partition_table,
                    load_system_mapping, logged_run, verify_analysis_plan,
                    save_json, sha256)
from languages import LANGUAGES

UNIVERSE = 255
LANGUAGE_ORDER = ("abs", "rel_r", "rel_s", "all")
LAMBDA_GRID = (0, 1, 2, 3)


def canonical_feature(mask: int) -> int:
    """互补二分去重；包含0号单元的一侧记为值1。"""
    if not isinstance(mask, (int, np.integer)) or not 0 < int(mask) < UNIVERSE:
        raise ValueError("候选必须为非平凡的八元二分。")
    mask = int(mask)
    return mask if mask & 1 else UNIVERSE ^ mask


def feature_mask(values) -> int:
    values = tuple(values)
    if len(values) != 8 or any(value not in (0, 1) for value in values):
        raise ValueError("特征必须给出八个二元值。")
    return canonical_feature(sum(int(value) << i for i, value in enumerate(values)))


def feature_values(mask: int) -> tuple[int, ...]:
    mask = canonical_feature(mask)
    return tuple(int(bool(mask & (1 << i))) for i in range(8))


def sex_swap_permutation(atoms=ATOMS) -> tuple[int, ...]:
    lookup = {tuple(atom): i for i, atom in enumerate(atoms)}
    if len(lookup) != 8:
        raise ValueError("需要完整且唯一的八单元坐标。")
    return tuple(lookup[(1 - s, a, 1 - r)] for s, a, r in atoms)


def transform_mask(mask: int, permutation) -> int:
    permutation = tuple(permutation)
    if sorted(permutation) != list(range(8)):
        raise ValueError("单元变换必须为八位置的置换。")
    return sum(1 << permutation[i] for i in range(8) if mask & (1 << i))


def symmetry_class(mask: int, permutation=None) -> str:
    mask = canonical_feature(mask)
    transformed = transform_mask(mask, sex_swap_permutation() if permutation is None else permutation)
    if transformed == mask:
        return "value_preserving"
    if transformed == UNIVERSE ^ mask:
        return "block_swapping"
    return "not_stable"


def candidate_features() -> list[dict]:
    aliases = {feature_mask(FEATURES[name]): name for name in ("s", "a", "r", "q")}
    return [{"feature_id": f"f_{mask:03d}", "mask": mask,
             "alias": aliases.get(mask, ""), "values": feature_values(mask),
             "symmetry_class": symmetry_class(mask)}
            for mask in range(1, UNIVERSE, 2)]


def conjunctive_extents(feature_columns) -> frozenset[int]:
    """独立于T1固定语言的动态候选合取外延；含真式、不含空外延。"""
    columns = tuple(tuple(column) for column in feature_columns)
    if any(len(column) != 8 or any(x not in (0, 1) for x in column) for column in columns):
        raise ValueError("每个特征必须为八位二元列。")
    result = set()
    for assignment in product((-1, 0, 1), repeat=len(columns)):
        mask = sum(1 << i for i in range(8)
                   if all(value == -1 or column[i] == value
                          for column, value in zip(columns, assignment)))
        if mask:
            result.add(mask)
    return frozenset(result)


def build_acceptance(partitions) -> tuple[list[dict], np.ndarray]:
    """列0为不加第四特征的abs；其余127列均保留，包括与原始特征重复者。"""
    partitions = tuple(tuple(int(block) for block in partition) for partition in partitions)
    for blocks in partitions:
        covered = 0
        for block in blocks:
            if block <= 0 or block & ~UNIVERSE or covered & block:
                raise ValueError("划分块须非空且互不重叠。")
            covered |= block
        if covered != UNIVERSE:
            raise ValueError("划分未覆盖八单元。")
    specs = [{"feature_id": "abs", "mask": None, "alias": "abs", "values": None,
              "symmetry_class": "not_applicable"}] + candidate_features()
    base = tuple(FEATURES[name] for name in ("s", "a", "r"))
    matrix = np.empty((len(partitions), len(specs)), dtype=bool)
    for j, spec in enumerate(specs):
        columns = base if spec["mask"] is None else base + (spec["values"],)
        extents = conjunctive_extents(columns)
        matrix[:, j] = [all(block in extents for block in blocks) for blocks in partitions]
    return specs, matrix


def _group_statistics(values, groups):
    values = np.asarray(values, dtype=float)
    if values.ndim == 1:
        values = values[:, None]
    raw_groups = np.asarray(groups, dtype=object)
    if raw_groups.ndim != 1 or any(pd.isna(g) or g == "" for g in raw_groups):
        raise ValueError("谱系标记必须为非空且无缺失的一维序列。")
    groups = raw_groups.astype(str)
    if values.ndim != 2 or len(values) == 0 or len(groups) != len(values):
        raise ValueError("观测矩阵和谱系标记维度不符或为空。")
    if not np.isfinite(values).all() or np.any(groups == ""):
        raise ValueError("输入含非有限值或缺失谱系。")
    family_ids, inverse = np.unique(groups, return_inverse=True)
    counts = np.bincount(inverse)
    totals = np.zeros((len(family_ids), values.shape[1]))
    np.add.at(totals, inverse, values)
    return values, family_ids, inverse, counts, totals, totals / counts[:, None]


def cluster_bootstrap_matrix(values, groups, replicates=BOOTSTRAP_REPLICATES,
                             seed=SEED, batch_size=100) -> dict:
    """同一整谱系重抽用于全部列；保留成对比较所需协方差。"""
    if replicates < 1 or batch_size < 1:
        raise ValueError("重抽次数与批大小必须为正。")
    values, ids, inverse, counts, totals, means = _group_statistics(values, groups)
    rng = np.random.default_rng(seed)
    system = np.empty((replicates, values.shape[1]))
    family = np.empty_like(system)
    for start in range(0, replicates, batch_size):
        stop = min(start + batch_size, replicates)
        draws = rng.integers(0, len(ids), size=(stop - start, len(ids)))
        family[start:stop] = means[draws].mean(axis=1)
        system[start:stop] = totals[draws].sum(axis=1) / counts[draws].sum(axis=1)[:, None]
    return {"system_estimate": values.mean(axis=0), "family_estimate": means.mean(axis=0),
            "system_draws": system, "family_draws": family,
            "family_ids": ids, "family_counts": counts, "inverse": inverse,
            "system_ci95": np.quantile(system, [.025, .975], axis=0).T,
            "family_ci95": np.quantile(family, [.025, .975], axis=0).T}


def shape_reference(acceptance, partition_shapes, observed_shapes, groups,
                    replicates=BOOTSTRAP_REPLICATES, seed=SEED, batch_size=100):
    """固定每系统shape，在该shape的全部理论划分上均匀、独立生成样本。

    此处给随机参照预测区间，不是整谱系重抽置信区间。共同随机抽样
    同时评价所有候选，候选间相关性得以保留；边际分布与单独生成相同。
    """
    acceptance = np.asarray(acceptance, dtype=bool)
    observed_shapes = tuple(tuple(shape) for shape in observed_shapes)
    partition_shapes = tuple(tuple(shape) for shape in partition_shapes)
    if acceptance.ndim != 2 or len(acceptance) != len(partition_shapes):
        raise ValueError("理论划分矩阵与shape不一致。")
    if not observed_shapes or len(groups) != len(observed_shapes) or replicates < 1 or batch_size < 1:
        raise ValueError("观测shape与谱系维度不一致，或重抽次数无效。")
    _, family_ids, inverse, counts, _, _ = _group_statistics(np.ones(len(groups)), groups)
    family_weights = 1 / (len(family_ids) * counts[inverse])
    pools = defaultdict(list)
    observed = defaultdict(list)
    for i, shape in enumerate(partition_shapes):
        pools[shape].append(i)
    for i, shape in enumerate(observed_shapes):
        if shape not in pools:
            raise ValueError("观测shape不在理论空间。")
        observed[shape].append(i)
    per_system = np.vstack([acceptance[pools[shape]].mean(axis=0) for shape in observed_shapes])
    expected_system = per_system.mean(axis=0)
    expected_family = family_weights @ per_system
    counts_draws = np.zeros((replicates, acceptance.shape[1]))
    family_draws = np.zeros_like(counts_draws)
    streams = np.random.SeedSequence(seed).spawn(len(observed))
    rngs = {shape: np.random.default_rng(stream)
            for shape, stream in zip(sorted(observed), streams)}
    for start in range(0, replicates, batch_size):
        stop = min(start + batch_size, replicates)
        for shape in sorted(observed):
            positions = np.array(observed[shape], dtype=int)
            pool = np.array(pools[shape], dtype=int)
            picked = pool[rngs[shape].integers(0, len(pool), size=(stop - start, len(positions)))]
            indicators = acceptance[picked]
            counts_draws[start:stop] += indicators.sum(axis=1)
            family_draws[start:stop] += np.einsum("bik,i->bk", indicators, family_weights[positions])
    return {"expected_system": expected_system, "expected_family": expected_family,
            "count_pi95": np.quantile(counts_draws, [.025, .975], axis=0).T,
            "system_pi95": np.quantile(counts_draws / len(groups), [.025, .975], axis=0).T,
            "family_pi95": np.quantile(family_draws, [.025, .975], axis=0).T,
            "count_draws": counts_draws, "family_draws": family_draws,
            "pools": dict(pools), "per_system_probabilities": per_system}


def tied_ranks(values, descending=True):
    """competition rank：1、1、3；用精确Fraction避免浮点造成假破同分。"""
    order = sorted(range(len(values)), key=lambda i: values[i], reverse=descending)
    ranks = [0] * len(values)
    previous = None
    for position, i in enumerate(order, 1):
        if position == 1 or values[i] != previous:
            rank = position
        ranks[i] = rank
        previous = values[i]
    return ranks


def _exact_family_mean(integer_values, groups):
    values, ids, inverse, counts, totals, _ = _group_statistics(integer_values, groups)
    if not np.equal(values, np.round(values)).all():
        raise ValueError("精确排名要求整数观测或整数描述长度。")
    return [sum((Fraction(int(totals[g, j]), int(counts[g])) for g in range(len(ids))), Fraction()) / len(ids)
            for j in range(values.shape[1])]


def summarize_features(specs, acceptance, observed_ids, groups, partition_shapes,
                       replicates=BOOTSTRAP_REPLICATES, seed=SEED):
    acceptance = np.asarray(acceptance, dtype=bool)
    observed_ids = np.asarray(observed_ids, dtype=int)
    if observed_ids.ndim != 1 or np.any(observed_ids < 0) or np.any(observed_ids >= len(acceptance)):
        raise ValueError("观测划分编号越界。")
    if acceptance.shape[1] != len(specs):
        raise ValueError("特征描述与接受矩阵列数不一致。")
    observed = acceptance[observed_ids]
    boot = cluster_bootstrap_matrix(observed, groups, replicates, seed)
    reference = shape_reference(acceptance, partition_shapes,
                                [partition_shapes[i] for i in observed_ids], groups,
                                replicates, seed)
    n, n_theory, families = len(observed), len(acceptance), len(boot["family_ids"])
    C = acceptance.sum(axis=0).astype(int)
    N = observed.sum(axis=0).astype(int)
    exact_family = _exact_family_mean(observed, groups)
    E_system = [Fraction(int(N[j]) * n_theory, n * int(C[j])) for j in range(len(specs))]
    E_family = [exact_family[j] / Fraction(int(C[j]), n_theory) for j in range(len(specs))]
    rows = []
    for j, spec in enumerate(specs):
        theory = C[j] / n_theory
        row = {key: spec[key] for key in ("feature_id", "mask", "alias", "symmetry_class")}
        row.update(C=int(C[j]), N_system=int(N[j]), n_systems=n, n_families=families,
                   theory_proportion=float(theory), observed_system_proportion=float(N[j] / n),
                   observed_family_proportion=float(exact_family[j]),
                   N_family_fraction_sum=float(exact_family[j] * families),
                   E_system=float(E_system[j]), E_family=float(E_family[j]),
                   E_system_exact=str(E_system[j]), E_family_exact=str(E_family[j]),
                   shape_reference_expected_N=float(reference["expected_system"][j] * n),
                   shape_reference_expected_system_proportion=float(reference["expected_system"][j]),
                   shape_reference_expected_family_proportion=float(reference["expected_family"][j]))
        for weight in ("system", "family"):
            for edge, value in zip(("low", "high"), boot[weight + "_ci95"][j]):
                row[f"observed_{weight}_ci95_{edge}"] = float(value)
                row[f"E_{weight}_ci95_{edge}"] = float(value / theory)
            for edge, value in zip(("low", "high"), reference[weight + "_pi95"][j]):
                row[f"shape_reference_{weight}_pi95_{edge}"] = float(value)
        for edge, value in zip(("low", "high"), reference["count_pi95"][j]):
            row[f"shape_reference_N_pi95_{edge}"] = float(value)
        rows.append(row)
    metrics = {"N_system": list(N), "N_family": exact_family, "C": list(C),
               "E_system": E_system, "E_family": E_family}
    for label, values in metrics.items():
        for universe, indices in (("candidates", list(range(1, len(rows)))),
                                  ("with_abs", list(range(len(rows))))):
            ranks = tied_ranks([values[i] for i in indices])
            for rank, i in zip(ranks, indices):
                rows[i][f"rank_{label}_{universe}"] = rank
                rows[i][f"ties_{label}_{universe}"] = sum(values[k] == values[i] for k in indices)
        for rank, i in zip(tied_ranks(values, descending=False), range(len(rows))):
            rows[i][f"rank_{label}_ascending_with_abs"] = rank
    return rows, boot, reference


def description_cost_comparison(dl_values, groups, lambda_grid=LAMBDA_GRID,
                                replicates=BOOTSTRAP_REPLICATES, seed=SEED):
    dl_values = np.asarray(dl_values, dtype=float)
    if dl_values.ndim != 2 or dl_values.shape[1] != len(LANGUAGE_ORDER):
        raise ValueError("描述长度必须按abs、rel_r、rel_s、all给出四列。")
    if not np.equal(dl_values, np.round(dl_values)).all() or np.any(dl_values < 0):
        raise ValueError("T1文字成本应为非负整数。")
    boot = cluster_bootstrap_matrix(dl_values, groups, replicates, seed)
    means = {"system": [Fraction(int(dl_values[:, j].sum()), len(dl_values)) for j in range(4)],
             "family": _exact_family_mean(dl_values, groups)}
    dimensions = np.array([len(LANGUAGES[language]) for language in LANGUAGE_ORDER])
    rows, pairwise, crossings, orderings = [], [], [], {}
    for weight in ("system", "family"):
        orderings[weight] = {}
        for lam in lambda_grid:
            exact = [means[weight][j] + Fraction(lam) * int(dimensions[j]) for j in range(4)]
            ranks = tied_ranks(exact, descending=False)
            orderings[weight][str(lam)] = [list(sorted(LANGUAGE_ORDER[i] for i in range(4) if ranks[i] == rank))
                                          for rank in sorted(set(ranks))]
            for j, language in enumerate(LANGUAGE_ORDER):
                ci = boot[weight + "_ci95"][j] + lam * dimensions[j]
                rows.append({"weighting": weight, "language": language, "lambda": lam,
                             "n_features": int(dimensions[j]), "mean_DL": float(means[weight][j]),
                             "mean_DL_exact": str(means[weight][j]), "mean_total_cost": float(exact[j]),
                             "ci95_low": float(ci[0]), "ci95_high": float(ci[1]), "rank": ranks[j]})
            for i, j in combinations(range(4), 2):
                draws = boot[weight + "_draws"][:, i] - boot[weight + "_draws"][:, j]
                draws += lam * (dimensions[i] - dimensions[j])
                low, high = np.quantile(draws, [.025, .975])
                pairwise.append({"weighting": weight, "lambda": lam,
                                 "left": LANGUAGE_ORDER[i], "right": LANGUAGE_ORDER[j],
                                 "difference_left_minus_right": float(exact[i] - exact[j]),
                                 "ci95_low": float(low), "ci95_high": float(high)})
        for i, j in combinations(range(4), 2):
            dimension_difference = int(dimensions[i] - dimensions[j])
            difference = means[weight][i] - means[weight][j]
            row = {"weighting": weight, "left": LANGUAGE_ORDER[i], "right": LANGUAGE_ORDER[j],
                   "DL_difference": float(difference), "dimension_difference": dimension_difference}
            if dimension_difference:
                crossing = -difference / dimension_difference
                draws = -(boot[weight + "_draws"][:, i] - boot[weight + "_draws"][:, j]) / dimension_difference
                low, high = np.quantile(draws, [.025, .975])
                row.update(lambda_crossing=float(crossing), lambda_crossing_exact=str(crossing),
                           crossing_ci95_low=float(low), crossing_ci95_high=float(high),
                           crossing_in_scanned_range=bool(min(lambda_grid) <= crossing <= max(lambda_grid)),
                           status="single_crossing")
            else:
                row.update(lambda_crossing=None, lambda_crossing_exact=None,
                           crossing_ci95_low=None, crossing_ci95_high=None,
                           crossing_in_scanned_range=False,
                           status="equal_all_lambda" if difference == 0 else "parallel_no_crossing")
            crossings.append(row)
    return {"rows": rows, "pairwise": pairwise, "crossings": crossings,
            "ordering_by_lambda": orderings,
            "ordering_stable_on_grid": {w: all(x == next(iter(orderings[w].values())) for x in orderings[w].values())
                                        for w in orderings}}


def plot_results(rows, costs, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    matplotlib.rcParams["svg.hashsalt"] = "kinship-t3-20261016"
    # TTC中的实际登记名可能为JP；显式载入现有字体文件，避免缓存中
    # 没有SC家族别名而渲染成方框。此处不下载或安装字体。
    cjk_paths = sorted(path for path in font_manager.findSystemFonts()
                       if Path(path).name == "NotoSansCJK-Regular.ttc")
    if not cjk_paths:
        raise RuntimeError("未找到已安装的NotoSansCJK-Regular.ttc，无法生成中文图。")
    font_manager.fontManager.addfont(cjk_paths[0])
    family_name = font_manager.FontProperties(fname=cjk_paths[0]).get_name()
    matplotlib.rcParams["font.family"] = [family_name, "DejaVu Sans"]
    matplotlib.rcParams["axes.unicode_minus"] = False
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharex=True, sharey=True)
    for ax, weight in zip(axes, ("system", "family")):
        candidates = rows[1:]
        ax.scatter([r["theory_proportion"] for r in candidates],
                   [r[f"observed_{weight}_proportion"] for r in candidates],
                   color="#6e879e", s=25, alpha=.55)
        top = sorted(candidates, key=lambda r: (r[f"rank_E_{weight}_candidates"], r["mask"]))[:5]
        marked = {r["feature_id"] for r in top} | {r["feature_id"] for r in candidates if r["alias"]}
        xylabels = defaultdict(list)
        for r in rows:
            if r["feature_id"] in marked or r["feature_id"] == "abs":
                xylabels[(r["theory_proportion"], r[f"observed_{weight}_proportion"])].append(r["alias"] or r["feature_id"])
        callout = 0
        for (x, y), labels in sorted(xylabels.items()):
            if "q" in labels:
                ax.annotate(", ".join(labels), (x, y), xytext=(5, 5), textcoords="offset points", fontsize=9)
            else:
                ax.annotate(", ".join(labels), (x, y), xytext=(.62, .10 + .12 * callout),
                            textcoords="axes fraction", fontsize=8,
                            arrowprops={"arrowstyle": "-", "color": "#707070", "lw": .6})
                callout += 1
        q = next(r for r in rows if r["alias"] == "q")
        ax.scatter(q["theory_proportion"], q[f"observed_{weight}_proportion"],
                   marker="*", color="#c74b31", s=140, zorder=5)
        ax.set(xlabel="理论合取比例 C / 4140", title="系统等权" if weight == "system" else "谱系等权")
        ax.set_xlim(0, max(r["theory_proportion"] for r in rows) + .03)
        ax.set_ylim(min(r[f"observed_{weight}_proportion"] for r in rows) - .04, 1.02)
        ax.grid(alpha=.15)
    axes[0].set_ylabel("观测合取比例")
    fig.tight_layout()
    for extension in ("png", "svg"):
        fig.savefig(output / ("Fx_basis_enrichment." + extension), dpi=200,
                    metadata={"Date": None} if extension == "svg" else None)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.3), sharey=True)
    for ax, weight in zip(axes, ("system", "family")):
        for language in LANGUAGE_ORDER:
            subset = [r for r in costs["rows"] if r["weighting"] == weight and r["language"] == language]
            ax.plot([r["lambda"] for r in subset], [r["mean_total_cost"] for r in subset], label=language, marker="o")
            ax.fill_between([r["lambda"] for r in subset], [r["ci95_low"] for r in subset],
                            [r["ci95_high"] for r in subset], alpha=.1)
        ax.set(xlabel="语言库存的特征成本 λ", title="系统等权" if weight == "system" else "谱系等权", xticks=LAMBDA_GRID)
        ax.grid(alpha=.15)
    axes[0].set_ylabel("平均最小DNF文字数＋λd")
    axes[1].legend()
    fig.tight_layout()
    for extension in ("png", "svg"):
        fig.savefig(output / ("Fx_basis_description_cost." + extension), dpi=200,
                    metadata={"Date": None} if extension == "svg" else None)
    plt.close(fig)


def write_report(result, output):
    q, baseline = result["q"], result["absolute_baseline"]
    lines = ["# T3 基底比较报告", "", "本报告列出全部候选及两种权重，不按有利结果筛选。",
             "", "## 定义及区间", "",
             "八单元顺序沿用T1。候选是127个非平凡互补二分，含0号单元一侧标为1；q别名对应q=0侧，互补不改变描述语言。另加不增加特征的abs基准，共128行。",
             "系统口径N是合取系统数；谱系口径先求各谱系合取比例再等权平均，N_family_fraction_sum为这些比例之和，不是多数票或整数合取谱系数。E分别以两种观测比例除以理论C/4140。",
             "排名使用精确分数及competition并列名次1、1、3；同时给127候选与含abs的128行排名。C高意味着允许范围宽，不等于理论更好；N、C、E全部保留。",
             "随机参照固定每系统词项数及块大小，均匀抽该shape所有划分，5000个独立合成样本给预测区间。观测区间另用5000次整谱系重抽；两者不是同一种区间，不作直接替换。",
             "", "## q核查及全部排名", "",
             f"严格样本{q['n_systems']}系统、{q['n_families']}谱系；N_q={q['N_system']}，预期603的定义核查通过。C_q={q['C']}；abs的C={baseline['C']}、N={baseline['N_system']}。",
             f"q系统富集E={q['E_system']:.8f}，127候选并列第{q['rank_E_system_candidates']}（同值{q['ties_E_system_candidates']}项）；谱系等权E={q['E_family']:.8f}，并列第{q['rank_E_family_candidates']}（同值{q['ties_E_family_candidates']}项）。该排名不能被改称唯一最优。",
             f"q按N系统口径第{q['rank_N_system_candidates']}，按谱系口径第{q['rank_N_family_candidates']}，按C由高至低第{q['rank_C_candidates']}。",
             f"abs基准的系统/谱系富集为{baseline['E_system']:.8f}/{baseline['E_family']:.8f}。q虽覆盖最多观测系统，却不是按E最优；覆盖收益与扩大理论允许空间的代价必须同时报告，不能仅选N排名维护优势结论。",
             "", "## 全局性别互换", "",
             "保值f(Tx)=f(x)的候选为7；另有8个会交换两块标签，二者合为15个无标签稳定二分。只有前7个可称特征值不变，不能把另8个删除或混叫保值。q和a属于前者，s和r属于后者。",
             "", "| 候选 | mask | 分类 | C | N系统 | 谱系比例 | E系统 | E谱系 |",
             "|---|---:|---|---:|---:|---:|---:|---:|"]
    for row in result["symmetry_features"]:
        lines.append(f"| {row['alias'] or row['feature_id']} | {row['mask']} | {row['symmetry_class']} | {row['C']} | {row['N_system']} | {row['observed_family_proportion']:.8f} | {row['E_system']:.8f} | {row['E_family']:.8f} |")
    lines += ["", "## 带特征库存成本的四语言比较", "",
              "三特征语言abs、rel_r={q,a,r}、rel_s={q,a,s}均列出，all为四特征。成本是每系统的精确最小DNF文字数加lambda乘语言特征数。区间为同一整谱系重抽的成对区间，所有lambda均保留。",
              "固定语言内部的lambda*d是常数，进入T2概率归一化会抵消；本节比较实际跨语言总成本，不把此扫描当成T2中可辨识的库存惩罚参数。",
              "", "| 权重 | lambda | 语言 | 平均DL | 总成本 | 95%区间 | 名次 |",
              "|---|---:|---|---:|---:|---|---:|"]
    for row in result["description_cost"]["rows"]:
        lines.append(f"| {row['weighting']} | {row['lambda']} | {row['language']} | {row['mean_DL']:.8f} | {row['mean_total_cost']:.8f} | [{row['ci95_low']:.8f}, {row['ci95_high']:.8f}] | {row['rank']} |")
    lines += ["", "同为三特征的rel_r与rel_s给出不同结果：rel_r的平均DNF成本低于abs，rel_s反而高于abs；不能统称相对基底优于绝对基底。四特征all在lambda=0最低，但扫描至lambda=1–3时rel_r最低；all对abs的排序也发生改变。以下成对差是abs减相对语言，正值表示相对语言成本较低。", "",
              "| 权重 | 对比 | DL差 | 整谱系95%区间 |", "|---|---|---:|---|"]
    for row in result["description_cost"]["pairwise"]:
        if row["lambda"] == 0 and row["left"] == "abs" and row["right"] in ("rel_r", "rel_s"):
            lines.append(f"| {row['weighting']} | abs−{row['right']} | {row['difference_left_minus_right']:.8f} | [{row['ci95_low']:.8f}, {row['ci95_high']:.8f}] |")
    lines += ["", "各权重下排序是否在扫描网格保持：" + str(result["description_cost"]["ordering_stable_on_grid"]) + "。",
              "全部语言两两差值与交点见language_cost_pairwise.csv、language_cost_crossings.csv；交点是经验平均成本的线性交点及整谱系区间，不是留出预测结论。",
              "", "## 理论解释的范围", "",
              "T3检验候选基底的组合覆盖、数据富集及描述成本，不能独自证明q为先天心理基元、排除其他关系特征或证明效率形成机制。若q不是富集最高、只优于某种基底、或lambda改变排序，应在第三版中逐项限定；对称性也只把它放入一个小候选集合，不能证明其唯一性。留出预测优劣须由T2回答。",
              "", "## 文件及来源", "",
              "feature_enrichment.csv保留abs与127候选全部指标/排名/区间；feature_definitions.csv列八位取值；shape_reference_probabilities.csv给每shape精确参照概率；observed_conjunctivity.csv列每个系统每个候选的判定；symmetry_features.csv保留全部15种无标签稳定二分；四语言成本、差值、交点全部分别导出。",
              "图Fx_basis_enrichment在系统/谱系两个面板标q、s/a/r、abs及富集最高的五个候选；重复坐标合并注释。图Fx_basis_description_cost列出四语言的全部lambda。",
              "本轮为已知旧结果后的预先设定补充分析，不称验证性。计划执行门、输入SHA和种子记录在t3_results.json，运行尝试追加results/run_log.csv。", ""]
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results/t3")
    args = parser.parse_args(argv)
    guard = verify_analysis_plan(require_t1=True)
    spec = {"sample": "strict", "candidate_bipartitions": 127, "include_abs": True,
            "seed": SEED, "replicates": BOOTSTRAP_REPLICATES,
            "weights": ["system", "family"], "languages": list(LANGUAGE_ORDER),
            "lambda": list(LAMBDA_GRID), "plan_commit": guard["plan_commit"],
            "implementation_sha256": sha256(__file__)}
    with logged_run("T3", spec) as metrics:
        table = load_partition_table().sort_values("partition_id").reset_index(drop=True)
        systems = load_system_mapping("strict")
        if list(table.partition_id) != list(range(4140)) or len(systems) != 625 or systems.family_group.nunique() != 108:
            raise RuntimeError("T1编号或严格样本规模与冻结计划不一致。")
        specs, acceptance = build_acceptance(table.blocks)
        partition_shapes = [tuple(sorted(int(block).bit_count() for block in blocks)) for blocks in table.blocks]
        ids = systems.partition_id.to_numpy(dtype=int)
        rows, boot, reference = summarize_features(specs, acceptance, ids, systems.family_group,
                                                   partition_shapes)
        q = next(row for row in rows if row["alias"] == "q")
        if q["N_system"] != 603 or int(acceptance[:, 0].sum()) != 154:
            raise RuntimeError("N_q=603或abs纯组合154核查失败，停止T3并汇报。")
        for feature in ("s", "a", "r"):
            index = next(j for j, row in enumerate(rows) if row["alias"] == feature)
            if not np.array_equal(acceptance[:, index], acceptance[:, 0]):
                raise RuntimeError("加入重复原始特征改变了合取判定。")
        counts = {key: sum(row["symmetry_class"] == key for row in rows[1:])
                  for key in ("value_preserving", "block_swapping", "not_stable")}
        if counts["value_preserving"] != 7 or counts["block_swapping"] != 8:
            raise RuntimeError("全局性别互换7+8分类核查失败。")
        values = np.column_stack([table["DL_" + language].to_numpy()[ids] for language in LANGUAGE_ORDER])
        costs = description_cost_comparison(values, systems.family_group)
        output = args.output
        output.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_csv(output / "feature_enrichment.csv", index=False)
        definitions = [{"feature_id": row["feature_id"], "mask": row["mask"], "alias": row["alias"],
                        "symmetry_class": row["symmetry_class"],
                        **dict(zip(CATEGORY_ORDER, row["values"]))} for row in specs[1:]]
        pd.DataFrame(definitions).to_csv(output / "feature_definitions.csv", index=False)
        observation_table = pd.concat([
            systems[["system_id", "family_group", "partition_id"]].reset_index(drop=True),
            pd.DataFrame(acceptance[ids].astype(int), columns=[row["feature_id"] for row in rows])
        ], axis=1)
        observation_table.to_csv(output / "observed_conjunctivity.csv", index=False)
        shape_rows = []
        for shape, pool in sorted(reference["pools"].items()):
            for j, row in enumerate(rows):
                success = int(acceptance[pool, j].sum())
                shape_rows.append({"shape": ",".join(map(str, shape)), "feature_id": row["feature_id"],
                                   "theoretical_partitions": len(pool), "conjunctive_partitions": success,
                                   "exact_probability": str(Fraction(success, len(pool))),
                                   "probability": success / len(pool)})
        pd.DataFrame(shape_rows).to_csv(output / "shape_reference_probabilities.csv", index=False)
        symmetry = [row for row in rows if row["symmetry_class"] in ("value_preserving", "block_swapping")]
        pd.DataFrame(symmetry).to_csv(output / "symmetry_features.csv", index=False)
        for key, filename in (("rows", "language_costs.csv"), ("pairwise", "language_cost_pairwise.csv"),
                              ("crossings", "language_cost_crossings.csv")):
            pd.DataFrame(costs[key]).to_csv(output / filename, index=False)
        result = {"task": "T3", "guard": guard, "configuration": spec,
                  "producer": {"script": "analysis/v3/basis_enrichment.py",
                               "feature_function": "summarize_features",
                               "cost_function": "description_cost_comparison",
                               "shape_seed_strategy": "SEED的SeedSequence按排序后的观测shape分支；各流按系统独立抽划分",
                               "observed_seed_strategy": "同一SEED整谱系索引用于所有特征和四语言的成对比较"},
                  "input_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in
                                   [ROOT / "results/t1/partitions.csv", ROOT / "results/t1/systems_to_partition.csv"]},
                  "q_check_passed": True, "q": q, "absolute_baseline": rows[0],
                  "symmetry_counts": {**counts, "unlabeled_stable": 15},
                  "symmetry_features": symmetry, "features": rows, "description_cost": costs,
                  "interval_meaning": {"observed": "5000次整谱系bootstrap百分位95%区间",
                                       "shape_reference": "5000个固定每系统shape的随机合成样本95%预测区间"},
                  "ranking": "精确分数competition名次，候选127与含abs128两种范围同时给出"}
        save_json(output / "t3_results.json", result)
        write_report(result, output)
        plot_results(rows, costs, output)
        metrics.update(N_q=q["N_system"], C_q=q["C"],
                       E_q_system=q["E_system"], E_q_family=q["E_family"],
                       rank_q_system=q["rank_E_system_candidates"], rank_q_family=q["rank_E_family_candidates"],
                       symmetry_counts=counts, ordering_stable=costs["ordering_stable_on_grid"])
    return result


if __name__ == "__main__":
    main()
