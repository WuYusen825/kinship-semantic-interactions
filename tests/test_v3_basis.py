"""T3纯理论与人工数据测试；不读取实际T1映射或任何新结果。"""
from fractions import Fraction
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

V3 = Path(__file__).resolve().parents[1] / "analysis/v3"
sys.path.insert(0, str(V3))
import basis_enrichment as basis
from partitions import enumerate_rgs, rgs_to_blocks
from languages import is_conjunctive, partition_dl


class CandidateTheoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.partitions = tuple(rgs_to_blocks(rgs) for rgs in enumerate_rgs())
        cls.specs, cls.acceptance = basis.build_acceptance(cls.partitions)

    def test_all_nontrivial_bipartitions_complement_deduplicated(self):
        candidates = basis.candidate_features()
        self.assertEqual(len(candidates), 127)
        self.assertEqual(len({r["mask"] for r in candidates}), 127)
        for row in candidates:
            mask = row["mask"]
            self.assertTrue(mask & 1)
            self.assertEqual(mask, basis.canonical_feature(255 ^ mask))
            self.assertEqual(sum(x << i for i, x in enumerate(row["values"])), mask)
        for bad in [0, 255, -1, 256, 1.5]:
            with self.assertRaises(ValueError):
                basis.canonical_feature(bad)

    def test_preserving_seven_and_swapping_eight_are_disjoint(self):
        specs = basis.candidate_features()
        preserving = {r["mask"] for r in specs if r["symmetry_class"] == "value_preserving"}
        swapping = {r["mask"] for r in specs if r["symmetry_class"] == "block_swapping"}
        self.assertEqual((len(preserving), len(swapping), len(preserving | swapping)), (7, 8, 15))
        self.assertFalse(preserving & swapping)
        for row in specs:
            if row["alias"] in ["q", "a"]:
                self.assertIn(row["mask"], preserving)
            if row["alias"] in ["s", "r"]:
                self.assertIn(row["mask"], swapping)
        p = basis.sex_swap_permutation()
        self.assertEqual(tuple(p[p[i]] for i in range(8)), tuple(range(8)))

    def test_exact_theory_counts_and_duplicate_raw_features(self):
        self.assertEqual(self.acceptance.shape, (4140, 128))
        self.assertEqual(int(self.acceptance[:, 0].sum()), 154)
        q_index = next(i for i, r in enumerate(self.specs) if r["alias"] == "q")
        self.assertEqual(int(self.acceptance[:, q_index].sum()), 260)
        np.testing.assert_array_equal(self.acceptance[:, q_index],
                                      [is_conjunctive(p, "all") for p in self.partitions])
        for name in ["s", "a", "r"]:
            index = next(i for i, r in enumerate(self.specs) if r["alias"] == name)
            np.testing.assert_array_equal(self.acceptance[:, index], self.acceptance[:, 0])

    def test_dynamic_extents_match_independent_common_literal_closure(self):
        base = [basis.FEATURES[x] for x in ["s", "a", "r"]]
        # 合取外延的独立判据：目标中共同为真的所有文字之交恰好等于目标。
        for row in basis.candidate_features():
            columns = base + [row["values"]]
            extents = basis.conjunctive_extents(columns)
            for target in range(1, 256):
                points = [i for i in range(8) if target & (1 << i)]
                closure = 255
                for column in columns:
                    values = {column[i] for i in points}
                    if len(values) == 1:
                        value = next(iter(values))
                        closure &= sum(1 << i for i in range(8) if column[i] == value)
                self.assertEqual(target in extents, closure == target, (row["mask"], target))
            complement = tuple(1 - x for x in row["values"])
            self.assertEqual(extents, basis.conjunctive_extents(base + [complement]))

    def test_q_category_requires_relational_feature(self):
        same = basis.feature_mask(basis.FEATURES["q"])
        partition = tuple(sorted((same, 255 ^ same)))
        index = self.partitions.index(partition)
        q_column = next(i for i, r in enumerate(self.specs) if r["alias"] == "q")
        self.assertFalse(self.acceptance[index, 0])
        self.assertTrue(self.acceptance[index, q_column])

    def test_information_isomorphism_does_not_imply_equal_primitive_cost(self):
        for columns in [("s", "a", "r"), ("q", "a", "r"), ("q", "a", "s")]:
            self.assertEqual(len({tuple(basis.FEATURES[name][i] for name in columns) for i in range(8)}), 8)
        r = basis.feature_mask(basis.FEATURES["r"])
        partition = (r, 255 ^ r)
        self.assertEqual([partition_dl(partition, language) for language in basis.LANGUAGE_ORDER], [2, 2, 8, 2])

    def test_invalid_partitions_and_feature_vectors_rejected(self):
        for invalid in [((1, 1, 254),), ((1, 2),), ((0, 255),), ((256, 255),)]:
            with self.assertRaises(ValueError):
                basis.build_acceptance(invalid)
        for invalid in [[0] * 7, [0] * 7 + [2]]:
            with self.assertRaises(ValueError):
                basis.feature_mask(invalid)


