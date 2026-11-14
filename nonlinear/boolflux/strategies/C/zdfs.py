"""Exhaustive search for a k-member GF(4)-norm last layer over a FIXED E (default: the AD5 file's
10 level-1 + 5 inversion ANDs), in the case dim Z = r with pi-rank exactly r
(NOTES.md section 9).

Members m = (z, zeta), z = zeta*Y in F*, zeta in mu_5 (1275 of them for a given gamma).
pi(m) = member table mod (E + T). A set S works iff T is in span(S) + E; with |S| = k and
rank pi(S) <= k - 8 the kernel combinations have dimension >= 8. Case handled here:
rank pi(S) = dim Z = r where Z = span{z_m}; then pi restricted to S is a linear function of z
(f_11, which is the z-coordinate, vanishes on E and T). For every r-dim Z we run a DFS over the
2^r - 1 points of Z choosing at most one member per point (or none) so that the chosen pi values
extend linearly; every assignment with >= k used points is checked exactly.

usage: python3 zdfs.py --r 4 --k 12 [--gamma 17] [--efile AD5] [--out FILE]
"""
from __future__ import annotations

import argparse
import itertools
import json
import time

import gf
import qmc
import wsat
from exp_stage3 import tables_of
from fam_check import gp
from kj_search import Model

AD5 = '/home/joebachir20/xcr-boolflux/nonlinear/nist/aes-sbox/aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt'
MU5 = [gp(51 * i) for i in range(5)]
CUBE_ROOT = {}
for e in range(0, 255, 17):
    s0 = gp(e); CUBE_ROOT.setdefault(gf.power(s0, 3), s0)


def subspaces(r, n=8):
    """all r-dim subspaces of F_2^n as lists of basis ints (RREF)"""
    for piv in itertools.combinations(range(n), r):
        # rows: bit positions (from msb index 0); free positions are non-pivot columns after pivot
        free = [[c for c in range(n) if c > p and c not in piv] for p in piv]
        nfree = sum(len(f) for f in free)
        for bits in range(1 << nfree):
            rows = []; k = 0
            for p, fr in zip(piv, free):
                v = 1 << (n - 1 - p)
                for c in fr:
                    if (bits >> k) & 1: v |= 1 << (n - 1 - c)
                    k += 1
                rows.append(v)
            yield rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--r', type=int, default=4)
    ap.add_argument('--k', type=int, default=12)
    ap.add_argument('--gamma', default='17')
    ap.add_argument('--efile', default=AD5)
    ap.add_argument('--inv', default=AD5)
    ap.add_argument('--out', default=None)
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--zbasis', default=None, help='comma list of z ints: test only this Z')
    a = ap.parse_args()
    t0 = time.time()
    M = Model(gp(int(a.gamma)) if a.gamma != 'none' else None, 'hard')
    l1, _ = tables_of(a.efile)
    _, inv = tables_of(a.inv)
    E = [gf.ONES] + gf.X + l1 + inv
    En = qmc.Normal(E)
    ET = qmc.Normal(E + M.T)
    Tn = [En.nf(t) for t in M.T]
    pi = {}; red = {}
    for z in range(1, 256):
        for zeta in MU5:
            s = CUBE_ROOT[zeta]
            Y = gf.mul(gf.INV[zeta], z); A = gf.mul(Y, gf.INV[s])
            tab = wsat.member_table(M, A, s)
            pi[(z, zeta)] = ET.nf(tab); red[(z, zeta)] = En.nf(tab)
    print(json.dumps({'event': 'members', 'n': len(pi), 'dimE': En.dim(),
                      'secs': round(time.time() - t0, 1)}), flush=True)
    need = a.k
    from collections import Counter
    maxmult = max(max(Counter(pi[(z, zt)] for zt in MU5).values()) for z in range(1, 256))
    print(json.dumps({'event': 'maxmult', 'value': maxmult}), flush=True)
    npts = (1 << a.r) - 1
    nZ = 0; leaves = 0; hits = []

    def check(S):
        sp = gf.Span([red[m] for m in S])
        return all(sp.contains(t) for t in Tn)

    zlist = subspaces(a.r) if not a.zbasis else [[int(v) for v in a.zbasis.split(',')]]
    for Zb in zlist:
        nZ += 1
        if a.limit and nZ > a.limit: break
        # points of Z indexed by coordinate c in 1..npts
        zval = [0] * (npts + 1)
        for c in range(1, npts + 1):
            v = 0
            for i in range(a.r):
                if (c >> i) & 1: v ^= Zb[i]
            zval[c] = v
        cand = [[]] + [[(zeta, pi[(zval[c], zeta)]) for zeta in MU5] for c in range(1, npts + 1)]
        mm = [0] + [max(Counter(p for _, p in cand[c]).values()) for c in range(1, npts + 1)]
        suf = [0] * (npts + 2)
        for c in range(npts, 0, -1): suf[c] = suf[c + 1] + mm[c]
        # DFS over points in order; partial linear map: basis list of (coord, value)
        best_used = [0]

        def dfs(c, basis_c, basis_v, used, unused):
            nonlocal leaves
            if len(used) + suf[c] < need: return
            if c > npts:
                leaves += 1
                if len(used) >= need:
                    S = [(zval[cc], zt) for cc, zt in used]
                    if check(S):
                        hits.append({'Z': Zb, 'S': S})
                        print(json.dumps({'event': 'HIT', 'Z': Zb, 'S': S}), flush=True)
                return
            # is c in span(basis_c)?  reduce
            v = c; val = 0
            for bc, bv in sorted(zip(basis_c, basis_v), reverse=True):
                if v & (1 << (bc.bit_length() - 1)):
                    v ^= bc; val ^= bv
            if v == 0:
                ok = [zt for zt, p in cand[c] if p == val]
                if ok:
                    dfs(c + 1, basis_c, basis_v, used + [(c, zt) for zt in ok], unused)
                else:
                    dfs(c + 1, basis_c, basis_v, used, unused + 1)
            else:
                # new direction: reduced coordinate v (keep basis in echelon form by leading bit)
                done = set()
                for zt, p in cand[c]:
                    if p in done: continue
                    done.add(p)
                    same = [z2 for z2, p2 in cand[c] if p2 == p]
                    dfs(c + 1, basis_c + [v], basis_v + [p ^ val], used + [(c, z2) for z2 in same], unused)
                dfs(c + 1, basis_c, basis_v, used, unused + 1)

        dfs(1, [], [], [], 0)
        if nZ % 5000 == 0:
            print(json.dumps({'event': 'tick', 'Z': nZ, 'leaves': leaves, 'hits': len(hits),
                              'secs': round(time.time() - t0, 1)}), flush=True)
    out = {'event': 'done', 'r': a.r, 'k': a.k, 'gamma': a.gamma, 'Zs': nZ, 'leaves': leaves,
           'hits': len(hits), 'secs': round(time.time() - t0, 1)}
    print(json.dumps(out), flush=True)
    if a.out: open(a.out, 'w').write(json.dumps({**out, 'hit_list': hits}))


if __name__ == '__main__':
    main()
