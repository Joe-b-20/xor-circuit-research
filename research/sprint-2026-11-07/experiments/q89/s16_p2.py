"""s16_p2.py: prediction P2. Every 90-gate depth-4 state whose first layer is exactly the 89's 26-pair set (any byte
rotation, rotated back to L0's frame) is in L0's +1 band: (a) in B1 (one expand-envelope step from an L0 member),
(b) in D1 (the full remove1 closure of B1 at 90, barrier band_mc89d4full_w0.json, matched by Python's tuple hash as
bt_band.py did), (c) has a direct remove1 step into L0, (d) descends to L0 by a bounded BFS over non-increasing
exact remove1 moves at cap 4 (bound 5,000, stop at the first state <= 89).
Test objects: 90-gate 'best' states of the 2026-11-02-why pinned completions (out/*.jsonl), and 90-gate results of
the foundation / foundation2 / repair validation runs (runs/*-r*.json) whose first layer is a rotation of the 89's.
Also the recorded 90@4 states (states_90.json) are re-checked (none has the set). One process, nice 10.
"""
import glob
import json
import os
import sys
import time
from collections import Counter, deque

sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-05-exit/pes")
from pes_lib import make_space, fan, env_outcomes  # noqa: E402

HOME = os.path.expanduser("~")
Q = os.path.join(HOME, "xs-campaigns/2026-11-07-sprint/q89")
N = 32
INPUTS = [1 << i for i in range(N)]
lines = [l.strip() for l in open(os.path.join(HOME, "xor-circuit-research/circuits/aes-mixcolumns/aes-mixcolumns.mat.txt")) if l.strip()]
T = []
for l in lines[2:34]:
    v = 0
    for j, ch in enumerate(l.replace(" ", "")):
        if ch == "1":
            v |= 1 << j
    T.append(v)
TSET = set(T)
st7 = json.load(open(os.path.join(Q, "s7_structure.json")))
L1_main = frozenset(st7["L1_main"])
CORE = set(st7["const"])
s89 = json.load(open(os.path.join(Q, "states_89.json")))["states"]
L0 = [frozenset(s89[i]["helpers"]) for i in st7["fam_idx"]]
L0set = set(L0)


def rot(v, s):
    return ((v << s) | (v >> (N - s))) & ((1 << N) - 1)


def name(v):
    return "x" + "+x".join(str(i) for i in range(N) if v >> i & 1)


def helpers_from_values(vals):
    return frozenset(v for v in vals if v not in TSET and v not in INPUTS)


def align(H):
    """rotate helper set H so that its first layer equals L1_main; return (rotated set, shift) or None"""
    L1 = frozenset(v for v in H if bin(v).count("1") == 2)
    for s in (0, 8, 16, 24):
        if frozenset(rot(v, s) for v in L1) == L1_main:
            return frozenset(rot(v, s) for v in H), s
    return None


cands = []  # (label, helpers aligned, shift, gates)
# 1. pinned completions 2026-11-02-why
for f in sorted(glob.glob(os.path.join(HOME, "xs-campaigns/2026-11-02-why/foundations/out/*.jsonl"))):
    best = None
    for line in open(f):
        if not line.strip():
            continue
        d = json.loads(line)
        if d.get("ev") == "best" and d.get("d") == 4 and d.get("values"):
            best = d
    if best and best.get("g") == 90:
        H = helpers_from_values(best["values"])
        a = align(H)
        if a:
            cands.append((os.path.basename(f).replace(".jsonl", ""), a[0], a[1], 32 + len(a[0])))
# 2. validation runs of the foundation searches and the repair experiment
for base in ["2026-11-03-12h/foundation/run", "2026-11-03-12h/foundation-smoke", "2026-11-04-12h/foundation2/run",
             "2026-11-04-12h/foundation2/smoke/run", "2026-11-03-waits/repair/run"]:
    for f in sorted(glob.glob(os.path.join(HOME, "xs-campaigns", base, "runs", "*-r*.json"))):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        if d.get("gates") == 90 and d.get("depth") == 4 and d.get("values"):
            H = helpers_from_values(d["values"])
            a = align(H)
            if a:
                cands.append((base.split("/")[0] + ":" + os.path.basename(f).replace(".json", ""), a[0], a[1], 32 + len(a[0])))
