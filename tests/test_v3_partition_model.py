"""Synthetic and mathematical checks; no observed data or fitted outputs are read."""
from __future__ import annotations

from itertools import combinations
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis" / "v3"))
import partition_model as pm


class FeatureSpaceTests(unittest.TestCase):
    def test_constants_drop_and_standardization_uses_full_support(self):
        space = pm.FeatureSpace.from_raw(
            np.array([[1., 7., 10.], [3., 7., 20.], [5., 7., 30.]]),
            ("age", "inventory_constant", "sex"),
        )
        self.assertEqual(space.active_names, ("age", "sex"))
        self.assertEqual(space.dropped_names, ("inventory_constant",))
        np.testing.assert_allclose(space.mean, [3., 20.], atol=1e-14)
        np.testing.assert_allclose(space.scale, [np.sqrt(8 / 3), np.sqrt(200 / 3)])
        np.testing.assert_allclose(space.matrix.mean(axis=0), 0., atol=1e-14)
        np.testing.assert_allclose(space.matrix.std(axis=0), 1., atol=1e-14)

    def test_duplicate_patterns_retain_support_multiplicity(self):
        space = pm.FeatureSpace.from_raw(np.array([[0.], [0.], [0.], [1.]]), ("x",))
        self.assertEqual(space.matrix.shape, (4, 1))
        self.assertEqual(space.unique_matrix.shape, (2, 1))
        np.testing.assert_array_equal(sorted(space.multiplicities), [1., 3.])
        np.testing.assert_allclose(
            space.unique_matrix[space.pattern_index], space.matrix, atol=0., rtol=0.
        )

    def test_zero_dimensional_support_has_one_pattern_with_full_multiplicity(self):
        space = pm.FeatureSpace.from_raw(np.empty((4140, 0)), ())
        self.assertEqual(space.matrix.shape, (4140, 0))
        self.assertEqual(space.unique_matrix.shape, (1, 0))
        np.testing.assert_array_equal(space.multiplicities, [4140.])


class ObjectiveTests(unittest.TestCase):
    def setUp(self):
        self.space = pm.FeatureSpace.from_raw(
            np.array([[-2., 0.], [0., 1.], [0., 1.], [2., 0.], [2., 0.], [2., 0.]]),
            ("x", "y"),
        )

    def test_log_normalizer_counts_every_support_point(self):
        theta = np.array([.4, -.7])
        target = np.array([.1, -.2])
        value, gradient = pm.objective_gradient(theta, self.space, target, .3)
        # Direct summation over the original six support rows is the oracle.
        masses = np.exp(self.space.matrix @ theta)
        expected = np.log(sum(masses)) - theta @ target + .15 * (theta @ theta)
        self.assertAlmostEqual(value, expected, places=13)
        expected_gradient = sum(
            mass * row for mass, row in zip(masses, self.space.matrix)
        ) / sum(masses) - target + .3 * theta
        np.testing.assert_allclose(gradient, expected_gradient, atol=1e-13, rtol=0.)

    def test_exact_gradient_agrees_with_central_finite_difference(self):
        theta = np.array([.25, -.45])
        target = np.array([.1, .2])
        _, analytic = pm.objective_gradient(theta, self.space, target, .7)
        numerical = np.empty(2)
        for j in range(2):
            step = np.zeros(2)
            step[j] = 1e-6
            plus = pm.objective_gradient(theta + step, self.space, target, .7)[0]
            minus = pm.objective_gradient(theta - step, self.space, target, .7)[0]
            numerical[j] = (plus - minus) / 2e-6
        np.testing.assert_allclose(analytic, numerical, atol=2e-9, rtol=0.)

    def test_l2_penalty_has_declared_objective_and_gradient_scale(self):
        theta = np.array([.4, -.6])
        target = np.array([.2, .1])
        value0, gradient0 = pm.objective_gradient(theta, self.space, target, 0.)
        value1, gradient1 = pm.objective_gradient(theta, self.space, target, .8)
        self.assertAlmostEqual(value1 - value0, .4 * (theta @ theta), places=13)
        np.testing.assert_allclose(gradient1 - gradient0, .8 * theta, atol=1e-14)


