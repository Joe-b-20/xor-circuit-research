"""s7_structure.py: structure of the recorded 89@4 family and of the nearest 90@4 states.
Input: q89/states_89.json, q89/states_90.json (from s4_collect.py). Pure python, seconds.
 - rotation classes among the 90 distinct 89@4 value sets (which shift, which campaigns)
 - the variable level-2 values: slots x choices, product check (all combinations present?)
 - is each slot a re-pairing of a 3-leaf XOR tree (3 alternatives a^b, a^c, b^c over fixed leaves)?
 - 90@4 states with 26 first-layer gates: campaigns, overlap with the 89 L1
 - the 90@4 states closest to the 89 L1 (overlap 23-24): per-level difference from L0
 - MixColumns output weights
"""
import json
import os
from collections import Counter, defaultdict
from itertools import combinations

HOME = os.path.expanduser("~")
Q = os.path.join(HOME, "xs-campaigns/2026-11-07-sprint/q89")
MAT = os.path.join(HOME, "xor-circuit-research/circuits/aes-mixcolumns/aes-mixcolumns.mat.txt")
N = 32


def load_targets():
    lines = [l.strip() for l in open(MAT) if l.strip()]
    r, c = map(int, lines[1].split())
    rows = []
    for l in lines[2:2 + r]:
        v = 0
        for j, ch in enumerate(l.replace(" ", "")):
            if ch == "1":
                v |= 1 << j
        rows.append(v)
    return rows


T = load_targets()
TSET = set(T)
INPUTS = [1 << i for i in range(N)]


def rot(v, s):
    return ((v << s) | (v >> (N - s))) & ((1 << N) - 1)


def bits(v):
    return [i for i in range(N) if v >> i & 1]


def name(v):
    return "x" + "+x".join(map(str, bits(v))) if v not in TSET else "y%d" % T.index(v)


def main():
    print("MixColumns output weights:", dict(Counter(bin(t).count("1") for t in T)))
    s89 = json.load(open(os.path.join(Q, "states_89.json")))["states"]
    s90 = json.load(open(os.path.join(Q, "states_90.json")))["states"]
    sets = [frozenset(s["helpers"]) for s in s89]
    # rotation classes
    idx = {s: i for i, s in enumerate(sets)}
    main_L1 = Counter(frozenset(s["L1"]) for s in s89).most_common()
    print("L1 sets among 89@4:", [(len(k), n) for k, n in main_L1])
    L1_main = main_L1[0][0]
    fam = [i for i, s in enumerate(s89) if frozenset(s["L1"]) == L1_main]
    oth = [i for i, s in enumerate(s89) if frozenset(s["L1"]) != L1_main]
    print("main family size", len(fam), "other", len(oth))
    for s in (8, 16, 24):
        hits = sum(1 for i in oth if frozenset(rot(v, s) for v in sets[i]) in idx)
        print(f"  other states whose rotation by {s} is a main-family state: {hits}")
    print("other states: campaigns", Counter(c for i in oth for c in s89[i]["camps"]), "records", sum(s89[i]["n"] for i in oth))
    print("other states: files", [s89[i]["files"][0] for i in oth][:4])
    L1_other = [frozenset(s89[i]["L1"]) for i in oth][0] if oth else None
    if L1_other:
        print("L1 main & other common values:", [name(v) for v in L1_main & L1_other])
        for s in (8, 16, 24):
            print(f"  rot{s}(L1_main) == L1_other:", frozenset(rot(v, s) for v in L1_main) == L1_other)
    # product structure of the main family
    cnt = Counter(v for i in fam for v in sets[i])
    nf = len(fam)
    const = sorted(v for v, c in cnt.items() if c == nf)
    var = sorted(v for v, c in cnt.items() if c != nf)
    print("main family: constant helpers", len(const), "variable helpers", len(var), "counts", dict(Counter(cnt[v] for v in var)))
    # slots: group variable values by the set of states they appear in; two values in the same slot never co-occur
    occ = {v: frozenset(i for i in fam if v in sets[i]) for v in var}
    # build co-occurrence: values that are mutually exclusive and whose occurrence sets partition fam
    slots = []
    used = set()
    for v in var:
        if v in used:
            continue
        slot = [v]
        for w in var:
            if w != v and w not in used and not (occ[v] & occ[w]):
                slot.append(w)
        cover = frozenset().union(*(occ[w] for w in slot))
        slots.append((slot, len(cover) == nf))
        used.update(slot)
    print("slots:", len(slots))
    allvals = set(const) | set(INPUTS) | TSET
    for k, (slot, full) in enumerate(slots):
        x = 0
        for w in slot:
            x ^= w
        # each alternative = XOR of two constant values (leaves)?
        leaves = {}
        for w in slot:
            pairs = [(a, w ^ a) for a in allvals if (w ^ a) in allvals and a < (w ^ a)]
            leaves[w] = pairs
        print(f" slot {k}: choices {[name(w) for w in slot]} partition={full} xor_of_choices={'0' if x == 0 else name(x)}")
        for w in slot:
            print(f"    {name(w)} = " + " | ".join(f"{name(a)}^{name(b)}" for a, b in leaves[w][:4]))
    combos = Counter(tuple(next(w for w in slot if w in sets[i]) for slot, _ in slots) for i in fam)
    print("distinct choice tuples:", len(combos), "max multiplicity", max(combos.values()), "expected product", 1)
    for slot, _ in slots:
        pass
    # where the variable values sit: which outputs use them (recompute levels quickly by depth of tree)
    # 90@4 with |L1| = 26
    print("\n90@4 states by |L1|:", dict(sorted(Counter(len(s["L1"]) for s in s90).items())))
    big = [s for s in s90 if len(s["L1"]) == 26]
    print("90@4 with 26 L1 gates:", len(big), "campaigns", Counter(c for s in big for c in s["camps"]),
          "overlap with 89 L1", Counter(len(set(s["L1"]) & L1_main) for s in big),
          "profiles", Counter(" ".join(map(str, s["profile"])) for s in big))
    near = [s for s in s90 if len(set(s["L1"]) & L1_main) >= 23]
    print("90@4 with >=23 L1 pairs shared:", len(near), "campaigns", Counter(c for s in near for c in s["camps"]),
          "|L1|", Counter(len(s["L1"]) for s in near))
    H89 = set(const) | set(var)
    for s in near[:3]:
        hs = set(s["helpers"])
        print("  near state: helpers shared with 89 union", len(hs & H89), "of", len(hs), "; L1 missing from 89:",
              [name(v) for v in L1_main - set(s["L1"])], "; extra L1:", [name(v) for v in set(s["L1"]) - L1_main])
    # how many 90@4 states have exactly one L1 difference from the 89 L1 (|sym diff| small)
    sd = Counter(len(set(s["L1"]) ^ L1_main) for s in s90)
    print("90@4: |L1 symdiff with 89 L1| histogram:", dict(sorted(sd.items())))
    # the 90@4 L1 sets: how many distinct, and the most common
    c90 = Counter(frozenset(s["L1"]) for s in s90)
    print("90@4 distinct L1 sets:", len(c90), "top sizes:", [(len(k), n) for k, n in c90.most_common(5)])
    json.dump({"L1_main": sorted(L1_main), "const": const, "slots": [[w for w in s] for s, _ in slots], "fam_idx": fam, "oth_idx": oth},
              open(os.path.join(Q, "s7_structure.json"), "w"))


if __name__ == "__main__":
    main()
