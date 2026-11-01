# AGENTS.md

Maestro flows that `qa-request-mobile` runs reuse across PRs. Only Devin QA runs write here;
developers don't write or review flows. Goal: a QA run reuses scripted cases instead of
re-deriving taps from the PR's "How to test?" every time.

## Per-run workflow

1. `git pull --rebase` on `main`.
2. For each case in the PR's "How to test?", grep [INDEX.md](INDEX.md) for the screen, the
   classes the diff touches, the deep link and the resource IDs. Reuse a matching flow as is.
   Skip flows listed under Known broken unless this run repairs them.
3. No match: write a new flow. Compose it from `<platform>/common/` subflows with `runFlow`
   and copy steps from the closest existing flow. Extend a common subflow with `env`
   parameters instead of forking it.
4. Run every flow on the base build first. A flow is evidence only once it passes on base.
   If a reused flow fails on base, develop changed: fix the flow, and say so in the commit
   (see Stale IDs).
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

Every flow has one row. The app repo at the base build's develop SHA is the authority for which
IDs exist; INDEX.md is a cache of what flows rely on. When they disagree, the app wins and the
flow and its row get updated. Concurrent runs have different base SHAs, and the newest develop
SHA wins: compare two SHAs with `git merge-base --is-ancestor <a> <b>` in the app repo, never by
eye. "IDs it relies on" lists resource IDs; "Text fallbacks" lists
every text or point selector still in the flow. "Last verified" is the develop short SHA
of the base build the flow last passed on.

## Committing

- Push straight to `main`; no PRs. Many QA runs write at once, so `git pull --rebase` and
  retry the push when it's rejected.
- One commit per run, e.g. `android/main-tabs: add tab-tour (QA speak-android#1234)`.
- Commit only flows that passed on the base build. Never commit recordings, screenshots or
  Maestro debug output.

## Conflicts

Many runs write at once, so rebases conflict. Never force-push, never reset `main`, and never
resolve a conflict by dropping another run's work. During `git rebase`, `--ours` is `main` and
`--theirs` is this run's commit, so `git checkout --ours <file>` takes `main`'s version. Resolve
by file type:

- `INDEX.md` rows: keep both sides' rows and re-sort. If both rows point at the same flow path,
  resolve the flow first, then rewrite the row's ID and fallback columns from the resolved file
  and keep the newer "Last verified".
- Same flow edited by both runs: take `main`'s version, re-apply this run's change on top, and
  re-run the flow on the base build before pushing. If the two versions are different cases,
  split them into two files (one case per file) instead of merging taps.
- `main`'s version was verified on a newer develop than this run's base and fails on this base:
  it is not stale. Keep `main`'s version, test the case from a scratch copy, and don't commit
  changes to that flow.
- Common subflow (`<platform>/common/`): take `main`'s version and add this run's needs as `env`
  parameters. Re-run every flow in this run that `runFlow`s it.
- Both sides changed the selector for the same element: keep whichever resolves at the newer of
  the two base SHAs (`git grep` the app repo). If both resolve, prefer the ID. Update the INDEX
  row.
- One side deleted a flow the other edited: keep the deletion only if the screen's code is gone
  at the newer base SHA. Otherwise keep the edited file and its row.

Retry the rebase and push until it lands. Re-run on base only the flows and subflows that the
rebase changed and this run uses. Never leave the run's flows unpushed.

## Missing IDs

When a flow needs a text or point fallback because the element has no ID:

1. List the fallback in the flow's INDEX.md row.
2. Open a draft PR in speak-android or speak-ios that adds the ID, following
   `agent_docs/patterns/automation-resource-ids.md` (Android) or
   `agent_docs/coding-standards/automation-accessibility-identifiers.md` (iOS) and that
   repo's PR rules. One PR per screen: search open PRs for the screen first
   (`gh pr list -R usespeakeasy/speak-<platform> --search "<screen> automation id"`) and
   comment on an existing one with the extra IDs instead of opening a second. Use the names
   that repo's standard produces
   (feature-prefixed `snake_case` on Android, dotted namespace on iOS). A committed flow never
   relies on an ID from a draft PR until it is on develop.
3. Post the draft PR link in #devin-qa-request-mobile for review. Don't block the QA run on
   it. Switch the flow and the INDEX.md row to the ID once the PR is on develop.

## Stale IDs

A stale ID is one a flow or INDEX row relies on that the app no longer exports at the base build
(renamed, removed, or the screen was rewritten). It shows up as a base-build failure at an `id:`
selector, which is not a finding. Confirm it with the harness `dump` (only while no Maestro flow is
running) and with `git grep <id>` in the app repo at the base SHA. Look for the replacement in the
feature's `*TestTags` constants (Android) or identifier namespace (iOS). A grep miss alone is not
proof: identifiers built from pieces at runtime don't match a literal grep, so check the namespace
before calling an ID stale.

Repair it inside the run; never block the QA on it. In order:

1. Replacement ID exists: switch the flow to it, update the INDEX row, re-run on base and bump
   "Last verified". Name the swap in the commit, e.g.
   `android/main-tabs: tab-tour stale id stat_streak_title -> profile_streak_title`.
2. Element exists but has no ID: use a text selector, list it under "Text fallbacks", and follow
   Missing IDs. The run proceeds on the fallback.
3. Element or screen is gone (its code is removed at the base SHA, confirmed with `git grep`,
   not only missing from `dump`): the case is obsolete. Delete the flow and its row, or rewrite
   it if the product case still exists on a new screen. Say so in the commit.
4. Can't repair in this run (for example the base build is broken on that screen): don't use the
   flow as evidence. Test the case from a scratch flow or by hand and say so in the QA result.
   Add the flow to "Known broken" in INDEX.md with the flow path, base SHA and a one-line reason.
   The next run that sees it pass on base removes the entry. Never leave an unrepaired flow out
   of Known broken.

When fixing a stale ID or a conflict in a shared flow, grep INDEX.md and every flow for the old
ID, fix those in the same commit, and re-run each on base. If one can't be run this run, leave
its file unchanged and add it to Known broken with reason `stale id <old> -> <new>, not re-run`.
Any run that passes a flow on base updates its "Last verified" SHA when this run's base is newer
than the recorded one.

## Gotchas

- Maestro installs its driver on a device the first time it runs there (about 10 to 20 s).
- `screenrecord` stops at 180 s; split long cases into two flows or two recordings.
- Install Maestro with `curl -fsSL "https://get.maestro.mobile.dev" | bash` (needs Java 17+);
  the binary lands in `~/.maestro/bin/maestro`.
