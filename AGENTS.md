# AGENTS.md

Maestro flows that `qa-request-mobile` runs reuse across PRs. Only Devin QA runs write here;
developers don't write or review flows. Goal: a QA run reuses scripted cases instead of
re-deriving taps from the PR's "How to test?" every time.

QA runs: read [docs/qa-pr-instructions.md](docs/qa-pr-instructions.md) and
[LEARNINGS.md](LEARNINGS.md) first. The instructions have the per-run workflow for Android and
iOS, two emulators, committing, conflicts, missing and stale IDs, learnings, PR and Slack
writing, and Maestro gotchas. This file has the rules for flow files and INDEX.md.

## Changing these instructions

QA runs push only `android/`, `ios/`, `INDEX.md` and `LEARNINGS.md` changes to `main`. Changes to `AGENTS.md`,
`README.md`, `docs/` and `.agents/` go through a PR to Sean Kim.

## Flow rules

- One case per file: `<platform>/flows/<area>/<case>.yaml`, kebab-case. Use the same
  `<area>/<case>` name on Android and iOS for the same product case.
- Header comment: what the case checks, its entry point, and preconditions (account state,
  flag overrides, dev or prod). iOS flows that read automation markers launch with
  `SPEAK_AUTOMATION_MARKERS=1`.
- `appId: ${APP_ID}` with an `env` default: `com.selabs.speak.dev` (Android develop),
  `com.selabs.speak-v2.dev` (iOS Speak-Dev).
- Selector order: resource ID / accessibility identifier, then text regex (escape regex
  characters, e.g. `\\?`), then a point only as a last resort with a comment saying why.
- Assert an arrival after every screen change (`assertVisible` or `extendedWaitUntil`).
  No fixed sleeps over 2 s.
- No sign-in, sign-up or onboarding inside flows, and no credentials, emails or user IDs.
  The harness leases and signs in a pool account before flows run. Exception: when sign-in
  is the case under test (`android/flows/auth/`), flows take `EMAIL` and `PASSWORD` as
  `-e` parameters at run time; the values still never go in a file.
- A flow must work on any pool account. If it needs seeded state (progress, saved items,
  premium), the header says how to seed it, ideally with a common subflow.
- Run `maestro check-syntax <file>` before committing.

## INDEX.md

Every flow has one row. The app repo at the base build's develop SHA is the authority for which
IDs exist; INDEX.md is a cache of what flows rely on. When they disagree, the app wins and the
flow and its row get updated. Concurrent runs have different base SHAs, and the newest develop
SHA wins: compare two SHAs with `git merge-base --is-ancestor <a> <b>` in the app repo, never by
eye. "IDs it relies on" lists resource IDs; "Text fallbacks" lists
every text or point selector still in the flow. "Last verified" is the develop short SHA
of the base build the flow last passed on.
