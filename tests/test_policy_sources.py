import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import requests

from scripts import policy_sources
from scripts import create_issues_with_screenshots
from scripts import fetch_feed


class PolicySourcesHierarchyTests(unittest.TestCase):
    def test_compares_hierarchy_additions_and_removals(self):
        previous = [
            {"ID": "1", "Name": "Old Policy", "URL": "https://example/old"},
            {"ID": "2", "Name": "Existing Policy", "URL": "https://example/existing"},
        ]
        current = [
            {"ID": "2", "Name": "Existing Policy", "URL": "https://example/existing"},
            {"ID": "3", "Name": "New Directive", "URL": "https://example/new"},
        ]

        changes = policy_sources.compare_hierarchy(previous, current)

        self.assertEqual([row["ID"] for row in changes["added"]], ["3"])
        self.assertEqual([row["ID"] for row in changes["removed"]], ["1"])

    def test_fetch_hierarchy_uses_redirected_document_id(self):
        html = """
        <html><body>
        <main>
          <ul class="tv-ul">
            <li><a href="doc-eng.aspx?id=100">Old title, Policy on</a></li>
          </ul>
        </main>
        <dl id="wb-dtmd"><dt>Date modified:</dt><dd><time property="dateModified">2026-07-01</time></dd></dl>
        </body></html>
        """

        class FakeResponse:
            def __init__(self, text="", url="https://www.tbs-sct.canada.ca/pol/hierarch-eng.aspx"):
                self.text = text
                self.url = url

            def raise_for_status(self):
                return None

        def getter(url, **_kwargs):
            if "hierarch-eng.aspx" in url:
                return FakeResponse(html)
            return FakeResponse("", "https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=200")

        records = policy_sources.fetch_hierarchy_records(getter=getter, resolve_redirects=True)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["ID"], "200")
        self.assertEqual(records[0]["original_id"], "100")

    def test_fetch_hierarchy_retries_transient_timeout(self):
        html = """
        <html><body>
        <main>
          <ul class="tv-ul">
            <li><a href="doc-eng.aspx?id=100">Recovered Policy</a></li>
          </ul>
        </main>
        </body></html>
        """

        class FakeResponse:
            text = html
            url = "https://www.tbs-sct.canada.ca/pol/hierarch-eng.aspx"

            def raise_for_status(self):
                return None

        calls = {"count": 0}

        def getter(url, **_kwargs):
            calls["count"] += 1
            if calls["count"] == 1:
                raise requests.ReadTimeout("slow hierarchy page")
            return FakeResponse()

        records = policy_sources.fetch_hierarchy_records(
            getter=getter,
            resolve_redirects=False,
            retry_backoff_seconds=0,
        )

        self.assertEqual(calls["count"], 2)
        self.assertEqual(records[0]["ID"], "100")

    def test_hierarchy_tree_text_includes_nested_items_and_urls(self):
        records = [
            {
                "ID": "1",
                "Name": "Root Policy",
                "URL": "https://example.test/root",
                "Hierarchy Paths": "",
            },
            {
                "ID": "2",
                "Name": "Child Directive",
                "URL": "https://example.test/child",
                "Hierarchy Paths": "Root Policy",
            },
            {
                "ID": "32750",
                "Name": "GC Digital Talent Platform",
                "URL": "https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32750",
                "Hierarchy Paths": "Root Policy > Child Directive",
            },
        ]

        tree = policy_sources.hierarchy_tree_text(records)

        self.assertIn("Root Policy [1] - https://example.test/root", tree)
        self.assertIn("Child Directive", tree)
        self.assertIn("GC Digital Talent Platform [32750] - https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32750", tree)

    def test_capture_hierarchy_changes_falls_back_without_tree_write_on_timeout(self):
        previous = [{
            "ID": "32749",
            "Name": "Digital Talent, Directive on",
            "URL": "https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32749",
            "Min Level": "3",
            "Hierarchy Paths": "Values and Ethics Code for the Public Sector",
            "Other Names": "",
        }]

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            original_csv_path = fetch_feed.HIERARCHY_CSV_PATH
            original_dir = fetch_feed.HIERARCHY_DIR
            original_tree_path = fetch_feed.HIERARCHY_TREE_PATH
            fetch_feed.HIERARCHY_CSV_PATH = str(tmp_path / "hierarchy.csv")
            fetch_feed.HIERARCHY_DIR = str(tmp_path / "Hierarchy")
            fetch_feed.HIERARCHY_TREE_PATH = str(tmp_path / "Hierarchy" / "hierarchy.txt")
            try:
                policy_sources.write_hierarchy_csv(fetch_feed.HIERARCHY_CSV_PATH, previous)

                def failing_fetcher(**_kwargs):
                    raise requests.ReadTimeout("slow hierarchy page")

                current, changes, fetched = fetch_feed.capture_hierarchy_changes(
                    "2026-07-08",
                    fetcher=failing_fetcher,
                )

                self.assertFalse(fetched)
                self.assertEqual(changes, {"added": [], "removed": []})
                self.assertEqual(current, previous)
                self.assertFalse(Path(fetch_feed.HIERARCHY_TREE_PATH).exists())
                self.assertFalse((tmp_path / "Hierarchy" / "2026-07-08_hierarchy.txt").exists())
            finally:
                fetch_feed.HIERARCHY_CSV_PATH = original_csv_path
                fetch_feed.HIERARCHY_DIR = original_dir
                fetch_feed.HIERARCHY_TREE_PATH = original_tree_path


