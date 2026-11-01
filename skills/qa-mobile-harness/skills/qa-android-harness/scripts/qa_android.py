#!/usr/bin/env python3
"""Android QA harness for qa-request-mobile. One command per step, each blocks until done.

  qa_android.py emu [--avd A --port N]    start (or reuse) the emulator, wait for boot, no animations;
                                          --avd devin2 --port 5556 adds a second one (AVD cloned from devin)
  qa_android.py install <apk> [--pkg P]   adb install -r, force-stop
  qa_android.py lease --holder <URL>      claim a free pool account (BigQuery qa_account_pool), print email
  qa_android.py login                     bridge login as the leased account, launch, wait for Home
  qa_android.py release                   free the leased account (run after the report is posted)
  qa_android.py bridge <cmd> [k=v ...]    DebugBridge command, prints the JSON, exit 1 on err
  qa_android.py launch                    force-stop and cold-start SpeakActivity
  qa_android.py wait <sel> [--timeout S]  re-dump until a node matches; prints its bounds
  qa_android.py tap <sel> [--timeout S]   wait, then tap the node's center from that same dump
  qa_android.py type <text>               type into the focused field (spaces kept)
  qa_android.py has <sel>                 exit 0 if a node matches the current tree
  qa_android.py dump [file.xml]           save the current tree, or print id/text/desc/bounds
  qa_android.py shot <file.png>           full-resolution screenshot
  qa_android.py logcat <file>             stream lifecycle tags to <file> in the background
  qa_android.py logstop                   stop the background logcat
  qa_android.py mark <text>               write a QA_MARK line into logcat
  qa_android.py rec <file.mp4>            start screenrecord (one file per case, <180 s)
  qa_android.py stop <file.mp4>           stop it cleanly, pull, ffprobe; exit 1 if broken
  qa_android.py webp <in.mp4> <out.webp>  4x, 5 fps preview for the PR description

<sel> is id:<resource-id>, text:<regex>, desc:<regex>, or a bare regex matched on text then desc.
With two emulators, set ANDROID_SERIAL (e.g. emulator-5556) and QA_LEASE_FILE per emulator for every command.
Env: QA_POOL_PASSWORD (shared pool password), QA_PKG (default com.selabs.speak.dev), ANDROID_HOME (default ~/android-sdk).
"""
import glob
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

SDK = os.environ.get("ANDROID_HOME", os.path.expanduser("~/android-sdk"))
ADB = os.path.join(SDK, "platform-tools", "adb")
EMU = os.path.join(SDK, "emulator", "emulator")
PKG = os.environ.get("QA_PKG", "com.selabs.speak.dev")
ACTIVITY = "com.selabs.speak.SpeakActivity"
AVD_ROOT = os.path.expanduser("~/.android/avd")
LEASE_FILE = os.environ.get("QA_LEASE_FILE", os.path.expanduser("~/.qa_lease"))
POOL = "`speak-v2-2a1f1.devin_qa.qa_account_pool`"
LEASE_HOURS = 4
TAGS = ["SegmentAnalyticsManager", "LoggingLifecycleListener", "ControllerTransactionProvider",
        "EntryBreadcrumbs", "CoreViewModel", "DebugBridge", "QA_MARK", "AndroidRuntime"]


def adb(*args, check=True, timeout=120):
    r = subprocess.run([ADB, *args], capture_output=True, text=True, timeout=timeout)
    if check and r.returncode != 0:
        sys.exit(f"adb {' '.join(args)} failed: {r.stderr.strip() or r.stdout.strip()}")
    return r.stdout


def booted():
    try:
        return adb("shell", "getprop", "sys.boot_completed", check=False, timeout=10).strip() == "1"
    except subprocess.TimeoutExpired:
        return False


def logcat_pid():
    serial = os.environ.get("ANDROID_SERIAL")
    return os.path.expanduser(f"~/.qa_logcat.{serial}.pid" if serial else "~/.qa_logcat.pid")


