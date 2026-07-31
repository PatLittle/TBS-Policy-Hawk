import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts import generate_policy_heatmap


class FiscalQuarterTests(unittest.TestCase):
    def test_current_gc_fiscal_quarter_for_each_quarter(self):
        cases = {
            date(2026, 4, 1): (date(2026, 4, 1), date(2026, 6, 30)),
            date(2026, 7, 25): (date(2026, 7, 1), date(2026, 9, 30)),
            date(2026, 12, 31): (date(2026, 10, 1), date(2026, 12, 31)),
            date(2027, 2, 1): (date(2027, 1, 1), date(2027, 3, 31)),
        }

        for today, expected in cases.items():
            with self.subTest(today=today):
                self.assertEqual(
                    generate_policy_heatmap.current_gc_fiscal_quarter(today),
                    expected,
                )

    def test_completed_quarters_begin_with_2026_27_q1(self):
        cases = {
            date(2026, 6, 30): [],
            date(2026, 7, 1): ["2026-27Q1"],
            date(2026, 10, 1): ["2026-27Q1", "2026-27Q2"],
            date(2027, 4, 1): [
                "2026-27Q1",
                "2026-27Q2",
                "2026-27Q3",
                "2026-27Q4",
            ],
            date(2027, 7, 1): [
                "2026-27Q1",
                "2026-27Q2",
                "2026-27Q3",
                "2026-27Q4",
                "2027-28Q1",
            ],
        }

        for today, expected_labels in cases.items():
            with self.subTest(today=today):
                quarters = generate_policy_heatmap.completed_gc_fiscal_quarters(today)
                self.assertEqual(
                    [label for label, _, _ in quarters],
                    expected_labels,
                )

    def test_quarters_to_date_include_current_quarter_with_td_suffix(self):
        cases = {
            date(2026, 3, 31): [],
            date(2026, 4, 1): ["2026-27Q1TD"],
            date(2026, 6, 30): ["2026-27Q1TD"],
            date(2026, 7, 1): ["2026-27Q1", "2026-27Q2TD"],
            date(2026, 10, 1): [
                "2026-27Q1",
                "2026-27Q2",
                "2026-27Q3TD",
            ],
            date(2027, 4, 1): [
                "2026-27Q1",
                "2026-27Q2",
                "2026-27Q3",
                "2026-27Q4",
                "2027-28Q1TD",
            ],
        }

        for today, expected_labels in cases.items():
            with self.subTest(today=today):
                quarters = generate_policy_heatmap.gc_fiscal_quarters_to_date(today)
                self.assertEqual(
                    [label for label, _, _ in quarters],
                    expected_labels,
                )

    def test_resolve_dates_requires_both_explicit_bounds(self):
        with self.assertRaises(ValueError):
            generate_policy_heatmap.resolve_dates("2026-04-01", None)

        with self.assertRaises(ValueError):
            generate_policy_heatmap.resolve_dates("2026-06-30", "2026-04-01")


class HeatmapDataTests(unittest.TestCase):
    def test_collect_counts_uses_publication_dates_within_period(self):
        csv_text = (
            "guid,pubDate,updated_date,category\n"
            'a,"Wed, 01 Jul 2026 00:00:00 -0400",'
            "2026-07-02 10:00:00,Directive\n"
            'b,"Wed, 01 Jul 2026 12:00:00 -0400",'
            "2026-07-03 10:00:00,Policy\n"
            'c,"Tue, 30 Jun 2026 00:00:00 -0400",'
            "2026-07-01 10:00:00,Directive\n"
        )

        counts, instrument_counts = generate_policy_heatmap.collect_activity_counts(
            csv_text,
            date(2026, 7, 1),
            date(2026, 9, 30),
            "pubDate",
        )

        self.assertEqual(counts, {date(2026, 7, 1): 2})
        self.assertEqual(instrument_counts, {"Directive": 1, "Policy": 1})

    def test_collect_counts_retains_daily_count_api(self):
        csv_text = (
            "guid,pubDate,updated_date\n"
            'a,"Wed, 01 Jul 2026 00:00:00 -0400",2026-07-02 10:00:00\n'
        )

        self.assertEqual(
            generate_policy_heatmap.collect_counts(
                csv_text,
                date(2026, 7, 1),
                date(2026, 9, 30),
                "pubDate",
            ),
            {date(2026, 7, 1): 1},
        )

    def test_collects_instrument_counts_for_each_completed_quarter(self):
        csv_text = (
            "guid,pubDate,updated_date,category\n"
            'a,"Mon, 01 Jun 2026 00:00:00 -0400",'
            "2026-06-01 10:00:00,Directive\n"
            'b,"Wed, 01 Jul 2026 00:00:00 -0400",'
            "2026-07-01 10:00:00,Policy\n"
            'c,"Thu, 02 Jul 2026 00:00:00 -0400",'
            "2026-07-02 10:00:00,Directive\n"
        )

        quarter_counts = (
            generate_policy_heatmap.collect_completed_quarter_instrument_counts(
                csv_text,
                "pubDate",
                today=date(2026, 10, 1),
            )
        )

        self.assertEqual(
            quarter_counts,
            [
                ("2026-27Q1", {"Directive": 1}),
                ("2026-27Q2", {"Policy": 1, "Directive": 1}),
            ],
        )

    def test_collects_current_quarter_instrument_counts_to_date(self):
        csv_text = (
            "guid,pubDate,updated_date,category\n"
            'a,"Mon, 01 Jun 2026 00:00:00 -0400",'
            "2026-06-01 10:00:00,Directive\n"
            'b,"Wed, 01 Jul 2026 00:00:00 -0400",'
            "2026-07-01 10:00:00,Policy\n"
            'c,"Thu, 02 Jul 2026 00:00:00 -0400",'
            "2026-07-02 10:00:00,Directive\n"
        )

        quarter_counts = generate_policy_heatmap.collect_quarter_instrument_counts(
            csv_text,
            "pubDate",
            today=date(2026, 7, 1),
        )

        self.assertEqual(
            quarter_counts,
            [
                ("2026-27Q1", {"Directive": 1}),
                ("2026-27Q2TD", {"Policy": 1}),
            ],
        )

    def test_quarter_filename_is_constant(self):
        self.assertEqual(
            generate_policy_heatmap.heatmap_filename(
                date(2026, 4, 1),
                date(2026, 6, 30),
            ),
            "tbs_policy_hawk_heatmap_2026-04-01_to_2026-06-30.png",
        )

    def test_pie_value_label_returns_whole_number_count(self):
        self.assertEqual(generate_policy_heatmap.pie_value_label(80.0, 5), "4")
        self.assertEqual(generate_policy_heatmap.pie_value_label(20.0, 5), "1")
        self.assertEqual(generate_policy_heatmap.pie_value_label(0.0, 5), "")


