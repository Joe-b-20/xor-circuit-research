#!/usr/bin/env python3
"""winsat: exact SAT resynthesis of windows that span AND levels (2026-11-17), under the
operator contract of ops/common.py:

    python3 search/nonlinear/boolflux/ops/winsat.py --in START.circ.txt --target REF --seed S \
        --seconds T --out DIR [--K 8] [--maxg 10] [--budget 20000] [--strong 1] [--odc 1]
        [--strategies bigmffc,and2,viol,pair,and,x] [--modes cost:0.6,gd:0.25,slack:0.15] [--calib]

Method (winsat_lib.py; window code of 2026-11-15 with additions):
  * window W: a convex gate set, --ming (default 4) to --maxg gates, <= K inputs, 1..4 outputs; chosen by
      bigmffc  root drawn with weight (MFFC size - 2) (MFFC >= 5 targets are the kernel's most
               productive), grown from its cone;
      and2     an AND, an AND that reads it within 3 steps and the gates between (spans an AND level);
      viol     a gate on a critical path and its critical fan-in (gate level = required level);
      pair, and, x   the original strategies (two nearby ANDs; an AND and its operand trees; random growth).
  * the exact multi-output Boolean relation of W (all 256 inputs; ODC on by default), arrival times of
    W's inputs and required times of W's outputs (caps = the current circuit's GD and AD, or GD - 1
    in mode gd); a chain of r steps over {AND, XOR, XNOR, NOT} with at most aW ANDs (A never rises).
  * queries: cost (aW, gW - 1), then down by one while SAT; gd (aW, gW or gW + 1 with p 0.5) at
    D = GD - 1 (window must cut every path deeper than GD - 1); slack: every zero-slack output earlier;
    relax: the cost query with deadlines from GD + 1..2 (fewer gates at a deeper GD; offered to the
    Recorder, never adopted as the walk state).
  * mode andrm (winsat_andrm.py): a window of 2-4 ANDs (<= 10 inputs, <= 16 gates) is
    rebuilt with one AND fewer when the rank of its outputs mod span(1, inputs) on the care set allows it
    and flat products span the residues (exact per window); AD and GD may rise.  Every rebuild is
    offered; it becomes the walk state if AD <= current AD + --andrm-ad.  Results need a kernel
    polish/pull afterwards (2026-11-17: published inverse 32/4/118/19 -> 31/5/127/21 -> polish 31/5/118/21).
  * --strong 1 (default): the encoding adds dead-steps-first, live-steps-used and removable-step
    clauses (winsat_lib.Synth strong); --strong 0 is the original encoding.
  * splice, merge equal functions, verify on all 256 inputs; walk state = best by (A, AD, G, GD), plus
    plateau moves (equal key, new structure) with p --sideways; every result goes to the Recorder
    (aes_check, sidecar, Pareto-new inside A <= ref A, AD <= ref AD).
  * --calib: every window query runs with both encodings (same budget, random order), nothing adopted;
    windows.jsonl has both outcomes and CPU times.
Writes DIR/windows.jsonl (one line per window), DIR/result.json (+ 'winsat' stats), run records.
"""
from __future__ import annotations

import argparse
import json
import random
import resource
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as OC                         # noqa: E402
from boolflux import core                   # noqa: E402
import winsat_lib as R                      # noqa: E402

KIDX = {'a': 0, 'ad': 1, 'cost': 2, 'g': 2, 'gd': 3}
KEYS = ['a', 'ad', 'cost', 'gd']


def cpu():
    r = resource.getrusage(resource.RUSAGE_SELF)
    return r.ru_utime + r.ru_stime


def key(m):
    return tuple(m[KIDX[k]] for k in KEYS)


def fingerprint(c):
    n = c.n; t = c.tables()
    return frozenset(t[n + j] for j in range(len(c.gates)))


def solve(k, P, vin, okp, arr, arra, orq, ora, r, amax, forbid, seed, budget, deadline, strong):
    t0 = cpu()
    sy = R.Synth(k, P, vin, okp, arr, arra, orq, ora, r, min(amax, r), forbid, seed=seed, strong=strong)
    out = sy.run(budget, deadline=deadline)
    sy.close()
    return out, round(cpu() - t0, 3)


