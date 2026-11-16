#!/usr/bin/env python3
"""Operator `bottom` (M3): keep a circuit's front, re-plan its last AND level as shared rank-1 products
(strategies/P7 bopt.py / bbuild.py / overnight.sh generalised), build, then A-capped kernel polish.

    python3 nonlinear/boolflux/campaigns/targets/ops/bottom.py --in START --target Txx --seed S --seconds T
        --out DIR [--cpus 1] [--cut K] [--cap D] [--amax A] [--iters 30000] [--pw 0,3] [--T0 2.0]
        [--polish-seconds 300] [--polish-cap-a build|target] [--repair-keep 1]

Model (P7 NOTES s.2).  Cut K (default: the start's AND depth): the products at AND level K are the
bottom; the front is everything feeding their non-linear operands.  Four base Y-forms (independent
operands of degree > 1 of the level-K products, earliest gate level first) span the Y-space; every
output is y_j = c_j + sum_i Y_i u_ij(x) (u_ij linear), a 4 x 8 tensor B_j.  A plan = a set of rank-1
products AND(Y_alpha, w) and per output a subset summing to B_j with an exact Kraft check at the GD cap D
(product level = Y level + 1 (+1 / +2 for 2- / 3,4-sums of base Ys)), at most amax - front ANDs products.
Simulated annealing over per-output decompositions (bopt), build (bbuild: front cone + Y-sums +
Boyar-Peralta x-forms + products + shared pairs + Huffman output trees), then kernel polish with caps
A <= build A (default; keeps the A frontier), AD <= ref AD, GD <= D.
Not applicable (status "not-applicable", exit 0) when there are not four independent base Y-forms,
an output is not of the form above (linear junk), or some output has no Kraft-feasible decomposition at D.
"""
import argparse
import json
import math
import random
import sys
import time
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE / 'm3lib'))
import m3common as MC                                 # noqa: E402
from m3common import core, verify, metrics, clean, load, cid   # noqa: E402
import bopt as BO                                     # noqa: E402
import bsel                                           # noqa: E402
import bbuild as BU                                   # noqa: E402
L = BO.L


def setup(c, cut, cap, amax):
    """model of the start's bottom; returns (Model, B, opts, info) or (None, reason)"""
    BO.CUT = cut
    n = c.n
    T, lg, la, base = BO.base_front(c)
    if len(base) < 4:
        return None, 'only %d independent base Y-forms at AND level %d' % (len(base), cut)
    Ys = [b[1] for b in base]; Lb = [b[0] for b in base]
    try:
        U, C = bsel.decompose_outputs(c, T, Ys)
    except AssertionError as e:
        return None, 'outputs not in span(Y_i x_l, Y_i, x_l, 1): %s' % e
    junk = [j for j, (cst, v, yt) in enumerate(C) if v or yt]
    if junk:
        return None, 'outputs %s carry linear / Y-form junk terms' % junk
    B = [tuple(U[j][i] for i in range(4)) for j in range(8)]
    nfront = sum(1 for j, g in enumerate(c.gates) if g[0] in core.NONLINEAR_OPS and la[n + j] < cut)
    nbottom = sum(1 for j, g in enumerate(c.gates) if g[0] in core.NONLINEAR_OPS and la[n + j] >= cut)
    free = BO.front_free_forms(c, T, la)
    M = BO.Model(B, Lb, cap, free, amax - nfront)
    opts = []
    for j in range(8):
        oj = [S for A in BO.bases_of(BO.colspace(B[j])) for S in [BO.decompose(B[j], A)] if M.kraft(S)]
        if not oj:
            return None, 'output %d has no Kraft-feasible 4-product decomposition at GD %d (base Y levels %s)' % (j, cap, Lb)
        opts.append(oj)
    own = own_choice(c, cut, Ys)
    if own is not None and not all(BO.sum_t(S) == B[j] for j, S in enumerate(own)): own = None
    return (M, B, opts, {'Lb': Lb, 'nfront': nfront, 'nbottom': nbottom, 'C': C, 'own': own,
                         'own_kraft': [M.kraft(S) for S in own] if own else None}), None


