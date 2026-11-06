---
name: qa-request-mobile
description: Run a QA request on a Speak mobile PR (speak-android or speak-ios). Read the PR's "How to test?" section, build the base and the branch against dev or prod, record both runs, and write the Before | After result into the PR description. Use when someone asks for QA, a no-diff check, a before and after recording, or writes "qa-request-mobile <PR link>" in Slack, a PR comment or a Linear issue. Also use it for every @Devin request with a PR or ticket link in #devin-qa-request-mobile, whatever the wording ("test <link>", "check this").
metadata:
  version: 2026.11.06.1
---

# qa-request-mobile

The source of truth for this skill is `skills/qa-request-mobile/SKILL.md` in `usespeakeasy/devin-qa-flow`; what changed in each version is in that repo's `CHANGELOG.md`. Change the skill with a PR there, not by editing the saved copy.

One mobile PR goes in. Recorded QA evidence and a verdict come out, in the PR description and in the thread where the request was made. This skill does not review code, mark a PR ready, request approval or merge.

## Verdict

Every run ends with exactly one verdict. It is the first words of the PR status line and of the thread reply, so a reader knows whether the videos are good without watching them.

1. `QA passed.` Every case met its expected result (step 1), or is a note. The recordings show the PR does what it claims.
2. `QA failed.` At least one case did not meet its expected result. Name each failing case.
3. `QA incomplete.` No case failed, but at least one case was unreachable, unverified or not recorded. Name each one.

Each case also gets its own result: pass, fail, note, unreachable or unverified. "Same" or "differs" alone is not a result. On a behavior change PR "differs" is expected, so say whether the difference is the one "What's new?" describes.

No check, no pass. The packet webp is too small (320px, q60) and too sparse (4x at 5 fps) to show text, insets, switch states, transitions or anything off screen, so it is never the evidence for a pass on its own. A case passes only when it has, on both builds:

1. A mechanical check of the expected result: a scripted assertion (a Maestro `COMPLETED` or `FAILED` step line, or the view hierarchy id or text you asserted), or a measured value (inset frames from `dumpsys window`, a pixel read).
2. A full resolution screenshot at the case's arrival point.
3. The lifecycle check (see Lifecycle check): the case's lifecycle log lines on both builds, and why any difference is expected.

A case whose only evidence is the video is "unverified", and an unverified case makes the verdict `QA incomplete.` The video is the readable proof for people, not the check.

A case that misses its expected result on both builds is a "note", not a fail. The base already has the problem, so the PR did not cause it and it is not a regression. A note needs the same evidence as a pass: the check on both builds shows the base missing the expected result too. It never changes the verdict. Name it after the verdict, for example "QA passed. Cases 1 to 8 pass. Case 9 is a note: develop also resets the scroll on rotation." A case is a note only when the branch is no worse than the base. If the branch adds a problem the base does not have, the case is a fail.

## The request

Anyone can write it, wherever they talk to Devin:

```
@Devin qa-request-mobile <PR link> [env=prod] [mode=review] [post=linear|both] [extras="..."] [patch=<what to hard-code>]
```

| Field | Meaning |
|---|---|
| PR link | Required, or a ticket that links one (see Which request is a QA request). The repo (`speak-android` or `speak-ios`), the platform and the base branch come from the PR. |
| `env=dev` | Default. Debug build against the dev backend. |
| `env=prod` | Debug build against the production backend. Use it when the request says prod, or when "How to test?" needs production (a prod-only account, content or flag). See Platform notes. |
| `mode=run` | Default. Start QA right away on the test instructions as written. |
| `mode=review` | First review the test instructions, propose missing cases in the thread, and wait for the author before building anything. |
| `post=pr` | Default. Results go into the PR description and the thread where the request was made. |
| `post=linear` or `post=both` | Also comment on the Linear issue linked from the PR or the request (see step 6). `linear` and `both` behave the same, because the PR description is always updated. With no linked issue, say so in the thread and skip it. |
| `extras=` | Evidence beyond the recording that the requester wants in the packet, in their words. The lifecycle log diff and one screenshot per case are already the default (see Lifecycle check). Example: `extras="light and dark screenshots of the open sheet; path 4 with the kill switch override ON on the branch build"`. |
| `patch=` | State the app cannot reach on a test account (an organization account, an assigned goal, a server flag). Name the method to hard-code. The same uncommitted patch goes on both builds. |

A good request is two lines: the PR link, then anything the "How to test?" section does not already say. If the section is complete, the link alone is enough.

### Which request is a QA request

1. In #devin-qa-request-mobile (Slack channel `C0C8G9VS2KX`), every @Devin message with a PR or ticket link is a QA request, whatever the wording ("test <link>", "check this", "QA"). A message there without a link, like a follow-up "why did case 3 fail?", does not start a new run.
2. A `speak-android` or `speak-ios` PR sets the platform. Run it.
3. A PR in any other repo (for example `speak-api`) does not say which app to test. Ask in the thread whether they want iOS, Android or both, and wait for the answer before building.
4. For a ticket (a Linear issue), read the PRs and links attached to it. Linked `speak-android` or `speak-ios` PRs set the platform: run each one, both platforms when both are linked. If the ticket links no mobile PR, ask iOS, Android or both, as in item 3.