def ensure_avd(name):
    d = os.path.join(AVD_ROOT, f"{name}.avd")
    if os.path.isdir(d):
        return
    os.makedirs(d)
    cfg = open(os.path.join(AVD_ROOT, "devin.avd", "config.ini")).read()
    cfg = re.sub(r"(?m)^(AvdId|avd\.ini\.displayname)=.*$", lambda m: f"{m.group(1)}={name}", cfg)
    open(os.path.join(d, "config.ini"), "w").write(cfg)
    base = open(os.path.join(AVD_ROOT, "devin.ini")).read()
    open(os.path.join(AVD_ROOT, f"{name}.ini"), "w").write(base.replace("devin.avd", f"{name}.avd"))


def cmd_emu(a):
    avd, port = "devin", None
    for flag, val in zip(a[::2], a[1::2]):
        if flag == "--avd":
            avd = val
        elif flag == "--port":
            port = val
        else:
            sys.exit(f"unknown emu option {flag}")
    if port:
        os.environ["ANDROID_SERIAL"] = f"emulator-{port}"
    serial = os.environ.get("ANDROID_SERIAL")
    if not booted():
        devices = adb("devices", check=False)
        if not serial and devices.count("emulator-") > 1:
            sys.exit("more than one emulator running: set ANDROID_SERIAL (e.g. emulator-5554)")
        running = f"{serial}\t" in devices if serial else "emulator-" in devices
        if not running:
            ensure_avd(avd)
            # A killed emulator leaves crash data; the next boot then waits on a consent dialog.
            for db in glob.glob("/tmp/android-*/emu-crash-*.db"):
                shutil.rmtree(db, ignore_errors=True)
            args = [EMU, "-avd", avd, "-no-audio", "-no-boot-anim", "-no-snapshot",
                    "-memory", "4096", "-gpu", "swangle_indirect"]
            if port:
                args += ["-port", port]
            log = open(os.path.expanduser(f"~/emulator-{avd}.log" if avd != "devin" else "~/emulator.log"), "a")
            subprocess.Popen(args, stdout=log, stderr=log, start_new_session=True)
        adb("wait-for-device", timeout=300)
        deadline = time.time() + 300
        while not booted():
            if time.time() > deadline:
                sys.exit("emulator did not boot in 300 s")
            time.sleep(2)
    for s in ("window_animation_scale", "transition_animation_scale", "animator_duration_scale"):
        adb("shell", "settings", "put", "global", s, "0")
    adb("shell", "settings", "put", "system", "screen_off_timeout", "1800000")
    adb("shell", "svc", "power", "stayon", "true")
    print(f"emulator ready ({serial or 'default'})")


def cmd_install(a):
    apk = a[0]
    pkg = a[a.index("--pkg") + 1] if "--pkg" in a else PKG
    adb("install", "-r", "-t", apk, timeout=600)
    adb("shell", "am", "force-stop", pkg)
    for perm in ("android.permission.POST_NOTIFICATIONS", "android.permission.RECORD_AUDIO"):
        adb("shell", "pm", "grant", pkg, perm, check=False)
    print(f"installed {apk}")


def bridge(cmd, kv):
    extras = " ".join(f"--es {k} '{v}'" for k, v in kv)
    out = adb("shell", f"am broadcast -n {PKG}/com.selabs.speak.devtools.bridge.DebugBridgeReceiver "
                       f"-a {PKG}.BRIDGE --es cmd {cmd} {extras}", timeout=120)
    m = re.search(r'result=(\d+), data="(.*)"', out, re.S)
    if not m:
        sys.exit(f"no bridge result (app not running or not a develop build?): {out.strip()}")
    return m.group(1) == "0", m.group(2)


def cmd_bridge(a):
    ok, data = bridge(a[0], [x.split("=", 1) for x in a[1:]])
    print(data)
    sys.exit(0 if ok else 1)


def launch():
    adb("shell", "am", "force-stop", PKG)
    adb("shell", "am", "start", "-W", "-n", f"{PKG}/{ACTIVITY}")


def cmd_launch(_):
    launch()
    print("launched")


def bq(sql, **params):
    args = ["bq", "--project_id=speak-v2-2a1f1", "query", "--quiet", "--nouse_legacy_sql", "--format=json",
            "--maximum_bytes_billed=1000000000"]
    args += [f"--parameter={k}:STRING:{v}" for k, v in params.items()]
    for attempt in range(6):
        r = subprocess.run(args + [sql], capture_output=True, text=True)
        if r.returncode == 0:
            try:
                return json.loads(r.stdout or "[]")
            except json.JSONDecodeError:
                return []  # DML prints a row count, not JSON
        # Concurrent DML on one table can fail to serialize; retry with backoff.
        if "concurrent" not in (r.stderr + r.stdout).lower():
            sys.exit(f"bq failed: {(r.stderr or r.stdout).strip()}")
        time.sleep(2 + attempt * 3)
    sys.exit("bq failed: concurrent update retries exhausted")


