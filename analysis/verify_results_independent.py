"""独立核验已保存结果；不导入分析程序，也不拟合任何预测模型。

运行：python analysis/verify_results_independent.py
读取锁定原始数据、逐对预测及结果，写入 notes/independent_verification.json。
"""

from pathlib import Path
from collections import defaultdict
import datetime
import hashlib
import json
import re
import unicodedata

import numpy as np
import pandas as pd


BASE = Path(__file__).resolve().parents[1]
ANALYSIS = BASE / "analysis"
OUTPUT = BASE / "notes" / "independent_verification.json"
CATEGORIES = {"meB", "myB", "meZ", "myZ", "feB", "fyB", "feZ", "fyZ"}
MODELS = ("raw_additive", "classical_additive", "pairwise")
TOLERANCE = 1e-12


def normalized(value):
    return " ".join(unicodedata.normalize("NFC", value).split())


def main():
    results = json.loads((ANALYSIS / "results.json").read_text())
    pairs = pd.read_csv(ANALYSIS / "pairs_primary.csv", dtype={"pattern": str})
    predictions = pd.read_csv(ANALYSIS / "oof_predictions.csv", dtype={"pattern": str})
    stored_scores = pd.read_csv(ANALYSIS / "language_oof_scores.csv")
    raw = pd.read_csv(BASE / "data/kinbank/kinbank/cldf/forms.csv", keep_default_na=False)
    raw = raw[
        raw.Language_ID.isin(pairs.Language_ID.unique())
        & raw.Parameter_ID.isin(CATEGORIES)
    ].copy()
    raw["nf"] = [normalized(value) for value in raw.Form]
    raw = raw[~raw.nf.isin(("", "?", "-"))]
    form_sets = raw.groupby(["Language_ID", "Parameter_ID"]).nf.apply(set).to_dict()
    source_sets = defaultdict(dict)
    for record in raw.itertuples():
        source_ids = {
            re.sub(r"\[[^]]*\]", "", item).strip()
            for item in record.Source.split(";")
        }
        source_ids.discard("")
        source_sets[(record.Language_ID, record.Parameter_ID)].setdefault(
            record.nf, set()
        ).update(source_ids)

    overlap_mismatches = 0
    feature_mismatches = 0
    relative_mismatches = 0
    unordered_keys = []
    source_support = {"supported_no_missing": 0, "unsupported_with_missing": 0,
                      "unsupported_no_missing": 0, "supported_with_missing": 0}
    for pair in pairs.itertuples():
        first = form_sets[(pair.Language_ID, pair.category_a)]
        second = form_sets[(pair.Language_ID, pair.category_b)]
        common = first & second
        overlap_mismatches += int(bool(common)) != pair.shared_form
        differences = (
            int(pair.category_a[2] != pair.category_b[2]),
            int(pair.category_a[1] != pair.category_b[1]),
            int(pair.category_a[0] != pair.category_b[0]),
        )
        feature_mismatches += differences != (pair.Dr, pair.Da, pair.De)
        relative_mismatches += int(differences[0] != differences[2]) != pair.Drelative
        unordered_keys.append((pair.Glottocode, *sorted((pair.category_a, pair.category_b))))
        if common:
            source_a = source_sets[(pair.Language_ID, pair.category_a)]
            source_b = source_sets[(pair.Language_ID, pair.category_b)]
            supported = any(source_a[form] & source_b[form] for form in common)
            missing = any(not source_a[form] or not source_b[form] for form in common)
            label = ("supported" if supported else "unsupported") + (
                "_with_missing" if missing else "_no_missing"
            )
            source_support[label] += 1

    glottolog = pd.read_csv(BASE / "data/glottolog_languages.csv", keep_default_na=False)
    glottolog = glottolog.set_index("ID")
    genealogy_mismatches = []
    for language in pairs[["Glottocode", "family_group"]].drop_duplicates().itertuples():
        row = glottolog.loc[language.Glottocode]
        if row.Family_ID:
            expected = row.Family_ID
        else:
            language_root = row.Language_ID or language.Glottocode
            is_isolate = row.Is_Isolate == "true" or (
                language_root in glottolog.index
                and glottolog.loc[language_root].Is_Isolate == "true"
            )
            expected = "isolate:" + language_root if is_isolate else ""
        if language.family_group != expected:
            genealogy_mismatches.append(language.Glottocode)

    checks = {
        "primary_pairs": len(pairs),
        "primary_languages": int(pairs.Glottocode.nunique()),
        "primary_genealogical_groups": int(pairs.family_group.nunique()),
        "each_language_28_pairs": bool(pairs.groupby("Glottocode").size().eq(28).all()),
        "each_language_seven_patterns_four_pairs": bool(
            pairs.groupby(["Glottocode", "pattern"]).size().eq(4).all()
        ),
        "observed_patterns": sorted(pairs.pattern.unique().tolist()),
        "duplicate_unordered_pairs": len(unordered_keys) - len(set(unordered_keys)),
        "raw_overlap_mismatches": int(overlap_mismatches),
        "feature_bit_mismatches": int(feature_mismatches),
        "relative_sex_bit_mismatches": int(relative_mismatches),
        "genealogy_mapping_mismatches": genealogy_mismatches,
        "source_support_cross_tab": source_support,
        "condition_checks": [],
    }
    max_metric_error = max_loss_error = max_saved_score_error = max_ci_error = 0.0
    score_keys = ["Glottocode", "Language_ID", "family_group"]
    comparisons = (("raw", "raw_additive", "pairwise"),
                   ("classical", "classical_additive", "pairwise"),
                   ("classical_over_raw", "raw_additive", "classical_additive"))

    for metric in results["analyses"]:
        variant, grouping = metric["variant"], metric["cv_grouping"]
        subset = predictions[
            predictions.variant.eq(variant) & predictions.cv_grouping.eq(grouping)
        ].copy()
        variant_input = pd.read_csv(ANALYSIS / ("pairs_" + variant + ".csv"),
                                    dtype={"pattern": str})
        pair_keys = ["Language_ID", "Glottocode", "category_a", "category_b"]
        input_join = subset.merge(
            variant_input[pair_keys + ["shared_form", "family_group", "pattern"]],
            on=pair_keys, suffixes=("_prediction", "_input"), validate="one_to_one"
        )
        input_matches = len(input_join) == len(subset) == len(variant_input) and all(
            input_join[column + "_prediction"].eq(input_join[column + "_input"]).all()
            for column in ("shared_form", "family_group", "pattern")
        )
        group_column = "family_group" if grouping == "family" else "Glottocode"
        leakage = int(subset.groupby(group_column).fold.nunique().gt(1).sum())
        language_leakage = int(subset.groupby("Glottocode").fold.nunique().gt(1).sum())
        probability_valid = True
        y = subset.shared_form.to_numpy()
        for model in MODELS:
            p = subset["p_" + model].to_numpy()
            probability_valid &= bool(np.isfinite(p).all() and ((p > 0) & (p < 1)).all())
            loss = -np.log(np.where(y == 1, p, 1 - p))
            subset["loss_" + model + "_independent"] = loss
            subset["brier_" + model + "_independent"] = (p - y) ** 2
            max_loss_error = max(max_loss_error, float(np.max(
                np.abs(loss - subset["loss_" + model].to_numpy())
            )))

        independent = subset.groupby(score_keys, as_index=False).agg({
            column: "mean" for column in subset.columns if column.endswith("_independent")
        })
        independent = independent.rename(columns={
            column: column.removesuffix("_independent")
            for column in independent.columns if column.endswith("_independent")
        })
        saved = stored_scores[
            stored_scores.variant.eq(variant) & stored_scores.cv_grouping.eq(grouping)
        ]
        matched = independent.merge(saved, on=score_keys, suffixes=("_computed", "_stored"),
                                    validate="one_to_one")
        for model in MODELS:
            for prefix in ("loss_", "brier_"):
                col = prefix + model
                max_saved_score_error = max(max_saved_score_error, float(np.max(np.abs(
                    matched[col + "_computed"] - matched[col + "_stored"]
                ))))
            max_metric_error = max(
                max_metric_error,
                abs(float(independent["loss_" + model].mean())
                    - metric["language_equal_logloss"][model]),
                abs(float(subset["loss_" + model + "_independent"].mean())
                    - metric["pair_equal_logloss"][model]),
                abs(float(independent["brier_" + model].mean())
                    - metric["language_equal_brier"][model]),
            )
        reproduced_comparisons = {}
        for name, baseline, alternative in comparisons:
            delta = independent["loss_" + baseline] - independent["loss_" + alternative]
            fstats = pd.DataFrame({"delta": delta, "family": independent.family_group}).groupby(
                "family"
            ).delta.agg(["sum", "size"])
            draws = np.random.default_rng(20261014).integers(
                fstats.shape[0], size=(5000, fstats.shape[0])
            )
            draws_sum = fstats["sum"].values[draws].sum(axis=1)
            draws_n = fstats["size"].values[draws].sum(axis=1)
            ci = np.quantile(draws_sum / draws_n, [0.025, 0.975])
            observed = metric["comparisons"][name]
            max_metric_error = max(max_metric_error,
                                   abs(float(delta.mean()) - observed["language_equal_gain"]))
            max_ci_error = max(max_ci_error, float(np.max(np.abs(
                ci - np.asarray(observed["family_cluster_bootstrap_95ci"])
            ))))
            reproduced_comparisons[name] = {
                "language_equal_gain": float(delta.mean()),
                "fixed_prediction_family_cluster_interval": ci.tolist(),
            }
        checks["condition_checks"].append({
            "variant": variant,
            "cv_grouping": grouping,
            "pairs": len(subset),
            "languages": int(subset.Glottocode.nunique()),
            "genealogical_groups": int(subset.family_group.nunique()),
            "leaking_group_count": leakage,
            "leaking_language_count": language_leakage,
            "all_probabilities_finite_and_inside_unit_interval": probability_valid,
            "predictions_match_all_variant_input_pairs": bool(input_matches),
            "five_test_folds_present": sorted(subset.fold.unique().tolist()) == list(range(5)),
            "saved_language_score_rows_matched": len(matched) == len(saved) == len(independent),
            "reproduced_comparisons": reproduced_comparisons,
        })

    mle_predictions = predictions[
        predictions.variant.eq("unpenalized") & predictions.cv_grouping.eq("family")
    ]
    mle_fold_error = 0.0
    for fold in sorted(mle_predictions.fold.unique()):
        training_rates = mle_predictions[mle_predictions.fold.ne(fold)].groupby(
            "pattern"
        ).shared_form.mean()
        test = mle_predictions[mle_predictions.fold.eq(fold)]
        mle_fold_error = max(mle_fold_error, float(np.max(np.abs(
            test.p_pairwise.to_numpy() - test.pattern.map(training_rates).to_numpy()
        ))))
    cells = pd.read_csv(ANALYSIS / "seven_cell_probabilities.csv", dtype={"pattern": str})
    observed_rates = pairs.groupby("pattern").shared_form.mean()
    mle_full_error = float(np.max(np.abs(
        cells.p_pairwise_mle.to_numpy() - cells.pattern.map(observed_rates).to_numpy()
    )))
    rate_error = float(np.max(np.abs(
        cells.share_rate.to_numpy() - cells.pattern.map(observed_rates).to_numpy()
    )))
    diagnostics = pd.read_csv(ANALYSIS / "cv_fit_diagnostics.csv")
    ranks = {"raw_additive": 4, "classical_additive": 5, "pairwise": 7}
    provenance = json.loads((ANALYSIS / "provenance.json").read_text())
    script_matches = hashlib.sha256((ANALYSIS / "analyze.py").read_bytes()).hexdigest() == (
        provenance["script_sha256"]
    )
    checks.update({
        "maximum_aggregate_metric_error": max_metric_error,
        "maximum_saved_dyad_loss_error": max_loss_error,
        "maximum_saved_language_score_error": max_saved_score_error,
        "maximum_cluster_interval_error": max_ci_error,
        "maximum_saved_cell_rate_error": rate_error,
        "mle_oof_vs_training_cell_rates_max_error": mle_fold_error,
        "mle_fullfit_vs_observed_cell_rates_max_error": mle_full_error,
        "fit_count": len(diagnostics),
        "all_saved_fit_statuses_converged": bool(diagnostics.converged.all()),
        "all_saved_fit_ranks_correct": bool(diagnostics.apply(
            lambda row: row.design_rank == ranks[row.model], axis=1
        ).all()),
        "analysis_script_matches_provenance": script_matches,
    })
    structural_pass = (
        checks["each_language_28_pairs"] and checks["each_language_seven_patterns_four_pairs"]
        and checks["duplicate_unordered_pairs"] == 0 and overlap_mismatches == 0
        and feature_mismatches == 0 and relative_mismatches == 0 and not genealogy_mismatches
        and checks["observed_patterns"] == ["001", "010", "011", "100", "101", "110", "111"]
    )
    prediction_pass = all(
        x["leaking_group_count"] == x["leaking_language_count"] == 0
        and x["all_probabilities_finite_and_inside_unit_interval"]
        and x["predictions_match_all_variant_input_pairs"]
        and x["five_test_folds_present"]
        and x["saved_language_score_rows_matched"]
        for x in checks["condition_checks"]
    )
    numeric_pass = max(max_metric_error, max_loss_error, max_saved_score_error,
                       max_ci_error, rate_error) < TOLERANCE
    checks["passed"] = bool(
        structural_pass and prediction_pass and numeric_pass and mle_fold_error < 1e-4
        and mle_full_error < 1e-4 and checks["all_saved_fit_statuses_converged"]
        and checks["all_saved_fit_ranks_correct"] and script_matches
    )
    checks["verification_time_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    checks["verification_script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    checks["scope"] = (
        "原始主样本重建及已保存折外预测的独立数值核验；未重训模型，"
        "谱系簇区间保持固定预测与固定分折的条件解释。"
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(checks, ensure_ascii=False, indent=2, allow_nan=False),
                      encoding="utf-8")
    print(json.dumps({
        "passed": checks["passed"],
        "conditions": len(checks["condition_checks"]),
        "maximum_aggregate_metric_error": max_metric_error,
        "maximum_cluster_interval_error": max_ci_error,
        "output": str(OUTPUT),
    }, ensure_ascii=False, indent=2))
    if not checks["passed"]:
        raise SystemExit("独立核验存在差异，详见输出 JSON。")


if __name__ == "__main__":
    main()
