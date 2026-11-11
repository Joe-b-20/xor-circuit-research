"""Finite facts about the boundary of Q_m:  python3 facts.py [m_min m_max]   (default 2 8)

For each m prints
  - rank of Q_m, whether Q_m^T is Q_m up to the relabelling (c,j) -> (-c,-j) of inputs and outputs,
  - the number of zero-sum subsets ("relations") of the 8m boundary vectors (4m units, 4m rows) of
    each weight <= WMAX, split by the number of rows involved, and the rank of the span of the
    weight-6 relations,
  - the histogram of the number of 3-subsets of the boundary with a given XOR (triple multiplicity),
  - the valid partitions: is there a partition of the inputs into m+1 blocks such that every row is
    odd on exactly one block (SAT, pysat), and the number of valid partitions with exactly m blocks.
"""
import itertools
import sys
from collections import Counter

import qm

WMAX = 8


def relations(m, wmax):
    """All zero-sum subsets of the boundary of weight <= wmax, as (row set mask, unit set mask)."""
    n = 4 * m
    R = qm.rows(m)
    half = wmax // 2
    found = set()
    # few rows
    for k in range(1, half + 1):
        for z in itertools.combinations(range(n), k):
            u = 0
            for i in z:
                u ^= R[i]
            if k + qm.popcount(u) <= wmax:
                found.add((sum(1 << i for i in z), u))
    # few units: rows = u * Q^{-1}; row set z with sum_{i in z} R[i] = u  <=> z = u applied to inverse-transpose
    inv = qm.inverse(R, n)  # inv[i] = combination of original rows giving e_i  (as mask over rows)
    for k in range(1, half + 1):
        for us in itertools.combinations(range(n), k):
            z = 0
            for i in us:
                z ^= inv[i]
            if k + qm.popcount(z) <= wmax:
                u = sum(1 << i for i in us)
                found.add((z, u))
    # sanity
    for z, u in found:
        v = 0
        for i in range(n):
            if (z >> i) & 1:
                v ^= R[i]
        assert v == u
    return found


def triple_hist(m):
    n = 4 * m
    B = [1 << i for i in range(n)] + qm.rows(m)
    cnt = Counter()
    for a, b, c in itertools.combinations(range(len(B)), 3):
        cnt[B[a] ^ B[b] ^ B[c]] += 1
    return Counter(cnt.values()), cnt


def pair_sidon(m):
    n = 4 * m
    B = [1 << i for i in range(n)] + qm.rows(m)
    seen = {}
    bad = 0
    for a, b in itertools.combinations(range(len(B)), 2):
        v = B[a] ^ B[b]
        if v in seen:
            bad += 1
        seen[v] = (a, b)
    return len(set(B)) == len(B), bad


def partition_sat(m, nlabels, enumerate_all=False, limit=100000):
    """Valid partitions with exactly nlabels nonempty blocks (restricted-growth labelling)."""
    from pysat.solvers import Solver
    n = 4 * m
    R = qm.rows(m)
    nv = [0]

    def new():
        nv[0] += 1
        return nv[0]

    cl = []
    f = [[new() for _ in range(nlabels)] for _ in range(n)]
    for i in range(n):
        cl.append(f[i][:])
        for a in range(nlabels):
            for b in range(a + 1, nlabels):
                cl.append([-f[i][a], -f[i][b]])
    # restricted growth: input i may use label l >= 1 only if an earlier input uses label l-1
    for i in range(n):
        for l in range(1, nlabels):
            cl.append([-f[i][l]] + [f[i2][l - 1] for i2 in range(i)])
    for l in range(nlabels):
        cl.append([f[i][l] for i in range(n)])
    # parities
    for o in range(n):
        sup = [i for i in range(n) if (R[o] >> i) & 1]
        ps = []
        for l in range(nlabels):
            p = new()
            ps.append(p)
            xs = [f[i][l] for i in sup]
            k = len(xs)
            for signs in itertools.product((0, 1), repeat=k):
                par = sum(signs) & 1
                # assignment xs = signs forces p = par
                base = [(-x if sg else x) for x, sg in zip(xs, signs)]
                cl.append(base + [p if par else -p])
        cl.append(ps[:])
        for a in range(nlabels):
            for b in range(a + 1, nlabels):
                cl.append([-ps[a], -ps[b]])
    sols = []
    with Solver(name="cadical153", bootstrap_with=cl) as S:
        while S.solve():
            model = set(x for x in S.get_model() if x > 0)
            lab = tuple(next(l for l in range(nlabels) if f[i][l] in model) for i in range(n))
            sols.append(lab)
            if not enumerate_all or len(sols) >= limit:
                break
            S.add_clause([-f[i][lab[i]] for i in range(n)])
    return sols