class FiniteMleTests(unittest.TestCase):
    def setUp(self):
        # A square has edge-interior boundary points that are not vertices.
        self.space = pm.FeatureSpace.from_raw(
            np.array([[0., 0.], [0., 1.], [1., 0.], [1., 1.]]), ("x", "y")
        )

    def test_relative_interior_has_positive_common_pattern_mass(self):
        check = pm.finite_mle_check(self.space, np.zeros(2))
        self.assertTrue(check["lp_success"])
        self.assertTrue(check["finite_mle"])
        self.assertAlmostEqual(check["minimum_pattern_weight"], .25, places=10)

    def test_nonvertex_face_has_no_finite_mle(self):
        target = self.space.matrix[[0, 1]].mean(axis=0)
        check = pm.finite_mle_check(self.space, target)
        self.assertTrue(check["lp_success"])
        self.assertFalse(check["finite_mle"])
        self.assertAlmostEqual(check["minimum_pattern_weight"], 0., places=10)

    def test_affine_redundancy_uses_relative_interior(self):
        space = pm.FeatureSpace.from_raw(np.array([[0., 0.], [1., 2.], [2., 4.]]), ("x", "twice_x"))
        check = pm.finite_mle_check(space, np.zeros(2))
        self.assertTrue(check["lp_success"])
        self.assertTrue(check["finite_mle"])
        self.assertAlmostEqual(check["minimum_pattern_weight"], 1 / 3, places=10)


