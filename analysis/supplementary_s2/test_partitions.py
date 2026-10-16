"""纯理论结构测试；无CSV、共享预测或实测结果读取。"""
from collections import Counter
from pathlib import Path
import unittest

from structural_enumeration import (
    ATOMS, BASIS_RAW, BASIS_RELATIVE, FEATURES, FEATURES_FOUR, FEATURES_SIX,
    KINTYPES, PAPER_TABLE, UNIVERSE, basis_score, block_shape,
    canonical_partition, conjunction_witnesses, endpoint_design_report,
    enumerate_partitions, evaluate_partition, is_conjunctive, is_partition_tree,
    known_examples, labels_to_partition, partition_to_labels,
    prediction_directions, select_bases, shape_universe_count, tree_partitions,
    partition_from_groups, secondary_structure_witness, strict_prediction_directions,
    feature_tree_depth_options,
)


class PartitionEnumerationTests(unittest.TestCase):
    def test_bell_and_stirling_counts_independent_recurrence(self):
        partitions = enumerate_partitions()
        self.assertEqual(len(partitions), 4140)
        self.assertEqual(len(set(partitions)), 4140)
        stirling = [[0] * 9 for _ in range(9)]
        stirling[0][0] = 1
        for n in range(1, 9):
            for k in range(1, n + 1):
                stirling[n][k] = stirling[n - 1][k - 1] + k * stirling[n - 1][k]
        self.assertEqual(Counter(map(len, partitions)), {k: stirling[8][k] for k in range(1, 9)})

    def test_every_partition_covers_once(self):
        for partition in enumerate_partitions():
            self.assertEqual(canonical_partition(partition), partition)
            self.assertEqual(labels_to_partition(partition_to_labels(partition)), partition)

    def test_each_block_size_null_count_matches_factorial_formula(self):
        observed = Counter(map(block_shape, enumerate_partitions()))
        for shape, count in observed.items():
            self.assertEqual(count, shape_universe_count(shape), shape)

    def test_conjunctive_counts(self):
        for features, expected in ((BASIS_RAW, 154), (FEATURES_FOUR, 260), (FEATURES_SIX, 518)):
            actual = sum(is_conjunctive(p, features) for p in enumerate_partitions())
            self.assertEqual(actual, expected)

    def test_sex_of_elder_younger_respects_reciprocal_reversal(self):
        for index, (s, a, r) in enumerate(ATOMS):
            reciprocal = ATOMS.index((r, 1 - a, s))
            for name in ("elder_sex", "younger_sex"):
                self.assertEqual(FEATURES[name][index], FEATURES[name][reciprocal])
            self.assertEqual(FEATURES["elder_sex"][index], r if a == 0 else s)
            self.assertEqual(FEATURES["younger_sex"][index], s if a == 0 else r)

    def test_table1_differences_are_retained_not_fitted_away(self):
        four = Counter(block_shape(p) for p in enumerate_partitions() if is_conjunctive(p))
        six = Counter(block_shape(p) for p in enumerate_partitions() if is_conjunctive(p, FEATURES_SIX))
        self.assertEqual(four[(1, 1, 2, 4)], 36)
        self.assertEqual(PAPER_TABLE[(1, 1, 2, 4)][1], 32)
        self.assertEqual(four[(1, 1, 2, 2, 2)], 88)
        self.assertEqual(PAPER_TABLE[(1, 1, 2, 2, 2)][1], 68)
        self.assertEqual(six[(2, 3, 3)], 12)
        self.assertEqual(six[(1, 1, 1, 2, 3)], 56)
        self.assertEqual(PAPER_TABLE[(1, 1, 1, 2, 3)][0], 64)

    def test_stronger_partition_tree_is_proper_subset(self):
        for features, expected in ((BASIS_RAW, 146), (FEATURES_FOUR, 236), (FEATURES_SIX, 434)):
            trees = tree_partitions(features)
            self.assertEqual(len(trees), expected)
            self.assertTrue(all(is_conjunctive(partition, features) for partition in trees))
        # 总数236的相等不是分格重现：原表四词48、五词76。
        by_terms = Counter(map(len, tree_partitions(FEATURES_FOUR)))
        self.assertEqual((by_terms[4], by_terms[5]), (52, 72))
        non_tree = [p for p in enumerate_partitions() if is_conjunctive(p) and not is_partition_tree(p)]
        self.assertEqual(len(non_tree), 24)

    def test_equal_split_tree_differs_only_for_six_features(self):
        self.assertEqual(len(tree_partitions(FEATURES_FOUR, True)), 236)
        self.assertEqual(len(tree_partitions(FEATURES_SIX, True)), 318)


