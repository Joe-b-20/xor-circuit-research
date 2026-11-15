"""P4: the pre-inversion layer as (product-part circuit) + (x-linear injections).

Every XOR gate of the layer either merges two signals with non-zero product parts (an 'a-gate') or
adds an x-linear signal s to one signal (an 'injection'; s must be a signal the top layer computes,
'Avail', or costs extra top gates).  The x-part of target j is the sum, over injection points p
whose output reaches target j along an odd number of paths, of s_p:  X = R S, where R (targets x
points) is the 0/1 reach matrix.  So k injections can realise X only if rank X <= k, and with
k = rank X = 4 the points' reach vectors form a basis B of GF(2)^4 and S = B^-1 X is forced.

This script:
  1. reads the layer (targets t30..t33 of the reference = the inversion inputs) and Avail;
  2. lists the 4-sets of reach vectors (bases) whose forced injections S all lie in Avail ('good');
  3. enumerates product-part circuits with SAT (linslp2, blocking clauses) at a given size and
     reports which of them offer a good basis among their injection points (node, edge, output).
[C] statements hold for: same AND gates, same targets, injections from Avail only.

    python3 preinj.py CIRC --targets t30,t31,t32,t33 [--asteps 10] [--max 2000]
"""
import argparse
import itertools
import json
import sys

import circ
import linslp2


def rank(rows):
    rows = [r for r in rows if r]
    rk = 0
    rows = list(rows)
    while rows:
        p = max(rows)
        hb = p.bit_length() - 1
        rows = [r ^ p if (r >> hb) & 1 else r for r in rows if r != p]
        rows = [r for r in rows if r]
        rk += 1
    return rk


