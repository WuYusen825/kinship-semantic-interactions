"""T5合成核验：不读取实测结果，不以内部估计实现作为标准答案。"""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from scipy.special import expit, logit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis/v3"))
import common
from design_rank import abstract_rows
from pair_models import (aggregate_training, cluster_sandwich, comparison_rows, evaluate_cv,
                         fold_splits, recalibrate_intercept, row_weights,
                         vb_convergence, weighted_auc, weighted_score)


def synthetic_frame():
    atoms = sorted(abstract_rows(), key=lambda row: row["category_a"] + "|" + row["category_b"])
    families = ["g0", "g0", "g1", "g2", "g3", "g4"]
    family_folds = [0, 0, 1, 2, 3, 4]
    records = []
    for language in range(6):
        for index, atom in enumerate(atoms):
            records.append({"Language_ID": "L" + str(language), "Glottocode": "code" + str(language),
                            "family_group": families[language], "family_name": families[language],
                            "fold_family": family_folds[language], "fold_language": language % 5,
                            "macroarea": "" if language == 5 else "A" if language % 2 == 0 else "B",
                            "category_a": atom["category_a"], "category_b": atom["category_b"],
                            "pair_index": index,
                            "pattern": "".join(str(atom[name]) for name in ("Dr", "Da", "De")),
                            "shared_form": (language + index) % 2})
    return pd.DataFrame(records), [r["category_a"] + "|" + r["category_b"] for r in atoms]


class PairWeightAndCVTests(unittest.TestCase):
    def test_training_mass_and_family_language_targets(self):
        frame, _ = synthetic_frame()
        wf, wl = row_weights(frame, "family"), row_weights(frame, "language")
        self.assertAlmostEqual(wf.sum(), 6)
        self.assertAlmostEqual(wl.sum(), 6)
        mass = pd.Series(wf).groupby(frame.family_group).sum()
        self.assertTrue(np.allclose(mass, 6 / 5))
        self.assertTrue(np.allclose(pd.Series(wl).groupby(frame.Language_ID).sum(), 1))

    def test_score_target_is_not_average_of_fold_means(self):
        scores = pd.DataFrame({"family_group": ["a", "a", "a", "b"], "loss": [0, 0, 0, 1]})
        self.assertEqual(weighted_score(scores, "loss", "family"), .5)
        self.assertEqual(weighted_score(scores, "loss", "language"), .25)

    def test_fixed_folds_and_area_complete_cases(self):
        frame, _ = synthetic_frame()
        for mode, group in [("family", "family_group"), ("language", "Language_ID"), ("area", "macroarea")]:
            data, splits = fold_splits(frame, mode)
            self.assertEqual(len(data), (5 if mode == "area" else 6) * 28)
            for _, train, test in splits:
                self.assertFalse(set(data.iloc[train][group]) & set(data.iloc[test][group]))
            self.assertEqual(sorted(np.concatenate([te for _, _, te in splits])), list(range(len(data))))

    def test_failed_model_does_not_remove_test_systems(self):
        frame, pair_types = synthetic_frame()
        def fake(train, X, estimator, weighting, model):
            return np.zeros(X.shape[1]), {"converged": model != "M4", "method": "MLE"}
        with patch("pair_models.fit_model", side_effect=fake):
            predictions, scores, logs, _ = evaluate_cv(frame, pair_types)
        self.assertEqual(len(predictions), len(frame))
        self.assertEqual(len(scores), 6)
        self.assertTrue(scores.loss_M4.isna().all())
        self.assertTrue(np.allclose(scores.loss_M0, np.log(2)))
        comparisons = comparison_rows(scores, "family", {})
        self.assertTrue(comparisons[0]["available"])
        self.assertFalse(comparisons[1]["available"])
        self.assertEqual(len(comparisons[1]["failed_system_ids"]), 6)
        self.assertEqual(sum(not item["converged"] for item in logs), 5)

    def test_aggregation_retains_weighted_target_and_gradient(self):
        frame, _ = synthetic_frame()
        w = row_weights(frame)
        success, total = aggregate_training(frame, w)
        X = np.c_[np.ones(28), np.linspace(-1, 1, 28)]
        beta = np.array([.2, -.3])
        indices = frame.pair_index.to_numpy()
        p = expit(X @ beta)
        raw_gradient = X[indices].T @ (w * (frame.shared_form.to_numpy() - p[indices]))
        cell_gradient = X.T @ (success - total * p)
        self.assertTrue(np.allclose(raw_gradient, cell_gradient, rtol=0, atol=1e-12))
        self.assertAlmostEqual(total.sum(), 6)


