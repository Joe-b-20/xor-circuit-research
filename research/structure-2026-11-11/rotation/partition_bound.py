"""Transfer-graph certificate: a valid partition of Q_m has at most m + 1 blocks, for every m >= 3.

usage: python3 partition_bound.py

A valid partition is a labelling f of the inputs (c, j) such that every output
o(c,j) = {(c+1,j),(c+2,j),(c+3,j),(c,j-1),(c+1,j-1)} carries exactly one label an odd number of times.
(REPORT.md, Lemma 1.4) Splitting every label into its maximal cyclic runs of consecutive blocks keeps a
labelling valid and does not decrease the number of labels, so it suffices to bound "connected" labellings.

State  = (set partition pi of Z_4 = the label classes inside one block, set mu of "cyclic" classes).
Edge   = (state of block j-1, state of block j, partial matching between their classes saying which
          classes carry the same label), such that the four output constraints of sheet j hold, cyclic
          classes are matched to cyclic classes and every cyclic class of block j is matched.
Weight = number of classes of block j that are not matched (labels that start in block j).
For a connected valid labelling with kappa labels present in every block, marking exactly these gives a
closed walk of length m with kappa marks in every state, and  #labels = kappa + (sum of the weights).
The script computes, for every kappa, the maximum cycle mean of the weights (Karp) and the maximum total
weight of closed walks of each length m <= MMAX (max-plus matrix powers), and prints the resulting bound
max over kappa of (kappa + max total weight).  The relaxation (closed walks need not come from a
labelling) can only increase the bound.
"""
import itertools
from fractions import Fraction

MMAX = 40
NEG = -10 ** 9


def set_partitions4():
    res = []
    for rg in itertools.product(range(4), repeat=4):
        ok = rg[0] == 0 and all(rg[i] <= max(rg[:i]) + 1 for i in range(1, 4))
        if ok:
            res.append(rg)
    return res


def matchings(k1, k2):
    """Partial injective maps from classes 0..k2-1 of the new block to classes 0..k1-1 of the old block
    (None = unmatched)."""
    out = []
    for img in itertools.product([None] + list(range(k1)), repeat=k2):
        used = [x for x in img if x is not None]
        if len(used) == len(set(used)):
            out.append(img)
    return out


def valid(old, new, img):
    k1 = max(old) + 1
    lab_new = [img[cl] if img[cl] is not None else k1 + cl for cl in new]
    for c in range(4):
        labs = [lab_new[(c + 1) % 4], lab_new[(c + 2) % 4], lab_new[(c + 3) % 4], old[c], old[(c + 1) % 4]]
        odd = sum(1 for l in set(labs) if labs.count(l) % 2 == 1)
        if odd != 1:
            return False
    return True


def main():
    parts = set_partitions4()
    states = []
    for p in parts:
        k = max(p) + 1
        for r in range(k + 1):
            for mu in itertools.combinations(range(k), r):
                states.append((p, frozenset(mu)))
    idx = {s: i for i, s in enumerate(states)}
    S = len(states)
    best = {}
    n_edges = 0
    for p1 in parts:
        k1 = max(p1) + 1
        for p2 in parts:
            k2 = max(p2) + 1
            for img in matchings(k1, k2):
                if not valid(p1, p2, img):
                    continue
                n_edges += 1
                w = sum(1 for x in img if x is None)
                matched_old = {x for x in img if x is not None}
                # markings: mu1 subset of matched old classes, mu2 = their images; marked new classes must be matched
                for r in range(k1 + 1):
                    for mu1 in itertools.combinations(range(k1), r):
                        if not set(mu1) <= matched_old:
                            continue
                        mu2 = frozenset(cl for cl in range(k2) if img[cl] in mu1)
                        a, b = idx[(p1, frozenset(mu1))], idx[(p2, mu2)]
                        if best.get((a, b), NEG) < w:
                            best[(a, b)] = w
    print(f"block states: {len(parts)} set partitions, {S} marked states; valid (old, new, matching) triples: {n_edges}")
    overall = {}
    for kappa in range(5):
        nodes = [i for i, s in enumerate(states) if len(s[1]) == kappa]
        pos = {v: t for t, v in enumerate(nodes)}
        n = len(nodes)
        W = [[NEG] * n for _ in range(n)]
        for (a, b), w in best.items():
            if a in pos and b in pos:
                W[pos[a]][pos[b]] = w
        # max-plus powers: P[L][u][v] = max weight of a walk of length L from u to v
        cur = [row[:] for row in W]
        closed = {}
        for L in range(1, MMAX + 1):
            if L > 1:
                nxt = [[NEG] * n for _ in range(n)]
                for u in range(n):
                    cu = cur[u]
                    for t in range(n):
                        if cu[t] <= NEG // 2:
                            continue
                        wt = W[t]
                        base = cu[t]
                        row = nxt[u]
                        for v in range(n):
                            if wt[v] > NEG // 2 and base + wt[v] > row[v]:
                                row[v] = base + wt[v]
                cur = nxt
            closed[L] = max((cur[u][u] for u in range(n)), default=NEG)
        # Karp maximum cycle mean (over all nodes as sources via a super source)
        D = [[NEG] * n for _ in range(n + 1)]
        for v in range(n):
            D[0][v] = 0
        for kk in range(1, n + 1):
            for u in range(n):
                if D[kk - 1][u] <= NEG // 2:
                    continue
                for v in range(n):
                    if W[u][v] > NEG // 2 and D[kk - 1][u] + W[u][v] > D[kk][v]:
                        D[kk][v] = D[kk - 1][u] + W[u][v]
        mean = None
        for v in range(n):
            if D[n][v] <= NEG // 2:
                continue
            cand = min(Fraction(D[n][v] - D[kk][v], n - kk) for kk in range(n) if D[kk][v] > NEG // 2)
            if mean is None or cand > mean:
                mean = cand
        feas = {L: closed[L] for L in closed if closed[L] > NEG // 2}
        print(f"kappa = {kappa}: {n} states, maximum cycle mean of new labels per block = {mean}")
        print("   m : max #labels = kappa + max closed-walk weight:",
              " ".join(f"{L}:{kappa + feas[L]}" for L in sorted(feas) if L <= 12))
        slack = [(L, L + 1 - (kappa + feas[L])) for L in sorted(feas)]
        worst = min(sl for _, sl in slack) if slack else None
        print(f"   min over 2 <= m <= {MMAX} of (m + 1) - bound: {min((sl for L, sl in slack if L >= 3), default=None)}"
              f"   (m = 2: bound {kappa + feas[2] if 2 in feas else None})")
        overall[kappa] = (mean, feas)
    print("bound(m) = max over kappa:", " ".join(
        f"{L}:{max(k + overall[k][1][L] for k in overall if L in overall[k][1])}" for L in range(2, 13)))


if __name__ == "__main__":
    main()