class SamplingAndCostsTests(unittest.TestCase):
    def test_whole_family_bootstrap_matches_explicit_cluster_draws(self):
        values = np.array([[1, 0], [0, 1], [0, 1]], dtype=float)
        groups = ["A", "B", "B"]
        result = basis.cluster_bootstrap_matrix(values, groups, 200, seed=13, batch_size=17)
        np.testing.assert_allclose(result["system_estimate"], [1 / 3, 2 / 3])
        np.testing.assert_allclose(result["family_estimate"], [.5, .5])
        draws = np.random.default_rng(13).integers(0, 2, (200, 2))
        means = np.array([[1, 0], [0, 1]])
        totals = np.array([[1, 0], [0, 2]])
        counts = np.array([1, 2])
        np.testing.assert_array_equal(result["family_draws"], means[draws].mean(axis=1))
        np.testing.assert_array_equal(result["system_draws"], totals[draws].sum(axis=1) / counts[draws].sum(axis=1)[:, None])
        other = basis.cluster_bootstrap_matrix(values, groups, 200, seed=13, batch_size=200)
        np.testing.assert_array_equal(result["system_draws"], other["system_draws"])

    def test_shape_reference_preserves_each_system_shape_and_is_not_bootstrap(self):
        # 第一种shape只有全成功支持点；第二种shape只有全失败支持点。
        acceptance = np.array([[1, 1], [0, 0]], dtype=bool)
        shapes = [(8,), (1, 7)]
        observed = [(8,), (1, 7), (1, 7)]
        reference = basis.shape_reference(acceptance, shapes, observed, ["A", "B", "B"], 50, seed=2)
        np.testing.assert_allclose(reference["expected_system"], [1 / 3, 1 / 3])
        np.testing.assert_allclose(reference["expected_family"], [.5, .5])
        np.testing.assert_array_equal(reference["count_pi95"], [[1, 1], [1, 1]])
        np.testing.assert_array_equal(reference["family_pi95"], [[.5, .5], [.5, .5]])
        observed_boot = basis.cluster_bootstrap_matrix([[1], [0], [0]], ["A", "B", "B"], 50, seed=2)
        self.assertGreater(np.ptp(observed_boot["system_draws"]), 0)

    def test_shape_streams_are_batch_invariant_and_exact_probabilities_are_uniform(self):
        acceptance = np.array([[1, 0], [0, 1], [1, 1], [1, 0]], dtype=bool)
        shapes = [(4, 4), (4, 4), (2, 6), (2, 6)]
        observed = [(4, 4), (2, 6), (4, 4)]
        a = basis.shape_reference(acceptance, shapes, observed, ["A", "B", "B"], 101, seed=7, batch_size=13)
        b = basis.shape_reference(acceptance, shapes, observed, ["A", "B", "B"], 101, seed=7, batch_size=101)
        np.testing.assert_array_equal(a["count_draws"], b["count_draws"])
        np.testing.assert_array_equal(a["family_draws"], b["family_draws"])
        np.testing.assert_allclose(a["per_system_probabilities"], [[.5, .5], [1, .5], [.5, .5]])

    def test_exact_tied_ranks_do_not_select_favorable_tie_break(self):
        values = [Fraction(2, 3), Fraction(4, 6), Fraction(1, 2), Fraction(3, 4)]
        self.assertEqual(basis.tied_ranks(values), [2, 2, 4, 1])
        self.assertEqual(basis.tied_ranks(values, descending=False), [2, 2, 1, 4])

    def test_feature_summary_has_both_weights_all_ranks_and_abs_outside_candidate_ranks(self):
        specs = [{"feature_id": "abs", "mask": None, "alias": "abs", "symmetry_class": "not_applicable"},
                 {"feature_id": "f_001", "mask": 1, "alias": "", "symmetry_class": "not_stable"}]
        accepted = np.array([[1, 1], [0, 1]])
        rows, boot, reference = basis.summarize_features(specs, accepted, [0, 1, 1], ["A", "B", "B"],
                                                       [(8,), (1, 7)], 30, seed=8)
        self.assertEqual(rows[0]["E_system_exact"], "2/3")
        self.assertEqual(rows[0]["E_family_exact"], "1")
        self.assertNotIn("rank_E_system_candidates", rows[0])
        self.assertEqual(rows[1]["rank_E_system_candidates"], 1)
        self.assertEqual(rows[0]["rank_E_family_with_abs"], 1)
        self.assertEqual(rows[1]["rank_E_family_with_abs"], 1)
        self.assertEqual(rows[0]["ties_E_family_with_abs"], 2)

    def test_paired_costs_inventory_threshold_and_four_languages(self):
        values = np.array([[2, 3, 4, 1], [4, 5, 6, 3], [2, 3, 4, 1]])
        result = basis.description_cost_comparison(values, ["A", "B", "B"], replicates=80, seed=9)
        self.assertEqual(len(result["rows"]), 32)
        self.assertEqual(len(result["pairwise"]), 48)
        self.assertEqual(len(result["crossings"]), 12)
        for weight in ["system", "family"]:
            point = next(r for r in result["pairwise"] if r["weighting"] == weight and r["lambda"] == 1
                         and r["left"] == "abs" and r["right"] == "all")
            self.assertEqual(point["difference_left_minus_right"], 0)
            np.testing.assert_allclose([point["ci95_low"], point["ci95_high"]], [0, 0], atol=1e-12)
            crossing = next(r for r in result["crossings"] if r["weighting"] == weight
                            and r["left"] == "abs" and r["right"] == "all")
            self.assertEqual(crossing["lambda_crossing_exact"], "1")
            self.assertFalse(result["ordering_stable_on_grid"][weight])

    def test_invalid_sampling_inputs_rejected(self):
        for groups in [["A", None], ["A", ""], ["A", float("nan")]]:
            with self.assertRaises(ValueError):
                basis.cluster_bootstrap_matrix([1, 0], groups, 10)
        with self.assertRaises(ValueError):
            basis.cluster_bootstrap_matrix([1, float("nan")], ["A", "B"], 10)
        with self.assertRaises(ValueError):
            basis.shape_reference([[1]], [(8,)], [(4, 4)], ["A"], 10)

    def test_cli_execution_gate_precedes_result_reads_and_output_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "uncreated"
            with patch.object(basis, "verify_analysis_plan", side_effect=RuntimeError("T1未通过")), \
                    patch.object(basis, "load_partition_table") as loader:
                with self.assertRaisesRegex(RuntimeError, "T1未通过"):
                    basis.main(["--output", str(output)])
                loader.assert_not_called()
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
