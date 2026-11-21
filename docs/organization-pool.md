# Develop organization fixtures

`scripts/qa_org.py` is platform-neutral: the same lease is used by Android and
iOS and by both base/branch builds. It requires Python 3, authenticated `bq`,
write access to `speak-v2-2a1f1.devin_qa`, and `QA_ORG_ACCESS_TOKEN` containing a
**develop admin** access token. Tokens are read from the environment, never saved.
The backend is pinned to `https://speak-api.alpha.usespeak.dev`; production and
preview hosts are not supported. Do not put manifests/receipts in git or reports.

## Provision (operator/agent)

Use the normal develop Partners admin APIs, not `POST /v1/admin/e2e/users`.
That E2E endpoint may be cleanup-only on alpha; its 403 does not mean normal
organization learner creation is unavailable.

```sh
python3 scripts/qa_org_provision.py --journal /private/path/provision.json --holder SESSION_URL --product EXISTING_DEV_SPEAK_PRODUCT_ID
```

This creates a fingerprinted organization, a dedicated learner, a non-revenue
one-seat trial subscription, and its assignment. It disables onboarding campaigns
and does not create HubSpot deals or payments. Default language pair is
`korean-english`; select a supported assessment language pair explicitly when needed.
It then checks the organization rollout and configures a required scheduled
assessment. The subscription lasts 30 days and the schedule ends in 5 days;
expired baselines need explicit renewal/reset, not silent reuse.

The provisioner does **not** enroll the fixture or claim mobile readiness. Before
registration, authenticate as the dedicated learner and verify required eligibility,
course state and the profile's checks. For dedicated fixtures only, the normal
Partners admin `POST .../organizations/{id}/users/{userId}/reset-password` returns
a generated password for email login. Keep it private; never reset a shared learner
or log the response. No auth token/password belongs in the journal or manifest.

Resume with the same arguments and journal. Successful steps are not repeated.
A timeout/failed mutation leaves `pending`: inspect backend state by exact name,
fingerprint and dedicated email, record the confirmed response under that step's
key, then remove `pending`. Never clear it blindly or create another fixture.
If a non-required schedule already exists, record its ID as `schedule_id` so resume
patches that schedule rather than creating a duplicate. Keep journals outside git.

The `app_assessments_required` rollout must target the **organization ID**.
Individual user targets and mobile overrides are not a substitute. If
`canRequireAppAssessment` is false, provisioning stops without registering anything
as ready. Enable only the dedicated dev organization's rollout through the normal
flag-management process, then resume. Verify learner-facing state separately even
when the portal actor reports the rollout on.

## Refill / registration

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
   Configure the required schedule/audience/dates for the scenario. The provisioner above automates this setup; enrollment and learner-facing
   verification remain explicit steps, not mobile flag overrides.
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

This change ships pool and explicit provisioning tooling, not automatic
replenishment during leasing, an installed Devin plugin, or live B2B e2e validation. First enrollment must be reviewed against the deployed
backend and the scenario's actual required-state contract.
