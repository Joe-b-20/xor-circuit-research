#!/usr/bin/env python3
"""Exact SLP (SAT) re-synthesis of one linear region of a circuit, with gate-depth deadlines.

Region R = linear gates (XOR/XNOR/NOT) of one AND layer (trb_impl.pick_region: 'top' = AND level 0,
'bottom' = last AND level, 'mid' = a random middle level, or --layer k).  Leaves = operands of R's
gates outside R (arrival levels unchanged, R is convex), targets = R's gates read outside R or
outputs; every target is an affine form over the leaves (syntactic: the leaves are treated as
independent).  SAT question: are there <= k XOR gates computing every target's linear part, every
target meeting its required level for gate-depth cap D (from the unchanged consumers)?  Constants
are put on the last gate of each target (XNOR), or a NOT when the linear part is a leaf.
k runs downward from (current region XOR count - 1) while SAT; UNSAT at k means [C, for this region,
these leaves as independent variables, these targets and deadlines] no SLP with k gates exists.

Result spliced into the circuit with the trb assembly, checked on all 256 inputs; written if
G decreases (or GD decreases at equal G).

  slp.py --archive DIR --id ID | --file F  --cap D [--region top|bottom|mid|layer:K] [--budget N]
         [--out OUT.bfx] [--timeout S]
"""
from __future__ import annotations

import argparse
import itertools
import json
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux.hub.common import aesfn, core, metrics  # noqa: E402
from boolflux.hub import trb_impl as T  # noqa: E402
from pysat.solvers import Solver  # noqa: E402
from pysat.card import CardEnc, EncType  # noqa: E402

XOR, XNOR, NOT, AND = 6, 9, 3, 8


def region_data(c, D, region, rng):
    n = c.n
    lv, al, req, fo = T.struct(c, D)
    lin = [s for s in range(n, n + len(c.gates)) if c.gates[s - n][0] != AND]
    if region.startswith('layer:'):
        k = int(region.split(':')[1]); R = {s for s in lin if al[s] == k}
    else:
        R = T.pick_region(c, region, rng, lv, al, fo)
    outset = set(c.outputs)
    leaves = sorted({x for s in R for x in c.gates[s - n][1:] if x not in R})
    li = {x: i for i, x in enumerate(leaves)}
    form = {}
    for s in sorted(R):
        op, a, b = c.gates[s - n]
        fa = form[a] if a in R else (1 << (1 + li[a]))
        fb = form[b] if b in R else (1 << (1 + li[b]))
        if op == XOR: f = fa ^ fb
        elif op == XNOR: f = fa ^ fb ^ 1
        elif op == NOT: f = fa ^ 1
        else: raise ValueError
        form[s] = f
    tg = [s for s in sorted(R) if s in outset or any(y not in R for y in fo[s])]
    return dict(R=R, leaves=leaves, form=form, tg=tg, lv=lv, req=req, fo=fo)


