"""T4纯函数与估计对象测试；不读取实测T1映射。"""
from itertools import product
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis/v3"))
from position_tests import (
    AGE_CONFIGS, ATOMS, CONTRAST_IDS, GENDER_CONFIGS,
    age_distinction_set, bootstrap_ratio, configuration_contrast,
    contrast_statistics, equivalence_decision, equivalence_ii_statistics,
    family_modal_partial_type, gender_distinction_set, holm_six,
    partial_types, type_frequencies,
)


def labels_for_age_set(values):
    return tuple((s, r, a if "MF"[s] + "MF"[r] in values else None) for s, a, r in ATOMS)


def record(family, age_values, gender_values=()):
    return {"family_group": family, "A": frozenset(age_values), "G": frozenset(gender_values)}


class PositionSetTests(unittest.TestCase):
    def test_every_age_partial_set_can_be_recovered(self):
        self.assertEqual(len(partial_types(AGE_CONFIGS)), 14)
        for values in partial_types(AGE_CONFIGS):
            self.assertEqual(age_distinction_set(labels_for_age_set(values)), values)

    def test_gender_fixed_ego_does_not_mix_speaker_sex(self):
        labels = tuple((s, a, r if (s, a) in ((0, 0), (1, 1)) else None) for s, a, r in ATOMS)
        values = gender_distinction_set(labels)
        self.assertEqual(values, {"ME", "FY"})
        self.assertEqual(configuration_contrast((), values, "G_male_ego"), 1)
        self.assertEqual(configuration_contrast((), values, "G_female_ego"), -1)

    def test_coordinate_alignment_survives_row_permutation(self):
        labels = labels_for_age_set({"MM", "FF"})
        order = (7, 0, 5, 2, 1, 3, 6, 4)
        self.assertEqual(age_distinction_set([labels[i] for i in order], [ATOMS[i] for i in order]), {"MM", "FF"})
        with self.assertRaises(ValueError):
            age_distinction_set(labels, [(0, 0, 0)] * 8)

    def test_known_english_and_relative_sex_are_distinct_from_age_sets(self):
        english = tuple(r for s, a, r in ATOMS)
        relative = tuple(s ^ r for s, a, r in ATOMS)
        self.assertEqual(age_distinction_set(english), set())
        self.assertEqual(age_distinction_set(relative), set())
        self.assertEqual(gender_distinction_set(english), set(GENDER_CONFIGS))

    def test_exact_age_contrast_definitions(self):
        self.assertEqual(configuration_contrast({"MM", "FF"}, (), "A_i"), 1)
        self.assertEqual(configuration_contrast({"MF", "FM"}, (), "A_i"), -1)
        self.assertEqual(configuration_contrast({"MM", "MF"}, (), "A_i"), 0)
        self.assertEqual(configuration_contrast({"MM"}, (), "A_ii"), 1)
        self.assertEqual(configuration_contrast({"FF"}, (), "A_ii"), -1)
        self.assertEqual(configuration_contrast({"MM", "FF"}, (), "A_ii"), 0)
        self.assertEqual(configuration_contrast({"FM"}, (), "A_iii"), 1)
        self.assertEqual(configuration_contrast({"MF"}, (), "A_iii"), -1)
        self.assertEqual(configuration_contrast({"MM", "FM"}, (), "A_iv"), 1)
        self.assertEqual(configuration_contrast({"MF", "FF"}, (), "A_iv"), -1)
        for contrast in CONTRAST_IDS[:4]:
            self.assertEqual(configuration_contrast((), (), contrast), 0)
            self.assertEqual(configuration_contrast(AGE_CONFIGS, (), contrast), 0)

    def test_type_table_keeps_all_zero_frequency_types(self):
        rows = [record("g", {"MM"})]
        result = type_frequencies(rows, "A")
        self.assertEqual(len(result["types"]), 14)
        self.assertEqual(sum(value["systems"] for value in result["types"]), 1)
        self.assertEqual(sum(value["systems"] == 0 for value in result["types"]), 13)


