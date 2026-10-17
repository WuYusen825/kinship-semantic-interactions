"""第三版T2：精确划分分布、嵌套选择和留出评估；只写results/t2。

先运行 --phase cv --sample strict --weighting family --validation family。
--phase all 运行全部划分模型及检查；--phase compare 读取T5d作Q3/Q4对照。
"""
from __future__ import annotations

import os
for _key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_key] = "1"

import argparse
from collections import Counter
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path
import sys
import time
import subprocess

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import common
from partition_model import (FeatureSpace, FitResult, fit_maxent, pair_probabilities,
                             seven_cell_rates, m2_logit_contrasts)

OUTPUT = common.RESULTS / "t2"
SOLVER_PROFILE = "refined"
REFINEMENT_COMMIT = "2b59811c"
ALPHAS = (0.0, 0.01, 0.1, 1.0)
DESCRIPTIVE = ("A2", "A3r", "A3s", "A4", "A5r", "A5s", "A6")
MODELS = ("A0", "A1", *DESCRIPTIVE, "BASE", "A7")
FEATURES = {"A0": (), "A1": ("k", "k_squared"),
            "A2": ("k", "k_squared", "conj_abs"),
            "A3r": ("k", "k_squared", "conj_rel_r"),
            "A3s": ("k", "k_squared", "conj_rel_s"),
            "A4": ("k", "k_squared", "DL_abs"),
            "A5r": ("k", "k_squared", "DL_rel_r"),
            "A5s": ("k", "k_squared", "DL_rel_s"),
            "A6": ("k", "k_squared", "DL_all")}
M2_COLUMNS = ("intercept", "Dr", "Da", "De", "DrDa", "DrDe", "DaDe")


