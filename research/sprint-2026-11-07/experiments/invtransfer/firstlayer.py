"""Step 4 (finding e): first-layer (level-1 pair) structure of the 118@5 family.
Level-1 pairs of a value set = its weight-2 values (a weight-2 value can only be input ^ input).
Writes firstlayer118.json."""
import json
from collections import Counter, defaultdict
import common as C
import pes_lib

sp = pes_lib.make_space("inv", 5)
R = C.load("records118.json")["states"]
PL = C.load("plateaus118.json")
member_of = PL["member_of"]
tset = sp.tset


def l1_of(hk):
    vals = set(hk) | tset
    return frozenset(v for v in vals if bin(v).count("1") == 2)


def canon(pairs):
    return C.canon_mod_rot(sp, pairs)


L1 = {k: l1_of(e["hk"]) for k, e in R.items()}
sizes = Counter(len(s) for s in L1.values())
distinct = set(L1.values())
distinct_rot = set(canon(s) for s in L1.values())
n = len(L1)
allp = Counter(p for s in L1.values() for p in s)
in_all = [p for p, c in allp.items() if c == n]
ge90 = sum(1 for c in allp.values() if c >= 0.9 * n)
ge50 = sum(1 for c in allp.values() if c >= 0.5 * n)
same_bit = sum(1 for p in allp if (p >> 8 | p >> 16 | p >> 24 | p) & 0xff and bin(p & 0xff | (p >> 8) & 0xff | (p >> 16) & 0xff | (p >> 24) & 0xff).count("1") == 1)
# per plateau: does L1 vary inside a plateau?
perpl = defaultdict(set)
for k, pid in member_of.items():
    perpl[pid].add(L1[k])
varying = sum(1 for s in perpl.values() if len(s) > 1)
# per plateau L1 of the full closure (union over factors): use plateaus' factor values
pl_l1 = {}
for p in PL["plateaus"]:
    vs = set()
    for f in p["factors"]:
        for ch in f["values_hex"]:
            for h in ch:
                v = int(h, 16)
                if bin(v).count("1") == 2:
                    vs.add(v)
    pl_l1[p["pid"]] = sorted(hex(v) for v in vs)
# overlap between distinct layers (Jaccard, after best rotation)
dl = list(distinct_rot)
import itertools
jac = []
for a, b in itertools.combinations(dl[:60], 2):
    A, B = set(a), set(b)
    best = 0
    for s in sp.shifts:
        Bs = set(sp.rot(tuple(sorted(B)), s)) if s else B
        j = len(A & Bs) / len(A | Bs)
        best = max(best, j)
    jac.append(best)
out = {"n_states": n, "size_hist": dict(sorted(sizes.items())), "distinct_L1": len(distinct),
       "distinct_L1_mod_rot": len(distinct_rot), "pairs_ever_used": len(allp),
       "pairs_in_all": len(in_all), "pairs_in_all_hex": sorted(hex(p) for p in in_all),
       "pairs_ge90": ge90, "pairs_ge50": ge50,
       "plateaus_with_varying_L1": varying, "plateaus_total": len(perpl),
       "mobile_L1_pairs_per_plateau": {str(k): v for k, v in pl_l1.items()},
       "mean_jaccard_distinct_layers": sum(jac) / len(jac) if jac else None,
       "pair_frequency": {hex(p): c for p, c in allp.most_common()}}
C.dump("firstlayer118.json", out)
for k, v in out.items():
    if k not in ("pair_frequency", "mobile_L1_pairs_per_plateau"):
        print(k, ":", v)
print("mobile L1 pairs per plateau (first 10):", {k: v for k, v in list(pl_l1.items())[:10]})
print("frequency of the pairs not in all (top 20):", [(h, c) for h, c in out["pair_frequency"].items() if c < n][:20])
