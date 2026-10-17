"""T6覆盖审计的纯数据测试，不计算跨领域结果。"""
import sys
from pathlib import Path
import unittest

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis/v3"))
from domain_feasibility import (collect_cells, coverage_for_system, domain_registry,
                                normalize_form, source_ids)


class DomainCoverageTests(unittest.TestCase):
    def frame(self, rows):
        return pd.DataFrame([{"ID": str(i), "Language_ID": lid, "Parameter_ID": code,
                              "Form": form, "Source": source, "Value": form,
                              "Comment": ""} for i,(lid,code,form,source) in enumerate(rows)])

    def test_explicit_domain_cells_and_ego_sex(self):
        domains = domain_registry()
        self.assertEqual([len(rows) for rows in domains.values()], [16,16,8])
        for rows in domains.values():
            self.assertEqual(len(rows), len({row["Parameter_ID"] for row in rows}))
            self.assertEqual({row["s"] for row in rows}, {0,1})
            self.assertTrue(all(row["Parameter_ID"][0] in "mf" for row in rows))
        self.assertIn("a_parent", domains["parent_siblings_age16"][0])
        self.assertNotIn("a_parent", domains["parent_siblings_generic8"][0])

    def test_nfc_whitespace_preserves_diacritics(self):
        self.assertEqual(normalize_form("  a\u0301   b\t"), "á b")
        self.assertNotEqual(normalize_form("á"), normalize_form("a"))

    def test_source_locations_removed_without_merging_keys(self):
        self.assertEqual(source_ids("author2020[12-13]; other2000; author2020[7]"), {"author2020","other2000"})

    def test_invalid_missing_and_multiple_remain_distinct(self):
        raw=self.frame([("x","mFB","?","s"),("x","mFZ","-","s"),
                        ("x","mMB","a","s"),("x","mMB","b","s")])
        cells=collect_cells(raw,{"x"},{"mFB","mFZ","mMB","mMZ"})
        value=coverage_for_system("x",["mFB","mFZ","mMB","mMZ"],cells)
        self.assertEqual(value["valid_cells"],1)
        self.assertEqual(value["singleton_cells"],0)
        self.assertEqual(value["invalid_rows"],2)
        self.assertEqual(value["multiple_form_codes"],["mMB"])
        self.assertFalse(value["complete"])

    def test_other_language_id_and_generic_do_not_fill_ego_cells(self):
        raw=self.frame([("x","FB","a","s"),("y","mFB","b","s"),("x","mFeB","a","s")])
        cells=collect_cells(raw,{"x"},{"mFB"})
        value=coverage_for_system("x",["mFB"],cells)
        self.assertEqual(value["valid_cells"],0)

    def test_union_of_distinct_sources_does_not_create_common_source(self):
        raw=self.frame([("x","mFB","a","s1"),("x","mFZ","a","s2")])
        cells=collect_cells(raw,{"x"},{"mFB","mFZ"})
        value=coverage_for_system("x",["mFB","mFZ"],cells)
        self.assertTrue(value["complete_singleton"])
        self.assertFalse(value["has_common_source_complete"])

    def test_source_singleton_and_pooled_singleton_are_separate(self):
        raw=self.frame([("x","mFB","a","s1"),("x","mFB","b","s2"),
                        ("x","mFZ","c","s1"),("x","mFZ","d","s2")])
        cells=collect_cells(raw,{"x"},{"mFB","mFZ"})
        value=coverage_for_system("x",["mFB","mFZ"],cells)
        self.assertFalse(value["complete_singleton"])
        self.assertTrue(value["has_common_source_singleton"])
        self.assertEqual(value["common_singleton_sources"],["s1","s2"])

    def test_duplicate_nfc_rows_are_one_form_but_raw_rows_retained(self):
        raw=self.frame([("x","mFB","a\u0301","s[2]"),("x","mFB","á","s[3]")])
        cells=collect_cells(raw,{"x"},{"mFB"})
        value=coverage_for_system("x",["mFB"],cells)
        self.assertTrue(value["complete_singleton"])
        self.assertEqual(len(cells[("x","mFB")]["rows"]),2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