def verify_refinement():
    path = common.ROOT / "docs/numerical_refinement_v3.md"
    commit = subprocess.check_output(["git", "rev-parse", REFINEMENT_COMMIT], cwd=common.ROOT, text=True).strip()
    frozen = subprocess.check_output(["git", "show", f"{commit}:docs/numerical_refinement_v3.md"], cwd=common.ROOT)
    if hashlib.sha256(frozen).hexdigest() != common.sha256(path):
        raise RuntimeError("数值精化附录与其单独提交不一致")
    subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=common.ROOT, check=True)
    return {"commit": commit, "sha256": common.sha256(path),
            "status": "postdiagnostic_numerical_refinement_not_original_plan"}


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [clean(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    return value


def save(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
    common.save_json(temporary, clean(value))
    os.replace(temporary, path)


def run_spec(value):
    return {**value, "solver_profile": SOLVER_PROFILE,
            "output_root": str(OUTPUT.relative_to(common.ROOT)),
            "plan_commit": common.verify_analysis_plan()["plan_commit"],
            "refinement": verify_refinement() if SOLVER_PROFILE == "refined" else None}


def score(values, systems, weighting):
    values = np.asarray(values, dtype=float)
    if len(values) != len(systems) or not len(values) or not np.isfinite(values).all():
        return None
    return float(common.system_weights(systems, weighting) @ values)


def make_spaces(catalogue):
    table = catalogue.copy()
    table["k_squared"] = table.k ** 2
    spaces = {m: FeatureSpace.from_raw(table[list(cols)].to_numpy(dtype=float), cols)
              for m, cols in FEATURES.items()}
    for base in DESCRIPTIVE:
        columns = (*FEATURES[base], "P2", "P3", "P4")
        spaces["A7@" + base] = FeatureSpace.from_raw(table[list(columns)].to_numpy(dtype=float), columns)
    return spaces


def choose_configuration(candidates, spaces):
    """Apply the frozen score tolerance, stronger alpha, dimension and model order."""
    usable = [r for r in candidates if r["score"] is not None and np.isfinite(r["score"])]
    if not usable:
        return None
    maximum = max(r["score"] for r in usable)
    tied = [r for r in usable if maximum - r["score"] <= 1e-10]
    order = {m: i for i, m in enumerate(("A1", *DESCRIPTIVE))}
    return min(tied, key=lambda r: (-r["alpha"], spaces[r["space"]].dimension,
                                   order.get(r["model"], 99)))


def inner_splits(systems, train_indices):
    frame = systems.iloc[train_indices]
    if frame.family_group.nunique() < 3:
        raise ValueError("内层谱系数少于3，不能执行预定选择")
    splits = []
    for fold, (a, b) in enumerate(GroupKFold(3).split(frame, groups=frame.family_group)):
        train, test = np.asarray(train_indices)[a], np.asarray(train_indices)[b]
        if set(systems.iloc[train].family_group) & set(systems.iloc[test].family_group):
            raise RuntimeError("内层谱系泄漏")
        splits.append((fold, train, test))
    return splits


class FitHub:
    def __init__(self, systems, spaces, weighting, output):
        self.systems, self.spaces, self.weighting = systems, spaces, weighting
        self.cache = {}
        self.count = 0
        self.failed = 0
        self.handle = gzip.open(output / "fit_diagnostics.jsonl.gz", "wt", encoding="utf8")

    def fit(self, model, indices, alpha, split_id):
        indices = np.asarray(indices, dtype=int)
        cache_key = (model, tuple(indices.tolist()), float(alpha))
        if cache_key in self.cache:
            return self.cache[cache_key]
        train = self.systems.iloc[indices]
        weights = common.system_weights(train, self.weighting)
        fitted = fit_maxent(self.spaces[model], train.partition_id.to_numpy(), weights, alpha,
                            precision_retry=SOLVER_PROFILE == "refined")
        self.count += 1
        self.failed += not fitted.converged
        record = {"fit_id": self.count, "space": model, "split_id": split_id,
                  "alpha": alpha, "train_systems": len(train),
                  "train_families": int(train.family_group.nunique()),
                  "weight_sum": float(weights.sum()), "converged": fitted.converged,
                  "solver_profile": SOLVER_PROFILE,
                  "theta_standardized": fitted.theta.tolist(),
                  "raw_coefficients": fitted.raw_coefficients,
                  "diagnostics": fitted.diagnostics}
        self.handle.write(json.dumps(clean(record), ensure_ascii=False, allow_nan=False) + "\n")
        self.handle.flush()
        self.cache[cache_key] = fitted
        return fitted

    def close(self):
        self.handle.close()


def select_models(hub, train_indices, prefix):
    frame = hub.systems.iloc[train_indices]
    rows = []
    splits = inner_splits(hub.systems, train_indices)
    manifest = []
    for fold, train, test in splits:
        manifest.append({"split_id": f"{prefix}/inner{fold}",
                         "train_ids": hub.systems.iloc[train].Language_ID.tolist(),
                         "test_ids": hub.systems.iloc[test].Language_ID.tolist(),
                         "genealogy_isolated": True})
    lookup = {value: i for i, value in enumerate(train_indices)}

    def evaluate(model, model_space):
        result = []
        for alpha in ALPHAS:
            out = np.full(len(train_indices), np.nan)
            success = 0
            for fold, train, test in splits:
                fitted = hub.fit(model_space, train, alpha, f"{prefix}/inner{fold}")
                if fitted.converged:
                    positions = [lookup[i] for i in test]
                    out[positions] = fitted.log_probabilities[hub.systems.iloc[test].partition_id.to_numpy()]
                    success += 1
            row = {"model": model, "space": model_space, "alpha": alpha,
                   "score": score(out, frame, hub.weighting), "successful_inner_folds": success,
                   "scoring": "pooled_inner_OOF_then_requested_system_weights", "outer_fold": prefix}
            rows.append(row)
            result.append(row)
        return choose_configuration(result, hub.spaces)

    choices = {model: evaluate(model, model) for model in ("A1", *DESCRIPTIVE)}
    # Apply the tolerance once against the global best descriptive candidate.
    # Selecting a near-tied alpha per model first would accumulate tolerances.
    base = choose_configuration([row for row in rows if row["model"] in DESCRIPTIVE], hub.spaces)
    # The choice of base is made WITHOUT position features.  A7 scores cannot
    # send selection back to a different base architecture.
    a7 = evaluate("A7", "A7@" + base["model"]) if base is not None else None
    return choices, base, a7, rows, manifest


def outer_splits(systems, validation):
    column = "macroarea" if validation == "area" else "fold_" + validation
    result = []
    for fold in sorted(systems[column].unique()):
        test = np.flatnonzero(systems[column].eq(fold).to_numpy())
        train = np.flatnonzero(~systems[column].eq(fold).to_numpy())
        if not len(test) or not len(train):
            raise ValueError("空外层训练或测试折")
        if validation == "family" and set(systems.iloc[train].family_group) & set(systems.iloc[test].family_group):
            raise RuntimeError("外层谱系泄漏")
        result.append((str(fold), train, test))
    return result


def sharing_matrix(catalogue, pair_meta):
    labels = np.asarray(catalogue.labels.tolist(), dtype=int)
    return (labels[:, pair_meta.atom_i.to_numpy()] == labels[:, pair_meta.atom_j.to_numpy()]).astype(float)


def score_fit(fitted, observed_ids, same):
    if not fitted.converged:
        return np.full(len(observed_ids), np.nan), np.full(len(observed_ids), np.nan), np.full(same.shape[1], np.nan)
    pair_p = pair_probabilities(fitted.probabilities, same)
    clipped = np.clip(pair_p, 1e-15, 1 - 1e-15)
    outcomes = same[observed_ids]
    losses = -(outcomes * np.log(clipped) + (1 - outcomes) * np.log1p(-clipped)).mean(axis=1)
    return fitted.log_probabilities[observed_ids], losses, pair_p


def comparisons_from_scores(scores, systems, weighting):
    comparisons = []
    indexed = {}
    ids = systems.Language_ID.tolist()
    for (model, penalty), group in scores.groupby(["model", "penalty"]):
        indexed[model, penalty] = group.set_index("Language_ID").reindex(ids)
    for penalty in ("selected", *[f"fixed_{a:g}" for a in ALPHAS]):
        pairs = [(model, reference) for model in MODELS if model != "BASE"
                 for reference in ("A0", "A1") if model != reference]
        pairs += [("A3r", "A2"), ("A3s", "A2"), ("A5r", "A4"), ("A5s", "A4"), ("A7", "BASE")]
        for model, reference in pairs:
            left = indexed.get((model, penalty))
            right = indexed.get((reference, "selected" if reference == "BASE" else penalty))
            if left is None or right is None:
                continue
            difference = left.log_probability.to_numpy() - right.log_probability.to_numpy()
            row = {"comparison": model + "-" + reference, "penalty": penalty,
                   "gain": score(difference, systems, weighting), "systems": len(systems),
                   "scope": "fixed OOF, family cluster resampling, no refitting"}
            if np.isfinite(difference).all():
                interval = common.bootstrap_grouped(difference, systems.family_group, weighting)
                row.update(ci95=interval["ci95"], evaluable=True,
                           interval_excludes_zero_positive=interval["ci95"][0] > 0)
            else:
                row.update(ci95=None, evaluable=False,
                           reason="预定测试样本存在非收敛拟合；未删除系统或改换估计器")
            comparisons.append(row)
    return comparisons


def run_cv(sample, weighting, validation, catalogue, spaces, pair_meta):
    setting = f"{sample}_{weighting}_{validation}"
    output = OUTPUT / ("cv_" + setting)
    output.mkdir(parents=True, exist_ok=True)
    systems = common.load_system_mapping(sample).reset_index(drop=True)
    if validation == "area":
        systems = systems[systems.macroarea.ne("")].reset_index(drop=True)
    same = sharing_matrix(catalogue, pair_meta)
    hub = FitHub(systems, spaces, weighting, output)
    score_rows, probability_rows, inner_rows, selections, manifests = [], [], [], [], []
    with common.logged_run("T2_CV", run_spec({"sample": sample, "weighting": weighting, "validation": validation,
                                             "alphas": ALPHAS})) as metrics:
        try:
            for fold, train, test in outer_splits(systems, validation):
                choices, base, a7, inner, inner_manifest = select_models(hub, train, "outer" + fold)
                inner_rows.extend(inner)
                manifests.extend(inner_manifest)
                manifests.append({"split_id": "outer" + fold,
                                  "train_ids": systems.iloc[train].Language_ID.tolist(),
                                  "test_ids": systems.iloc[test].Language_ID.tolist(),
                                  "train_families": sorted(systems.iloc[train].family_group.unique()),
                                  "test_families": sorted(systems.iloc[test].family_group.unique()),
                                  "genealogy_isolated": validation == "family"})
                selections.append({"fold": fold, "base": base, "A7": a7, "models": choices})
                for model in MODELS:
                    for penalty in ("selected", *[f"fixed_{a:g}" for a in ALPHAS]):
                        if model == "BASE" and penalty != "selected":
                            continue
                        configuration = base if model == "BASE" else a7 if model == "A7" else choices.get(model)
                        model_space = "A0" if model == "A0" else configuration["space"] if configuration else None
                        alpha = (0.0 if model == "A0" else configuration["alpha"] if configuration else None) if penalty == "selected" else float(penalty[6:])
                        # Fixed A7 penalties retain the independently selected base.
                        if model == "A7" and base is not None:
                            model_space = "A7@" + base["model"]
                        if penalty != "selected" and model in FEATURES:
                            model_space = model
                        fitted = hub.fit(model_space, train, alpha, "outer" + fold) if model_space is not None and alpha is not None else None
                        if fitted is None:
                            log_p, losses, pair_p = np.full(len(test), np.nan), np.full(len(test), np.nan), np.full(28, np.nan)
                        else:
                            log_p, losses, pair_p = score_fit(fitted, systems.iloc[test].partition_id.to_numpy(), same)
                        for j, index in enumerate(test):
                            meta = systems.iloc[index]
                            score_rows.append({"sample": sample, "weighting": weighting, "validation": validation,
                                               "fold": fold, "model": model, "penalty": penalty, "alpha": alpha,
                                               "selected_base": base["model"] if base else None,
                                               "Language_ID": meta.Language_ID, "Glottocode": meta.Glottocode,
                                               "family_group": meta.family_group, "macroarea": meta.macroarea,
                                               "partition_id": int(meta.partition_id), "log_probability": log_p[j],
                                               "pair_logloss": losses[j], "converged": bool(fitted and fitted.converged)})
                        for j, pair in pair_meta.iterrows():
                            probability_rows.append({"fold": fold, "model": model, "penalty": penalty,
                                                     "pair_index": int(j), "category_a": pair.category_a,
                                                     "category_b": pair.category_b, "pattern": pair.pattern,
                                                     "probability": pair_p[j]})
                print(f"T2 {setting}: outer {fold} saved; fits={hub.count}, failed={hub.failed}", flush=True)
                pd.DataFrame(score_rows).to_csv(output / "oof_system_scores.csv.gz", index=False)
                pd.DataFrame(probability_rows).to_csv(output / "fold_pair_probabilities.csv", index=False)
                save(output / "selection.json", selections)
                save(output / "fold_manifest.json", manifests)
            scores = pd.DataFrame(score_rows)
            ladder = []
            for (model, penalty), frame in scores.groupby(["model", "penalty"], sort=False):
                frame = frame.set_index("Language_ID").reindex(systems.Language_ID)
                ladder.append({"model": model, "penalty": penalty,
                               "mean_log_probability": score(frame.log_probability, systems, weighting),
                               "derived_pair_logloss": score(frame.pair_logloss, systems, weighting),
                               "evaluable": bool(np.isfinite(frame.log_probability).all())})
            comparisons = comparisons_from_scores(scores, systems, weighting)
            result = {"setting": setting, "sample": sample, "weighting": weighting, "validation": validation,
                      "systems": len(systems), "families": int(systems.family_group.nunique()),
                      "ladder": ladder, "comparisons": comparisons, "fits": hub.count, "failed_fits": hub.failed,
                      "A6_lambda": {"values": [0, 1, 2, 3], "status": "identical",
                                    "reason": "constant 4*lambda cancels in exact normalization; not refitted"},
                      "unweighted": {"identical_to": "language", "refitted": False},
                      "seed": common.SEED, "bootstrap_replicates": common.BOOTSTRAP_REPLICATES}
            result["selected_models"] = {r["model"]: r for r in ladder if r["penalty"] == "selected"}
            result["selected_comparisons"] = {r["comparison"]: r for r in comparisons if r["penalty"] == "selected"}
            save(output / "summary.json", result)
            pd.DataFrame(inner_rows).to_csv(output / "inner_selection.csv", index=False)
            pd.DataFrame(ladder).to_csv(output / "ladder.csv", index=False)
            pd.DataFrame(comparisons).to_csv(output / "comparisons.csv", index=False)
            metrics.update(systems=len(systems), fits=hub.count, failed_fits=hub.failed,
                           selected_ladder=[r for r in ladder if r["penalty"] == "selected"])
            return result
        finally:
            hub.close()


def predictive_statistics(catalogue):
    names, columns = [], []
    for k in range(1, 9):
        names.append(f"k_{k}")
        columns.append(catalogue.k.eq(k).to_numpy(dtype=float))
    for language in ("abs", "rel_r", "rel_s", "all"):
        names.append("conj_" + language)
        columns.append(catalogue["conj_" + language].to_numpy(dtype=float))
    for direction in ("P2", "P3", "P4"):
        for label, value in (("predicted", 1), ("reverse", -1), ("not_applicable", 0)):
            names.append(direction + "_" + label)
            columns.append(catalogue[direction].eq(value).to_numpy(dtype=float))
    return names, np.column_stack(columns)


def predictive_check(fitted, systems, names, statistics):
    """Independent synthetic systems, with the observed sample's fixed weights."""
    if not fitted.converged:
        return []
    weights = common.system_weights(systems, systems.attrs["weighting"])
    observed = weights @ statistics[systems.partition_id.to_numpy()]
    expected = fitted.probabilities @ statistics
    generator = np.random.default_rng(common.SEED)
    draws = np.empty((common.BOOTSTRAP_REPLICATES, len(names)))
    for start in range(0, len(draws), 128):
        stop = min(start + 128, len(draws))
        indices = generator.choice(len(fitted.probabilities), size=(stop - start, len(systems)),
                                   p=fitted.probabilities)
        draws[start:stop] = np.einsum("bnd,n->bd", statistics[indices], weights, optimize=False)
    rows = []
    for j, name in enumerate(names):
        interval = np.quantile(draws[:, j], [.025, .975])
        rows.append({"statistic": name, "observed": observed[j], "model_expected": expected[j],
                     "synthetic_mean": draws[:, j].mean(), "predictive_ci95": interval.tolist(),
                     "inside_interval": bool(interval[0] <= observed[j] <= interval[1]),
                     "synthetic_samples": len(draws), "sample_size": len(systems),
                     "scope": "MLE fitted-distribution simulation; not Bayesian posterior"})
    for direction in ("P2", "P3", "P4"):
        a, b = names.index(direction + "_predicted"), names.index(direction + "_reverse")
        denominator = draws[:, a] + draws[:, b]
        available = denominator > 0
        values = draws[available, a] / denominator[available]
        obs_denominator, exp_denominator = observed[a] + observed[b], expected[a] + expected[b]
        rows.append({"statistic": direction + "_predicted_among_applicable",
                     "observed": observed[a] / obs_denominator if obs_denominator else None,
                     "model_expected": expected[a] / exp_denominator if exp_denominator else None,
                     "predictive_ci95": np.quantile(values, [.025, .975]).tolist() if len(values) else None,
                     "synthetic_samples": len(draws), "valid_nonempty_denominator_samples": int(available.sum()),
                     "scope": "conditional directional proportion; empty synthetic denominators recorded"})
    return rows


def coefficient_bootstrap(space, systems, weighting, alpha, output):
    """One fixed selected A7 specification; each resampled cluster gets equal mass."""
    groups = sorted(systems.family_group.unique())
    indices = {group: np.flatnonzero(systems.family_group.eq(group).to_numpy()) for group in groups}
    generator = np.random.default_rng(common.SEED)
    sampled = generator.integers(0, len(groups), size=(common.BOOTSTRAP_REPLICATES, len(groups)))
    coefficients, statuses = [], Counter()
    with gzip.open(output / "coefficient_bootstrap_diagnostics.jsonl.gz", "wt", encoding="utf8") as handle:
        for replicate, draw in enumerate(sampled):
            counts = np.bincount(draw, minlength=len(groups))
            weights = np.zeros(len(systems))
            for j, group in enumerate(groups):
                weights[indices[group]] = counts[j] / (len(groups) * len(indices[group]))
            fitted = fit_maxent(space, systems.partition_id.to_numpy(), weights, alpha,
                                precision_retry=SOLVER_PROFILE == "refined")
            status = fitted.diagnostics["status"]
            statuses[status] += 1
            row = {"replicate": replicate, "converged": fitted.converged, "status": status,
                   "sampled_distinct_families": int(np.count_nonzero(counts)),
                   "P2": fitted.raw_coefficients.get("P2", float("nan")),
                   "P3": fitted.raw_coefficients.get("P3", float("nan")),
                   "P4": fitted.raw_coefficients.get("P4", float("nan"))}
            coefficients.append(row)
            handle.write(json.dumps(clean({**row, "family_multiplicities": counts.tolist(),
                                           "diagnostics": fitted.diagnostics}), ensure_ascii=False, allow_nan=False) + "\n")
            if (replicate + 1) % 500 == 0:
                handle.flush()
                pd.DataFrame(coefficients).to_csv(output / "coefficient_bootstrap.csv.gz", index=False)
                print(f"T2 coefficient bootstrap {replicate + 1}/{len(sampled)}; statuses={dict(statuses)}", flush=True)
    frame = pd.DataFrame(coefficients)
    frame.to_csv(output / "coefficient_bootstrap.csv.gz", index=False)
    success = frame.converged.to_numpy(dtype=bool)
    enough = bool(success.mean() >= .95 and space.rank == space.dimension)
    intervals = {}
    for term in ("P2", "P3", "P4"):
        values = frame.loc[success, term].to_numpy(dtype=float)
        intervals[term] = {"ci95": np.quantile(values, [.025, .975]).tolist() if enough else None,
                           "bonferroni_ci_98_333333": np.quantile(values, [.05 / 6, 1 - .05 / 6]).tolist() if enough else None,
                           "expected_sign": "positive", "successful_replicates": int(success.sum()),
                           "positive_ci95": bool(enough and np.quantile(values, .025) > 0),
                           "positive_adjusted_ci": bool(enough and np.quantile(values, .05 / 6) > 0)}
    return {"replicates": len(frame), "successful_replicates": int(success.sum()),
            "success_proportion": float(success.mean()), "statuses": dict(statuses),
            "report_intervals": enough, "intervals": intervals, "alpha": alpha,
            "feature_space": space.metadata(), "seed": common.SEED,
            "scope": "fixed full-sample selected base and alpha; no selection uncertainty; no replacement of failed draws"}


def run_full(sample, weighting, catalogue, spaces, pair_meta):
    setting = f"{sample}_{weighting}"
    output = OUTPUT / ("full_" + setting)
    output.mkdir(parents=True, exist_ok=True)
    systems = common.load_system_mapping(sample).reset_index(drop=True)
    systems.attrs["weighting"] = weighting
    weights = common.system_weights(systems, weighting)
    same = sharing_matrix(catalogue, pair_meta)
    empirical_pairs = weights @ same[systems.partition_id.to_numpy()]
    codes = pair_meta.pattern.astype(str).to_numpy()
    cell_order = sorted(set(codes))
    design = pair_meta.groupby("pattern", sort=True)[list(M2_COLUMNS)].first().to_numpy(dtype=float)
    empirical_cells = seven_cell_rates(empirical_pairs, codes)
    empirical_contrast = m2_logit_contrasts(np.array([empirical_cells[c] for c in cell_order]), design, M2_COLUMNS)
    hub = FitHub(systems, spaces, weighting, output)
    with common.logged_run("T2_FULL", run_spec({"sample": sample, "weighting": weighting,
                                      "predictive_replicates": common.BOOTSTRAP_REPLICATES,
                                      "coefficient_bootstrap": sample == "strict" and weighting == "family"})) as metrics:
        try:
            indices = np.arange(len(systems))
            choices, base, a7, inner, manifest = select_models(hub, indices, "full")
            save(output / "selection.json", {"base": base, "A7": a7, "models": choices})
            save(output / "fold_manifest.json", manifest)
            pd.DataFrame(inner).to_csv(output / "inner_selection.csv", index=False)
            names, statistics = predictive_statistics(catalogue)
            distribution_rows, coefficient_rows, pair_rows, contrast_rows, predictive_rows = [], [], [], [], []
            fitted_models, model_summaries = {}, {}
            for model in MODELS:
                configuration = base if model == "BASE" else a7 if model == "A7" else choices.get(model)
                model_space = "A0" if model == "A0" else configuration["space"] if configuration else None
                alpha = 0.0 if model == "A0" else configuration["alpha"] if configuration else None
                fitted = hub.fit(model_space, indices, alpha, "full") if model_space is not None else None
                if fitted is None or not fitted.converged:
                    model_summaries[model] = {"converged": False, "alpha": alpha,
                                              "reason": "全样本拟合或内层选择未通过预定数值门"}
                    continue
                fitted_models[model] = fitted
                log_p, pair_loss, pair_p = score_fit(fitted, systems.partition_id.to_numpy(), same)
                model_summaries[model] = {"converged": True, "space": model_space, "alpha": alpha,
                                          "mean_log_probability": score(log_p, systems, weighting),
                                          "derived_pair_logloss": score(pair_loss, systems, weighting),
                                          "raw_coefficients": fitted.raw_coefficients,
                                          "gradient_max": fitted.gradient_max,
                                          "normalization_error": fitted.normalization_error}
                for partition_id, probability in enumerate(fitted.probabilities):
                    distribution_rows.append({"partition_id": partition_id, "model": model, "probability": probability})
                for j, term in enumerate(spaces[model_space].active_names):
                    coefficient_rows.append({"model": model, "space": model_space, "alpha": alpha,
                                             "feature": term, "coefficient_raw": fitted.raw_coefficients[term],
                                             "coefficient_standardized": fitted.theta[j]})
                cells = seven_cell_rates(pair_p, codes)
                contrasts = m2_logit_contrasts(np.array([cells[c] for c in cell_order]), design, M2_COLUMNS)
                for term, value in contrasts["coefficients"].items():
                    contrast_rows.append({"model": model, "term": term, "generated_gamma": value,
                                          "observed_seven_cell_gamma": empirical_contrast["coefficients"][term],
                                          "generated_minus_observed": value - empirical_contrast["coefficients"][term],
                                          "saturated_projection_residual": contrasts["max_abs_residual"]})
                for j, pair in pair_meta.iterrows():
                    cell_mask = codes == str(pair.pattern)
                    pair_rows.append({"model": model, "pair_index": int(j), "category_a": pair.category_a,
                                      "category_b": pair.category_b, "pattern": pair.pattern,
                                      "generated_probability": pair_p[j], "observed_probability": empirical_pairs[j],
                                      "generated_within_cell_range": float(np.ptp(pair_p[cell_mask])),
                                      "observed_within_cell_range": float(np.ptp(empirical_pairs[cell_mask]))})
                # BASE duplicates an already simulated descriptive model exactly.
                if model != "BASE":
                    for row in predictive_check(fitted, systems, names, statistics):
                        predictive_rows.append({"model": model, **row})
                print(f"T2 {setting}: full {model} fitted and predictive checks saved", flush=True)
            pd.DataFrame(distribution_rows).to_csv(output / "partition_distributions.csv.gz", index=False)
            pd.DataFrame(coefficient_rows).to_csv(output / "coefficients.csv", index=False)
            pd.DataFrame(pair_rows).to_csv(output / "pair_predictions.csv", index=False)
            pd.DataFrame(contrast_rows).to_csv(output / "mixture_logit_contrasts.csv", index=False)
            pd.DataFrame(predictive_rows).to_csv(output / "predictive_checks.csv", index=False)
            result = {"setting": setting, "sample": sample, "weighting": weighting,
                      "systems": len(systems), "families": int(systems.family_group.nunique()),
                      "selected_base": base, "selected_A7": a7, "models": model_summaries,
                      "empirical_seven_cells": empirical_cells, "empirical_M2_contrast": empirical_contrast,
                      "contrasts": contrast_rows, "predictive_checks": predictive_rows,
                      "coefficient_bootstrap": None, "fits": hub.count, "failed_fits": hub.failed,
                      "A6_lambda": {"values": [0, 1, 2, 3], "status": "identical", "refitted": False},
                      "unweighted": {"identical_to": "language", "refitted": False}}
            # Save point results before the 5000 refits so the main analysis is
            # inspectable while its interval calculation is still running.
            save(output / "summary.json", result)
            collect_results()
            if sample == "strict" and weighting == "family" and "A7" in fitted_models:
                bootstrap = coefficient_bootstrap(spaces[a7["space"]], systems, weighting, a7["alpha"], output)
                result["coefficient_bootstrap"] = bootstrap
                save(output / "summary.json", result)
            metrics.update(fits=hub.count, failed_fits=hub.failed, models=model_summaries,
                           bootstrap_success=result["coefficient_bootstrap"]["success_proportion"] if result["coefficient_bootstrap"] else None)
            return result
        finally:
            hub.close()


def run_pair_comparisons(catalogue, pair_meta):
    """Q3: match systems AND inherited folds before computing paired losses."""
    output = OUTPUT / "pair_comparisons"
    output.mkdir(parents=True, exist_ok=True)
    pair_source = common.RESULTS / "t5/strict_language_scores.csv"
    strict_full_source = common.RESULTS / "t5/strict_fullfit.json"
    reference = pd.read_csv(pair_source, keep_default_na=False)
    rows, alignment = [], []
    with common.logged_run("T2_PAIR_COMPARISON", run_spec({"pair_source": str(pair_source.relative_to(common.ROOT)),
                                                          "margin_nats": 0.0, "bootstrap": 5000})) as metrics:
        for weighting in ("family", "language"):
            for validation in ("family", "area", "language"):
                setting = f"strict_{weighting}_{validation}"
                source = OUTPUT / ("cv_" + setting) / "oof_system_scores.csv.gz"
                scores = pd.read_csv(source, keep_default_na=False)
                scores = scores[scores.penalty.eq("selected")]
                pairs = reference[reference.weighting.eq(weighting) & reference.validation.eq(validation)].copy()
                if pairs.Language_ID.duplicated().any():
                    raise RuntimeError("T5d同规格出现重复系统")
                systems = common.load_system_mapping("strict").reset_index(drop=True)
                if validation == "area":
                    systems = systems[systems.macroarea.ne("")].reset_index(drop=True)
                expected = set(systems.Language_ID)
                if set(pairs.Language_ID) != expected:
                    raise RuntimeError("T2与T5d测试总体不同；拒绝通过删行匹配")
                for model, group in scores.groupby("model", sort=False):
                    if group.Language_ID.duplicated().any() or set(group.Language_ID) != expected:
                        raise RuntimeError("T2逐模型缺失或重复预定测试系统")
                    joint = group.merge(pairs, on="Language_ID", validate="one_to_one", suffixes=("_partition", "_pair"))
                    joint = joint.set_index("Language_ID").reindex(systems.Language_ID)
                    def fold_values(series):
                        return series.astype(str).map(lambda x: str(int(float(x))) if validation != "area" else x)
                    if not fold_values(joint.fold_partition).equals(fold_values(joint.fold_pair)):
                        raise RuntimeError("T2与T5d分折不一致")
                    if not joint.family_group_partition.eq(joint.family_group_pair).all():
                        raise RuntimeError("T2与T5d谱系标签不一致")
                    alignment.append({"setting": setting, "model": model, "systems": len(joint),
                                      "same_systems": True, "same_folds": True, "same_families": True})
                    partition_loss = pd.to_numeric(joint.pair_logloss, errors="coerce").to_numpy()
                    for pair_model in ("M0", "M1", "M2", "M3", "M4"):
                        pair_loss = pd.to_numeric(joint["loss_" + pair_model], errors="coerce").to_numpy()
                        difference = partition_loss - pair_loss
                        row = {"setting": setting, "sample": "strict", "weighting": weighting,
                               "validation": validation, "partition_model": model, "pair_model": pair_model,
                               "systems": len(joint), "loss_difference": score(difference, systems, weighting),
                               "partition_logloss": score(partition_loss, systems, weighting),
                               "pair_model_logloss": score(pair_loss, systems, weighting),
                               "definition": "partition-derived pair loss minus pair-model loss; lower is better",
                               "noninferiority_margin": 0.0}
                        if np.isfinite(difference).all():
                            interval = common.bootstrap_grouped(difference, systems.family_group, weighting)
                            row.update(ci95=interval["ci95"], evaluable=True,
                                       noninferiority_supported=interval["ci95"][1] <= 0)
                        else:
                            row.update(ci95=None, evaluable=False, noninferiority_supported=False,
                                       reason="至少一个预定测试系统拟合失败；保留NA，不删除系统")
                        rows.append(row)
        pd.DataFrame(rows).to_csv(output / "comparisons.csv", index=False)
        pd.DataFrame(alignment).to_csv(output / "fold_alignment.csv", index=False)
        primary = {r["partition_model"] + "-" + r["pair_model"]: r for r in rows
                   if r["weighting"] == "family" and r["validation"] == "family"}
        result = {"comparisons": rows, "primary": primary, "alignment": alignment,
                  "pair_source": str(pair_source.relative_to(common.ROOT)),
                  "pair_source_sha256": common.sha256(pair_source), "margin": 0.0,
                  "interpretation": "只有差值95%区间上界<=0才支持零界不劣；未显著不表示相当。"}
        result["mixture_reference_comparisons"] = mixture_reference_comparisons(strict_full_source)
        save(output / "summary.json", result)
        metrics.update(comparisons=len(rows), all_alignments_passed=True,
                       primary_A7_M2=primary["A7-M2"], primary_A7_M4=primary["A7-M4"])
        return result


def mixture_reference_comparisons(strict_full_source):
    """Q4 compares substantive gamma values; the seven-cell residual is saturated."""
    strict = json.loads(Path(strict_full_source).read_text())
    frozen_path = common.S2 / "prediction_results.json"
    frozen = json.loads(frozen_path.read_text())
    pair_meta = common.pair_design_metadata()
    design = pair_meta.groupby("pattern", sort=True)[list(M2_COLUMNS)].first().to_numpy(dtype=float)
    codes = sorted(pair_meta.pattern.astype(str).unique())
    rows = []
    for weighting in ("family", "language"):
        original = [r for r in frozen["full_sample_calibration"]["D1_MLE_" + weighting]
                    if r["area"] == "全部" and r["model"] == "M2"]
        frozen_cells = {str(r["pattern"]): r["predicted"] for r in original}
        if set(frozen_cells) != set(codes):
            raise RuntimeError("旧939 M2七单元参照不完整")
        old_coefficients = m2_logit_contrasts(np.array([frozen_cells[c] for c in codes]), design, M2_COLUMNS)["coefficients"]
        strict_fit = strict["model_fits"][weighting]["M2"]
        if tuple(strict_fit["columns"]) != M2_COLUMNS or not strict_fit["diagnostics"]["converged"]:
            raise RuntimeError("严格样本M2参照未通过或列序不同")
        strict_coefficients = dict(zip(M2_COLUMNS, strict_fit["coefficients"]))
        for sample in ("strict", "equal_sets", "components"):
            contrasts = pd.read_csv(OUTPUT / f"full_{sample}_{weighting}/mixture_logit_contrasts.csv")
            for row in contrasts.itertuples(index=False):
                if row.term not in ("DrDa", "DrDe", "DaDe"):
                    continue
                rows.append({"sample": sample, "weighting": weighting, "model": row.model,
                             "term": row.term, "generated_gamma": row.generated_gamma,
                             "strict_M2_gamma": strict_coefficients[row.term],
                             "full939_original_D1_M2_gamma": old_coefficients[row.term],
                             "generated_minus_strict_M2": row.generated_gamma - strict_coefficients[row.term],
                             "generated_minus_original939_M2": row.generated_gamma - old_coefficients[row.term],
                             "seven_cell_projection_residual": row.saturated_projection_residual,
                             "reference_scope": "严格625及旧D1非传递共享939参照；939敏感性划分不等于旧D1"})
    output = OUTPUT / "pair_comparisons"
    pd.DataFrame(rows).to_csv(output / "mixture_gamma_references.csv", index=False)
    return {"rows": rows, "strict_fullfit_source": str(Path(strict_full_source).relative_to(common.ROOT)),
            "strict_fullfit_sha256": common.sha256(strict_full_source),
            "original939_source": str(frozen_path.relative_to(common.ROOT)),
            "original939_sha256": common.sha256(frozen_path),
            "original939_gamma_recovery": "由冻结M2七单元完整拟合概率按相同满秩设计还原，不重新估计旧数据。",
            "interpretation": "比较交互的方向、量值及28对内部异质性；饱和投影零残差仅作数值核验。"}


def refinement_comparison():
    initial = common.RESULTS / "t2/initial_solver"
    result = {"appendix": verify_refinement(), "settings": {}}
    all_fit_rows, all_candidate_rows, all_oof_rows = [], [], []
    for old_summary in sorted(initial.glob("cv_*/summary.json")):
        setting_dir = old_summary.parent.name
        active = OUTPUT / setting_dir
        if not (active / "summary.json").exists():
            continue
        before, after = json.loads(old_summary.read_text()), json.loads((active / "summary.json").read_text())
        def fit_rows(path):
            with gzip.open(path, "rt", encoding="utf8") as stream:
                return {(r["space"], r["split_id"], r["alpha"]): r
                        for r in map(json.loads, stream)}
        old_fits = fit_rows(old_summary.parent / "fit_diagnostics.jsonl.gz")
        new_fits = fit_rows(active / "fit_diagnostics.jsonl.gz")
        for key in sorted(set(old_fits) & set(new_fits)):
            old, new = old_fits[key], new_fits[key]
            a, b = old["diagnostics"]["attempts"], new["diagnostics"]["attempts"]
            if not a or not b:
                continue
            all_fit_rows.append({"setting": setting_dir, "space": key[0], "split_id": key[1], "alpha": key[2],
                                 "initial_converged": old["converged"], "refined_converged": new["converged"],
                                 "initial_objective": a[-1]["objective"], "refined_objective": b[-1]["objective"],
                                 "objective_difference": b[-1]["objective"] - a[-1]["objective"],
                                 "initial_gradient": a[-1]["gradient_max"], "refined_gradient": b[-1]["gradient_max"],
                                 "refined_attempts": len(b)})
        keys = ["outer_fold", "model", "space", "alpha"]
        old_candidates = pd.read_csv(old_summary.parent / "inner_selection.csv")
        new_candidates = pd.read_csv(active / "inner_selection.csv")
        joined = old_candidates.merge(new_candidates, on=keys, suffixes=("_initial", "_refined"), how="outer")
        all_candidate_rows.extend(joined.assign(setting=setting_dir).to_dict("records"))
        keys = ["Language_ID", "model", "penalty"]
        old_scores = pd.read_csv(old_summary.parent / "oof_system_scores.csv.gz")
        new_scores = pd.read_csv(active / "oof_system_scores.csv.gz")
        joint = old_scores.merge(new_scores, on=keys, suffixes=("_initial", "_refined"), validate="one_to_one")
        joint["log_probability_difference"] = joint.log_probability_refined - joint.log_probability_initial
        all_oof_rows.extend(joint[keys + ["log_probability_initial", "log_probability_refined", "log_probability_difference"]].assign(setting=setting_dir).to_dict("records"))
        result["settings"][before["setting"]] = {
            "initial_selected_models": before["selected_models"], "refined_selected_models": after["selected_models"],
            "initial_selected_comparisons": before["selected_comparisons"],
            "refined_selected_comparisons": after["selected_comparisons"],
            "initial_selections": json.loads((old_summary.parent / "selection.json").read_text()),
            "refined_selections": json.loads((active / "selection.json").read_text())}
    target = OUTPUT / "numerical_refinement"
    target.mkdir(exist_ok=True)
    pd.DataFrame(all_fit_rows).to_csv(target / "fit_changes.csv", index=False)
    pd.DataFrame(all_candidate_rows).to_csv(target / "candidate_changes.csv", index=False)
    pd.DataFrame(all_oof_rows).to_csv(target / "oof_changes.csv.gz", index=False)
    save(target / "summary.json", result)
    return result


def collect_results():
    """Collect completed jobs only; an absent job remains visibly absent."""
    result = {"plan": common.verify_analysis_plan(), "seed": common.SEED,
              "bootstrap_replicates": common.BOOTSTRAP_REPLICATES, "cv": {}, "full": {},
              "pair_comparisons": {}, "analysis_status": "only_completed_jobs_are_listed"}
    for path in sorted(OUTPUT.glob("cv_*/summary.json")):
        value = json.loads(path.read_text())
        result["cv"][value["setting"]] = value
    for path in sorted(OUTPUT.glob("full_*/summary.json")):
        value = json.loads(path.read_text())
        result["full"][value["setting"]] = value
    comparison = OUTPUT / "pair_comparisons/summary.json"
    if comparison.exists():
        result["pair_comparisons"] = json.loads(comparison.read_text())
    result["solver_profile"] = SOLVER_PROFILE
    result["numerical_refinement"] = verify_refinement() if SOLVER_PROFILE == "refined" else None
    result["completeness"] = {"cv_settings": len(result["cv"]), "expected_cv_settings": 18,
                              "full_settings": len(result["full"]), "expected_full_settings": 6,
                              "pair_comparison_completed": bool(result["pair_comparisons"])}
    save(OUTPUT / "t2_results.json", result)


def write_report_and_plots():
    path = OUTPUT / "t2_results.json"
    result = json.loads(path.read_text())
    if len(result["cv"]) != 18 or len(result["full"]) != 6 or not result["pair_comparisons"]:
        return
    primary = result["cv"]["strict_family_family"]
    full = result["full"]["strict_family"]
    boot = full["coefficient_bootstrap"]
    def number(value):
        return "不可评估" if value is None else f"{value:.6f}"
    def interval(value):
        return "不可评估" if value is None else "[" + ", ".join(number(v) for v in value) + "]"
    lines = ["# T2 划分层面概率模型结果", "",
             "本轮科学模型与评价方案见冻结分析计划。首次L-BFGS-B因目标变化阈值提前停止的NA输出保留于initial_solver；正式结果采用运行后明确追加的数值精化附录，在全部规格一致允许第三次更严格求解，原梯度、归一和有限MLE门均未放宽。", "",
             "A6中固定语言库存成本4λ在归一化中抵消，λ=0/1/2/3分布相同，仅拟合一次；语言等权与无权数学相同，另列恒等关系，不伪装为两项独立结果。", "",
             "## Q1：相对坐标与绝对坐标", "",
             "主严格625、谱系等权、原谱系五折。增益为每系统留出log似然之差，正值较好；区间为5000次固定OOF整谱系重抽。", "",
             "|比较|增益nats|95%区间|正增益区间支持|", "|---|---:|---|---|"]
    for comparison in ("A3r-A2", "A3s-A2", "A5r-A4", "A5s-A4"):
        row = primary["selected_comparisons"][comparison]
        lines.append(f"|{comparison}|{number(row['gain'])}|{interval(row['ci95'])}|{row.get('interval_excludes_zero_positive', False)}|")
    lines += ["", "两种相对坐标分别报告；不能把r坐标的优势概括成任意相对坐标都更好。", "",
              "## Q2：位置项的增量与系数", ""]
    q2 = primary["selected_comparisons"]["A7-BASE"]
    lines += [f"A7相对同一外层训练内选定描述模型的增益为{number(q2['gain'])}，95%区间{interval(q2['ci95'])}。基底先在不含P的候选中选择，再固定基底调A7惩罚；不使用外层测试回选。", "",
              f"全样本选择为{full['selected_base']['model']}，A7的α={full['selected_A7']['alpha']}。主A7三个P方向的预期系数为正；它们不是旧M4的负向pair条件项。", "",
              "|项|原始坐标系数|95%区间|Bonferroni 98.333%区间|", "|---|---:|---|---|"]
    if boot:
        for term in ("P2", "P3", "P4"):
            ci = boot["intervals"][term]
            lines.append(f"|{term}|{number(full['models']['A7']['raw_coefficients'][term])}|{interval(ci['ci95'])}|{interval(ci['bonferroni_ci_98_333333'])}|")
        lines += ["", f"重拟合成功{boot['successful_replicates']}/{boot['replicates']}；失败不填零、不补抽。区间以选定基底和α为条件，不包含选择不确定性。"]
    lines += ["", "## Q3：同折同权重的类别对预测", "",
              "差值=划分模型导出的pair logloss−原pair模型logloss，负值较好；零界不劣仅在95%区间上界≤0时得到支持。未显著不等于相当。", "",
              "|划分模型|参照|损失差|95%区间|支持零界不劣|", "|---|---|---:|---|---|"]
    for model in MODELS:
        for reference in ("M2", "M4"):
            row = result["pair_comparisons"]["primary"][model + "-" + reference]
            lines.append(f"|{model}|{reference}|{number(row['loss_difference'])}|{interval(row['ci95'])}|{row['noninferiority_supported']}|")
    lines += ["", "## Q4：分布混合与总体logit交互", "",
              "由拟合划分分布精确导出28对共享率，再求七差异单元logit系数。下表比较量值；七单元M2满秩饱和，零投影残差只说明数值一致，不能作为混合机制成立的证据。", "",
              "|模型|项|生成γ|严格625 M2γ|旧D1 939 M2γ|", "|---|---|---:|---:|---:|"]
    for row in result["pair_comparisons"]["mixture_reference_comparisons"]["rows"]:
        if row["sample"] == "strict" and row["weighting"] == "family":
            lines.append(f"|{row['model']}|{row['term']}|{number(row['generated_gamma'])}|{number(row['strict_M2_gamma'])}|{number(row['full939_original_D1_M2_gamma'])}|")
    lines += ["", "生成的非零交互说明类型分布能够产生总体非加性；其符号、量值及七单元内28对差别仍需与实测比较，不能据此识别真实历史混合原因。", "",
              "## 全部预设敏感性", "",
              "三样本×两权重×三推广目标共18规格；四固定α的全阶梯保留在各CV目录的ladder/comparisons/inner_selection中。所有失败候选和预定测试系统均保留。", "",
              "|样本/权重/验证|A3r−A2|A3s−A2|A5r−A4|A5s−A4|A7−BASE及95%区间|", "|---|---:|---:|---:|---:|---|"]
    for setting, value in result["cv"].items():
        c = value["selected_comparisons"]
        final = c["A7-BASE"]
        lines.append("|" + "|".join([setting, *[number(c[k]["gain"]) for k in ("A3r-A2", "A3s-A2", "A5r-A4", "A5s-A4")],
                                        number(final["gain"]) + " " + interval(final["ci95"])]) + "|")
    lines += ["", "## 合成预测检查与结果来源", "",
              "每个有效全样本模型独立生成5000个与原样本等大的合成样本；使用对应固定系统权重，比较类别数、四基底合取比例与P2–P4的预测/相反/不适用比例。条件方向分母为空时单列。该检查来自MLE拟合分布，不称贝叶斯后验。", "",
              "完整统计在各full目录的predictive_checks.csv和summary.json；28对预测及七单元内差异在pair_predictions.csv，生成γ在mixture_logit_contrasts.csv。配对身份/折号核查在pair_comparisons/fold_alignment.csv；全部首次数值尝试和第三次精化均保留于fit_diagnostics。", "",
              "汇总JSON为t2_results.json；原计划与精化之间的目标、梯度、OOF和候选变化见numerical_refinement目录。所有结果均为补充分析，既有探索结果已知，不称验证性研究。", ""]
    (OUTPUT / "report.md").write_text("\n".join(lines), encoding="utf8")
    plot_results(result)


def plot_results(result):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    font = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    if Path(font).exists():
        font_manager.fontManager.addfont(font)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=font).get_name()
    plt.rcParams.update({"font.size": 11, "axes.unicode_minus": False,
                         "axes.spines.top": False, "axes.spines.right": False})
    figure_dir = OUTPUT / "figures"
    figure_dir.mkdir(exist_ok=True)
    def finish(fig, name):
        fig.tight_layout()
        fig.savefig(figure_dir / (name + ".png"), dpi=200, bbox_inches="tight")
        fig.savefig(figure_dir / (name + ".pdf"), bbox_inches="tight")
        plt.close(fig)
    models = [m for m in MODELS if m != "BASE"]
    fig, ax = plt.subplots(figsize=(11, 4.5))
    x = np.arange(len(models))
    for j, (cv, label) in enumerate((("family", "未见谱系"), ("area", "未见区域"), ("language", "未见语言"))):
        table = result["cv"]["strict_family_" + cv]["selected_models"]
        ax.bar(x + (j - 1) * .25, [table[m]["mean_log_probability"] for m in models], width=.24, label=label)
    ax.set_xticks(x, models)
    ax.set_ylabel("每系统留出log似然（nats）")
    ax.legend(ncol=3)
    finish(fig, "Fx_T2_model_ladder")
    pairs = pd.read_csv(OUTPUT / "full_strict_family/pair_predictions.csv", dtype={"pattern": str})
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for model in ("A1", "A5r", "A6", "A7"):
        group = pairs[pairs.model.eq(model)].groupby("pattern", sort=True).mean(numeric_only=True)
        ax.plot(np.arange(len(group)), group.generated_probability, marker="o", label=model)
    group = pairs[pairs.model.eq("A7")].groupby("pattern", sort=True).mean(numeric_only=True)
    ax.scatter(np.arange(len(group)), group.observed_probability, color="black", marker="x", s=65, label="观测")
    ax.set_xticks(np.arange(len(group)), group.index)
    ax.set_xlabel("差异组合（Dr, Da, De）")
    ax.set_ylabel("词形共享概率")
    ax.legend(ncol=5)
    finish(fig, "Fx_T2_seven_cells")
    full = result["full"]["strict_family"]
    ppc = full["predictive_checks"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, statistics, labels in ((axes[0], [f"k_{i}" for i in range(1, 9)], [str(i) for i in range(1, 9)]),
                                   (axes[1], ["conj_abs", "conj_rel_r", "conj_rel_s", "conj_all"], ["绝对", "相对r", "相对s", "四特征"])):
        for j, model in enumerate(("A5r", "A7")):
            records = [next(v for v in ppc if v["model"] == model and v["statistic"] == name) for name in statistics]
            central = np.array([v["synthetic_mean"] for v in records])
            bounds = np.array([v["predictive_ci95"] for v in records])
            positions = np.arange(len(records)) + (j - .5) * .1
            ax.vlines(positions, bounds[:, 0], bounds[:, 1], color=f"C{j}")
            ax.scatter(positions, central, color=f"C{j}", label=model)
        ax.scatter(np.arange(len(records)), [v["observed"] for v in records], marker="x", color="black", label="观测")
        ax.set_xticks(np.arange(len(records)), labels)
        ax.set_ylabel("系统比例与95%合成预测区间")
    axes[0].set_xlabel("类别数k")
    axes[1].set_xlabel("合取语言")
    axes[1].legend()
    finish(fig, "Fx_T2_predictive_checks")
    boot = full["coefficient_bootstrap"]
    if boot and boot["report_intervals"]:
        fig, ax = plt.subplots(figsize=(7, 4))
        terms = ("P2", "P3", "P4")
        for j, term in enumerate(terms):
            point = full["models"]["A7"]["raw_coefficients"][term]
            a, b = boot["intervals"][term]["ci95"], boot["intervals"][term]["bonferroni_ci_98_333333"]
            ax.plot(b, [j, j], color="#a6bfd2", lw=5)
            ax.plot(a, [j, j], color="#1b5277", lw=2)
            ax.scatter(point, j, color="#1b5277", zorder=3)
        ax.axvline(0, color="gray", ls="--")
        ax.set_yticks(range(3), ["年长侧 P2", "男性侧 P3", "同性侧 P4"])
        ax.set_xlabel("划分方向系数；细线95%，粗线98.333%区间")
        finish(fig, "Fx_T2_position_coefficients")


def main():
    global OUTPUT, SOLVER_PROFILE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["cv", "full", "compare", "all"], default="all")
    parser.add_argument("--sample", choices=["strict", "equal_sets", "components", "all"], default="all")
    parser.add_argument("--weighting", choices=["family", "language", "all"], default="all")
    parser.add_argument("--validation", choices=["family", "area", "language", "all"], default="all")
    parser.add_argument("--solver-profile", choices=["planned", "refined"], default="refined")
    args = parser.parse_args()
    SOLVER_PROFILE = args.solver_profile
    OUTPUT = common.RESULTS / "t2" / ("initial_solver" if SOLVER_PROFILE == "planned" else "")
    gate = common.verify_analysis_plan()
    if SOLVER_PROFILE == "refined":
        gate["numerical_refinement"] = verify_refinement()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    catalogue = common.load_partition_table().sort_values("partition_id").reset_index(drop=True)
    if len(catalogue) != 4140 or catalogue.partition_id.tolist() != list(range(4140)):
        raise RuntimeError("T1划分ID不覆盖精确4140支持点")
    spaces = make_spaces(catalogue)
    pair_meta = common.pair_design_metadata()
    save(OUTPUT / "feature_spaces.json", {model: space.metadata() for model, space in spaces.items()})
    pair_meta.to_csv(OUTPUT / "pair_metadata.csv", index=False)
    save(OUTPUT / "execution_gate.json", {**gate, "seed": common.SEED,
                                         "runner_sha256": common.sha256(__file__),
                                         "model_sha256": common.sha256(HERE / "partition_model.py")})
    samples = ("strict", "equal_sets", "components") if args.sample == "all" else (args.sample,)
    weights = ("family", "language") if args.weighting == "all" else (args.weighting,)
    validations = ("family", "area", "language") if args.validation == "all" else (args.validation,)
    if args.phase in {"cv", "all"}:
        for sample in samples:
            for weighting in weights:
                for validation in validations:
                    run_cv(sample, weighting, validation, catalogue, spaces, pair_meta)
    if args.phase in {"full", "all"}:
        for sample in samples:
            for weighting in weights:
                run_full(sample, weighting, catalogue, spaces, pair_meta)
    if args.phase in {"compare", "all"}:
        run_pair_comparisons(catalogue, pair_meta)
    collect_results()
    if SOLVER_PROFILE == "refined":
        refinement_comparison()
        write_report_and_plots()


if __name__ == "__main__":
    main()
