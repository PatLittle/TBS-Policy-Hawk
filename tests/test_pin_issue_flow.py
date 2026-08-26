import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

if "github" not in sys.modules:
    github_stub = types.ModuleType("github")
    github_stub.Github = object
    github_stub.Auth = types.SimpleNamespace(Token=lambda token: token)
    sys.modules["github"] = github_stub
if "playwright.sync_api" not in sys.modules:
    playwright_stub = types.ModuleType("playwright")
    playwright_sync_stub = types.ModuleType("playwright.sync_api")
    playwright_sync_stub.sync_playwright = None
    playwright_stub.sync_api = playwright_sync_stub
    sys.modules["playwright"] = playwright_stub
    sys.modules["playwright.sync_api"] = playwright_sync_stub

from scripts import create_issues_with_screenshots as create_issues
from scripts import enrich_issue
from scripts.pin_change_evidence import canonical_pin_text, load_pin_change


class FakeResponse:
    def __init__(self, status_code, text=""):
        self.status_code = status_code
        self.text = text


class FakeComment:
    def __init__(self, body):
        self.body = body


class FakeIssue:
    def __init__(self, number=42, title="PIN Changed: Test notice"):
        self.number = number
        self.title = title
        self.comments = []

    def get_comments(self):
        return list(self.comments)

    def create_comment(self, body):
        self.comments.append(FakeComment(body))


class FakeLabel:
    def __init__(self, name):
        self.name = name


class FakeRepo:
    def __init__(self, labels_by_issue=None):
        self.labels_by_issue = labels_by_issue or {}

    def get_issue(self, number):
        issue = FakeIssue(number=number)
        issue.labels = [FakeLabel(name) for name in self.labels_by_issue.get(number, [])]
        return issue


def make_change(root: Path, change_type="changed") -> str:
    change_dir = root / "data/PINs/changes/pin-test"
    change_dir.mkdir(parents=True)
    previous = change_dir / "previous.md"
    current = change_dir / "current.md"
    previous.write_text("# Notice\n\n- Captured at (UTC): old\n\nOld direction.\n", encoding="utf-8")
    current.write_text("# Notice\n\n- Captured at (UTC): new\n\nNew direction.\n", encoding="utf-8")
    metadata = {
        "change_type": "pin",
        "pin_change": change_type,
        "title": "Test notice",
        "family": "HRIN",
        "notice_identifier": "2026-01",
        "detected_date": "2026-08-26",
        "url": "https://example.test/notice",
    }
    if change_type != "added":
        metadata["previous_path"] = previous.relative_to(root).as_posix()
    if change_type != "removed":
        metadata["current_path"] = current.relative_to(root).as_posix()
    metadata_path = change_dir / "change.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    return metadata_path.relative_to(root).as_posix()


class PinEvidenceTests(unittest.TestCase):
    def test_canonicalization_removes_collection_churn(self):
        text = "# Notice\n- Source page modified: 2026-01-01\n- Captured at (UTC): now\nBody\n"
        self.assertEqual(canonical_pin_text(text), "# Notice\n\nBody\n")

    def test_loader_confines_all_paths_to_change_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata_path = make_change(root)
            evidence = load_pin_change(metadata_path, root)
            self.assertEqual(evidence["change_type"], "changed")
            self.assertIn("Old direction", evidence["previous_text"])

            outside = root / "outside.md"
            outside.write_text("secret", encoding="utf-8")
            manifest = root / metadata_path
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["current"] = "outside.md"
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "outside"):
                load_pin_change(metadata_path, root)


