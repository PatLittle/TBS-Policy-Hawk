import csv
import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from scripts import sync_pin_sources as sync


class PinSyncTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.old_cwd = Path.cwd()
        os.chdir(self.tempdir.name)
        self.paths = mock.patch.multiple(
            sync,
            PIN_SOURCES_MD_PATH=Path("PIN_sources.md"),
            PIN_ROOT=Path("data/PINs"),
            PIN_MANIFEST_PATH=Path("data/PINs/pin_sources_manifest.json"),
            PIN_EVENTS_PATH=Path("data/pin_events.csv"),
            NEW_ITEMS_PATH=Path("data/new_items.csv"),
            ISSUE_MAP_PATH=Path("data/issue_map.json"),
        )
        self.paths.start()
        self.details = {}
        self.fetch_patch = mock.patch.object(sync, "_fetch_details", side_effect=self._detail_results)
        self.fetch_patch.start()
        self.defn = sync.SourceDefinition(
            key="test_notices",
            title="Test policy notices",
            short_name="TPIN",
            url="https://example.test/notices",
            folder="TPIN",
            parser_name="unused",
        )
        self.session = object()

    def tearDown(self):
        self.fetch_patch.stop()
        self.paths.stop()
        os.chdir(self.old_cwd)
        self.tempdir.cleanup()

    def _detail_results(self, records, session):
        return {
            notice["url"]: self.details.get(notice["url"], {"html": None, "error": "timeout"})
            for record in records
            for notice in record["notices"]
        }

    @staticmethod
    def _html(title, body, modified="2026-08-20"):
        return (
            "<html><body><main>"
            f'<h1 id="wb-cont">{title}</h1><p>{body}</p>'
            f'<div class="pagedetails"><time property="dateModified" datetime="{modified}">{modified}</time></div>'
            "</main></body></html>"
        )

    def _notice(self, url="https://example.test/notices/one", title="Notice one", code="2026-01"):
        return {
            "title": title,
            "url": url,
            "listing_date": "2026-08-20",
            "notice_code": code,
            "group": "",
            "table_schema": "date_notice_title_url",
            "table_date": "2026-08-20",
        }

    def _records(self, notices, source_modified="2026-08-20"):
        return [{"definition": self.defn, "source_modified": source_modified, "notices": notices}]

    def _set_success(self, notice, body="Original direction", page_title=None, modified="2026-08-20"):
        self.details[notice["url"]] = {
            "html": self._html(page_title or notice["title"], body, modified),
            "error": "",
        }

    def _sync(self, notices, when=datetime(2026, 8, 26, 14, tzinfo=timezone.utc), source_modified="2026-08-20"):
        return sync.sync_source_records(self._records(notices, source_modified), self.session, when)

    def _manifest(self):
        return json.loads(sync.PIN_MANIFEST_PATH.read_text(encoding="utf-8"))

    def _write_ledger_event(self, guid="pin_test_event_2026-08-26"):
        metadata_path = Path(f"data/PINs/changes/{guid}/change.json")
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(
            json.dumps(
                {
                    "guid": guid,
                    "family": "TPIN",
                    "pin_change": "changed",
                    "notice_identifier": "2026-01",
                }
            ),
            encoding="utf-8",
        )
        sync.PIN_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sync.PIN_EVENTS_PATH.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=sync.ITEM_HEADERS)
            writer.writeheader()
            writer.writerow(
                {
                    "guid": guid,
                    "title": "Notice one",
                    "link": "https://example.test/notices/one",
                    "pubDate": "Wed, 26 Aug 2026 00:00:00 -0400",
                    "category": "PIN",
                    "filename": metadata_path.as_posix(),
                    "updated_date": "2026-08-26T10:00:00-04:00",
                }
            )
        return guid

    def test_canonicalization_ignores_only_run_and_source_page_timestamps(self):
        first = "# PIN\n- Source page modified: 2026-01-01\n- Captured at (UTC): 2026-01-01T00:00:00Z\n- Notice modified: 2026-01-01\nBody\n"
        second = "# PIN\n- Source page modified: 2026-02-01\n- Captured at (UTC): 2026-02-01T00:00:00Z\n- Notice modified: 2026-01-01\nBody\n"
        self.assertEqual(sync.canonical_notice_text(first), sync.canonical_notice_text(second))
        self.assertNotEqual(sync.canonical_notice_text(first), sync.canonical_notice_text(second.replace("Body", "New body")))

    def test_empty_repository_baselines_without_emitting_events(self):
        notice = self._notice()
        self._set_success(notice)
        events = self._sync([notice])
        self.assertEqual(events, [])
        self.assertTrue(Path("data/PINs/TPIN/Notice_one.md").exists())
        self.assertFalse(sync.NEW_ITEMS_PATH.exists())
        self.assertEqual(self._manifest()["schema_version"], 2)

    def test_timestamp_only_second_sync_is_byte_identical(self):
        notice = self._notice()
        self._set_success(notice)
        self._sync([notice])
        before = {
            path.as_posix(): path.read_bytes()
            for path in [sync.PIN_SOURCES_MD_PATH, sync.PIN_MANIFEST_PATH, *sync.PIN_ROOT.glob("*/*.md")]
        }
        events = self._sync(
            [notice],
            datetime(2026, 8, 27, 3, tzinfo=timezone.utc),
            source_modified="2026-08-27",
        )
        after = {path: Path(path).read_bytes() for path in before}
        self.assertEqual(events, [])
        self.assertEqual(before, after)

    def test_content_change_reuses_filename_and_emits_evidence_and_ledgers(self):
        notice = self._notice(title="Original title")
        self._set_success(notice, "Original direction")
        self._sync([notice])
        original_path = Path(self._manifest()["sources"][0]["notices"][0]["path"])

        renamed = self._notice(title="Renamed listing title")
        self._set_success(renamed, "New operational requirement", page_title="Renamed listing title")
        events = self._sync([renamed], datetime(2026, 8, 26, 2, tzinfo=timezone.utc))

        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event["pin_change"], "changed")
        self.assertTrue(event["guid"].endswith("_2026-08-25"))
        self.assertEqual(Path(event["stable_path"]), original_path)
        evidence = Path(event["metadata_path"]).parent
        self.assertIn("Original direction", (evidence / "previous.md").read_text(encoding="utf-8"))
        self.assertIn("New operational requirement", (evidence / "current.md").read_text(encoding="utf-8"))
        self.assertEqual(json.loads((evidence / "change.json").read_text(encoding="utf-8"))["guid"], event["guid"])
        with sync.NEW_ITEMS_PATH.open(newline="", encoding="utf-8") as handle:
            new_row = next(csv.DictReader(handle))
        with sync.PIN_EVENTS_PATH.open(newline="", encoding="utf-8") as handle:
            heatmap_row = next(csv.DictReader(handle))
        self.assertEqual(new_row["change_type"], "pin")
        self.assertEqual(heatmap_row["category"], "PIN")
        self.assertEqual(new_row["guid"], heatmap_row["guid"])

    def test_transition_guid_is_retry_stable(self):
        first = sync._event_guid(self.defn, "https://example.test/n", "changed", "before", "after", "2026-08-26")
        second = sync._event_guid(self.defn, "https://example.test/n", "changed", "before", "after", "2026-08-26")
        different = sync._event_guid(self.defn, "https://example.test/n", "changed", "before", "other", "2026-08-26")
        self.assertEqual(first, second)
        self.assertNotEqual(first, different)
        self.assertTrue(first.endswith("_2026-08-26"))

    def test_change_evidence_is_immutable_on_retry(self):
        notice = self._notice()
        stable_path = Path("data/PINs/TPIN/Notice_one.md")
        first = sync._write_change_evidence(
            self.defn,
            notice,
            "changed",
            "before",
            "after\n- Captured at (UTC): 2026-08-26T01:00:00Z\n",
            "2026-08-26",
            stable_path,
        )
        current_path = Path(first["current_path"])
        original = current_path.read_bytes()
        second = sync._write_change_evidence(
            self.defn,
            notice,
            "changed",
            "before",
            "after\n- Captured at (UTC): 2026-08-26T02:00:00Z\n",
            "2026-08-26",
            stable_path,
        )
        self.assertEqual(first["guid"], second["guid"])
        self.assertEqual(current_path.read_bytes(), original)

    def test_transient_failure_preserves_last_good_and_defers_uncaptured_notice(self):
        existing = self._notice()
        self._set_success(existing)
        self._sync([existing])
        stable = Path(self._manifest()["sources"][0]["notices"][0]["path"])
        before = stable.read_bytes()

        new = self._notice("https://example.test/notices/two", "Notice two", "2026-02")
        self.details[existing["url"]] = {"html": None, "error": "timeout"}
        self.details[new["url"]] = {"html": None, "error": "timeout"}
        events = self._sync([existing, new], source_modified="2026-08-27")

        self.assertEqual(events, [])
        self.assertEqual(stable.read_bytes(), before)
        urls = [item["url"] for item in self._manifest()["sources"][0]["notices"]]
        self.assertEqual(urls, [existing["url"]])

    def test_suspicious_twenty_five_percent_inventory_drop_fails_before_fetch(self):
        notices = [self._notice(f"https://example.test/notices/{index}", f"Notice {index}", str(index)) for index in range(8)]
        for notice in notices:
            self._set_success(notice)
        self._sync(notices)
        with self.assertRaisesRegex(RuntimeError, "Suspicious PIN inventory drop"):
            self._sync(notices[:6])

    def test_removal_requires_two_successful_listing_checks(self):
        first = self._notice()
        removed = self._notice("https://example.test/notices/two", "Notice two", "2026-02")
        self._set_success(first)
        self._set_success(removed)
        self._sync([first, removed])
        removed_path = Path(self._manifest()["sources"][0]["notices"][1]["path"])

        self.assertEqual(self._sync([first]), [])
        self.assertTrue(removed_path.exists())
        self.assertEqual(self._manifest()["pending_removals"][self.defn.key][removed["url"]], 1)

        events = self._sync([first], datetime(2026, 8, 27, 14, tzinfo=timezone.utc))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["pin_change"], "removed")
        self.assertFalse(removed_path.exists())
        self.assertNotIn(removed["url"], [item["url"] for item in self._manifest()["sources"][0]["notices"]])
        self.assertIn("no longer listed", Path(events[0]["current_path"]).read_text(encoding="utf-8"))

    def test_reappearance_clears_pending_removal(self):
        first = self._notice()
        second = self._notice("https://example.test/notices/two", "Notice two", "2026-02")
        self._set_success(first)
        self._set_success(second)
        self._sync([first, second])
        self._sync([first])
        self.assertEqual(self._sync([first, second]), [])
        self.assertEqual(self._manifest()["pending_removals"], {})

    def test_missing_or_corrupt_manifest_with_captures_fails_closed(self):
        capture = sync.PIN_ROOT / self.defn.folder / "existing.md"
        capture.parent.mkdir(parents=True)
        capture.write_text("last good", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "manifest is missing"):
            self._sync([])
        sync.PIN_MANIFEST_PATH.write_text("{broken", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "manifest is unreadable"):
            self._sync([])

    def test_unmapped_durable_pin_event_is_requeued_on_unchanged_sync(self):
        guid = self._write_ledger_event()
        sync.ISSUE_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
        sync.ISSUE_MAP_PATH.write_text("{}\n", encoding="utf-8")

        self._sync([])

        with sync.NEW_ITEMS_PATH.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual([row["guid"] for row in rows], [guid])
        self.assertEqual(rows[0]["change_type"], "pin")
        self.assertEqual(rows[0]["source_id"], "TPIN")
        self.assertEqual(rows[0]["change_summary"], "PIN changed: TPIN 2026-01")

    def test_mapped_pin_event_is_not_requeued(self):
        guid = self._write_ledger_event()
        sync.ISSUE_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
        sync.ISSUE_MAP_PATH.write_text(json.dumps({guid: 321}), encoding="utf-8")

        self._sync([])

        self.assertFalse(sync.NEW_ITEMS_PATH.exists())

    def test_corrupt_or_non_object_issue_map_fails_before_sync_writes(self):
        sync.ISSUE_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
        for payload in ("{broken", "[]"):
            with self.subTest(payload=payload):
                sync.ISSUE_MAP_PATH.write_text(payload, encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, "issue map"):
                    self._sync([])
                self.assertFalse(sync.PIN_SOURCES_MD_PATH.exists())
                self.assertFalse(sync.PIN_MANIFEST_PATH.exists())


if __name__ == "__main__":
    unittest.main()
