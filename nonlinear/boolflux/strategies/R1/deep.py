#!/usr/bin/env python3
"""Deep window study (R1): large mixed windows (>= 2 ANDs, 6..10 gates) on goal circuits, one exact query per
window with a large conflict budget, AND reduction first: (aW - 1 ANDs, <= gW + 2 steps), then (aW, gW - 1).
Every SAT answer is spliced, verified on all 256 inputs, written to OUT/found-*.bfx with metrics.

    deep.py CAMPAIGN ID[,ID...] HOURS SEED OUT.jsonl [--budget 400000] [--mode cost|ad|gd] [--maxg 10] [--ming 6]
"""
import argparse, json, random, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(next(p for p in HERE.parents if (p / 'boolflux' / 'core.py').exists()))); sys.path.insert(0, str(HERE))
from boolflux import core                         # noqa: E402
from boolflux.hub.archive import Archive          # noqa: E402
from boolflux.hub.common import metrics           # noqa: E402
import wres as R                                   # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('camp'); ap.add_argument('ids'); ap.add_argument('hours', type=float); ap.add_argument('seed', type=int)
ap.add_argument('out'); ap.add_argument('--budget', type=int, default=400000); ap.add_argument('--mode', default='cost')
ap.add_argument('--maxg', type=int, default=10); ap.add_argument('--ming', type=int, default=6); ap.add_argument('--K', type=int, default=8)
ap.add_argument('--minand', type=int, default=2)
ap.add_argument('--aonly', action='store_true', help='only the AND-reduction query (aW-1, gW+extra)')
ap.add_argument('--gdrelax', type=int, default=0, help='gate-depth deadlines from GD + this (A first: GD may grow)')
ap.add_argument('--adrelax', type=float, default=0.0, help='probability of AND-depth deadlines from AD + 1')
ap.add_argument('--extra', type=int, default=2)
a = ap.parse_args()
rng = random.Random(a.seed)
ar = Archive(a.camp, )
ids = a.ids.split(',')
circ = {i: ar.circuit(i) for i in ids}
outdir = Path(a.out).with_suffix(''); outdir.mkdir(parents=True, exist_ok=True)
f = open(a.out, 'a')
t_end = time.time() + a.hours * 3600
seen = set()
while time.time() < t_end:
    i = rng.choice(ids); c = circ[i]; net = R.Net(c)
    W = R.pick_window(net, rng.choice(['and', 'pair', 'pair', 'x']), rng, K=a.K, maxg=a.maxg, ming=a.ming)
    if not W: continue
    aW = sum(1 for s in W if net.op(s) == R.AND)
    if aW < a.minand: continue
    key = (i, frozenset(W))
    if key in seen: continue
    seen.add(key)
    D, DA = net.GD - (a.mode == 'gd') + a.gdrelax, net.AD - (a.mode == 'ad') + (rng.random() < a.adrelax)
    ins, outs = net.info(W); T = net.tfo(W)
    rq, ra = net.req_ex(W, D, DA)
    rec = {'id': i, 'm': metrics(c), 'mode': a.mode, 'D': D, 'DA': DA, 'g': len(W), 'a': aW, 'k': len(ins), 'o': len(outs), 'W': sorted(W)}
    if not net.outside_ok(W, T, rq, ra):
        continue
    P, vin, okp, tg = R.relation(net, W, ins, outs, T)
    rec['P'] = P
    arr = [net.lv[x] for x in ins]; arra = [net.al[x] for x in ins]
    orq = [rq[o] for o in outs]; ora = [ra[o] for o in outs]
    forbid = {(h, v + 1) for h, o in enumerate(outs) for v, x in enumerate(ins) if o in net.isout and x < net.n}
    res = []
    plan = [(aW - 1, len(W) + a.extra), (aW, len(W) - 1)] if a.mode == 'cost' else [(aW - 1, len(W) + a.extra), (aW, len(W))]
    if a.aonly: plan = plan[:1]
    for amax, r in plan:
        t0 = time.time()
        sy = R.Synth(len(ins), P, vin, okp, arr, arra, orq, ora, r, min(amax, r), forbid, seed=rng.randrange(1 << 30))
        out = sy.run(a.budget); sy.close()
        e = {'q': '%d/%d' % (amax, r), 'st': out[0], 'dt': round(time.time() - t0, 2)}
        if out[0] == 'sat':
            chain, om = R.prune(out[1], out[2], len(ins))
            nc = R.splice(c, net, W, ins, outs, chain, om)
            mc = R.merge_dups(nc)
            if metrics(mc) <= metrics(nc): nc = mc
            e['ok'] = nc.output_tables() == c.output_tables()
            e['m_new'] = metrics(nc)
            if e['ok']:
                p = outdir / ('found-%s-%d.bfx' % (i, len(seen)))
                p.write_text(core.to_kernel(nc)); e['file'] = str(p)
        res.append(e)
        if out[0] == 'sat' and amax < aW: break
    rec['res'] = res
    f.write(json.dumps(rec) + '\n'); f.flush()
