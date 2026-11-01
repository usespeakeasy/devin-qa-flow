# QA PR instructions

What a `qa-request-mobile` run does with this repo, from finding flows to pushing them back and
writing the ID PR. Read this before touching a flow. The rules for writing a flow file and an
INDEX.md row are in [AGENTS.md](../AGENTS.md).

## Per-run workflow

1. `git pull --rebase` on `main`, then read [LEARNINGS.md](../LEARNINGS.md).
2. For each case in the PR's "How to test?", grep [INDEX.md](../INDEX.md) for the screen, the
   classes the diff touches, the deep link and the resource IDs. Reuse a matching flow as is.
   Skip flows listed under Known broken unless this run repairs them.
3. No match: write a new flow, following the Flow rules in [AGENTS.md](../AGENTS.md#flow-rules). Compose it from `<platform>/common/` subflows with `runFlow`
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
7. Add or update the INDEX.md row (format in [AGENTS.md](../AGENTS.md#indexmd)), then commit
   and push (see Committing).
8. If a flow this run wrote or ran uses a text or point fallback, open the ID PR or
   comment on the open one (see Missing IDs). This is for Android and iOS runs.
9. If the run hit a major failure, add a learning (see Learnings).

Step 6 and the next two sections are for Android. iOS runs use the same steps, with the
changes listed in iOS runs.

Base and branch can run at the same time on two emulators: `maestro --device emulator-5554`
and `--device emulator-5556`. Keep animation and timing cases sequential; two emulators
share the CPU and recordings drop frames.

## Running a flow in the case script

- Run each flow with `maestro --device <serial> test [-e KEY=value] <flow>` inside the case
  script, between harness `rec` and `stop`. Account lease and login stay in the harness.
- Sign-in flows take the pool account as `-e EMAIL=... -e PASSWORD="$QA_POOL_PASSWORD"`.
  Never write the values in a file.
- Maestro logs typed text, passwords included. Pass `--debug-output /tmp/maestro-<serial>/<case>`,
  filter the password out of its console output, and delete the debug folder after the run.
- The flow's step lines (`COMPLETED` / `FAILED`) are the case's assertion. Keep them for the
  packet's toggle.
- Keep each case under 180 s (`screenrecord` stops there). Split a longer case into two flows.
- Find selectors with harness `dump` on the base build, only while no flow is running.

## Pre-auth flows

Flows in `android/flows/auth/` and `android/flows/onboarding/` start signed out (header
`Entry: app data cleared`). Cases for the welcome screen, sign-in, sign-up, onboarding steps
and first-run prompts go there.

1. Reset the app with `qa_android.py fresh` before each pre-auth flow. It runs `pm clear`,
   grants the notification and microphone permissions again (`--no-grant` keeps them unset
   for a case about the permission prompt) and cold-starts the app on the welcome screen.
   Don't `launchApp` with `clearState` in the flow; `fresh` does it once, outside the recording.
2. Cases that don't need an account (welcome screen, onboarding steps before account creation,
   the paywall shown before sign-up) need no lease. Stop the flow before the account step.
3. Sign-in cases use the leased pool account: `-e EMAIL=<leased email> -e PASSWORD="$QA_POOL_PASSWORD"`.
4. Sign-up cases need a new user. `qa_android.py newuser` prints a throwaway
   `devin+qa-new-<time>-<random>@usespeak.com`; pass it as `-e EMAIL=...` with
   `-e PASSWORD="$QA_POOL_PASSWORD"`. Use a new one per build and per run, so base and branch
   don't share server state. Never add a throwaway account to the pool, and never put its email
   in a file, the PR or the thread. Set `account_source` to `fresh_signup` in the run record.
5. A signed-in case after a pre-auth flow needs `qa_android.py login` again, because `fresh`
   signed the app out.

## Two emulators

Base and branch can run at the same time, one build per emulator, with the same AVD config,
account and flags.

- Stop Gradle and the Kotlin daemon first (`./gradlew --stop` in each worktree, then check that
  `pgrep -f GradleDaemon` prints nothing). Idle daemons hold about 13 GB; two emulators need
  about 11 GB of the 31 GB VM.
- Harness `emu` boots `emulator-5554` (`devin`). `emu --avd devin2 --port 5556` boots
  `emulator-5556`, cloned from `devin` on first use. Install the base APK on one and the branch
  APK on the other.
- With two emulators up, every harness command needs `ANDROID_SERIAL`. Lease one pool account,
  log both emulators in to it (same `QA_LEASE_FILE`), and release it once.
- Run the two case scripts in parallel, each with its own `ANDROID_SERIAL` and output folder.
- Run one build at a time when a case measures timing or animation (recordings lose 10 to 25%
  of frames when two emulators share the CPU), or when a case changes server state that the
  other build would see (lesson progress, counters, sign out of all sessions, account deletion,
  purchases).

## iOS runs

iOS builds and runs only on macOS. A Linux QA session hands the run to one macOS child, and
the child clones this repo and follows this file. The child prompt says so.

- Flows: `ios/common/` and `ios/flows/<area>/<case>.yaml`, with the same `<area>/<case>` name
  as the Android flow for the same product case. Run with
  `maestro --device <simulator UDID> test -e APP_ID=com.selabs.speak-v2.dev <flow>`.
- Selectors: accessibility identifiers first (`id:` in Maestro matches them), then text.
  Read the tree with `axe describe-ui --udid <UDID>` on the base build, only while no flow is
  running.
- Automation markers are off unless the app launches with `SPEAK_AUTOMATION_MARKERS=1` in its
  launch environment. Launch with
  `SIMCTL_CHILD_SPEAK_AUTOMATION_MARKERS=1 xcrun simctl launch <UDID> com.selabs.speak-v2.dev`
  before a flow that reads markers, and start that flow without `launchApp`.
- Install each build with `xcrun simctl install`. Installing over the same bundle ID keeps the
  signed-in account, so one pool account serves both builds.
- Record with `xcrun simctl io <UDID> recordVideo --codec h264 <file>` and stop it with
  `kill -INT`. It has no 180 s limit; keep one file per case anyway so the packet timestamps
  stay simple.
- Two simulators: base and branch can run at once on two booted simulators of the same device
  type and runtime (`xcrun simctl clone <UDID> <name>`), one `maestro --device` per simulator.
  The same rules for timing cases and shared server state apply as on Android.
- Missing IDs: the ID PR goes to speak-ios instead of speak-android. Follow its `AGENTS.md` and
  `agent_docs/workflows/git-pr-workflow.md` (branch prefix, template), but open it ready for review
  as in Missing IDs.

## Committing

- Push straight to `main`; no PRs. Many QA runs write at once, so `git pull --rebase` and
  retry the push when it's rejected.
- One commit per run, e.g. `android/main-tabs: add tab-tour (QA speak-android#1234)` or
  `ios/settings: add manage-account (QA speak-ios#1234)`.
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
2. Open a PR in speak-android or speak-ios that adds the ID, following
   `agent_docs/patterns/automation-resource-ids.md` (Android) or
   `agent_docs/coding-standards/automation-accessibility-identifiers.md` (iOS) and that
   repo's PR rules. One PR per screen: search open PRs for the screen first
   (`gh pr list -R usespeakeasy/speak-<platform> --search "<screen> automation id"`) and
   comment on an existing one with the extra IDs instead of opening a second. Use the names
   that repo's standard produces
   (feature-prefixed `snake_case` on Android, dotted namespace on iOS). A committed flow never
   relies on an ID from an open PR until it is on develop.
3. Open it ready for review, not as a draft, under the QA'd PR's author's GitHub account
   (`git_create_pr` with `author_user_id` set to that author's Devin user). Then comment
   `@codex review` on it as the ID PR's author, not as Devin's bot: Codex declines the bot's
   request. Check the PR's and the comment's author; if either is the bot, say so in the report.
   Request a review from the `qa-devin` team
   (`gh api -X POST repos/usespeakeasy/speak-<platform>/pulls/<n>/requested_reviewers -f 'team_reviewers[]=qa-devin'`).
   If it fails, say so in the report.
4. Post the PR link as a reply in the QA request's thread, with "Also send to channel" on, so it
   shows in #devin-qa-request-mobile too, and tag Sean Kim in it (`<@U06CM4TRNBX>`, a real
   mention, not plain text). Don't make a separate top-level post. Example text:
   `<@U06CM4TRNBX> ID PR for the Free Talk community details, report and report confirmation sheets, ready for review: <PR URL>` Neither
   `message_user` nor the Slack MCP's `slack_reply_to_thread` can set that flag, so call
   `chat.postMessage` with `reply_broadcast` and the Slack MCP server's token (it posts as
   `devin_mcp`):

   ```bash
   SLACK_TOKEN=$(tr '\0' '\n' < /proc/$(pgrep -f 'node .*mcp-server-slack' | head -1)/environ \
     | sed -n 's/^SLACK_BOT_TOKEN=//p')
   jq -n --arg ts "$THREAD_TS" --arg text "$TEXT" \
     '{channel: "C0C8G9VS2KX", thread_ts: $ts, reply_broadcast: true, text: $text}' \
     | curl -s -H "Authorization: Bearer $SLACK_TOKEN" -H 'Content-Type: application/json; charset=utf-8' \
       --data @- https://slack.com/api/chat.postMessage | jq '{ok, ts, error}'
   ```

   Never print the token. Write the text as in Writing PRs and Slack posts. Don't block the QA
   run on it. Switch the flow and the INDEX.md row to the ID once the PR is on develop.

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

## Learnings

[LEARNINGS.md](../LEARNINGS.md) holds what went wrong in past runs, so the next run doesn't
repeat it. Runs push to it directly, like flows.

Add an entry when a run hit a major failure: a wrong or `QA incomplete.` verdict, a stuck or
crashed emulator or simulator, a leaked secret, or about 15 minutes or more lost to one cause.
Skip one-off flakes that a single retry fixed.

- One bullet per failure, under its platform heading: what happened, the cause, and the rule
  that prevents it. Add the QA PR link and the date.
- If an entry for the same cause exists, update it instead of adding a second one.
- When a fix moves into a flow, a common subflow or the harness, say so in the entry, so a
  reader knows the rule is already applied.
- Never put credentials, emails or user IDs in an entry.
- Commit it with the run's flow commit, or alone as `learnings: <one line> (QA <repo>#<PR>)`.

## Writing PRs and Slack posts

This applies to ID PRs, PRs in this repo, and every Slack post about them.

1. Write plain English: B1-level words and sentences, with C2-level grammar and accuracy.
   Keep exact names, IDs, paths and commands as they are.
2. Shape it with [i-have-adhd](../.agents/skills/i-have-adhd/SKILL.md): next action or main
   point first, numbered steps, no preamble, recap or closing line.
3. Then run [humanizer](../.agents/skills/humanizer/SKILL.md) in embedded mode and keep only the
   final text.
4. PR description: follow the target repo's PR template and PR rules.
5. Slack: keep the top-level message to one or two lines with the PR link, and tag Sean Kim
   (`<@U06CM4TRNBX>`). Put the details in the first reply in the thread, written with steps 1 to 3.
   An ID PR has no top-level message: its post is the broadcast thread reply from Missing IDs
   step 4, one or two lines with the PR link and the Sean Kim tag, and the details go in the
   next reply in the same thread.

## Gotchas

- Maestro installs its driver on a device the first time it runs there (about 10 to 20 s).
- `screenrecord` stops at 180 s; split long cases into two flows or two recordings.
- Maestro is slow on the software-rendered emulator: `inputText` takes ~10 s and
  `eraseText` ~15 s. Don't erase fields that are already empty.
- Maestro debug output (`~/.maestro/tests/` by default) logs typed text, passwords included.
  Pass `--debug-output /tmp/maestro-<serial>/<case>` and delete it after the run.
- `tapOn` hits the element's centre, so in a text field the cursor can land mid-text and
  `eraseText` leaves a tail. Retype only short values, or reopen the screen.
- Two emulators at once: one `maestro --device <serial>` per emulator works in parallel.
- Install Maestro with `curl -fsSL "https://get.maestro.mobile.dev" | bash` (needs Java 17+);
  the binary lands in `~/.maestro/bin/maestro`.
