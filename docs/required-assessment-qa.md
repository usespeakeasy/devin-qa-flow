# Required-assessment QA (Android and iOS)

Use this real-backend setup for an organization learner whose assessment blocks
app use. A generic test user or a mobile flag override does not establish the
organization's required-assessment state. Read [organization-pool.md](organization-pool.md)
for provisioning, leases, private credentials, verification and quarantine.

## 1. Choose the account and environment

- Prefer a ready `required-assessment-v1` fixture; lease its organization and
  dedicated learner together. Keep the same lease for base and branch.
- An explicitly authorized shared dev organization can be used for a one-off
  test with a dedicated learner. It is **not** eligible for pool registration.
  Do not reset another learner, disable organization-wide recurring assessments,
  or change other learners' schedules to make a test work.
- Confirm active membership and an assigned, active subscription seat. Select a
  supported assessment course/language (the verified setup used `en-US`). The
  learner must not have submitted an assessment for the tested cycle.
- Use develop Partners and alpha API together. The pool scripts do not support
  preview or production; don't silently mix their accounts or schedules.

## 2. Check capability with client info before changing a flag

Authenticate as the authorized Partners actor and GET
`/v1/partners/organizations/{organizationId}/assessment`.
`canRequireAppAssessment` is computed, not directly editable. The backend
checks `app_assessments_required` with client context. Missing client headers
can produce **false even when the organization rollout is on**.

Send `x-access-token` plus `x-client-info`, using the target build's actual
platform, OS version, app version and build number. For example, the header
shape for iOS is (substitute actual values):

```text
x-client-info: platform=ios;platformVersion=OS_VERSION;appVersion=APP_VERSION;buildNumber=BUILD_NUMBER;device=iPhone;timezone=America/Los_Angeles;appLocale=en_US;appLanguage=en_US;deviceLocale=en_US;anonymousId=QA_RUN_ID
```

For Android, use its actual client header, not the iOS platform/version values.
Do not print tokens. Recheck capability with these headers before attributing
false to Harness, requesting re-authentication, or changing rollout targeting.
If still off, verify the flag targets the **organization ID**, not just the user.

**Current script limitation:** `scripts/qa_org.py` sends authentication and JSON
headers but no `x-client-info`; `qa_org_provision.py` uses that helper. Its
"rollout is OFF" error alone is not authoritative. Check manually with client
headers and reconcile the same private journal before resuming; do not blindly
retry mutations, enroll an unverified fixture, or claim this limitation is fixed.

## 3. Create a required window that is open now

In develop Partners → select the organization → Assessments → Create assessment:

1. Name: a unique QA run/case name.
2. Audience: **By Individual**, select only the dedicated QA learner. Check that
   the selected count is one; do not select the entire subscription by default.
3. Window: choose a start already in the past and an end after the whole QA run.
   Check the portal timezone against UTC. A schedule starting tomorrow cannot
   unblock today's test.
4. Requirement: turn **Require** on.
5. Review: verify learner, dates and requirement, then create.

API equivalent: POST
`/v1/partners/organizations/{organizationId}/scheduled-assessments` with
`name`, ISO-8601 `startAt`/`endAt`, `requireAppAssessment: true`, and
`audience: {"userIds": ["DEDICATED_LEARNER_ID"]}`. Use the client headers above.
GET the created schedule by ID and confirm saved requirement, open window and
exact audience/participant count. Inspect an uncertain POST result before retrying.
Do not create duplicate schedules or change an unrelated existing schedule.

## 4. Verify as the learner, then run mobile QA

Sign in as the dedicated learner, not the portal admin. GET
`/v1/standalone-assessments/entrypoint` with learner authentication and client
headers. Before starting, confirm:

- `appAssessment` is non-null and `hasAccess` is true.
- `cycleId` identifies the intended scheduled assessment and language.
- `requirementNotice.cycleId` matches that cycle. The verified fresh learner
  returned `state: "neverTaken"`; don't require that state for a retake case.

A true admin capability does not prove learner eligibility. If entrypoint is null,
check seat, course, audience, open window and prior submission before mobile work.
Record redacted setup evidence privately; credentials and lease receipts never go
in flows, commits, PR bodies or Slack.

Run the PR's cases on exact base and branch builds and record both. For
[speak-ios#10884](https://github.com/usespeakeasy/speak-ios/pull/10884):

- **Start course:** complete the blocking assessment with a recommendation for a
  different course; tap Start course. Verify Home selects the recommended course
  after the assessment closes (including after relaunch).
- **Other report actions:** exercise lesson, course browsing and Return home.
  Verify the chosen destination opens after dismissal; Return home must not
  start a lesson.
- **Cancel unfinished assessment:** leave before completion. Verify the required
  screen remains and the selected course does not change.

Completion mutates server state. Do not race base/branch on the same learner or
assume reinstall resets the cycle. Before each stateful case/build, establish and
verify an equivalent eligible cycle through supported setup/reset; if that cannot
be done, report the case incomplete. Don't fabricate server responses and call it
real-backend QA. Keep intended branch-only assertions separate from reusable flows.

## 5. Report and release

Separate **setup verified**, **base reproduced**, and **branch validated**. An
open required schedule and a valid entrypoint prove setup only, not navigation.
Report each case as pass/fail/NOT RUN with Before | After recordings. Capture
private IDs and window evidence for reproducibility without committing identities.
Release the fixture lease (which quarantines it) and record changed server state
for operator reset. For a one-off shared-org test, record the QA-only schedule's
expiry and any authorized cleanup; leave unrelated members and schedules alone.
