#!/usr/bin/env python3
"""Memetic skeleton-kick search (Track E, mechanism M2).

Cycle: current circuit C -> AND-skeleton (skeleton.extract) -> a few skeleton moves (private skel
kernel, emit_current 1, at least one accepted move: swap/merge/split/perturb of AND products) ->
seeded rebuild with C as parent (the parent's XOR logic is kept wherever its function survives) ->
gate-kernel polish (bfx_e, control configuration) for P seconds -> accept the polished circuit if its
objective is <= C's (plateau) or with probability exp(-delta/T); keep the best.

    python3 kick.py --start FILE --out DIR --tag TAG --seed S --seconds TOTAL --polish P [caps]
"""
import argparse, json, math, random, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import core, load, metrics, correct, MODEL, SBOX   # noqa: E402
import skeleton_e as skeleton   # noqa: E402
from erun import DEFAULTS, weights, parse_log   # noqa: E402

SKEL = {'w.a': 1, 'w.lin': 0.02, 'T0': 0.3, 'Tperiod_it': 4000, 'mv.swap': 4, 'mv.merge': 3,
        'mv.split': 1, 'mv.perturb': 1, 'pairs': 60000, 'fext': 400, 'emit_current': 1}


def obj_of(m, w, caps):
    A, AD, G, GD = m
    viol = sum(max(0, v - c) for v, c in ((A, caps.get('A')), (AD, caps.get('AD')), (GD, caps.get('GD'))) if c is not None)
    return w['w.cost'] * G + w['w.g'] * G + w['w.a'] * A + w['w.gd'] * GD + w['w.ad'] * AD + 1e6 * viol


def skel_kick(c, out, seed, iters, cap_ad, over=None):
    sk = skeleton.extract(c)
    outs = core.tables_from_values(c.n, c.m, SBOX)
    sp = out / 'k.skin'; so = out / 'k.skout'; cp = out / 'k.skcfg'
    sp.write_text(skeleton.write_skel(sk, outs))
    cfg = dict(SKEL); cfg.update({'in': sp, 'out': so, 'seed': seed, 'iters': iters, 'seconds': 30})
    if cap_ad is not None: cfg['cap.ad'] = cap_ad
    cfg.update(over or {})
    cp.write_text(''.join('%s %s\n' % kv for kv in cfg.items()))
    r = subprocess.run([str(HERE / 'skel_e'), str(cp)], capture_output=True, text=True)
    if r.returncode != 0: return None, 0
    sk2 = skeleton.read_skel(so.read_text())
    old = set(sk['ands']); changed = sum(1 for a in sk2['ands'] if a not in old)
    if sk2['ands'] == sk['ands']: return None, 0
    c2 = skeleton.synthesize(sk2, MODEL.ops(), name='kick', parent=c)
    if c2.value_table() != SBOX: raise RuntimeError('rebuild wrong')
    return c2, changed


