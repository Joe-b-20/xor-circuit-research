"""Compare delta(T) = 0 with the forest criterion (Theorem C) over ALL reduced T of size m.

usage: python3 delta_vs_forest.py m          (m = 3, 4, 5; m = 5 takes a few minutes)

For every zero-diagonal T without zero row or column: delta by the closed formula
delta = |D| - 2m + s  (D = distinct nonzero vectors w_k, t_k, t_k + w_k; s = number of pairs j != k with
t_j = w_k and t_k = w_j), cross-checked against the rank definition on a sample; the forest criterion is
evaluated once per class (simultaneous permutation, transpose NOT used since the criterion is not
obviously transpose-invariant).  Prints the number of matrices and classes with delta = 0, and every class
where the two properties differ.
"""
import itertools
import sys

import dmap
import geom


def delta_formula(T):
    m = len(T)
    D = set()
    for k in range(m):
        D.add(1 << k)
        D.add(T[k])
        D.add(T[k] | (1 << k))
    s = 0
    for j in range(m):
        for k in range(j + 1, m):
            if T[j] == (1 << k) and T[k] == (1 << j):
                s += 1
    return len(D) - 2 * m + s


def canon_perm(T):
    m = len(T)
    best = None
    for perm in itertools.permutations(range(m)):
        c = dmap.conj(T, perm)
        if best is None or c < best:
            best = c
    return best


def main():
    m = int(sys.argv[1])
    offdiag = [(j, k) for j in range(m) for k in range(m) if j != k]
    total = red = zero = 0
    classes = {}
    checked = 0
    for bits in range(1 << len(offdiag)):
        T = [0] * m
        for idx, (j, k) in enumerate(offdiag):
            if (bits >> idx) & 1:
                T[j] |= 1 << k
        total += 1
        if not all(T):
            continue
        cols = 0
        for r in T:
            cols |= r
        if cols != (1 << m) - 1:
            continue
        red += 1
        T = tuple(T)
        d = delta_formula(T)
        if red % 97 == 0:
            assert d == geom.delta(T), (T, d, geom.delta(T))
            checked += 1
        if d == 0:
            zero += 1
            c = canon_perm(T)
            classes[c] = classes.get(c, 0) + 1
    print(f"m={m}: zero-diagonal matrices {total}, reduced {red}, with delta = 0: {zero} in {len(classes)} permutation classes"
          f" (formula cross-checked on {checked} matrices)")
    bad = []
    for c in sorted(classes):
        ok, _ = geom.forest_criterion(c)
        if not ok:
            bad.append(c)
    print("classes with delta = 0 but forest criterion false:", len(bad))
    for c in bad[:20]:
        print("   ", dmap.tstr(c))
    # converse on a sample of delta > 0 is implied by Theorem B (forest => circuit with 3m gates => delta = 0)


if __name__ == "__main__":
    main()
