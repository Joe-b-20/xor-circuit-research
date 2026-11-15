import json, os, collections
B = os.path.expanduser("~/xs-campaigns/2026-11-13-aes/E/")
for arm in ("long1/splice", "long1/control", "low1/run"):
    L = [json.loads(l) for l in open(B + arm + "/log.jsonl")]
    t0 = L[0]["ts"]
    c = collections.Counter(); wall = collections.Counter()
    for e in L:
        if e["ev"] != "polished": continue
        kind = "pull" if (e.get("caps") or {}).get("tag") else "polish"
        A = e["m0"][0]
        grp = "A28" if A == 28 else ("A29-31" if A <= 31 else "A32+")
        imp = tuple(e["m"]) != tuple(e["m0"])
        c[(kind, grp, "jobs")] += 1; c[(kind, grp, "adm")] += bool(e["admitted"]); c[(kind, grp, "changed")] += imp
        feas = True
        cp = e.get("caps") or {}
        if cp.get("A") is not None and e["m"][0] > cp["A"]: feas = False
        if cp.get("GD") is not None and e["m"][3] > cp["GD"]: feas = False
        c[(kind, grp, "infeasible_out")] += (not feas)
        wall[(kind, grp)] += e["wall"]
    print("==", arm)
    for k in sorted(set((a, b) for a, b, _ in c)):
        print("   %-7s %-7s jobs %3d  admitted %2d  changed %3d  cap-not-met %3d  cpu_h %.2f" % (k[0], k[1], c[k + ("jobs",)], c[k + ("adm",)], c[k + ("changed",)], c[k + ("infeasible_out",)], wall[k] / 3600))
    sp = [e for e in L if e["ev"] == "spliced"]
    print("   splice steps %d, tried %d, admitted %d, secs %.0f" % (len(sp), sum(e["tried"] for e in sp), sum(e["admitted"] for e in sp), sum(e["secs"] for e in sp)))
    ad = [(round((e["ts"] - t0) / 60, 1), e["m"]) for e in L if e["ev"] == "admit"]
    print("   join admissions at min:", ad[:40])
    if arm == "low1/run":
        print("   A28 pull detail:")
        for e in L:
            if e["ev"] == "polished" and e["m0"][0] == 28:
                print("     ", round((e["ts"] - t0) / 60), "min", "pull" if (e.get("caps") or {}).get("tag") else "polish", e["m0"], "->", e["m"], "caps", {k: v for k, v in (e.get("caps") or {}).items() if k != "tag"}, "adm", e["admitted"], "t", e.get("t_last_imp"))
