#!/usr/bin/env python3
"""Walk a freshly signed-up dev account through Magic onboarding (Spanish) to Home.
Usage: qa_onboard.py [timeout_s]. Exit 0 at home_root_ready, 2 when stuck, 1 on timeout.
Used to refill the qa_account_pool; QA runs log in to a pool account instead."""
import os,subprocess,sys,time,re,importlib.util
spec=importlib.util.spec_from_file_location("q",os.path.join(os.path.dirname(os.path.abspath(__file__)),"qa_android.py"));q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
PRIO=[r"id:home_root_ready"]
TAPS=["id:onboarding_language_option_es_mx","id:onboarding_app_language_keep_button","id:onboarding_magic_action_switch_to_text","id:exit","id:onboarding_magic_action_generate_curriculum","id:onboarding_magic_action_continue","id:onboarding_magic_action_start",r"^(Continue|Next|Get started|Start|Skip|Maybe later|Not now|Later|No thanks|Set up later|OK|Got it|Close|Start learning|Let.s go|Retry)$"]
last=None;same=0;sent=0;t0=time.time()
ANSWERS=["Vacation in Mexico to talk with locals and order food","I am a beginner and know a few words","About 15 minutes every day","Ordering food, asking for directions and small talk","Yes that sounds great"]
while time.time()-t0<float(sys.argv[1] if len(sys.argv)>1 else 300):
    r=q.dump()
    if r is None: time.sleep(1);continue
    if q.find(r,"id:home_root_ready") is not None: print("HOME",round(time.time()-t0));sys.exit(0)
    ids=[n.get("resource-id").split("/")[-1] for n in r.iter("node") if n.get("resource-id") and ":id/" not in n.get("resource-id") and not n.get("resource-id").startswith("android:")]
    texts=[n.get("text") for n in r.iter("node") if n.get("text")]
    sig=tuple(ids)+tuple(texts)
    if sig==last: same+=1
    else: same=0; print("SCREEN",ids[:12],texts[:6],flush=True)
    last=sig
    if same>(12 if "onboarding_magic_freeform_text_input" in ids else 6): print("STUCK");sys.exit(2)
    if "onboarding_magic_action_open_reset" in ids and any("learn English" in t for t in texts):
        q.tap_node(q.find(r,"id:onboarding_magic_action_open_reset")); print(" reset (wrong course)"); time.sleep(2)
        r2=q.dump(); n=q.find(r2,"^Start over$") if r2 is not None else None
        if n is not None: q.tap_node(n); print(" start over")
        time.sleep(2); continue
    if any("Not learning Spanish" in t for t in texts) is False and "onboarding_magic_action_start" in ids:
        n=q.find(r,"text:^Not learning")
        if n is not None: q.tap_node(n); print(" switch language"); time.sleep(2); continue
    if "onboarding_magic_freeform_text_input" in ids and same % 3 == 0:
        q.tap_node(q.find(r,"id:onboarding_magic_freeform_text_input")); time.sleep(1)
        ans=ANSWERS[sent % len(ANSWERS)]; sent+=1
        subprocess.run([q.ADB,"shell","input","text",ans.replace(" ","%s")]); time.sleep(1)
        for _ in range(5):
            r2=q.dump(); n=q.find(r2,"id:onboarding_magic_action_send_text") if r2 is not None else None
            if n is not None: q.tap_node(n); print(" freeform reply sent"); break
            time.sleep(1)
        time.sleep(3); continue
    # options first
    opt=[n for n in r.iter("node") if re.search(r"_option|_choice|_answer",n.get("resource-id","")) and "onboarding_language_option" not in n.get("resource-id","") and n.get("clickable")=="true"]
    done=False
    if opt and same==0:
        q.tap_node(opt[0]);print(" tap option",opt[0].get("resource-id"));done=True; time.sleep(1.5); continue
    for s in TAPS:
        n=q.find(r,s)
        if n is not None and n.get("enabled")!="false":
            q.tap_node(n);print(" tap",s[:40]);done=True;break
    if not done and same>2:
        # try first clickable non-system node
        c=[n for n in r.iter("node") if n.get("clickable")=="true" and n.get("bounds")!="[0,0][0,0]" and "reset" not in n.get("resource-id","")]
        if c: q.tap_node(c[-1]);print(" tap last clickable",c[-1].get("resource-id"),c[-1].get("text"))
    time.sleep(2)
print("TIMEOUT");sys.exit(1)
