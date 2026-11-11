#!/usr/bin/env python3
"""Per-claim ladders at G = 75: every key whose LP feasibility can keep one of the 280 open claims alive.

For an open claim (state, ori, k, l) with state = (a, b, Y, V, he, ho, le, lo, Se, So, budget): the even phase's keys are
(he, Y, V, ori, q, z) with s = q + z, the odd phase's are (ho, V, Y, other, q, z).  The claim is open iff some LP-feasible
even key at level s_e <= Se and some LP-feasible odd key at level s_o <= So have s_e + s_o <= budget (the driver's first_s
returns the least feasible level on each side).  So the keys that matter are the LP-feasible even keys with
le <= s_e <= min(Se, budget - lo) and the odd keys with lo <= s_o <= min(So, budget - le).  For each such key we record
its open leaves (A, q_D) and the integer status of every open leaf (HiGHS MILP, status recorded), and then evaluate the
claim under hypotheses WITHOUT the driver (a key counts as feasible under hypothesis H iff it has an open leaf allowed by H):
  full         every open leaf
  A01          leaves with A <= 1                 (all A >= 2 leaves assumed excluded)
  A01_or_dark  A <= 1 or q_D >= 1                 (all A >= 2, q_D = 0 leaves assumed excluded)
  A0           A = 0
  INT          integer-feasible leaves            (all integer-infeasible leaves assumed certified)
  INT_A01      integer-feasible leaves with A <= 1
Writes ladders.json.  Everything here is LP / MILP status [measured]; nothing is a certificate.
"""
import sys, json, time
sys.dont_write_bytecode = True
from pathlib import Path
from collections import Counter
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hypo_scan as HS  # noqa: E402
import leaves_int as LI  # noqa: E402

FULL = json.load(open(HERE / "hypo_full.json"))
FEAS = {tuple(k) for k in FULL["lp_feasible_keys"]}
SURV = [(tuple(st), o, k, l) for st, o, k, l in FULL["survivor_list"]]
HYP = {"full": lambda a, d, c: True, "A01": lambda a, d, c: a <= 1, "A01_or_dark": lambda a, d, c: a <= 1 or d >= 1,
       "A0": lambda a, d, c: a == 0, "INT": lambda a, d, c: c == "feasible", "INT_A01": lambda a, d, c: c == "feasible" and a <= 1}
KEYINFO = {}


def key_info(key):
    if key in KEYINFO: return KEYINFO[key]
    h, y, F, ori, q, z = key
    feas = key in FEAS or (not HS.CC.direct_exclusion(key) and 2 * h + y + z + HS.comb(q, 2) >= 32 and bool(HS.CC.package_types(key))
                           and HS.feasible_cases(key, HS.ALLOW["full"]))
    info = {"feasible": feas, "leaves": []}
    if feas:
        for a, d in HS.open_leaves(key, HS.ALLOW["full"]):
            res, sols = LI.solve(key, a, d)
            statuses = [v["status"] for v in res.values()]
            cls = "infeasible" if 2 in statuses else ("feasible" if any(v.get("violations") == 0 for v in res.values()) else "unresolved")
            info["leaves"].append({"A": a, "qD": d, "int": cls, "int_statuses": statuses, "solutions": sols[:3]})
    KEYINFO[key] = info
    return info


def main():
    t0 = time.time(); out = []
    for n, (st, ori, k, l) in enumerate(SURV):
        a, b, Y, V, he, ho, le, lo, Se, So, budget = st
        other = "Mt" if ori == "M" else "M"
        even = {}; odd = {}
        for s in range(le, min(Se, budget - lo) + 1):
            for q in range(s + 1):
                key = (he, Y, V, ori, q, s - q)
                if key_info(key)["feasible"]: even.setdefault(s, []).append(key)
        for s in range(lo, min(So, budget - le) + 1):
            for q in range(s + 1):
                key = (ho, V, Y, other, q, s - q)
                if key_info(key)["feasible"]: odd.setdefault(s, []).append(key)
        assert min(even) == k and min(odd) == l, (st, ori, k, l, sorted(even), sorted(odd))
        status = {}
        for hname, allow in HYP.items():
            def ok(key): return any(allow(lf["A"], lf["qD"], lf["int"]) for lf in KEYINFO[key]["leaves"])
            ev = {s: [key for key in ks if ok(key)] for s, ks in even.items()}; od = {s: [key for key in ks if ok(key)] for s, ks in odd.items()}
            ev = {s: v for s, v in ev.items() if v}; od = {s: v for s, v in od.items() if v}
            alive = any(se + so <= budget for se in ev for so in od)
            status[hname] = {"open": alive, "k": min(ev) if ev else None, "l": min(od) if od else None}
        out.append({"state": list(st), "ori": ori, "k": k, "l": l, "Se": Se, "So": So, "budget": budget, "shortfall": budget - k - l,
                    "even_ladder": {str(s): [list(x) for x in ks] for s, ks in sorted(even.items())},
                    "odd_ladder": {str(s): [list(x) for x in ks] for s, ks in sorted(odd.items())},
                    "status": status})
        if n % 40 == 0: print(f"{n}/280 keys evaluated {len(KEYINFO)} {time.time()-t0:.0f}s", flush=True)
    keys = {str(k): v for k, v in KEYINFO.items() if v["feasible"]}
    summary = {h: sum(1 for c in out if c["status"][h]["open"]) for h in HYP}
    json.dump({"claims": out, "keys": keys, "summary_open_claims": summary, "ladder_keys_feasible": len(keys), "seconds": round(time.time() - t0)},
              open(HERE / "ladders.json", "w"))
    print("open claims by hypothesis", summary, "feasible ladder keys", len(keys), f"{time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
