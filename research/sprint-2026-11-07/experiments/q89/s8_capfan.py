"""s8_capfan.py: what the depth cap does to the neutral-move structure around the 89@4 plateau L0.
For members of L0 (main family from states_89.json), the exact remove1 fan (pes_lib.fan) at search cap 4, 5 and none:
number of neutral and down moves, and the depth of the outcomes. Then a bounded R1-neutral closure of member 0
at cap 5 and at no cap (limit --limit states, --time seconds) to compare with the 81-state closure at cap 4.
One process, nice 10. Output: q89/s8_capfan.json
"""
import argparse
import json
import os
import sys
import time
from collections import Counter, deque

sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-05-exit/pes")
from pes_lib import make_space, fan  # noqa: E402

HOME = os.path.expanduser("~")
Q = os.path.join(HOME, "xs-campaigns/2026-11-07-sprint/q89")


def closure(sp, S0, cap, limit, tlim):
    t0 = time.time()
    seen = {S0}
    q = deque([S0])
    expanded = 0
    downs_seen = 0
    depth_hist = Counter()
    edges = 0
    while q and expanded < limit and time.time() - t0 < tlim:
        S = q.popleft()
        g, d, neutral, downs, binds = fan(sp, S)
        expanded += 1
        depth_hist[d] += 1
        downs_seen += len(downs)
        for R, A, hk, dep in neutral:
            if cap is not None and dep > cap:
                continue
            K = frozenset(hk)
            edges += 1
            if K not in seen:
                seen.add(K)
                q.append(K)
    return {"cap": cap, "expanded": expanded, "reached": len(seen), "complete": not q and expanded < limit,
            "downs_seen_from_expanded": downs_seen, "depth_hist_of_expanded": dict(depth_hist), "neutral_edges": edges,
            "sec": round(time.time() - t0, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--members", type=int, default=5)
    ap.add_argument("--limit", type=int, default=1500)
    ap.add_argument("--time", type=float, default=420)
    a = ap.parse_args()
    try:
        os.nice(10)
    except OSError:
        pass
    st = json.load(open(os.path.join(Q, "s7_structure.json")))
    s89 = json.load(open(os.path.join(Q, "states_89.json")))["states"]
    fam = st["fam_idx"]
    out = {"fans": [], "closures": []}
    spaces = {}
    for cap in (4, 5, None):
        spaces[cap] = make_space("mc", cap)
        print("space cap", cap, "search_cap", spaces[cap].cap, flush=True)
    for i in fam[:a.members]:
        S = frozenset(s89[i]["helpers"])
        row = {"member": i}
        for cap, sp in spaces.items():
            t0 = time.time()
            g, d, neutral, downs, binds = fan(sp, S)
            dep_n = Counter(dep for _, _, _, dep in neutral)
            row[str(cap)] = {"gates": g, "depth": d, "neutral": len(neutral), "neutral_by_depth": dict(dep_n),
                             "downs": [(dg, dep) for _, dg, dep in downs], "binds": binds, "sec": round(time.time() - t0, 2)}
        out["fans"].append(row)
        print(json.dumps(row), flush=True)
    S0 = frozenset(s89[fam[0]]["helpers"])
    for cap in (4, 5, None):
        c = closure(spaces[cap], S0, cap, a.limit, a.time)
        out["closures"].append(c)
        print(json.dumps(c), flush=True)
    json.dump(out, open(os.path.join(Q, "s8_capfan.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
