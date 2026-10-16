"""按已提交 S2 协议执行系数重拟合、区域系数与三模型 GLMM。

运行：python analysis/supplementary_s2/uncertainty_analysis.py --task glmm
      python analysis/supplementary_s2/uncertainty_analysis.py --task bootstrap
本程序只写所属 uncertainty/glmm 结果文件，不改冻结分析或 S1。
"""

import argparse
import csv
import datetime
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import subprocess
import time
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold

from design_rank import M2_COLUMNS, M4_COLUMNS, abstract_rows


HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
ANALYSIS = HERE.parent
SEED = 20261014
BOOTSTRAPS = 5000
PROTOCOL_COMMIT = "6ba7afba369d3d15446ea7571eabd2117b7e8c74"
PROTOCOL_SHA = "61874a1c28ab37758670a61d12e08b6097af07f7922f63cfd76da5dacfcef8be"
TERMS = ("DrE", "DaB", "DaS")


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def clean_json(value):
    if isinstance(value, dict):
        return {str(k): clean_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [clean_json(x) for x in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if math.isfinite(value) else None
    return value


def save_json(path, value):
    Path(path).write_text(json.dumps(clean_json(value), ensure_ascii=False,
                                    indent=2, allow_nan=False), encoding="utf-8")


def verify_protocol():
    protocol = HERE / "protocol_s2.md"
    assert digest(protocol) == PROTOCOL_SHA, "协议工作文件哈希不符"
    relative = "analysis/supplementary_s2/protocol_s2.md"
    committed = subprocess.check_output(["git", "show", f"{PROTOCOL_COMMIT}:{relative}"], cwd=BASE)
    assert hashlib.sha256(committed).hexdigest() == PROTOCOL_SHA, "独立提交中的协议哈希不符"
    subprocess.run(["git", "merge-base", "--is-ancestor", PROTOCOL_COMMIT, "HEAD"],
                   cwd=BASE, check=True)
    message = subprocess.check_output(["git", "show", "-s", "--format=%s", PROTOCOL_COMMIT],
                                      cwd=BASE, text=True).strip()
    assert "pre-run protocol" in message
    committed_timestamp = int(subprocess.check_output(
        ["git", "show", "-s", "--format=%ct", PROTOCOL_COMMIT], cwd=BASE, text=True))
    assert time.time() > committed_timestamp
    absent = subprocess.run(["git", "cat-file", "-e", f"{PROTOCOL_COMMIT}:analysis/supplementary_s2/uncertainty_analysis.py"],
                            cwd=BASE, capture_output=True).returncode != 0
    assert absent, "实测脚本不能已经存在于运行前协议提交"
    return {"protocol_commit": PROTOCOL_COMMIT, "protocol_sha256": PROTOCOL_SHA,
            "protocol_commit_utc": datetime.datetime.fromtimestamp(
                committed_timestamp, datetime.timezone.utc).isoformat(),
            "script_absent_from_protocol_commit": absent,
            "script_sha256": digest(__file__), "pairs_sha256": digest(ANALYSIS / "pairs_primary.csv"),
            "seed": SEED,
            "versions": {name: importlib.metadata.version(name)
                         for name in ("numpy", "pandas", "scipy", "scikit-learn", "statsmodels")}}


def load_data():
    frame = pd.read_csv(ANALYSIS / "pairs_primary.csv", dtype={"pattern": str}, keep_default_na=False)
    frame["pair_type"] = frame.category_a + "|" + frame.category_b
    frame["area_primary"] = frame.Macroarea.str.split(";").str[0].str.strip()
    pair_types = sorted(frame.pair_type.unique())
    assert len(frame) == 26292 and frame.Glottocode.nunique() == 939
    assert frame.family_group.nunique() == 125 and len(pair_types) == 28
    assert frame.groupby("Glottocode").size().eq(28).all()
    assert not frame.duplicated(["Glottocode", "pair_type"]).any()
    return frame, pair_types


def own_design(pair_types, model):
    lookup = {row["category_a"] + "|" + row["category_b"]: row for row in abstract_rows()}
    if model == "M0":
        names = M2_COLUMNS[:4]
    elif model == "M1":
        names = ("intercept", "Dr", "Da", "De", "Dq")
    elif model == "M2":
        names = M2_COLUMNS
    elif model == "M4":
        names = M4_COLUMNS
    else:
        raise ValueError(model)
    values = []
    for key in pair_types:
        row = lookup[key]
        values.append([row["Dr"] ^ row["De"] if name == "Dq" else row[name] for name in names])
    return np.asarray(values, dtype=float), list(names)


def verify_frozen_baseline(frame, pair_types):
    """逐行 sklearn 拟合；任何新实测估计之前核验旧的三项 C=1 分数。"""
    frozen = json.loads((ANALYSIS / "results.json").read_text())
    expected = next(x for x in frozen["analyses"]
                    if x["variant"] == "primary" and x["cv_grouping"] == "family")
    frozen_folds = pd.read_csv(ANALYSIS / "oof_predictions.csv", usecols=[
        "variant", "cv_grouping", "Language_ID", "category_a", "category_b", "fold"])
    frozen_folds = frozen_folds[frozen_folds.variant.eq("primary") & frozen_folds.cv_grouping.eq("family")]
    fold_values = np.full(len(frame), -1)
    prediction = {model: np.full(len(frame), np.nan) for model in ("M0", "M1", "M2")}
    type_index = {value: i for i, value in enumerate(pair_types)}
    row_index = frame.pair_type.map(type_index).to_numpy()
    for fold, (train_idx, test_idx) in enumerate(GroupKFold(5).split(frame, groups=frame.family_group)):
        train = frame.iloc[train_idx]
        weight = train.Glottocode.map(1 / train.Glottocode.value_counts()).to_numpy()
        fold_values[test_idx] = fold
        for model in prediction:
            X, _ = own_design(pair_types, model)
            estimator = LogisticRegression(C=1, l1_ratio=0, solver="lbfgs", tol=1e-9, max_iter=5000)
            estimator.fit(X[row_index[train_idx], 1:], train.shared_form.to_numpy(), sample_weight=weight)
            prediction[model][test_idx] = estimator.predict_proba(X[row_index[test_idx], 1:])[:, 1]
    check = frame[["Language_ID", "category_a", "category_b"]].copy()
    check["current_fold"] = fold_values
    joined = check.merge(frozen_folds, on=["Language_ID", "category_a", "category_b"], validate="one_to_one")
    assert len(joined) == len(frame) and joined.current_fold.eq(joined.fold).all()
    errors = {}
    losses = {}
    mapping = {"M0": "raw_additive", "M1": "classical_additive", "M2": "pairwise"}
    y = frame.shared_form.to_numpy()
    for model, p in prediction.items():
        loss = -(y * np.log(p) + (1 - y) * np.log1p(-p))
        value = float(pd.Series(loss, index=frame.Glottocode).groupby(level=0).mean().mean())
        losses[model] = value
        errors[model] = abs(value - expected["language_equal_logloss"][mapping[model]])
    assert max(errors.values()) < 1e-9, errors
    result = {"passed": True, "maximum_absolute_error": max(errors.values()),
              "language_equal_logloss": losses, "frozen_family_folds_identical": True}
    print("冻结C=1逐行复现通过：" + json.dumps(result, ensure_ascii=False), flush=True)
    return result


def fit_one_glmm(model_name):
    """一个未加权模型；不调用待完成的聚合 MLE API。"""
    import statsmodels
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM

    started = utcnow()
    frame, pair_types = load_data()
    frame = frame[frame.area_primary.ne("")].copy()
    X28, names = own_design(pair_types, model_name)
    row_index = frame.pair_type.map({value: i for i, value in enumerate(pair_types)}).to_numpy()
    X = X28[row_index]
    families = sorted(frame.family_group.unique())
    areas = sorted(frame.area_primary.unique())
    family_index = frame.family_group.map({name: i for i, name in enumerate(families)}).to_numpy()
    area_index = frame.area_primary.map({name: i for i, name in enumerate(areas)}).to_numpy()
    rows = np.arange(len(frame))
    Z = sparse.hstack([
        sparse.csr_matrix((np.ones(len(frame)), (rows, family_index)), shape=(len(frame), len(families))),
        sparse.csr_matrix((np.ones(len(frame)), (rows, area_index)), shape=(len(frame), len(areas))),
    ], format="csr")
    ident = np.r_[np.zeros(len(families), dtype=int), np.ones(len(areas), dtype=int)]
    model = BinomialBayesMixedGLM(
        frame.shared_form.to_numpy(), X, Z, ident, vcp_p=0.5, fe_p=2,
        fep_names=names, vcp_names=["family", "area"],
        vc_names=["family:" + name for name in families] + ["area:" + name for name in areas],
    )
    K = model.k_fep + model.k_vcp + model.k_vc
    attempts = []
    result = None
    for maxiter in (2000, 10000):
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            result = model.fit_vb(mean=np.zeros(K), sd=np.full(K, np.exp(-0.5)),
                                  fit_method="BFGS", minim_opts={"maxiter": maxiter, "gtol": 1e-6},
                                  scale_fe=False, rng=SEED)
        opt = result.optim_retvals
        sd = np.sqrt(result._cov_params)
        gm, gs = model.vb_elbo_grad(result.params, sd)
        gradient = np.r_[gm, gs * sd]
        attempt = {"maxiter": maxiter, "success": bool(opt.success),
                   "status": int(opt.status), "message": str(opt.message),
                   "iterations": int(opt.get("nit", -1)), "function_evaluations": int(opt.get("nfev", -1)),
                   "ELBO": float(model.vb_elbo(result.params, sd)),
                   "optimizer_gradient_max_abs": float(np.max(np.abs(gradient))),
                   "optimizer_gradient_l2": float(np.linalg.norm(gradient)),
                   "warnings": [str(w.message) for w in captured],
                   "all_parameters_and_sd_finite": bool(np.isfinite(result.params).all() and np.isfinite(sd).all())}
        attempts.append(attempt)
        print(f'GLMM {model_name} 迭代上限{maxiter}：成功={attempt["success"]}，ELBO={attempt["ELBO"]:.6f}，梯度={attempt["optimizer_gradient_max_abs"]:.3g}', flush=True)
        if attempt["success"] and attempt["all_parameters_and_sd_finite"]:
            break
    fixed = {
        name: {"mean": float(mu), "sd": float(sd),
               "normal_approximate_95_interval": [float(mu - 1.96 * sd), float(mu + 1.96 * sd)]}
        for name, mu, sd in zip(names, result.fe_mean, result.fe_sd)
    }
    variance = {
        name: {"log_sd_mean": float(mu), "log_sd_posterior_sd": float(sd),
               "sd_posterior_median": float(np.exp(mu)),
               "sd_normal_approximate_95_interval": [float(np.exp(mu - 1.96 * sd)), float(np.exp(mu + 1.96 * sd))]}
        for name, mu, sd in zip(("family", "area"), result.vcp_mean, result.vcp_sd)
    }
    return {"model": model_name, "started_utc": started, "finished_utc": utcnow(),
            "statsmodels_version": statsmodels.__version__, "rows": len(frame),
            "systems": int(frame.Glottocode.nunique()), "family_groups": len(families), "areas": areas,
            "design_rank": int(np.linalg.matrix_rank(X28)), "fixed_effect_columns": names,
            "fixed_effects": fixed, "random_intercept_scale": variance,
            "attempts": attempts, "converged": bool(attempts[-1]["success"] and attempts[-1]["all_parameters_and_sd_finite"]),
            "prior": {"fixed_effect_sd": 2, "log_random_sd_prior_sd": 0.5},
            "weighting": "未加权独立敏感性；不是谱系等权主估计。",
            "interval_scope": "均值场变分后验的正态近似；仍未单独表示语言内28对依赖。"}


def run_glmm(metadata, baseline):
    source = Path(__file__).read_bytes()
    assert hashlib.sha256(source).hexdigest() == metadata["script_sha256"]
    (HERE / "uncertainty_glmm_executed_script.log").write_bytes(source)
    report = {"status": "running", "started_utc": utcnow(), "metadata": metadata,
              "frozen_baseline_reproduction": baseline, "models": {}}
    output = HERE / "glmm_results.json"
    save_json(output, report)
    with ProcessPoolExecutor(max_workers=3) as pool:
        jobs = {pool.submit(fit_one_glmm, model): model for model in ("M0", "M2", "M4")}
        for future in as_completed(jobs):
            name = jobs[future]
            try:
                report["models"][name] = future.result()
            except Exception as exc:
                report["models"][name] = {"model": name, "converged": False,
                                           "error": repr(exc), "finished_utc": utcnow()}
            save_json(output, report)
    report["finished_utc"] = utcnow()
    report["status"] = "completed"
    report["all_models_converged"] = all(x["converged"] for x in report["models"].values())
    save_json(output, report)
    print("GLMM三模型完成：" + str(output), flush=True)


def annotate_input_accounting(frame):
    """只补输入清单与真实执行时序，不重新估计或改变任何模型结果。"""
    records = frame[["Language_ID", "Glottocode", "Name", "family_group", "area_primary"]].drop_duplicates()
    missing = records[records.area_primary.eq("")].sort_values("Glottocode")
    complete = records[records.area_primary.ne("")]
    accounting = {"primary_systems": len(records), "complete_case_systems": len(complete),
                  "complete_case_pairs": len(complete) * 28,
                  "complete_case_family_groups": int(complete.family_group.nunique()),
                  "excluded_missing_area_systems": len(missing),
                  "excluded_system_records": missing.to_dict("records"),
                  "policy": "随机区域截距仅使用area_primary非空的完整个案；其他主分析仍用939系统。"}
    glmm_path = HERE / "glmm_results.json"
    if glmm_path.exists():
        result = json.loads(glmm_path.read_text())
        assert all(item["systems"] == len(complete) and item["rows"] == len(complete) * 28
                   for item in result["models"].values())
        result["input_accounting"] = accounting
        clarification_commit = "b3640d9336e3dfd98673ff8f7a31ff1cc835a1cc"
        clarification_time = subprocess.check_output(
            ["git", "show", "-s", "--format=%cI", clarification_commit], cwd=BASE, text=True).strip()
        snapshot = HERE / "uncertainty_glmm_executed_script.log"
        assert digest(snapshot) == result["metadata"]["script_sha256"]
        result["execution_source_snapshot"] = {"file": snapshot.name, "sha256": digest(snapshot)}
        result["implementation_timing_account"] = {
            "initial_glmm_started_utc": result["started_utc"],
            "missing_area_clarification_commit": clarification_commit,
            "missing_area_clarification_committed_utc": clarification_time,
            "clarification_commit_is_after_initial_fit_start": (
                datetime.datetime.fromisoformat(clarification_time)
                > datetime.datetime.fromisoformat(result["started_utc"])),
            "note": "初始执行版本已排除缺地域记录；并行发现后的澄清提交晚于启动，不能冒称运行前提交证据。输入筛选未依据GLMM结果改变。",
        }
        result["interpretation_status"] = (
            "三个模型两次协议内尝试均precision loss，未达到预置收敛；后验数值仅供诊断，不用于稳定推断。"
            if not result["all_models_converged"] else "协议内优化收敛。")
        result["accounting_annotation_utc"] = utcnow()
        result["accounting_script_sha256"] = digest(__file__)
        save_json(glmm_path, result)
    uncertainty_path = HERE / "uncertainty_results.json"
    if uncertainty_path.exists():
        result = json.loads(uncertainty_path.read_text())
        snapshot = HERE / "uncertainty_bootstrap_executed_script.log"
        assert digest(snapshot) == result["metadata"]["script_sha256"]
        result["execution_source_snapshot"] = {"file": snapshot.name, "sha256": digest(snapshot)}
        result["regional_input_accounting"] = accounting
        result["accounting_annotation_utc"] = utcnow()
        result["accounting_script_sha256"] = digest(__file__)
        save_json(uncertainty_path, result)
    print("已补完整个案清单与执行时序，未重估模型。", flush=True)


def grouped_rates(frame, pair_types):
    systems = frame[["Glottocode", "family_group"]].drop_duplicates()
    means = frame.pivot_table(index="family_group", columns="pair_type", values="shared_form", aggfunc="mean")
    means = means.reindex(index=sorted(systems.family_group.unique()), columns=pair_types)
    assert not means.isna().any().any()
    return means, len(systems), int(systems.family_group.nunique())


def numerical_checks(frame, pair_types, X, success, total, fitter):
    """核对真实加权聚合，并用有解析答案的合成资料检验两个估计分支。"""
    row_indices = frame.pair_type.map({key: i for i, key in enumerate(pair_types)}).to_numpy()
    rows_X = X[row_indices]
    systems = frame[["Glottocode", "family_group"]].drop_duplicates()
    family_sizes = systems.family_group.value_counts()
    weight = (len(systems) / (len(family_sizes) * frame.family_group.map(family_sizes) * 28)).to_numpy()
    y = frame.shared_form.to_numpy()
    beta = np.linspace(-0.3, 0.4, X.shape[1])
    eta_rows, eta_cells = rows_X @ beta, X @ beta
    row_objective = np.sum(weight * (y * eta_rows - np.logaddexp(0, eta_rows)))
    cell_objective = success @ eta_cells - total @ np.logaddexp(0, eta_cells)
    row_gradient = rows_X.T @ (weight * (y - expit(eta_rows)))
    cell_gradient = X.T @ (success - total * expit(eta_cells))
    row_information = rows_X.T @ ((weight * expit(eta_rows) * (1 - expit(eta_rows)))[:, None] * rows_X)
    cell_information = X.T @ ((total * expit(eta_cells) * (1 - expit(eta_cells)))[:, None] * X)
    differences = {"objective": float(abs(row_objective - cell_objective)),
                   "gradient": float(np.max(np.abs(row_gradient - cell_gradient))),
                   "information": float(np.max(np.abs(row_information - cell_information))),
                   "total_weight": float(abs(weight.sum() - total.sum()))}
    assert max(differences.values()) < 1e-9, differences
    known_beta = np.linspace(-0.4, 0.2, X.shape[1])
    synthetic_total = np.full(len(X), 200.0)
    synthetic_success = synthetic_total * expit(X @ known_beta)
    recovered, recovered_diag = fitter(X, synthetic_success, synthetic_total, estimator="MLE")
    parameter_error = float(np.max(np.abs(recovered - known_beta)))
    prediction_error = float(np.max(np.abs(expit(X @ recovered) - expit(X @ known_beta))))
    assert recovered_diag["converged"] and recovered_diag["method"] == "MLE"
    assert parameter_error < 1e-5 and prediction_error < 1e-6
    firth_cases = []
    for test_X, test_success, test_total in [
        (np.ones((1, 1)), np.array([0.0]), np.array([20.0])),
        (np.array([[1.0, -1.0], [1.0, 1.0]]), np.array([0.0, 20.0]), np.array([20.0, 20.0])),
    ]:
        fitted, diag = fitter(test_X, test_success, test_total, estimator="MLE")
        analytic = (test_success + 0.5) / (test_total + 1)
        error = float(np.max(np.abs(expit(test_X @ fitted) - analytic)))
        assert diag["converged"] and diag["method"] == "Firth" and diag["separation"]
        assert error < 1e-7
        firth_cases.append({"binomial_cells": len(test_X), "analytic_probability_max_error": error,
                            "diagnostics": diag})
    return {"passed": True, "actual_weighted_row_vs_cell_absolute_errors": differences,
            "synthetic_finite_MLE": {"parameter_max_error": parameter_error,
                                     "probability_max_error": prediction_error, "diagnostics": recovered_diag},
            "synthetic_separated_Firth_analytic_cases": firth_cases,
            "scope": "验证目标/梯度/信息矩阵的聚合等价与解析可解估计，不重现内部实现作为答案。"}


def run_coefficients(metadata, baseline):
    from s2_models import build_design, fit_aggregated

    source = Path(__file__).read_bytes()
    assert hashlib.sha256(source).hexdigest() == metadata["script_sha256"]
    (HERE / "uncertainty_bootstrap_executed_script.log").write_bytes(source)
    frame, pair_types = load_data()
    X = np.asarray(build_design(pair_types, "M4"), dtype=float)
    independent_X, columns = own_design(pair_types, "M4")
    assert X.shape == (28, 14) and np.array_equal(X, independent_X)
    means, N, G = grouped_rates(frame, pair_types)
    assert (N, G) == (939, 125)
    total = np.full(28, N / 28)
    success = (N / (28 * G)) * means.to_numpy().sum(axis=0)
    checks = numerical_checks(frame, pair_types, X, success, total, fit_aggregated)
    print("聚合等价与合成解析核验通过：" + json.dumps(clean_json(checks), ensure_ascii=False), flush=True)
    point, point_diagnostics = fit_aggregated(X, success, total, estimator="MLE")
    point = np.asarray(point)
    result = {"status": "running", "started_utc": utcnow(), "metadata": metadata,
              "frozen_baseline_reproduction": baseline,
              "numerical_verification": checks,
              "fit_api_sha256": digest(HERE / "s2_models.py"),
              "measurement": "D1", "weighting": "family_equal", "estimator_requested": "MLE",
              "systems": N, "family_groups": G, "pairs": len(frame),
              "columns": columns, "pair_types": pair_types,
              "full_sample_coefficients": dict(zip(columns, point.tolist())),
              "full_sample_diagnostics": point_diagnostics,
              "bootstrap_requested": BOOTSTRAPS,
              "bootstrap_weight_formula": "k_g*N/(G*n_g*28); 每次总权重固定N",
              "regional_coefficients": {}}
    for area in sorted(frame.area_primary.unique()):
        if not area:
            continue
        subset = frame[frame.area_primary.eq(area)]
        regional, regional_N, regional_G = grouped_rates(subset, pair_types)
        reg_total = np.full(28, regional_N / 28)
        reg_success = regional_N / (28 * regional_G) * regional.to_numpy().sum(axis=0)
        beta, diagnostic = fit_aggregated(X, reg_success, reg_total, estimator="MLE")
        beta = np.asarray(beta)
        result["regional_coefficients"][area] = {
            "systems": regional_N, "family_groups": regional_G,
            "coefficients": dict(zip(columns, beta.tolist())),
            "theory_term_signs": {term: int(np.sign(beta[columns.index(term)])) for term in TERMS},
            "diagnostics": diagnostic,
        }
    save_json(HERE / "uncertainty_results.json", result)
    rng = np.random.default_rng(SEED)
    draws = rng.integers(0, G, size=(BOOTSTRAPS, G))
    counts = np.zeros((BOOTSTRAPS, G), dtype=np.int16)
    np.add.at(counts, (np.repeat(np.arange(BOOTSTRAPS), G), draws.ravel()), 1)
    all_success = (N / (28 * G)) * (counts @ means.to_numpy())
    coefficients = np.full((BOOTSTRAPS, 14), np.nan)
    valid = np.zeros(BOOTSTRAPS, dtype=bool)
    methods = []
    errors = []
    started_clock = time.perf_counter()
    output = HERE / "coefficient_bootstrap.csv"
    fields = ["replicate", "unique_sampled_families", "weight_sum_expected", "method", "converged",
              "iterations", "standardized_score", "weight_sum_reported", "error", "diagnostics_json"] + columns
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for index in range(BOOTSTRAPS):
            error = ""
            diagnostic = {}
            try:
                beta, diagnostic = fit_aggregated(X, all_success[index], total, estimator="MLE")
                beta = np.asarray(beta, dtype=float)
                coefficients[index] = beta
                valid[index] = bool(diagnostic.get("converged", False) and np.isfinite(beta).all())
                if not valid[index]:
                    error = "未达到已定收敛规则"
            except Exception as exc:
                error = repr(exc)
            method = diagnostic.get("method", "failed")
            methods.append(method)
            errors.append(error)
            record = {"replicate": index, "unique_sampled_families": int(np.count_nonzero(counts[index])),
                      "weight_sum_expected": N, "method": method, "converged": bool(valid[index]),
                      "iterations": diagnostic.get("iterations"), "standardized_score": diagnostic.get("standardized_score"),
                      "weight_sum_reported": diagnostic.get("weight_sum"), "error": error,
                      "diagnostics_json": json.dumps(clean_json(diagnostic), ensure_ascii=False),
                      **dict(zip(columns, coefficients[index].tolist()))}
            writer.writerow(record)
            if (index + 1) % 250 == 0:
                stream.flush()
                print(f'系数重拟合 {index + 1}/{BOOTSTRAPS}，成功{int(valid[:index + 1].sum())}，耗时{time.perf_counter() - started_clock:.1f}秒', flush=True)
    result["bootstrap_completed"] = BOOTSTRAPS
    result["bootstrap_valid"] = int(valid.sum())
    result["bootstrap_failures"] = int((~valid).sum())
    result["all_requested_refits_converged"] = bool(valid.all())
    result["bootstrap_method_counts"] = {method: methods.count(method) for method in sorted(set(methods))}
    result["bootstrap_failure_replicates"] = np.flatnonzero(~valid).tolist()
    result["bootstrap_failure_messages"] = {str(i): errors[i] for i in np.flatnonzero(~valid)}
    result["bootstrap_csv_sha256"] = digest(output)
    result["bootstrap_intervals_conditioned_on_successful_refits"] = not bool(valid.all())
    result["theory_terms"] = {}
    for term in TERMS:
        values = coefficients[valid, columns.index(term)]
        ci = np.quantile(values, [0.025, 0.975]).tolist() if len(values) else [None, None]
        bonferroni = np.quantile(values, [0.05 / 6, 1 - 0.05 / 6]).tolist() if len(values) else [None, None]
        direction = "方向证据未定"
        if len(values) and ci[1] < 0:
            direction = "逐项95%区间支持预期负方向"
        elif len(values) and ci[0] > 0:
            direction = "逐项95%区间支持相反方向"
        result["theory_terms"][term] = {
            "point_estimate": float(point[columns.index(term)]),
            "family_refit_percentile_95_interval": ci,
            "bonferroni_98_333333_percent_interval": bonferroni,
            "negative_fraction": float(np.mean(values < 0)) if len(values) else None,
            "valid_replicates": len(values), "direction_assessment": direction,
        }
    result["all_three_pointwise_intervals_below_zero"] = bool(valid.sum() and all(
        result["theory_terms"][term]["family_refit_percentile_95_interval"][1] < 0 for term in TERMS))
    result["interval_scope"] = "整谱系重抽样并重拟合的全样本条件系数区间；不是固定折外评分区间。"
    result["finished_utc"] = utcnow()
    result["elapsed_bootstrap_seconds"] = time.perf_counter() - started_clock
    result["status"] = "completed"
    save_json(HERE / "uncertainty_results.json", result)
    print("系数重拟合完成：" + json.dumps(result["theory_terms"], ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=("glmm", "bootstrap", "all", "accounting"), default="all")
    args = parser.parse_args()
    metadata = verify_protocol()
    frame, pair_types = load_data()
    if args.task == "accounting":
        annotate_input_accounting(frame)
        return
    existing_check = HERE / "s2_baseline_reproduction.json"
    if existing_check.exists():
        baseline = json.loads(existing_check.read_text())
        assert baseline["passed"] and baseline["protocol_sha256"] == PROTOCOL_SHA
        assert baseline["max_absolute_error"] < 1e-9
        baseline = {**baseline, "artifact_sha256": digest(existing_check)}
    else:
        baseline = verify_frozen_baseline(frame, pair_types)
    if args.task in ("glmm", "all"):
        run_glmm(metadata, baseline)
    if args.task in ("bootstrap", "all"):
        run_coefficients(metadata, baseline)


if __name__ == "__main__":
    main()
