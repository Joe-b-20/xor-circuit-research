"""c4_facts2.py -- solver-free facts on the level-4 recipes of the weight-7 outputs over P89 (strict S).
For each weight-7 output: R1 recipes split by partner type (input/pair = free, U2 mask = costs x_t),
R2 recipes split into (helper, weight-5 output) and (helper, helper); the helper weights involved.
"""
import json, os, sys, collections, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c2_model as M
pc = M.pc
U = M.Universe(M.P89, strict=True)
print(U.info())
T = M.T; TSET = M.TSET; W = M.W
rows = {}
for i in M.W7:
    o = T[i]
    c = collections.Counter()
    for s in U.fan_inv[i]:
        t = o ^ s
        if t in U.base: c["R1 free partner"] += 1
        elif t in U.U2set: c["R1 U2 partner"] += 1
        elif t in TSET: c["R2 partner = output"] += 1
        elif s in TSET: pass
        else: c["R2 helper+helper (ordered)"] += 1
    rows[i] = dict(c)
    print(f"y{i}: {dict(c)}")
# helpers with fan into W7 >= 2 using only R1 recipes (partners in V2): distribution of partner types
share = collections.Counter()
for s, outs in U.fan.items():
    if s in TSET: continue
    o7 = [i for i in outs if W[i] == 7 and (T[i] ^ s) in U.V2]
    if len(o7) >= 2:
        kinds = tuple(sorted("free" if (T[i] ^ s) in U.base else "U2" for i in o7))
        share[(len(o7), kinds)] += 1
print("helpers serving >= 2 weight-7 outputs via R1 only: (count, partner kinds) ->", dict(share))
# pairs of weight-7 outputs that can share a helper via R1 with both partners free
free_share = collections.defaultdict(list)
for s, outs in U.fan.items():
    if s in TSET: continue
    o7 = [i for i in outs if W[i] == 7 and (T[i] ^ s) in U.base]
    for a, b in itertools.combinations(sorted(o7), 2):
        free_share[(a, b)].append(s)
print("weight-7 output pairs sharing an R1 helper with both partners free:", {k: len(v) for k, v in sorted(free_share.items())})
# helper masks of type 'output partner' for W7 (s = o + y, y weight-5): how many, their fan
oc = {}
for i in M.W7:
    for j in M.W5:
        s = T[i] ^ T[j]
        if s in U.S: oc.setdefault(s, set()).add((i, j))
print(f"distinct helper masks o7 + y5 in S: {len(oc)}; fan of those into W7 via output partners: ",
      sorted(collections.Counter(len({i for i, j in v}) for v in oc.values()).items()))
json.dump({"W7_recipe_types": rows, "free_share": {f"{a},{b}": len(v) for (a, b), v in free_share.items()}},
          open(os.path.join(M.HERE, "c4_facts2.json"), "w"))