def solve(m, arr, targets_lin, deadlines, k, timeout, budget=None):
    """m leaves (unit vectors, arrival arr[i]), targets = list of linear forms (int bitmask over leaves,
    bit i = leaf i), deadlines per target.  Returns list of gates (p, q) over signal ids (leaves 0..m-1,
    gate j = m + j) and target -> signal map, or None (UNSAT), or 'unknown'."""
    top = [0]
    def nv():
        top[0] += 1; return top[0]
    cl = []
    maxlev = max(deadlines)
    S = m + k
    # vectors
    V = {}
    for j in range(k):
        for d in range(m): V[(m + j, d)] = nv()
    def vlit(s, d):     # returns ('c', bit) for leaves or ('v', var)
        if s < m: return ('c', 1 if s == d else 0)
        return ('v', V[(s, d)])
    # levels: le[s][t] = level(s) <= t, t in 0..maxlev
    LE = {}
    for j in range(k):
        for t in range(maxlev + 1): LE[(m + j, t)] = nv()
        for t in range(maxlev): cl.append([-LE[(m + j, t)], LE[(m + j, t + 1)]])
        cl.append([-LE[(m + j, 0)]])
    def le(s, t):
        if s < m: return True if arr[s] <= t else False
        if t < 0: return False
        if t > maxlev: return True
        return LE[(s, t)]
    P = {}
    for j in range(k):
        g = m + j
        prs = []
        for p in range(g):
            for q in range(p + 1, g):
                x = nv(); P[(j, p, q)] = x; prs.append(x)
                for d in range(m):
                    a = vlit(p, d); b = vlit(q, d); o = V[(g, d)]
                    if a[0] == 'c' and b[0] == 'c':
                        cl.append([-x, o if (a[1] ^ b[1]) else -o])
                    elif a[0] == 'c' or b[0] == 'c':
                        cst, var = (a[1], b[1]) if a[0] == 'c' else (b[1], a[1])
                        if cst: cl += [[-x, o, var], [-x, -o, -var]]
                        else: cl += [[-x, o, -var], [-x, -o, var]]
                    else:
                        A_, B_ = a[1], b[1]
                        cl += [[-x, -o, A_, B_], [-x, -o, -A_, -B_], [-x, o, -A_, B_], [-x, o, A_, -B_]]
                # level: le(g, t) -> le(p, t-1) and le(q, t-1)
                for t in range(maxlev + 1):
                    for s in (p, q):
                        r = le(s, t - 1)
                        if r is True: continue
                        if r is False: cl.append([-x, -LE[(g, t)]])
                        else: cl.append([-x, -LE[(g, t)], r])
        enc = CardEnc.equals(lits=prs, bound=1, top_id=top[0], encoding=EncType.seqcounter)
        top[0] = max(top[0], enc.nv); cl += enc.clauses
    # targets
    TOPT = {m + j: [] for j in range(k)}
    for ti, (f, dl) in enumerate(zip(targets_lin, deadlines)):
        opts = []
        for j in range(k):
            g = m + j; x = nv(); opts.append(x); TOPT[g].append(x)
            for d in range(m):
                cl.append([-x, V[(g, d)] if (f >> d) & 1 else -V[(g, d)]])
            r = le(g, dl)
            cl.append([-x, r])
        cl.append(opts)
    # every gate is used (by a target or a later gate): sound for minimum k (a useless gate can be dropped)
    users = {g: [] for g in range(m, S)}
    for (j, p, q), x in P.items():
        for s in (p, q):
            if s >= m: users[s].append(x)
    for g in range(m, S): users[g] += TOPT[g]
    for g in range(m, S): cl.append(users[g])
    # colex order of consecutive independent gates (swap symmetry): idx(j) < idx(j+1) unless j+1 reads j
    def pidx(p, q): return q * (q - 1) // 2 + p
    Q = {}
    for j in range(k):
        g = m + j; npr = g * (g - 1) // 2
        for i in range(1, npr): Q[(j, i)] = nv()
        for i in range(1, npr - 1): cl.append([-Q[(j, i + 1)], Q[(j, i)]])
        for p in range(g):
            for q in range(p + 1, g):
                x = P[(j, p, q)]; i = pidx(p, q)
                if i >= 1: cl.append([-x, Q[(j, i)]])
                if (j, i + 1) in Q: cl.append([-x, -Q[(j, i + 1)]])
    for j in range(k - 1):
        g = m + j
        for p in range(g + 1):
            for q in range(p + 1, g + 1):
                if q == g: continue
                i = pidx(p, q)
                if (j, i) in Q: cl.append([-P[(j + 1, p, q)], -Q[(j, i)]])
    with Solver(name='cadical195', bootstrap_with=cl) as sv:
        t0 = time.time()
        if budget: sv.conf_budget(budget); ok = sv.solve_limited()
        else: ok = sv.solve()
        if ok is None: return 'unknown'
        if not ok: return None
        mod = set(l for l in sv.get_model() if l > 0)
    gates = []
    for j in range(k):
        for (jj, p, q), x in P.items():
            if jj == j and x in mod: gates.append((p, q)); break
    vec = [1 << i for i in range(m)]
    for p, q in gates: vec.append(vec[p] ^ vec[q])
    tmap = []
    for f in targets_lin:
        s = vec.index(f); tmap.append(s)
    return gates, tmap


