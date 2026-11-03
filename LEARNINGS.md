# Learnings

What went wrong in past QA runs and the rule that prevents it. Read this before a run. Add to it
after a major failure, as [docs/qa-pr-instructions.md](docs/qa-pr-instructions.md#learnings)
describes.

## Android

- A base case ran with `ai_data_consent_mode` = `LOCAL · lert_only` (an unknown treatment, so no alert) and passed as "no alert". Cause: `set-custom-treatment.yaml` typed into Treatment before the keyboard settled and dropped the first character, and its final assert only matched a substring. Rule: the flow now waits for the animation, asserts the exact typed text and `LOCAL · <treatment>`; still read `debug_feature_flag_source_<flag>` after every override. ([QA of speak-android#8807](https://github.com/usespeakeasy/speak-android/pull/8807), 2026-11-03)
- On dev, Start on a new account's first learning path loop ("[PROD-CLONE] Ask someone to take your picture") logs `Course Learning Loop CTA Tapped` and opens nothing, on base and branch, so the AI data alert never shows. Rule: reach the lesson-start site through the second loop's Preview (`common/start-path-lesson.yaml`). Throwaway accounts also get the premium intro with "An unexpected error occurred." after each sign-in: OK, then Back. ([QA of speak-android#8807](https://github.com/usespeakeasy/speak-android/pull/8807), 2026-11-03)
- A sign-in case timed out on `home_root_ready` twice and its recording reached 182 s. Cause: pool accounts with a frozen streak get a "We saved your N-day streak!" bottom sheet over Home after every sign-in, and it hides `home_root_ready`. Rule: `common/dismiss-premium-intro.yaml` now closes it with Back; after `qa_android.py login` times out, check for the sheet and press Back. ([QA of speak-android#8339](https://github.com/usespeakeasy/speak-android/pull/8339), 2026-11-02)
- Superwall paywalls never presented on the `google_apis` AVD: `PaywallPresentationRequest` ended `no_presentation` with `status_reason=subscription_status_timeout`, and the app showed the native premium screen with "An unexpected error occurred." Cause: that image's `com.android.vending` is a 1.8 stub, so Play Billing is unavailable even with a Google account added ("Billing service unavailable on device"). Rule: for paywalls, purchases or subscription status, use a `google_apis_playstore` AVD (`sdkmanager "system-images;android-36;google_apis_playstore;x86_64"`, `PlayStore.enabled=yes`), add `qa@usespeak.com` (licensed tester) and test on `productionRelease`. The Superwall paywall then opens; with `setprop log.tag.FA-SVC VERBOSE` and `setprop debug.firebase.analytics.app com.selabs.speak`, logcat shows `Superwall_Paywall_Open` with `presented_by_event_name` and `user_attributes.appUserId`. ([QA of speak-android#8339](https://github.com/usespeakeasy/speak-android/pull/8339), 2026-11-02)
- A cold start through `speak-dev://profile/settings` (`stopApp`, then `openLink`) landed on Home, not Settings, in 4 of 5 tries on develop `0f19e5556c` and 4 of 4 on a branch, on a signed-in pool account; Superwall still logged its `DeepLink` event each time. Cause: not found. Rule: don't use a cold deep link to reach Settings; open it from Profile instead. ([QA of speak-android#8339](https://github.com/usespeakeasy/speak-android/pull/8339), 2026-11-02)
- A run lost its base screenshots and had to rerun the base light and dark passes (about 15 min). Cause: a flow's `env:` default (`SHOT: arrival`) won over `maestro test -e SHOT=<path>`, so `takeScreenshot: ${SHOT}` wrote `arrival.png` inside the `--debug-output` folder, and the case script deleted that folder at the end. Rule: copy `<debug-output>/**/takeScreenshot/*.png` into the run folder right after each `maestro test`, before deleting the debug folder. (QA of the speak-android 4.73 Navigation 3 release sweep, 2026-11-01)
- A process death case relaunched with `adb shell monkey -p com.selabs.speak.dev -c android.intent.category.LAUNCHER 1` and opened LeakCanary's launcher activity on one build, so that build's restore check was invalid and both builds had to be rerun. Cause: the dev app has two LAUNCHER activities and monkey picks one at random. Rule: relaunch after `am kill` with `adb shell am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -f 0x10200000 -n com.selabs.speak.dev/com.selabs.speak.SpeakActivity`, which brings the killed task back with its saved state. ([QA of speak-android#8665](https://github.com/usespeakeasy/speak-android/pull/8665), 2026-11-01)
- Second emulator hung on boot, waiting on a crash-report consent dialog. Cause: crash data
  left by a force-killed emulator under `/tmp/android-*/emu-crash-*.db`. Rule: delete it before
  booting; harness `emu` now does this. ([dry run of speak-android#8617](https://github.com/usespeakeasy/speak-android/pull/8617), 2026-11-01)
- One emulator died and peak host RAM hit 24 GB of 31. Cause: Gradle and Kotlin daemons left
  running after the build hold about 13 GB. Rule: `./gradlew --stop` in every worktree and check
  `pgrep -f GradleDaemon` is empty before booting two emulators. ([dry run of speak-android#8617](https://github.com/usespeakeasy/speak-android/pull/8617), 2026-11-01)
- A sign-in case took 179 s, one second under the `screenrecord` limit. Cause: Maestro
  `eraseText` (~15 s) on fields that were already empty. Rule: don't erase empty fields; keep
  each case under 180 s. ([dry run of speak-android#8617](https://github.com/usespeakeasy/speak-android/pull/8617), 2026-11-01)
- The pool password appeared in plain text in Maestro's debug logs. Cause: Maestro logs typed
  text to `~/.maestro/tests/` by default. Rule: `--debug-output /tmp/maestro-<serial>/<case>`,
  filter the password from console output, delete the folder after the run. ([dry run of speak-android#8617](https://github.com/usespeakeasy/speak-android/pull/8617), 2026-11-01)
- A Maestro flow that cycled a Debug Menu feature flag chip asserted `SERVER` and passed while the flag stayed `LOCAL · on`, so a later case ran with the kill switch on. Cause: right after typing in the flag search, the unfiltered list is still on screen, so `rightOf: <flag>` and label regexes match other flags' rows. Rule: after setting a flag, read the row with harness `dump` and check the `<SOURCE> · <value>` label under the flag key before running a case; confirm the path in logcat (`navigation=nav3` vs `conductor`). ([QA of speak-android#8630](https://github.com/usespeakeasy/speak-android/pull/8630), 2026-11-01)
- On tablet emulation, a case that dies on a `wait` (set -e) leaves `wm size 1600x2560` and rotation lock on, and the next harness steps miss their nodes. Rule: `trap` the `wm ... reset` lines on EXIT in the case script. ([QA of speak-android#8630](https://github.com/usespeakeasy/speak-android/pull/8630), 2026-11-01)
- Back on the lesson end progress wait spinner landed after the check-in had already replaced it, so the base case failed. Cause: a separate `maestro test` for the back step started about 15 s after the opener ended, longer than the 12 s QA hold. Rule: for a step that lasts only seconds, run the opener and the action in one Maestro run (a wrapper flow with two `runFlow`s and a `takeScreenshot` between them). ([QA of speak-android#8690](https://github.com/usespeakeasy/speak-android/pull/8690), 2026-11-02)
- A process death case ran `am kill` right after `KEYCODE_HOME` and the process lived on (same pid in logcat), so the relaunch only brought the task to the front. Cause: `am kill` only kills a cached background process, and the app is not cached yet just after Home. Rule: record `pidof` before, retry `am kill` once a second until `pidof` is empty, and log both pids with the case. ([QA of speak-android#8690](https://github.com/usespeakeasy/speak-android/pull/8690), 2026-11-02)

## iOS

- The permission-off case (A4) did not get the "Allow notifications" alert, and about 15 min
  went to finding out why. Cause: Maestro `launchApp` `permissions: {notifications: deny}` has
  no effect on the iOS 27 simulator and `simctl privacy` has no notifications service. Rule:
  turn notifications off in iOS Settings; `ios/common/system-notifications-off.yaml` does
  this. Use a toggle on a UIKit screen that refreshes on foreground
  (`CompactNotificationSettingsVC`), not Marketing Communications, which does not.
  ([dry run of speak-ios#9662](https://github.com/usespeakeasy/speak-ios/pull/9662), 2026-11-01)

- Android emulator 1080x2400: a held `adb shell input swipe` that starts at y 144 (16 px below the
  128 px status bar) opens the notification shade on about 2 of 3 tries on every screen, on develop
  too and with no sheet showing. A handle drag check that starts there measures the emulator, not the
  app. Start drags from a top handle at y 169 or lower and read `mCurrentFocus` mid-drag.
  ([QA of speak-android#8706 at dd95dfb](https://github.com/usespeakeasy/speak-android/pull/8706), 2026-11-02)
- Android process death: `adb shell input keyevent 3` straight into `am kill <pkg>` can leave the app
  alive (it is still the foreground process), and the relaunch then logs nothing. Wait 1 s after Home,
  run `am kill`, and check `adb shell pidof <pkg>` is empty before relaunching.
  The leagues animator flows take the learner's current username as `NAME`: after
  `animator-username-save` the defaults screen shows the saved name, not "User 1".
  ([QA of speak-android#8742 at 135244cfd5](https://github.com/usespeakeasy/speak-android/pull/8742), 2026-11-03)
- android tutor-everywhere (2026-11-03, speak-android#8808): after "I want to try this card again in the lesson" the sheet sometimes shows the user bubble and follow-up chips but no tutor reply and no `tutor_everywhere_action_button_retry_card`, while analytics still log `Speak Tutor Action Shown` and `Agent Response Loaded`. Seen on develop 885d2adb52 (1 of 20 tries) and on the PR (4 of 16); the PR does not touch the sheet's reply rendering. `retry-card-from-tutor.yaml` then fails on the action wait; rerun the case alone before calling a fail.