def cmd_lease(a):
    if os.path.exists(LEASE_FILE):
        print(open(LEASE_FILE).read().split()[0])
        return
    holder = a[a.index("--holder") + 1] if "--holder" in a else sys.exit("lease needs --holder <session URL>")
    env = a[a.index("--env") + 1] if "--env" in a else "dev"
    bq(f"""UPDATE {POOL} SET holder = @holder, holder_url = @holder, leased_at = CURRENT_TIMESTAMP(),
             released_at = NULL
           WHERE email = (SELECT email FROM {POOL}
                          WHERE env = @env
                            AND (holder IS NULL OR holder != 'broken' AND leased_at < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {LEASE_HOURS} HOUR))
                          ORDER BY RAND() LIMIT 1)
             AND (holder IS NULL OR holder != 'broken' AND leased_at < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {LEASE_HOURS} HOUR))""",
       holder=holder, env=env)
    rows = bq(f"SELECT email FROM {POOL} WHERE holder = @holder AND env = @env", holder=holder, env=env)
    if not rows:
        sys.exit("no free account in the pool; every account is leased")
    email = rows[0]["email"]
    open(LEASE_FILE, "w").write(f"{email} {holder}\n")
    print(email)


def cmd_release(a):
    if not os.path.exists(LEASE_FILE):
        print("no lease held")
        return
    email, holder = open(LEASE_FILE).read().split()
    bq(f"UPDATE {POOL} SET holder = NULL, holder_url = NULL, released_at = CURRENT_TIMESTAMP() "
       "WHERE email = @email AND holder = @holder", email=email, holder=holder)
    os.remove(LEASE_FILE)
    print(f"released {email}")


def cmd_login(a):
    if not os.path.exists(LEASE_FILE):
        sys.exit("no lease held; run `lease --holder <session URL>` first")
    email = open(LEASE_FILE).read().split()[0]
    pw = os.environ.get("QA_POOL_PASSWORD")
    if not pw:
        sys.exit("QA_POOL_PASSWORD not set")
    launch()
    time.sleep(3)
    ok, data = False, ""
    for _ in range(5):
        ok, data = bridge("login", [("email", email), ("password", pw)])
        if ok:
            break
        time.sleep(3)
    if not ok:
        sys.exit(f"login failed: {data}")
    launch()
    dismiss_until("id:home_root_ready", 90)
    print(f"logged in as {email}; Home ready")


DISMISS = r"^(Don.t allow|Not now|Set up later|Later|Maybe later|OK|Got it|Skip|Close|No thanks|Allow)$"


def dismiss_until(sel, timeout):
    deadline = time.time() + timeout
    while time.time() < deadline:
        root = dump()
        if root is not None and find(root, sel) is not None:
            return
        if root is not None:
            n = find(root, DISMISS)
            if n is None:
                n = find(root, "id:exit")
            if n is not None:
                tap_node(n)
        time.sleep(1.5)
    sys.exit(f"timed out waiting for {sel}")


def dump(path=None):
    adb("shell", "rm", "-f", "/sdcard/qa_dump.xml", check=False)
    out = adb("shell", "uiautomator", "dump", "/sdcard/qa_dump.xml", check=False, timeout=30)
    if "dumped" not in out:
        return None
    xml = adb("exec-out", "cat", "/sdcard/qa_dump.xml", check=False)
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return None
    if path:
        open(path, "w").write(xml)
    return root


def find(root, sel):
    if sel.startswith("id:"):
        want = sel[3:]
        pred = lambda n: n.get("resource-id", "").split("/")[-1] == want
    elif sel.startswith("text:"):
        rx = re.compile(sel[5:])
        pred = lambda n: rx.search(n.get("text", "") or "")
    elif sel.startswith("desc:"):
        rx = re.compile(sel[5:])
        pred = lambda n: rx.search(n.get("content-desc", "") or "")
    else:
        rx = re.compile(sel)
        pred = lambda n: rx.search(n.get("text", "") or "") or rx.search(n.get("content-desc", "") or "")
    for n in root.iter("node"):
        if pred(n) and n.get("bounds") != "[0,0][0,0]":
            return n
    return None


