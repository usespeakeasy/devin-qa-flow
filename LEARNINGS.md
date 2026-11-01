# Learnings

What went wrong in past QA runs and the rule that prevents it. Read this before a run. Add to it
after a major failure, as [docs/qa-pr-instructions.md](docs/qa-pr-instructions.md#learnings)
describes.

## Android

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

## iOS

- The permission-off case (A4) did not get the "Allow notifications" alert, and about 15 min
  went to finding out why. Cause: Maestro `launchApp` `permissions: {notifications: deny}` has
  no effect on the iOS 27 simulator and `simctl privacy` has no notifications service. Rule:
  turn notifications off in iOS Settings; `ios/common/system-notifications-off.yaml` does
  this. Use a toggle on a UIKit screen that refreshes on foreground
  (`CompactNotificationSettingsVC`), not Marketing Communications, which does not.
  ([dry run of speak-ios#9662](https://github.com/usespeakeasy/speak-ios/pull/9662), 2026-11-01)
