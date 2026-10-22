import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from scripts import cabinet_directives as cabinet
from scripts import enrich_cabinet_directive as enrichment
from scripts import enrich_issue


URL = "https://www.canada.ca/en/test/cabinet.html"
OLD_URL = "https://www.canada.ca/en/test/previous-cabinet.html"


def html(direction="Departments must report annually. ", modified="2026-10-22"):
    return (f'<html><head><meta name="dcterms.issued" content="2018-06-28">'
            f'<meta name="dcterms.modified" content="{modified}"></head><body>'
            '<nav>Volatile navigation</nav><main><h1>Cabinet Directive on Testing</h1>'
            '<h2>1. Obligations</h2><p>' + direction * 20 + '</p>'
            f'<div class="pagedetails">Date modified: {modified}</div></main></body></html>')


def entry(url=URL):
    return {"title": "Cabinet Directive on Testing", "url": url, "Status": "In Force",
            "Date Published": "2018-06-28", "Date of effect": "Unknown", "Date last modified": "2026-10-22"}


class FakeIssue:
    def __init__(self, number=123, body="", labels=()):
        self.number, self.body, self.title = number, body, "CABDir"
        self.labels = [SimpleNamespace(name=name) for name in labels]
        self.comments = []

    def get_comments(self):
        return self.comments

    def create_comment(self, body):
        self.comments.append(SimpleNamespace(body=body))


class CabinetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original = Path.cwd()
        os.chdir(self.temp.name)
        Path("CabinetDirectives.md").write_text("# Cabinet Directives\n")
        cabinet.update_register(entry())
        Path("SKILL.md").write_text("Repository skill: screenshots are required.")

    def tearDown(self):
        os.chdir(self.original)
        self.temp.cleanup()

    def capture(self, direction="Departments must report annually. ", **kwargs):
        manifest = cabinet.read_manifest()
        event = cabinet.capture(entry(), cabinet.parse_source(html(direction), URL), manifest,
                                detected="2026-10-22", **kwargs)
        cabinet.save_manifest(manifest)
        return event

    def test_url_validation_rejects_non_government_and_credentials(self):
        for url in ["http://www.canada.ca/x", "https://canada.ca.evil.test/x", "https://localhost/x",
                    "https://user:pass@www.canada.ca/x", "https://www.canada.ca:8443/x"]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                cabinet.validate_url(url)
        self.assertEqual(cabinet.validate_url(OLD_URL), OLD_URL)

    def test_redirect_is_validated_before_following(self):
        response = SimpleNamespace(is_redirect=True, headers={"Location": "https://localhost/private"}, raise_for_status=lambda: None)
        with mock.patch.object(cabinet.requests, "get", return_value=response) as get:
            with self.assertRaises(ValueError):
                cabinet.fetch_source(URL)
        self.assertEqual(get.call_count, 1)

    def test_normalization_ignores_navigation_and_page_date(self):
        first = cabinet.parse_source(html(), URL)
        second = cabinet.parse_source(html(modified="2026-10-23").replace("Volatile navigation", "New navigation"), URL)
        self.assertEqual(first["markdown"], second["markdown"])
        self.assertNotEqual(first["modified"], second["modified"])
        self.assertIn("## 1. Obligations", first["markdown"])

    def test_error_or_overview_page_rejected(self):
        for text in ["<main><h1>Request rejected</h1></main>", "<main><h1>Strategic Environmental Assessment</h1><p>Overview</p></main>",
                     "<main><h1>Cabinet Directive</h1><p>Access denied</p></main>"]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                cabinet.parse_source(text, URL)

    def test_register_roundtrip_preserves_prose_and_validates_status(self):
        with Path("CabinetDirectives.md").open("a") as handle:
            handle.write("\nAnalyst notes survive.\n")
        updated = entry()
        updated["Status"] = "Announced"
        cabinet.update_register(updated)
        self.assertEqual(cabinet.read_register()[0]["Status"], "Announced")
        self.assertIn("Analyst notes survive.", Path("CabinetDirectives.md").read_text())
        Path("CabinetDirectives.md").write_text(Path("CabinetDirectives.md").read_text().replace("Announced", "Made up"))
        with self.assertRaises(ValueError):
            cabinet.read_register()

    def test_sync_is_byte_stable_and_preserves_pending_events(self):
        with mock.patch.object(cabinet, "fetch_source", return_value=html()):
            cabinet.sync_sources()
            before = {p: p.read_bytes() for p in Path(".").rglob("*") if p.is_file()}
            cabinet.sync_sources()
        self.assertEqual(before, {p: p.read_bytes() for p in Path(".").rglob("*") if p.is_file()})
        self.assertEqual(len(cabinet.read_manifest()["events"]), 1)

    def test_sync_page_modified_only_updates_register_without_an_issue(self):
        self.capture()
        with mock.patch.object(cabinet, "fetch_source", return_value=html(modified="2026-10-23")):
            cabinet.sync_sources()
        self.assertEqual(len(cabinet.read_manifest()["events"]), 1)
        self.assertEqual(cabinet.read_register()[0]["Date last modified"], "2026-10-23")

    def test_changed_capture_has_immutable_before_after_and_reversion(self):
        first = self.capture()
        first_bytes = Path(first["current"]).read_bytes()
        second = self.capture("Departments must report monthly. ")
        third = self.capture()
        self.assertEqual(second["change_type"], "changed")
        self.assertEqual(Path(second["previous"]).read_bytes(), first_bytes)
        self.assertEqual(Path(first["current"]).read_bytes(), first_bytes)
        self.assertEqual(Path(third["current"]).read_bytes(), first_bytes)
        self.assertEqual(len(cabinet.read_manifest()["events"]), 3)

    def test_failed_batch_leaves_baseline_and_register_unchanged(self):
        self.capture()
        cabinet.update_register(entry(OLD_URL))
        before = {p: p.read_bytes() for p in Path(".").rglob("*") if p.is_file()}
        with mock.patch.object(cabinet, "fetch_source", side_effect=[html("Changed obligations. "), "<main>Error</main>"]):
            with self.assertRaises(ValueError):
                cabinet.sync_sources()
        self.assertEqual(before, {p: p.read_bytes() for p in Path(".").rglob("*") if p.is_file()})

    def test_truncated_page_does_not_replace_baseline(self):
        self.capture("This is an extensive detailed statutory obligation and reporting clause. " * 5)
        before = cabinet.MANIFEST.read_bytes()
        with mock.patch.object(cabinet, "fetch_source", return_value=html()):
            with self.assertRaisesRegex(ValueError, "shrink"):
                cabinet.sync_sources()
        self.assertEqual(cabinet.MANIFEST.read_bytes(), before)

    def test_loader_rejects_evidence_outside_change_directory(self):
        event = self.capture()
        metadata = Path(event["current"]).with_name("change.json")
        event["current"] = "CabinetDirectives.md"
        metadata.write_text(json.dumps(event))
        with self.assertRaises(ValueError):
            enrichment.load_event(str(metadata))

    def test_manual_issue_registers_source_and_retry_reuses_capture(self):
        body = f"- [x] New:\n\nLink to published html:  \n{URL}\n\n- [ ] replaces:\n\nLink to supercede Cab Dir (if applicable):\n"
        with mock.patch.object(cabinet, "fetch_source", return_value=html()) as fetch:
            first = enrichment.prepare_manual_issue(FakeIssue(), body)
            second = enrichment.prepare_manual_issue(FakeIssue(), body)
        self.assertEqual(first, second)
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(first["issue_number"], 123)

    def test_manual_future_replacement_retains_in_force_predecessor(self):
        self.capture()
        body = (f"- [x] replaces:\nLink to published html: {OLD_URL}\n"
                f"Link to supercede Cab Dir (if applicable): {URL}\n"
                "- Status: In Force\n- Date of effect: 2026-12-31\n")
        with mock.patch.object(cabinet, "fetch_source", return_value=html("Future new directive. ")):
            event = enrichment.prepare_manual_issue(FakeIssue(), body)
        entries = {e['url']: e for e in cabinet.read_register()}
        self.assertEqual(event["change_type"], "replacement")
        self.assertEqual(entries[OLD_URL]["Status"], "Announced")
        self.assertEqual(entries[URL]["Status"], "In Force")
        self.assertTrue(Path(event["previous"]).is_file())

    def test_manual_replacement_needs_checkbox_and_predecessor(self):
        for body in [f"- [x] replaces:\nLink to published html: {URL}",
                     f"Link to published html: {URL}\nLink to supercede Cab Dir (if applicable): {OLD_URL}"]:
            with self.subTest(body=body), self.assertRaises(ValueError):
                enrichment.prepare_manual_issue(FakeIssue(), body)

    def test_confirmed_replacement_updates_predecessor_status_and_links(self):
        self.capture()
        body = (f"- [x] replaces:\nLink to published html: {OLD_URL}\n"
                f"Link to supercede Cab Dir (if applicable): {URL}\n")
        source = html("This Directive replaces the Cabinet Directive on Testing. ")
        with mock.patch.object(cabinet, "fetch_source", return_value=source):
            event = enrichment.prepare_manual_issue(FakeIssue(), body)
        entries = {e['url']: e for e in cabinet.read_register()}
        self.assertEqual(entries[URL]["Status"], "Superseded")
        self.assertEqual(event["replacement_status"], "in effect")
        self.assertIn(f"]({OLD_URL})", cabinet.REGISTER.read_text())
        self.assertEqual(enrichment.load_event(str(Path(event['current']).with_name('change.json')))["replacement_status"], "in effect")

    def test_missing_manifest_does_not_rebaseline_existing_captures(self):
        self.capture()
        cabinet.MANIFEST.unlink()
        with self.assertRaisesRegex(ValueError, "manifest is missing"):
            cabinet.read_manifest()

    def test_manual_untracked_predecessor_is_captured_once_without_extra_issue(self):
        body = (f"- [x] replaces:\nLink to published html: {OLD_URL}\n"
                f"Link to supercede Cab Dir (if applicable): {URL}\n")
        with mock.patch.object(cabinet, "fetch_source", return_value=html()) as fetch:
            event = enrichment.prepare_manual_issue(FakeIssue(), body)
        self.assertEqual(fetch.call_count, 2)
        self.assertEqual(len(cabinet.read_manifest()["events"]), 1)
        self.assertIn("not a historical before-state", event["previous_evidence_basis"])
        self.assertTrue(Path(event["previous"]).with_suffix('.html').exists())

    def test_screenshot_failure_prevents_analysis_comment_report_and_completion(self):
        event = self.capture()
        issue = FakeIssue()
        body = f"**Cabinet metadata:** {Path(event['current']).with_name('change.json')}"
        with mock.patch.object(enrichment, "capture_screenshots", side_effect=RuntimeError("screenshot failed")), mock.patch.object(enrich_issue, "generate_gemini_summary") as model:
            with self.assertRaisesRegex(RuntimeError, "screenshot failed"):
                enrichment.enrich_cabinet_issue(issue, body, "owner/repo")
        model.assert_not_called()
        self.assertEqual(issue.comments, [])
        self.assertEqual(list(Path('.').glob('PolicyEvolution*.md')), [])

    def test_analysis_uses_skill_and_images_and_active_quarter_idempotently(self):
        event = self.capture()
        issue = FakeIssue()
        body = f"**Cabinet metadata:** {Path(event['current']).with_name('change.json')}"
        image = Path("screenshots/current.png")
        image.parent.mkdir()
        image.write_bytes(b"image bytes")
        output = Path("step-output")
        analysis = ("## Policy change analysis\n\n### Summary\nFirst capture of an older instrument.\n"
                    "### Substantive changes identified\n| Before | After |\n|---|---|\n| No prior capture | Direction |\n"
                    "### Practical effect\nAssess obligations.\n### Non-substantive changes\nNone.\n### Watch item\nNone.")
        with mock.patch.object(enrichment, "capture_screenshots", return_value=[image]), mock.patch.object(enrich_issue, "generate_gemini_summary", return_value=analysis) as model, mock.patch.dict(os.environ, {"GEMINI_API_KEY": "test-key", "GITHUB_OUTPUT": str(output)}):
            enrichment.enrich_cabinet_issue(issue, body, "owner/repo")
            enrichment.enrich_cabinet_issue(issue, body, "owner/repo")
        model.assert_called_once()
        self.assertIn("Repository skill", model.call_args.args[1])
        self.assertEqual(model.call_args.kwargs["image_paths"], [image])
        report = Path("PolicyEvolution2026-27Q3.md").read_text()
        self.assertIn("**Category:** Cabinet Directive", report)
        self.assertIn("screenshots/current.png", report)
        self.assertEqual(report.count("policy-hawk:issue-123:start"), 1)
        self.assertEqual(len(issue.comments), 3)
        self.assertIn("cabinet_autoanalyzed=true", output.read_text())

    def test_outbox_recovers_issue_and_retries_until_completion_label(self):
        event = self.capture()
        issue = FakeIssue(body=f"<!-- policy-hawk:cabdir:{event['guid']} -->", labels=[cabinet.LABEL])
        repo = mock.Mock(default_branch="main")
        repo.get_labels.return_value = [SimpleNamespace(name=cabinet.LABEL), SimpleNamespace(name="policy-update"), SimpleNamespace(name="🪄📝AutoAnalyzed")]
        repo.get_issues.return_value = [issue]
        repo.get_issue.return_value = issue
        from scripts import create_issues_with_screenshots
        with mock.patch("github.Github") as client, mock.patch.object(create_issues_with_screenshots, "dispatch_enrichment", return_value=True) as dispatch, mock.patch.dict(os.environ, {"GITHUB_TOKEN": "test", "GITHUB_REPOSITORY": "owner/repo"}):
            client.return_value.get_repo.return_value = repo
            cabinet.publish_issues()
            cabinet.publish_issues()
            self.assertEqual(dispatch.call_count, 2)
            self.assertFalse(cabinet.read_manifest()["events"][event["guid"]]["complete"])
            issue.labels.append(SimpleNamespace(name="🪄📝AutoAnalyzed"))
            cabinet.publish_issues()
            self.assertEqual(dispatch.call_count, 2)
        repo.create_issue.assert_not_called()
        self.assertTrue(cabinet.read_manifest()["events"][event["guid"]]["complete"])


if __name__ == "__main__":
    unittest.main()
