"""第三版T5入口：strict先交付T2共享配对基准；full按约定在T2–T4后执行。"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
from pathlib import Path

import numpy as np
import pandas as pd

import common
from common import ROOT, RESULTS, SEED, logged_run, save_json, sha256, utc_now, verify_analysis_plan
from pair_models import (MODELS, VALIDATIONS, WEIGHTINGS, ESTIMATORS, comparison_rows,
                         evaluate_cv, finite_json, fit_family_only_vb, full_sample_fit,
                         prepare_measurements, regional_calibration, row_weights, weighted_score)

OUT = RESULTS / "t5"


def provenance(gate):
    return {**gate, "seed": SEED, "bootstrap_replicates": 5000,
            "runner_sha256": sha256(__file__), "pair_models_sha256": sha256(Path(__file__).with_name("pair_models.py")),
            "S2_fitter_sha256": sha256(common.S2 / "s2_models.py"),
            "input_pairs_sha256": sha256(ROOT / "analysis/pairs_primary.csv")}


def write_gzip(frame, path):
    frame.to_csv(path, index=False, compression={"method": "gzip", "mtime": 0})


def compact_predictions(predictions):
    return predictions[[column for column in predictions.columns
                        if not column.startswith("loss_") and not column.startswith("brier_")]]


def fit_block(frame, pair_types, weighting, validation, estimator, sample):
    with logged_run("T5_fit", {"sample": sample, "weighting": weighting,
                               "validation": validation, "estimator": estimator}) as metrics:
        pred, scores, diagnostics, folds = evaluate_cv(frame, pair_types, weighting, validation, estimator, sample)
        metrics.update(systems=len(scores), fits=len(diagnostics),
                       converged=sum(bool(item["converged"]) for item in diagnostics),
                       losses={model: weighted_score(scores, "loss_" + model, weighting) for model in MODELS})
    print(utc_now(), sample, estimator, weighting, validation, metrics["losses"], flush=True)
    return pred, scores, diagnostics, folds


def strict_phase(gate=None):
    gate = verify_analysis_plan() if gate is None else gate
    OUT.mkdir(parents=True, exist_ok=True)
    definitions, pair_types = prepare_measurements()
    frame = definitions["D3"]
    if frame.Language_ID.nunique() != 625 or frame.family_group.nunique() != 108:
        raise RuntimeError("T1严格样本规模不一致")
    all_predictions, all_scores, diagnostics, folds = [], [], [], []
    with logged_run("T5d", {"sample": "strict", "weightings": WEIGHTINGS,
                            "validations": VALIDATIONS, "estimator": "MLE/Firth"}) as metrics:
        for weighting in WEIGHTINGS:
            for validation in VALIDATIONS:
                pred, scores, fit_info, fold_info = fit_block(frame, pair_types, weighting, validation, "MLE", "strict")
                all_predictions.append(compact_predictions(pred))
                all_scores.append(scores)
                diagnostics.extend(fit_info)
                folds.extend(fold_info)
        scores = pd.concat(all_scores, ignore_index=True)
        predictions = pd.concat(all_predictions, ignore_index=True)
        scores.to_csv(OUT / "strict_language_scores.csv", index=False)
        write_gzip(predictions, OUT / "strict_pair_predictions.csv.gz")
        save_json(OUT / "strict_fit_diagnostics.json", finite_json(diagnostics))
        save_json(OUT / "strict_fold_info.json", folds)
        fullfits = {weighting: full_sample_fit(frame, pair_types, weighting) for weighting in WEIGHTINGS}
        cells = []
        for weighting in WEIGHTINGS:
            for pattern, cell in frame.groupby("pattern"):
                w = row_weights(cell, weighting)
                cells.append({"weighting": weighting, "pattern": pattern,
                              "observed_rate": float(w @ cell.shared_form.to_numpy() / w.sum()),
                              "systems": int(cell.Language_ID.nunique()), "pairs": len(cell)})
        save_json(OUT / "strict_fullfit.json", {"sample": "strict", "systems": 625, "families": 108,
                                                "model_fits": fullfits, "seven_cells": cells,
                                                "coefficient_order_M2": fullfits["family"]["M2"]["columns"]})
        report = {**provenance(gate), "completed_utc": utc_now(), "sample": "strict", "systems": 625,
                  "families": 108, "settings": 6, "models": list(MODELS),
                  "cv_fits": len(diagnostics), "all_cv_fits_converged": all(item["converged"] for item in diagnostics),
                  "firth_fits": sum(item.get("method") == "Firth" for item in diagnostics),
                  "scores_file": "strict_language_scores.csv", "predictions_file": "strict_pair_predictions.csv.gz",
                  "fullfit_file": "strict_fullfit.json", "same_old_folds": True,
                  "missing_area_systems": int(frame.loc[frame.macroarea.eq(""), "Language_ID"].nunique()),
                  "schema_note": "逐系统loss为28对均值；validation/cv=family,area,language；fold字符串规范比较。",
                  "files": {name: sha256(OUT / name) for name in ["strict_language_scores.csv", "strict_pair_predictions.csv.gz",
                                                                    "strict_fit_diagnostics.json", "strict_fold_info.json", "strict_fullfit.json"]}}
        save_json(OUT / "strict_results.json", report)
        metrics.update(settings=6, cv_fits=report["cv_fits"], all_converged=report["all_cv_fits_converged"],
                       scores_file=report["scores_file"])
    return report


def load_strict_cache():
    path = OUT / "strict_results.json"
    if not path.exists():
        return None
    info = json.loads(path.read_text())
    if info["pair_models_sha256"] != sha256(Path(__file__).with_name("pair_models.py")):
        return None
    for name, expected in info["files"].items():
        if sha256(OUT / name) != expected:
            raise RuntimeError("严格结果缓存哈希改变：" + name)
    scores = pd.read_csv(OUT / "strict_language_scores.csv", keep_default_na=False, dtype={"fold": str})
    for column in ["loss_" + model for model in MODELS] + ["brier_" + model for model in MODELS]:
        scores[column] = pd.to_numeric(scores[column], errors="coerce")
    return scores, json.loads((OUT / "strict_fit_diagnostics.json").read_text()), json.loads((OUT / "strict_fold_info.json").read_text())


def specification_phase(definitions, pair_types, gate):
    cache = load_strict_cache()
    blocks, comparisons, all_scores, diagnostics, fold_info = [], [], [], [], []
    regional_predictions = None
    for measurement in ("D1", "D2", "D3", "D4", "D5"):
        for estimator in ESTIMATORS:
            for weighting in WEIGHTINGS:
                for validation in VALIDATIONS:
                    spec = {"measurement": measurement, "estimator": estimator, "weighting": weighting,
                            "validation": validation, "main_specification": (
                                measurement == "D1" and estimator == "MLE" and weighting == "family" and validation == "family")}
                    if cache is not None and measurement == "D3" and estimator == "MLE":
                        stored_scores, stored_diagnostics, stored_folds = cache
                        scores = stored_scores[stored_scores.weighting.eq(weighting) & stored_scores.validation.eq(validation)].copy()
                        fits = [item for item in stored_diagnostics if item["weighting"] == weighting and item["validation"] == validation]
                        folds = [item for item in stored_folds if item["weighting"] == weighting and item["validation"] == validation]
                        pred = None
                        origin = "复用本轮T5d已重拟合且哈希核验的确定性逐系统分数"
                    else:
                        pred, scores, fits, folds = fit_block(definitions[measurement], pair_types, weighting, validation, estimator, measurement)
                        origin = "本轮实际重拟合"
                    current = comparison_rows(scores, weighting, spec)
                    comparisons.extend(current)
                    block = {**spec, "systems": len(scores), "families": int(scores.family_group.nunique()),
                             "origin": origin, "logloss": {model: weighted_score(scores, "loss_" + model, weighting) for model in MODELS},
                             "comparisons": current, "all_fits_converged": all(item["converged"] for item in fits)}
                    blocks.append(block)
                    tagged_scores = scores.copy()
                    tagged_scores["measurement"] = measurement
                    all_scores.append(tagged_scores)
                    diagnostics.extend({**item, "measurement": measurement} for item in fits)
                    fold_info.extend({**item, "measurement": measurement} for item in folds)
                    common.log_run("T5c", spec, finite_json(block), "completed")
                    if measurement == "D1" and estimator == "MLE" and weighting == "family" and validation == "area":
                        regional_predictions = pred
                        write_gzip(compact_predictions(pred), OUT / "regional_pair_predictions.csv.gz")
    if len(blocks) != 60 or len(comparisons) != 180:
        raise RuntimeError("完整规格网格未达到60×3")
    pd.DataFrame(comparisons).to_csv(OUT / "specification_curve.csv", index=False)
    write_gzip(pd.concat(all_scores, ignore_index=True), OUT / "all_language_scores.csv.gz")
    save_json(OUT / "fit_diagnostics.json", finite_json(diagnostics))
    save_json(OUT / "fold_info.json", fold_info)
    results = {**provenance(gate), "settings": blocks, "settings_count": 60, "contrast_rows": 180,
               "all_fits_converged": all(item["converged"] for item in diagnostics),
               "cv_fits": len(diagnostics), "seed": SEED, "bootstrap_replicates": 5000}
    save_json(OUT / "specification_results.json", results)
    return results, regional_predictions


def calibration_phase(predictions):
    records = regional_calibration(predictions)
    pd.DataFrame(records).to_csv(OUT / "regional_calibration.csv", index=False)
    macro = {}
    for model in MODELS:
        available = [item for item in records if item["model"] == model and item["available"]]
        macro[model] = {"regions": len(available)}
        for field in ("raw_logloss", "calibrated_diagnostic_logloss", "auc"):
            values = [item[field] for item in available if item.get(field) is not None]
            macro[model][field] = float(np.mean(values)) if values else None
    contrasts = []
    for area in sorted({item["macroarea"] for item in records}):
        models = {item["model"]: item for item in records if item["macroarea"] == area}
        for baseline, larger in (("M0", "M2"), ("M0", "M4")):
            left, right = models[baseline], models[larger]
            if not left["available"] or not right["available"]:
                contrasts.append({"macroarea": area, "baseline": baseline, "larger_model": larger, "available": False})
                continue
            contrasts.append({"macroarea": area, "baseline": baseline, "larger_model": larger, "available": True,
                              "raw_gain": left["raw_logloss"] - right["raw_logloss"],
                              "calibrated_diagnostic_gain": left["calibrated_diagnostic_logloss"] - right["calibrated_diagnostic_logloss"],
                              "auc_gain": right["auc"] - left["auc"] if left["auc"] is not None and right["auc"] is not None else None})
    result = {"regions": records, "region_macro_average": macro, "contrasts": contrasts,
              "auc_definition": "区域内原始28对的加权ROC U统计量；每谱系总权相同，不是仅对可计算族AUC取均值。",
              "scope": "单一截距用留出区域真实结果估计，属于事后校准诊断，不是样本外重新预测。"}
    save_json(OUT / "regional_calibration_results.json", finite_json(result))
    common.log_run("T5a", {"sample": "D1", "weighting": "family", "validation": "area"}, finite_json(macro), "completed")
    return result


def dependence_phase(frame, pair_types):
    fits = {weighting: full_sample_fit(frame, pair_types, weighting, sandwich=True) for weighting in WEIGHTINGS}
    old = json.loads((common.S2 / "uncertainty_results.json").read_text())
    comparison = {}
    main = fits["family"]["M4"]
    for term in ("DrE", "DaB", "DaS"):
        index = main["columns"].index(term)
        comparison[term] = {"point_estimate": main["coefficients"][index],
                            "old_family_refit_point": old["theory_terms"][term]["point_estimate"],
                            "old_family_refit_95": old["theory_terms"][term]["family_refit_percentile_95_interval"],
                            "old_bootstrap_seed": old.get("metadata", {}).get("seed", 20261014),
                            "sandwich_95": main["sandwich"]["ci95"][index] if main["sandwich"]["available"] else None}
    output = {"sample": "D1", "systems": 939, "families": 125, "model_fits": fits,
              "M4_interval_comparison": comparison,
              "old_bootstrap_sha256": sha256(common.S2 / "uncertainty_results.json"),
              "scope": "CR1整谱系sandwich与旧重拟合区间并列；二者估计不确定性方法不同。"}
    save_json(OUT / "cluster_sandwich.json", output)
    common.log_run("T5b_sandwich", {"sample": "D1", "weightings": WEIGHTINGS}, comparison, "completed")
    glmm = {"started_utc": utc_now(), "models": {}, "scope": "仅谱系随机截距、未加权VB敏感性；无地域交叉项。"}
    with ProcessPoolExecutor(max_workers=3) as pool:
        jobs = {pool.submit(fit_family_only_vb, frame, pair_types, model): model for model in MODELS}
        for future in as_completed(jobs):
            model = jobs[future]
            try:
                item = future.result()
            except Exception as exc:
                item = {"model": model, "converged": False, "inference_available": False, "error": repr(exc)}
            glmm["models"][model] = item
            common.log_run("T5b_family_VB", {"sample": "D1", "model": model}, finite_json(item),
                           "converged" if item["converged"] else "failed_record_only")
            save_json(OUT / "family_only_glmm.json", glmm)
    glmm["finished_utc"] = utc_now()
    glmm["converged_models"] = sorted(name for name, item in glmm["models"].items() if item["converged"])
    glmm["failed_models"] = sorted(name for name, item in glmm["models"].items() if not item["converged"])
    glmm["inference_table"] = {name: item for name, item in glmm["models"].items() if item["converged"]}
    save_json(OUT / "family_only_glmm.json", glmm)
    return output, glmm


def figures(specifications, calibration):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    font = Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
    if font.exists():
        font_manager.fontManager.addfont(str(font))
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=str(font)).get_name()
    plt.rcParams["axes.unicode_minus"] = False
    curves = pd.read_csv(OUT / "specification_curve.csv")
    fig, axes = plt.subplots(1, 3, figsize=(16, 19), sharey=False)
    names = [("M2_over_M0", "M2相对M0"), ("M4_over_M2", "M4相对M2"), ("M4_over_M0", "M4相对M0")]
    colors = {"family": "#326baf", "area": "#c7652b", "language": "#39844b"}
    for ax, (name, label) in zip(axes, names):
        subset = curves[curves.comparison.eq(name)].sort_values("gain", na_position="last")
        for position, row in enumerate(subset.itertuples()):
            if not row.available:
                continue
            ax.plot([row.ci95_low, row.ci95_high], [position, position], color=colors[row.validation], alpha=.65)
            ax.plot(row.gain, position, "*" if row.main_specification else "o", color=colors[row.validation], markersize=10 if row.main_specification else 3)
        labels = [f"{r.measurement}/{r.estimator}/{r.weighting}/{r.validation}" for r in subset.itertuples()]
        ax.set_yticks(range(len(labels)), labels, fontsize=6)
        ax.axvline(0, color="gray", linestyle="--")
        ax.set_title(label)
        ax.set_xlabel("对数损失增益及固定预测谱系自助95%区间")
    fig.tight_layout()
    fig.savefig(OUT / "Fx_T5_specification_curve.png", dpi=160)
    fig.savefig(OUT / "Fx_T5_specification_curve.svg")
    plt.close(fig)
    records = calibration["regions"]
    fig, ax = plt.subplots(figsize=(7, 6))
    for model in MODELS:
        selected = [item for item in records if item["model"] == model and item["available"]]
        ax.scatter([item["observed_prevalence"] for item in selected],
                   [item["predicted_prevalence"] for item in selected], label=model, s=45)
    ax.plot([0, 1], [0, 1], "--", color="gray")
    ax.set_xlabel("留出区域实测共享率（区域内谱系等权）")
    ax.set_ylabel("原始预测共享率")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "Fx_T5_region_calibration.png", dpi=180)
    fig.savefig(OUT / "Fx_T5_region_calibration.svg")
    plt.close(fig)


def full_phase(gate=None):
    gate = verify_analysis_plan() if gate is None else gate
    OUT.mkdir(parents=True, exist_ok=True)
    with logged_run("T5_full", {"phase": "full", "seed": SEED}) as metrics:
        definitions, pair_types = prepare_measurements()
        specifications, regional_predictions = specification_phase(definitions, pair_types, gate)
        calibration = calibration_phase(regional_predictions)
        sandwich, glmm = dependence_phase(definitions["D1"], pair_types)
        figures(specifications, calibration)
        summary = {**provenance(gate), "completed_utc": utc_now(), "specifications": specifications,
                   "regional_calibration": calibration, "cluster_sandwich": sandwich, "family_only_glmm": glmm,
                   "strict_results_file": "strict_results.json", "status": "全部预设规格已记录；失败VB不进入推断表。"}
        save_json(OUT / "t5_results.json", finite_json(summary))
        lines = ["# 第三版T5结果", "", "## 规格曲线", "",
                 "全部60规格及180个预设增益的区间使用新种子20261016、5000次谱系整组重抽；完整表见specification_curve.csv。",
                 "", "## 地域诊断", "",
                 "截距偏移由测试区域真实结果估计，只作事后校准诊断。加权AUC为区域内谱系等权的ROC统计量；不把校准改进当作真正未见区域预测。",
                 "", "## 依赖与模型化敏感性", "",
                 "加权MLE的谱系CR1 sandwich采用t(G−1)区间，与旧M4重拟合区间并列。只有谱系随机截距的未加权VB拟合与主加权分析区分。",
                 "", "收敛的VB模型：" + ("、".join(glmm["converged_models"]) or "无") + "。",
                 "未收敛、仅保留诊断的VB模型：" + ("、".join(glmm["failed_models"]) or "无") + "。", "",
                 "## 严格样本共享基准", "", "strict_language_scores.csv与strict_pair_predictions.csv.gz提供T2配对比较所需的原折预测；失败行不被删除。", ""]
        (OUT / "report.md").write_text("\n".join(lines), encoding="utf-8")
        metrics.update(specifications=60, contrasts=180, converged_VB=glmm["converged_models"], failed_VB=glmm["failed_models"])
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("strict", "full"), default="strict")
    args = parser.parse_args()
    gate = verify_analysis_plan()
    if args.phase == "strict":
        strict_phase(gate)
    else:
        full_phase(gate)


if __name__ == "__main__":
    main()
