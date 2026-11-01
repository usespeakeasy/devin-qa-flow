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
- A Maestro flow that cycled a Debug Menu feature flag chip asserted `SERVER` and passed while the flag stayed `LOCAL · on`, so a later case ran with the kill switch on. Cause: right after typing in the flag search, the unfiltered list is still on screen, so `rightOf: <flag>` and label regexes match other flags' rows. Rule: after setting a flag, read the row with harness `dump` and check the `<SOURCE> · <value>` label under the flag key before running a case; confirm the path in logcat (`navigation=nav3` vs `conductor`). ([QA of speak-android#8630](https://github.com/usespeakeasy/speak-android/pull/8630), 2026-11-01)
- On tablet emulation, a case that dies on a `wait` (set -e) leaves `wm size 1600x2560` and rotation lock on, and the next harness steps miss their nodes. Rule: `trap` the `wm ... reset` lines on EXIT in the case script. ([QA of speak-android#8630](https://github.com/usespeakeasy/speak-android/pull/8630), 2026-11-01)

## iOS

None yet.
