#!/usr/bin/env python3
"""pass2c_q3.py -- round C of the second pass: ONE skeleton with a long CPU cap, the skeleton that alone blocks nine
UNRESOLVED leaves of ladder keys:  [(1,{0,1,2}), (2,{0}) x2, (2,{1}) x2, (2,{2}) x2], statuses BBB.
If the run completes, the affected leaf files of results_final/ are updated in place (their previous versions are kept in
results_final/before_roundC/); otherwise nothing changes.  A cap stays UNRESOLVED.
usage: python3 pass2c_q3.py [cap_seconds]
"""
import sys, json, glob, time, shutil
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import enum_q3 as E, verify_q3 as V, pass2_q3 as P2
RD = HERE / "results_final"
ROLES = [[1, [0, 1, 2]], [2, [0]], [2, [0]], [2, [1]], [2, [1]], [2, [2]], [2, [2]]]
STATUS = ["B", "B", "B"]

if __name__ == "__main__":
    cap = float(sys.argv[1]) if len(sys.argv) > 1 else 1700.0
    geo = E.build_geo()
    sg = P2.sig_of(ROLES, STATUS)
    res = P2.geom((sg, ROLES, STATUS, cap))
    print("round C:", {k: v for k, v in res.items() if k not in ("snaps", "deepest")}, flush=True)
    json.dump({k: v for k, v in res.items() if k != "snaps"}, open(RD / "roundC_outcome.json", "w"))
    if res["status"] != "done":
        print("not completed within the cap: nothing changed"); sys.exit(0)
    bak = RD / "before_roundC"; bak.mkdir(exist_ok=True); changed = []
    for fn in sorted(glob.glob(str(RD / "leaf_*.json"))):
        r = json.load(open(fn))
        hit = [sk for sk in r["skeleton_list"] if sk["roles"] == ROLES and E.slot_status(r["A"], r["qD"]) == STATUS and sk["status"] != "done"]
        if not hit: continue
        shutil.copy(fn, bak / Path(fn).name)
        key = tuple(r["key"]); a = r["A"]; d = r["qD"]; sk = hit[0]
        sk.update(source="pass2-roundC", status="done", survivors=res["survivors"], nodes=res["nodes"], mode=res["mode"], seg_counts=res["seg_counts"], geo_stats=res["stats"], cap=cap)
        if res["survivors"]:
            pl = E.plan(dict(roles=ROLES, status=STATUS, W=sk["W"]), sym_first_root=True); ok_w = 0
            for snap in res["snaps"][:5]:
                obj, rep = E.complete_witness(geo, pl, snap, key, a, d)
                w = dict(skeleton=ROLES, object=obj, verify={k: [v[0], v[1]] for k, v in rep.items() if isinstance(v, tuple)})
                if rep["all"][0]: w["milp"] = V.milp_status(key, a, d, dict(V.counts_of(obj))); ok_w += 1
                r["witnesses"].append(w)
            sk["witnesses_verified"] = ok_w
            if ok_w: r["survivors"] += res["survivors"]
        r["unresolved_skeletons"] = [u for u in r["unresolved_skeletons"] if u["roles"] != ROLES]
        if res["survivors"] and not sk.get("witnesses_verified"): r["unresolved_skeletons"].append(dict(roles=ROLES, status="witness completion failed"))
        r["nodes"] = sum(e["nodes"] for e in r["skeleton_list"])
        r["result"] = "SURVIVING" if r["survivors"] else ("UNRESOLVED" if r["unresolved_skeletons"] else "EXCLUDED")
        if r["result"] == "EXCLUDED": r["excluded_by"] = "step G (geometry)"
        r["witness_verify_all"] = all(w["verify"]["all"][0] for w in r["witnesses"]) if r["witnesses"] else None
        json.dump(r, open(fn, "w")); changed.append((key, a, d, r["result"]))
    print("updated leaves:", changed)
