# Develop organization fixtures

`scripts/qa_org.py` is platform-neutral: the same lease is used by Android and
iOS and by both base/branch builds. It requires Python 3, authenticated `bq`,
write access to `speak-v2-2a1f1.devin_qa`, and `QA_ORG_ACCESS_TOKEN` containing a
**develop admin** access token. Tokens are read from the environment, never saved.
The backend is pinned to `https://speak-api.alpha.usespeak.dev`; production and
preview hosts are not supported. Do not put manifests/receipts in git or reports.

## Refill (operator)

1. Once, run `python3 scripts/qa_org.py init`. Run initialization serially before
   enrolling fixtures; it creates the table and the registry serialization row.
2. Generate provenance: `python3 scripts/qa_org.py stamp --holder <session-url>
   --output /private/path/stamp.json`. This records source repository, creator,
   UTC timestamp and unique nonce; SHA-256 over canonical JSON produces
   `devin-qa-org:v1:<digest>`. This identifies origin, not a cryptographic signature.
3. Use the develop admin organization creation endpoint
   `POST /v1/partners/admin/organizations/` (or Partners admin UI) to create a
   dedicated `Devin QA <profile> <nonce>` organization. Put the **entire stamp
   JSON** in its description. Set B2B/assessment flags as the scenario requires.
   Never adopt a customer/shared organization or overwrite its description.
4. Provision a dedicated, onboarded learner, active organization membership and
   seat/subscription using the backend admin tools. This learner must **not** also
   be in `qa_account_pool`, another organization fixture, or an unrelated run.
   Configure the required schedule/audience/dates for the scenario. There is no
   automatic seat/schedule provisioner in this change: backend setup remains an
   explicit operator step, not a mobile flag override.
5. Make a private manifest with the following structure (placeholders only):

```json
{
  "base_url": "https://speak-api.alpha.usespeak.dev",
  "organization_id": "REPLACE",
  "profile": "required-assessment-v1",
  "learner_user_id": "REPLACE",
  "provenance": {"source": "https://github.com/usespeakeasy/devin-qa-flow", "created_by": "SESSION_URL", "created_at": "FROM_STAMP", "nonce": "FROM_STAMP"},
  "fingerprint": "FROM_STAMP",
  "checks": [
    {"path": "/v1/partners/admin/organizations/REPLACE", "pointer": "/organization/enableB2BExperience", "equals": true},
    {"path": "/v1/partners/admin/organizations/REPLACE", "pointer": "/organization/enableStandaloneAssessments", "equals": true}
  ]
}
```

The example checks are **not sufficient for a required-assessment fixture**.
Add backend checks for the dedicated learner's membership, active seat, schedule
ID/audience, and required state using the deployed backend's response schema.
Each check is an authenticated GET plus an RFC 6901 JSON pointer and exact
expected JSON value. Verify learner-facing required/eligibility state with that
learner's authentication separately, not with the admin token. Record that evidence
in the QA report. Avoid array-position assertions on unordered collections.

6. `python3 scripts/qa_org.py register /private/path/fixture.json` verifies backend
   provenance and all checks before inserting a ready row. Enrollment rejects
   duplicate organization or learner IDs. IAM should restrict table writers to
   operators/harness; arbitrary SQL edits bypass the lifecycle guarantees.

## Run

```sh
python3 scripts/qa_org.py lease --holder SESSION_URL --profile required-assessment-v1 --receipt /private/path/run-org.json
python3 scripts/qa_org.py verify --receipt /private/path/run-org.json
python3 scripts/qa_org.py renew --receipt /private/path/run-org.json
python3 scripts/qa_org.py release --receipt /private/path/run-org.json
```

Lease output identifies organization, learner, fingerprint and expiry, not login
credentials. Mint a test sign-in code for **that learner** using approved dev
backend tools; do not create a generic test user or acquire a separate user-pool
lease. If test sign-in tools cannot authenticate an existing learner, use its
operator-provisioned dedicated credentials, never post them. No available fixture
or failed backend check means `incomplete/account`, not a generic-user fallback.

Use a different private receipt path per run. The receipt is written exclusively
with mode 0600 and retained for crash recovery. Never share it (it contains a lease
token). Transactions serialize allocation and registration via a registry row;
random fencing tokens prevent old receipts releasing a replacement lease.

Leases last four hours. Renew before expiry; stop using the organization at
expiry. An expired lease is **not free**: a crashed run may have changed server
state. Release always quarantines; it does not delete accounts, remove seats,
clear assessment history, or make the organization immediately reusable.
Verification checks the baseline: after intentionally changing it, test the new
expected state directly rather than claiming baseline verification still passes.

## Reset and recovery

An operator restores backend state, including assessment history, seat validity,
course/settings, schedules and audience. Validate the original baseline manifest,
then run `python3 scripts/qa_org.py reset /private/path/fixture.json --evidence
RESET_RUN_URL`. Reset takes an exclusive resetting claim and verifies again before
making the fixture ready. It refuses unexpired leases, changed baseline manifests
or changed fingerprints. Failed reset stays quarantined. The last reset evidence
is stored as holder while resetting; retain the reset report externally for audit.
A process dying while `resetting` needs explicit operator investigation; it is never
silently reclaimed. Do not reset a fixture while a stopped/expired agent may still
be using it: registry fencing cannot fence requests made directly to the backend.

This change ships pool tooling, not a populated pool, an installed Devin plugin,
or live B2B e2e validation. First enrollment must be reviewed against the deployed
backend and the scenario's actual required-state contract.
