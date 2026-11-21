import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parents[1]))
import qa_org_provision as p


class ProvisionTests(unittest.TestCase):
    def backend(self, journal, rolled_out=True):
        def call(path, method='GET', body=None):
            state = json.loads(journal.read_text())
            if method == 'GET':
                if '/organizations/?name=' in path:
                    return {'organizations': [{'id': 'org', 'name': state['name'], 'description': state['fingerprint']}]}
                if path.endswith('/subscriptions'):
                    return {'data': [{'id': 'subscription'}]}
                if path.endswith('/assessment'):
                    return {'canRequireAppAssessment': rolled_out}
                return {'organization': {'description': state['fingerprint']}}
            if path.endswith('/users'):
                return {'organizationUser': {'userId': 'learner'}}
            if path.endswith('/scheduled-assessments'):
                return {'id': 'schedule', 'requireAppAssessment': True}
        return call

    def test_success_creates_paired_fixture_without_e2e_endpoint(self):
        with tempfile.TemporaryDirectory() as d:
            journal = Path(d)/'journal.json'
            with patch.object(p.q, 'request', side_effect=self.backend(journal)) as request:
                result = p.provision(journal, 'holder', 'product', 'korean-english')
            self.assertEqual(result['learner'], 'learner')
            self.assertTrue(result['schedule']['requireAppAssessment'])
            self.assertFalse(any('/e2e/' in call.args[0] for call in request.call_args_list))
            self.assertEqual(journal.stat().st_mode & 0o777, 0o600)

    def test_rollout_block_then_resume_does_not_duplicate_users_or_seats(self):
        with tempfile.TemporaryDirectory() as d:
            journal = Path(d)/'journal.json'
            with patch.object(p.q, 'request', side_effect=self.backend(journal, False)), self.assertRaisesRegex(RuntimeError, 'rollout is OFF'):
                p.provision(journal, 'holder', 'product', 'korean-english')
            self.assertNotIn('schedule', json.loads(journal.read_text()))
            with patch.object(p.q, 'request', side_effect=self.backend(journal)) as request:
                p.provision(journal, 'holder', 'product', 'korean-english')
            self.assertFalse(any(call.args[0].endswith('/users') or 'subscription-assignments/' in call.args[0]
                                 for call in request.call_args_list))

    def test_ambiguous_post_is_not_retried(self):
        with tempfile.TemporaryDirectory() as d:
            journal = Path(d)/'journal.json'
            with patch.object(p.q, 'request', side_effect=TimeoutError), self.assertRaises(TimeoutError):
                p.provision(journal, 'holder', 'product', 'korean-english')
            with patch.object(p.q, 'request') as request, self.assertRaisesRegex(RuntimeError, 'Reconcile pending'):
                p.provision(journal, 'holder', 'product', 'korean-english')
            request.assert_not_called()

    def test_plain_text_created_is_success_not_retryable_parse_error(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'Created'
        with patch.dict('os.environ', QA_ORG_ACCESS_TOKEN='test'), patch('urllib.request.urlopen', return_value=response):
            self.assertIsNone(p.q.request('/v1/partners/admin/organizations/', 'POST', {}))
            with self.assertRaises(json.JSONDecodeError):
                p.q.request('/v1/partners/admin/organizations/', 'GET')