class FitTests(unittest.TestCase):
    def assert_distribution(self, fit):
        self.assertTrue(fit.converged, fit.diagnostics)
        self.assertTrue(np.isfinite(fit.theta).all())
        self.assertTrue(np.isfinite(fit.log_probabilities).all())
        self.assertTrue(np.isfinite(fit.probabilities).all())
        self.assertLess(abs(sum(fit.probabilities) - 1.), 1e-9)
        self.assertLess(fit.normalization_error, 1e-9)
        self.assertLessEqual(fit.gradient_max, 1e-6)
        np.testing.assert_allclose(np.exp(fit.log_probabilities), fit.probabilities, atol=1e-14)

    def assert_unusable_failure(self, fit, status):
        self.assertFalse(fit.converged)
        self.assertEqual(fit.diagnostics["status"], status)
        self.assertTrue(np.isnan(fit.theta).all())
        self.assertTrue(np.isnan(fit.probabilities).all())
        self.assertTrue(np.isnan(fit.log_probabilities).all())

    def test_a0_is_analytic_uniform_over_all_4140_support_points(self):
        space = pm.FeatureSpace.from_raw(np.empty((4140, 0)), ())
        fit = pm.fit_maxent(space, np.array([0, 2, 4139]), alpha=0.)
        self.assert_distribution(fit)
        self.assertEqual(fit.theta.shape, (0,))
        self.assertEqual(fit.raw_coefficients, {})
        np.testing.assert_allclose(fit.probabilities, 1 / 4140, atol=1e-18, rtol=0.)
        self.assertAlmostEqual(fit.objective, np.log(4140), places=12)

    def test_binary_interior_mle_matches_hand_calculation(self):
        space = pm.FeatureSpace.from_raw(np.array([[0.], [1.]]), ("x",))
        fit = pm.fit_maxent(space, np.array([0, 1]), weights=np.array([.25, .75]), alpha=0.)
        self.assert_distribution(fit)
        np.testing.assert_allclose(fit.probabilities, [.25, .75], atol=1e-7, rtol=0.)
        self.assertAlmostEqual(fit.raw_coefficients["x"], np.log(3), places=6)
        self.assertAlmostEqual(fit.theta[0], np.log(3) / 2, places=6)

    def test_duplicate_feature_patterns_split_mass_per_partition(self):
        space = pm.FeatureSpace.from_raw(np.array([[0.], [0.], [0.], [1.]]), ("x",))
        fit = pm.fit_maxent(space, np.array([0, 3]), weights=np.array([.6, .4]), alpha=0.)
        self.assert_distribution(fit)
        np.testing.assert_allclose(fit.probabilities, [.2, .2, .2, .4], atol=1e-7, rtol=0.)

    def test_unregularized_boundary_is_not_returned_as_a_predictive_fit(self):
        space = pm.FeatureSpace.from_raw(np.array([[0.], [1.]]), ("x",))
        fit = pm.fit_maxent(space, np.array([1, 1]), alpha=0.)
        self.assert_unusable_failure(fit, "nonfinite_mle_boundary")
        self.assertFalse(fit.diagnostics["finite_mle"]["finite_mle"])

    def test_positive_penalty_gives_finite_boundary_fit(self):
        space = pm.FeatureSpace.from_raw(np.array([[0.], [1.]]), ("x",))
        fit = pm.fit_maxent(space, np.array([1, 1]), alpha=.5)
        self.assert_distribution(fit)
        self.assertGreater(fit.probabilities[1], .5)
        self.assertLess(fit.probabilities[1], 1.)
        # Standardized x is -1,+1: penalized first-order condition is explicit.
        self.assertAlmostEqual(2 * fit.probabilities[1] - 2 + .5 * fit.theta[0], 0., places=6)

    def test_inventory_constant_and_feature_units_cancel_from_normalization(self):
        ids = np.array([0, 1, 2])
        weights = np.array([.2, .3, .5])
        original = pm.FeatureSpace.from_raw(np.array([[0.], [1.], [2.]]), ("x",))
        shifted = pm.FeatureSpace.from_raw(
            np.array([[100., 7.], [110., 7.], [120., 7.]]), ("x", "inventory_constant")
        )
        fit0 = pm.fit_maxent(original, ids, weights, alpha=.3)
        fit1 = pm.fit_maxent(shifted, ids, weights, alpha=.3)
        self.assert_distribution(fit0)
        self.assert_distribution(fit1)
        np.testing.assert_allclose(fit0.probabilities, fit1.probabilities, atol=1e-10, rtol=0.)
        self.assertNotIn("inventory_constant", fit1.raw_coefficients)
        self.assertAlmostEqual(fit0.raw_coefficients["x"], 10 * fit1.raw_coefficients["x"], places=8)

    def test_normalized_l2_fit_is_invariant_to_replication_and_weight_scale(self):
        space = pm.FeatureSpace.from_raw(np.array([[0.], [1.], [2.]]), ("x",))
        ids = np.array([0, 1, 2])
        weights = np.array([.2, .3, .5])
        original = pm.fit_maxent(space, ids, weights, alpha=.4)
        replicated = pm.fit_maxent(space, np.tile(ids, 7), np.tile(weights, 7), alpha=.4)
        scaled = pm.fit_maxent(space, ids, 23 * weights, alpha=.4)
        for fit in (original, replicated, scaled):
            self.assert_distribution(fit)
        np.testing.assert_allclose(original.theta, replicated.theta, atol=1e-10, rtol=0.)
        np.testing.assert_allclose(original.theta, scaled.theta, atol=1e-10, rtol=0.)
        self.assertAlmostEqual(original.objective, replicated.objective, places=12)

    def test_solver_failure_even_at_zero_gradient_prohibits_prediction(self):
        space = pm.FeatureSpace.from_raw(np.array([[0.], [1.]]), ("x",))
        failure = SimpleNamespace(x=np.zeros(1), success=False, status=1, message="synthetic failure", nit=0)
        with patch.object(pm, "minimize", return_value=failure) as solver:
            fit = pm.fit_maxent(space, np.array([0, 1]), alpha=.2, maxiter=1, retry_maxiter=2)
        self.assert_unusable_failure(fit, "optimizer_failed")
        self.assertEqual(solver.call_count, 2)
        self.assertEqual(len(fit.diagnostics["attempts"]), 2)
        for call in solver.call_args_list:
            np.testing.assert_array_equal(call.args[1], np.zeros(1))

    def test_solver_success_with_wrong_gradient_prohibits_prediction(self):
        space = pm.FeatureSpace.from_raw(np.array([[0.], [1.]]), ("x",))
        false_success = SimpleNamespace(x=np.zeros(1), success=True, status=0, message="synthetic stop", nit=0)
        with patch.object(pm, "minimize", return_value=false_success):
            fit = pm.fit_maxent(space, np.array([1]), alpha=.2, maxiter=1, retry_maxiter=2)
        self.assert_unusable_failure(fit, "optimizer_failed")


