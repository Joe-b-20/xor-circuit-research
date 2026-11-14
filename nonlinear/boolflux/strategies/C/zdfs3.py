"""Exhaustive k-member last layer over a fixed E, case dim Z = r and rank pi(S) = r + 1
(complements zdfs.py). Then pi(S) lies in R = graph(Theta) + <r0> with r0 in ker f_11. Since
|S| > number of points of Z is needed only if... in general some point carries two members whose
pi differ by r0, OR all members sit on distinct points and r0 appears as a value offset. We
enumerate r0 among (a) differences pi(z,zeta) + pi(z,zeta') at one point and (b) for the
distinct-point case, r0 is the pi of a combination; (b) is covered by trying r0 = pi(m1) + pi(m2) +
pi(m3) + Theta-consistency... -- here we implement (a) only, which is complete whenever some
point of Z carries >= 2 members of S (forced when k > 2^r - 1, e.g. r = 3, k = 12).
With r0 fixed, pi mod r0 must be linear in z; DFS over the 2^r - 1 points as in zdfs.py, taking
every member whose value matches mod r0.

usage: python3 zdfs3.py --r 3 --k 12 [--gamma 17] [--efile F] [--inv F] [--out FILE]
"""
from __future__ import annotations

import argparse
import json
import time
from collections import Counter

import gf
import qmc
import wsat
from exp_stage3 import tables_of
from fam_check import gp
from kj_search import Model
from zdfs import MU5, CUBE_ROOT, AD5, subspaces


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--r', type=int, default=3)
    ap.add_argument('--k', type=int, default=12)
    ap.add_argument('--gamma', default='17')
    ap.add_argument('--efile', default=AD5)
    ap.add_argument('--inv', default=AD5)
    ap.add_argument('--out', default=None)
    ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args()
    t0 = time.time()
    M = Model(gp(int(a.gamma)) if a.gamma != 'none' else None, 'hard')
    l1, _ = tables_of(a.efile); _, inv = tables_of(a.inv)
    E = [gf.ONES] + gf.X + l1 + inv
    En = qmc.Normal(E); ET = qmc.Normal(E + M.T)
    Tn = [En.nf(t) for t in M.T]
    pi = {}; red = {}
    for z in range(1, 256):
        for zeta in MU5:
            s = CUBE_ROOT[zeta]; Y = gf.mul(gf.INV[zeta], z); A = gf.mul(Y, gf.INV[s])
            tab = wsat.member_table(M, A, s)
            pi[(z, zeta)] = ET.nf(tab); red[(z, zeta)] = En.nf(tab)
    print(json.dumps({'event': 'members', 'secs': round(time.time() - t0, 1)}), flush=True)
    npts = (1 << a.r) - 1; need = a.k
    nZ = 0; hits = []; checks = 0
    for Zb in subspaces(a.r):
        nZ += 1
        if a.limit and nZ > a.limit: break
        zval = [0] * (npts + 1)
        for c in range(1, npts + 1):
            v = 0
            for i in range(a.r):
                if (c >> i) & 1: v ^= Zb[i]
            zval[c] = v
        P = [None] + [[(zt, pi[(zval[c], zt)]) for zt in MU5] for c in range(1, npts + 1)]
        r0s = set()
        for c in range(1, npts + 1):
            for i in range(5):
                for j in range(i + 1, 5):
                    d = P[c][i][1] ^ P[c][j][1]
                    if d: r0s.add(d)
        for r0 in r0s:
            Nr = qmc.Normal([r0])
            cand = [None] + [[(zt, Nr.nf(p)) for zt, p in P[c]] for c in range(1, npts + 1)]
            mm = [0] + [max(Counter(p for _, p in cand[c]).values()) for c in range(1, npts + 1)]
            suf = [0] * (npts + 2)
            for c in range(npts, 0, -1): suf[c] = suf[c + 1] + mm[c]
            if suf[1] < need: continue

            def dfs(c, bc, bv, used):
                nonlocal checks
                if len(used) + suf[c] < need: return
                if c > npts:
                    if len(used) >= need:
                        checks += 1
                        S = [(zval[cc], zt) for cc, zt in used]
                        sp = gf.Span([red[m] for m in S])
                        if all(sp.contains(t) for t in Tn):
                            hits.append({'Z': Zb, 'r0': r0, 'S': S})
                            print(json.dumps({'event': 'HIT', 'Z': Zb, 'S': S}), flush=True)
                    return
                v = c; val = 0
                for x, y in sorted(zip(bc, bv), reverse=True):
                    if v & (1 << (x.bit_length() - 1)): v ^= x; val ^= y
                if v == 0:
                    ok = [zt for zt, p in cand[c] if p == val]
                    dfs(c + 1, bc, bv, used + [(c, zt) for zt in ok])
                else:
                    seen = set()
                    for zt, p in cand[c]:
                        if p in seen: continue
                        seen.add(p)
                        same = [z2 for z2, p2 in cand[c] if p2 == p]
                        dfs(c + 1, bc + [v], bv + [p ^ val], used + [(c, z2) for z2 in same])
                    dfs(c + 1, bc, bv, used)

            dfs(1, [], [], [])
        if nZ % 5000 == 0:
            print(json.dumps({'event': 'tick', 'Z': nZ, 'checks': checks, 'hits': len(hits),
                              'secs': round(time.time() - t0, 1)}), flush=True)
    out = {'event': 'done', 'r': a.r, 'k': a.k, 'gamma': a.gamma, 'Zs': nZ, 'checks': checks,
           'hits': len(hits), 'secs': round(time.time() - t0, 1)}
    print(json.dumps(out), flush=True)
    if a.out: open(a.out, 'w').write(json.dumps({**out, 'hit_list': hits}))


if __name__ == '__main__':
    main()
