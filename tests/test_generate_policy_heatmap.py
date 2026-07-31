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

    def test_resolve_dates_requires_both_explicit_bounds(self):
        with self.assertRaises(ValueError):
            generate_policy_heatmap.resolve_dates("2026-04-01", None)

        with self.assertRaises(ValueError):
            generate_policy_heatmap.resolve_dates("2026-06-30", "2026-04-01")


class HeatmapDataTests(unittest.TestCase):
    def test_collect_counts_uses_publication_dates_within_period(self):
        csv_text = (
            "guid,pubDate,updated_date\n"
            'a,"Wed, 01 Jul 2026 00:00:00 -0400",2026-07-02 10:00:00\n'
            'b,"Wed, 01 Jul 2026 12:00:00 -0400",2026-07-03 10:00:00\n'
            'c,"Tue, 30 Jun 2026 00:00:00 -0400",2026-07-01 10:00:00\n'
        )

        counts = generate_policy_heatmap.collect_counts(
            csv_text,
            date(2026, 7, 1),
            date(2026, 9, 30),
            "pubDate",
        )

        self.assertEqual(counts, {date(2026, 7, 1): 2})

    def test_quarter_filename_is_constant(self):
        self.assertEqual(
            generate_policy_heatmap.heatmap_filename(
                date(2026, 4, 1),
                date(2026, 6, 30),
            ),
            "tbs_policy_hawk_heatmap_2026-04-01_to_2026-06-30.png",
        )


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