class PolicySourcesGlossaryTests(unittest.TestCase):
    def test_parses_and_merges_bilingual_glossary_rows(self):
        html_en = """
        <main><dl>
          <dt>access request (<span lang="fr"><i>demande d'accès</i></span>)</dt>
          <dd>English definition.<footer><cite>Source: <a href="doc-eng.aspx?id=12453">Access to Information, Policy on</a></cite></footer></dd>
        </dl></main>
        <dl id="wb-dtmd"><dt>Date modified:</dt><dd><time property="dateModified">2026-07-01</time></dd></dl>
        """
        html_fr = """
        <main><dl>
          <dt>demande d'accès (<span lang="en"><i>access request</i></span>)</dt>
          <dd>Définition française.<footer><cite>Source : <a href="doc-fra.aspx?id=12453">Politique sur l'accès à l'information</a></cite></footer></dd>
        </dl></main>
        <dl id="wb-dtmd"><dt>Date modified:</dt><dd><time property="dateModified">2026-07-01</time></dd></dl>
        """

        rows_en = policy_sources.parse_glossary_html(html_en, "en")
        rows_fr = policy_sources.parse_glossary_html(html_fr, "fr")
        rows = policy_sources.merge_glossary_rows(rows_en, rows_fr)

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["source_id"], "12453")
        self.assertEqual(row["source_en"], "Access to Information, Policy on")
        self.assertEqual(row["source_fr"], "Politique sur l'accès à l'information")
        self.assertEqual(row["term_en"], "access request")
        self.assertEqual(row["term_fr"], "demande d'accès")
        self.assertEqual(row["def_en"], "English definition.")
        self.assertEqual(row["def_fr"], "Définition française.")

    def test_detects_glossary_definition_changes(self):
        previous = [{
            "source_id": "12453",
            "source_en": "Access to Information, Policy on",
            "source_fr": "",
            "term_en": "access request",
            "term_fr": "demande d'accès",
            "def_en": "Old definition.",
            "def_fr": "",
            "date_modified": "2026-01-01",
        }]
        current = [{**previous[0], "def_en": "New definition."}]

        changes = policy_sources.compare_glossary_rows(previous, current)
        payload = policy_sources.build_glossary_change_payload(changes)

        self.assertEqual(len(changes["changed"]), 1)
        self.assertIn("12453", payload["changes_by_source"])
        self.assertEqual(payload["changes_by_source"]["12453"]["changed"][0]["term_en"], "access request")


class IssueBodyTests(unittest.TestCase):
    def test_policy_issue_body_includes_related_glossary_changes(self):
        row = {
            "guid": "12453_2026-07-01",
            "title": "Access to Information, Policy on",
            "link": "https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=12453",
            "category": "Policy",
            "change_type": "policy_update",
        }
        glossary_changes = {
            "12453": {
                "source_en": "Access to Information, Policy on",
                "source_fr": "Politique sur l'accès à l'information",
                "added": [{"term_en": "new term", "term_fr": "nouveau terme"}],
                "removed": [],
                "changed": [],
            }
        }

        body = create_issues_with_screenshots.issue_body_for_row(
            row,
            screenshot_success=False,
            screenshot_url="",
            glossary_changes=glossary_changes,
        )

        self.assertIn("A new or updated policy document has been detected.", body)
        self.assertIn("### Glossary changes", body)
        self.assertIn("new term", body)


if __name__ == "__main__":
    unittest.main()
