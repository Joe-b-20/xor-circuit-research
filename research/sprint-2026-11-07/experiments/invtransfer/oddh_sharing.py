"""Step 3 (finding d): odd-weight non-output helpers and the sharing identity
G = 228 + delta - S (+ dead) on real inverse circuits: every distinct 118@5 record (own wiring from
the first record file; plus 20 random re-wirings of the value set for 10 states), the repo's
unrestricted-depth inverse circuits (88@17 ... 104@6), and the archive's two 88-gate inverse circuits
(depths 19 and 33).  Writes oddh118.json."""
import glob
import json
import os
import random
from collections import Counter
import common as C

INV = C.TSET
INPUTS = C.INPUTS
INSET = C.INSET


def check(order):
    avail = {v: 0 for v in INPUTS}
    for v, a, b in order:
        assert a in avail and b in avail and a ^ b == v, "bad gate"
        avail[v] = 1 + max(avail[a], avail[b])
    assert INV <= set(avail), "targets missing"
    return len(order), max(avail[t] for t in C.TARGETS), avail


def cones(order):
    par = {v: (a, b) for v, a, b in order}
    cone = []
    for g in range(8):
        seen = set()
        stack = [t for t in C.GROUP_TARGETS[g] if t in par]
        while stack:
            v = stack.pop()
            if v in seen:
                continue
            seen.add(v)
            for o in par[v]:
                if o in par and o not in seen:
                    stack.append(o)
        cone.append(seen)
    return par, cone


def sharing(order):
    par, cone = cones(order)
    G = len(order)
    gv = [v for v, _, _ in order]
    k = {v: sum(1 for g in range(8) if v in cone[g]) for v in gv}
    dead = sum(1 for v in gv if k[v] == 0)
    S_mult = sum(max(k[v] - 1, 0) for v in gv)
    S_cnt = sum(1 for v in gv if k[v] >= 2)
    sizes = [len(c) for c in cone]
    delta_g = [sizes[g] - C.M_GROUP_INV[g] for g in range(8)]
    delta = sum(delta_g)
    return {"G": G, "dead": dead, "S_mult": S_mult, "S_cnt": S_cnt, "sizes": sizes, "delta_g": delta_g,
            "delta": delta, "S_minus_delta": S_mult - delta,
            "identity_ok": G == sum(C.M_GROUP_INV) + delta - S_mult + dead,
            "kdist": dict(sorted(Counter(k.values()).items())),
            "min_cone_minus_claim": min(delta_g)}


def oddh(order):
    vals = [v for v, _, _ in order]
    helpers = [v for v in vals if v not in INV]
    odd = sum(1 for v in helpers if bin(v).count("1") % 2)
    even = len(helpers) - odd
    # the 75-proof coordinates: x = odd+odd gates, y = even+even gates, mixed = the rest
    x = y = m = 0
    for v, a, b in order:
        pa, pb = bin(a).count("1") % 2, bin(b).count("1") % 2
        if pa and pb:
            x += 1
        elif not pa and not pb:
            y += 1
        else:
            m += 1
    return {"helpers": len(helpers), "odd_helpers": odd, "even_helpers": even,
            "odd_values_all": sum(1 for v in vals if bin(v).count("1") % 2),
            "x_oddodd": x, "y_eveneven": y, "mixed": m}


def splits(v, avail):
    return [(a, a ^ v) for a in avail if (a ^ v) in avail and a < (a ^ v)]


def rewire(values, rng):
    avail = set(INPUTS)
    todo = set(values) - avail
    order = []
    while todo:
        cands = []
        for v in sorted(todo):
            sp = splits(v, avail)
            if sp:
                cands.append((v, rng.choice(sp)))
        if not cands:
            return None
        v, (a, b) = rng.choice(cands)
        order.append((v, a, b))
        avail.add(v)
        todo.discard(v)
    return order


res = {"records118": {}, "repo": {}, "archive": {}, "rewire": {}}
R = C.load("records118.json")["states"]
for key, e in R.items():
    d = json.load(open(e["wiring_file"]))
    order = C.wiring_of_record(d)
    G, dep, _ = check(order)
    res["records118"][key] = {"G": G, "depth": dep, "oddh": oddh(order), "sharing": sharing(order)}