class CalibrationTests(unittest.TestCase):
    def test_constant_probability_has_known_calibration_offset(self):
        y, p = np.array([0, 0, 1, 1]), np.full(4, .2)
        result = recalibrate_intercept(y, p, np.ones(4))
        self.assertAlmostEqual(result["offset"], np.log(4), places=10)
        self.assertTrue(np.allclose(result["calibrated_probability"], .5))
        self.assertTrue(result["used_test_outcomes"])

    def test_weighted_offset_matches_test_prevalence_and_preserves_auc(self):
        y = np.array([0, 1, 0, 1])
        p = np.array([.1, .8, .8, .4])
        w = np.array([1., 2., 3., 4.])
        result = recalibrate_intercept(y, p, w)
        self.assertAlmostEqual(float(w @ result["calibrated_probability"] / w.sum()), float(w @ y / w.sum()), places=11)
        self.assertAlmostEqual(weighted_auc(y, p, w), 9 / 24)
        self.assertAlmostEqual(weighted_auc(y, p, w), weighted_auc(y, result["calibrated_probability"], w))

    def test_single_outcome_has_no_auc_or_fake_finite_offset(self):
        result = recalibrate_intercept(np.ones(3), np.full(3, .2), np.ones(3))
        self.assertIsNone(result["offset"])
        self.assertEqual(result["status"], "boundary_outcome")
        self.assertTrue(np.all(result["calibrated_probability"] == 1))
        self.assertIsNone(weighted_auc(np.ones(3), np.full(3, .2), np.ones(3)))


class DependenceTests(unittest.TestCase):
    def test_intercept_cluster_covariance_has_analytic_answer(self):
        X = np.ones((8, 1))
        y = np.array([0, 0, 0, 0, 1, 1, 1, 1])
        groups = np.repeat(["a", "b", "c", "d"], 2)
        result = cluster_sandwich(X, y, np.full(8, .5), np.ones(8), groups, correction=False)
        self.assertAlmostEqual(result["covariance"][0, 0], 1)
        corrected = cluster_sandwich(X, y, np.full(8, .5), np.ones(8), groups)
        self.assertAlmostEqual(corrected["covariance"][0, 0], 4 / 3)

    def test_cluster_covariance_is_invariant_to_global_weight_scale(self):
        X = np.c_[np.ones(12), np.linspace(-1, 1, 12)]
        y = np.tile([0, 1, 0], 4)
        p = expit(X @ np.array([.2, -.3]))
        groups = np.repeat(np.arange(4), 3)
        first = cluster_sandwich(X, y, p, np.ones(12), groups)
        second = cluster_sandwich(X, y, p, np.full(12, .007), groups)
        self.assertTrue(np.allclose(first["covariance"], second["covariance"], rtol=1e-12, atol=1e-12))

    def test_vb_gate_never_upgrades_precision_loss(self):
        self.assertFalse(vb_convergence(False, np.array([1e-10]), np.array([0.]), np.array([1.])))
        self.assertFalse(vb_convergence(True, np.array([1.1e-6]), np.array([0.]), np.array([1.])))
        self.assertFalse(vb_convergence(True, np.array([0.]), np.array([np.nan]), np.array([1.])))
        self.assertTrue(vb_convergence(True, np.array([1e-7]), np.array([0.]), np.array([1.])))


if __name__ == "__main__":
    unittest.main()