def try_window(c, net, W, D, DA, rng, deadline, budget, strong, odc=True, tighten=False, gd_extra=0, calib=False):
    """-> (status, circuit or None, detail)"""
    ins, outs = net.info(W)
    T = net.tfo(W)
    rq, ra = net.req_ex(W, D, DA)
    det = {'k': len(ins), 'o': len(outs), 'g': len(W), 'a': sum(1 for s in W if net.op(s) == R.AND),
           'lv': sorted({net.al[s] for s in W if net.op(s) == R.AND})}
    if not net.outside_ok(W, T, rq, ra): return 'outside', None, det
    P, vin, okp, tg = R.relation(net, W, ins, outs, T, odc=odc)
    det['P'] = P
    arr = [net.lv[i] for i in ins]; arra = [net.al[i] for i in ins]
    orq = [rq[o] for o in outs]; ora = [ra[o] for o in outs]
    if tighten:
        z = [h for h, o in enumerate(outs) if net.lv[o] >= orq[h]]
        if not z: return 'noslack', None, det
        for h in z: orq[h] = net.lv[outs[h]] - 1
        if min(orq) < 1: return 'noslack', None, det
    forbid = {(h, v + 1) for h, o in enumerate(outs) for v, i in enumerate(ins) if o in net.isout and i < net.n}
    gW, aW = det['g'], det['a']
    depth_mode = D < net.GD or tighten
    r = gW + gd_extra if depth_mode else gW - 1
    base = key(OC.metrics(c))
    best = bestk = None; res = []; cal = []
    amax = aW
    while r >= 1:
        if time.time() > deadline: res.append('deadline'); break
        sd = rng.randrange(1 << 30)
        if calib:
            order = [True, False]; rng.shuffle(order); outs_ = {}
            for st in order:
                o_, t_ = solve(len(ins), P, vin, okp, arr, arra, orq, ora, r, amax, forbid, sd, budget, deadline, st)
                outs_[st] = (o_, t_)
            cal.append({'r': r, 'amax': amax, 'strong': [outs_[True][0][0], outs_[True][1]],
                        'r1': [outs_[False][0][0], outs_[False][1]]})
            out = outs_[True][0] if outs_[True][0][0] == 'sat' else outs_[False][0]
        else:
            out, t_ = solve(len(ins), P, vin, okp, arr, arra, orq, ora, r, amax, forbid, sd, budget, deadline, strong)
        res.append('%d/%d:%s' % (amax, r, out[0]))
        if out[0] != 'sat': break
        chain, om = R.prune(out[1], out[2], len(ins))
        nc = R.splice(c, net, W, ins, outs, chain, om)
        mc = R.merge_dups(nc)
        if key(OC.metrics(mc)) <= key(OC.metrics(nc)): nc = mc
        if nc.output_tables() != c.output_tables():
            res.append('VERIFY-FAIL'); break
        kk = key(OC.metrics(nc))
        if bestk is None or kk < bestk: best, bestk = nc, kk
        na = sum(1 for g in chain if g[0] == R.AND)
        amax = min(amax, na)
        if depth_mode: break
        r = len(chain) - 1
    det['plan'] = res
    if cal: det['calib'] = cal
    if best is None:
        st = 'unsat' if res and all(x.endswith('unsat') for x in res) else ('unknown' if any('unknown' in x for x in res) else 'none')
        return st, None, det
    det['key'] = list(bestk)
    return ('improved' if bestk < base else 'equal'), best, det


def andrm_window(c, net, rng, K=10, maxg=16, maxo=6, amax=4):
    """-> (status, circuit or None, detail): the AND-removal check on one window of 2..amax ANDs (winsat_andrm.py).
    status: nowindow | rank | no_flat | affine | removed (rebuilt, verified) | rebuild-fail | verify-fail."""
    import winsat_andrm as M
    if len(net.ands) < 2: return 'nowindow', None, {}
    W = M.windows(net, rng, K, maxg, maxo, amax)
    if not W: return 'nowindow', None, {}
    rr = M.check_window(net, W, K)
    if rr is None: return 'nowindow', None, {}
    det, ctx, prods = rr
    st = det.pop('status')
    if prods is None: return st, None, det
    rb = M.rebuild(net, ctx, prods)
    if rb is None: return 'rebuild-fail', None, det
    chain, om = rb
    nc = R.splice(c, net, W, ctx[0], ctx[1], chain, om)
    mc = R.merge_dups(nc)
    if OC.metrics(mc) <= OC.metrics(nc): nc = mc
    if nc.output_tables() != c.output_tables(): return 'verify-fail', None, det
    det['key'] = list(key(OC.metrics(nc)))
    return 'removed', nc, det