def main():
    lo, hi = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (2, 8)
    for m in range(lo, hi + 1):
        n = 4 * m
        R = qm.rows(m)
        print(f"== m = {m}  (n = {n})")
        print("  rank", qm.rank(R), " row weights", sorted(Counter(map(qm.popcount, R)).items()),
              " column weights", sorted(Counter(map(qm.popcount, qm.transpose(R, n))).items()))
        # transpose symmetry: (c,j) -> (-c,-j)
        perm = [4 * ((-j) % m) + ((-c) % 4) for j in range(m) for c in range(4)]
        RT = qm.transpose(R, n)
        ok = all(sum(((RT[o] >> i) & 1) << perm[i] for i in range(n)) == R[perm[o]] for o in range(n))
        print("  Q^T equals Q after relabelling (c,j)->(-c,-j) on both sides:", ok)
        distinct, bad = pair_sidon(m)
        print(f"  boundary masks distinct: {distinct};  coinciding pair-XORs (weight-4 relations): {bad}")
        rel = relations(m, WMAX)
        byw = Counter()
        for z, u in rel:
            byw[(qm.popcount(z) + qm.popcount(u), qm.popcount(z))] += 1
        print(f"  minimum relation weight: {min(w for w, _ in byw)}")
        for w in sorted(set(w for w, _ in byw)):
            parts = ", ".join(f"{k} rows: {byw[(w, k)]}" for (w2, k) in sorted(byw) if w2 == w)
            print(f"  relations of weight {w}: {sum(v for (w2, _), v in byw.items() if w2 == w)}   ({parts})")
        for wcap in (6, 8):
            vecs = [(z << n) | u for z, u in rel if qm.popcount(z) + qm.popcount(u) <= wcap]
            print(f"  rank of the span of relations of weight <= {wcap}: {qm.rank(vecs)}")
        hist, cnt = triple_hist(m)
        print("  triple multiplicity histogram (representations: number of values):", sorted(hist.items()))
        full = [v for v, k in cnt.items() if k >= 3]
        shapes = Counter()
        for v in full:
            blocks = [(v >> (4 * j)) & 15 for j in range(m)]
            shapes[tuple(sorted(qm.popcount(b) for b in blocks if b))] += 1
        print("  values with >= 3 triple representations, by sorted block weights:", sorted(shapes.items()))
        more = partition_sat(m, m + 1)
        print(f"  valid partition with {m + 1} blocks exists: {bool(more)}")
        if more:
            print("     example labelling (inputs in order 4j+c):", more[0])
            k = m + 1
            while True:
                k += 1
                if k > n or not partition_sat(m, k):
                    break
            print(f"     largest number of blocks: {k - 1}")
        allm = partition_sat(m, m, enumerate_all=True)
        print(f"  valid partitions with exactly {m} blocks: {len(allm)}")
        for lab in allm[:12]:
            print("     ", " ".join("".join(str(lab[4 * j + c]) for c in range(4)) for j in range(m)))


if __name__ == "__main__":
    main()
