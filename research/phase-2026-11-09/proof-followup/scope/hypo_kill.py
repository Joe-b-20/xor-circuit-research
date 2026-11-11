#!/usr/bin/env python3
"""Block-closure hypotheticals at G = 75 (LP status; a MEASUREMENT, never a premise).

Oracle: the published combined feasibility (cached from hypo_full.json for every key it touched; recomputed with the
same matrices for any key first touched here), except that every key in a KILL set is declared infeasible.  This answers
"if exactly these keys were certified dead, which claims would close and which keys would become load-bearing".
usage: python3 hypo_kill.py NAME 'python-expression over key=(h,y,F,ori,q,z) and LEAVES (open leaves of the 229)' ...
Writes hypo_kill_<NAME>.json.
"""
import sys, json, time
sys.dont_write_bytecode = True
from pathlib import Path
from collections import Counter
from functools import lru_cache
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hypo_scan as HS  # noqa: E402

FULL = json.load(open(HERE / "hypo_full.json"))
FEAS = {tuple(k) for k in FULL["lp_feasible_keys"]}
TOUCHED = None  # keys touched by the full scan are exactly those whose feasibility the driver asked; we cache feasible ones
LEAVES = {tuple(eval(k)): v for k, v in json.load(open(Path.home() / "xor-circuit-research/lower-bound-proofs/mixcolumns-lb75-open-cases/combined/measurement/scan_leaves.json"))["leaves"].items()}
INT = {}
for e in json.load(open(HERE / "leaves_int.json"))["leaves"]:
    INT.setdefault(tuple(e["key"]), {})[(e["A"], e["qD"])] = e["class"]
KILL = [set()]
RECORD = {}


@lru_cache(None)
def feasible(h, y, F, q, z, ori):
    key = (h, y, F, ori, q, z)
    if key in KILL[0]: r = False
    elif key in FEAS: r = True
    else:
        # not feasible in the full scan if it was touched there; keys never touched are evaluated now
        r = HS.feasible(h, y, F, q, z, ori) if key not in FULLTOUCH else False
    RECORD[key] = r
    return r


def run(name, expr):
    t0 = time.time(); RECORD.clear(); feasible.cache_clear(); HS.VARIANT[0] = "full"
    kill = {k for k in FEAS if eval(expr, {"key": k, "LEAVES": LEAVES, "INT": INT, "h": k[0], "y": k[1], "F": k[2], "ori": k[3], "q": k[4], "z": k[5]})}
    KILL[0] = kill
    HS.LR.feasible = feasible
    states, claims, surv = HS.LR.run(HS.G)
    feas = {k for k, v in RECORD.items() if v}
    lb = HS.load_bearing(surv, feas)
    out = {"name": name, "kill_expr": expr, "killed_keys": len(kill), "killed_keys_list": sorted(list(k) for k in kill),
           "survivors": len(surv), "survivors_M": sum(1 for st, o, k, l in surv if o == "M"), "survivors_Mt": sum(1 for st, o, k, l in surv if o == "Mt"),
           "shortfall": sorted(Counter(st[10] - k - l for st, o, k, l in surv).items()),
           "survivor_list": [[list(st), o, k, l] for st, o, k, l in sorted(surv)],
           "keys_load_bearing": len(lb), "load_bearing_keys": sorted(list(k) for k in lb),
           "new_load_bearing_keys": sorted(list(k) for k in lb if list(k) not in FULL["load_bearing_keys"]),
           "lb_by_q": sorted(Counter(k[4] for k in lb).items()), "seconds": round(time.time() - t0)}
    json.dump(out, open(HERE / f"hypo_kill_{name}.json", "w"))
    print(f"[{name}] killed {len(kill)} keys -> survivors {len(surv)} (M {out['survivors_M']}, Mt {out['survivors_Mt']}), shortfall {out['shortfall']}, "
          f"load-bearing {len(lb)} (new {len(out['new_load_bearing_keys'])}), {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    FULLTOUCH = set()
    # reconstruct the touched set: rerun is expensive, so approximate "touched" by the driver's own walk below (keys asked here
    # and absent from FEAS are treated as infeasible unless unknown).  To be safe we recompute feasibility for every key not in
    # FEAS that the driver asks (HS.feasible is cached per process).
    args = sys.argv[1:]
    for i in range(0, len(args), 2):
        run(args[i], args[i + 1])