class PinIssueCreationTests(unittest.TestCase):
    def test_pin_issue_body_contains_evidence_metadata(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch("os.getcwd", return_value=tmp):
            root = Path(tmp)
            metadata_path = make_change(root)
            row = {
                "guid": "pin_hrin_hash_changed_hash_2026-08-26",
                "title": "Test notice",
                "link": "https://example.test/notice",
                "category": "PIN",
                "filename": metadata_path,
                "change_type": "pin",
                "updated_date": "2026-08-26 10:00:00",
            }
            with mock.patch.object(create_issues, "load_pin_change", side_effect=lambda path: load_pin_change(path, root)):
                body = create_issues.issue_body_for_row(row, False, "", {})
            self.assertIn("**Change type:** pin", body)
            self.assertIn("**PIN change:** changed", body)
            self.assertIn("**PIN family:** HRIN", body)
            self.assertIn(f"**PIN metadata:** {metadata_path}", body)

    @mock.patch.object(create_issues.time, "sleep")
    def test_dispatch_retries_three_times(self, _sleep):
        request = mock.Mock(side_effect=[FakeResponse(500), FakeResponse(502), FakeResponse(204)])
        self.assertTrue(create_issues.dispatch_enrichment("owner/repo", 42, "token", request=request))
        self.assertEqual(request.call_count, 3)
        self.assertEqual(request.call_args.kwargs["json"]["inputs"]["issue_number"], "42")

    @mock.patch.object(create_issues.time, "sleep")
    def test_failed_dispatch_remains_pending(self, _sleep):
        with mock.patch.object(create_issues, "dispatch_enrichment", return_value=False):
            pending = create_issues.retry_pending_enrichment(
                [{"issue_number": 42, "guid": "legacy-guid"}], FakeRepo(), "owner/repo", "token", "main"
            )
        self.assertEqual(pending, [{"issue_number": 42, "guid": "legacy-guid"}])

    def test_pin_stays_pending_after_dispatch_until_completion_label(self):
        item = {
            "issue_number": 42,
            "guid": "pin-guid",
            "completion_label": create_issues.AUTOANALYZED_LABEL,
        }
        with mock.patch.object(create_issues, "dispatch_enrichment", return_value=True) as dispatch:
            pending = create_issues.retry_pending_enrichment(
                [item], FakeRepo(), "owner/repo", "token", "main"
            )
        self.assertEqual(pending, [item])
        dispatch.assert_called_once()

        with mock.patch.object(create_issues, "dispatch_enrichment") as dispatch:
            pending = create_issues.retry_pending_enrichment(
                [item],
                FakeRepo({42: [create_issues.AUTOANALYZED_LABEL]}),
                "owner/repo",
                "token",
                "main",
            )
        self.assertEqual(pending, [])
        dispatch.assert_not_called()

    def test_new_pin_is_pending_even_when_dispatch_is_accepted(self):
        record = create_issues.pending_record_for_issue("pin", 42, "pin-guid", True)
        self.assertEqual(record["completion_label"], create_issues.AUTOANALYZED_LABEL)

    def test_corrupt_pending_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pending.json"
            path.write_text("{not json", encoding="utf-8")
            with mock.patch.object(create_issues, "PENDING_ENRICHMENT_JSON_PATH", str(path)):
                with self.assertRaisesRegex(RuntimeError, "refusing to overwrite"):
                    create_issues.load_pending_enrichment()

    def test_save_pending_deduplicates_and_preserves_completion_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pending.json"
            items = [
                {"issue_number": 42, "guid": "pin-guid", "completion_label": create_issues.AUTOANALYZED_LABEL},
                {"issue_number": 42, "guid": "pin-guid"},
            ]
            with mock.patch.object(create_issues, "PENDING_ENRICHMENT_JSON_PATH", str(path)):
                create_issues.save_pending_enrichment(items)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(len(payload), 1)
            self.assertEqual(payload[0]["completion_label"], create_issues.AUTOANALYZED_LABEL)


class PinEnrichmentTests(unittest.TestCase):
    def test_enrichment_posts_evidence_writes_analysis_report_and_output(self):
        analysis = (
            "## Policy change analysis\n\n### Summary\nDirection changed.\n\n"
            "### Substantive changes identified\n\n| Area | Evidence before / previous state | Evidence now | Interpretation |\n"
            "|---|---|---|---|\n| Direction | Old | New | Operational change |\n\n"
            "### Practical effect\nAct on new direction.\n\n### Non-substantive changes\nNone.\n\n"
            "### Watch item\nConfirm implementation.\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata_path = make_change(root)
            output_path = root / "github_output"
            body = (
                "**Title:** Test notice\n**Link:** https://example.test/notice\n**Category:** PIN\n"
                "**GUID:** pin_hrin_hash_changed_hash_2026-08-26\n**PIN family:** HRIN\n"
                "**Notice identifier:** 2026-01\n**Detected date:** 2026-08-26\n"
                f"**PIN metadata:** {metadata_path}\n"
            )
            issue = FakeIssue()
            old_cwd = Path.cwd()
            os.chdir(root)
            try:
                with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "test", "GITHUB_OUTPUT": str(output_path)}), mock.patch.object(
                    enrich_issue, "generate_gemini_summary", return_value=analysis
                ):
                    enrich_issue.enrich_pin_issue(issue, body, "owner/repo")
                    enrich_issue.enrich_pin_issue(issue, body, "owner/repo")
            finally:
                os.chdir(old_cwd)

            change_dir = root / "data/PINs/changes/pin-test"
            saved_analysis = (change_dir / "analysis.md").read_text(encoding="utf-8")
            self.assertIn("Compared the PIN evidence for", saved_analysis)
            self.assertIn("### Summary", saved_analysis)
            report = root / "PolicyEvolution2026-27Q2.md"
            report_text = report.read_text(encoding="utf-8")
            self.assertEqual(report_text.count("policy-hawk:issue-42:start"), 1)
            self.assertIn("### Policy change analysis", report_text)
            self.assertIn("pin_autoanalyzed=true", output_path.read_text(encoding="utf-8"))
            self.assertEqual(sum("policy-hawk:pin-analysis" in c.body for c in issue.comments), 1)


if __name__ == "__main__":
    unittest.main()
