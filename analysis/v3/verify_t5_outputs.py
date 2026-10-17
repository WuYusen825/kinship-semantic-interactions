"""独立重算本轮T5导出值，不调用T5拟合器、评分器或自助实现。"""
from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd
from scipy.special import expit, logit
from scipy.stats import t

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "results/t5"
MODELS = tuple("M" + str(i) for i in range(5))
KEYS = ["measurement", "estimator", "weighting", "validation"]


def read(name):
    return json.loads((HERE / name).read_text())


def check_close(actual, expected, tolerance=2e-12):
    error = float(np.max(np.abs(np.asarray(actual) - np.asarray(expected))))
    assert error <= tolerance, (error, tolerance)
    return error


def weight_rows(frame):
    systems = frame[["Language_ID", "family_group"]].drop_duplicates()
    counts = systems.groupby("family_group").size()
    weight = 1 / frame.family_group.map(counts).to_numpy(float)
    return weight / weight.sum()


def binary_loss(y, p):
    p = np.clip(p, 1e-15, 1-1e-15)
    return -y * np.log(p) - (1-y) * np.log1p(-p)


def auc_by_weighted_ranks(y, p, weight):
    # 对相同预测值先合并，正类权重乘以累积负类权重；相等时计半分。
    cells = pd.DataFrame({"p": p, "positive": weight*y,
                          "negative": weight*(1-y)}).groupby("p").sum().sort_index()
    below = cells.negative.cumsum() - cells.negative
    return float((cells.positive * (below + .5*cells.negative)).sum() /
                 (cells.positive.sum()*cells.negative.sum()))


