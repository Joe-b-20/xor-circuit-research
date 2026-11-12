"""Numerical test of INDEPENDENT-SHEETS Theorem 2 on existing circuits (read-only; a test, not a proof).

usage: python3 family_check.py [--limit N]

For a circuit and a family J of sheets:  D_J = gates that are ancestors-or-equal of an output gate of a sheet
of J and nonzero on the own block of some sheet of J.  Theorem 2 claims |D_J| >= 10 |J| when the windows are
pairwise disjoint and no output of J meets the own block of another sheet of J.
Also counts the gates of D_J that are charged to two different sheets of J (nonzero on both own blocks and
ancestors of outputs of both): the double services inside the family.

MixColumns: J = {0,2,4,6}, {1,3,5}, {7}, and every admissible J found by the conditions (i), (ii).
Rotation model: all sets of pairwise non-adjacent sheets of the recorded circuits of Q_m.
"""
import glob
import itertools
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "rotation", "mc"))
sys.path.insert(0, os.path.join(HERE, "..", "rotation"))
import mc  # noqa: E402
import qm  # noqa: E402

HOME = os.path.expanduser("~")
KSTE = os.path.join(HOME, "xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor")
HUNT = os.path.join(HOME, "xs-campaigns/2026-11-07-sprint/hunt")
REPO = os.path.join(HERE, "..", "..", "..", "circuits", "aes-mixcolumns")


def anc_sets(n, gates, target_masks, nsheets, sheet_of, blocks_of):
    vals = [1 << i for i in range(n)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    first = {}
    for i in range(n, len(vals)):
        first.setdefault(vals[i], i)
    if any(t not in first for t in target_masks):
        return None
    anc = [set() for _ in range(nsheets)]
    for oi, t in enumerate(target_masks):
        seen, stack = set(), [first[t]]
        while stack:
            s = stack.pop()
            if s < n or s in seen:
                continue
            seen.add(s)
            stack.extend(gates[s - n])
        anc[sheet_of(oi)] |= seen
    sup = [blocks_of(v) for v in vals]
    return anc, sup


def family_count(anc, sup, J):
    D = set()
    for j in J:
        D |= {g for g in anc[j] if sup[g] & set(J)}
    double = sum(1 for g in D if sum(1 for j in J if j in sup[g] and g in anc[j]) >= 2)
    return len(D), double


def mc_admissible():
    S = mc.SHEET_SUPPORT
    win = [frozenset([(j - 1) % 8, j]) for j in range(8)]
    out = []
    for r in range(1, 5):
        for J in itertools.combinations(range(8), r):
            if any(win[a] & win[b] for a, b in itertools.combinations(J, 2)):
                continue
            if any(b in S[a] for a in J for b in J if a != b):
                continue
            out.append(J)
    return out


def main():
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    fams = mc_admissible()
    print("MixColumns: admissible families (conditions (i), (ii)):", len(fams), " maximal ones:",
          [J for J in fams if not any(set(J) < set(K) for K in fams)])
    worst = {J: None for J in fams}
    dbl = Counter()
    nc = 0

    def do(gates, tag):
        nonlocal nc
        res = anc_sets(32, gates, mc.TARGETS, 8, lambda oi: oi % 8, mc.blocks)
        if res is None:
            return
        nc += 1
        anc, sup = res
        for J in fams:
            k, d = family_count(anc, sup, J)
            slack = k - 10 * len(J)
            if worst[J] is None or slack < worst[J][0]:
                worst[J] = (slack, tag)
            if d:
                dbl[J] += 1

    for f in sorted(glob.glob(os.path.join(REPO, "*.circ.txt"))):
        do(mc.parse_ncff(f), os.path.basename(f))
    nl = 0
    for fn in ("circuits_1.txt", "circuits_2.txt", "circuits_3.txt", "circuits_depth5.txt"):
        p = os.path.join(KSTE, fn)
        if not os.path.exists(p):
            continue
        for line in open(p):
            if not line.strip():
                continue
            nl += 1
            if limit and nl > limit:
                break
            g = mc.parse_pairs(line)
            if len(g) == 88:
                do(g, f"{fn}:{nl}")
    for f in sorted(glob.glob(os.path.join(HUNT, "runs/*/workers/*/records/g88-*.json"))):
        if f.endswith(".verification.json"):
            continue
        do([tuple(x) for x in json.load(open(f))["gates"]], os.path.basename(f))
    print(f"MixColumns circuits examined: {nc}")
    bad = 0
    for J in fams:
        slack, tag = worst[J]
        if slack < 0:
            bad += 1
        if len(J) >= 3 or slack < 0 or J in ((7,),):
            print(f"   J = {J}: min |D_J| - 10|J| = {slack} (at {tag}); circuits with a double service inside J: {dbl[J]}")
    print("   smallest slack over all admissible families:", min(w[0] for w in worst.values()),
          " families violated:", bad)
    # rotation model
    C = os.path.join(HERE, "..", "rotation", "circuits")
    for m, name in ((4, "q4_40.txt"), (4, "walk_q4_40.txt"), (5, "q5_50.txt"), (6, "q6_60.txt"), (7, "q7_70.txt"),
                    (8, "q8_80.txt"), (8, "walk_q8_80.txt"), (3, "q3_28.txt")):
        n, gates = qm.read_circuit(os.path.join(C, name))
        res = anc_sets(n, gates, qm.rows(m), m, lambda oi: oi // 4,
                       lambda v, m=m: frozenset(j for j in range(m) if (v >> (4 * j)) & 15))
        anc, sup = res
        ws, nf = None, 0
        for r in range(1, m // 2 + 1):
            for J in itertools.combinations(range(m), r):
                if any((a - b) % m in (1, m - 1) for a, b in itertools.combinations(J, 2)):
                    continue
                nf += 1
                k, d = family_count(anc, sup, J)
                if ws is None or k - 10 * r < ws[0]:
                    ws = (k - 10 * r, J, d)
        print(f"{name}: families of pairwise non-adjacent sheets: {nf}; min |D_J| - 10|J| = {ws[0]} at J = {ws[1]} (double services there: {ws[2]})")


if __name__ == "__main__":
    main()
