#!/usr/bin/env python3
"""Develop-only shared organization fixtures. No credentials stored in manifests."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import urllib.request
import uuid

TABLE = '`speak-v2-2a1f1.devin_qa.qa_organization_pool`'
BASE = 'https://speak-api.alpha.usespeak.dev'
SOURCE = 'https://github.com/usespeakeasy/devin-qa-flow'
DDL = f'''CREATE TABLE IF NOT EXISTS {TABLE} (
 organization_id STRING, profile STRING, manifest STRING, fingerprint STRING,
 state STRING, holder STRING, token STRING, expires_at TIMESTAMP,
 created_at TIMESTAMP, updated_at TIMESTAMP
)'''


def bq(sql, **params):
    args = ['bq', '--project_id=speak-v2-2a1f1', '--location=US', 'query',
            '--quiet', '--nouse_legacy_sql', '--format=json',
            '--maximum_bytes_billed=1000000000']
    args += [f'--parameter={k}:STRING:{v}' for k, v in params.items()]
    for attempt in range(5):
        r = subprocess.run(args + [sql], capture_output=True, text=True)
        if not r.returncode:
            # DML without SELECT can print a non-JSON row count.
            try:
                return json.loads(r.stdout or '[]')
            except json.JSONDecodeError:
                if 'SELECT' in sql.upper():
                    raise RuntimeError('BigQuery did not return JSON')
                return []
        if 'concurrent' not in (r.stdout + r.stderr).lower():
            raise RuntimeError('BigQuery query failed (inspect CLI authentication/table access)')
        time.sleep(attempt + 1)
    raise RuntimeError('BigQuery contention retries exhausted')


def request(path, method='GET', body=None):
    if not path.startswith('/v1/') or '..' in path or '#' in path:
        raise ValueError('Only /v1/ backend paths are allowed')
    token = os.environ['QA_ORG_ACCESS_TOKEN']
    req = urllib.request.Request(BASE + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'x-access-token': token, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as response:
        data = response.read()
        return json.loads(data) if data else None


def fingerprint(provenance):
    raw = json.dumps(provenance, sort_keys=True, separators=(',', ':')).encode()
    return 'devin-qa-org:v1:' + hashlib.sha256(raw).hexdigest()


def pointer(value, path):
    if path == '':
        return value
    if not path.startswith('/'):
        raise ValueError('Check pointer must be a JSON pointer')
    for part in path[1:].split('/'):
        part = part.replace('~1', '/').replace('~0', '~')
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def validate(m):
    if m['base_url'] != BASE or m['provenance']['source'] != SOURCE:
        raise ValueError('Only this harness and the develop backend are supported')
    for key in ('organization_id', 'profile'):
        if not re.fullmatch(r'[A-Za-z0-9_-]+', m[key]):
            raise ValueError('Invalid organization/profile')
    if m['fingerprint'] != fingerprint(m['provenance']):
        raise ValueError('Provenance fingerprint mismatch')
    if not m.get('checks') or not m.get('learner_user_id'):
        raise ValueError('A dedicated learner and backend checks are required')
    org = request('/v1/partners/admin/organizations/' + m['organization_id'])['organization']
    if m['fingerprint'] not in (org.get('description') or ''):
        raise ValueError('Backend organization fingerprint does not match')
    for check in m['checks']:
        actual = pointer(request(check['path']), check['pointer'])
        if actual != check['equals']:
            raise ValueError('Backend fixture check failed: ' + check['path'])


def save(path, value):
    # Refuse overwriting a lease receipt: it is the only local fencing token.
    with open(path, 'x', opener=lambda p, f: os.open(p, f, 0o600)) as f:
        json.dump(value, f, indent=2)
        f.write('\n')


def claim(profile, holder, token):
    # Read/update in one transaction: concurrent writers conflict and retry.
    return bq(f'''DECLARE chosen STRING;
BEGIN TRANSACTION;
UPDATE {TABLE} SET updated_at=CURRENT_TIMESTAMP() WHERE organization_id='__registry__';
SET chosen = (SELECT organization_id FROM {TABLE}
 WHERE profile=@profile AND state='ready' ORDER BY created_at LIMIT 1);
UPDATE {TABLE} SET state='leased', holder=@holder, token=@token,
 expires_at=TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 4 HOUR), updated_at=CURRENT_TIMESTAMP()
 WHERE organization_id=chosen AND state='ready';
COMMIT TRANSACTION;
SELECT * FROM {TABLE} WHERE token=@token AND state='leased';''',
        profile=profile, holder=holder, token=token)


def fence(receipt, state):
    rows = bq(f'''UPDATE {TABLE} SET state=@state, updated_at=CURRENT_TIMESTAMP()
 WHERE organization_id=@org AND token=@token AND state='leased';
SELECT state FROM {TABLE} WHERE organization_id=@org AND token=@token;''',
        state=state, org=receipt['organization_id'], token=receipt['token'])
    if len(rows) != 1 or rows[0]['state'] != state:
        raise RuntimeError('Stale or lost lease: no mutation authorized')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    s.add_parser('init')
    c = s.add_parser('stamp'); c.add_argument('--holder', required=True); c.add_argument('--output', required=True)
    c = s.add_parser('register'); c.add_argument('manifest')
    c = s.add_parser('reset'); c.add_argument('manifest'); c.add_argument('--evidence', required=True)
    c = s.add_parser('lease'); c.add_argument('--holder', required=True); c.add_argument('--profile', required=True); c.add_argument('--receipt', required=True)
    for name in ('verify', 'renew', 'release'):
        c = s.add_parser(name); c.add_argument('--receipt', required=True)
    a = p.parse_args()
    if a.cmd == 'init':
        bq(DDL)
        bq(f"""MERGE {TABLE} t USING (SELECT '__registry__' AS id) s ON t.organization_id=s.id
