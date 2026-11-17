#!/usr/bin/env python3
"""Boyar-Peralta SLP heuristic (cancellation allowed, exact distances) re-synthesis of one linear region.

Region / leaves / targets as in slp.py (trb_impl regions, or layer:K).  Leaves are treated as independent
(dimension m = #leaves, exact distance table over GF(2)^m by BFS, m <= 22).  Each step adds the sum of two
base elements minimising the summed target distance; ties broken by the BP norm rule (max sum of squared
distances) with probability --p-norm, else at random (RNBP); a target at distance 1 is added at once.
Constants: XNOR on the target's last gate, NOT when the linear part is a leaf.  Gate depth is not
constrained during the search; results are kept only if they meet --cap (GD) and lower G (or GD at equal G).

  bp.py --archive DIR --id ID | --file F --cap D --region top|bottom|mid|layer:K --runs N --seed S [--out F]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE))
from boolflux.hub.common import aesfn, core, metrics  # noqa: E402
import slp  # noqa: E402


def dist_table(S, m):
    d = np.full(1 << m, 127, dtype=np.int8); d[0] = 0
    frontier = np.array([0], dtype=np.int64); Sv = np.array(S, dtype=np.int64); lay = 0
    while frontier.size:
        lay += 1
        nb = (frontier[:, None] ^ Sv[None, :]).ravel()
        nb = np.unique(nb); nb = nb[d[nb] == 127]
        d[nb] = lay; frontier = nb
    return d


def bp_run(m, tl, rng, p_norm=0.5, max_steps=200):
    """One randomised BP run over GF(2)^m: the gate list (pairs of base indices), None past max_steps.
    Same gates and same rng draws as bp_run_ref: the distance table
    is updated per new base element c by d'(x) = min(d(x), 1 + d(x ^ c)) (exact: a shortest sum uses c at
    most once) instead of a BFS per step; the pair scan is one numpy expression; the two rng.random() per
    candidate of bp_run_ref (their values never decide anything) are drawn as one getrandbits(128 n)
    (CPython: random() takes two 32-bit words, getrandbits(k) ceil(k / 32) words, in the same order)."""
    S = [1 << i for i in range(m)]; inS = set(S)
    gates = []
    T = list(tl)
    idx_all = np.arange(1 << m, dtype=np.int64)
    d = dist_table(S, m).astype(np.int64)
    while True:
        rest = [t for t in T if t not in inS]
        if not rest: return gates
        if len(gates) > max_steps: return None
        quick = [t for t in rest if d[t] == 2]
        if quick:
            t = rng.choice(quick)
            idx = {v: i for i, v in enumerate(S)}
            pr = None
            for i, v in enumerate(S):
                w = t ^ v
                if w in idx and idx[w] != i: pr = (min(i, idx[w]), max(i, idx[w])); break
            S.append(t); inS.add(t); gates.append(pr)
            d = np.minimum(d, d[idx_all ^ t] + 1); continue
        n = len(S)
        D0 = np.array([int(d[t]) - 1 for t in rest], dtype=np.int64)
        Tr = np.array(rest, dtype=np.int64)
        Sa = np.array(S, dtype=np.int64)
        ii, jj = np.triu_indices(n, 1)
        C = Sa[ii] ^ Sa[jj]
        keep = ~np.isin(C, Sa)
        ii, jj, C = ii[keep], jj[keep], C[keep]
        if C.size == 0: return None
        dn = np.minimum(D0[None, :], d[Tr[None, :] ^ C[:, None]])
        s1 = dn.sum(axis=1); s2 = -(dn * dn).sum(axis=1)
        rng.getrandbits(128 * int(C.size))
        cs = np.flatnonzero(s1 == s1.min())
        if rng.random() < p_norm:
            m2 = s2[cs].min(); cs = cs[s2[cs] == m2]
        x = int(cs[rng.choice(range(len(cs)))])
        c = int(C[x])
        S.append(c); inS.add(c); gates.append((int(ii[x]), int(jj[x])))
        d = np.minimum(d, d[idx_all ^ c] + 1)


def bp_run_ref(m, tl, rng, p_norm=0.5, max_steps=200):
    """The BP run before 2026-11-17 (BFS distance table per step, Python pair loop); bp_run gives the same
    gates and leaves rng in the same state (tests/test_conjpull.py)."""
    S = [1 << i for i in range(m)]; inS = set(S)
    gates = []
    T = list(tl)
    while True:
        rest = [t for t in T if t not in inS]
        if not rest: return gates
        if len(gates) > max_steps: return None
        d = dist_table(S, m)
        # immediate: target = sum of two base elements
        quick = []
        for t in rest:
            if d[t] == 2: quick.append(t)
        if quick:
            t = rng.choice(quick)
            idx = {v: i for i, v in enumerate(S)}
            pr = None
            for i, v in enumerate(S):
                w = t ^ v
                if w in idx and idx[w] != i: pr = (min(i, idx[w]), max(i, idx[w])); break
            S.append(t); inS.add(t); gates.append(pr); continue
        best = None; cands = []
        n = len(S)
        D0 = np.array([int(d[t]) - 1 for t in rest])
        Tr = np.array(rest, dtype=np.int64)
        for i in range(n):
            for j in range(i + 1, n):
                c = S[i] ^ S[j]
                if c in inS: continue
                dn = np.minimum(D0, d[Tr ^ c].astype(np.int64))  # using c: 1 + (d(t^c)-1)
                s1 = int(dn.sum()); s2 = -int((dn * dn).sum())
                key = (s1, s2) if rng.random() < p_norm else (s1,)
                cands.append((s1, s2, rng.random(), i, j, c))
        if not cands: return None
        mn = min(x[0] for x in cands)
        cs = [x for x in cands if x[0] == mn]
        if rng.random() < p_norm:
            m2 = min(x[1] for x in cs); cs = [x for x in cs if x[1] == m2]
        x = rng.choice(cs)
        S.append(x[5]); inS.add(x[5]); gates.append((x[3], x[4]))


def optimise(c, D, region, rng, runs, p_norm=0.5, log=print, region_seed=None, fallback=False):
    """Best of `runs` BP re-syntheses of the region: fewest G (then GD) among those with GD <= D and A, AD
    not above c's and G below c's.  fallback: if no run meets GD <= D, the best run regardless of GD
    (info['fallback'] True).  The runs and rng draws do not depend on D or fallback."""
    rd = slp.region_data(c, D, region, random.Random(region_seed if region_seed is not None else rng.random()))
    R, leaves, form, tg = rd['R'], rd['leaves'], rd['form'], rd['tg']
    m = len(leaves)
    if len(R) < 2 or not tg or m > 22: return None, {'skip': 'size', 'm': m, 'R': len(R)}
    nx = sum(1 for s in R if c.gates[s - c.n][0] != slp.NOT)
    lin = {}
    for t in tg: lin.setdefault(form[t] >> 1, []).append(t)
    tl = [f for f in lin if bin(f).count('1') >= 2]
    m0 = metrics(c)
    info = {'region': region, 'R': len(R), 'xor_gates': nx, 'leaves': m, 'xor_targets': len(tl), 'runs': []}
    best = None; bm = m0; anyb = None; am = m0
    for r in range(runs):
        gates = bp_run(m, tl, rng, p_norm)
        if gates is None: continue
        vec = [1 << i for i in range(m)]
        for p, q in gates: vec.append(vec[p] ^ vec[q])
        tb = {}
        for f, ts in lin.items():
            s = vec.index(f) if f in vec else None
            for t in ts: tb[t] = (s, form[t] & 1)
        nc = slp.assemble(c, rd, gates, tb)
        if tuple(nc.value_table()) != aesfn.table():
            info['error'] = 'wrong'; continue
        mm = metrics(nc)
        info['runs'].append((len(gates), mm[2], mm[3]))
        if mm[3] <= D and mm[0] <= m0[0] and mm[1] <= m0[1] and (mm[2] < bm[2] or (mm[2] == bm[2] and mm[3] < bm[3])):
            best = nc; bm = mm
        if fallback and mm[0] <= m0[0] and mm[1] <= m0[1] and (mm[2] < am[2] or (mm[2] == am[2] and mm[3] < am[3])):
            anyb = nc; am = mm
    if best is None and fallback and anyb is not None:
        info['fallback'] = True
        return anyb, info
    return best, info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--archive'); ap.add_argument('--id'); ap.add_argument('--file')
    ap.add_argument('--cap', type=int, required=True); ap.add_argument('--region', default='top')
    ap.add_argument('--runs', type=int, default=20); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--p-norm', type=float, default=0.5); ap.add_argument('--out')
    a = ap.parse_args()
    if a.id: c = core.from_kernel((Path(a.archive) / 'archive' / (a.id + '.bfx')).read_text(), a.id)
    else:
        p = Path(a.file); c = core.from_kernel(p.read_text()) if p.suffix == '.bfx' else core.read_ncff(str(p))
    m0 = metrics(c); t0 = time.time()
    nc, info = optimise(c, a.cap, a.region, random.Random(a.seed), a.runs, a.p_norm, region_seed=a.seed)
    rs = info.pop('runs', [])
    info['bp_gates_hist'] = sorted(set(x[0] for x in rs)); info['G_min'] = min((x[1] for x in rs), default=None)
    info['secs'] = round(time.time() - t0, 1)
    print(json.dumps(info))
    if nc is not None:
        print('before', m0, 'after', metrics(nc))
        if a.out: Path(a.out).write_text(core.to_kernel(nc))
    else: print('before', m0, 'no improvement')


if __name__ == '__main__':
    main()