class KnownExamplesTests(unittest.TestCase):
    def setUp(self):
        self.examples = known_examples()

    def test_english_and_age_sex_cross(self):
        english = self.examples["english_referent_sex"]
        crossed = self.examples["age_by_referent_sex"]
        self.assertTrue(is_conjunctive(labels_to_partition(english)))
        self.assertTrue(is_conjunctive(labels_to_partition(crossed)))
        self.assertEqual(evaluate_partition(english, BASIS_RAW)["features"]["r"]["separated_count"], 4)
        self.assertEqual(basis_score(english, BASIS_RAW), 2)
        self.assertEqual(basis_score(crossed, BASIS_RAW), 6)

    def test_relative_sex_is_basis_dependent(self):
        labels = self.examples["relative_sex_only"]
        self.assertFalse(is_conjunctive(labels_to_partition(labels), BASIS_RAW))
        self.assertTrue(is_conjunctive(labels_to_partition(labels), BASIS_RELATIVE))
        self.assertEqual(basis_score(labels, BASIS_RAW), 6)
        self.assertEqual(basis_score(labels, BASIS_RELATIVE), 2)
        raw = evaluate_partition(labels, BASIS_RAW)
        relative = evaluate_partition(labels, BASIS_RELATIVE)
        self.assertEqual(raw["features"]["s"]["separated_count"], 4)
        self.assertEqual(relative["features"]["s"]["separated_count"], 0)

    def test_p2_p3_p4_directional_examples(self):
        for name, prediction in (("sex_split_only_elder", "P2"), ("age_split_only_male", "P3"), ("age_split_only_same_sex", "P4")):
            self.assertEqual(prediction_directions(self.examples[name])[prediction], "predicted_side")
            self.assertEqual(strict_prediction_directions(self.examples[name])[prediction], "predicted_side")

    def test_parent_four_edges_does_not_validate_target_subroot(self):
        labels = self.examples["older_q_younger_merged"]
        diagnosis = secondary_structure_witness(labels, "a", "r", BASIS_RAW)
        self.assertTrue(diagnosis["parent_full_edge_coverage"])
        self.assertTrue(diagnosis["root_compatible"])
        self.assertEqual(diagnosis["parent_filtered_edge_direction"], "predicted_side")
        self.assertFalse(diagnosis["candidates"]["0"]["target_branch_compatible"])
        self.assertEqual(diagnosis["strict_direction"], "not_applicable")

    def test_parent_four_edges_does_not_validate_parent_root(self):
        partition = partition_from_groups((("mofe",), ("momy", "mofy"), ("fome",), ("fofe",), ("mome", "fomy", "fofy")))
        diagnosis = secondary_structure_witness(partition_to_labels(partition), "a", "r", BASIS_RAW)
        self.assertTrue(diagnosis["parent_full_edge_coverage"])
        self.assertFalse(diagnosis["root_compatible"])
        self.assertEqual(diagnosis["strict_direction"], "not_applicable")

    def test_unfiltered_side_is_not_a_primary_secondary_hierarchy(self):
        diagnosis = secondary_structure_witness(self.examples["older_female_versus_rest"], "a", "r", BASIS_RAW)
        self.assertEqual(diagnosis["unfiltered_edge_direction"], "predicted_side")
        self.assertFalse(diagnosis["parent_full_edge_coverage"])
        self.assertFalse(diagnosis["root_compatible"])
        self.assertEqual(diagnosis["strict_direction"], "not_applicable")

    def test_faris_surface_and_semantic_reanalysis_must_differ(self):
        surface = labels_to_partition(self.examples["faris_surface_1_1_3_3"])
        semantic = labels_to_partition(self.examples["faris_polysemy_1_1_1_1_2_2"])
        self.assertEqual(block_shape(surface), (1, 1, 3, 3))
        self.assertEqual(block_shape(semantic), (1, 1, 1, 1, 2, 2))
        self.assertFalse(is_conjunctive(surface, FEATURES_SIX))
        self.assertTrue(is_conjunctive(semantic, FEATURES_FOUR))
        diagnosis = evaluate_partition(self.examples["faris_polysemy_1_1_1_1_2_2"], BASIS_RELATIVE)
        self.assertEqual(diagnosis["secondary_side"]["q"], {"s": 0})
        self.assertEqual(diagnosis["features"]["s"]["separated_count"], 4)

    def test_kronenfeld491_counterexample(self):
        partition = labels_to_partition(self.examples["kronenfeld_491_nonconjunctive"])
        self.assertFalse(is_conjunctive(partition, FEATURES_FOUR))
        self.assertFalse(is_conjunctive(partition, FEATURES_SIX))

    def test_p5_all_tree_depths_distinguish_omissible_and_required(self):
        relative_only = feature_tree_depth_options(labels_to_partition(self.examples["relative_sex_only"]))
        self.assertTrue(relative_only["representation_without_feature_exists"])
        self.assertFalse(relative_only["all_tree_representations_violate_only_tertiary"])
        faris = feature_tree_depth_options(labels_to_partition(self.examples["faris_polysemy_1_1_1_1_2_2"]))
        self.assertTrue(faris["tree_exists"])
        self.assertTrue(faris["all_tree_representations_violate_only_tertiary"])
        self.assertFalse(faris["representation_without_feature_exists"])

    def test_p5_conditioned_r_q_tree_is_compatible_despite_edge_proxy(self):
        labels = self.examples["older_r_younger_q"]
        self.assertEqual(prediction_directions(labels)["P5"], "beyond_tertiary_proxy")
        theory = feature_tree_depth_options(labels_to_partition(labels))
        self.assertEqual(theory["status"], "compatible")
        self.assertTrue(theory["representation_without_feature_exists"])
        self.assertIsNotNone(theory["compatible_tree_witness"])
        non_tree = next(p for p in enumerate_partitions() if is_conjunctive(p) and not is_partition_tree(p))
        outside = feature_tree_depth_options(non_tree)
        self.assertEqual(outside["status"], "outside_single_leaf_tree_domain")
        self.assertFalse(outside["all_tree_representations_violate_only_tertiary"])
        self.assertIsNone(outside["compatible_tree_witness"])

    def test_two_edges_can_lack_a_secondary_side(self):
        evaluation = evaluate_partition(self.examples["two_diagonal_contexts"], BASIS_RAW)
        profile = evaluation["features"]["s"]
        self.assertEqual(profile["separated_count"], 2)
        self.assertEqual(profile["secondary_side"], {})
        self.assertEqual(profile["coverage_proxy"], "irregular_two_contexts")

    def test_two_three_feature_bases_do_not_exhaust_four_feature_conjunctions(self):
        labels = self.examples["older_r_younger_q"]
        partition = labels_to_partition(labels)
        self.assertTrue(is_conjunctive(partition, FEATURES_FOUR))
        self.assertFalse(is_conjunctive(partition, BASIS_RAW))
        self.assertFalse(is_conjunctive(partition, BASIS_RELATIVE))

    def test_basis_ties_share_display_weight_without_duplicating_system(self):
        labels = tuple(a for s, a, r in ATOMS)
        selections = select_bases(labels)
        self.assertEqual(len(selections), 2)
        self.assertEqual([value["display_weight"] for value in selections], [0.5, 0.5])
        directions = prediction_directions(labels)
        self.assertEqual(directions["system_weight_per_prediction"], 1)

    def test_endpoint_cube_exact_ranks_and_nesting(self):
        report = endpoint_design_report()
        self.assertEqual({key: value["rank"] for key, value in report["models"].items()}, {"M0": 4, "M1": 5, "M2": 7, "M4": 14})
        self.assertEqual(report["M3_M4_joint_rank"], 28)
        self.assertTrue(report["M4_nested_in_M3"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