# wiring dependence on 10 states
rng = random.Random(7)
for key in sorted(R)[:10]:
    vals = [v for v, _, _ in C.wiring_of_record(json.load(open(R[key]["wiring_file"])))]
    outs = []
    for _ in range(20):
        o2 = rewire(vals, rng)
        if o2 is None:
            continue
        s2 = sharing(o2)
        outs.append((s2["S_mult"], s2["delta"], s2["dead"]))
    res["rewire"][key] = {"S_range": [min(a for a, _, _ in outs), max(a for a, _, _ in outs)],
                          "delta_range": [min(b for _, b, _ in outs), max(b for _, b, _ in outs)],
                          "S_minus_delta_set": sorted(set(a - b for a, b, _ in outs)),
                          "dead_set": sorted(set(c for _, _, c in outs))}
for p in sorted(glob.glob(C.INVDIR + "/*.circ.txt")):
    order = C.wiring_of_ncff(p)
    G, dep, _ = check(order)
    res["repo"][os.path.basename(p)] = {"G": G, "depth": dep, "oddh": oddh(order), "sharing": sharing(order)}
for name, p in C.ARCHIVE88.items():
    try:
        d = json.load(open(p))
    except Exception as ex:
        res["archive"][name] = {"error": repr(ex)}
        continue
    order = C.wiring_of_archive(d)
    if order is None:
        res["archive"][name] = {"error": "unknown format", "keys": list(d)[:10]}
        continue
    try:
        G, dep, _ = check(order)
    except AssertionError as ex:
        res["archive"][name] = {"error": str(ex), "n_gates": len(order)}
        continue
    res["archive"][name] = {"G": G, "depth": dep, "oddh": oddh(order), "sharing": sharing(order)}
C.dump("oddh118.json", res)

# ---- print
oh = Counter(v["oddh"]["odd_helpers"] for v in res["records118"].values())
print("118@5 distinct states:", len(res["records118"]))
print("odd non-output helpers per 118@5:", dict(sorted(oh.items())))
print("helpers per 118@5:", dict(Counter(v["oddh"]["helpers"] for v in res["records118"].values())))
print("x/y/mixed (odd+odd, even+even, mixed gates):", Counter((v["oddh"]["x_oddodd"], v["oddh"]["y_eveneven"], v["oddh"]["mixed"]) for v in res["records118"].values()).most_common(6))
print("identity_ok all:", all(v["sharing"]["identity_ok"] for v in res["records118"].values()))
print("delta:", dict(sorted(Counter(v["sharing"]["delta"] for v in res["records118"].values()).items())))
print("S_mult:", dict(sorted(Counter(v["sharing"]["S_mult"] for v in res["records118"].values()).items())))
print("S-delta:", dict(sorted(Counter(v["sharing"]["S_minus_delta"] for v in res["records118"].values()).items())))
print("dead:", dict(Counter(v["sharing"]["dead"] for v in res["records118"].values())))
print("min(cone - claimed minimum) over groups:", dict(sorted(Counter(v["sharing"]["min_cone_minus_claim"] for v in res["records118"].values()).items())))
print("cone sizes (most common):", Counter(tuple(v["sharing"]["sizes"]) for v in res["records118"].values()).most_common(3))
print("rewire:", json.dumps(res["rewire"], indent=0)[:1500])
for sec in ("repo", "archive"):
    for name, v in res[sec].items():
        if "error" in v:
            print(sec, name, v)
        else:
            print(sec, name, "G", v["G"], "depth", v["depth"], "oddh", v["oddh"]["odd_helpers"], "of", v["oddh"]["helpers"],
                  "x/y/m", v["oddh"]["x_oddodd"], v["oddh"]["y_eveneven"], v["oddh"]["mixed"],
                  "| sizes", v["sharing"]["sizes"], "delta", v["sharing"]["delta"], "S", v["sharing"]["S_mult"],
                  "S-delta", v["sharing"]["S_minus_delta"], "dead", v["sharing"]["dead"], "id_ok", v["sharing"]["identity_ok"],
                  "min(cone-claim)", v["sharing"]["min_cone_minus_claim"])
