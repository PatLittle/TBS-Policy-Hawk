import unittest

from scripts import policy_sources
from scripts import create_issues_with_screenshots


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