def solve_basis(B, X, ntg):
    """B: list of 4 reach vectors (bit j = target j); X: list of ntg x-vectors.  Solve sum_p B[p][j] s_p = X[j]."""
    n = len(B)
    # matrix M (ntg x n) with M[j][p] = B[p] bit j; augmented with X[j]
    rows = [([(B[p] >> j) & 1 for p in range(n)], X[j]) for j in range(ntg)]
    piv = []
    r = 0
    rows = [list(a) + [b] for a, b in rows]
    for c in range(n):
        pr = next((i for i in range(r, ntg) if rows[i][c]), None)
        if pr is None:
            return None
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circ')
    ap.add_argument('--targets', default='t30,t31,t32,t33')
    ap.add_argument('--asteps', type=int, default=10)
    ap.add_argument('--max', type=int, default=2000)
    ap.add_argument('--k', type=int, default=4)
    a = ap.parse_args()
    gates = circ.read(a.circ)
    s = circ.symbolic(gates)
    xs = [f'x{i}' for i in range(8)]
    names = a.targets.split(',')
    prod = sorted({t for n in names for t in s[n][0] if t[0] != 'x'}, key=lambda t: int(t[1:]))
    xm = lambda atoms: sum(1 << int(t[1:]) for t in atoms if t[0] == 'x')
    am = lambda atoms: sum(1 << prod.index(t) for t in atoms if t[0] != 'x')
    X = [xm(s[n][0]) for n in names]
    P = [am(s[n][0]) for n in names]
    avail = {xm(s[o][0]) for op, o, ins in gates if op != 'AND' and s[o][0] <= set(xs)}
    avail |= {1 << i for i in range(8)}
    print('products', prod, 'rank X', rank(X), 'avail', len(avail), file=sys.stderr)
    ntg = len(names)
    vecs = list(range(1, 1 << ntg))
    good = []
    av0 = sorted(avail | {0})
    for B in itertools.combinations(vecs, a.k):
        if rank(list(B)) < ntg:
            continue
        # choose a basis subset of B; the other points are free: try every Avail value for them
        basis = None
        for sub in itertools.combinations(range(a.k), ntg):
            if rank([B[i] for i in sub]) == ntg:
                basis = sub
                break
        free = [i for i in range(a.k) if i not in basis]
        for fv in itertools.product(av0, repeat=len(free)):
            Xr = list(X)
            for i, v in zip(free, fv):
                for j in range(ntg):
                    if (B[i] >> j) & 1:
                        Xr[j] ^= v
            Sb = solve_basis([B[i] for i in basis], Xr, ntg)
            if Sb is None:
                continue
            S = [0] * a.k
            for i, v in zip(basis, Sb):
                S[i] = v
            for i, v in zip(free, fv):
                S[i] = v
            if all(v in avail for v in S):    # every point is a real injection (k gates)
                good.append((B, S))
                break
    print(json.dumps(dict(k=a.k, good_sets=len(good))))
    for B, S in good[:50]:
        print(json.dumps(dict(reach=[bin(b) for b in B], inj=[circ.fmt((frozenset(f'x{i}' for i in range(8) if v >> i & 1), 0)) for v in S])))
    if not good:
        return
    goodsets = [set(B) for B, S in good]
    # enumerate product-part circuits
    base = [1 << i for i in range(len(prod))]
    found = 0
    hits = 0
    from pysat.formula import IDPool
    blocked = []
    while found < a.max:
        st, ch, el = slp_block(len(prod), base, P, a.asteps, blocked)
        if st != 'sat':
            print(json.dumps(dict(enum_done=st, circuits=found, hits=hits)))
            break
        found += 1
        blocked.append(ch)
        vals = linslp2.values(base, ch)
        nb = len(base)
        N = len(vals)
        # node reach: R[u] = bitmask over targets of odd path parity from node u to target node
        tnode = [vals.index(p, nb) if p in vals[nb:] else vals.index(p) for p in P]
        readers = {u: [] for u in range(N)}
        for i, (j, k) in enumerate(ch):
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
        pts = set()
        for u in range(N):
            pts.add(R[u])                 # node injection
            for w in readers[u]:
                pts.add(R[w] if True else 0)  # edge injection u->w (reaches what w reaches)
        for jj in range(ntg):
            pts.add(1 << jj)              # output injection
        pts.discard(0)
        ok = [g for g in goodsets if g <= pts]
        if ok:
            hits += 1
            print(json.dumps(dict(hit=found, chain=ch, good=[sorted(map(bin, g)) for g in ok[:5]])))
    print(json.dumps(dict(circuits=found, hits=hits)))


def slp_block(dim, base, targets, steps, blocked):
    """linslp2 with blocking of previous chains (exact chain match)."""
    import linslp2 as L2
    from pysat.solvers import Solver
    return _solve_with_blocks(dim, base, targets, steps, blocked)


_cache = {}


def _solve_with_blocks(dim, base, targets, steps, blocked):
    # rebuild each time (simple); blocking: not all (l,r) choices equal those of a previous chain
    import linslp2 as L2
    from pysat.formula import IDPool
    from pysat.solvers import Solver
    key = (dim, tuple(base), tuple(targets), steps)
    if key not in _cache:
        cls, pool = L2.build(dim, base, targets, steps)
        S = Solver(name='cadical153', bootstrap_with=cls)
        _cache[key] = (S, pool)
    S, pool = _cache[key]
    nb = len(base)
    if blocked:
        ch = blocked[-1]
        S.add_clause([-pool.id(('l', nb + i, j)) for i, (j, k) in enumerate(ch)] +
                     [-pool.id(('r', nb + i, k)) for i, (j, k) in enumerate(ch)])
    if not S.solve():
        return 'unsat', None, 0
    model = set(l for l in S.get_model() if l > 0)
    chain = []
    N = nb + steps
    for i in range(nb, N):
        j = next(j for j in range(i - 1) if pool.id(('l', i, j)) in model)
        k = next(k for k in range(1, i) if pool.id(('r', i, k)) in model)
        chain.append((j, k))
    return 'sat', chain, 0


if __name__ == '__main__':
    main()
