"""T5 类别对预测、区域校准、加权 AUC 与谱系 sandwich 的可复用函数。

保留 S2 的设计、MLE/Firth 与 C=1 数值定义；本模块导入时不读取数据。
"""
from __future__ import annotations

import math
import warnings

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.optimize import brentq
from scipy.special import expit, logit
from scipy.stats import t as student_t
from sklearn.metrics import roc_auc_score

import common
from common import BOOTSTRAP_REPLICATES, SEED, bootstrap_grouped, system_weights
from design_rank import M4_COLUMNS
from s2_models import MODELS, build_design, fit_aggregated, fit_c1_rows, logloss


VALIDATIONS = ("family", "area", "language")
WEIGHTINGS = ("family", "language")
ESTIMATORS = ("MLE", "C1")
CONTRASTS = (("M0", "M2"), ("M2", "M4"), ("M0", "M4"))


def finite_json(value):
    if isinstance(value, dict):
        return {str(k): finite_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [finite_json(x) for x in value]
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if math.isfinite(value) else None
    return value


def model_columns(pair_types, model):
    return {"M0": list(M4_COLUMNS[:4]), "M1": list(M4_COLUMNS[:4]) + ["Dq"],
            "M2": list(M4_COLUMNS[:7]), "M3": list(pair_types),
            "M4": list(M4_COLUMNS)}[model]


def row_weights(frame, weighting="family"):
    """S2 数值尺度：总量=N系统；完整系统的每对权重按固定28对定义。"""
    info = frame[["Language_ID", "family_group"]].drop_duplicates()
    if info.Language_ID.duplicated().any() or not len(info):
        raise ValueError("系统分组不唯一或训练集为空")
    if weighting == "language":
        return np.full(len(frame), 1 / 28)
    if weighting != "family":
        raise ValueError("未知权重：" + weighting)
    counts = info.family_group.value_counts()
    return len(info) / (len(counts) * frame.family_group.map(counts).to_numpy(dtype=float) * 28)


def prepare_measurements():
    """调用原测量函数，联结第三版固定折，不另改五种共享定义。"""
    from measurement_analysis import load_measurement_data
    definitions, _, _ = load_measurement_data()
    original = common.load_base_data()
    systems = original["systems"]
    strict = common.load_system_mapping("strict")
    if set(strict.Language_ID) != set(definitions["D3"].Language_ID):
        raise RuntimeError("T1严格映射与原D3系统不同")
    pair_types = sorted((definitions["D1"].category_a + "|" + definitions["D1"].category_b).unique())
    if len(pair_types) != 28:
        raise RuntimeError("类别对空间不等于28")
    lookup = {key: index for index, key in enumerate(pair_types)}
    folds = systems[["Language_ID", "fold_family", "fold_language", "macroarea"]]
    result = {}
    for name, frame in definitions.items():
        frame = frame.merge(folds, on="Language_ID", validate="many_to_one", sort=False)
        frame["pair_type"] = frame.category_a + "|" + frame.category_b
        frame["pair_index"] = frame.pair_type.map(lookup).astype(int)
        if not frame.groupby("Language_ID").size().eq(28).all():
            raise RuntimeError("保留系统未含全部28对：" + name)
        result[name] = frame.reset_index(drop=True)
    return result, pair_types


def aggregate_training(frame, weights, n_pairs=28):
    pair_index = frame.pair_index.to_numpy(dtype=int)
    total = np.bincount(pair_index, weights=weights, minlength=n_pairs)
    success = np.bincount(pair_index, weights=weights * frame.shared_form.to_numpy(), minlength=n_pairs)
    return success, total


def fit_model(train, X, estimator="MLE", weighting="family", model="M4"):
    weights = row_weights(train, weighting)
    if estimator == "C1":
        beta, diagnostics = fit_c1_rows(X[train.pair_index.to_numpy()],
                                        train.shared_form.to_numpy(), weights, model)
    elif estimator == "MLE":
        success, total = aggregate_training(train, weights, len(X))
        beta, diagnostics = fit_aggregated(X, success, total, estimator="MLE")
    else:
        raise ValueError(estimator)
    beta = np.asarray(beta, dtype=float)
    diagnostics = dict(diagnostics)
    diagnostics["finite_coefficients"] = bool(np.isfinite(beta).all())
    diagnostics["converged"] = bool(diagnostics.get("converged", False) and np.isfinite(beta).all())
    return beta, diagnostics


def fold_splits(frame, validation):
    if validation == "area":
        data = frame[frame.macroarea.ne("")].reset_index(drop=True)
        labels = sorted(data.macroarea.unique())
        values = data.macroarea
    elif validation in ("family", "language"):
        data = frame.reset_index(drop=True)
        labels = list(range(5))
        values = data["fold_" + validation]
    else:
        raise ValueError(validation)
    splits = []
    for fold in labels:
        mask = values.eq(fold).to_numpy()
        test, train = np.flatnonzero(mask), np.flatnonzero(~mask)
        if len(test) == 0:
            continue
        if not len(train):
            raise RuntimeError("非空测试折没有训练集")
        column = {"family": "family_group", "language": "Language_ID", "area": "macroarea"}[validation]
        if set(data.iloc[train][column]) & set(data.iloc[test][column]):
            raise RuntimeError("训练测试分组泄漏")
        splits.append((str(fold), train, test))
    return data, splits


def evaluate_cv(frame, pair_types, weighting="family", validation="family", estimator="MLE", sample="strict"):
    """失败模型保留全部测试行和NaN，不按可用行缩小比较样本。"""
    data, splits = fold_splits(frame, validation)
    designs = {model: build_design(pair_types, model) for model in MODELS}
    predictions = np.full((len(data), len(MODELS)), np.nan)
    fold_id = np.full(len(data), "", dtype=object)
    logs, fold_info = [], []
    for fold, training, testing in splits:
        train, test = data.iloc[training], data.iloc[testing]
        fold_id[testing] = fold
        fold_info.append({"fold": fold, "validation": validation, "weighting": weighting,
                          "sample": sample, "estimator": estimator,
                          "train_systems": int(train.Language_ID.nunique()),
                          "test_systems": int(test.Language_ID.nunique()),
                          "train_family_ids": sorted(train.family_group.unique()),
                          "test_family_ids": sorted(test.family_group.unique()),
                          "train_system_ids": sorted(train.Language_ID.unique()),
                          "test_system_ids": sorted(test.Language_ID.unique())})
        for index, model in enumerate(MODELS):
            diagnostic = {"fold": fold, "model": model, "validation": validation,
                          "weighting": weighting, "sample": sample, "estimator_requested": estimator}
            try:
                beta, fitted = fit_model(train, designs[model], estimator, weighting, model)
                diagnostic.update(fitted)
                if diagnostic["converged"]:
                    predictions[testing, index] = expit(designs[model][test.pair_index.to_numpy()] @ beta)
            except Exception as exc:
                diagnostic.update(converged=False, error=repr(exc))
            logs.append(diagnostic)
    if (fold_id == "").any():
        raise RuntimeError("有系统未取得测试折")
    columns = ["Language_ID", "Glottocode", "family_group", "family_name", "macroarea",
               "category_a", "category_b", "pair_index", "pattern", "shared_form"]
    output = data[columns].copy()
    output["sample"] = sample
    output["weighting"] = weighting
    output["validation"] = validation
    output["cv"] = validation
    output["estimator"] = estimator
    output["fold"] = fold_id
    y = data.shared_form.to_numpy()
    for index, model in enumerate(MODELS):
        p = predictions[:, index]
        output["p_" + model] = p
        output["loss_" + model] = logloss(y, p)
        output["brier_" + model] = (y - p) ** 2
    keys = ["sample", "weighting", "validation", "cv", "estimator", "fold", "Language_ID",
            "Glottocode", "family_group", "family_name", "macroarea"]
    metric_columns = ["loss_" + model for model in MODELS] + ["brier_" + model for model in MODELS]
    scores = output.groupby(keys, sort=False, dropna=False)[metric_columns].agg(
        lambda values: float(values.mean()) if np.isfinite(values).all() else np.nan).reset_index()
    counts = output.groupby("Language_ID").size()
    if not counts.eq(28).all() or len(scores) != data.Language_ID.nunique():
        raise RuntimeError("逐系统评分未保留全部28对")
    return output, scores, logs, fold_info


def weighted_score(scores, column, weighting):
    values = scores[column].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        return None
    return float(system_weights(scores, weighting) @ values)


def comparison_rows(scores, weighting, spec):
    result = []
    for baseline, larger in CONTRASTS:
        values = (scores["loss_" + baseline] - scores["loss_" + larger]).to_numpy()
        available = bool(np.isfinite(values).all())
        row = {**spec, "baseline": baseline, "larger_model": larger,
               "comparison": larger + "_over_" + baseline,
               "gain_definition": "baseline loss minus larger-model loss",
               "systems": len(scores), "families": int(scores.family_group.nunique()),
               "available": available, "seed": SEED, "bootstrap_replicates": BOOTSTRAP_REPLICATES}
        if available:
            computed = bootstrap_grouped(values, scores.family_group.to_numpy(), weighting)
            row.update(gain=computed["estimate"], ci95_low=computed["ci95"][0], ci95_high=computed["ci95"][1],
                       interval_scope=computed["scope"])
        else:
            row.update(gain=None, ci95_low=None, ci95_high=None,
                       failed_system_ids=scores.loc[~np.isfinite(values), "Language_ID"].tolist())
        result.append(row)
    return result


def recalibrate_intercept(y, p, weights):
    """在测试结果上估计单一偏移；明确只用于事后诊断。"""
    y, p, weights = np.asarray(y, float), np.asarray(p, float), np.asarray(weights, float)
    if not np.isfinite(p).all() or not np.isfinite(weights).all() or (weights < 0).any() or weights.sum() <= 0:
        raise ValueError("校准输入无效")
    weights = weights / weights.sum()
    observed = float(weights @ y)
    active = y[weights > 0]
    if np.all(active == 0) or np.all(active == 1):
        observed = float(active[0])
        return {"offset": None, "status": "boundary_outcome", "calibrated_probability": np.full(len(y), observed),
                "observed_prevalence": observed, "used_test_outcomes": True}
    eta = logit(np.clip(p, 1e-15, 1 - 1e-15))
    score = lambda offset: float(weights @ (y - expit(eta + offset)))
    limit = 1.0
    while score(-limit) * score(limit) > 0 and limit < 1024:
        limit *= 2
    offset = float(brentq(score, -limit, limit, xtol=1e-12))
    return {"offset": offset, "status": "finite_offset", "calibrated_probability": expit(eta + offset),
            "observed_prevalence": observed, "used_test_outcomes": True}


def weighted_auc(y, p, weights):
    y, p, weights = np.asarray(y), np.asarray(p), np.asarray(weights)
    if not np.isfinite(p).all() or len(np.unique(y[weights > 0])) != 2:
        return None
    return float(roc_auc_score(y, p, sample_weight=weights))


def regional_calibration(predictions):
    rows = []
    for area, region in predictions.groupby("macroarea", sort=True):
        if not area:
            continue
        weights = row_weights(region, "family")
        weights = weights / weights.sum()
        y = region.shared_form.to_numpy()
        for model in MODELS:
            p = region["p_" + model].to_numpy()
            record = {"macroarea": area, "model": model, "systems": int(region.Language_ID.nunique()),
                      "families": int(region.family_group.nunique()), "used_test_outcomes_for_offset": True,
                      "target_weighting": "区域内谱系等权", "available": bool(np.isfinite(p).all())}
            if record["available"]:
                calibrated = recalibrate_intercept(y, p, weights)
                pc = calibrated["calibrated_probability"]
                raw_loss, calibrated_loss = float(weights @ logloss(y, p)), float(weights @ logloss(y, pc))
                if calibrated_loss > raw_loss + 1e-10:
                    raise RuntimeError("可选零偏移的校准使训练目标上升")
                record.update(observed_prevalence=float(weights @ y), predicted_prevalence=float(weights @ p),
                              calibrated_predicted_prevalence=float(weights @ pc), raw_logloss=raw_loss,
                              calibrated_diagnostic_logloss=calibrated_loss, intercept_offset=calibrated["offset"],
                              calibration_status=calibrated["status"], auc=weighted_auc(y, p, weights),
                              calibrated_auc=weighted_auc(y, pc, weights),
                              note="偏移使用留出区真实结果；非真正未见区域预测，也不证明斜率普遍稳定。")
            rows.append(record)
    return rows


def cluster_sandwich(X, y, p, weights, groups, correction=True):
    """加权MLE的CR1整谱系 sandwich；返回t_(G-1)区间所需协方差。"""
    X, y, p, weights = (np.asarray(v, dtype=float) for v in (X, y, p, weights))
    groups = np.asarray(groups)
    if X.ndim != 2 or len(X) != len(y) or not np.isfinite(p).all():
        raise ValueError("sandwich输入无效")
    labels, inverse = np.unique(groups, return_inverse=True)
    G, n, K = len(labels), len(y), X.shape[1]
    if G <= 1 or n <= K:
        raise ValueError("聚类数或样本行数不足")
    information = X.T @ ((weights * p * (1 - p))[:, None] * X)
    cluster_scores = np.zeros((G, K))
    np.add.at(cluster_scores, inverse, X * (weights * (y - p))[:, None])
    bread = np.linalg.inv(information)
    covariance = bread @ (cluster_scores.T @ cluster_scores) @ bread
    factor = (G / (G - 1)) * ((n - 1) / (n - K)) if correction else 1.0
    covariance *= factor
    covariance = (covariance + covariance.T) / 2
    return {"covariance": covariance, "se": np.sqrt(np.maximum(np.diag(covariance), 0)),
            "clusters": G, "rows": n, "parameters": K, "CR1_factor": factor,
            "critical_t95": float(student_t.ppf(0.975, G - 1)), "degrees_of_freedom": G - 1,
            "total_cluster_score_max_abs": float(np.abs(cluster_scores.sum(axis=0)).max()),
            "method": "加权二项MLE，谱系聚类CR1 sandwich，t(G−1)区间"}


def full_sample_fit(frame, pair_types, weighting="family", models=MODELS, sandwich=False):
    results = {}
    for model in models:
        X = build_design(pair_types, model)
        beta, diagnostics = fit_model(frame, X, "MLE", weighting, model)
        record = {"model": model, "columns": model_columns(pair_types, model),
                  "coefficients": beta.tolist(), "diagnostics": diagnostics}
        if sandwich and diagnostics["converged"] and diagnostics["method"] == "MLE":
            indices = frame.pair_index.to_numpy()
            p = expit(X[indices] @ beta)
            try:
                computed = cluster_sandwich(X[indices], frame.shared_form.to_numpy(), p,
                                            row_weights(frame, weighting), frame.family_group.to_numpy())
                se, critical = computed["se"], computed["critical_t95"]
                record["sandwich"] = {**computed, "available": True,
                                      "ci95": np.c_[beta - critical * se, beta + critical * se].tolist()}
            except Exception as exc:
                record["sandwich"] = {"available": False, "reason": repr(exc)}
        elif sandwich:
            record["sandwich"] = {"available": False,
                                  "reason": "普通MLE sandwich未被冒充为Firth估计方程或未收敛模型的协方差。"}
        results[model] = record
    return finite_json(results)


def vb_convergence(optimizer_success, gradient, parameters, standard_deviations):
    return bool(optimizer_success and np.isfinite(parameters).all() and
                np.isfinite(standard_deviations).all() and
                np.max(np.abs(gradient)) <= 1e-6)


def fit_family_only_vb(frame, pair_types, model_name):
    """仅谱系随机截距；失败只输出诊断，不输出可用于推断的系数表。"""
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
    X28 = build_design(pair_types, model_name)
    X = X28[frame.pair_index.to_numpy()]
    groups = sorted(frame.family_group.unique())
    group_index = frame.family_group.map({value: index for index, value in enumerate(groups)}).to_numpy()
    Z = sparse.csr_matrix((np.ones(len(frame)), (np.arange(len(frame)), group_index)), shape=(len(frame), len(groups)))
    names = model_columns(pair_types, model_name)
    model = BinomialBayesMixedGLM(frame.shared_form.to_numpy(), X, Z, np.zeros(len(groups), dtype=int),
                                  vcp_p=0.5, fe_p=2, fep_names=names, vcp_names=["family"])
    K = model.k_fep + model.k_vcp + model.k_vc
    attempts = []
    fitted = None
    passed = False
    for maxiter in (2000, 10000):
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            fitted = model.fit_vb(mean=np.zeros(K), sd=np.full(K, np.exp(-0.5)), fit_method="BFGS",
                                  minim_opts={"maxiter": maxiter, "gtol": 1e-6}, scale_fe=False, rng=SEED)
        sd = np.sqrt(fitted._cov_params)
        mean_gradient, sd_gradient = model.vb_elbo_grad(fitted.params, sd)
        gradient = np.r_[mean_gradient, sd_gradient * sd]
        passed = vb_convergence(fitted.optim_retvals.success, gradient, fitted.params, sd)
        attempts.append({"maxiter": maxiter, "optimizer_success": bool(fitted.optim_retvals.success),
                         "converged": passed, "message": str(fitted.optim_retvals.message),
                         "iterations": int(fitted.optim_retvals.get("nit", -1)),
                         "gradient_max_abs": float(np.abs(gradient).max()),
                         "ELBO": float(model.vb_elbo(fitted.params, sd)),
                         "warnings": [str(item.message) for item in captured]})
        if passed:
            break
    record = {"model": model_name, "converged": passed, "systems": int(frame.Language_ID.nunique()),
              "families": len(groups), "rows": len(frame), "attempts": attempts,
              "random_effects": "仅谱系随机截距，无地域交叉项", "weighting": "未加权模型敏感性",
              "prior": {"fixed_effect_sd": 2, "log_random_sd_prior_sd": 0.5}, "seed": SEED,
              "inference_available": passed}
    if passed:
        record["fixed_effects"] = {
            name: {"mean": float(mu), "sd": float(sd), "vb95": [float(mu - 1.96 * sd), float(mu + 1.96 * sd)]}
            for name, mu, sd in zip(names, fitted.fe_mean, fitted.fe_sd)}
        record["family_log_sd_mean"] = float(fitted.vcp_mean[0])
        record["family_log_sd_posterior_sd"] = float(fitted.vcp_sd[0])
    else:
        record["note"] = "两次预置尝试未过严格收敛门；不将近似系数或区间纳入推断表。"
    return finite_json(record)
