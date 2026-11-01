---
name: qa-android-harness
description: Scripts for Android emulator QA on speak-android (emulator boot, dev pool account lease/login/release, signed-out reset and throwaway sign-up emails, fresh-tree wait/tap, screenshots, screenrecord with ffprobe, logcat marks, webp). Use when running a qa-request-mobile Android run or any scripted emulator walk of the Speak dev app.
metadata:
  version: 2026.11.01.2
---

# Android QA harness

`scripts/qa_android.py` runs one QA step per command and blocks until it's done. `qa_android.py --help` lists the commands. `scripts/qa_onboard.py` walks a freshly signed-up dev account through onboarding to Home; use it only to refill the dev account pool.

Find the scripts with `ls /opt/.devin/plugins/cache/*/*/skills/qa-android-harness/scripts/`. `qa_android.py emu --avd devin2 --port 5556` boots a second emulator (the AVD is cloned from `devin` on first use). Set `ANDROID_SERIAL` for every command when more than one emulator is running; `logcat`/`logstop` keep one background logcat per serial. The `qa-request-mobile` skill says when to use each command.

For pre-auth cases, `qa_android.py fresh [--no-grant]` clears app data and cold-starts the app on the welcome screen, and `qa_android.py newuser` prints a throwaway sign-up email (`devin+qa-new-<time>-<random>@usespeak.com`) that never joins the pool.
