#!/usr/bin/env python3
"""rgeo.py -- reviewer's OWN finite geometry for M^T (independent of geo_q3 / jc_geo / enum_q3 / verify_q3).

Boundary B (M^T): the 32 input unit masks and the 32 columns of M (output i of M^T has mask sum_j M[j][i] x_j).
Index k of B: 0..31 inputs, 32..63 outputs.  Subsets of B are 64-bit ints over these indices.
Formal vectors: bits 0..63 boundary coordinates, bit 64+i helper coordinate H_i.
Rank: Gaussian elimination keyed on the HIGHEST set bit with a fully reduced basis (written here).
"""
import itertools, sys, time
from collections import defaultdict, Counter

MAT = '/home/joebachir20/xor-circuit-research/circuits/aes-mixcolumns/aes-mixcolumns.mat.txt'


def read_M():
    lines = [l.split() for l in open(MAT) if l.strip()]
    k = next(i for i, l in enumerate(lines) if l == ['32', '32'])
    M = [[int(x) for x in l] for l in lines[k + 1:k + 33]]
    assert len(M) == 32 and all(len(r) == 32 and set(r) <= {0, 1} for r in M)
    return M


def boundary_Mt():
    M = read_M()
    cols = []
    for i in range(32):
        m = 0
        for j in range(32):
            if M[j][i]: m |= 1 << j
        cols.append(m)
    B = [1 << j for j in range(32)] + cols
    assert len(set(B)) == 64
    assert all(bin(b).count('1') % 2 == 1 for b in B)
    return B


def rot(m):
    """byte rotation: bit i -> bit i+8 (mod 32)."""
    return ((m << 8) & 0xFFFFFFFF) | (m >> 24)


def orbit_min(m):
    best = m; x = rot(m)
    while x != m:
        if x < best: best = x
        x = rot(x)
    return best


def rank(vecs):
    basis = {}               # highest bit -> vector, fully reduced on pivots
    for v in vecs:
        while v:
            hb = v.bit_length() - 1
            p = basis.get(hb)
            if p is None:
                basis[hb] = v
                break
            v ^= p
    return len(basis)


class Basis:
    """incremental basis (copyable) for depth-first search."""
    __slots__ = ('piv',)

    def __init__(self, piv=None):
        self.piv = dict(piv) if piv else {}

    def copy(self):
        return Basis(self.piv)

    def add(self, v):
        piv = self.piv
        while v:
            hb = v.bit_length() - 1
            p = piv.get(hb)
            if p is None:
                piv[hb] = v
                return True
            v ^= p
        return False

    def add_all(self, vs):
        for v in vs:
            if not self.add(v): return False
        return True


class Geo:
    def __init__(self, with_ranks=True, verbose=False):
        t0 = time.time()
        B = boundary_Mt(); self.B = B; self.Bset = set(B); self.idx = {b: k for k, b in enumerate(B)}
        pair = {}
        for i, j in itertools.combinations(range(64), 2):
            v = B[i] ^ B[j]
            assert v not in pair, 'F2 fails'
            pair[v] = (1 << i) | (1 << j)
        self.pair = pair
        trip = defaultdict(list)
        for i, j, k in itertools.combinations(range(64), 3):
            trip[B[i] ^ B[j] ^ B[k]].append((1 << i) | (1 << j) | (1 << k))
        self.trip = dict(trip)
        self.f3 = Counter(len(t) for t in self.trip.values())
        self.fulls = sorted(v for v, t in self.trip.items() if len(t) == 3)
        self.rotB = all(rot(b) in self.Bset for b in B) and all(rot(b) in set(B[:32]) for b in B[:32]) and all(rot(b) in set(B[32:]) for b in B[32:])
        self.rank_of = {}
        if with_ranks:
            self._ranks()
        if verbose:
            print('F3', dict(self.f3), 'fulls', len(self.fulls), 'rotB', self.rotB, 'Lambda_1', len(self.rank_of),
                  'rank hist', sorted(Counter(self.rank_of.values()).items()), f'{time.time()-t0:.0f}s', flush=True)

    def _ranks(self):
        """rank(C_l) for every even l with a 2- or 4-subset form: built from pairs of disjoint boundary pairs."""
        items = list(self.pair.items())
        forms = defaultdict(set)
        for v, m in items: forms[v].add(m)
        n = len(items)
        for a in range(n):
            va, ma = items[a]
            for b in range(a + 1, n):
                vb, mb = items[b]
                if ma & mb: continue
                forms[va ^ vb].add(ma | mb)
        E = 1 << 64
        rk = {}
        for l, ds in forms.items():
            if len(ds) == 1: rk[l] = 1
            else: rk[l] = rank([E | d for d in ds])
        self.rank_of = rk
        del forms

    def rk(self, l): return self.rank_of.get(l, 0)

    def labels_ge(self, w):
        return sorted(l for l, r in self.rank_of.items() if r >= w)


if __name__ == '__main__':
    G = Geo(verbose=True)
    for w in range(1, 8):
        L = G.labels_ge(w)
        print('rank >=', w, len(L), 'orbit reps', sum(1 for l in L if orbit_min(l) == l))
    print('triple values', len(G.trip), 'with >=2 triples', sum(1 for t in G.trip.values() if len(t) >= 2))