def main(argv=None):
    ap = argparse.ArgumentParser(prog='winsat')
    OC.contract_args(ap)
    ap.add_argument('--K', type=int, default=8); ap.add_argument('--maxg', type=int, default=10)
    ap.add_argument('--ming', type=int, default=4)
    ap.add_argument('--budget', type=int, default=20000, help='SAT conflicts per call')
    ap.add_argument('--strong', type=int, default=1); ap.add_argument('--odc', type=int, default=1)
    ap.add_argument('--strategies', default='bigmffc,and2,viol,pair,and,x')
    ap.add_argument('--modes', default='cost:0.6,gd:0.25,slack:0.15')
    ap.add_argument('--sideways', type=float, default=0.3)
    ap.add_argument('--calib', action='store_true')
    ap.add_argument('--andrm-ad', dest='andrm_ad', type=int, default=1,
                    help='mode andrm: an A-1 rebuild becomes the walk state if its AD <= current AD + this')
    a = ap.parse_args(argv)
    OC.init_function(a)
    t0 = time.time(); c0 = cpu()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(a.seed)
    c = OC.load(a.inp)
    params = {k: getattr(a, k) for k in ('K', 'maxg', 'ming', 'budget', 'strong', 'odc', 'strategies', 'modes', 'sideways', 'calib', 'andrm_ad')}
    rec = OC.Recorder(out, 'winsat', a.target, a.inp, a.seed, ' '.join(sys.argv), 'window exact SAT resynthesis', params,
                      t0=t0, budget_s=a.seconds)
    strategies = [s for s in a.strategies.split(',') if s]
    modes = [(m.split(':')[0], float(m.split(':')[1])) for m in a.modes.split(',') if m]
    t_end = t0 + a.seconds
    cur = c; curk = key(OC.metrics(c)); net = R.Net(cur); curcrit = len(R.critical(net, net.GD))
    seen = {fingerprint(c)}; stats = {}; nwin = 0; adopted = 0
    log = open(out / 'windows.jsonl', 'w')
    while time.time() < t_end - 1:
        mode = rng.choices([m for m, _ in modes], [p for _, p in modes])[0]
        strat = rng.choice(strategies)
        D = net.GD; DA = net.AD; gd_extra = 0
        if mode == 'gd': D = net.GD - 1; gd_extra = 1 if rng.random() < 0.5 else 0
        if mode == 'relax': D = net.GD + rng.choice([1, 1, 2])
        tw = cpu()
        if mode == 'andrm':          # exact window AND removal (rank test + exhaustive flat products)
            st, nc, det = andrm_window(cur, net, rng)
            stats[('andrm', mode, st)] = stats.get(('andrm', mode, st), 0) + 1
            if st == 'nowindow': continue
            nwin += 1; ad = False
            if nc is not None:
                m = OC.metrics(nc)
                rec.offer(nc, how='winsat andrm g%d k%d a%d' % (det['g'], det['k'], det['a']))
                if m[0] < curk[0] and m[1] <= curk[1] + a.andrm_ad:
                    cur, curk, net = nc, key(m), R.Net(nc); curcrit = len(R.critical(net, net.GD))
                    ad = True; adopted += 1; seen.add(fingerprint(nc))
            log.write(json.dumps({'t': round(time.time() - t0, 2), 'cpu': round(cpu() - tw, 3), 'strategy': 'andrm',
                                  'mode': mode, 'status': st, 'adopted': ad, 'cur': list(curk), **det}) + '\n')
            continue
        W = None
        for _try in range(30 if mode == 'gd' else 1):
            st_ = strat if mode != 'gd' else rng.choice(['viol', 'crit'])
            W = R.pick_window(net, st_, rng, K=a.K, maxg=a.maxg, ming=a.ming)
            if W and (mode != 'gd' or net.outside_ok(W, net.tfo(W), *net.req_ex(W, D, DA))): break
            W = None
        if mode == 'gd': strat = 'viol/crit'
        if not W:
            stats[(strat, mode, 'nowindow')] = stats.get((strat, mode, 'nowindow'), 0) + 1
            continue
        nwin += 1
        st, nc, det = try_window(cur, net, W, D, DA, rng, t_end, a.budget, bool(a.strong), odc=bool(a.odc),
                                 tighten=(mode == 'slack'), gd_extra=gd_extra, calib=a.calib)
        stats[(strat, mode, st)] = stats.get((strat, mode, st), 0) + 1
        ad = False
        if nc is not None and not a.calib:
            m = OC.metrics(nc); kk = key(m)
            rec.offer(nc, how='winsat %s/%s g%d k%d' % (strat, mode, det['g'], det['k']))
            fp = fingerprint(nc); nnet = R.Net(nc); ncrit = len(R.critical(nnet, nnet.GD))
            okcap = m[0] <= curk[0] and m[1] <= curk[1] and m[3] <= curk[3]
            if okcap and (kk < curk or (kk == curk and fp not in seen and (ncrit < curcrit or rng.random() < a.sideways))):
                cur, curk, net, curcrit = nc, kk, nnet, ncrit; ad = True; adopted += 1; seen.add(fp)
        log.write(json.dumps({'t': round(time.time() - t0, 2), 'cpu': round(cpu() - tw, 3), 'strategy': strat, 'mode': mode,
                              'status': st, 'adopted': ad, 'cur': list(curk), **det}) + '\n')
        log.flush()
    log.close()
    extra = {'winsat': {'windows': nwin, 'adopted': adopted, 'final_key': list(curk), 'cpu_s': round(cpu() - c0, 2),
                        'stats': {'%s/%s/%s' % k: v for k, v in sorted(stats.items())}}}
    rec.finish('ok', extra)
    return 0


if __name__ == '__main__':
    sys.exit(main())
