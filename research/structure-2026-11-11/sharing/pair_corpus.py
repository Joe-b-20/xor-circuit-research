"""Pair counts on existing circuits (read-only; a test of the pair bound, not a proof).

usage: python3 pair_corpus.py

For a circuit and two adjacent sheets j, j+1:  D = gates that are ancestors-or-equal of an output gate of sheet
j or j+1 and nonzero on block j or block j+1.  After setting all inputs outside blocks j-1, j, j+1 to zero, D is
a local circuit of the pair problem (block j-1 free) whenever the restricted outputs are [j: E_c] + [j-1: s_c]
and [j+1: E_c] + [j: s_c].  For MixColumns this holds for the pairs (1,2), (2,3), (3,4), (4,5), (5,6), (6,7), (7,0)
(checked below against the matrix), not for (0,1).  Prints the minimum and the histogram of |D| per pair over the
repository circuits, the kste corpus and the hunt records; and the same for the recorded circuits of Q_m.
"""
import glob
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


def nib(v, j):
    return sum(((v >> (8 * c + j)) & 1) << c for c in range(4))


def mc_pairs():
    ok = []
    for j in range(8):
        k = (j + 1) % 8
        a = (j - 1) % 8
        good = True
        for c in range(4):
            E = 15 ^ (1 << c)
            s = (1 << c) | (1 << ((c + 1) % 4))
            tj, tk = mc.TARGETS[8 * c + j], mc.TARGETS[8 * c + k]
            if not (nib(tj, j) == E and nib(tj, a) == s and nib(tj, k) == 0):
                good = False
            if not (nib(tk, k) == E and nib(tk, j) == s and nib(tk, a) == 0):
                good = False
        if good:
            ok.append((j, k))
    return ok


def anc_sup(n, gates, targets, sheet_of, blocks_of, nsheets):
    vals = [1 << i for i in range(n)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    first = {}
    for i in range(n, len(vals)):
        first.setdefault(vals[i], i)
    if any(t not in first for t in targets):
        return None
    anc = [set() for _ in range(nsheets)]
    for oi, t in enumerate(targets):
        seen, stack = set(), [first[t]]
        while stack:
            s = stack.pop()
            if s < n or s in seen:
                continue
            seen.add(s)
            stack.extend(gates[s - n])
        anc[sheet_of(oi)] |= seen
    return anc, [blocks_of(v) for v in vals]


def main():
    pairs = mc_pairs()
    print("MixColumns pairs that restrict to the pair problem:", pairs)
    hist = {p: Counter() for p in pairs}
    where = {}
    nc = 0

    def do(gates, tag):
        nonlocal nc
        r = anc_sup(32, gates, mc.TARGETS, lambda oi: oi % 8, mc.blocks, 8)
        if r is None:
            return
        nc += 1
        anc, sup = r
        for (j, k) in pairs:
            d = sum(1 for g in (anc[j] | anc[k]) if j in sup[g] or k in sup[g])
            hist[(j, k)][d] += 1
            if d <= 20:
                where.setdefault(((j, k), d), tag)

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
            g = mc.parse_pairs(line)
            if len(g) == 88:
                do(g, f"{fn}:{nl}")
    for f in sorted(glob.glob(os.path.join(HUNT, "runs/*/workers/*/records/g88-*.json"))):
        if not f.endswith(".verification.json"):
            do([tuple(x) for x in json.load(open(f))["gates"]], os.path.basename(f))
    print("circuits examined:", nc)
    for p in pairs:
        print(f"   pair {p}: min |D| = {min(hist[p])}  histogram {dict(sorted(hist[p].items()))}")
    print("   first circuits attaining |D| <= 20:", {k: v for k, v in sorted(where.items())})
    C = os.path.join(HERE, "..", "rotation", "circuits")
    for m, name in ((3, "q3_28.txt"), (4, "q4_40.txt"), (4, "walk_q4_40.txt"), (5, "q5_50.txt"), (6, "q6_60.txt"),
                    (7, "q7_70.txt"), (8, "q8_80.txt"), (8, "walk_q8_80.txt"), (12, "q12_120.txt")):
        n, gates = qm.read_circuit(os.path.join(C, name))
        anc, sup = anc_sup(n, gates, qm.rows(m), lambda oi: oi // 4,
                           lambda v, m=m: frozenset(j for j in range(m) if (v >> (4 * j)) & 15), m)
        ds = [sum(1 for g in (anc[j] | anc[(j + 1) % m]) if j in sup[g] or (j + 1) % m in sup[g]) for j in range(m)]
        print(f"{name}: |D| for the pairs (j, j+1), j = 0..{m - 1}: {ds}")


if __name__ == "__main__":
    main()
