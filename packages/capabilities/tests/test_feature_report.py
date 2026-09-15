"""`features report`: the completeness vector as a table people can paste.

A Harvey ball is a rolled (covered, total) pair drawn as a glyph. The glyph is
computed from the ratio and NEVER from a bare percentage across the tree: a
feature with total 0 renders as unassessed ('?'), not as full.
"""

from __future__ import annotations

import unittest

from capcov.features.coverage import rollup
from capcov.features.model import example
from capcov.features.report import glyph, render


OBL = {"auth": {"covered": 1, "total": 1}, "password": {"covered": 2, "total": 4},
       "mfa": {"covered": 0, "total": 3}}


class GlyphTests(unittest.TestCase):
    def test_glyphs_follow_quarters(self) -> None:
        self.assertEqual(glyph(0, 0), "?")
        self.assertEqual(glyph(0, 4), "○")
        self.assertEqual(glyph(1, 4), "◔")
        self.assertEqual(glyph(2, 4), "◑")
        self.assertEqual(glyph(3, 4), "◕")
        self.assertEqual(glyph(4, 4), "●")
        self.assertEqual(glyph(1, 3), "◔")
        self.assertEqual(glyph(2, 3), "◕")


class RenderTests(unittest.TestCase):
    def test_markdown_has_one_row_per_feature_with_glyph_and_counts(self) -> None:
        text = render(rollup(example(), OBL, selected={"mfa"}), fmt="md")
        self.assertIn("| Authentication |", text)
        self.assertIn("| ◑ | 2/4 |", text)
        self.assertIn("| ○ | 0/3 |", text)
        self.assertIn("unassessed", text)

    def test_csv_rows_are_parseable(self) -> None:
        import csv, io
        text = render(rollup(example(), OBL), fmt="csv")
        rows = list(csv.DictReader(io.StringIO(text)))
        self.assertEqual(rows[0]["feature"], "auth")
        self.assertEqual({"feature", "name", "parent", "kind", "status", "self_covered",
                          "self_total", "covered", "total", "glyph"}, set(rows[0]))

    def test_unknown_format_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            render(rollup(example(), OBL), fmt="xlsx")
