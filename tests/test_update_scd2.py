import unittest
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

from scripts import update_scd2


class UpdateSCD2FallbackTests(unittest.TestCase):
    @patch('scripts.update_scd2.requests.get')
    @patch('scripts.update_scd2.feedparser.parse')
    def test_uses_modifications_table_when_rss_unavailable(self, mock_parse, mock_get):
        # Primary and instrument feeds unavailable for both languages.
        mock_parse.return_value = SimpleNamespace(bozo=True, entries=[])

        html_en = """
        <table id='results-table'><tbody>
          <tr>
            <td>
              <h2><a href='doc-eng.aspx?id=32728'>Making Communications Products and Activities Accessible, Guidelines on</a></h2>
              <p class='mrgn-bttm-0'>English summary text.</p>
            </td>
            <td>2026-03-12</td>
          </tr>
        </tbody></table>
        """
        html_fr = """
        <table id='results-table'><tbody>
          <tr>
            <td>
              <h2><a href='doc-fra.aspx?id=32728'>Rendre les produits et activités de communication accessibles, Lignes directrices sur</a></h2>
              <p class='mrgn-bttm-0'>Résumé français.</p>
            </td>
            <td>2026-03-12</td>
          </tr>
        </tbody></table>
        """

        class FakeResponse:
            def __init__(self, text):
                self.text = text
                self.content = text.encode('utf-8')

            def raise_for_status(self):
                return None

        def fake_get(url, timeout=60, headers=None):
            if 'modifications-eng.aspx' in url:
                return FakeResponse(html_en)
            if 'modifications-fra.aspx' in url:
                return FakeResponse(html_fr)
            # Final parse_rss fallback should not be hit in this test.
            raise AssertionError(f'unexpected URL requested: {url}')

        mock_get.side_effect = fake_get

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(update_scd2, 'TMP_SNAPSHOT', Path(tmpdir) / 'snapshot.csv'):
                df = update_scd2.fetch_and_union()
        self.assertEqual(len(df), 1)
        row = df.iloc[0]
        self.assertEqual(row['guid'], '32728')
        self.assertIn('doc-eng.aspx?id=32728', row['link_en'])
        self.assertIn('doc-fra.aspx?id=32728', row['link_fr'])
        self.assertEqual(row['description_en'], 'English summary text.')
        self.assertEqual(row['description_fr'], 'Résumé français.')


if __name__ == '__main__':
    unittest.main()
