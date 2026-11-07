"""s13_shelf_slots.py: (1) find and read the v9c shelf member 08226d6b72c8; (2) are the 4 slot roots outputs?"""
import glob
import json
import os

HOME = os.path.expanduser("~")
Q = os.path.join(HOME, "xs-campaigns/2026-11-07-sprint/q89")
N = 32
st = json.load(open(os.path.join(Q, "s7_structure.json")))
L1_main = set(st["L1_main"])
INPUTS = [1 << i for i in range(N)]
lines = [l.strip() for l in open(os.path.join(HOME, "xor-circuit-research/circuits/aes-mixcolumns/aes-mixcolumns.mat.txt")) if l.strip()]
T = []
for l in lines[2:34]:
    v = 0
    for j, ch in enumerate(l.replace(" ", "")):
        if ch == "1":
            v |= 1 << j
    T.append(v)


def rot(v, s):
    return ((v << s) | (v >> (N - s))) & ((1 << N) - 1)


def name(v):
    return "x" + "+x".join(str(i) for i in range(N) if v >> i & 1)


shelf = os.path.join(HOME, "xs-campaigns/2026-11-04-12h/runs/v9c/shelf")
print("shelf tree:", sorted(os.listdir(shelf)))
for sub in sorted(os.listdir(shelf)):
    p = os.path.join(shelf, sub)
    if os.path.isdir(p):
        print(" ", sub, len(os.listdir(p)), sorted(os.listdir(p))[:3])
cands = glob.glob(os.path.join(shelf, "**", "*08226d6b72c8*"), recursive=True)
print("candidates:", cands)
for f in cands:
    if os.path.isdir(f):
        continue
    try:
        d = json.load(open(f))
    except Exception as e:
        print("  not json:", f, open(f).read()[:200])
        continue
    print("  keys:", list(d.keys())[:20])
    vals = d.get("values") or d.get("helpers")
    gates = d.get("gates") or d.get("circuit") or (d.get("record") or {}).get("gates")
    if vals is None and gates:
        val = list(INPUTS)
        for a, b in gates:
            val.append(val[a] ^ val[b])
        vals = val[N:]
    if vals:
        L1 = {v for v in vals if bin(v).count("1") == 2}
        for s in (0, 8, 16, 24):
            R = {rot(v, s) for v in L1_main}
            print(f"  rot {s}: overlap {len(L1 & R)} of {len(L1)}; missing {[name(v) for v in R - L1]}; extra {[name(v) for v in L1 - R]}")
# also the shelf members index
for f in glob.glob(os.path.join(shelf, "*.json")) + glob.glob(os.path.join(shelf, "*", "*.json")):
    if "08226d6b72c8" in open(f).read():
        print("  mentioned in", f)
        d = json.load(open(f))
        m = d.get("members") or d
        if isinstance(m, dict) and "08226d6b72c8" in m:
            print("   entry:", json.dumps(m["08226d6b72c8"])[:600])
        break
print("\nslot roots:")
for slot in st["slots"]:
    root = 0
    # root = XOR of the three leaves = (choice) ^ (third leaf); choices a^b, a^c, b^c; leaves = pairwise XORs of choices
    a, b, c = slot
    leaves = [a ^ b, a ^ c, b ^ c]
    root = leaves[0] ^ leaves[1] ^ leaves[2]
    kind = f"output y{T.index(root)}" if root in T else "helper"
    print(f"  leaves {[name(x) for x in leaves]} -> root {name(root)} ({kind}, weight {bin(root).count('1')})")