# 3. recorded 90@4 states
s90 = json.load(open(os.path.join(Q, "states_90.json")))["states"]
nrec = 0
for s in s90:
    a = align(frozenset(s["helpers"]))
    if a:
        nrec += 1
        cands.append(("record:" + s["files"][0], a[0], a[1], 32 + len(a[0])))
print("recorded 90@4 states with the 89's first layer (any rotation):", nrec)
# dedupe
seen = {}
for lab, H, s, g in cands:
    seen.setdefault(H, []).append((lab, s))
print("candidate 90-gate states with the 89's exact first layer:", len(cands), "distinct:", len(seen))
for H, labs in seen.items():
    print("  ", len(H) + 32, "gates;", labs)

os.nice(10)
sp = make_space("mc", 4)
# B1
t0 = time.time()
B1 = set()
for S in L0:
    for hk, dg, dep, ed in env_outcomes(sp, S):
        if dg == 1 and dep <= 4:
            B1.add(frozenset(hk))
print("B1 regenerated:", len(B1), "states in", round(time.time() - t0, 1), "s (barrier: 16,173)")
# D1 hashes
band = json.load(open(os.path.join(HOME, "xs-campaigns/2026-11-05-views/barrier/band_mc89d4full_w0.json")))
D1h = {n["b"] for n in band["nodes"] if n.get("b") is not None}
print("D1 hashes loaded:", len(D1h), "of", len(band["nodes"]), "nodes")


def descend(S, bound=5000):
    parent = {S: 0}
    q = deque([S])
    visited = 0
    while q:
        Y = q.popleft()
        if visited >= bound:
            return {"result": "cut", "visited": visited}
        visited += 1
        g, d, neutral, downs, _ = fan(sp, Y)
        nxt = [(frozenset(k), dep, g) for R, A, k, dep in neutral] + [(frozenset(k), dep, g + dg) for k, dg, dep in downs]
        for K, dep, g1 in nxt:
            if dep > 4 or K in parent:
                continue
            parent[K] = parent[Y] + 1
            if g1 <= 89:
                return {"result": "home" if K in L0set else ("lower" if g1 < 89 else "other89"), "gates": g1,
                        "steps": parent[K], "visited": visited, "landing": sorted(K)}
            q.append(K)
    return {"result": "stuck", "visited": visited}


results = []
for H, labs in seen.items():
    st = sp.state(sorted(H))
    hk = sp.hkey(st)
    K = frozenset(hk)
    g = st.count()
    row = {"labels": labs, "gates": g, "depth": st.depth(), "trimmed_changed": K != H,
           "in_B1": K in B1, "in_D1": hash(tuple(hk)) in D1h}
    gg, d, neutral, downs, binds = fan(sp, K)
    row["r1_neutral"] = len(neutral)
    row["r1_down_total"] = len(downs)
    row["r1_down_into_L0"] = sum(1 for k, dg, dep in downs if frozenset(k) in L0set and dep <= 4)
    row["descent"] = descend(K)
    # what distinguishes it: helpers vs the 53-core and the union of L0
    U = set().union(*L0)
    row["helpers"] = len(K)
    row["core_shared"] = len(K & CORE)
    row["not_in_L0_union"] = [name(v) for v in sorted(K - U)]
    row["core_missing"] = [name(v) for v in sorted(CORE - K)]
    lev = Counter()
    results.append(row)
    print(json.dumps(row)[:1200], flush=True)

summary = {"n_candidates": len(cands), "n_distinct": len(seen), "n_recorded_90_with_set": nrec,
           "in_B1": sum(r["in_B1"] for r in results), "in_D1": sum(r["in_D1"] for r in results),
           "direct_r1_into_L0": sum(1 for r in results if r["r1_down_into_L0"] > 0),
           "descent": Counter(r["descent"]["result"] for r in results)}
print("SUMMARY", json.dumps(summary))
json.dump({"summary": summary, "results": results}, open(os.path.join(Q, "s16_p2.json"), "w"), indent=1)
