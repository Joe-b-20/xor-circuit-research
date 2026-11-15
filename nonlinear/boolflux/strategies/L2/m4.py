import json, os, collections, glob
H = os.path.expanduser("~")
R = H + "/xcr-boolflux/"
m = json.load(open(R + "nonlinear/boolflux/results/MANIFEST.json"))
par = set(tuple(t) for t in m["aes_pareto"]["tuples_A_AD_G_GD"])
aes = [e for e in m["entries"] if e.get("target") == "aes"]
print("AES entries", len(aes), "with track", sum(1 for e in aes if e.get("track")), collections.Counter(e.get("track") for e in aes))
print("\n-- caps not met by the stored circuit")
for e in aes:
    mt = e["metrics"]; c = e.get("caps") or {}
    bad = [(k, c[k], mt[k]) for k in ("A", "AD", "GD") if c.get(k) is not None and mt[k] > c[k]]
    jc = e.get("job_caps")
    if bad or (jc and any(jc.get(k) is not None and mt[k] > jc[k] for k in ("A", "AD", "GD"))):
        print("  ", (mt["A"], mt["AD"], mt["G"], mt["GD"]), os.path.basename(e["file"]), "caps", c, "job_caps", jc)
print("\n-- mechanism classes among Pareto entries")
cl = collections.Counter(); rows = []
for e in aes:
    mt = e["metrics"]; t = (mt["A"], mt["AD"], mt["G"], mt["GD"])
    if t not in par: continue
    mech = str(e.get("mechanism"))
    k = mech.split(":")[0].split("(")[0].strip()[:40]
    cl[(e.get("track"), k)] += 1
for k, v in sorted(cl.items(), key=str): print("  ", k, v)
print("pareto circuits", sum(cl.values()), "tuples", len(par))
print("\n-- reproduction classes (all AES)")
rc = collections.Counter(str(e.get("reproduction")).split(":")[0][:60] for e in aes)
for k, v in rc.items(): print("  ", v, k)
print("\n-- provenance gaps among Pareto entries")
for e in aes:
    mt = e["metrics"]; t = (mt["A"], mt["AD"], mt["G"], mt["GD"])
    if t not in par: continue
    gaps = []
    if not e.get("seeds") and "join" not in str(e.get("mechanism")): gaps.append("no seed")
    if e.get("seeds") and any(isinstance(s, str) and not s.isdigit() for s in e["seeds"]): gaps.append("seed=" + str(e["seeds"]))
    if not e.get("code_sha256_12"):
        cv = json.dumps(e.get("code_version"))
        if "uncommitted" in cv: gaps.append("code: uncommitted scripts, sha256 'now'")
        elif cv in ("null", "{}"): gaps.append("no code version")
    ttr = e.get("time_to_result_s")
    if ttr is None or (isinstance(ttr, dict) and ttr.get("within_job_s") is None and "since_run_start_s" in ttr and "polish" in str(e.get("mechanism"))): gaps.append("no within-job time")
    ps = [p.get("file") if isinstance(p, dict) else p for p in (e.get("parents") or [])]
    if not ps or any((p is None) for p in ps): gaps.append("parents=%s" % (e.get("parents"),))
    st = e.get("start"); sp = st.get("path") if isinstance(st, dict) else st
    if sp and "pool hash" in str(sp): gaps.append("start only as pool hash")
    print("  ", t, e.get("track"), "|", "; ".join(gaps) if gaps else "ok")
print("\n-- parents field sample")
for e in aes[:400]:
    if e.get("track") == "E":
        print(json.dumps(e.get("parents"))[:600]); print(json.dumps(e.get("start"))[:300]); break
print("\n-- code_version distinct kernels")
kc = collections.Counter()
for e in aes:
    cv = e.get("code_version") or {}
    kc[str(cv.get("kernel") if isinstance(cv, dict) else cv)[:110]] += 1
for k, v in kc.items(): print("  ", v, k)
print("code_sha256_12:", collections.Counter(e.get("code_sha256_12") for e in aes))
print("curated_utc:", collections.Counter(str(e.get("curated_utc"))[:16] for e in aes))
