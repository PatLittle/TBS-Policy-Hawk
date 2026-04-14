import unittest
from types import SimpleNamespace
from unittest.mock import patch

from scripts import fetch_feed


class FakeEntry(dict):
    def __getattr__(self, item):
        return self[item]


class FetchFeedFallbackTests(unittest.TestCase):
    def test_uses_primary_when_available(self):
        primary_entries = [
            FakeEntry(guid='g1', title='Policy A', link='https://example/a', published='Mon, 01 Jan 2024 10:00:00 GMT', category='Policy')
        ]

        def parser(url):
            if url == fetch_feed.RSS_URL:
                return SimpleNamespace(bozo=False, entries=primary_entries)
            self.fail('Fallback feeds should not be called when primary succeeds')

        entries, source = fetch_feed.fetch_entries_with_fallback(parser=parser)
        self.assertEqual(source, 'primary')
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['guid'], 'g1')

    def test_falls_back_and_deduplicates_by_guid(self):
        def parser(url):
            if url == fetch_feed.RSS_URL:
                return SimpleNamespace(bozo=True, bozo_exception=Exception('broken'), entries=[])
            if 'type=79' in url:
                return SimpleNamespace(bozo=False, entries=[
                    FakeEntry(guid='g1', title='Old', link='https://example/old', published='Mon, 01 Jan 2024 10:00:00 GMT', category='Framework')
                ])
            if 'type=27' in url:
                return SimpleNamespace(bozo=False, entries=[
                    FakeEntry(guid='g1', title='New', link='https://example/new', published='Tue, 02 Jan 2024 10:00:00 GMT', category='Policy'),
                    FakeEntry(guid='g2', title='Policy B', link='https://example/b', published='Wed, 03 Jan 2024 10:00:00 GMT', category='Policy'),
                ])
            return SimpleNamespace(bozo=False, entries=[])

        entries, source = fetch_feed.fetch_entries_with_fallback(parser=parser)
        self.assertEqual(source, 'fallback')
        self.assertEqual([entry['guid'] for entry in entries], ['g2', 'g1'])
        guid1 = next(e for e in entries if e['guid'] == 'g1')
        self.assertEqual(guid1['title'], 'New')

    @patch('scripts.fetch_feed.fetch_entries_from_modifications_table')
    def test_uses_modifications_table_when_all_rss_sources_fail(self, mock_table):
        mock_table.return_value = [
            {'guid': 'g3', 'title': 'Policy C', 'link': 'https://example/c', 'pubDate': '2026-03-12', 'category': 'Policy'}
        ]

        def parser(_):
            return SimpleNamespace(bozo=True, bozo_exception=Exception('unavailable'), entries=[])

        entries, source = fetch_feed.fetch_entries_with_fallback(parser=parser)
        self.assertEqual(source, 'modifications-table')
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['guid'], 'g3')

    @patch('scripts.fetch_feed.fetch_entries_from_modifications_table')
    def test_returns_empty_when_all_sources_fail(self, mock_table):
        mock_table.return_value = []

        def parser(_):
            return SimpleNamespace(bozo=True, bozo_exception=Exception('unavailable'), entries=[])

        entries, source = fetch_feed.fetch_entries_with_fallback(parser=parser)
        self.assertEqual(source, 'fallback')
        self.assertEqual(entries, [])


class ModificationsTableParsingTests(unittest.TestCase):
    def test_extracts_rows_and_normalizes_fields(self):
        html = """
        <table id="results-table">
          <tbody>
            <tr>
              <td>
                <h2><a href="doc-eng.aspx?id=32728">Making Communications Products and Activities Accessible, Guidelines on</a></h2>
                <p class="text-muted">Guidelines | <a href="#">Communications and Federal Identity</a></p>
              </td>
              <td>2026-03-12</td>
            </tr>
          </tbody>
        </table>
        """

        class FakeResponse:
            def __init__(self, text):
                self.text = text

            def raise_for_status(self):
                return None

        def getter(url, timeout, headers):
            return FakeResponse(html)

        entries = fetch_feed.fetch_entries_from_modifications_table(getter=getter)
        self.assertEqual(len(entries), 1)
        row = entries[0]
        self.assertEqual(row['guid'], '32728')
        self.assertEqual(row['category'], 'Guidelines')
        self.assertEqual(row['pubDate'], 'Thu, 12 Mar 2026 00:00:00 GMT')
        self.assertEqual(row['link'], 'https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32728')

    def test_normalizes_french_categories(self):
        self.assertEqual(fetch_feed.normalize_category('Politique'), 'Policy')
        self.assertEqual(fetch_feed.normalize_category('Directive'), 'Directive')
        self.assertEqual(fetch_feed.normalize_category('Cadre stratégique'), 'Framework')


if __name__ == '__main__':
    unittest.main()