## Lifecycle check

Every run checks lifecycle on both builds, for every case, without being asked. Checkpoint screenshots per case and the logcat diff of screen views, controller lifecycle and ViewModels are the default packet, so `extras=` only needs what goes beyond them.

On Android, stream these tags for the whole run (SpeakLog infers the tag from the calling class):

| What | Tag | Lines |
|---|---|---|
| Screen views and events | `SegmentAnalyticsManager` | `Screen '<name>', properties {...}`, `Track '<event>'` |
| Controller lifecycle | `LoggingLifecycleListener` | `<Controller> bound to activity`, `view created`, `attached`, `appearing`, `disappearing`, `detached`, `view destroyed`, `destroyed`, `instance state saved`, `instance state restored` |
| Navigation | `ControllerTransactionProvider` | `Transaction between <A> and <B> using method <method> (tag <tag>)` |
| Navigation 3 entries | `EntryBreadcrumbs` | `<Key> appearing`, `attached`, `disappearing`, `instance state saved`, `instance state restored` |
| ViewModels | `CoreViewModel` | `ViewModel cleared: <Class>` |

1. Start `adb logcat -c`, then `adb logcat -v threadtime -s SegmentAnalyticsManager:D LoggingLifecycleListener:D ControllerTransactionProvider:D EntryBreadcrumbs:D CoreViewModel:D > <build>.log &` before the first case, and kill it after the last. `adb logcat -d` afterwards loses lines to buffer rotation.
2. `adb shell am force-stop <package>` before each build's run, so both start cold. A warm start on one side adds `MainController` lines that look like a diff.
3. Diff per case after stripping `@hash`, timestamps, PIDs and per-run ids (a new `savedItemId` after re-saving). Start each case's diff at its first transaction line; cold start and deep link lines vary per run on both builds.
4. Expected per case: the same screen views (name and properties), each screen created once and destroyed once on leave, every ViewModel of a closed screen cleared, and nothing left attached after back. A missing or doubled screen view, a missing `destroyed` or `ViewModel cleared`, or a duplicate create is a fail unless "What's new?" describes it.
5. A difference by design still needs a reason. For example "pass, same on screen; lifecycle moves from `<X>Controller` to the `<Key>` entry, per What's new". Never write just "as intended".
6. Some screens log nothing. Only `BaseController`, `BaseDialogController` and `SegmentHostController` attach `LoggingLifecycleListener`, so a `ConductorComposeController` shows only through its caller's lines, the transaction line and `ViewModel cleared`. Say so on the case line instead of calling it a diff.
7. There is no shared ViewModel init line. Show init with the ViewModel's own first log line if it has one, otherwise with the screen's `view created` or `attached` line, and say which. Add an init log only as a QA-only patch on both builds when the requester asks.
8. Timing-dependent order (two lines swapping between runs) is not a diff. Rerun that case once on both builds before reporting it, and report the first delta and the settled rerun.

When the PR touches navigation, lifecycle or saved state, also run rotation and process death (step 2 item 4) on the changed screen on both builds, even in `mode=run`. Report them as `Lifecycle: rotation` and `Lifecycle: process death` lines after the cases, not as new case labels. Each needs the screen restored with the same state and the same lifecycle lines (`instance state saved`, then `instance state restored`) on both builds.

On iOS, stream the app's console with `xcrun simctl spawn <simulator> log stream --level debug --predicate 'subsystem == "<bundle id>"' > <build>.log &` for the whole run and compare the screen view and view controller lines per case the same way.

## Run record

Every run records its duration in BigQuery table `speak-v2-2a1f1.devin_qa.qa_request_mobile_runs`, one row per request, so the ETA below improves over time. The `bq` CLI is authenticated as `devin-ai@speak-2-dev` on Linux and macOS machines by the org blueprint. Pass `--maximum_bytes_billed=1000000000` on every `bq query`.

