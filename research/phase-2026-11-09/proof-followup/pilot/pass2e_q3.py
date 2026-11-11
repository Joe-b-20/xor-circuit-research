#!/usr/bin/env python3
"""pass2e_q3.py -- round E: the single skeleton that keeps the last three leaves UNRESOLVED ((16,0,1..3), A = 0, q_D = 0):
[(0,{0,1,2}), (2,{0}) x3, (2,{1}) x2, (2,{2}) x2], statuses BBB, with the validated join of pass2d_q3.run_join, the
combination cap lifted and a long CPU cap.  Leaf files are updated only if the run completes (previous versions kept in
results_final/before_roundE/).
usage: python3 pass2e_q3.py [cap_seconds]
"""
import sys, json, glob, time, shutil
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import enum_q3 as E, verify_q3 as V, pass2_q3 as P2, pass2d_q3 as D
RD = HERE / "results_final"
ROLES = [[0, [0, 1, 2]], [2, [0]], [2, [0]], [2, [0]], [2, [1]], [2, [1]], [2, [2]], [2, [2]]]
STATUS = ["B", "B", "B"]

if __name__ == "__main__":
    cap = float(sys.argv[1]) if len(sys.argv) > 1 else 1500.0
    geo = E.build_geo(); c0 = time.process_time()
    skel = dict(roles=ROLES, status=STATUS, W=[sum(r for r, L in ROLES if s in L) for s in range(3)])
    pl = E.plan(skel, sym_first_root=True)
    res = D.run_join(geo, pl, time.process_time() + cap, max_combos=10 ** 12)
    res.update(cap=cap, cpu=round(time.process_time() - c0, 1), nodes=res["stats"].get("seg_nodes", 0) + res["stats"].get("prod_nodes", 0))
    print("round E:", {k: v for k, v in res.items() if k != "snaps"}, flush=True)
    json.dump({k: v for k, v in res.items() if k != "snaps"}, open(RD / "roundE_outcome.json", "w"))
    if res["status"] != "done":
        print("not completed within the cap: nothing changed"); sys.exit(0)
    bak = RD / "before_roundE"; bak.mkdir(exist_ok=True); changed = []
    for fn in sorted(glob.glob(str(RD / "leaf_*.json"))):
        r = json.load(open(fn))
        hit = [sk for sk in r["skeleton_list"] if sk["roles"] == ROLES and E.slot_status(r["A"], r["qD"]) == STATUS and sk["status"] != "done"]
        if not hit: continue
        shutil.copy(fn, bak / Path(fn).name)
        key = tuple(r["key"]); a = r["A"]; d = r["qD"]; sk = hit[0]
        sk.update(source="pass2-roundE(join)", status="done", survivors=res["survivors"], nodes=res["nodes"], mode="join", seg_counts=res["seg_counts"], geo_stats=res["stats"], cap=cap)
        if res["survivors"]:
            ok_w = 0
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