def assemble(c, rd, gates, tmap_by_target):
    """build the circuit: original gates minus R, the SLP gates, constants via XNOR twin / NOT."""
    n = c.n; R = rd['R']; leaves = rd['leaves']; m = len(leaves)
    out_gates = []; built = {}; mp = {i: i for i in range(n)}; tmap = {}
    sys.setrecursionlimit(20000)

    def bsig(x):
        if x in built: return built[x]
        if x < m: built[x] = mp_get(leaves[x]); return built[x]
        p, q = gates[x - m]
        a = bsig(p); b = bsig(q)
        out_gates.append((XOR, a, b)); built[x] = n + len(out_gates) - 1
        return built[x]

    def mp_get(s):
        if s < n: return s
        if s in R:
            if s not in tmap:
                x, cst = tmap_by_target[s]
                g = bsig(x)
                if cst:
                    if x >= m:
                        p, q = gates[x - m]
                        out_gates.append((XNOR, bsig(p), bsig(q))); g = n + len(out_gates) - 1
                    else:
                        out_gates.append((NOT, g, g)); g = n + len(out_gates) - 1
                tmap[s] = g
            return tmap[s]
        if s not in mp:
            op, a, b = c.gates[s - n]
            aa = mp_get(a); bb = mp_get(b)
            out_gates.append((op, aa, bb)); mp[s] = n + len(out_gates) - 1
        return mp[s]
    outs = [mp_get(o) for o in c.outputs]
    return core.Circuit(n, c.m, out_gates, outs, c.name, c.in_names, c.out_names).live()


def optimise(c, D, region, rng, timeout=60, budget=None, log=print, slack=0):
    rd = region_data(c, D, region, rng)
    R, leaves, form, tg = rd['R'], rd['leaves'], rd['form'], rd['tg']
    m = len(leaves)
    if len(R) < 2 or not tg: return None, {'skip': 'small'}
    nx = sum(1 for s in R if c.gates[s - c.n][0] != NOT)
    lin = {}
    for t in tg:
        f = form[t] >> 1
        lin.setdefault(f, []).append(t)
    tl = [f for f in lin if bin(f).count('1') >= 2]
    if not tl: return None, {'skip': 'no xor targets'}
    arr = [rd['lv'][x] for x in leaves]
    dls = [min(rd['req'][t] for t in lin[f]) for f in tl]
    # constant-on-leaf targets need a NOT; xor targets with const: free on its own gate
    info = {'region': region, 'R': len(R), 'xor_gates': nx, 'leaves': m, 'targets': len(tg), 'xor_targets': len(tl),
            'tries': []}
    best = None
    k = nx - 1 + slack
    while k >= len(tl):
        t0 = time.time()
        r = solve(m, arr, tl, dls, k, timeout, budget)
        dt = round(time.time() - t0, 2)
        info['tries'].append((k, 'unknown' if r == 'unknown' else ('unsat' if r is None else 'sat'), dt))
        log('  k=%d %s %.1fs' % (k, info['tries'][-1][1], dt))
        if r is None or r == 'unknown': break
        gates, tmap = r
        tb = {}
        for f, s in zip(tl, tmap):
            for t in lin[f]: tb[t] = (s, form[t] & 1)
        for f, ts in lin.items():
            if f in tl: continue
            i = (f).bit_length() - 1
            for t in ts: tb[t] = (i, form[t] & 1)
        nc = assemble(c, rd, gates, tb)
        if tuple(nc.value_table()) != aesfn.table():
            info['error'] = 'wrong'; break
        best = nc
        k = len(set(gates)) - 1
        k = min(k, len(gates) - 1)
    return best, info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--archive'); ap.add_argument('--id'); ap.add_argument('--file')
    ap.add_argument('--cap', type=int, required=True); ap.add_argument('--region', default='top')
    ap.add_argument('--budget', type=int, default=None); ap.add_argument('--timeout', type=float, default=60)
    ap.add_argument('--out'); ap.add_argument('--seed', type=int, default=1); ap.add_argument('--slack', type=int, default=0)
    a = ap.parse_args()
    if a.id: c = core.from_kernel((Path(a.archive) / 'archive' / (a.id + '.bfx')).read_text(), a.id)
    else:
        p = Path(a.file); c = core.from_kernel(p.read_text()) if p.suffix == '.bfx' else core.read_ncff(str(p))
    m0 = metrics(c)
    nc, info = optimise(c, a.cap, a.region, random.Random(a.seed), a.timeout, a.budget, slack=a.slack)
    print(json.dumps(info))
    if nc is not None:
        m1 = metrics(nc); print('before', m0, 'after', m1)
        if a.out and (m1[2] < m0[2] or (m1[2] == m0[2] and m1[3] < m0[3])):
            Path(a.out).write_text(core.to_kernel(nc)); print('written', a.out)
    else:
        print('before', m0, 'no improvement')


if __name__ == '__main__':
    main()