class MarginalAndContrastTests(unittest.TestCase):
    def test_pair_marginals_match_three_atom_partition_semantics(self):
        labels = ((0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 2))
        pairs = tuple(combinations(range(3), 2))
        same_block = np.array([[row[i] == row[j] for i, j in pairs] for row in labels])
        actual = pm.pair_probabilities(np.array([.1, .2, .3, .4]), same_block)
        # P(0~1)=.1+.2, P(0~2)=.1, P(1~2)=.1+.3.
        np.testing.assert_allclose(actual, [.3, .1, .4], atol=1e-15, rtol=0.)

    def test_failed_or_unnormalized_distribution_cannot_produce_marginals(self):
        same_block = np.array([[1, 0], [0, 1]])
        for bad in (np.array([np.nan, np.nan]), np.array([.2, .2]), np.array([-.1, 1.1])):
            with self.subTest(probabilities=bad):
                with self.assertRaises(ValueError):
                    pm.pair_probabilities(bad, same_block)

    def test_difference_cells_average_pairs_within_cell(self):
        result = pm.seven_cell_rates(np.array([.1, .3, .8, .6]), ("001", "001", "110", "110"))
        self.assertEqual(set(result), {"001", "110"})
        self.assertAlmostEqual(result["001"], .2)
        self.assertAlmostEqual(result["110"], .7)

    def test_seven_cell_logit_projection_recovers_known_interactions(self):
        cells = np.array([(s, r, a) for s in (0, 1) for r in (0, 1) for a in (0, 1) if s or r or a])
        design = np.array([[1., s, r, a, s*r, s*a, r*a] for s, r, a in cells])
        names = ("Intercept", "Ds", "Dr", "Da", "DsDr", "DsDa", "DrDa")
        beta = np.array([-.4, .3, -.2, .1, .15, -.25, .35])
        rates = 1 / (1 + np.exp(-(design @ beta)))
        result = pm.m2_logit_contrasts(rates, design, names)
        np.testing.assert_allclose([result["coefficients"][name] for name in names], beta, atol=1e-12, rtol=0.)
        self.assertLess(result["max_abs_residual"], 1e-12)


class NestedSelectionTests(unittest.TestCase):
    """Control OOF scores synthetically without fitting or reading observations."""

    @staticmethod
    def selection_hub(scores):
        import pandas as pd
        import run_t2 as runner

        systems = pd.DataFrame({
            "Language_ID": ["synthetic_a", "synthetic_b", "synthetic_c"],
            "family_group": ["family_a", "family_b", "family_c"],
            "partition_id": [0, 0, 0],
        })
        spaces = {name: SimpleNamespace(dimension=len(columns))
                  for name, columns in runner.FEATURES.items()}
        spaces.update({"A7@" + name: SimpleNamespace(dimension=len(runner.FEATURES[name]) + 3)
                       for name in runner.DESCRIPTIVE})
        calls = []

        def fit(model, indices, alpha, split_id):
            calls.append((model, alpha, tuple(indices), split_id))
            value = scores.get((model, alpha), -20.)
            return SimpleNamespace(converged=True, log_probabilities=np.array([value]))

        return SimpleNamespace(systems=systems, spaces=spaces, weighting="family", fit=fit), calls

    def test_base_tie_tolerance_is_applied_once_across_all_candidates(self):
        import run_t2 as runner

        # Per-model tolerance followed by another tolerance would incorrectly
        # select A2/1, which is 1.8e-10 below the global maximum.  The declared
        # one-shot tie set instead includes A3r/1 but excludes A2/1.
        scores = {("A2", 0.): -1. - .9e-10,
                  ("A2", 1.): -1. - 1.8e-10,
                  ("A3r", 0.): -1.,
                  ("A3r", 1.): -1. - .9e-10}
        hub, _ = self.selection_hub(scores)
        choices, base, _, rows, _ = runner.select_models(hub, np.arange(3), "synthetic")
        self.assertEqual((choices["A2"]["space"], choices["A2"]["alpha"]), ("A2", 1.))
        self.assertEqual((base["space"], base["alpha"]), ("A3r", 1.))
        global_maximum = max(row["score"] for row in rows if row["model"] in runner.DESCRIPTIVE)
        self.assertLessEqual(global_maximum - base["score"], 1e-10)

    def test_position_scores_cannot_reselect_descriptive_base(self):
        import run_t2 as runner

        # A3r with positions would dominate, but its inferior descriptive score
        # must exclude it before any A7 alpha is tuned.
        scores = {("A2", 0.): -1., ("A3r", 0.): -2.,
                  ("A7@A2", .1): -.75,
                  **{("A7@A3r", alpha): -.1 for alpha in runner.ALPHAS}}
        hub, calls = self.selection_hub(scores)
        _, base, a7, _, _ = runner.select_models(hub, np.arange(3), "synthetic")
        self.assertEqual((base["space"], base["alpha"]), ("A2", 0.))
        self.assertEqual((a7["space"], a7["alpha"]), ("A7@A2", .1))
        position_spaces = {model for model, _, _, _ in calls if model.startswith("A7@")}
        self.assertEqual(position_spaces, {"A7@A2"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
