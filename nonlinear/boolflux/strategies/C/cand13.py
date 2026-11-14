"""9 + 5 + 13 candidates from rich member families.

Over the AD5 E, the DFS of zdfs.py finds, in the A28 subspace Z, a pi-consistent family of up to
19 members (pi-rank 5). Every 13-subset S of such a family with T in span(S) + E_AD5 is a valid
last layer for the AD5 stage 1. Here we re-express each such S over E_min (no level-1 extras) and
ask whether some 9-product stage 1 can carry its junk: U_S = V_N + junk(S) must be covered by 9
rank-2 forms (cover_enum, exact when 9 - dim U_S <= 2). A hit is a 27-AND design.

usage: python3 cand13.py --zbasis 116,250,207,28,145 [--gamma 17] [--hits FILE]
"""
from __future__ import annotations

import argparse
import itertools
import json
import time

import gf
import qmc
import wsat
import cover_enum
from exp_stage3 import tables_of
from fam_check import gp
from kj_search import Model
from zdfs import MU5, CUBE_ROOT, AD5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--zbasis', required=True)
    ap.add_argument('--gamma', default='17')
    ap.add_argument('--efile', default=AD5)
    ap.add_argument('--k', type=int, default=13)
    ap.add_argument('--l', type=int, default=9)
    ap.add_argument('--hits', default=None)
    ap.add_argument('--families', default=None, help='JSONL with HIT lines (S as [z, zeta] lists)')
    a = ap.parse_args()
    t0 = time.time()
    M = Model(gp(int(a.gamma)) if a.gamma != 'none' else None, 'hard')
    l1, inv = tables_of(a.efile)
    E = [gf.ONES] + gf.X + l1 + inv
    En = qmc.Normal(E); ET = qmc.Normal(E + M.T)
    Tn = [En.nf(t) for t in M.T]
    Zb = [int(v) for v in a.zbasis.split(',')]
    r = len(Zb); npts = (1 << r) - 1
    zval = [0] * (npts + 1)
    for c in range(1, npts + 1):
        v = 0
        for i in range(r):
            if (c >> i) & 1: v ^= Zb[i]
        zval[c] = v
    mem = {}
    for c in range(1, npts + 1):
        for zeta in MU5:
            z = zval[c]; s = CUBE_ROOT[zeta]
            Y = gf.mul(gf.INV[zeta], z); A = gf.mul(Y, gf.INV[s])
            tab = wsat.member_table(M, A, s)
            mem[(c, zeta)] = (A, s, tab, ET.nf(tab), En.nf(tab))
    # maximal pi-consistent families: DFS without the size requirement, keep maximal leaves
    fams = []

    def dfs(c, bc, bv, used):
        if c > npts:
            fams.append(list(used)); return
        v = c; val = 0
        for x, y in sorted(zip(bc, bv), reverse=True):
            if v & (1 << (x.bit_length() - 1)): v ^= x; val ^= y
        cand = [(zt, mem[(c, zt)][3]) for zt in MU5]
        if v == 0:
            ok = [zt for zt, p in cand if p == val]
            dfs(c + 1, bc, bv, used + [(c, zt) for zt in ok])
        else:
            seen = set()
            for zt, p in cand:
                if p in seen: continue
                seen.add(p)
                same = [z2 for z2, p2 in cand if p2 == p]
                dfs(c + 1, bc + [v], bv + [p ^ val], used + [(c, z2) for z2 in same])
            dfs(c + 1, bc, bv, used)

    # restrict: only families of size >= k (prune by suffix)
    big = []
    def dfs2(c, bc, bv, used):
        if len(used) + 2 * (npts - c + 1) < a.k: return
        if c > npts:
            big.append(list(used)); return
        v = c; val = 0
        for x, y in sorted(zip(bc, bv), reverse=True):
            if v & (1 << (x.bit_length() - 1)): v ^= x; val ^= y
        cand = [(zt, mem[(c, zt)][3]) for zt in MU5]
        if v == 0:
            ok = [zt for zt, p in cand if p == val]
            if ok: dfs2(c + 1, bc, bv, used + [(c, zt) for zt in ok])
            else: dfs2(c + 1, bc, bv, used)
        else:
            seen = set()
            for zt, p in cand:
                if p in seen: continue
                seen.add(p)
                same = [z2 for z2, p2 in cand if p2 == p]
                dfs2(c + 1, bc + [v], bv + [p ^ val], used + [(c, z2) for z2 in same])
            dfs2(c + 1, bc, bv, used)
    if a.families:
        cidx = {zval[c]: c for c in range(1, npts + 1)}
        for line in open(a.families):
            if 'HIT' not in line: continue
            d = json.loads(line)
            big.append([(cidx[z], zt) for z, zt in d['S']])
    else:
        dfs2(1, [], [], [])
    # keep maximal families only
    sets = sorted({frozenset(u) for u in big}, key=len, reverse=True)
    maxi = []
    for s_ in sets:
        if not any(s_ <= m for m in maxi): maxi.append(s_)
    print(json.dumps({'event': 'families', 'n_leaves': len(big), 'maximal': [len(m) for m in maxi],
                      'secs': round(time.time() - t0, 1)}), flush=True)
    Nf = wsat.n_forms(); qsp = wsat.quad_form_coords(M)
    tested = set(); nval = 0; hits = 0; stats = {}
    for fam in maxi:
        fam = sorted(fam)
        for S in itertools.combinations(fam, a.k):
            if S in tested: continue
            tested.add(S)
            sp = gf.Span([mem[m][4] for m in S])
            if not all(sp.contains(t) for t in Tn): continue
            nval += 1
            tabs = [mem[m][2] for m in S]
            ok, res, kj, _ = wsat.residuals(M, tabs)
            if not ok:
                stats['g0_fail'] = stats.get('g0_fail', 0) + 1; continue
            rho = wsat.to_forms(qsp, res); kap = wsat.to_forms(qsp, kj)
            U = []; spu = gf.Span()
            for v in Nf + rho:
                if spu.add(v): U.append(v)
            key = ('d', len(U), 'kernel', len(kap))
            stats[str(key)] = stats.get(str(key), 0) + 1
            if kap or a.l - len(U) > 2 or a.l < len(U): continue
            info, found = cover_enum.run(U, a.l)
            if found:
                hits += 1
                rec = {'S': [[mem[m][0], mem[m][1]] for m in S], 'd': len(U), 'gamma': a.gamma}
                print(json.dumps({'event': 'COVER_HIT', **rec}), flush=True)
                if a.hits:
                    with open(a.hits, 'a') as fh: fh.write(json.dumps(rec) + '\n')
            if nval % 200 == 0:
                print(json.dumps({'event': 'tick', 'valid': nval, 'stats': stats, 'hits': hits,
                                  'secs': round(time.time() - t0, 1)}), flush=True)
    print(json.dumps({'event': 'done', 'valid': nval, 'stats': stats, 'hits': hits,
                      'secs': round(time.time() - t0, 1)}), flush=True)


if __name__ == '__main__':
    main()
