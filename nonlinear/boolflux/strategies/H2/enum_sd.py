"""Enumerate all bilinear spans S = T + W (W <= M/T, dim e), spanned by the members inside S.
Saves per d = 8 + e: list of member-index lists.  Usage: enum_sd.py e [e ...]"""
import itertools, pickle, sys, time, os
from h2lib import Basis
import relax as RX


def subspaces(n, e):
    """All e-dim subspaces of F_2^n as lists of RREF basis rows (ints)."""
    for pivots in itertools.combinations(range(n), e):
        # row i has pivot bit pivots[i] (as highest set bit) ; free positions: lower bits not pivots
        frees = []
        for i, p in enumerate(pivots):
            fr = [b for b in range(p) if b not in pivots]
            frees.append(fr)
        tot = sum(len(f) for f in frees)
        for bits in range(1 << tot):
            rows = []; off = 0
            for i, p in enumerate(pivots):
                r = 1 << p
                for j, b in enumerate(frees[i]):
                    if bits >> (off + j) & 1: r |= 1 << b
                off += len(frees[i])
                rows.append(r)
            yield rows


if __name__ == '__main__':
    M = RX.all_members()
    T = [RX.target_parts(1 << i, 0)[0] for i in range(8)]
    TB = Basis()
    for t in T: TB.add(t)
    img = [TB.full_reduce(m[0])[0] for m in M]
    # compress images to 8-bit coordinates: quotient basis
    pts = sorted(set(img) - {0})
    QB = Basis(track=True)
    qcoord = {}
    basis_vecs = []
    for p in pts:
        if QB.add(p, 1 << len(basis_vecs)): basis_vecs.append(p)
    assert len(basis_vecs) == 8
    for i, p in enumerate(img):
        r, tag = QB.full_reduce(p)
        assert r == 0
        qcoord[i] = tag
    groups = {}
    for i in range(len(M)): groups.setdefault(qcoord[i], []).append(i)
    for e in map(int, sys.argv[1:]):
        t0 = time.time(); res = []; hist = {}
        for rows in subspaces(8, e):
            Wsp = [0]
            for r in rows: Wsp += [s ^ r for s in Wsp]
            inside = []
            for wv in Wsp: inside += groups.get(wv, [])
            S = Basis()
            for i in inside: S.add(M[i][0])
            if S.n == 8 + e and all(S.contains(t) for t in T):
                res.append(sorted(inside))
                hist[len(inside)] = hist.get(len(inside), 0) + 1
        print('d =', 8 + e, 'spans', len(res), 'members-in-S hist', dict(sorted(hist.items())), round(time.time() - t0, 1), flush=True)
        pickle.dump(res, open(os.path.expanduser('~/xs-campaigns/2026-11-15-study/H2/S%d.list.pkl' % (8 + e)), 'wb'))
