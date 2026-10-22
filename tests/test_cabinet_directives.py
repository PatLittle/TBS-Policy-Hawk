import csv
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from scripts import cabinet_directives as cabinet
from scripts import enrich_issue
from scripts import create_issues_with_screenshots as issues

URL = 'https://www.canada.ca/en/test/cabinet.html'
OTHER = 'https://www.canada.ca/en/test/replacement.html'


def html(text='Departments coordinate implementation and report on results. ', modified='2026-10-22'):
    return (f'<html><head><meta name="dcterms.issued" content="2018-06-28">'
            f'<meta name="dcterms.modified" content="{modified}"></head><body><nav>Navigation</nav>'
            '<main><h1>Cabinet Directive on Testing</h1><h2>1. Direction</h2><p>' + text * 20 + '</p>'
            f'<div class="pagedetails">Date modified: {modified}</div></main></body></html>')


def source(text='Departments coordinate implementation and report on results. ', modified='2026-10-22', url=URL):
    return dict(cabinet.parse_source(html(text, modified), url), resolved_url=url)


def entry(url=URL, archive='CD_Test20180628'):
    return {'title': 'Cabinet Directive on Testing', 'url': url, 'Status': 'In Force',
            'Date Published': '2018-06-28', 'Date of effect': 'Unknown',
            'Date last modified': '2026-10-22', 'Archive': archive}


class CabinetMonitoringTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original = Path.cwd()
        os.chdir(self.temp.name)
        cabinet.REGISTER.write_text('# Cabinet Directives\n')
        cabinet.update_register(entry())

    def tearDown(self):
        os.chdir(self.original)
        self.temp.cleanup()

    def sync(self, value=None, failure=None):
        with mock.patch.object(cabinet, 'fetch_source', side_effect=failure, return_value=value or source()):
            cabinet.sync_sources()

    def rows(self):
        path=Path('data/new_items.csv')
        return list(csv.DictReader(path.open())) if path.exists() else []

    def test_first_capture_is_quiet_baseline_and_repeat_is_byte_stable(self):
        self.sync()
        manifest=cabinet.read_manifest()
        event=next(iter(manifest['events'].values()))
        self.assertEqual(event['change_type'], 'baseline')
        self.assertEqual(cabinet.read_register()[0]['Archive'],'CD_Test20180628')
        self.assertTrue(event['complete'])
        self.assertIn('CD_Test20180628/captures/20261022/current.md',event['current'])
        self.assertEqual(self.rows(),[])
        before={str(p):p.read_bytes() for p in Path('.').rglob('*') if p.is_file()}
        self.sync()
        self.assertEqual(before,{str(p):p.read_bytes() for p in Path('.').rglob('*') if p.is_file()})

    def test_content_change_uses_common_handoff_and_survives_handoff_loss(self):
        self.sync(); self.sync(source('Departments now submit quarterly results. '))
        row=self.rows()[0]
        self.assertEqual(row['change_type'],'cabinet')
        self.assertEqual(row['change_summary'],'changed')
        event=json.loads(Path(row['filename']).read_text())
        self.assertTrue(Path(event['previous']).is_file())
        Path('data/new_items.csv').unlink()
        self.sync(source('Departments now submit quarterly results. '))
        self.assertEqual(self.rows()[0]['guid'],row['guid'])
        Path('data/issue_map.json').write_text(json.dumps({row['guid']:12}))
        Path('data/new_items.csv').unlink()
        self.sync(source('Departments now submit quarterly results. '))
        self.assertEqual(self.rows(),[])

    def test_modified_only_change_updates_register_without_policy_event(self):
        self.sync(); self.sync(source(modified='2026-10-23'))
        self.assertEqual(self.rows(),[])
        self.assertEqual(len(cabinet.read_manifest()['events']),1)
        self.assertEqual(cabinet.read_register()[0]['Date last modified'],'2026-10-23')

    def test_two_explicit_missing_pages_queue_once_preserve_source_and_legal_status(self):
        self.sync(); baseline=cabinet.read_manifest()['sources'][cabinet.identity(URL)]['current']
        error=cabinet.requests.HTTPError(response=SimpleNamespace(status_code=404))
        self.sync(failure=error); self.assertEqual(self.rows(),[])
        self.sync(failure=error); row=self.rows()[0]
        self.assertEqual(row['change_summary'],'unavailable')
        self.assertTrue(Path(baseline).is_file())
        self.assertEqual(cabinet.read_register()[0]['Status'],'In Force')
        before=cabinet.MANIFEST.read_bytes(); self.sync(failure=error)
        self.assertEqual(len(self.rows()),1); self.assertEqual(cabinet.MANIFEST.read_bytes(),before)

    def test_soft404_confirmation_and_recovery(self):
        self.sync()
        self.sync(failure=cabinet.SourceUnavailable('Soft 404'))
        self.sync(failure=cabinet.SourceUnavailable('Soft 404'))
        self.sync()
        self.assertEqual([r['change_summary'] for r in self.rows()],['unavailable','restored'])
        self.assertNotIn('availability',cabinet.read_manifest()['sources'][cabinet.identity(URL)])

    def test_timeout_does_not_prove_removal_and_interrupts_pending_confirmation(self):
        self.sync(); baseline=cabinet.read_manifest()['sources'][cabinet.identity(URL)]['current']
        error=cabinet.requests.HTTPError(response=SimpleNamespace(status_code=410))
        self.sync(failure=error)
        self.sync(failure=cabinet.requests.ReadTimeout('source timeout'))
        self.sync(failure=error)
        self.assertEqual(self.rows(),[])
        self.assertTrue(Path(baseline).is_file())

    def test_invalid_or_truncated_source_retains_baseline(self):
        self.sync(); baseline=cabinet.read_manifest()['sources'][cabinet.identity(URL)]['current']
        self.sync(failure=ValueError('Request rejected'))
        shortened=source();shortened['markdown']='# Cabinet Directive\nShort.'
        self.sync(shortened)
        self.assertEqual(cabinet.read_manifest()['sources'][cabinet.identity(URL)]['current'],baseline)
        self.assertEqual(self.rows(),[])

    def test_redirect_is_reviewable_even_when_text_is_unchanged(self):
        self.sync(); moved=source();moved['resolved_url']=OTHER;self.sync(moved)
        self.assertEqual(self.rows()[0]['change_summary'],'redirected')
        self.assertEqual(cabinet.read_register()[0]['url'],URL)

    def test_user_led_shorter_replacement_has_readable_evidence_without_diff(self):
        self.sync(source('An extensive predecessor with many obligations. '*10))
        manifest=cabinet.read_manifest();new=entry(OTHER,'CD_Replacement20261021')
        new.update({'Status':'Announced','Date Published':'2026-10-21','Date of effect':'2026-12-31'})
        event=cabinet.capture(new,source(url=OTHER),manifest,detected='2026-10-22',previous_url=URL,manual_issue=527,change='replacement')
        self.assertEqual(event['change_type'],'replacement')
        self.assertIn('CD_Replacement20261021',event['current'])
        self.assertTrue(Path(event['previous']).with_suffix('.html').exists())
        self.assertFalse(Path(event['current']).with_name('diff.md').exists())
        self.assertEqual(new['Status'],'Announced')

    def test_invalid_issue_map_stops_before_mutating_sources(self):
        self.sync();before=cabinet.MANIFEST.read_bytes()
        Path('data/issue_map.json').write_text('[]')
        with self.assertRaises(ValueError):self.sync(source('Changed direction. '))
        self.assertEqual(cabinet.MANIFEST.read_bytes(),before)

    def test_missing_manifest_does_not_rebaseline_existing_archives(self):
        self.sync();cabinet.MANIFEST.unlink()
        with self.assertRaises(ValueError):cabinet.read_manifest()

    def test_source_fetch_retries_transient_failure_and_validates_redirect_target(self):
        response=SimpleNamespace(is_redirect=False,headers={'Content-Type':'text/html'},text=html(),encoding=None,raise_for_status=lambda:None)
        with mock.patch.object(cabinet.requests,'get',side_effect=[cabinet.requests.ReadTimeout(),response]) as get,mock.patch.object(cabinet.time,'sleep'):
            fetched=cabinet.fetch_source(URL)
        self.assertEqual(get.call_count,2);self.assertEqual(fetched['resolved_url'],URL)
        redirect=SimpleNamespace(is_redirect=True,headers={'Location':'https://localhost/private'},raise_for_status=lambda:None)
        with mock.patch.object(cabinet.requests,'get',return_value=redirect) as get:
            with self.assertRaises(ValueError):cabinet.fetch_source(URL)
        self.assertEqual(get.call_count,1)

    def test_successful_http_soft404_and_error_page_are_not_valid_policy_content(self):
        soft=SimpleNamespace(is_redirect=False,headers={'Content-Type':'text/html'},text='<main><h1>Page not found</h1></main>',encoding=None,raise_for_status=lambda:None)
        with mock.patch.object(cabinet.requests,'get',return_value=soft):
            with self.assertRaises(cabinet.SourceUnavailable):cabinet.fetch_source(URL)
        with self.assertRaises(ValueError):cabinet.parse_source('<main><h1>Request rejected</h1></main>',URL)

    def test_common_issue_body_is_proportionate_and_points_to_agent(self):
        self.sync();self.sync(source('Departments now report quarterly. '))
        row=self.rows()[0];body=issues.issue_body_for_row(row,False,'',{})
        self.assertIn('ordinary change review',body)
        self.assertIn('skills/cabinet-directives/SKILL.md',body)
        self.assertIn(row['filename'],body)

    def test_manual_and_automated_cabinet_issues_never_call_gemini_or_write_quarterly_reports(self):
        for body in ['Link to published HTML: '+OTHER,'**Cabinet metadata:** data/CabinetDirectives/change.json']:
            issue=mock.Mock(body=body,labels=[SimpleNamespace(name=cabinet.LABEL)],number=527)
            issue.get_comments.return_value=[]
            repo=mock.Mock();repo.get_issue.return_value=issue
            client=mock.Mock();client.get_repo.return_value=repo
            with mock.patch.dict(os.environ,{'GITHUB_REPOSITORY':'owner/repo','GITHUB_TOKEN':'test','ISSUE_NUMBER':'527'},clear=True),mock.patch.object(enrich_issue,'make_github_client',return_value=client),mock.patch.object(enrich_issue,'generate_gemini_summary') as model:
                enrich_issue.main()
            model.assert_not_called()
            issue.create_comment.assert_called_once()
            self.assertIn('agent',issue.create_comment.call_args.args[0])
            self.assertEqual(list(Path('.').glob('PolicyEvolution*.md')),[])


if __name__=='__main__':unittest.main()
