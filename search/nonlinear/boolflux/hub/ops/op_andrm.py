#!/usr/bin/env python3
"""Hub operator andrm (opt-in: --ops ...,andrm; idea 09's recommendation, 2026-11-17): exact window AND
removal, then a kernel polish of the hit and a pull back to the source's gate depth.

    python3 hub/ops/op_andrm.py --archive DIR --in ID --seed S --seconds T --out JOBDIR [--bests 8]

1. AND removal (ops/winsat.py andrm_window = ops/winsat_andrm.py, R1's mc1): random windows of 2-4 ANDs
   (<= 10 inputs, <= 16 gates) of the input; a window whose outputs, mod span(1, window inputs) on the care
   set, have rank <= aW - 1 and are spanned by flat products is rebuilt with one AND fewer, spliced, merged
   and checked on all 256 inputs (exact per window).  AD and GD may rise.  Runs for ANDRM_SHARE of T, or
   until ANDRM_HITS distinct hits.  No hit: no candidates (info 'skip').
2. The best hit by (A, AD, G, GD): gate kernel (hub op_polish settings) at the hit's own caps (A, AD, GD),
   POLISH_SHARE of the time left.
3. From the polish best: the kernel with GD capped at the source's GD (A and AD of the hit; repair mode
   when the hit is deeper), the rest of the time.  When the hit is not deeper than the source, step 3 is
   skipped and step 2 gets the whole time.
Candidates: every placeable hit, the kernel finals and up to --bests intermediate bests of each kernel run,
highest archive gain first, at most --max-cands.  Measured by idea 09 (outside the hub): ~1.1 new circuits
per CPU-h, the only operator that lowers A (published inverse 32/4/118/19 -> 31/5/127/21 -> 31/5/118/21;
forward 37/4/127/13 -> 36/4/128/14 -> pull 36/4/128/13).
"""
import sys
import time
from pathlib import Path

OPS_DIR = Path(__file__).resolve().parent
PKG = OPS_DIR.parents[1]
sys.path.insert(0, str(PKG.parent)); sys.path.insert(0, str(PKG / 'ops'))
from boolflux.hub import ops as HO                       # noqa: E402
from boolflux.hub.common import core, metrics, cid       # noqa: E402

ANDRM_SHARE = 0.3       # of --seconds for the window search
ANDRM_HITS = 3          # stop the window search after this many distinct A-1 hits
POLISH_SHARE = 0.5      # of the time left after the search, when a pull follows


def search(c, rng, seconds, max_hits=None):
    """distinct verified hits (fewer ANDs than c) of the window AND removal within `seconds`; (hits, stats)"""
    import winsat_lib as R
    import winsat
    max_hits = max_hits or ANDRM_HITS
    net = R.Net(c); A0 = metrics(c)[0]
    hits = {}; stats = {}; t_end = time.time() + seconds; nwin = 0
    while time.time() < t_end and len(hits) < max_hits:
        st, nc, det = winsat.andrm_window(c, net, rng)
        stats[st] = stats.get(st, 0) + 1
        if st == 'nowindow':
            if stats[st] > 2000 and nwin == 0: break       # no AND pair with a window: nothing to do
            continue
        nwin += 1
        if nc is not None and metrics(nc)[0] < A0:
            hits.setdefault(cid(nc), nc)
    return sorted(hits.values(), key=metrics), stats


def op_andrm(ar, args, rng, out):
    c = ar.circuit(args.inp); A, AD, G, GD = metrics(c)
    t0 = time.time(); T = float(args.seconds)
    hits, stats = search(c, rng, ANDRM_SHARE * T)
    info = {'andrm': stats, 'hits': [list(metrics(h)) for h in hits], 'source': [A, AD, G, GD]}
    if not hits:
        info['skip'] = 'no window AND removal found (%s)' % ', '.join('%s %d' % kv for kv in sorted(stats.items()))
        return [], info
    cands = []
    for h in hits:
        hc, m, why = HO.placeable(ar, h)
        if why == 'ok': cands.append(hc)
    h = hits[0]; hA, hAD, hG, hGD = metrics(h)
    left = max(1.0, T - (time.time() - t0))
    pull = hGD > GD
    s_pol = max(1.0, POLISH_SHARE * left) if pull else left
    pd = out / 'polish'; pd.mkdir(parents=True, exist_ok=True)
    caps = {'A': hA, 'AD': hAD, 'GD': hGD}
    k1, i1 = HO._kernel(h, caps, args.objective, args.seed, s_pol, pd, args.archive)
    cands += HO.with_bests(ar, k1, i1, getattr(args, 'bests', 0))
    info['polish'] = {'caps': caps, 'seconds': round(s_pol, 1), 'final': [list(metrics(x)) for x in k1],
                      'bests': i1.get('bests'), 'kernel_bin': i1.get('kernel_bin'), 't_last_improvement': i1.get('t_last_improvement')}
    if pull:
        base = k1[0] if k1 else h
        s_pull = max(1.0, T - (time.time() - t0))
        qd = out / 'pull'; qd.mkdir(parents=True, exist_ok=True)
        caps2 = {'A': hA, 'AD': hAD, 'GD': GD}
        k2, i2 = HO._kernel(base, caps2, args.objective, args.seed + 1, s_pull, qd, args.archive)
        cands += HO.with_bests(ar, k2, i2, getattr(args, 'bests', 0))
        info['pull'] = {'caps': caps2, 'seconds': round(s_pull, 1), 'final': [list(metrics(x)) for x in k2],
                        'bests': i2.get('bests'), 't_last_improvement': i2.get('t_last_improvement')}
    uniq = {}
    for x in cands:
        xc, m, why = HO.placeable(ar, x)
        if why == 'ok': uniq.setdefault(cid(xc), xc)
    cl = sorted(uniq.values(), key=lambda x: (-ar.gain(metrics(x)), metrics(x)))
    info['placeable'] = len(cl)
    return cl[:args.max_cands], info


HO.OPS['andrm'] = op_andrm

if __name__ == '__main__':
    sys.exit(HO.main('andrm'))
