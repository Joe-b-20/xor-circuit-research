#!/usr/bin/env python3
"""Hub operator wres: window exact resynthesis (agent R1, 2026-11-15; method in wres.py, NOTES.md).

    op_wres.py --archive DIR --in ID [--caps A,AD,GD] [--objective KEYS] --seed S --seconds T --out JOBDIR
        [--K 8] [--maxg 9] [--budget 8000] [--sideways 0.3] [--no-log] [--no-odc]

Loop until T seconds: pick a window (strategy and depth mode at random), SAT-resynthesise it on its
care set under the deadlines from the rest of the circuit, splice, merge duplicates, verify on all
256 inputs; adopt lexicographic improvements (objective keys over A, AD, G, GD; job caps hold) and,
with probability --sideways, equal-key different structures (plateau moves); every adopted circuit
that the archive would place is a candidate.  Modes: 'cost' (caps = job caps), 'gd' (gate-depth
deadline GD-1: equal-cost shallower replacements count), 'ad' (AND depth AD-1).
Writes JOBDIR/cand-*.bfx, JOBDIR/record.json and (unless --no-log) JOBDIR/windows.jsonl (one line per window).
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
sys.path.insert(0, str(next(p for p in HERE.parents if (p / 'boolflux' / 'core.py').exists())))   # .../nonlinear
sys.path.insert(0, str(HERE))
from boolflux.hub.common import core, metrics, code_version   # noqa: E402
import wres as R   # noqa: E402

DEFAULT_OBJECTIVE = 'a,ad,cost,gd'
KIDX = {'a': 0, 'ad': 1, 'cost': 2, 'g': 2, 'gd': 3}


def key(m, keys):
    return tuple(m[KIDX[k]] for k in keys)


def try_window(c, net, W, D, DA, keys, budget, rng, deadline, p_andred=0.5, odc=True, tighten=False):
    """returns (status, best_circuit_or_None, detail)"""
    t0 = time.time()
    ins, outs = net.info(W)
    T = net.tfo(W)
    rq, ra = net.req_ex(W, D, DA)
    det = {'k': len(ins), 'o': len(outs), 'g': len(W), 'a': sum(1 for s in W if net.op(s) == R.AND)}
    if not net.outside_ok(W, T, rq, ra): return 'outside', None, det
    P, vin, okp, tg = R.relation(net, W, ins, outs, T, odc=odc)
    det['P'] = P
    arr = [net.lv[i] for i in ins]; arra = [net.al[i] for i in ins]
    orq = [rq[o] for o in outs]; ora = [ra[o] for o in outs]
    if tighten:      # slack mode: every zero-slack window output must become earlier (fewer critical paths)
        z = [h for h, o in enumerate(outs) if net.lv[o] >= orq[h]]
        if not z: return 'noslack', None, det
        for h in z: orq[h] = net.lv[outs[h]] - 1
        if min(orq) < 1: return 'noslack', None, det
    forbid = {(h, v + 1) for h, o in enumerate(outs) for v, i in enumerate(ins) if o in net.isout and i < net.n}
    gW, aW = det['g'], det['a']
    depth_mode = D < net.GD or DA < net.AD or tighten
    a_first = keys.index('a') < min(keys.index(x) for x in ('cost', 'g') if x in keys) if 'a' in keys else False
    plan = []
    if a_first:
        if aW >= 1 and rng.random() < p_andred: plan.append((aW - 1, gW + 1))
        plan.append((aW, gW if depth_mode else gW - 1))
    else:
        plan.append((gW, gW if depth_mode else gW - 1))
    base_key = key(metrics(c), keys)
    best = None; bestk = None; res = []; nsat = 0
    for amax, r in plan:
        while r >= 1 and amax >= 0:
            if time.time() > deadline: res.append('deadline'); break
            sy = R.Synth(len(ins), P, vin, okp, arr, arra, orq, ora, r, min(amax, r), forbid, seed=rng.randrange(1 << 30))
            out = sy.run(budget, deadline=deadline)
            sy.close()
            res.append('%d/%d:%s' % (amax, r, out[0]))
            if out[0] != 'sat': break
            nsat += 1
            chain, om = R.prune(out[1], out[2], len(ins))
            nc = R.splice(c, net, W, ins, outs, chain, om)
            mc = R.merge_dups(nc)
            if key(metrics(mc), keys) <= key(metrics(nc), keys): nc = mc
            if nc.output_tables() != c.output_tables():
                res.append('VERIFY-FAIL'); break
            kk = key(metrics(nc), keys)
            if bestk is None or kk < bestk: best, bestk = nc, kk
            na = sum(1 for g in chain if g[0] == R.AND)
            r = len(chain) - 1; amax = min(amax, na)
        if best is not None and bestk < base_key and a_first and plan and plan[0][0] < aW: break
    det['plan'] = res; det['dt'] = round(time.time() - t0, 3)
    if best is None:
        st = 'unsat' if res and all(x.endswith('unsat') for x in res) else ('unknown' if any('unknown' in x for x in res) else 'none')
        return st, None, det
    det['key'] = bestk
    return ('improved' if bestk < base_key else 'equal'), best, det


def run(c, caps, keys, seconds, rng, would_place=None, K=8, maxg=9, budget=30000, sideways=0.3, log=None, odc=True,
        modes=(('cost', 0.55), ('slack', 0.25), ('gd', 0.15), ('ad', 0.05)), strategies=('and', 'pair', 'reconv', 'crit', 'mixed')):
    t_end = time.time() + seconds
    cur = c; curk = key(metrics(c), keys); net = R.Net(cur); curcrit = len(R.critical(net, net.GD))
    cands = {}; stats = {}; nwin = 0; seen_eq = set()
    while time.time() < t_end:
        mode = rng.choices([m for m, p in modes], [p for m, p in modes])[0]
        strat = rng.choice(strategies)
        D = caps['GD'] if caps.get('GD') is not None else net.GD
        DA = caps['AD'] if caps.get('AD') is not None else net.AD
        D = min(D, net.GD); DA = min(DA, net.AD)
        if mode == 'gd': D = net.GD - 1
        if mode == 'ad': DA = net.AD - 1
        W = None
        for _try in range(30 if mode != 'cost' else 1):     # depth modes: the window must cut every late path
            W = R.pick_window(net, 'crit' if mode != 'cost' else (strat if strat != 'mixed' else 'x'), rng, K=K, maxg=maxg)
            if W and (mode in ('cost', 'slack') or net.outside_ok(W, net.tfo(W), *net.req_ex(W, D, DA))): break
            W = None
        if mode != 'cost': strat = 'crit'
        if not W:
            stats.setdefault((strat, mode, 'nowindow'), 0); stats[(strat, mode, 'nowindow')] += 1; continue
        nwin += 1
        st, nc, det = try_window(cur, net, W, D, DA, keys, budget, rng, t_end, odc=odc, tighten=(mode == 'slack'))
        stats[(strat, mode, st)] = stats.get((strat, mode, st), 0) + 1
        adopted = False
        if nc is not None:
            m = metrics(nc)
            okcap = (caps.get('A') is None or m[0] <= caps['A']) and m[1] <= DA and m[3] <= D
            kk = key(m, keys)
            txt = core.to_kernel(nc)
            nnet = R.Net(nc); ncrit = len(R.critical(nnet, nnet.GD))
            if okcap and (kk < curk or (kk == curk and txt not in seen_eq and (ncrit < curcrit or rng.random() < sideways))):
                cur, curk, net, curcrit = nc, kk, nnet, ncrit; adopted = True; seen_eq.add(txt)
                if would_place is None or would_place(m): cands[txt] = nc
        if log is not None:
            log.write(json.dumps({'strategy': strat, 'mode': mode, 'status': st, 'adopted': adopted, 'cur': list(curk), 'ncrit': curcrit, **det}) + '\n')
            log.flush()
    return list(cands.values()), {'windows': nwin, 'final_key': list(curk),
                                  'stats': {'%s/%s/%s' % k: v for k, v in sorted(stats.items())}}


def main(argv=None):
    ap = argparse.ArgumentParser(prog='op_wres')
    ap.add_argument('--archive', required=True); ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--in2'); ap.add_argument('--caps')
    ap.add_argument('--objective', default=DEFAULT_OBJECTIVE)
    ap.add_argument('--seed', type=int, default=1); ap.add_argument('--seconds', type=float, default=60)
    ap.add_argument('--max-cands', type=int, default=40)
    ap.add_argument('--K', type=int, default=8); ap.add_argument('--maxg', type=int, default=9)
    ap.add_argument("--budget", type=int, default=8000); ap.add_argument("--sideways", type=float, default=0.3)
    ap.add_argument("--no-log", action="store_true"); ap.add_argument("--no-odc", action="store_true")
    ap.add_argument('--out', required=True)
    args = ap.parse_args(argv)
    from boolflux.hub.archive import Archive
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    t0 = time.time(); r0 = resource.getrusage(resource.RUSAGE_SELF)
    ar = Archive(args.archive)
    c = ar.circuit(args.inp); A, AD, G, GD = metrics(c)
    caps = {'A': A, 'AD': AD, 'GD': GD}
    if args.caps:
        a, ad, gd = (None if x in ('', '-') else int(x) for x in args.caps.split(','))
        caps = {'A': a, 'AD': ad if ad is not None else AD, 'GD': gd if gd is not None else GD}
    keys = [k.strip() for k in args.objective.split(',')]
    log = None if args.no_log else open(out / "windows.jsonl", "w")
    cands, info = run(c, caps, keys, args.seconds, rng, would_place=ar.would_place, K=args.K, maxg=args.maxg,
                      budget=args.budget, sideways=args.sideways, log=log, odc=not args.no_odc)
    if log: log.close()
    if len(cands) > args.max_cands:   # keep the best by objective key
        cands = sorted(cands, key=lambda x: key(metrics(x), keys))[:args.max_cands]
    for k, cc in enumerate(cands):
        (out / ('cand-%03d.bfx' % k)).write_text(core.to_kernel(cc))
    r1 = resource.getrusage(resource.RUSAGE_SELF)
    cpu = r1.ru_utime + r1.ru_stime - r0.ru_utime - r0.ru_stime
    info.update({'odc': not args.no_odc, 'K': args.K, 'maxg': args.maxg, 'budget': args.budget, 'sideways': args.sideways, 'caps_used': caps})
    rec = {'operator': 'wres', 'inputs': [args.inp], 'caps': caps, 'objective': args.objective, 'seed': args.seed,
           'seconds': args.seconds, 'wall_s': round(time.time() - t0, 2), 'cpu_s': round(cpu, 2),
           'candidates': len(cands), 'code_version': code_version(), 'info': info}
    (out / 'record.json').write_text(json.dumps(rec, indent=1, default=str))
    return 0


if __name__ == '__main__':
    sys.exit(main())
