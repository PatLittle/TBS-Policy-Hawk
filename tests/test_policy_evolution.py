import tempfile
import unittest
from datetime import date
from pathlib import Path

from scripts.policy_evolution import fiscal_quarter, upsert_pin_analysis


class PolicyEvolutionTests(unittest.TestCase):
    def test_gc_fiscal_quarters(self):
        self.assertEqual((fiscal_quarter(date(2026, 4, 1))["fiscal_label"], fiscal_quarter(date(2026, 4, 1))["quarter"]), ("2026-27", 1))
        self.assertEqual((fiscal_quarter(date(2026, 8, 26))["fiscal_label"], fiscal_quarter(date(2026, 8, 26))["quarter"]), ("2026-27", 2))
        self.assertEqual((fiscal_quarter(date(2026, 1, 15))["fiscal_label"], fiscal_quarter(date(2026, 1, 15))["quarter"]), ("2025-26", 4))

    def test_upsert_is_marker_delimited_and_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            kwargs = dict(
                issue_number=17,
                repo_full_name="owner/repo",
                title="Notice title",
                guid="pin_test_2026-08-26",
                detected_date="2026-08-26",
                family="SPIN",
                identifier="SPIN 2026-1",
                change_type="changed",
                analysis="## Policy change analysis\n\n### Summary\nFirst.",
            )
            report = upsert_pin_analysis(Path(tmp), **kwargs)
            kwargs["analysis"] = "## Policy change analysis\n\n### Summary\nUpdated."
            upsert_pin_analysis(Path(tmp), **kwargs)
            text = report.read_text(encoding="utf-8")
            self.assertEqual(text.count("policy-hawk:issue-17:start"), 1)
            self.assertNotIn("First.", text)
            self.assertIn("Updated.", text)
            self.assertIn("screenshots/tbs_policy_hawk_heatmap_2026-07-01_to_2026-09-30.png", text)

    def test_pin_sections_sort_by_date_title_and_issue_without_losing_other_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            common = dict(
                repo_full_name="owner/repo",
                family="HRIN",
                identifier="Notice",
                change_type="changed",
                analysis="## Policy change analysis\n\n### Summary\nSummary.",
            )
            report = upsert_pin_analysis(
                root, issue_number=30, title="Zulu", guid="pin-30", detected_date="2026-08-30", **common
            )
            original = report.read_text(encoding="utf-8")
            sentinel = "## Existing non-PIN policy analysis\n\nThis content must remain unchanged.\n\n"
            report.write_text(original.replace("---\n", f"---\n\n{sentinel}", 1), encoding="utf-8")

            upsert_pin_analysis(
                root, issue_number=20, title="Bravo", guid="pin-20", detected_date="2026-08-20", **common
            )
            upsert_pin_analysis(
                root, issue_number=11, title="Alpha", guid="pin-11", detected_date="2026-08-20", **common
            )
            upsert_pin_analysis(
                root, issue_number=10, title="Alpha", guid="pin-10", detected_date="2026-08-20", **common
            )
            text = report.read_text(encoding="utf-8")
            positions = [text.index(f"policy-hawk:issue-{number}:start") for number in (10, 11, 20, 30)]
            self.assertEqual(positions, sorted(positions))
            self.assertEqual(text.count(sentinel.strip()), 1)

    def test_delayed_pin_sorts_before_later_unmarked_policy_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = root / "PolicyEvolution2026-27Q2.md"
            header = "# Policy Evolution 2026-27 Q2\n\nIntro remains intact.\n\n---\n\n"
            ordinary = (
                "## 2026-08-25 — Ordinary policy update\n\n"
                "**Issue:** [#90](https://github.com/owner/repo/issues/90)\n\n"
                "Ordinary section body remains intact.\n\n---\n"
            )
            report.write_text(header + ordinary, encoding="utf-8")

            upsert_pin_analysis(
                root,
                issue_number=42,
                repo_full_name="owner/repo",
                title="Delayed PIN",
                guid="pin-42",
                detected_date="2026-08-20",
                family="SPIN",
                identifier="SPIN 42",
                change_type="changed",
                analysis="## Policy change analysis\n\n### Summary\nDelayed analysis.",
            )

            text = report.read_text(encoding="utf-8")
            self.assertTrue(text.startswith(header))
            self.assertLess(text.index("## 2026-08-20 — Delayed PIN"), text.index("## 2026-08-25 — Ordinary policy update"))
            self.assertIn("Ordinary section body remains intact.", text)


if __name__ == "__main__":
    unittest.main()