def polish(c, out, tag, seed, secs, args):
    sp = out / (tag + '.start.bfx'); sp.write_text(core.to_kernel(c))
    bp = out / (tag + '.best.bfx'); cp = out / (tag + '.cfg'); lp = out / (tag + '.log')
    cfg = dict(DEFAULTS); cfg.update(weights(args.objective))
    for op, cc in MODEL.cost.items(): cfg['cost.%d' % op] = cc
    for k, v in (('cap.a', args.cap_a), ('cap.ad', args.cap_ad), ('cap.gd', args.cap_gd)):
        if v is not None: cfg[k] = v
    for s in args.set or []:
        k, v = s.split('=', 1); cfg[k] = v
    cfg.update({'in': sp, 'out': bp, 'seed': seed, 'seconds': secs})
    cp.write_text(''.join('%s %s\n' % kv for kv in cfg.items()))
    with open(lp, 'w') as lf:
        subprocess.run([str(HERE / "bfx_new"), str(cp)], stdout=lf, stderr=subprocess.STDOUT)
    c2 = core.from_kernel(bp.read_text(), tag)
    assert correct(c2)
    return c2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--tag', required=True); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--seconds', type=float, default=600); ap.add_argument('--polish', type=float, default=20)
    ap.add_argument('--first-polish', type=float, default=None)
    ap.add_argument('--skel-iters', type=int, default=20000)
    ap.add_argument('--max-acc', type=int, default=1)
    ap.add_argument('--tries', type=int, default=3)
    ap.add_argument('--max-penalty', type=float, default=1e18)
    ap.add_argument('--temp', type=float, default=0.7)
    ap.add_argument('--skel-wlin', type=float, default=None)
    ap.add_argument('--skel-capk', type=int, default=None)
    ap.add_argument('--cap-a', type=int); ap.add_argument('--cap-ad', type=int); ap.add_argument('--cap-gd', type=int)
    ap.add_argument('--objective', default='cost,gd'); ap.add_argument('--set', action='append')
    args = ap.parse_args()
    out = Path(args.out); wd = out / (args.tag + '.work'); wd.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    caps = {'A': args.cap_a, 'AD': args.cap_ad, 'GD': args.cap_gd}
    w = weights(args.objective)
    start = load(args.start); assert correct(start)
    t0 = time.time()
    fp = args.first_polish if args.first_polish is not None else args.polish
    cur = polish(start, wd, 'p0', args.seed * 1000, fp, args)
    cm = metrics(cur); co = obj_of(cm, w, caps)
    best, bm, bo = cur, cm, co
    hist = [{'t': round(time.time() - t0, 1), 'cycle': 0, 'polished': cm, 'accepted': True}]
    bests = [{'t': round(time.time() - t0, 2), 'cycle': 0, 'metrics': bm}]
    cyc = 0; nk = 0
    while time.time() - t0 < args.seconds:
        cyc += 1
        over = {'max_acc': args.max_acc}
        if args.skel_wlin is not None: over['w.lin'] = args.skel_wlin
        if args.skel_capk is not None: over['cap.k'] = args.skel_capk
        elif args.cap_a is not None: over['cap.k'] = args.cap_a
        # several single-move kicks; keep the cheapest rebuild (objective of the rebuilt circuit)
        k = None; changed = 0; ko = None
        for _ in range(args.tries):
            k1, ch1 = skel_kick(cur, wd, rng.randrange(1 << 30), args.skel_iters, args.cap_ad, over)
            if k1 is None: continue
            o1 = metrics(k1)[2]
            if ko is None or o1 < ko: k, changed, ko = k1, ch1, o1
        if k is None or ko - cm[2] > args.max_penalty:
            hist.append({'cycle': cyc, 'kick': None if k is None else metrics(k)}); continue
        nk += 1
        km = metrics(k)
        left = args.seconds - (time.time() - t0)
        if left < 2: break
        p = polish(k, wd, 'p%d' % (cyc % 2), args.seed * 1000 + cyc, min(args.polish, left), args)
        pm = metrics(p); po = obj_of(pm, w, caps)
        acc = po <= co + 1e-9 or (args.temp > 0 and rng.random() < math.exp(-(po - co) / args.temp))
        hist.append({'t': round(time.time() - t0, 1), 'cycle': cyc, 'changed': changed, 'kicked': km,
                     'polished': pm, 'accepted': acc})
        if acc: cur, cm, co = p, pm, po
        if po < bo - 1e-9:
            best, bm, bo = p, pm, po
            bests.append({'t': round(time.time() - t0, 2), 'cycle': cyc, 'metrics': bm})
            (out / (args.tag + '.best.bfx')).write_text(core.to_kernel(best))
            print('best t %.1f cycle %d %s' % (time.time() - t0, cyc, bm), flush=True)
    (out / (args.tag + '.best.bfx')).write_text(core.to_kernel(best))
    rec = {'tag': args.tag, 'arm': 'kick', 'start': args.start, 'start_metrics': metrics(start), 'seed': args.seed,
           'seconds': args.seconds, 'polish': args.polish, 'skel_iters': args.skel_iters, 'caps': caps,
           'objective': args.objective, 'core_ok': correct(best), 'metrics': bm, 'cycles': cyc, 'kicks': nk,
           'improvements': [{'t': b['t'], 'mv': 'kick' if b['cycle'] else 'polish0', 'G': b['metrics'][2]} for b in bests],
           'history': hist, 'stats': {}, 'command': ' '.join(sys.argv)}
    (out / (args.tag + '.json')).write_text(json.dumps(rec, indent=1) + '\n')
    print(json.dumps({'tag': args.tag, 'metrics': bm, 'cycles': cyc, 'kicks': nk}))


if __name__ == '__main__':
    main()