def main():
    checks = {}
    strict = read("strict_results.json")
    for name, expected in strict["files"].items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest() == expected
    for name, path in [("runner_sha256", ROOT/"analysis/v3/run_t5.py"),
                       ("pair_models_sha256", ROOT/"analysis/v3/pair_models.py")]:
        assert hashlib.sha256(path.read_bytes()).hexdigest() == strict[name]
    checks["严格缓存与代码哈希"] = True

    scores = pd.read_csv(HERE/"strict_language_scores.csv", dtype={"fold": str}, keep_default_na=False)
    pred = pd.read_csv(HERE/"strict_pair_predictions.csv.gz", dtype={"fold": str}, keep_default_na=False)
    id_keys = ["weighting", "validation", "fold", "Language_ID"]
    assert not scores.duplicated(id_keys).any()
    assert pred.groupby(id_keys).size().eq(28).all()
    assert scores[["loss_"+m for m in MODELS]].notna().all().all()
    error = 0.
    for model in MODELS:
        pred["check"] = binary_loss(pred.shared_form.to_numpy(), pred["p_"+model].to_numpy())
        recomputed = pred.groupby(id_keys).check.mean().reset_index()
        joined = scores.merge(recomputed, on=id_keys, validate="one_to_one")
        assert len(joined) == len(scores)
        error = max(error, check_close(joined["loss_"+model], joined.check))
    checks["严格样本逐对重算逐系统loss最大误差"] = error

    folds = read("fold_info.json")
    checked_folds = 0
    for item in folds:
        assert not set(item["train_system_ids"]) & set(item["test_system_ids"])
        if item["validation"] == "family":
            assert not set(item["train_family_ids"]) & set(item["test_family_ids"])
        checked_folds += 1
    checks["训练测试系统与谱系分组隔离的折数"] = checked_folds

    all_scores = pd.read_csv(HERE/"all_language_scores.csv.gz", keep_default_na=False)
    spec = read("specification_results.json")
    curve = pd.read_csv(HERE/"specification_curve.csv", keep_default_na=False)
    assert len(spec["settings"]) == 60 and len(curve) == 180
    max_score_error = max_ci_error = 0.
    for setting in spec["settings"]:
        block = all_scores
        rows = curve
        for key in KEYS:
            block = block[block[key].eq(setting[key])]
            rows = rows[rows[key].eq(setting[key])]
        assert len(block) == setting["systems"] and len(rows) == 3
        assert not block.Language_ID.duplicated().any()
        language_losses = block[["loss_"+m for m in MODELS]].to_numpy()
        assert np.isfinite(language_losses).all()
        groups = sorted(block.family_group.unique())
        group_idx = np.asarray([groups.index(value) for value in block.family_group])
        counts = np.bincount(group_idx)
        sums = np.zeros((len(groups), 5))
        for j in range(5):
            sums[:, j] = np.bincount(group_idx, weights=language_losses[:, j])
        if setting["weighting"] == "family":
            score = (sums/counts[:, None]).mean(axis=0)
        else:
            score = language_losses.mean(axis=0)
        max_score_error = max(max_score_error, check_close(score, [setting["logloss"][m] for m in MODELS]))
        # 用重抽频数矩阵求和，独立于被审查代码的索引后均值实现。
        draws = np.random.default_rng(20261016).integers(0, len(groups), size=(5000, len(groups)))
        multiplicity = np.stack([np.bincount(row, minlength=len(groups)) for row in draws])
        if setting["weighting"] == "family":
            bootstrap_scores = multiplicity @ (sums/counts[:, None]) / len(groups)
        else:
            bootstrap_scores = (multiplicity @ sums) / (multiplicity @ counts)[:, None]
        for row in rows.itertuples():
            baseline, larger = MODELS.index(row.baseline), MODELS.index(row.larger_model)
            ci = np.quantile(bootstrap_scores[:, baseline]-bootstrap_scores[:, larger], [.025, .975])
            max_ci_error = max(max_ci_error, check_close(ci, [row.ci95_low, row.ci95_high]))
            check_close(score[baseline]-score[larger], row.gain)
    diagnostics = read("fit_diagnostics.json")
    assert len(diagnostics) == 1600 and all(d["converged"] for d in diagnostics)
    assert curve.available.all()
    checks.update({"规格数": 60, "区间数": 180, "收敛拟合数": len(diagnostics),
                   "全规格loss最大误差": max_score_error, "180区间独立频数重算最大误差": max_ci_error})

    regions = pd.read_csv(HERE/"regional_pair_predictions.csv.gz", keep_default_na=False)
    calibration = read("regional_calibration_results.json")
    max_loss_error = max_auc_error = max_rate_error = 0.
    for row in calibration["regions"]:
        assert row["available"]
        block = regions[regions.macroarea.eq(row["macroarea"])]
        y, probability = block.shared_form.to_numpy(), block["p_"+row["model"]].to_numpy()
        weight = weight_rows(block)
        recalibrated = expit(logit(probability)+row["intercept_offset"])
        max_loss_error = max(max_loss_error, check_close(weight@binary_loss(y, probability), row["raw_logloss"]),
                             check_close(weight@binary_loss(y, recalibrated), row["calibrated_diagnostic_logloss"]))
        max_auc_error = max(max_auc_error, check_close(auc_by_weighted_ranks(y, probability, weight), row["auc"]))
        max_rate_error = max(max_rate_error, check_close(weight@recalibrated, weight@y, 5e-12))
    assert regions.Language_ID.nunique() == 909 and len(calibration["regions"]) == 30
    for model in MODELS:
        rows = [r for r in calibration["regions"] if r["model"] == model]
        assert len(rows) == 6
        for metric in ["raw_logloss", "calibrated_diagnostic_logloss", "auc"]:
            check_close(np.mean([r[metric] for r in rows]), calibration["region_macro_average"][model][metric])
    checks.update({"六地域全部30个模型指标可用": True, "区域loss独立重算最大误差": max_loss_error,
                   "加权秩AUC最大误差": max_auc_error, "校准率匹配最大误差": max_rate_error})

    sandwich = read("cluster_sandwich.json")
    minimum_eigenvalue = float("inf")
    for weighting, models in sandwich["model_fits"].items():
        for model, fit in models.items():
            diagnostic, result = fit["diagnostics"], fit["sandwich"]
            assert diagnostic["converged"] and diagnostic["method"] == "MLE" and result["available"]
            covariance = np.asarray(result["covariance"])
            check_close(covariance, covariance.T)
            eigenvalue = float(np.linalg.eigvalsh(covariance).min())
            assert eigenvalue >= -1e-10
            minimum_eigenvalue = min(minimum_eigenvalue, eigenvalue)
            coefficient = np.asarray(fit["coefficients"])
            halfwidth = t.ppf(.975, 124)*np.sqrt(np.diag(covariance))
            check_close(np.c_[coefficient-halfwidth, coefficient+halfwidth], result["ci95"])
    checks["10个CR1协方差最小特征值"] = minimum_eigenvalue
    checks["10个主拟合与CR1区间可用"] = True

    vb = read("family_only_glmm.json")
    for model, fit in vb["models"].items():
        attempt = fit["attempts"][-1]
        assert fit["converged"] and fit["inference_available"] and attempt["optimizer_success"]
        assert attempt["gradient_max_abs"] <= 1e-6
        assert fit["systems"] == 939 and fit["families"] == 125
        assert np.isfinite([v["mean"] for v in fit["fixed_effects"].values()]).all()
    checks["VB严格收敛记录数"] = len(vb["converged_models"])
    checks["passed"] = True
    (HERE/"self_check.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(checks, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
