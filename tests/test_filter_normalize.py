"""filter._normalize_scientific_output の回帰テスト。"""

from __future__ import annotations

import html
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from filter import _normalize_scientific_output  # noqa: E402


class TestNormalizeScientificOutput(unittest.TestCase):
    def test_sub_sup_html(self) -> None:
        self.assertEqual(_normalize_scientific_output("CO<sub>2</sub>"), "CO₂")
        self.assertEqual(_normalize_scientific_output("10<sup>3</sup>"), "10³")

    def test_latex_symbols_and_dollars(self) -> None:
        self.assertIn("≲", _normalize_scientific_output("$Re \\lesssim 1000$"))
        self.assertNotIn("$", _normalize_scientific_output("$Re \\lesssim 1000$"))
        self.assertIn("≤", _normalize_scientific_output("a \\leq b"))

    def test_empty(self) -> None:
        self.assertEqual(_normalize_scientific_output(""), "")

    def test_normalized_ok_after_html_escape(self) -> None:
        raw = _normalize_scientific_output("CO<sub>2</sub>、$x \\leq 1$")
        esc = html.escape(raw)
        self.assertNotIn("<sub>", esc)
        self.assertNotIn("&lt;sub", esc)
        self.assertIn("₂", esc)
        self.assertIn("≤", esc)


if __name__ == "__main__":
    unittest.main()
