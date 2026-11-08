#!/usr/bin/env python3
"""Why did every exit-89 state yield 0 valid 88-subset candidates?  Take one logged expand exit
and enumerate its 88-subsets with pes_lib's state builder."""
import json, os, sys
sys.path.insert(0, os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/translog"))
import plateau_sig as ps  # noqa: E402
sp = ps.sp
E = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/translog/exp1")
rows = [json.loads(l) for l in open(f"{E}/runs/E1/workers/p1-00/translog.jsonl")]
body = [r for r in rows if r["k"] in ("step", "chain")]
for i, r in enumerate(body[:400]):
    if r["g"] == 89 and r.get("p") == 88 and r.get("v") and r["m"] == "walk.expand":
        X = r["v"]
        prev = body[i - 1]
        nxt = body[i + 1]
        print("exit row it", r["it"], "len v", len(X), "prev entry len", len(prev.get("v") or []), "next", nxt["g"], nxt["m"])
        helpers = [v for v in X if v not in sp.tset]
        print("helpers in X:", len(helpers), "targets in X:", len(X) - len(helpers), "tset size", len(sp.tset))
        st = sp.state(helpers)
        print("89 state: count", st.count(), "depth", st.depth(), "ok", getattr(st, "ok", lambda: None)())
        ok88 = 0
        for u in helpers:
            s2 = sp.state([v for v in helpers if v != u])
            c, d = s2.count(), s2.depth()
            if c == 88 and d is not None:
                ok88 += 1
        print("88-subsets realizable:", ok88, "of", len(helpers))
        # is the previous entry state a subset of X?
        if prev.get("v"):
            print("prev entry subset of X:", set(prev["v"]) <= set(X), "diff", len(set(X) - set(prev["v"])), len(set(prev["v"]) - set(X)))
        break
