import unittest
from types import SimpleNamespace

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

    def test_returns_empty_when_all_sources_fail(self):
        def parser(_):
            return SimpleNamespace(bozo=True, bozo_exception=Exception('unavailable'), entries=[])

        entries, source = fetch_feed.fetch_entries_with_fallback(parser=parser)
        self.assertEqual(source, 'fallback')
        self.assertEqual(entries, [])


if __name__ == '__main__':
    unittest.main()
