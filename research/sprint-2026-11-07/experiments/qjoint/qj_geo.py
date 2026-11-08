#!/usr/bin/env python3
"""qjoint/qj_geo.py -- shared finite geometry for the joint hub searches (both orientations).

Coordinates of the formal vectors (python ints as GF(2) bit vectors):
  bits 0..63          the boundary masks B[0..63] (B_b)
  bit 64 + j          the full helper with global index j (H_f), j < 112
  bit 200 + k         hub number k of a configuration (H_i)
A triple / pair stands for the sum of its boundary coordinates (bit masks over 0..63), as in qhub/hub2.py.

Joint family of a configuration (qhub section 2 / qcert3 C.3 applied to all hubs at once; derivation in REPORT.md
section 2): hubs k = 0..K-1 with values h_k, represented triples R_k (r_k <= 2 of the F3 triples of h_k), witness full
sets S_k subset of N(h_k) (the full helpers met at full-met missing labels of hub k), and a set X of hub pairs sharing a
hub-only missing label:
   {H_f + T : f in union S_k, T triple of f}  u  {H_k + T : T in R_k}  u  {H_k + H_f + P(h_k + f) : f in S_k}
   u  {H_k + H_k' + P(h_k + h_k') : (k, k') in X}.
"""
import sys, json, itertools
from collections import defaultdict
from pathlib import Path
SPRINT = Path.home()/'xs-campaigns/2026-11-07-sprint'
sys.path.insert(0, str(SPRINT/'lb76/pkg_copy/source/lower_bounds/checks'))
from stress import BOUNDARY  # noqa: E402

def FULLC(j): return 1 << (64 + j)
def HUBC(k): return 1 << (200 + k)
BMASK = (1 << 64) - 1

def rank(vectors):
    piv = {}
    r = 0
    for v in vectors:
        while v:
            hb = v.bit_length() - 1
            if hb in piv: v ^= piv[hb]
            else: piv[hb] = v; r += 1; break
    return r

def independent(vectors):
    return rank(vectors) == len(vectors)

class Basis:
    """incremental GF(2) basis with undo (as hub2.py)"""
    def __init__(self): self.piv = {}; self.stack = []
    def add(self, v):
        while v:
            hb = v.bit_length() - 1
            if hb in self.piv: v ^= self.piv[hb]
            else: self.piv[hb] = v; self.stack.append(hb); return True
        return False
    def mark(self): return len(self.stack)
    def undo(self, m):
        while len(self.stack) > m: del self.piv[self.stack.pop()]

def bits(m):
    while m:
        b = m & -m; yield b.bit_length() - 1; m ^= b

class Geo:
    def __init__(self, ori):
        self.ori = ori
        B = BOUNDARY[ori]; self.B = B; self.Bset = set(B)
        self.bidx = {v: i for i, v in enumerate(B)}
        trip = defaultdict(list)
        for i, j, k in itertools.combinations(range(64), 3):
            trip[B[i] ^ B[j] ^ B[k]].append((1 << i) | (1 << j) | (1 << k))
        self.trip = trip
        self.fulls = sorted(v for v, ts in trip.items() if len(ts) == 3)
        self.fidx = {f: j for j, f in enumerate(self.fulls)}
        self.pairmask = {}
        for i, j in itertools.combinations(range(64), 2): self.pairmask[B[i] ^ B[j]] = (1 << i) | (1 << j)
        assert len(self.pairmask) == 2016
        N = defaultdict(list)
        for f in self.fulls:
            for p in self.pairmask: N[f ^ p].append(f)
        self.N = {h: sorted(fs) for h, fs in N.items() if h not in self.Bset}
        self.PV = set(self.pairmask)
        self.cap = None

    def load_cap(self):
        """per-value capacities cap_r(h) under C1 from qhub/hub2_{ori}.json (values with cap >= 1 only)"""
        d = json.load(open(SPRINT/f'qhub/hub2_{self.ori}.json'))
        self.cap = {int(r): {int(h): v['c1'] for h, v in tab.items()} for r, tab in d['cap'].items()}
        return self.cap

    def is_odd(self, v):
        """odd = odd number of ... in this model 'odd' values are the odd-parity signals; the boundary parity
        convention is that of stress.py: boundary masks are odd, XOR of an even number of them is even."""
        return bin(v).count('1') % 2 == 1 if False else None

    def full_vectors(self, f):
        j = self.fidx[f]
        return [T | FULLC(j) for T in self.trip[f]]

    def hub_vectors(self, k, h, R, S):
        vs = [T | HUBC(k) for T in R]
        for f in S:
            vs.append(HUBC(k) | FULLC(self.fidx[f]) | self.pairmask[h ^ f])
        return vs

    def joint_vectors(self, hubs, X=()):
        """hubs: list of (h, R, S); X: list of (k, k') sharing a hub-only label.  Returns the joint family."""
        vs = []
        fullset = sorted({f for _, _, S in hubs for f in S})
        for f in fullset: vs += self.full_vectors(f)
        for k, (h, R, S) in enumerate(hubs): vs += self.hub_vectors(k, h, R, S)
        for k, k2 in X:
            p = hubs[k][0] ^ hubs[k2][0]
            assert p in self.pairmask, 'hubs sharing a label have XOR in PV'
            vs.append(HUBC(k) | HUBC(k2) | self.pairmask[p])
        return vs

    def joint_independent(self, hubs, X=()):
        return independent(self.joint_vectors(hubs, X))

    def label_partners(self, h, f, c):
        """hub values h2 that meet the same full-met label l = f + c as hub h (which meets it through its end
        b = l + h): h2 = l + b2 for b2 in B \\ {b, c}, odd non-boundary, != h"""
        l = f ^ c
        out = []
        for b2 in self.B:
            h2 = l ^ b2
            if h2 == h or h2 in self.Bset or b2 == c: continue
            out.append((h2, b2))
        return out