class AggregationTests(unittest.TestCase):
    def test_contrast_majority_is_not_modal_type(self):
        rows = [record("g", {"MM"})] * 2 + [record("g", {"FF"})] + [record("g", {"MF"})] * 3
        within = contrast_statistics(rows, "A_ii", "family_contrast_majority")
        modal = contrast_statistics(rows, "A_ii", "family_modal_partial_type_sensitivity")
        self.assertEqual((within["left"], within["right"]), (1, 0))
        self.assertEqual(modal["denominator"], 0)
        self.assertEqual(modal["family_exclusion_status"]["unique_modal_type_outside_contrast"], 1)

    def test_modal_ties_and_no_partial_are_not_arbitrarily_resolved(self):
        tie = family_modal_partial_type([{"MM"}, {"FF"}])
        self.assertEqual(tie["status"], "multiple_modal_types")
        self.assertIsNone(tie["modal_type"])
        absent = family_modal_partial_type([set(), set(AGE_CONFIGS)])
        self.assertEqual(absent["status"], "no_partial_age_systems")

    def test_family_vote_ties_excluded_with_counts_retained(self):
        rows = [record("g1", {"MM"}), record("g1", {"FF"}), record("g2", {"MM"}), record("g3", set())]
        result = contrast_statistics(rows, "A_ii", "family_contrast_majority")
        self.assertEqual(result["denominator"], 1)
        self.assertEqual(result["family_exclusion_status"]["family_tie"], 1)
        self.assertEqual(result["family_exclusion_status"]["no_related_systems"], 1)
        self.assertEqual(result["excluded_systems"], 1)

    def test_modal_sensitivity_preserves_original_G_family_aggregation(self):
        rows = [record("g", {"MM"}, {"ME"}), record("g", {"FF"}, {"ME"}), record("g", {"MF"}, {"MY"})]
        direct = contrast_statistics(rows, "G_male_ego", "family_contrast_majority")
        sensitivity = contrast_statistics(rows, "G_male_ego", "family_modal_partial_type_sensitivity")
        self.assertEqual((direct["left"], direct["right"]), (sensitivity["left"], sensitivity["right"]))

    def test_ii_estimands_are_not_interchanged(self):
        rows = [record("g1", {"MM"})] * 100 + [record("g2", {"FF"})]
        result = equivalence_ii_statistics(rows)
        self.assertEqual(result["family_direction_majority_primary"]["estimate"], 0)
        self.assertAlmostEqual(result["system_ratio_sensitivity"]["estimate"], 99 / 101)
        self.assertEqual(result["continuous_family_equal_sensitivity"]["estimate"], 0)
        self.assertFalse(result["family_direction_majority_primary"]["supported"])


class InferenceTests(unittest.TestCase):
    def test_fixed_six_holm_includes_unassessable_contrast(self):
        self.assertEqual(holm_six([.001, .01, .03, .04, .2, None]), [.006, .05, .12, .12, .4, None])
        with self.assertRaises(ValueError):
            holm_six([.01] * 4)

    def test_equivalence_requires_narrow_interval_not_zero_inclusion(self):
        narrow = {"ci95": [-.1, .1], "empty_denominator_replicates": 0}
        broad = {"ci95": [-.6, .6], "empty_denominator_replicates": 0}
        boundary = {"ci95": [-.15, .1], "empty_denominator_replicates": 0}
        self.assertTrue(equivalence_decision(narrow)["supported"])
        self.assertFalse(equivalence_decision(broad)["supported"])
        self.assertFalse(equivalence_decision(boundary)["supported"])

    def test_bootstrap_retains_cluster_size_and_repeated_draws(self):
        output = bootstrap_ratio([(100, 0), (0, 1)], "system_ratio", replicates=200, seed=19)
        self.assertAlmostEqual(output["estimate"], 99 / 101)
        self.assertEqual(output["ci95"], [-1., 1.])
        self.assertEqual(output, bootstrap_ratio([(100, 0), (0, 1)], "system_ratio", replicates=200, seed=19))

    def test_empty_denominator_is_recorded_not_zero_filled(self):
        empty = bootstrap_ratio([(0, 0)], "system_ratio", replicates=10)
        self.assertIsNone(empty["estimate"])
        self.assertIsNone(empty["ci95"])
        self.assertEqual(empty["empty_denominator_replicates"], 10)
        self.assertEqual(equivalence_decision(empty)["status"], "not_assessable_empty_denominator")


if __name__ == "__main__":
    unittest.main(verbosity=2)
