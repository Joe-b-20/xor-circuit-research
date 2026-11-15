"""P4: keep a pre-inversion product-part circuit, re-choose the x-linear injections for a given set
of available top values (Avail).  Injection points: node u (all readers of u and u itself if it is
a target), edge u->w (only w), output j (only target j).  Each injection costs one XOR gate.
Finds all k-point solutions X = R S with S in Avail (k = 4, 5).

Used as a library: solutions(achain, nb, P, X, avail, k)
  achain  product-part chain over nb atoms (list of (j, k) node pairs; nodes 0..nb-1 = atoms)
"""
import itertools

import preinj


def points(achain, nb, P):
    vals = [1 << i for i in range(nb)]
    for j, k in achain:
        vals.append(vals[j] ^ vals[k])
    N = len(vals)
    tnode = [vals.index(p) for p in P]
    readers = {u: [] for u in range(N)}
    for i, (j, k) in enumerate(achain):
        readers[j].append(nb + i)
        readers[k].append(nb + i)
    R = [0] * N
    for u in reversed(range(N)):
        r = 0
        for w in readers[u]:
            r ^= R[w]
        for jj, tn in enumerate(tnode):
            if tn == u:
                r ^= 1 << jj
        R[u] = r
    pts = []
    for u in range(N):
        if R[u]:
            pts.append((('node', u), R[u]))
        for w in readers[u]:
            if R[w]:
                pts.append((('edge', u, w), R[w]))
    for jj in range(len(P)):
        pts.append((('out', jj), 1 << jj))
    return vals, tnode, readers, pts


def solutions(achain, nb, P, X, avail, k, limit=1000):
    vals, tnode, readers, pts = points(achain, nb, P)
    byr = {}
    for p, r in pts:
        byr.setdefault(r, []).append(p)
    rv = sorted(byr)
    ntg = len(P)
    av = sorted(avail)
    out = []
    for B in itertools.combinations_with_replacement(rv, k):
        if preinj.rank(list(B)) < preinj.rank(X):
            continue
        # enumerate S: pick a maximal independent subset of B as basis, others free in Avail
        basis = []
        for i in range(k):
            if preinj.rank([B[j] for j in basis] + [B[i]]) > len(basis):
                basis.append(i)
        free = [i for i in range(k) if i not in basis]
        for fv in itertools.product(av, repeat=len(free)):
            Xr = list(X)
            for i, v in zip(free, fv):
                for j in range(ntg):
                    if (B[i] >> j) & 1:
                        Xr[j] ^= v
            Sb = preinj.solve_basis([B[i] for i in basis], Xr, ntg) if len(basis) == ntg else _solve_sub([B[i] for i in basis], Xr, ntg)
            if Sb is None:
                continue
            S = [0] * k
            for i, v in zip(basis, Sb):
                S[i] = v
            for i, v in zip(free, fv):
                S[i] = v
            if all(v in avail for v in S):
                out.append((B, S))
                if len(out) >= limit:
                    return out, byr
    return out, byr


def _solve_sub(B, X, ntg):
    # rank < ntg: least-structure solve via brute force over avail is done by the caller; here try
    # Gaussian elimination on the consistent system
    n = len(B)
    rows = [[(B[p] >> j) & 1 for p in range(n)] + [X[j]] for j in range(ntg)]
    r = 0
    piv = []
    for c in range(n):
        pr = next((i for i in range(r, ntg) if rows[i][c]), None)
        if pr is None:
            continue
        rows[r], rows[pr] = rows[pr], rows[r]
        for i in range(ntg):
            if i != r and rows[i][c]:
                rows[i] = [a ^ b for a, b in zip(rows[i][:n], rows[r][:n])] + [rows[i][n] ^ rows[r][n]]
        piv.append(c)
        r += 1
    for i in range(r, ntg):
        if rows[i][n]:
            return None
    S = [0] * n
    for i, c in enumerate(piv):
        S[c] = rows[i][n]
    return S
