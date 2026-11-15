import json, os, sys, hashlib, re
H = os.path.expanduser("~")
R = H + "/xcr-boolflux/"
m = json.load(open(R + "nonlinear/boolflux/results/MANIFEST.json"))
par = set(tuple(t) for t in m["aes_pareto"]["tuples_A_AD_G_GD"])
def ex(p):
    if not p: return "-"
    p = p.split(" (")[0].replace("~", H)
    if not p.startswith("/"): p = R + p
    return "Y" if os.path.exists(p) else "MISSING"
rows = []
for e in m["entries"]:
    if e.get("target") != "aes": continue
    mt = e["metrics"]; t = (mt["A"], mt["AD"], mt["G"], mt["GD"])
    rows.append((t, e))
rows.sort(key=lambda r: r[0])
amax = int(sys.argv[1]) if len(sys.argv) > 1 else 99
amin = int(sys.argv[2]) if len(sys.argv) > 2 else 0
for t, e in rows:
    if not (amin <= t[0] <= amax): continue
    st = e.get("start"); stp = st.get("path") if isinstance(st, dict) else st
    ps = e.get("pinned_set") or {}
    ttr = e.get("time_to_result_s")
    if isinstance(ttr, dict): ttr = {k: v for k, v in ttr.items() if k in ("within_job_s", "since_run_start_s", "iteration")}
    cv = e.get("code_version")
    print("%s %s trk=%s new=%s sup=%s | %s" % ("/".join(map(str, t)), "P" if t in par else "-", e.get("track"), ps.get("new_point"), len(ps.get("superseded_by_ours") or []), os.path.basename(e["file"])))
    print("   start=%s | seeds=%s kseed=%s iters=%s code12=%s ttr=%s" % (os.path.basename(str(stp)), e.get("seeds"), e.get("kernel_seed"), e.get("iters"), e.get("code_sha256_12"), ttr))
    print("   cmd=%s" % str(e.get("command"))[:230])
    print("   mech=%s" % str(e.get("mechanism"))[:260])
    print("   parents=%s" % ([ (os.path.basename(p.get("file", "?")) if isinstance(p, dict) else p) for p in (e.get("parents") or [])]))
    print("   rr=%s[%s] job[%s] repro=%s" % (str(e.get("run_record"))[:90], ex(e.get("run_record")), ex(e.get("job")), str(e.get("reproduction"))[:110]))
