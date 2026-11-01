# Learnings

What went wrong in past QA runs and the rule that prevents it. Read this before a run. Add to it
after a major failure, as [docs/qa-pr-instructions.md](docs/qa-pr-instructions.md#learnings)
describes.

## Android

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

## iOS

- The permission-off case (A4) did not get the "Allow notifications" alert, and about 15 min
  went to finding out why. Cause: Maestro `launchApp` `permissions: {notifications: deny}` has
  no effect on the iOS 27 simulator and `simctl privacy` has no notifications service. Rule:
  turn notifications off in iOS Settings; `ios/common/system-notifications-off.yaml` does
  this. Use a toggle on a UIKit screen that refreshes on foreground
  (`CompactNotificationSettingsVC`), not Marketing Communications, which does not.
  ([dry run of speak-ios#9662](https://github.com/usespeakeasy/speak-ios/pull/9662), 2026-11-01)