1. ETA. In the first reply to the request, after the case list or proposals, post one line such as "Usually 60 to 110 min for Android on dev." Take the p25 and p75 of `total_min` from the table for the same `platform` and `env` over the last 60 days (`APPROX_QUANTILES(total_min, 4)`, offsets 1 and 3, `WHERE verdict IS NOT NULL`). With fewer than 10 rows, use 60 to 110 min on Android and 40 to 70 min on iOS. Add "longer with `patch=`" when a patch is set. If the query fails, use the fallback and carry on.
2. Phase marks. Write down UTC times as you go: request (the request message), build start (the first build command), builds ready (both builds installed), recording done (the last recording pulled and checked) and report posted. `build_min` is build start to builds ready. `record_min` is builds ready to recording done. `writeup_min` is recording done to report posted. `setup_min` is the rest of `total_min`. In `mode=review`, the wait for the author counts as setup.
3. Run time line. End the step 6 thread reply with `Run time: 74 min (setup 12, builds 31, recording 22, write-up 9)`.
4. Row. After the reply is posted, write one JSON line to a file and load it with `bq --project_id=speak-v2-2a1f1 --location=US load --source_format=NEWLINE_DELIMITED_JSON speak-v2-2a1f1:devin_qa.qa_request_mobile_runs <file>`. Fields: `thread_ts` (the Slack message ts, else `pr_comment:<comment id>`, `linear:<issue key>` or `session:<session id>`), `trigger` (`slack`, `pr_comment`, `linear` or `session`), `request_url`, `thread_url` (Slack only), `request_at`, `verdict_at`, `total_min`, `repo`, `platform` (`android` or `ios`), `pr_number`, `pr_url`, `ticket`, `env`, `mode`, `requester_id`, `requester_name`, `verdict` (`passed`, `failed` or `incomplete`), `verdict_line`, `case_count`, `cases_passed`, `verdict_count` (1), `has_patch`, `post_targets`, `eta_low_min`, `eta_high_min`, `devin_session_id`, `devin_session_url`, the four phase fields, `ack_at` (when the first reply was posted), `harness_used` (Android: true only if `qa_android.py` and devin-qa-flow Maestro flows drove every case, with no hand-rolled `ui.sh`, `uiautomator dump` or tap/sleep loops; null on iOS), `account_source` (`pool`, `fresh_signup`, `existing` or `none`), `incomplete_reason` (only when the verdict is incomplete: `env` for emulator, simulator or machine trouble, `build`, `account`, `flake`, `out_of_scope` for cases the build can't reach, `author` for a reply that never came, or `other`), `skill_version` (`metadata.version` at the top of this file), `flow_repo_sha` (the devin-qa-flow `main` SHA recorded after the step 1 pull in "Reusable flows"; on iOS, the SHA the macOS child reports), `source` (`skill`) and `ingested_at`. Leave `session_created_at`, `queue_min`, `acus`, `cost_usd`, `verdict_overturned`, `overturn_note` and `enriched_at` out: the daily reconcile fills them after the session ends. If a row with the same `thread_ts` already exists (a rerun in the same thread), do not add one; run `UPDATE ... SET verdict_count = verdict_count + 1 WHERE thread_ts = '<key>'` instead.
5. For iOS handed to a macOS child, the child reports its phase marks in its last message and the parent writes the row.
6. The record never delays or changes the verdict. If the load fails, retry once, then say so in one line at the end of the session, not in the thread.

## Cost

A run's cost follows its number of agent steps and the screenshots it opens, not its wall time. In late October 2026, 39 of 40 Android runs wrote their own `ui.sh` or `uiautomator dump` loops and drove cases one tap per tool call. They averaged $8.4 and 92 min, with 47 to 137 opened images each. The one run that used the bundled harness cost $6.3 and took 48 min for 6 cases.

1. On Android, every emulator action goes through `qa_android.py` (see "Android harness") or a Maestro flow from devin-qa-flow (see "Reusable flows"). Don't write `ui.sh`, `uiautomator dump` loops, or `adb input tap` / `sleep` / `screencap` chains. This applies to every step, including exploring a screen and rerunning a case. Using the harness only for `emu`, `lease` and `login` and then driving the cases with your own script doesn't count. If neither has a step, put one plain `adb` line inside the case script.
2. One script per build. Write all cases as one script and run it in one exec. Don't drive a case step by step in separate tool calls. Rerun only the case that failed, alone. After you fix a flow, the case script or a patch mid-run, rerun only the cases that use the changed file, on each build that ran them. Keep the results and recordings of the other cases. Never rerun a whole pass (all cases on one build or flag setting) for one fix.
3. Check arrival with text, not images. `wait`, `has` and `dump` print the matched node; that is the assertion. Don't open a screenshot (`view_image`, the desktop) to confirm a tap, a load or where you are. When lost, read `dump` first; open a screenshot only when the tree can't explain it.
4. Open each case's full resolution screenshot pair once, at write-up, to compare the builds.
5. The iOS macOS child follows the same rules: one script per build that runs Maestro flows from devin-qa-flow (see "Reusable flows"), arrival asserted from the accessibility tree, screenshot pairs opened once at write-up, and one report at the end. It messages the parent before then only when it is blocked.

## Steps

### 1. Read the test instructions

Open the PR description and read `## 👨‍🏫 How to test?`. Both repos use that heading. Android PRs list numbered paths; iOS PRs list lettered manual cases with numbered steps. Call each one a case and keep the author's label (`3.` or `B.`) everywhere you refer to it. The description, the recording and the thread all use the same labels. Never renumber or reletter; new cases are appended.

Take four things from the section:

1. The prerequisites. Account type, language pair, feature flags or experiment variants, debug settings, deep links. They may name helper scripts from another repo; the flag names, lesson ids and account type are what you need, and the in-app Debug Menu or a deep link sets them.
2. The cases, in order.
3. The pass condition. When none is written, use this one: the screen arrives, and back returns to the screen it came from.
4. The PR's claim. "No behavior change" means every case must look the same on both builds. Anything else means the After side must match what `## 🆕 What's new?` describes.

Read "What's new?" too, so you know which screens the PR touches. Step 2 compares the cases against that.

Write down an expected result for each case before recording, from the pass condition and the claim. A no-diff case passes when After looks and behaves like Before and the pass condition holds. A behavior change case passes when After shows what "What's new?" describes and nothing else changed.

If the prerequisites name no account and the app needs one, use a pool account on dev (see "Dev accounts") and ask nothing. On prod, or when the case needs an account type the pool doesn't have (an organization member, a paid tier, a specific course), ask the requester in the thread before building.

### 2. Judge coverage

Check the cases against the screens the PR touches:

1. Every way in: each caller, deep link and debug shortcut.
2. Back on every screen the case passes through. On Android that is system back and the in-app back arrow; on iOS the swipe and the navigation bar button.
3. The error or offline state when the screen loads data.
4. Rotation, backgrounding and process death when the change touches navigation, lifecycle or saved state. The Lifecycle check runs these even when the list does not. `SpeakActivity` is portrait-locked, so on Android rotate by emulating a tablet: `adb shell wm size 1600x2560; adb shell wm density 280; adb shell wm user-rotation lock 1`, then restore with `wm user-rotation lock 0; wm size reset; wm density reset`. On Android: Home, then `adb shell am kill <package>`, relaunch ("Don't keep activities" leaves the activity alive on the API 36 image). On iOS: background the app, `xcrun simctl terminate <simulator> <bundle id>`, relaunch. Do not swipe it away in the app switcher; that discards restoration state.
5. Gated state (flag, account type, server state) with a way to reach it, or a `patch=` to hard-code it on both builds.
6. Analytics or screen-view events when the change touches lifecycle.
7. A screen that opens the changed screen and reacts to what it returns.

Write each gap as a case in the author's style, one line each.

In `mode=run`, do not post proposals and do not edit the section. Record the author's list as written. Before recording, check in code that each case reaches the changed path. If a written step takes another route (a snackbar instead of a dialog, a deep link that does not route), run the route that reaches the change on both builds, and say so in a numbered note and in the thread. If you found gaps, end the thread report with "Not covered by the list" and one line per gap, three at most, with no case labels (the author may add cases later and the labels would collide).

When the request itself asks you to add missing cases and go (for example "Add the cases you think are missing and go"), append gaps as cases with the suffix `(added by QA)` until the list has 8 cases, most important gap first. Never drop an author's case to stay under 8. If the author's list already has 8 or more, add none. Put the gaps you did not add under "Not covered by the list", as above.

In `mode=review`, post the proposals in the thread and stop. Start the proposals with the prerequisites the cases need and the section does not state, or states wrong: one line per flag or experiment with its value and where to set it (Debug Menu > Feature flag override on Android, `speak-dev://set-split-overrides?<flag>=on` on iOS dev, the debug screen on iOS prod), plus account type and language pair when missing. Take them from the code path each case reaches. When the author agrees, add them to the prerequisites in "How to test?" with the suffix `(added by QA)`, and fix a wrong flag in place with the same suffix. Resume only when the author answers. "Go" means record the author's list. "Add B and C" means append the agreed cases to "How to test?" with the suffix `(added by QA)`, then record all of them. No answer means nothing is recorded, and the thread says so.

### 3. Build both sides

1. Before is the PR's merge-base with its base branch. After is the PR head. Write down both full SHAs.
2. Same build on both sides. With `env=dev`: on Android `developDebug` (package `com.selabs.speak.dev`), on iOS the `Speak-Dev` scheme. With `env=prod`: on Android `productionDebug` (package `com.selabs.speak`), on iOS the `Speak` scheme in the Debug configuration. Write the environment in the status line and the toggle.
3. Same device or simulator, same account, same flags and experiment variants, same debug settings.
4. Start the build in the background before you set up the emulator and the account, and block on it with `get_output` and a long timeout. Don't poll it with `sleep`.
5. A QA-only patch (a repository method returning a fixed value, a forced error) is applied with `git apply` to both working trees and reverted after the run. It is never committed. Its diff goes in the packet toggle.

### 4. Record

1. One recording per build, every case in order, one timestamp per case written down as you go. Playback at 4x is fine; say so in the status line.
2. Drive the UI with one script per build and assert each arrival from the view hierarchy (see Cost). On Android, the taps and waits come from Maestro flows in devin-qa-flow, reused or added there (see "Reusable flows"), and the rest from the bundled harness (see "Android harness"); never write a new harness per run. On iOS, the macOS child does the same with the iOS flows in devin-qa-flow, following its `docs/qa-pr-instructions.md` "iOS runs". Record that scripted run; do not record a separate pass by hand. Keep each case's assertion output; the toggle cites it.
3. At each case's arrival point take a full resolution screenshot on both builds (`adb exec-out screencap -p`, or `xcrun simctl io <simulator> screenshot <file>`). Compare the pair, not the webp, for small visual differences. Keep the lifecycle log streaming for the whole run on both builds (see Lifecycle check).
4. On Android, run `adb shell screenrecord` per case and concatenate the files. On iOS, run `xcrun simctl io <simulator> recordVideo --codec h264 --force <file>` per case, stop it with `kill -INT` and wait for the process to exit.
5. A case you cannot reach is recorded as "unreachable" on both sides. Never skip one silently. Any unreachable case makes the verdict `QA incomplete.`
6. GitHub renders an animated webp or gif inside `<img src="..." height="500" />`. It does not render an mp4 inline, and the PR update tool rejects mp4 paths. Convert each recording to an animated webp (for example `setpts=PTS/4,fps=5,scale=320:-1`, libwebp q60, under 10 MB) and embed it by local path; the PR update tool uploads it to GitHub.
7. Link the mp4 under the table only when it has a host whose link still works a month later (on iOS, the `artifact-upload` skill's GCS bucket). Never use a presigned link that expires in days, or a Devin attachment link, which needs a Devin login. Without such a host, attach the mp4s to the thread reply only.

### 5. Write the PR description

Edit the description. QA and reviewers read the description and miss comments. Change only `## 📸 Can I see?`. Everything else in the body stays as the author wrote it, including a `Local checks` toggle if there is one, which goes after your toggle.

The section, top to bottom:

1. One status line that starts with the verdict. "QA passed. All 4 cases match develop, as the PR claims. Recordings play at 4x." or "QA passed. Cases 1 and 2 show the new sheet from What's new, 3 and 4 match develop." or "QA failed. Case 6 differs from develop and the PR claims no behavior change, see the toggle." or "QA incomplete. Cases 1 to 3 pass, 4 is unreachable without an org account."
2. The table. Base on the left, branch on the right, one timestamp per case under each video:

   ```
   | Before (develop `<short sha>`) | After (this branch `<short sha>`) |
   | --- | --- |
   | <img src="<develop webp>" height="500" /> | <img src="<branch webp>" height="500" /> |
   | 1. <case> 0:00<br>2. <case> 0:07<br>3. <case> 0:19 | 1. <case> 0:00 pass<br>2. <case> 0:10 pass<br>3. <case> 0:22 pass |
   ```

   Put each case's result (pass, fail, note, unreachable or unverified) after its timestamp on the After side. With more than six cases, drop the timestamp row and put a `| Case | develop | branch | Result |` table under the videos instead, with the result in the Result column.
3. One collapsed toggle. `<details><summary>No-diff run (develop vs branch)</summary>` when the PR claims no behavior change. `<details><summary>QA packet</summary>` when it changes behavior. Inside, in this order: device and build details with both full SHAs, account email (never the password) and flags, one line per case (result, same or differs, what followed each tap, the check behind the result, and lifecycle same or differs), the full resolution screenshot pair per case as a `| develop | branch |` table with `width="300"` images, the lifecycle log diff per case (join consecutive lines per controller or entry when the body gets long) and the `Lifecycle:` lines, the QA-only patch diff if any, then whatever `extras=` asked for. A case that needs more than one line gets a numbered note after the list.
4. If the author left placeholders such as `_recording pending_`, replace them. Do not add a second table.

### 6. Report where the request came from

Reply in the same thread, comment or issue, tagging the requester. In Slack, the tag must be a real mention: the raw `<@USERID>` token with the ID taken from the request message (a person, or a bot such as seanbot2 `U0C9M343A8J`). Don't hardcode one ID, because the requester varies. `@user:<id>`, `@name` and bare names render as plain text and ping nobody. The first line is the verdict and its reason, for example "QA passed. All 4 cases match develop, as the PR claims." Attach the two full resolution mp4s. Then:

1. The two SHAs and the build configuration.
2. One line per case: label, result, same or differs, what you saw, the check behind the result, and lifecycle same or differs. Start each line with the case's timestamps in the attached full speed mp4s, base then branch (`1. 0:00 / 0:00`). These are not the 4x webp timestamps from the PR table; take them from the mp4s. A note line says what both builds did. Then the `Lifecycle:` lines, if any.
3. The PR link.
4. In `mode=run`, the "Not covered by the list" lines, if any.
5. The `ID PR:` line: the ID PR this run opened or commented on for each screen (see Missing IDs in devin-qa-flow's `docs/qa-pr-instructions.md`), or `ID PR: none needed` when no flow used a text or point fallback. Every report has this line, including commit and release sweeps; a request with no PR still gets its ID PR (Missing IDs step 3 says who authors it). Post the ID PR itself in #devin-qa-flow (`C0CDW7WKWGN`), not in this thread, with devin-qa-flow's `scripts/slack-id-pr-post.sh "<@U06CM4TRNBX> ID PR for <screens>, ready for review: <PR URL>"` (Missing IDs step 4), then put the details and a link to this QA thread in a reply to that post. Don't post the report until this line is true.
6. The `Run time:` line (see Run record).

When the request did not come from a PR comment, also leave a one-line PR comment, for example "QA passed (4/4). Results in Can I see?", so the author gets a notification; a description edit sends none.

With `post=linear` or `post=both`, also comment on the linked Linear issue. No videos there. Use this shape:

```
QA passed. All 4 cases match develop, as the PR claims.
PR: speak-android#7837 (developDebug, develop a1b2c3d vs branch e4f5a6b)

1. <case>: pass, same
2. <case>: pass, same

Flags: <flag> = on (Debug Menu > Feature flag override)
Recordings and per-case checks: PR description, "Can I see?"
Slack thread: <link>
```

On a fail, the first line names the failing case and each failing case gets one extra line with what it saw.

If a case differs and the PR claims no behavior change, name the case and stop there, even when a case on the branch behaves better than the base. Marking the PR ready, requesting approval, merging and fixing conflicts are outside this skill. Do them only when the same request asks for them explicitly, and only after every case matches the PR's claim.

## How to write

These rules apply to the PR text, the proposals and the thread reply:

1. Lead with the verdict. The first line starts with `QA passed.`, `QA failed.` or `QA incomplete.` (or, in `mode=review`, what you need from the author).
2. Numbered cases, one line each. At most five visible items per group; the rest goes in the toggle.
3. No bold labels, no "Label: sentence" bullets, no "not X but Y", no em or en dashes (ranges use "to"), no opener, no closer.
4. Short plain sentences, one fact each. Keep every SHA, timestamp, count and link.
5. A failure is a cause and what you saw. No "unfortunately", no apology.

## Platform notes

### iOS requests on a Linux machine

A Linux machine can read the PR but cannot build or record. Do only the reading there and hand the run to one macOS child session. The parent's cost is mostly wakeups: on speak-ios#9275 it woke five times in 37 minutes to check on the child.

1. Read the test instructions and judge coverage on Linux (steps 1 and 2). In `mode=review`, post the proposals and wait for the author there.
2. Start one child with `devin_session_create`, `platform: "macos"`, repo `usespeakeasy/speak-ios`, `notify_on_response: true`. Its prompt holds the whole request: the PR link, the fields, the final case list with labels and expected results, both SHAs, and the thread with the requester. The child runs steps 3 to 5 and does not re-read or re-judge the cases. Paste the Cost section into the prompt and say the child follows it.
3. Post the child link in the thread, then end your turn. Do not poll the child with `wait`, `get` or `get_messages`. The notification wakes you when it finishes or blocks.
4. When it arrives, read the child's last message and attachments once, post the step 6 report with its verdict and videos, and stop.

When the request starts on a macOS machine, run everything there.

### Dev (`env=dev`)

On Android the dev build is the `developDebug` flavor, package `com.selabs.speak.dev`. Flags and debug settings live in the in-app Debug Menu (`speak-dev://debug-menu`). Deep links use the `speak-dev://` scheme, for example `speak-dev://lesson?id=<lesson id>`. Some screens need the API 36 emulator started with `-gpu swangle_indirect`.

On iOS the dev build is the `Speak-Dev` scheme, run on one simulator for both builds. A Linux Devin machine has no Xcode or simulator. Run iOS requests on a macOS Devin machine; from Linux, hand off as described in "iOS requests on a Linux machine", and say so in the thread before building. Never put a password from `email-login` in the PR or the thread. Experiment variants are set with `xcrun simctl openurl <simulator> 'speak-dev://set-split-overrides?<flag>=on'` and sign-in with `speak-dev://email-login?email=...&password=...`. The repo's `deep-links` skill lists the rest.

### Dev accounts

Use a pool account for every dev run, on both builds. The pool is onboarded dev accounts (`devin+qa-pool-NN@usespeak.com`, Spanish A1 unless the table's `note` says otherwise) in BigQuery table `speak-v2-2a1f1.devin_qa.qa_account_pool`. One shared password is the org secret `QA_POOL_PASSWORD`. A lease keeps concurrent runs from sharing an account's server state.

1. Lease before building: `qa_android.py lease --holder <your session URL>`. It claims one free account with an atomic `UPDATE`, prints the email and keeps it in `~/.qa_lease`. A lease older than 4 h counts as free, so a crashed session doesn't hold its account.
2. On Android, `qa_android.py login` signs in as the leased account through the DebugBridge and waits for Home, dismissing the premium intro and permission prompts. On iOS, use `speak-dev://email-login?email=...&password=...`.
3. Release after the step 6 report is posted, and on any early stop: `qa_android.py release`. A macOS child leases and releases its own account.
4. If every account is leased, sign up a fresh account as before and say so in the toggle.
5. If a pool account can't reach Home (deleted, stuck in a state), set its `note` and `holder = 'broken'` so nobody leases it, and tell the requester in the toggle.
6. To refill the pool: `qa_android.py bridge signUp email=devin+qa-pool-NN@usespeak.com password=$QA_POOL_PASSWORD name=QAPoolNN`, relaunch, run `qa_onboard.py` (next to `qa_android.py`) until it prints HOME, then insert the row with `platform='android', env='dev'`.
7. Sign up a fresh account only when a case needs a new user (signup, onboarding, first-run prompts). Run those cases as pre-auth flows: `qa_android.py fresh` clears the app, `qa_android.py newuser` prints a throwaway email for the flow's `-e EMAIL`, and devin-qa-flow's "Pre-auth flows" section has the rest. A throwaway account never joins the pool. Don't leave an account in state the next run would trip on: undo a changed course or setting before releasing, or put one line in the row's `note` when you can't.

### Prod (`env=prod`)

Use a debug build pointed at production, never a store or release build, so the debug tools stay available.

On Android build `productionDebug` (`./gradlew :app:assembleProductionDebug`, package `com.selabs.speak`). Deep links use the `speak://` scheme, for example `speak://lesson?id=<lesson id>`. The Debug Menu opens at `speak://debug-menu` or by shaking, because a debug build type always allows it. Feature flag override and Subscription override work the same as on dev. The prod and dev apps install side by side, so check that `adb` commands name `com.selabs.speak`. Launch with `adb shell am start -n com.selabs.speak/com.selabs.speak.SpeakActivity`.

On iOS run the `Speak` scheme (Debug configuration, bundle id `com.selabs.speak-v2`, URL scheme `speak://`). The agent deep links (`set-split-overrides`, `email-login`, `debug`, `preview`, `set-user-defaults`) only work on dev builds. On prod, sign in through the UI and set flags in the debug screen (shake, or Settings > Debug), which a Debug build always allows. The QA-Prod scheme is the CI Enterprise build (`build-prod` PR label), not a local QA build.

Prod rules:

1. Use a test account the requester names. Ask in the thread if none is named. Never sign up a new prod account and never use a real customer's account.
2. No real purchases. Use Subscription override (Android) or the debug screen (iOS) for tier states. If a case needs a real purchase, mark it unreachable.
3. Do not change server-side state the account cannot undo (deleting the account, changing the course, sending referrals) unless the case asks for it. Say in the toggle that the run sent analytics events to production.

### Android Google sign-in

Test Google sign-in with the real Google account `qa@usespeak.com`, never a stubbed or hardcoded ID token. Its secrets are `PLAY_TESTER_EMAIL`, `PLAY_TESTER_PASSWORD` and `_2FA_PLAY_TESTER` (a TOTP code). Bind them in the exec `env` and type them with `adb shell input text`. Never print them.

1. The session network allowlist needs `*.google.com`, `*.gstatic.com`, `accounts.youtube.com` and `*.googleusercontent.com`. Without them, Settings shows "Something went wrong" when adding the account. Request them with `request_network_access` before building.
2. Add the account once per AVD: Settings > Add account > Google, SKIP the phone screen, email, password, then Try another way > Google Authenticator and the `_2FA_PLAY_TESTER` code. Accept the terms. The default `google_apis` image works; Play Store is not needed.
3. Set a screen lock before the first in-app sign-in: `adb shell locksettings set-pin 1234`. The account's Workspace policy requires one. Without it Google opens a lock screen setup in the middle of sign-in and the app gets `ApiException 12501` and "An unexpected error occurred."
4. In the app: Log in, Continue with Google, pick `qa@usespeak.com` in "Choose an account". The check is `Track 'signedIn' {provider=google.com}` and the Home tree (`home_root_ready`), after the notification prompt (Don't allow, Set up later, OK).

### Android harness

`qa_android.py` from the `qa-android-harness` skill (find it with `ls /opt/.devin/plugins/cache/*/*/skills/qa-android-harness/scripts/qa_android.py`) runs one step per command, and each command blocks until it's done. `qa_android.py --help` lists them: `emu` (start or reuse the emulator with the stable flags, wait for boot, disable animations), `install`, `lease`, `login`, `release`, `launch`, `bridge`, `wait`, `tap`, `has`, `type`, `dump`, `shot`, `logcat`, `logstop`, `mark`, `rec`, `stop` (stop screenrecord cleanly, pull, ffprobe) and `webp`. Selectors are `id:<resource-id>`, `text:<regex>` or `desc:<regex>`. `wait` and `tap` re-dump until the node appears and tap from that same dump.

Write each run's cases as one shell script with `set -e`: per case a `mark` and `rec`, the case's `maestro test` flow (see "Reusable flows"), the arrival `wait`, a `shot` and `stop`. A case no flow covers yet gets a new flow, not harness taps.

- Call the harness at its install path (`H=$(ls /opt/.devin/plugins/cache/*/*/skills/qa-android-harness/scripts/qa_android.py)`, then `python3 $H <command>`). Don't copy it, and don't wrap it in your own `run.py`, `lib/` or helper module.
- The case script is bash, and nearly every line is a `python3 $H ...` call. Plain `adb` lines are only for what the harness doesn't do: a deep link (`am start -d`), `am force-stop`, a back `keyevent`, or a settings toggle.
- To find selectors before writing the script, run `python3 $H dump`, or `has` / `wait` on a guess. Don't probe with `tap && sleep && shot` chains or open screenshots to see where you are.
- Before the first run, `grep -nE 'input tap|screencap|uiautomator|sleep [0-9]{2,}' <script>` must print nothing. If it prints a line, replace that line with the matching harness command: `tap`, `shot`, `dump` or `wait`.

Run the script in the foreground with a long exec timeout, or in the background and block with `get_output`. A failing step exits nonzero right away, so fix that case and rerun it alone. Don't `sleep` or call `wait` for more than 30 s to watch a script.

### Reusable flows (devin-qa-flow)

Case steps live as Maestro flows in `usespeakeasy/devin-qa-flow`, shared by every QA run. Developers don't write them; QA runs reuse them and add what's missing. That repo owns every flow instruction: finding and writing flows, running them on both builds, credentials and Maestro debug logs, two emulators at once, missing-ID PRs, pushing flows back, and how to write the PR and Slack posts.

1. Clone or pull it: `git clone https://github.com/usespeakeasy/devin-qa-flow ~/repos/devin-qa-flow`, or `git -C ~/repos/devin-qa-flow pull --rebase`. Then write down `git -C ~/repos/devin-qa-flow rev-parse HEAD` for the run record's `flow_repo_sha`.
2. Before touching a flow, read its `AGENTS.md` and the file it points to (`docs/qa-pr-instructions.md`), and follow them. Where they and this skill disagree about flows, the repo wins.

Maestro is at `~/.maestro/bin/maestro`. If it's missing, install it with `curl -fsSL "https://get.maestro.mobile.dev" | bash`.

### Android capture

- If the emulator desktop window is stale but `adb exec-out screencap -p` shows current pixels, use scrcpy as the visible recording surface. A static Linux release can run with `ADB=$HOME/android-sdk/platform-tools/adb ./scrcpy --no-audio --max-size 1200 --max-fps 60`. Maximize or use its fullscreen shortcut (Alt+F).
- Prefer native `adb screenrecord` for compact raw evidence; a fullscreen scrcpy recording also works. Keep original-speed footage. Automatically edited desktop recordings may skip feedback holds and are unsuitable for timing evidence; use the recorder's raw MKV remuxed to MP4 instead.
- State the measurement endpoints. UI feedback first appearing to next-card first appearing includes rendering/scheduling overhead, so it is not an exact internal delay measurement. Inspect frame timestamps, not 4x/5fps previews, for countdown behavior.

### Android Drill mock recognition

- Quote the complete ADB shell command, then quote text inside it, or multi-word text can be truncated by remote shell parsing:
  `adb shell "am broadcast -n com.selabs.speak.dev/com.selabs.speak.devtools.bridge.DebugBridgeReceiver -a com.selabs.speak.dev.BRIDGE --es cmd mockRecognition --es text 'Y tú, ¿qué tal?' --es locale es-ES --es isSuccess true"`
- Confirm the bridge response includes the complete text. A failure can be injected with text `banana`, `--es confidence 0.1 --es isSuccess false`. Use the shipped bridge only when the requester authorizes simulated speech, and disclose it.
- Do not tap any word when testing onboarding tooltip recurrence. Read-only inspection of the per-user pronunciation preferences can confirm `pronunciation_coach_word_tapped=false`.
- Published lesson `EN_ES_A1-1_quetal_SP_DL_IC` has loaded a real Drill with usable audio. It is a fallback, not a permanent guarantee: old temporary lesson audio may return 404. Confirm actual pixels and tooltip before recording.
- After APK replacement, let the app reach Home before deep-linking. Repeated lesson deep links during initialization can leave a blank route over the loaded lesson; return to Home and open one link again.

### Android emulator stability

Emulator crashes, corrupt recordings and retry loops made up a third or more of the time on the most expensive Android runs. Set up once, check each file as it lands, and redo only what broke.

- Start the emulator with an explicit GPU and keep it for both builds (or one per build, see devin-qa-flow `docs/qa-pr-instructions.md`): `qa_android.py emu` runs `emulator -avd devin -no-audio -no-boot-anim -no-snapshot -memory 4096 -gpu swangle_indirect` and waits until `sys.boot_completed` is `1`. The gfxstream default can die in long runs, and `swiftshader_indirect` crashes on the Free Talk tab.
- Stop `adb shell screenrecord` with `adb shell pkill -INT screenrecord` and wait for it to exit before pulling. Any other stop can leave an mp4 with no moov atom. It also stops by itself at 180 s, so keep one file per case.
- Run `ffprobe` on each recording right after pulling it. Re-record only the case whose file fails.
- `uiautomator dump` can return an empty or stale tree during a transition. Re-dump until the node you assert appears, with a timeout, and never tap from a stale dump.
- After a crash (`adb devices` empty or the emulator process gone), restart with the same command, wait for boot and relaunch the app. The AVD data partition keeps the install and the login. Resume at the case that failed, not at case 1.
- `market://` links need a `google_apis_playstore` system image. On the default image, mark those cases unreachable.
- Two strikes. When the same case fails twice for a reason outside the PR (an emulator crash, server state such as a counter or prompt that a fresh account does not get), stop retrying. Mark it unreachable on both builds, or ask in the thread with what you saw. Do not loop through fresh or pool accounts.

## Worked example

Request: `@Devin qa-request-mobile https://github.com/usespeakeasy/speak-android/pull/7837`

The PR is a prep PR that says "No behavior change" and lists four cases on a drill lesson's options sheet. Both builds were `developDebug` on one API 36 emulator with the same signed-in account and flags. The description got the status line "QA passed. All 4 cases match develop, as the PR claims. Recordings play at 4x.", the Before | After table with four timestamps per side and "pass" on each After case, and a "No-diff run" toggle with both SHAs, one line per case citing its Maestro assertion, a screenshot pair per case and the lifecycle logcat lines. The thread got the requester tag, the "QA passed." line, the two mp4s, the SHAs and four "pass, same" lines.
