import importlib.util
import pathlib
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('qa_org', pathlib.Path(__file__).parents[1] / 'qa_org.py')
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)

class OrganizationPoolTests(unittest.TestCase):
    def manifest(self):
        provenance = {'source': q.SOURCE, 'created_by': 'test', 'nonce': 'unique'}
        return dict(base_url=q.BASE, provenance=provenance, fingerprint=q.fingerprint(provenance),
                    organization_id='org123', profile='required', learner_user_id='dedicated',
                    checks=[dict(path='/v1/fixture', pointer='/required', equals=True)])

    def test_fingerprint_is_order_independent_and_detects_edits(self):
        self.assertEqual(q.fingerprint({'a': 1, 'b': 2}), q.fingerprint({'b': 2, 'a': 1}))
        self.assertNotEqual(q.fingerprint({'a': 1}), q.fingerprint({'a': 2}))

    def test_rejects_wrong_backend_before_request(self):
        m = self.manifest(); m['base_url'] = 'https://production.invalid'
        with patch.object(q, 'request') as req, self.assertRaises(ValueError):
            q.validate(m)
        req.assert_not_called()

    def test_rejects_missing_remote_fingerprint(self):
        with patch.object(q, 'request', return_value={'organization': {'description': 'customer'}}), self.assertRaises(ValueError):
            q.validate(self.manifest())

    def test_backend_state_must_match(self):
        m = self.manifest()
        with patch.object(q, 'request', side_effect=[{'organization': {'description': m['fingerprint']}}, {'required': False}]), self.assertRaises(ValueError):
            q.validate(m)

    def test_verified_fixture(self):
        m = self.manifest()
        with patch.object(q, 'request', side_effect=[{'organization': {'description': m['fingerprint']}}, {'required': True}]):
            q.validate(m)

    def test_stale_release_refused(self):
        with patch.object(q, 'bq', return_value=[]), self.assertRaises(RuntimeError):
            q.fence({'organization_id': 'org123', 'token': 'old'}, 'quarantined')

    def test_claim_never_recycles_expired_lease(self):
        with patch.object(q, 'bq', return_value=[]) as query:
            q.claim('required', 'run', 'nonce')
        sql = query.call_args.args[0]
        self.assertIn('BEGIN TRANSACTION', sql)
        self.assertIn("state='ready'", sql)
        self.assertNotIn('TIMESTAMP_SUB', sql)
        self.assertIn("organization_id='__registry__'", sql)

    def test_dml_row_count_is_not_a_json_error(self):
        import subprocess
        result = subprocess.CompletedProcess([], 0, 'Number of affected rows: 1', '')
        with patch.object(q.subprocess, 'run', return_value=result):
            self.assertEqual(q.bq('MERGE table USING (SELECT 1) ON FALSE'), [])

    def test_json_pointer(self):
        self.assertEqual(q.pointer({'a/b': [{'~key': True}]}, '/a~1b/0/~0key'), True)

if __name__ == '__main__':
    unittest.main()
