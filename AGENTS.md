# AGENTS.md

Maestro flows that `qa-request-mobile` runs reuse across PRs. Only Devin QA runs write here;
developers don't write or review flows. Goal: a QA run reuses scripted cases instead of
re-deriving taps from the PR's "How to test?" every time.

## Per-run workflow

1. `git pull --rebase` on `main`.
2. For each case in the PR's "How to test?", grep [INDEX.md](INDEX.md) for the screen, the
   classes the diff touches, the deep link and the resource IDs. Reuse a matching flow as is.
3. No match: write a new flow. Compose it from `<platform>/common/` subflows with `runFlow`
   and copy steps from the closest existing flow. Extend a common subflow with `env`
   parameters instead of forking it.
4. Run every flow on the base build first. A flow is evidence only once it passes on base.
   If a reused flow fails on base, develop changed: fix the flow, and say so in the commit.
5. Run the same flow on the branch build. A flow that passes on base and fails on the branch
   is a possible finding: report it in the QA result, and don't edit the flow to make the
   branch pass. Branch-only expectations (a PR's intended new behavior) stay in the run's
   scratch dir until the change is on develop; the next run that sees base fail updates it.
6. Record with the qa-request-mobile harness (`qa_android.py rec` / `stop`, one mp4 per
   case, under 180 s), not `maestro record`. Don't call harness `dump`/`tap`/`wait` while a
   Maestro flow is running; both drive UiAutomator.
7. Add or update the INDEX.md row, then commit and push (see Committing).

Base and branch can run at the same time on two emulators: `maestro --device emulator-5554`
and `--device emulator-5556`. Keep animation and timing cases sequential; two emulators
share the CPU and recordings drop frames.

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
  The harness leases and signs in a pool account before flows run.
- A flow must work on any pool account. If it needs seeded state (progress, saved items,
  premium), the header says how to seed it, ideally with a common subflow.
- Run `maestro check-syntax <file>` before committing.

## INDEX.md

Every flow has one row. "IDs it relies on" lists resource IDs; "Text fallbacks" lists
every text or point selector still in the flow. "Last verified" is the develop short SHA
of the base build the flow last passed on.

## Committing

- Push straight to `main`; no PRs. Many QA runs write at once, so `git pull --rebase` and
  retry the push when it's rejected.
- One commit per run, e.g. `android/main-tabs: add tab-tour (QA speak-android#1234)`.
- Commit only flows that passed on the base build. Never commit recordings, screenshots or
  Maestro debug output.

## Missing IDs

When a flow needs a text or point fallback because the element has no ID:

1. List the fallback in the flow's INDEX.md row.
2. Open a draft PR in speak-android or speak-ios that adds the ID, following
   `agent_docs/patterns/automation-resource-ids.md` (Android) or
   `agent_docs/coding-standards/automation-accessibility-identifiers.md` (iOS) and that
   repo's PR rules. One PR per screen; check for an open one first.
3. Post the draft PR link in #devin-qa-request-mobile for review. Don't block the QA run on
   it. Switch the flow and the INDEX.md row to the ID once the PR is on develop.

## Gotchas

- Maestro installs its driver on a device the first time it runs there (about 10 to 20 s).
- `screenrecord` stops at 180 s; split long cases into two flows or two recordings.
- Install Maestro with `curl -fsSL "https://get.maestro.mobile.dev" | bash` (needs Java 17+);
  the binary lands in `~/.maestro/bin/maestro`.
