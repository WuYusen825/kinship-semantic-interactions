"""T6探索性跨域指标与关联；严格执行独立提交的补充方案。"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from functools import lru_cache
from itertools import product
import hashlib
import json
from pathlib import Path
import subprocess
import warnings

import numpy as np
import pandas as pd
from scipy.optimize import linprog, minimize
from scipy.special import expit
from scipy.stats import t
from statsmodels.discrete.conditional_models import ConditionalLogit
from statsmodels.tools.numdiff import approx_fprime

from common import (ATOMS, CATEGORY_ORDER, ROOT, RESULTS, SEED, git_commit,
                    load_system_mapping, logged_run, save_json, sha256, utc_now,
                    verify_analysis_plan)
from domain_feasibility import (RAW, collect_cells, coverage_for_system,
                                domain_registry)


OUT = RESULTS / "t6"
T6_PLAN = ROOT / "docs/t6_association_plan.md"
T6_COMMIT = "d7c121b93fc6e98101c261b98581b0f1ad50bc7a"
T6_SHA = "652ea03412416615d320b6ca7f63e3dba1e136b06104e53aa847dc43360c1d39"
PRIMARY_DOMAINS = ("cousins16", "parent_siblings_age16")
PERMUTATIONS = 5000


def verify_t6_plan():
    guard = verify_analysis_plan(require_t1=True)
    if sha256(T6_PLAN) != T6_SHA:
        raise RuntimeError("T6补充计划SHA不符")
    committed = subprocess.check_output(["git", "show", f"{T6_COMMIT}:docs/t6_association_plan.md"], cwd=ROOT)
    if hashlib.sha256(committed).hexdigest() != T6_SHA:
        raise RuntimeError("T6补充计划提交对象不符")
    subprocess.run(["git", "merge-base", "--is-ancestor", T6_COMMIT, "HEAD"], cwd=ROOT, check=True, capture_output=True)
    return {**guard, "t6_commit": T6_COMMIT, "t6_sha256": T6_SHA,
            "t6_commit_time": subprocess.check_output(["git", "show", "-s", "--format=%cI", T6_COMMIT], cwd=ROOT, text=True).strip()}


class FiniteDescriptionLanguage:
    """有限格点的精确DNF文字成本；只求实际块，不枚举Bell(16)。"""
    def __init__(self, feature_values):
        values = np.asarray(feature_values, dtype=int)
        if values.ndim != 2 or not np.isin(values, [0, 1]).all():
            raise ValueError("特征须为二元矩阵")
        if len({tuple(row) for row in values}) != len(values):
            raise ValueError("语言必须能区分所有格点")
        self.values = values
        self.universe = (1 << len(values)) - 1
        terms = {}
        for assignment in product((-1, 0, 1), repeat=values.shape[1]):
            mask = sum(1 << i for i, row in enumerate(values)
                       if all(value == -1 or row[j] == value for j, value in enumerate(assignment)))
            if mask:
                cost = sum(value != -1 for value in assignment)
                terms[mask] = min(terms.get(mask, cost), cost)
        self.terms = terms
        self._costs = {}

    def minimum_dnf(self, target):
        target = int(target)
        if not 0 < target <= self.universe:
            raise ValueError("目标须为非空格点子集")
        if target in self._costs:
            return self._costs[target]
        usable = [(extent, cost) for extent, cost in self.terms.items() if not extent & ~target]
        @lru_cache(None)
        def solve(remaining):
            if not remaining:
                return 0
            first = remaining & -remaining
            return min(cost + solve(remaining & ~extent) for extent, cost in usable if extent & first)
        value = solve(target)
        self._costs[target] = value
        return value

    def partition_metrics(self, labels):
        if len(labels) != len(self.values):
            raise ValueError("标签数与格点不符")
        blocks = defaultdict(int)
        for index, label in enumerate(labels):
            blocks[label] |= 1 << index
        return {"dl": sum(self.minimum_dnf(mask) for mask in blocks.values()),
                "conjunction": all(mask in self.terms for mask in blocks.values()), "k": len(blocks)}


def metric_languages(entries, coordinate_names):
    absolute = np.array([[entry[name] for name in coordinate_names] for entry in entries], dtype=int)
    s_index, r_index = coordinate_names.index("s"), coordinate_names.index("r")
    q = absolute[:, s_index] ^ absolute[:, r_index]
    relative_r, relative_s = absolute.copy(), absolute.copy()
    relative_r[:, s_index] = q
    relative_s[:, r_index] = q
    return {"abs": FiniteDescriptionLanguage(absolute),
            "rel_r": FiniteDescriptionLanguage(relative_r), "rel_s": FiniteDescriptionLanguage(relative_s)}


def relative_metrics(labels, languages):
    costs = {key: language.partition_metrics(labels) for key, language in languages.items()}
    output = {"k": costs["abs"]["k"], "abs_nonconj": not costs["abs"]["conjunction"],
              **{"dl_" + key: row["dl"] for key, row in costs.items()}}
    for key in ("r", "s"):
        delta = costs["abs"]["dl"] - costs["rel_" + key]["dl"]
        output.update({"delta_dl_" + key: delta, "q_advantage_" + key: int(delta > 0),
                       "q_rescue_" + key: int(output["abs_nonconj"] and costs["rel_" + key]["conjunction"])})
    return output


def separation_diagnostic(differences):
    """冻结的box约束LP：任何严格改善方向即无有限MLE。"""
    differences = np.asarray(differences, dtype=float)
    if differences.ndim != 2 or not len(differences):
        return {"status": "no_comparable_vectors", "separated": None}
    result = linprog(-differences.sum(axis=0), A_ub=-differences,
                     b_ub=np.zeros(len(differences)), bounds=[(-1, 1)] * differences.shape[1], method="highs")
    if not result.success:
        return {"status": "linear_program_failed", "separated": None, "message": result.message}
    optimum = float(-result.fun)
    return {"status": "separation_detected" if optimum > 1e-9 else "no_separation_detected",
            "separated": optimum > 1e-9, "objective": optimum, "direction": result.x.tolist(),
            "difference_vectors": len(differences), "bound": "each coefficient in [-1,1]"}


def _fit_objective(group_evaluators, parameter_count):
    """每组evaluation返回该组LL/n和score/n；再取等族平均。"""
    count = len(group_evaluators)
    def evaluate(params):
        pieces = [function(params) for function in group_evaluators]
        return (float(np.mean([piece[0] for piece in pieces])),
                np.array([piece[1] for piece in pieces], dtype=float) / count)
    def score(params):
        return evaluate(params)[1].sum(axis=0)
    def objective(params):
        try:
            value, scores = evaluate(params)
            return -value, -scores.sum(axis=0)
        except (OverflowError, FloatingPointError, ValueError):
            return np.inf, np.full(parameter_count, np.nan)
    attempts = []
    for limit in (2000, 10000):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            optimum = minimize(objective, np.zeros(parameter_count), method="BFGS", jac=True,
                               options={"gtol": 1e-8, "maxiter": limit})
        attempt = {"maxiter": limit, "success": bool(optimum.success), "status": int(optimum.status),
                   "message": str(optimum.message), "iterations": int(optimum.nit),
                   "parameters": optimum.x.tolist(), "warnings": sorted({str(item.message) for item in caught})}
        try:
            value, scores = evaluate(optimum.x)
            gradient = scores.sum(axis=0)
            hessian = np.asarray(approx_fprime(optimum.x, score, centered=True), dtype=float)
            hessian = (hessian + hessian.T) / 2
            information = -hessian
            finite = bool(np.isfinite(optimum.x).all() and np.isfinite(value) and np.isfinite(scores).all() and np.isfinite(hessian).all())
            eigenvalues = np.linalg.eigvalsh(information) if finite else np.array([np.nan])
            condition = float(np.linalg.cond(information)) if finite else np.inf
            gradient_max = float(np.max(np.abs(gradient)))
            accepted = bool(optimum.success and finite and gradient_max <= 1e-7 and eigenvalues.min() > 0 and condition <= 1e12)
            attempt.update({"weighted_loglik": value if np.isfinite(value) else None,
                            "max_abs_average_gradient": gradient_max if np.isfinite(gradient_max) else None,
                            "information_eigenvalues": eigenvalues.tolist() if np.isfinite(eigenvalues).all() else None,
                            "information_condition": condition if np.isfinite(condition) else None,
                            "accepted": accepted})
        except (OverflowError, FloatingPointError, ValueError, np.linalg.LinAlgError) as error:
            accepted = False
            attempt.update({"accepted": False, "diagnostic_error": repr(error)})
        attempts.append(attempt)
        if accepted:
            return {"accepted": True, "parameters": optimum.x, "scores": scores,
                    "information": information, "attempts": attempts}
    return {"accepted": False, "attempts": attempts}


def sandwich_inference(parameters, scores, information, target_index=0):
    groups = len(scores)
    if groups < 2:
        return {"status": "not_estimable_fewer_than_two_contributing_families"}
    inverse = np.linalg.inv(information)
    covariance = groups / (groups - 1) * inverse @ (scores.T @ scores) @ inverse
    variance = float(covariance[target_index, target_index])
    if not np.isfinite(covariance).all() or variance <= 0:
        return {"status": "not_estimable_invalid_sandwich"}
    beta = float(parameters[target_index])
    standard_error = float(np.sqrt(variance))
    critical = float(t.ppf(.975, groups - 1))
    interval = [beta - critical * standard_error, beta + critical * standard_error]
    pvalue = float(2 * t.sf(abs(beta / standard_error), groups - 1))
    def finite_exp(value):
        return float(np.exp(value)) if -745 < value < 709 else None
    return {"status": "estimated", "beta": beta, "or": finite_exp(beta), "se_cluster_cr1": standard_error,
            "beta_ci95_t": interval, "or_ci95_t": [finite_exp(value) for value in interval],
            "exponentiation_overflow": any(not -745 < value < 709 for value in [beta, *interval]),
            "p_two_sided_t": pvalue, "df": groups - 1, "covariance": covariance.tolist(),
            "variance_rule": "CR1 G/(G−1), weighted family scores; t(G−1)"}


def fit_conditional(records):
    grouped = defaultdict(list)
    for row in records:
        grouped[row["family_group"]].append(row)
    family_rows = [{"family_group": family, "systems": len(rows), "positive_Y": sum(row["Y"] for row in rows),
                    "contributes": 0 < sum(row["Y"] for row in rows) < len(rows)} for family,rows in sorted(grouped.items())]
    kept = [row for row in family_rows if row["contributes"]]
    output = {"model": "family_equal_conditional_logit", "systems": len(records), "families": len(grouped),
              "contributing_families": len(kept), "contributing_systems": sum(row["systems"] for row in kept),
              "family_diagnostics": family_rows, "controls": ["k_sibling", "k_domain"], "weighting": "mean_g(loglik_g/n_g)"}
    if not kept:
        return {**output, "status": "not_estimable_no_within_family_outcome_variation"}
    designs, outcomes, group_labels, differences = [], [], [], []
    for item in kept:
        family = item["family_group"]
        rows = grouped[family]
        z = np.array([[row["X"], row["k_sibling"], row["k_domain"]] for row in rows], dtype=float)
        y = np.array([row["Y"] for row in rows], dtype=int)
        z -= z.mean(axis=0)
        designs.extend(z); outcomes.extend(y); group_labels.extend([family] * len(rows))
        differences.extend(left - right for left in z[y == 1] for right in z[y == 0])
    design, y = np.array(designs), np.array(outcomes)
    rank = int(np.linalg.matrix_rank(design))
    output["centered_design_rank"] = rank
    if rank != 3:
        return {**output, "status": "not_estimable_rank_deficient_controls_retained"}
    separation = separation_diagnostic(differences)
    output["separation"] = separation
    if separation["separated"] is not False:
        return {**output, "status": "not_estimable_separation" if separation["separated"] else "not_estimable_separation_check_failed"}
    model = ConditionalLogit(y, design, groups=np.array(group_labels))
    evaluators = []
    for group_index, item in enumerate(kept):
        def evaluator(params, group_index=group_index, size=item["systems"]):
            return model.loglike_grp(group_index, params) / size, model.score_grp(group_index, params) / size
        evaluators.append(evaluator)
    result = _fit_objective(evaluators, 3)
    output["optimization_attempts"] = result["attempts"]
    if not result["accepted"]:
        return {**output, "status": "not_estimable_convergence_gate_failed"}
    inference = sandwich_inference(result["parameters"], result["scores"], result["information"])
    return {**output, **inference, "coefficients": dict(zip(("X", "k_sibling", "k_domain"), result["parameters"].tolist())),
            "weighted_family_scores": result["scores"].tolist(), "weighted_information": result["information"].tolist()}


def fit_general_logit(records):
    output = {"model": "family_equal_general_logit_cluster_sensitivity", "systems": len(records),
              "families": len({row["family_group"] for row in records}),
              "interpretation": "聚类标准误不消除谱系混淆；该模型不替代主条件logit。"}
    if not records:
        return {**output, "status": "not_estimable_empty_sample"}
    design = np.array([[1, row["X"], row["k_sibling"], row["k_domain"]] for row in records], dtype=float)
    y = np.array([row["Y"] for row in records])
    rank = int(np.linalg.matrix_rank(design))
    output["design_rank"] = rank
    if rank != 4:
        return {**output, "status": "not_estimable_rank_deficient_controls_retained"}
    separation = separation_diagnostic((2 * y[:,None] - 1) * design)
    output["separation"] = separation
    if separation["separated"] is not False:
        return {**output, "status": "not_estimable_separation" if separation["separated"] else "not_estimable_separation_check_failed"}
    groups = defaultdict(list)
    for index, row in enumerate(records):
        groups[row["family_group"]].append(index)
    evaluators = []
    for family, indices in sorted(groups.items()):
        z, response = design[indices], y[indices]
        def evaluator(params, z=z, response=response):
            linear = z @ params
            return float(np.mean(response * linear - np.logaddexp(0, linear))), z.T @ (response - expit(linear)) / len(z)
        evaluators.append(evaluator)
    result = _fit_objective(evaluators, 4)
    output.update({"families": len(groups), "contributing_families": len(groups), "optimization_attempts": result["attempts"]})
    if not result["accepted"]:
        return {**output, "status": "not_estimable_convergence_gate_failed"}
    return {**output, **sandwich_inference(result["parameters"], result["scores"], result["information"], target_index=1),
            "coefficients": dict(zip(("intercept", "X", "k_sibling", "k_domain"), result["parameters"].tolist())),
            "weighted_family_scores": result["scores"].tolist(), "weighted_information": result["information"].tolist()}


def exact_stratum_permutation(records, permutations=PERMUTATIONS, seed=SEED):
    grouped = defaultdict(list)
    for row in records:
        grouped[(row["family_group"], row["k_sibling"], row["k_domain"])].append(row)
    strata, informative = [], []
    for key, rows in sorted(grouped.items()):
        x, y = np.array([row["X"] for row in rows]), np.array([row["Y"] for row in rows])
        active = len(rows) >= 2 and len(set(x)) > 1 and len(set(y)) > 1
        strata.append({"family_group": key[0], "k_sibling": key[1], "k_domain": key[2],
                       "systems": len(rows), "positive_X": int(x.sum()), "positive_Y": int(y.sum()), "informative": active,
                       "Language_IDs": [row["Language_ID"] for row in rows]})
        if active:
            informative.append((x - x.mean(), y - y.mean()))
    active_families = sorted({row["family_group"] for row in strata if row["informative"]})
    output = {"strata": strata, "informative_strata": len(informative),
              "informative_families": len(active_families), "informative_family_groups": active_families,
              "informative_systems": sum(row["systems"] for row in strata if row["informative"]),
              "permutations": permutations, "seed": seed,
              "null": "同一family,k_sibling,k_domain层内X可交换；与条件logit的线性k控制不同。"}
    if not informative:
        return {**output, "status": "not_identifiable_no_informative_strata", "statistic": None,
                "p_two_sided": None, "unique_permutation_statistics": 0}
    observed = float(sum(x @ y for x,y in informative))
    rng = np.random.default_rng(seed)
    draws = np.zeros(permutations)
    for x,y in informative:
        shuffled = rng.permuted(np.tile(x, (permutations, 1)), axis=1)
        draws += shuffled @ y
    distribution = Counter(float(value) for value in np.round(draws, 12))
    extreme = int(np.sum(np.abs(draws) >= abs(observed) - 1e-12))
    return {**output, "status": "estimated", "statistic": observed,
            "p_two_sided": (1 + extreme) / (1 + permutations), "extreme_permutations": extreme,
            "unique_permutation_statistics": len(distribution),
            "permutation_distribution": [{"statistic": value, "count": count} for value,count in sorted(distribution.items())]}


def holm_two(values):
    if len(values) != 2:
        raise ValueError("主校正族固定为两个16格领域")
    order = sorted(range(2), key=lambda i: 1 if values[i] is None else values[i])
    result, previous = [None, None], 0.
    for rank, index in enumerate(order):
        previous = max(previous, min(1., (2-rank) * (1 if values[index] is None else values[index])))
        if values[index] is not None:
            result[index] = previous
    return result


def build_indicators():
    mapping = load_system_mapping("strict")
    registry = domain_registry()
    coordinate_names = {"cousins16": ("s", "p", "c", "r"),
                        "parent_siblings_age16": ("s", "p", "a_parent", "r"),
                        "parent_siblings_generic8": ("s", "p", "r")}
    sibling_entries = [dict(zip(("s", "a", "r"), atom)) for atom in ATOMS]
    sibling_languages = metric_languages(sibling_entries, ("s", "a", "r"))
    sibling = {}
    raw = pd.read_csv(RAW / "forms.csv", keep_default_na=False)
    needed = set(CATEGORY_ORDER) | {entry["Parameter_ID"] for rows in registry.values() for entry in rows}
    cells = collect_cells(raw, set(mapping.Language_ID), needed)
    for row in mapping.to_dict("records"):
        labels = tuple(map(int, row["rgs"]))
        sibling[row["Language_ID"]] = relative_metrics(labels, sibling_languages)
    rows = []
    for domain, entries in registry.items():
        language = metric_languages(entries, coordinate_names[domain])
        codes = [entry["Parameter_ID"] for entry in entries]
        for row in mapping.to_dict("records"):
            lid = row["Language_ID"]
            coverage = coverage_for_system(lid, codes, cells)
            if not coverage["complete_singleton"]:
                continue
            labels = [next(iter(cells[(lid, code)]["forms"])) for code in codes]
            domain_metrics = relative_metrics(labels, language)
            sibling_sources = coverage_for_system(lid, CATEGORY_ORDER, cells)["common_sources"]
            common_sources = sorted(set(sibling_sources) & set(coverage["common_sources"]))
            rows.append({"domain": domain, "Language_ID": lid, "Glottocode": row["Glottocode"],
                         "family_group": row["family_group"], "family_name": row["family_name"], "macroarea": row["macroarea"],
                         "X": sibling[lid]["q_advantage_r"], "Y": domain_metrics["q_advantage_r"],
                         "k_sibling": sibling[lid]["k"], "k_domain": domain_metrics["k"],
                         **{"sibling_" + key: value for key,value in sibling[lid].items()},
                         **{"domain_" + key: value for key,value in domain_metrics.items()},
                         "same_source_cross_domain": bool(common_sources), "cross_domain_sources": common_sources,
                         "domain_labels_json": json.dumps(labels, ensure_ascii=False)})
    return rows


def analyse_sample(rows):
    descriptions = {}
    for prefix in ("sibling_", "domain_"):
        for metric in ("q_advantage_r", "delta_dl_r", "q_rescue_r", "abs_nonconj",
                       "q_advantage_s", "delta_dl_s", "q_rescue_s"):
            descriptions[prefix + metric] = dict(sorted(Counter(str(row[prefix + metric]) for row in rows).items()))
    return {"systems": len(rows), "families": len({row["family_group"] for row in rows}),
            "joint_XY_counts": {f"{x},{y}": sum(row["X"] == x and row["Y"] == y for row in rows) for x,y in product((0,1),repeat=2)},
            "descriptive_metric_frequencies": descriptions,
            "conditional_logit": fit_conditional(rows), "general_logit_cluster_sensitivity": fit_general_logit(rows),
            "exact_stratum_permutation": exact_stratum_permutation(rows)}


def _write_association_report(result):
    lines = ["# T6：相对性别指标的跨领域关联（探索性）", "", "按独立提交的补充方案实施。X和Y均为固定rel_r相对abs节省文字的二元指示；绝对非合取、连续差、rescue及rel_s完整描述并报，不替换主指标。", "",
             "|领域／样本|系统／谱系|Y有变化谱系／系统|条件logit状态|OR及95%t区间|主β Holm2 p|置换有效层／系统|置换p／Holm2 p|", "|---|---:|---:|---|---|---:|---:|---:|"]
    def number(value):
        return "NA" if value is None else f"{value:.6g}"
    for domain, domain_rows in result["domains"].items():
        for sample, row in domain_rows.items():
            model, permutation = row["conditional_logit"], row["exact_stratum_permutation"]
            interval = model.get("or_ci95_t")
            effect = f"{number(model.get('or'))} [{number(interval[0])},{number(interval[1])}]" if interval else "NA"
            lines.append(f"|{domain}／{sample}|{row['systems']}／{row['families']}|{model['contributing_families']}／{model['contributing_systems']}|{model['status']}|{effect}|{number(model.get('p_holm_two'))}|{permutation['informative_strata']}／{permutation['informative_systems']}|{number(permutation.get('p_two_sided'))}／{number(permutation.get('p_holm_two'))}|")
    lines.extend(["", "主条件模型消去谱系截距，各族条件似然除该族配对系统数，再对有效族平均。双k控制不删除；秩不足、分离或未通过收敛门的模型均不提供推断。合格模型的CR1 sandwich使用加权族score，并用实际贡献族数减1的t分布构造区间。", "", "两个16格领域的主β、一般logit敏感性p和精确分层置换p分别形成三个独立Holm2校正族；generic8和跨域同来源子集不混入主校正族。敏感性行未标Holm2不能视作另一个主检验。", "", "## 一般logit敏感性", "", "|领域／样本|状态|OR及95%t区间|原始p／主两域Holm2 p|", "|---|---|---|---:|"])
    for domain, domain_rows in result["domains"].items():
        for sample, row in domain_rows.items():
            model = row["general_logit_cluster_sensitivity"]
            interval = model.get("or_ci95_t")
            effect = f"{number(model.get('or'))} [{number(interval[0])},{number(interval[1])}]" if interval else "NA"
            lines.append(f"|{domain}／{sample}|{model['status']}|{effect}|{number(model.get('p_two_sided_t'))}／{number(model.get('p_holm_two'))}|")
    lines.extend(["", "一般logit仅将依赖纳入标准误，没有消去共享谱系的混淆；其可估计或较小p不替代主条件模型。", "", "## 数据范围与解释", "", "来源敏感性要求兄弟姐妹八格与目标域全部格点具有同一个共同Source键，而非两个领域分别有不同的完整来源。它仍不能证明原始文献独立调查每个编码格点。", "", "置换层严格固定为谱系与两个k相同，统计为层内中心化X、Y的协方差和。5000次层内洗牌不能扩大有效层数量；无同时变化的X/Y层时记不可识别，不返回p=1。该零假设与条件logit线性控制的β不同。", "", "无法估计或阴性不能证明两领域独立；观察到关联也只涉及固定描述语言的结构节约，不证明说话者实际复用q或存在特定历史传播路径。父母同胞领域的长幼相对父／母，堂表亲p⊕c与ego/referent的q不同。", "", "逐系统指标及所有描述性敏感性保存在cross_domain_indicators.csv；family_model_diagnostics.csv与permutation_strata.csv保留有效及排除单位。完整优化尝试、分离LP、输入哈希和置换统计分布见association_results.json。"])
    lines.extend(["", "## 主指标与有效信息范围", "", "|主样本领域|X=1系统／总数|Y=1系统／总数|置换有效谱系|不同置换统计值数|", "|---|---:|---:|---:|---:|"])
    for domain, domain_rows in result["domains"].items():
        row = domain_rows["all_complete_singleton"]
        xy, permutation = row["joint_XY_counts"], row["exact_stratum_permutation"]
        lines.append(f"|{domain}|{xy['1,0']+xy['1,1']}／{row['systems']}|{xy['0,1']+xy['1,1']}／{row['systems']}|{permutation['informative_families']}|{permutation['unique_permutation_statistics']}|")
    lines.extend(["", "置换的小p不能缩窄条件模型在少数信息谱系下的宽区间，也不能证明未出现正指标的其他领域同样有关联。完整有效层的谱系和系统ID均保留，不把5000次洗牌当作5000个独立谱系。"])
    (OUT / "association_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("all",), default="all")
    parser.parse_args()
    guard = verify_t6_plan()
    specification = {"phase": "all", "status": "探索性", "X_Y": "q_advantage_r",
                     "primary_domains": list(PRIMARY_DOMAINS), "family_equal_conditional": True,
                     "controls": ["k_sibling", "k_domain"], "holm_family_size": 2,
                     "permutations": PERMUTATIONS, "seed": SEED}
    with logged_run("T6_association", specification) as metrics:
        started = utc_now()
        rows = build_indicators()
        domains = {}
        for domain in domain_registry():
            subset = [row for row in rows if row["domain"] == domain]
            domains[domain] = {"all_complete_singleton": analyse_sample(subset),
                               "same_source_sensitivity": analyse_sample([row for row in subset if row["same_source_cross_domain"]])}
        for model_name, p_key in (("conditional_logit", "p_two_sided_t"),
                                  ("general_logit_cluster_sensitivity", "p_two_sided_t"),
                                  ("exact_stratum_permutation", "p_two_sided")):
            values = [domains[domain]["all_complete_singleton"][model_name].get(p_key) for domain in PRIMARY_DOMAINS]
            for domain, adjusted in zip(PRIMARY_DOMAINS, holm_two(values)):
                domains[domain]["all_complete_singleton"][model_name].update({"p_holm_two": adjusted, "holm_scope": "two_primary_16_cell_domains"})
        result = {"task": "T6_association", "started_at": started, "completed_at": utc_now(),
                  "guard": guard, "specification": specification, "domains": domains,
                  "input_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in
                                   [RAW/"forms.csv", RAW/"parameters.csv", RESULTS/"t1/systems_to_partition.csv", T6_PLAN]},
                  "source_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in
                                    [Path(__file__), Path(__file__).with_name("domain_feasibility.py")]},
                  "git_commit": git_commit(), "script": "analysis/v3/cross_domain.py"}
        OUT.mkdir(parents=True, exist_ok=True)
        save_json(OUT / "association_results.json", result)
        pd.DataFrame([{**row, "cross_domain_sources": json.dumps(row["cross_domain_sources"], ensure_ascii=False)} for row in rows]).to_csv(OUT / "cross_domain_indicators.csv", index=False)
        family_rows, strata, model_rows = [], [], []
        for domain, samples in domains.items():
            for sample, analysis in samples.items():
                family_rows.extend({"domain": domain, "sample": sample, **row} for row in analysis["conditional_logit"]["family_diagnostics"])
                strata.extend({"domain": domain, "sample": sample, **row, "Language_IDs": json.dumps(row["Language_IDs"])} for row in analysis["exact_stratum_permutation"]["strata"])
                for name in ("conditional_logit", "general_logit_cluster_sensitivity"):
                    model = analysis[name]
                    model_rows.append({"domain": domain, "sample": sample, "model": name,
                                       **{key: model.get(key) for key in ("status", "systems", "families", "contributing_families", "contributing_systems", "beta", "or", "se_cluster_cr1", "beta_ci95_t", "or_ci95_t", "p_two_sided_t", "p_holm_two", "df")}})
        pd.DataFrame(family_rows).to_csv(OUT / "family_model_diagnostics.csv", index=False)
        pd.DataFrame(strata).to_csv(OUT / "permutation_strata.csv", index=False)
        pd.DataFrame(model_rows).to_csv(OUT / "association_models.csv", index=False)
        _write_association_report(result)
        metrics.update({"domains": {domain: {"systems": domains[domain]["all_complete_singleton"]["systems"],
                                              "conditional_status": domains[domain]["all_complete_singleton"]["conditional_logit"]["status"],
                                              "permutation_status": domains[domain]["all_complete_singleton"]["exact_stratum_permutation"]["status"]} for domain in domains}})
        print(json.dumps(metrics, ensure_ascii=False))


if __name__ == "__main__":
    main()