def wait(sel, timeout):
    deadline = time.time() + timeout
    while time.time() < deadline:
        root = dump()
        n = find(root, sel) if root is not None else None
        if n is not None:
            return n
        time.sleep(1)
    sys.exit(f"timed out after {timeout} s waiting for {sel}")


def tap_node(n):
    x1, y1, x2, y2 = map(int, re.findall(r"\d+", n.get("bounds")))
    adb("shell", "input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2))


def timeout_of(a, default=30):
    return float(a[a.index("--timeout") + 1]) if "--timeout" in a else default


def cmd_wait(a):
    print(wait(a[0], timeout_of(a)).get("bounds"))


def cmd_tap(a):
    n = wait(a[0], timeout_of(a))
    tap_node(n)
    print(f"tapped {a[0]} at {n.get('bounds')}")


def cmd_has(a):
    root = dump()
    sys.exit(0 if root is not None and find(root, a[0]) is not None else 1)


def cmd_type(a):
    text = " ".join(a)
    for i, word in enumerate(text.split(" ")):
        if i:
            adb("shell", "input", "keyevent", "62")
        if word:
            adb("shell", "input", "text", word.replace("'", "\\'"))
    print("typed")


def cmd_dump(a):
    root = dump(a[0] if a else None)
    if root is None:
        sys.exit("dump failed")
    if not a:
        for n in root.iter("node"):
            rid = n.get("resource-id", "").split("/")[-1]
            if rid or n.get("text") or n.get("content-desc"):
                print(rid, repr(n.get("text", "")), repr(n.get("content-desc", "")), n.get("bounds"))


def cmd_shot(a):
    with open(a[0], "wb") as f:
        subprocess.run([ADB, "exec-out", "screencap", "-p"], stdout=f, check=True)
    print(a[0])


def cmd_logcat(a):
    adb("logcat", "-c", check=False)
    out = open(a[0], "a")
    filt = [f"{t}:V" for t in TAGS] + ["*:S"]
    p = subprocess.Popen([ADB, "logcat", "-v", "time", *filt], stdout=out, stderr=out,
                         start_new_session=True)
    open(logcat_pid(), "w").write(str(p.pid))
    print(f"logcat pid {p.pid} -> {a[0]}")


def cmd_logstop(a):
    try:
        os.killpg(int(open(logcat_pid()).read()), signal.SIGTERM)
        os.remove(logcat_pid())
        print("logcat stopped")
    except (FileNotFoundError, ProcessLookupError):
        print("no logcat running")


def cmd_mark(a):
    adb("shell", "log", "-t", "QA_MARK", "'" + " ".join(a).replace("'", "") + "'")
    print("marked")


def cmd_rec(a):
    name = os.path.basename(a[0])
    subprocess.Popen([ADB, "shell", "screenrecord", "--bit-rate", "6000000", f"/sdcard/{name}"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    time.sleep(1)
    print(f"recording /sdcard/{name}")


def cmd_stop(a):
    name = os.path.basename(a[0])
    adb("shell", "pkill", "-INT", "screenrecord", check=False)
    for _ in range(30):
        if not adb("shell", "pidof", "screenrecord", check=False).strip():
            break
        time.sleep(0.5)
    time.sleep(1)
    adb("pull", f"/sdcard/{name}", a[0])
    adb("shell", "rm", "-f", f"/sdcard/{name}", check=False)
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a[0]],
                       capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        sys.exit(f"BROKEN recording {a[0]}: {r.stderr.strip()}")
    print(f"{a[0]} ok, {float(r.stdout):.1f} s")


def cmd_webp(a):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", a[0], "-vf", "setpts=PTS/4,fps=5,scale=360:-1",
                    "-loop", "0", "-c:v", "libwebp", "-q:v", "60", a[1]], check=True)
    print(a[1])


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    fn = globals().get("cmd_" + sys.argv[1])
    if not fn:
        sys.exit(f"unknown command {sys.argv[1]}\n{__doc__}")
    fn(sys.argv[2:])


if __name__ == "__main__":
    main()
