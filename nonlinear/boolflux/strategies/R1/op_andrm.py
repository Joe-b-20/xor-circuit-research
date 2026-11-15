#!/usr/bin/env python3
"""Hub operator andrm (R1, 2026-11-15): exact window AND removal, then a gate-kernel polish of the result.

    op_andrm.py --archive DIR --in ID [--caps A,AD,GD] [--objective KEYS] --seed S --seconds T --out JOBDIR
        [--share 0.5] [--K 10] [--ad-slack 1]

Phase 1 (share of T): random convex windows with 2-4 ANDs (mc1.windows); a window is rebuilt with one AND
less when mc1.check_window finds flat products (rank test + exhaustive flat search) or, for 3-AND windows
with output rank 2, seq2.check finds a sequential 2-AND rebuild.  Each removal is spliced, merged,
verified on all 256 inputs and chained (repeat until no window removes an AND or the phase ends).
The AND depth may rise by at most --ad-slack over the input's AD (A first in the user's value order).
Phase 2: the gate kernel (hub ops._kernel, op_polish settings) polishes the reduced circuit under its own
caps.  Candidates: every reduced circuit (raw and polished) the archive would place with the generator
slack (archive.GEN_SLACK), best first.  Register as a generator so the scheduler's nursery polishes them.
"""
from __future__ import annotations

import argparse, json, random, resource, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(next(p for p in HERE.parents if (p / 'boolflux' / 'core.py').exists())))
sys.path.insert(0, str(HERE))
from boolflux.hub.common import core, metrics, code_version   # noqa: E402
import wres as R    # noqa: E402
import mc1          # noqa: E402
import seq2         # noqa: E402


def remove(c, rng, seconds, K=10, ad_cap=None, log=None):
    t_end = time.time() + seconds
    cur = c; ref = c.output_tables(); steps = []; nwin = 0
    while time.time() < t_end:
        net = R.Net(cur); done = False; seen = set()
        for _ in range(3000):
            if time.time() > t_end: break
            W = mc1.windows(net, rng, K, 16, 6, 4)
            if not W: continue
            fw = frozenset(W)
            if fw in seen: continue
            seen.add(fw); nwin += 1
            rr = mc1.check_window(net, W, K)
            if rr is None: continue
            det, ctx, prods = rr
            rb = None; how = det['status']
            if prods is not None:
                rb = mc1.rebuild(net, ctx, prods); ins, outs = ctx[0], ctx[1]
            elif det['status'] == 'no_flat' and det['a'] == 3 and det['r'] == 2:
                r2 = seq2.check(net, W, K)
                if r2 is not None and r2[1] is not None:
                    rb = seq2.rebuild(net, r2[1]); ins, outs = r2[1][0], r2[1][1]; how = 'seq2'
            if log is not None:
                log.write(json.dumps({'k': det['k'], 'g': det['g'], 'a': det['a'], 'r': det['r'], 'status': how, 'rebuilt': rb is not None}) + '\n')
            if rb is None: continue
            nc = R.splice(cur, net, W, ins, outs, *rb)
            mc = R.merge_dups(nc)
            if metrics(mc) <= metrics(nc): nc = mc
            if nc.output_tables() != ref: continue
            m = metrics(nc)
            if m[0] < metrics(cur)[0] and (ad_cap is None or m[1] <= ad_cap):
                steps.append({'from': list(metrics(cur)), 'to': list(m), 'how': how, 'k': det['k'], 'g': det['g'], 'a': det['a']})
                cur = nc; done = True; break
        if not done: break
    return cur, steps, nwin


def main(argv=None):
    ap = argparse.ArgumentParser(prog='op_andrm')
    ap.add_argument('--archive', required=True); ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--in2'); ap.add_argument('--caps'); ap.add_argument('--objective', default='a,ad,cost,gd')
    ap.add_argument('--seed', type=int, default=1); ap.add_argument('--seconds', type=float, default=60)
    ap.add_argument('--max-cands', type=int, default=40); ap.add_argument('--share', type=float, default=0.5)
    ap.add_argument('--K', type=int, default=10); ap.add_argument('--ad-slack', type=int, default=1)
    ap.add_argument('--out', required=True)
    args = ap.parse_args(argv)
    from boolflux.hub.archive import Archive, GEN_SLACK
    from boolflux.hub.ops import _kernel
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    t0 = time.time(); r0 = resource.getrusage(resource.RUSAGE_SELF); c0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    t_end = t0 + args.seconds
    ar = Archive(args.archive)
    c = ar.circuit(args.inp); A, AD, G, GD = metrics(c)
    with open(out / 'windows.jsonl', 'w') as log:
        red, steps, nwin = remove(c, rng, args.seconds * args.share, args.K, AD + args.ad_slack, log)
    cands = []; pol = None
    if steps:
        cands.append(red)
        mr = metrics(red)
        left = t_end - time.time()
        if left > 3:
            pd = out / 'polish'; pd.mkdir(exist_ok=True)
            pcs, pinfo = _kernel(red, {'A': mr[0], 'AD': mr[1], 'GD': mr[3]}, args.objective, rng.randrange(1, 1 << 30), left, pd, args.archive)
            for x in pcs:
                if x.output_tables() == c.output_tables(): cands.append(x)
            pol = [list(metrics(x)) for x in pcs]
    keep = []; seen = set()
    for x in sorted(cands, key=lambda x: metrics(x)):
        tx = core.to_kernel(x)
        if tx in seen or not ar.would_place(metrics(x), slack=GEN_SLACK): continue
        seen.add(tx); keep.append(x)
    keep = keep[:args.max_cands]
    for k, x in enumerate(keep):
        (out / ('cand-%03d.bfx' % k)).write_text(core.to_kernel(x))
    r1 = resource.getrusage(resource.RUSAGE_SELF); c1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = (r1.ru_utime + r1.ru_stime - r0.ru_utime - r0.ru_stime) + (c1.ru_utime + c1.ru_stime - c0.ru_utime - c0.ru_stime)
    rec = {'operator': 'andrm', 'inputs': [args.inp], 'caps': None, 'objective': args.objective, 'seed': args.seed,
           'seconds': args.seconds, 'wall_s': round(time.time() - t0, 2), 'cpu_s': round(cpu, 2), 'candidates': len(keep),
           'code_version': code_version(),
           'info': {'windows': nwin, 'steps': steps, 'reduced': list(metrics(red)), 'polished': pol, 'share': args.share,
                    'K': args.K, 'ad_slack': args.ad_slack}}
    (out / 'record.json').write_text(json.dumps(rec, indent=1, default=str))
    return 0


if __name__ == '__main__':
    sys.exit(main())
