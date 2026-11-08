#!/usr/bin/env python3
"""qhubcheck/pk_enum.py -- exhaustive re-derivation of the packing rows PK4, PK5 (and the package's L23 at q = 6, 7).

Lemma 10.4's premise (from Lemma 4.6): the missing-label sets of the helpers with u >= 3 are DISTINCT subsets of a
q-set that pairwise intersect in at most one element.  We enumerate every such family (a clique in the compatibility
graph on the subsets of size >= 3), record the count vector (n_3, n_4, ..., n_q) with n_j = #{helpers with u = j},
and compute the maximum of each candidate row over all families.  A row is valid iff its maximum is <= its constant;
it is tight iff the maximum equals the constant.  For q = 4, 5 we also print the achievable vectors and the facets of
their convex hull (the complete linear description of the packing constraint at the level of these counts).
"""
import itertools, sys
from collections import Counter

def families(q):
    sets = [frozenset(c) for k in range(3, q + 1) for c in itertools.combinations(range(q), k)]
    comp = {s: [t for t in sets if len(s & t) <= 1 and t is not s] for s in sets}
    out = []
    def rec(chosen, cand):
        out.append(tuple(chosen))
        for i, s in enumerate(cand):
            rec(chosen + [s], [t for t in cand[i + 1:] if len(s & t) <= 1])
    rec([], sets)
    return out

def vec(fam, q):
    c = Counter(len(s) for s in fam)
    return tuple(c.get(j, 0) for j in range(3, q + 1))

ROWS = {
    4: [('PK4 as implemented: #{u>=3} <= 1', {3: 1, 4: 1}, 1),
        ('PK4 as stated (N_3 <= 1 with N_j = #{u>=j}): same row', {3: 1, 4: 1}, 1)],
    5: [('PK5 as implemented: n3 + 2 n4 + 2 n5 <= 2', {3: 1, 4: 2, 5: 2}, 2),
        ('PK5 as stated in qhub REPORT, N_j = #{u>=j}: N3 + 2 N4 = n3 + 3 n4 + 3 n5 <= 2', {3: 1, 4: 3, 5: 3}, 2),
        ('PK5 read with the package notation N_j = #{u=j}: n3 + 2 n4 <= 2', {3: 1, 4: 2, 5: 0}, 2),
        ('weaker: #{u>=3} <= 2', {3: 1, 4: 1, 5: 1}, 2)],
    6: [('L23 q=6 (package): N3 + 3N4 + 4N5 + 4N6 <= 4 (N_j = #{u=j})', {3: 1, 4: 3, 5: 4, 6: 4}, 4)],
    7: [('L23 q=7 (package): 2N3 + 7N4 + 12N5 + 14N6 + 14N7 <= 14', {3: 2, 4: 7, 5: 12, 6: 14, 7: 14}, 14)],
}

def hull_facets(points):
    try:
        import numpy as np
        from scipy.spatial import ConvexHull
        P = np.array(points, float)
        if np.linalg.matrix_rank(P - P[0]) < P.shape[1]:
            return ['(points not full-dimensional; no hull computed)']
        H = ConvexHull(P)
        out = set()
        for eq in H.equations:
            a, b = eq[:-1], eq[-1]
            # normalize to integers
            s = min(abs(x) for x in a if abs(x) > 1e-9)
            a2 = tuple(round(x / s, 6) for x in a); b2 = round(-b / s, 6)
            out.add((a2, b2))
        return [f"{' + '.join(f'{c:g} n{j+3}' for j, c in enumerate(a) if c)} <= {b:g}" for a, b in sorted(out)]
    except Exception as e:
        return [f'(hull not computed: {e})']

if __name__ == '__main__':
    for q in (4, 5, 6, 7):
        fams = families(q)
        vecs = Counter(vec(f, q) for f in fams)
        print(f'q = {q}: {len(fams)} families of distinct >=3-subsets pairwise meeting in <= 1 element; '
              f'{len(vecs)} distinct count vectors (n_3..n_{q})')
        if q <= 5:
            print('   achievable vectors:', sorted(vecs))
            print('   convex hull facets:', hull_facets(sorted(vecs)))
        for name, coef, const in ROWS[q]:
            mx = max(sum(coef.get(j + 3, 0) * v[j] for j in range(len(v))) for v in vecs)
            arg = [v for v in vecs if sum(coef.get(j + 3, 0) * v[j] for j in range(len(v))) == mx][:4]
            verdict = 'VALID' if mx <= const else 'INVALID'
            print(f'   {name}: max {mx} vs constant {const}: {verdict}{" (tight)" if mx == const else ""}; maximizers {arg}')
        # the strongest possible conclusions: max #{u>=3}, max n_u for each u, and max total pairs
        print(f'   max #helpers with u>=3: {max(sum(v) for v in vecs)}; max per size: '
              + ', '.join(f'u={j+3}: {max(v[j] for v in vecs)}' for j in range(q - 2)))
