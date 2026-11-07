"""s14_fix.py: slot roots (correctly: root = XOR of the three leaves = choice_i XOR its complementary leaf), and the
v9c shelf entry 08226d6b72c8 (mc-cap4.json) first layer vs the 89's L1."""
import json
import os

HOME = os.path.expanduser("~")
Q = os.path.join(HOME, "xs-campaigns/2026-11-07-sprint/q89")
N = 32
st = json.load(open(os.path.join(Q, "s7_structure.json")))
L1_main = set(st["L1_main"])
const = set(st["const"])
INPUTS = [1 << i for i in range(N)]
lines = [l.strip() for l in open(os.path.join(HOME, "xor-circuit-research/circuits/aes-mixcolumns/aes-mixcolumns.mat.txt")) if l.strip()]
T = []
for l in lines[2:34]:
    v = 0
    for j, ch in enumerate(l.replace(" ", "")):
        if ch == "1":
            v |= 1 << j
    T.append(v)
allv = const | set(INPUTS) | set(T)


def rot(v, s):
    return ((v << s) | (v >> (N - s))) & ((1 << N) - 1)


def name(v):
    return "x" + "+x".join(str(i) for i in range(N) if v >> i & 1)


print("slot roots:")
for slot in st["slots"]:
    a = slot[0]
    # leaves: a = L1 ^ L2 with L1, L2 in allv (weight-2 or input); third leaf = root ^ a where root in allv and weight 5
    roots = [a ^ x for x in allv if bin(a ^ x).count("1") == 5 and (a ^ x) in allv]
    roots = sorted(set(roots))
    for r in roots:
        kind = f"output y{T.index(r)}" if r in T else "constant helper"
        print(f"  slot {[name(c) for c in slot]} -> root {name(r)} ({kind}); third leaf {name(r ^ a)}")

d = json.load(open(os.path.join(HOME, "xs-campaigns/2026-11-04-12h/runs/v9c/shelf/mc-cap4.json")))
print("shelf json keys:", list(d.keys())[:10] if isinstance(d, dict) else type(d))
members = d.get("members") if isinstance(d, dict) else d
ent = None
if isinstance(members, dict):
    ent = members.get("08226d6b72c8")
elif isinstance(members, list):
    ent = next((m for m in members if "08226d6b72c8" in json.dumps(m)[:300]), None)
print("entry keys:", list(ent.keys()) if isinstance(ent, dict) else ent)
if isinstance(ent, dict):
    vals = ent.get("values") or ent.get("helpers") or (ent.get("state") or {}).get("values")
    if vals:
        L1 = {v for v in vals if bin(v).count("1") == 2}
        for s in (0, 8, 16, 24):
            R = {rot(v, s) for v in L1_main}
            print(f"  rot {s}: overlap {len(L1 & R)} of |L1|={len(L1)}; missing {[name(v) for v in R - L1]}; extra {[name(v) for v in L1 - R]}")
        hs = set(vals) - set(T) - set(INPUTS)
        print("  helpers", len(hs), "shared with L0 core(53)", len(hs & const), "layout", ent.get("layout"))
    else:
        print("  entry:", json.dumps(ent)[:800])
