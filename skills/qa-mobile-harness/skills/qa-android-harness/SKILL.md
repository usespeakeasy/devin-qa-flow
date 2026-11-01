---
name: qa-android-harness
description: Scripts for Android emulator QA on speak-android (emulator boot, dev pool account lease/login/release, fresh-tree wait/tap, screenshots, screenrecord with ffprobe, logcat marks, webp). Use when running a qa-request-mobile Android run or any scripted emulator walk of the Speak dev app.
metadata:
  version: 2026.11.01.1
---

# Android QA harness

`scripts/qa_android.py` runs one QA step per command and blocks until it's done. `qa_android.py --help` lists the commands. `scripts/qa_onboard.py` walks a freshly signed-up dev account through onboarding to Home; use it only to refill the dev account pool.

Find the scripts with `ls /opt/.devin/plugins/cache/*/*/skills/qa-android-harness/scripts/`. `qa_android.py emu --avd devin2 --port 5556` boots a second emulator (the AVD is cloned from `devin` on first use). Set `ANDROID_SERIAL` for every command when more than one emulator is running; `logcat`/`logstop` keep one background logcat per serial. The `qa-request-mobile` skill says when to use each command.