WHEN NOT MATCHED THEN INSERT (organization_id,state,updated_at) VALUES (s.id,'lock',CURRENT_TIMESTAMP())"""); return
    if a.cmd == 'stamp':
        provenance = dict(source=SOURCE, created_by=a.holder,
            created_at=dt.datetime.now(dt.timezone.utc).isoformat(), nonce=str(uuid.uuid4()))
        save(a.output, dict(provenance=provenance, fingerprint=fingerprint(provenance)))
        return
    if a.cmd in ('register', 'reset'):
        m = json.loads(Path(a.manifest).read_text()); validate(m)
        if a.cmd == 'reset':
            token = str(uuid.uuid4())
            rows = bq(f'''BEGIN TRANSACTION;
UPDATE {TABLE} SET updated_at=CURRENT_TIMESTAMP() WHERE organization_id='__registry__';
UPDATE {TABLE} SET state='resetting',token=@token,holder=@evidence
 WHERE organization_id=@org AND fingerprint=@fp
 AND (state='quarantined' OR (state='leased' AND expires_at<CURRENT_TIMESTAMP()));
COMMIT TRANSACTION;
SELECT * FROM {TABLE} WHERE organization_id=@org AND token=@token AND state='resetting';''',
                org=m['organization_id'], fp=m['fingerprint'], token=token, evidence=a.evidence)
            if len(rows) != 1:
                raise RuntimeError('Reset refused: active lease, unknown fixture or mismatched fingerprint')
            try:
                if json.loads(rows[0]['manifest']) != m:
                    raise ValueError('Reset cannot change the registered baseline manifest')
                validate(m)
                state = 'ready'
            except Exception:
                bq(f"UPDATE {TABLE} SET state='quarantined' WHERE organization_id=@org AND token=@token", org=m['organization_id'], token=token)
                raise
            bq(f'''UPDATE {TABLE} SET state='ready',holder=NULL,token=NULL,expires_at=NULL,
 updated_at=CURRENT_TIMESTAMP() WHERE organization_id=@org AND token=@token AND state='resetting' ''',
                org=m['organization_id'], token=token)
            return
        # The registry lock row makes concurrent registration/claim transactions conflict.
        bq(f'''BEGIN TRANSACTION;
UPDATE {TABLE} SET updated_at=CURRENT_TIMESTAMP() WHERE organization_id='__registry__';
ASSERT NOT EXISTS(SELECT 1 FROM {TABLE} WHERE organization_id=@org
 OR JSON_VALUE(manifest, '$.learner_user_id')=@learner) AS 'Fixture already registered';
INSERT INTO {TABLE} VALUES (@org,@profile,@manifest,@fp,'ready',NULL,NULL,NULL,CURRENT_TIMESTAMP(),CURRENT_TIMESTAMP());
COMMIT TRANSACTION;''', org=m['organization_id'], learner=m['learner_user_id'], profile=m['profile'], manifest=json.dumps(m), fp=m['fingerprint'])
        return
    if a.cmd == 'lease':
        if Path(a.receipt).exists():
            raise ValueError('Receipt exists; verify/renew/release it first')
        token = str(uuid.uuid4()); rows = claim(a.profile, a.holder, token)
        if len(rows) != 1:
            raise RuntimeError('No ready organization; refill/reset the pool, never fall back to a generic user')
        r = rows[0]; m = json.loads(r['manifest'])
        # Save recovery evidence before touching the backend. Failed verification quarantines.
        try:
            save(a.receipt, r)
            validate(m)
        except Exception:
            fence(r, 'quarantined'); raise
        print(json.dumps({'organization_id': r['organization_id'], 'fingerprint': r['fingerprint'],
                          'learner_user_id': m['learner_user_id'], 'expires_at': r['expires_at']}))
        return
    r = json.loads(Path(a.receipt).read_text())
    if a.cmd == 'release':
        # Mutated server state is NOT automatically reusable, including after timeout.
        fence(r, 'quarantined'); print('Quarantined for backend reset; receipt retained'); return
    rows = bq(f'''SELECT * FROM {TABLE} WHERE organization_id=@org AND token=@token
 AND state='leased' AND expires_at>CURRENT_TIMESTAMP()''', org=r['organization_id'], token=r['token'])
    if len(rows) != 1:
        raise RuntimeError('Lease expired or ownership lost; stop using this organization')
    validate(json.loads(rows[0]['manifest']))
    if a.cmd == 'renew':
        rows = bq(f'''UPDATE {TABLE} SET expires_at=TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 4 HOUR)
 WHERE organization_id=@org AND token=@token AND state='leased' AND expires_at>CURRENT_TIMESTAMP();
SELECT * FROM {TABLE} WHERE organization_id=@org AND token=@token AND state='leased' AND expires_at>CURRENT_TIMESTAMP();''', org=r['organization_id'], token=r['token'])
        if len(rows) != 1:
            raise RuntimeError('Lease expired while renewing')
    print('Lease and backend fixture verified')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # Never dump HTTP bodies, tokens, manifests or CLI stderr to QA reports.
        raise SystemExit(f'{type(exc).__name__}: {exc}')
