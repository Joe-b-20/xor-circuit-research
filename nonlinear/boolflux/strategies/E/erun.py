#!/usr/bin/env python3
"""Run one Track-E kernel job (control or chain arm) from a start circuit; record a JSON sidecar.

    python3 erun.py --start FILE --out DIR --tag TAG --seed S --seconds T [--cap-a A --cap-ad AD --cap-gd GD]
                    [--objective cost,gd] [--arm control|chain] [--set key=value ...] [--bin PATH]
"""
import argparse, json, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import core, load, metrics, correct, MODEL   # noqa: E402

DEFAULTS = {'T0': 0.6, 'Tperiod_it': 20000, 'stall_it': 60000, 'uphill': 1.0, 'max_excess': 8,
            'mv.resub1': 1, 'mv.resub2': 2, 'mv.resub3': 1, 'dmax': 220, 'pdiv': 90,
            'nl_samples': 12, 'cand_cap': 40, 'fraig': 1}
CHAIN = {'chain': 0.15, 'chain_up': 2, 'chain_and': 0.5, 'chain_k': 6, 'chain_targets': 12, 'chain_rup': 1}
OBJ_KEYS = {'cost': 'w.cost', 'g': 'w.g', 'a': 'w.a', 'gd': 'w.gd', 'ad': 'w.ad'}


def weights(spec):
    w = {v: 0.0 for v in OBJ_KEYS.values()}
    for i, k in enumerate(spec.split(',')):
        w[OBJ_KEYS[k.strip()]] += 10.0 ** (-4 * i)
    w['lex'] = ','.join(k.strip() for k in spec.split(','))
    return w


def parse_log(text):
    bests = []; final = {}; extra = {}
    for ln in text.splitlines():
        t = ln.split()
        if not t: continue
        if t[0] == 'best':
            d = {t[i]: t[i + 1] for i in range(1, len(t) - 1, 2)}
            bests.append({'t': float(d['t']), 'it': int(d['it']), 'mv': d['mv'], 'G': int(d['G']), 'A': int(d['A']),
                          'GD': int(d['GD']), 'AD': int(d['AD']), 'cost': float(d['cost'])})
        elif t[0] == 'final':
            final = {t[i]: float(t[i + 1]) for i in range(1, len(t) - 1, 2)}
        elif t[0] in ('chain', 'move'):
            key = t[0] if t[0] == 'chain' else 'move_' + t[1]
            off = 1 if t[0] == 'chain' else 2
            extra[key] = {t[i]: float(t[i + 1]) for i in range(off, len(t) - 1, 2)}
    return bests, final, extra


def run(args):
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    start = load(args.start)
    assert correct(start), 'start is not the AES S-box'
    sp = out / (args.tag + '.start.bfx'); sp.write_text(core.to_kernel(start))
    bp = out / (args.tag + '.best.bfx'); cp = out / (args.tag + '.cfg'); lp = out / (args.tag + '.log')
    cfg = dict(DEFAULTS); cfg.update(weights(args.objective))
    for op, c in MODEL.cost.items(): cfg['cost.%d' % op] = c
    if args.arm == 'chain':
        cfg.update(CHAIN); cfg.pop('lex', None)
        if args.bin.endswith('bfx_new'): args.bin = str(HERE / 'bfx_e')
    for k, v in (('cap.a', args.cap_a), ('cap.ad', args.cap_ad), ('cap.gd', args.cap_gd)):
        if v is not None: cfg[k] = v
    for s in args.set or []:
        k, v = s.split('=', 1); cfg[k] = v
    cfg.update({'in': sp, 'out': bp, 'seed': args.seed, 'seconds': args.seconds})
    cp.write_text(''.join('%s %s\n' % kv for kv in cfg.items()))
    t0 = time.time()
    with open(lp, 'w') as lf:
        r = subprocess.run([args.bin, str(cp)], stdout=lf, stderr=subprocess.STDOUT)
    wall = time.time() - t0
    bests, final, extra = parse_log(lp.read_text())
    c = core.from_kernel(bp.read_text(), args.tag)
    ok = correct(c)
    rec = {'tag': args.tag, 'arm': args.arm, 'start': str(args.start), 'start_metrics': metrics(start),
           'seed': args.seed, 'seconds': args.seconds, 'caps': {'A': args.cap_a, 'AD': args.cap_ad, 'GD': args.cap_gd},
           'objective': args.objective, 'config': {k: str(v) for k, v in cfg.items()}, 'returncode': r.returncode,
           'core_ok': ok, 'metrics': metrics(c), 'wall_s': round(wall, 2), 'improvements': bests, 'final': final,
           'stats': extra, 'command': ' '.join(sys.argv)}
    (out / (args.tag + '.json')).write_text(json.dumps(rec, indent=1) + '\n')
    print(json.dumps({'tag': args.tag, 'metrics': rec['metrics'], 'ok': ok, 'rc': r.returncode}))
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--tag', required=True); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--seconds', type=float, default=60)
    ap.add_argument('--cap-a', type=int); ap.add_argument('--cap-ad', type=int); ap.add_argument('--cap-gd', type=int)
    ap.add_argument('--objective', default='cost,gd')
    ap.add_argument('--arm', default='control', choices=['control', 'chain'])
    ap.add_argument('--set', action='append')
    ap.add_argument('--bin', default=str(HERE / 'bfx_new'))
    run(ap.parse_args())


if __name__ == '__main__':
    main()
