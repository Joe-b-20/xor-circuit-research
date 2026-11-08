"""c7_facts3.py -- solver-free: (a) Lemma-5 recipes over P89 (level-4 weight-5 output = adjacent level-3
output + quartet): which of the 20 quartets o+y lie in U2(P89)?  (b) parity structure of recipes:
level-4 output (odd) = odd operand + even operand; fan-outs of odd / even helpers.  (c) per weight-5
output: R1-free / R1-U2 / R2-output / R2-hh recipe counts (as c4 did for weight-7)."""
import json, os, sys, collections, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c2_model as M
U = M.Universe(M.P89, strict=True); T = M.T; W = M.W; pc = M.pc; TSET = M.TSET
le4 = json.load(open(os.path.join(M.D4B, "d1_facts.json")))["pairs_le4"]
l5 = [(i, j, T[i] ^ T[j]) for i, j, w in le4]
inU2 = [(i, j) for i, j, q in l5 if q in U.U2set]
print(f"(a) of the 20 adjacent weight-5 output pairs, quartets o+y in U2(P89): {len(inU2)} -> {inU2}")
print("    quartets o+y that are sums of two P89 pairs:", [(i, j) for i, j, q in l5 if any((q & p) == p and (q ^ p) in set(M.P89) for p in M.P89)])
# (b) parity fan-outs
odd = {s: v for s, v in U.fan.items() if pc(s) % 2 == 1 and s not in TSET}
even = {s: v for s, v in U.fan.items() if pc(s) % 2 == 0 and s not in TSET}
print("(b) odd helpers:", len(odd), " fan hist", sorted(collections.Counter(len(v) for v in odd.values()).items()))
print("    even helpers:", len(even), " fan hist", sorted(collections.Counter(len(v) for v in even.values()).items()))
f7o = collections.Counter(sum(1 for i in v if W[i] == 7) for v in odd.values())
f7e = collections.Counter(sum(1 for i in v if W[i] == 7) for v in even.values())
print("    fan into W7: odd", sorted(f7o.items()), " even", sorted(f7e.items()))
# (c) weight-5 outputs recipe types
for i in M.W5:
    o = T[i]; c = collections.Counter()
    for s in U.fan_inv[i]:
        t = o ^ s
        if s in TSET:
            c["s = level-3 output" + (" (Lemma-5, t in V2)" if t in U.V2 else " + helper")] += 1; continue
        if t in U.base: c["R1 free"] += 1
        elif t in U.U2set: c["R1 U2"] += 1
        elif t in TSET: c["R2 output partner"] += 1
        else: c["R2 hh (ordered)"] += 1
    print(f"   y{i}: {dict(c)}")