class ImageMetadataTests(unittest.TestCase):
    def test_embeds_exif_and_exact_png_metadata(self):
        from PIL import Image

        with TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "heatmap.png"
            Image.new("RGB", (10, 10), color="white").save(output, dpi=(150, 150))

            generate_policy_heatmap.embed_image_metadata(output)

            with Image.open(output) as image:
                self.assertEqual(
                    image.info["Software"],
                    generate_policy_heatmap.IMAGE_SOFTWARE,
                )
                self.assertEqual(
                    image.info["Copyright"],
                    generate_policy_heatmap.IMAGE_COPYRIGHT,
                )
                self.assertEqual(
                    image.info["SubjectLocation"],
                    generate_policy_heatmap.IMAGE_SUBJECT_LOCATION,
                )
                self.assertAlmostEqual(image.info["dpi"][0], 150, delta=0.1)

                exif = image.getexif()
                self.assertEqual(exif[305], generate_policy_heatmap.IMAGE_SOFTWARE)
                self.assertEqual(
                    exif[33432],
                    generate_policy_heatmap.IMAGE_COPYRIGHT_EXIF,
                )
                self.assertTrue(exif[37510].startswith(b"UNICODE\0"))
                comment = exif[37510][8:].decode("utf-16-be")
                self.assertIn(
                    f"Copyright: {generate_policy_heatmap.IMAGE_COPYRIGHT}",
                    comment,
                )
                self.assertIn(
                    "SubjectLocation: "
                    f"{generate_policy_heatmap.IMAGE_SUBJECT_LOCATION}",
                    comment,
                )


class ReadmeUpdateTests(unittest.TestCase):
    def test_heatmap_is_last_content_before_main_datasets(self):
        with TemporaryDirectory() as tmpdir:
            readme = Path(tmpdir) / "README.md"
            readme.write_text(
                "# Project\n\nIntroduction.\n\n## Main Datasets\n\nDataset details.\n",
                encoding="utf-8",
            )

            generate_policy_heatmap.update_readme_heatmap(
                readme,
                "screenshots/tbs_policy_hawk_heatmap_2026-07-01_to_2026-09-30.png",
                date(2026, 7, 1),
                date(2026, 9, 30),
            )

            text = readme.read_text(encoding="utf-8")
            before_datasets = text.split("## Main Datasets", 1)[0].rstrip()
            self.assertTrue(
                before_datasets.endswith(
                    "![TBS Policy Hawk activity heatmap for 2026-07-01 to "
                    "2026-09-30](screenshots/"
                    "tbs_policy_hawk_heatmap_2026-07-01_to_2026-09-30.png)"
                )
            )

    def test_existing_heatmap_slot_is_replaced_not_duplicated(self):
        with TemporaryDirectory() as tmpdir:
            readme = Path(tmpdir) / "README.md"
            readme.write_text(
                "# Project\n\n"
                f"{generate_policy_heatmap.README_HEATMAP_MARKER}\n"
                "![old](screenshots/tbs_policy_hawk_heatmap_old.png)\n\n"
                "## Main Datasets\n",
                encoding="utf-8",
            )

            generate_policy_heatmap.update_readme_heatmap(
                readme,
                "screenshots/tbs_policy_hawk_heatmap_new.png",
                date(2026, 7, 1),
                date(2026, 9, 30),
            )

            text = readme.read_text(encoding="utf-8")
            self.assertEqual(text.count(generate_policy_heatmap.README_HEATMAP_MARKER), 1)
            self.assertNotIn("heatmap_old.png", text)
            self.assertIn("heatmap_new.png", text)


if __name__ == "__main__":
    unittest.main()
