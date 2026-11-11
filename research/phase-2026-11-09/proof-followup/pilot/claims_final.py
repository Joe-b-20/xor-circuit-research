#!/usr/bin/env python3
"""claims_final.py -- the claims analysis on the FINAL results (results_final/, farkas_final.json) with ../scope/ladders.json.

Grade of an EXCLUDED leaf (PILOT_SPEC.md section 6 and the report):
  certified        step S (LP) alone, and every LP prune of the leaf has an exact integer Farkas certificate;
  finite-checked   step G (geometry) emptied every skeleton, no skeleton was removed by R8-int (MILP), and every LP prune of
                   the leaf has an exact certificate (the exclusion rests on enum_q3's exhaustive search + exact certificates);
  measured         the exclusion uses at least one solver status without certificate: an LP prune without certificate, or
                   an R8-int (MILP) prune.
A key is fully excluded iff every open leaf (ladders.json) is EXCLUDED; its grade is the weakest of its leaves.  (The leaves
that are not open are LP-infeasible in the scans of the scope folder [measured]; that is outside this pilot.)
Claims: a claim is open iff some alive even level and alive odd level fit the budget (ladder.py's rule).  Evaluated under
  ALL    every EXCLUDED leaf accepted;      STRICT  only the certified and finite-checked ones.
For the 8 claims that close when the whole block dies: the block keys at their live levels and, per key, the leaves that are
not EXCLUDED (what still stands in the way).  Everything here is bookkeeping on LP status [measured]; no bound is implied.
"""
import sys, json, glob
from pathlib import Path
from collections import Counter
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import claims_q3 as CQ

RD = HERE / "results_final"


def main():
    fark = {(tuple(r["key"]), r["A"], r["qD"]): r for r in json.load(open(HERE / "farkas_final.json"))["rows"]}
    leaves = {}
    for fn in glob.glob(str(RD / "leaf_*.json")):
        r = json.load(open(fn)); k = (tuple(r["key"]), r["A"], r["qD"])
        f = fark[k]; lp_cert = f["vectors"] == f["certified"]
        grade = None
        if r["result"] == "EXCLUDED":
            if r["excluded_by"] == "step S (LP)": grade = "certified" if lp_cert else "measured"
            elif r["excluded_by"] == "step S (LP + MILP)": grade = "measured"
            else: grade = "finite-checked" if (lp_cert and r["skeletons_milp_infeasible"] == 0) else "measured"
        leaves[k] = dict(result=r["result"], excluded_by=r.get("excluded_by"), grade=grade, lp_vectors=f["vectors"], lp_certified=f["certified"],
                         milp_killed=r["skeletons_milp_infeasible"], skeletons=r["skeletons"], unresolved=len(r["unresolved_skeletons"]))
    keys3 = CQ.mt3_keys()
    def key_status(key):
        info = CQ.KEYS[key]
        ls = [leaves[(key, lf["A"], lf["qD"])] for lf in info["leaves"]]
        if all(l["result"] == "EXCLUDED" for l in ls):
            g = "measured" if any(l["grade"] == "measured" for l in ls) else ("finite-checked" if any(l["grade"] == "finite-checked" for l in ls) else "certified")
            return "EXCLUDED", g
        return ("SURVIVING" if any(l["result"] == "SURVIVING" for l in ls) else "UNRESOLVED"), None
    kst = {k: key_status(k) for k in keys3 if k in CQ.KEYS}
    dead_all = {}; dead_strict = {}
    for (key, a, d), l in leaves.items():
        if l["result"] == "EXCLUDED":
            dead_all.setdefault(key, set()).add((a, d))
            if l["grade"] in ("certified", "finite-checked"): dead_strict.setdefault(key, set()).add((a, d))
    n0, st0 = CQ.evaluate({}); nA, stA = CQ.evaluate(dead_all); nS, stS = CQ.evaluate(dead_strict)
    all_block = {k: {(lf["A"], lf["qD"]) for lf in CQ.KEYS[k]["leaves"]} for k in keys3 if k in CQ.KEYS}
    nB, stB = CQ.evaluate(all_block)
    set3 = set(keys3)
    out = dict(leaf_results=dict(Counter(l["result"] for l in leaves.values())), leaf_grades=dict(Counter(l["grade"] for l in leaves.values() if l["grade"])),
               keys_total=len(kst), key_status=dict(Counter(s for s, g in kst.values())), key_grades=dict(Counter(g for s, g in kst.values() if g)),
               keys_fully_excluded=[[list(k), g] for k, (s, g) in sorted(kst.items()) if s == "EXCLUDED"],
               open_claims=dict(baseline=n0, whole_block_dead=nB, pilot_ALL=nA, pilot_STRICT=nS))
    closed_all = []; blockdep = []; changed = []
    for c0, cA, cS, cB in zip(st0, stA, stS, stB):
        name = dict(state=c0["state"], ori=c0["ori"], k=c0["k0"], l=c0["l0"], budget=c0["budget"])
        if not cA["open"]: closed_all.append(name | dict(closed_STRICT=not cS["open"]))
        elif (cA["k"], cA["l"]) != (c0["k"], c0["l"]): changed.append(name | dict(k_l_ALL=[cA["k"], cA["l"]]))
        if not cB["open"]:
            side = "odd" if any(k in set3 for ks in c0["od"].values() for k in ks) and not any(k in set3 for ks in c0["ev"].values() for k in ks) else "even"
            lad = c0["od"] if side == "odd" else c0["ev"]; other = c0["ev"] if side == "odd" else c0["od"]
            live = {s: ks for s, ks in lad.items() if s + min(other) <= c0["budget"]}
            keys_live = [k for ks in live.values() for k in ks]
            rows = []
            for k in keys_live:
                info = CQ.KEYS[k]
                rows.append(dict(key=list(k), in_block=k in set3, key_status=kst.get(k, ("not in block", None))[0], key_grade=kst.get(k, (None, None))[1],
                                 leaves=[dict(A=lf["A"], qD=lf["qD"], int=lf["int"], **({kk: leaves[(k, lf["A"], lf["qD"])][kk] for kk in ("result", "excluded_by", "grade", "skeletons", "unresolved")} if k in set3 else {})) for lf in info["leaves"]]))
            blockdep.append(name | dict(side=side, live_levels={str(s): [list(k) for k in ks] for s, ks in live.items()}, keys=rows,
                                        status_ALL="closed" if not cA["open"] else "open", status_STRICT="closed" if not cS["open"] else "open",
                                        in_the_way=[[r["key"], lf["A"], lf["qD"], lf.get("result", "outside the block")] for r in rows for lf in r["leaves"] if lf.get("result") != "EXCLUDED"]))
    out.update(claims_closed_if_ALL_accepted=closed_all, claims_with_raised_levels_ALL=changed, block_dependent_claims=blockdep)
    json.dump(out, open(HERE / "claims_final.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ("block_dependent_claims",)}, indent=1))
    for b in blockdep:
        print("CLAIM", b["state"], b["ori"], "k,l", b["k"], b["l"], "budget", b["budget"], "| ALL:", b["status_ALL"], "STRICT:", b["status_STRICT"])
        for r in b["keys"]:
            print("    key", r["key"], r["key_status"], r["key_grade"], [(lf["A"], lf["qD"], lf.get("result"), lf.get("grade"), lf["int"]) for lf in r["leaves"]])
        print("    in the way:", b["in_the_way"])


if __name__ == "__main__":
    main()
