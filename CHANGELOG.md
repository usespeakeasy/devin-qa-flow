# Changelog

What changed in the QA system, newest first. One entry per change to a skill under `skills/` or to
the run instructions (`docs/`, `AGENTS.md`). Flow and `LEARNINGS.md` pushes are not listed here;
`git log` has them.

Skill versions are `YYYY.MM.DD.N`, set in `metadata.version` of the skill's `SKILL.md`. Every QA
run writes `skill_version` and `flow_repo_sha` (this repo's `main` SHA at run start) to
`devin_qa.qa_request_mobile_runs`, so you can compare runs before and after a change:

```sql
SELECT skill_version, platform, COUNT(*) AS runs,
  APPROX_QUANTILES(record_min, 2)[OFFSET(1)] AS record_p50,
  APPROX_QUANTILES(total_min, 2)[OFFSET(1)] AS total_p50
FROM `speak-v2-2a1f1.devin_qa.qa_request_mobile_runs`
WHERE request_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 60 DAY)
GROUP BY 1, 2 ORDER BY 1 DESC, 2
```

Runs before 2026-11-01 have no `skill_version`.

## 2026-11-01

- **qa-request-mobile 2026.11.01.6**: iOS runs drive cases with Maestro flows from this repo
  instead of an AXe or XCUITest script, and record with `recordVideo --codec h264 --force`.
  Found by the iOS dry run of speak-ios#9662.
- **Instructions**: iOS run steps corrected after the dry run of speak-ios#9662 (first real
  iOS run): build env vars, AXe path, pool sign-in by deep link and first-run prompts, one
  account per simulator for settings cases, switch selectors, notification permission through
  iOS Settings, `takeScreenshot` location, date picker and popover points, two-simulator load.
  Recording 44 → about 6 min for both builds in parallel.
- **qa-request-mobile 2026.11.01.5**: the Slack report needs an `ID PR:` line, with the draft ID
  PR link for each screen, or `ID PR: none needed`. The per-run workflow now has an ID PR step,
  for Android and iOS. Why: the speak-android#8630 rerun used text selectors on the review dialogs
  but skipped the ID PR. The ID rule was only under Missing IDs, and a search for it found only
  the iOS line ([#9](https://github.com/usespeakeasy/devin-qa-flow/pull/9)).
- **qa-request-mobile 2026.11.01.4, qa-android-harness 2026.11.01.2**: pre-auth flows. Flows in
  `auth/` and `onboarding/` start signed out and are the only ones that may sign in, sign up or
  walk onboarding. Harness `fresh` clears app data and waits for the welcome screen; `newuser`
  prints a throwaway sign-up email that never joins the pool. Why: sign-up and onboarding cases
  had no reusable flows, so every run walked them by hand ([#6](https://github.com/usespeakeasy/devin-qa-flow/pull/6)).
- **qa-request-mobile 2026.11.01.3**: the skill's source now lives in this repo under
  `skills/`. Runs write `skill_version` and `flow_repo_sha` to the run record. Change the skill
  with a PR here; after merge, Devin saves it with `manage_plugin` and posts the PSA.
  Harness `qa-android-harness` is 2026.11.01.1 (same content as the saved revision).
- **Instructions**: iOS run steps and `LEARNINGS.md`, which runs push to directly after a major
  failure ([#4](https://github.com/usespeakeasy/devin-qa-flow/pull/4)). iOS steps not yet tested
  on a real run.
- **qa-request-mobile 2026.11.01.2**: the skill's flow sections became one pointer to this repo's
  `AGENTS.md` and `docs/qa-pr-instructions.md`; the repo wins if they disagree
  ([#3](https://github.com/usespeakeasy/devin-qa-flow/pull/3), plugin revision
  `83bd5ed2c8c011ebb6a5696a3c2a54e3`). Instructions moved to `docs/qa-pr-instructions.md`, with
  PR and Slack writing rules and the vendored i-have-adhd and humanizer skills.
- **qa-request-mobile 2026.11.01.1**: Android cases run as Maestro flows from this repo, base and
  branch on two emulators at once. Harness `emu` takes `--avd`/`--port` and clears stale crash
  data before boot. Dry run of speak-android#8617: recording 30.5 → 6.4 min for both builds
  ([PSA](https://usespeak.slack.com/archives/C0C8G9VS2KX/p1793504506833249)).
- **Instructions**: seed Android flows, `AGENTS.md` and `README.md`
  ([#1](https://github.com/usespeakeasy/devin-qa-flow/pull/1)).