def own_choice(c, cut, Ys):
    """the start circuit's own bottom as a plan choice (P7 bopt --calib), or None if it does not fit the model"""
    from boolflux import skeleton
    T, lg, la = L.sim(c); n = c.n
    sk = skeleton.extract(c)
    andsig = [n + j for j, g in enumerate(c.gates) if g[0] in core.NONLINEAR_OPS]
    choice = [[] for _ in range(8)]
    for k, s in enumerate(andsig):
        if la[s] != cut: continue
        op, x, y = c.gates[s - n]
        if L.deg(T[x]) > 1: ty, tx = T[x], T[y]
        else: ty, tx = T[y], T[x]
        if L.deg(tx) > 1: return None
        if (ty & 1) or (tx & 1): return None          # complemented operands: linear junk, not in the model
        sol = bsel.gauss_solve(Ys, ty)
        w = BO.mask_of(tx)
        if sol is None or w is None or w == 0: return None
        p = (sum(1 << i for i in sol), w)
        for j, F in enumerate(sk['outputs']):
            if (F >> (1 + n + k)) & 1: choice[j].append(p)
    return choice


def anneal(M, B, opts, rng, iters, T0, deadline, init=None):
    """bopt.py main loop (P7), unchanged except the deadline and an optional initial choice"""
    choice = [list(S) for S in init] if init else [rng.choice(o) for o in opts]
    cur = M.cost(choice); best = (cur, [list(S) for S in choice])
    for it in range(iters):
        if (it & 255) == 0 and time.time() > deadline: break
        Tt = T0 * (1 - it / iters) + 0.05
        j = rng.randrange(8)
        others = Counter(p for k, S in enumerate(choice) if k != j for p in S)
        pool = list(others)
        cand = []
        if rng.random() < 0.3 or not pool:
            cand.append(rng.choice(opts[j]))
        else:
            ksz = rng.choice([1, 1, 2, 2, 3])
            R = rng.sample(pool, min(ksz, len(pool)))
            Mx = B[j]
            for p in R: Mx = BO.tsub(Mx, p)
            if not any(Mx):
                cand.append(list(R))
            else:
                bs = BO.bases_of(BO.colspace(Mx))
                if len(bs) > 60: bs = rng.sample(bs, 60)
                for A in bs:
                    S = list(R) + BO.decompose(Mx, A)
                    if len(set(S)) == len(S) and M.kraft(S): cand.append(S)
        if not cand: continue
        old = choice[j]; bestc = None
        for S in cand:
            choice[j] = S
            cc = M.cost(choice)
            if bestc is None or cc < bestc[0]: bestc = (cc, S)
        cc, S = bestc
        if cc[0] <= cur[0] or rng.random() < math.exp(-(cc[0] - cur[0]) / Tt):
            choice[j] = S; cur = cc
            if cc < best[0]: best = (cc, [list(x) for x in choice])
        else:
            choice[j] = old
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', required=True); ap.add_argument('--target', required=True)
    ap.add_argument('--seed', type=int, default=1); ap.add_argument('--seconds', type=float, required=True)
    ap.add_argument('--out', required=True); ap.add_argument('--cpus', type=int, default=1)
    ap.add_argument('--cut', type=int); ap.add_argument('--cap', type=int); ap.add_argument('--amax', type=int)
    ap.add_argument('--iters', type=int, default=30000); ap.add_argument('--pw', default='0,3')
    ap.add_argument('--T0', type=float, default=2.0); ap.add_argument('--polish-seconds', type=float, default=300)
    ap.add_argument('--polish-cap-a', choices=['build', 'target'], default='build')
    ap.add_argument('--repair-keep', type=int, default=1)
    ap.add_argument('--shard', default=None, help='set by --cpus for worker processes (unused here)')
    ap.add_argument('--plan-seeds', default='', help='comma list of exact SA seeds to use first (P7 bopt --seed: same plan)')
    ap.add_argument('--init', choices=['random', 'own', 'mix'], default='mix',
                    help="SA start: random per-output bases (P7), the start circuit's own bottom, or alternate (mix)")
    a = ap.parse_args()
    t0 = time.time(); deadline = t0 + a.seconds
    rng = random.Random(a.seed)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    tl = MC.limits(a.target)
    c0 = load(a.inp); m0 = metrics(c0)
    cut = a.cut or m0[1]
    cap = a.cap or min(tl['GD'], m0[3])
    amax = a.amax or tl['A']
    params = dict(cut=cut, cap=cap, amax=amax, iters=a.iters, pw=a.pw, T0=a.T0, polish_seconds=a.polish_seconds,
                  polish_cap_a=a.polish_cap_a, repair_keep=a.repair_keep)
    rec = MC.Recorder('bottom', a.target, out, a.inp, params, sys.argv, a.seed,
                      'ops/bottom.py: P7 bopt SA (rank-1 shared bottom, exact Kraft per output) + bbuild + A-capped gate kernel')
    log = open(out / 'bottom.jsonl', 'a')

    def LG(**kw):
        kw['t'] = round(time.time() - t0, 1); log.write(json.dumps(kw, default=str) + '\n'); log.flush()
        print(json.dumps(kw, default=str)[:300], flush=True)
    # the builder reads the front from a circuit file: give it an NCFF copy of the start
    sp = out / 'start.ncff.txt'
    if not sp.exists(): sp.write_text(core.write_ncff(c0, MC.MODEL))
    st, why = setup(c0, cut, cap, amax)
    if st is None:
        rec.notes.append(why); LG(event='not-applicable', reason=why, start=m0, cut=cut, cap=cap)
        rec.write('not-applicable'); return
    M, B, opts, info = st
    procs = MC.spawn_workers(sys.argv, a.cpus, a.seed, out) if a.cpus > 1 else []
    LG(event='start', start=m0, cut=cut, cap=cap, amax=amax, Lb=info['Lb'], nfront=info['nfront'], nbottom=info['nbottom'],
       opts=[len(o) for o in opts], own=info['own'] is not None, own_kraft=info['own_kraft'],
       own_cost=M.cost(info['own']) if info['own'] else None)
    pws = [float(x) for x in a.pw.split(',')]
    it = 0
    fixed = [int(x) for x in a.plan_seeds.split(',') if x.strip()]
    while time.time() < deadline - 20:
        pw = pws[it % len(pws)]
        sd = fixed[it] if it < len(fixed) else rng.randrange(1, 10 ** 6); it += 1
        M.pw = pw
        tb = time.time()
        use_own = info['own'] is not None and (a.init == 'own' or (a.init == 'mix' and (it - len(fixed)) % 2 == 1)) and it > len(fixed)
        cc, ch = anneal(M, B, opts, random.Random(sd), a.iters, a.T0, deadline - 15, info['own'] if use_own else None)
        plan = {'circuit': str(sp), 'cap': cap, 'amax': amax, 'Lb': info['Lb'], 'cost': cc,
                'choice': [[list(p) for p in S] for S in ch], 'C': info['C']}
        pj = out / 'plans' / ('plan-s%d.json' % sd); pj.parent.mkdir(exist_ok=True); json.dump(plan, open(pj, 'w'))
        try:
            BU.RNG = None
            nc = BU.build(plan)
        except Exception as e:
            LG(event='build-error', seed=sd, err=repr(e)[:200]); continue
        nc = clean(nc); ok, inf = verify(nc); bm = metrics(nc)
        LG(event='build', seed=sd, pw=pw, init='own' if use_own else 'random', cost=cc, ok=ok, build=bm, secs=round(time.time() - tb, 1))
        if not ok or bm[3] > cap or bm[1] > tl['AD']: continue
        meth = {'engine': 'ops/bottom.py (P7 bopt SA + bbuild, generalised cut)', 'cut': cut, 'cap': cap,
                'pw': pw, 'plan': str(pj), 'plan_cost': cc, 'plan_seed': sd}
        bp = out / 'builds' / ('b-%s.bfx' % cid(nc)); bp.parent.mkdir(exist_ok=True); bp.write_text(core.to_kernel(nc))
        rec.offer(nc, sp, dict(meth, stage='build'))
        if bm[0] > tl['A']:
            continue      # polish only from builds inside the hard A limit
        left = deadline - time.time() - 20
        if left < 20 or a.polish_seconds <= 0: continue
        caps = {'A': bm[0] if a.polish_cap_a == 'build' else tl['A'], 'AD': tl['AD'], 'GD': cap}
        k, kinfo = MC.kernel_stage(nc, caps, sd, min(a.polish_seconds, left), out / 'jobs' / ('s%d' % sd), repair_keep=a.repair_keep)
        if k is not None:
            km = metrics(k)
            LG(event='polish', seed=sd, build=bm, result=km)
            rec.offer(k, bp, dict(meth, stage='kernel', kernel_seed=sd, caps=caps), kernel_bin=kinfo.get('kernel_bin_path'))
        else:
            LG(event='polish', seed=sd, build=bm, result=None, err=kinfo.get('error'))
    if procs: MC.merge_workers(rec, procs, deadline + 30)
    rec.write('ok')
    LG(event='end', front=sorted(rec.front))


if __name__ == '__main__':
    main()
