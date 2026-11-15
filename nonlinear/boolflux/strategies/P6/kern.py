#!/usr/bin/env python3
"""P6: kernel stage(s) on one start under hard caps (hub.ops._kernel), verified result.

    python3 kern.py START --caps A,AD,GD --objective cost,gd --seed S --seconds T --out DIR [--stages K]

Each stage restarts the kernel from the best so far (feasible-only once feasible).  Writes
DIR/best.bfx and DIR/kern.json (per stage metrics, caps, seeds, kernel binary).
"""
import sys, json, time, argparse
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core                                   # noqa: E402
from boolflux.hub.common import verify, metrics, load, clean  # noqa: E402
from boolflux.hub import ops as O                           # noqa: E402
O.KDEFAULTS['repair_keep'] = 1   # compliance 18:20: no move may raise any single cap excess (A/AD stay hard)


def better(m, b, caps):
    feas = lambda x: x[0] <= caps['A'] and x[1] <= caps['AD'] and x[3] <= caps['GD']
    if feas(m) != feas(b): return feas(m)
    return (m[2], m[3]) < (b[2], b[3]) if feas(m) else (m[3], m[2]) < (b[3], b[2])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('start'); ap.add_argument('--caps', required=True)
    ap.add_argument('--objective', default='cost,gd'); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--seconds', type=float, default=120); ap.add_argument('--stages', type=int, default=1)
    ap.add_argument('--out', required=True); ap.add_argument('--bindir', default=str(Path.home() / 'xs-campaigns/2026-11-15-targets/P6/kbin'))
    ap.add_argument('--cfg', nargs='*', default=[], help='kernel setting overrides KEY=VALUE (hub.ops.KDEFAULTS)')
    a = ap.parse_args()
    for kv in a.cfg:
        k, v = kv.split('=', 1); O.KDEFAULTS[k] = float(v) if '.' in v else int(v)
    A, AD, GD = [int(x) for x in a.caps.split(',')]
    caps = {'A': A, 'AD': AD, 'GD': GD}
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    cur = load(a.start); cm = metrics(cur); t0 = time.time()
    rec = {'start': str(Path(a.start).resolve()), 'start_m': cm, 'caps': caps, 'objective': a.objective,
           'seed': a.seed, 'seconds': a.seconds, 'stages': [], 'cfg': a.cfg}
    print('start', cm, flush=True)
    for st in range(a.stages):
        sd = out / ('s%d' % st); sd.mkdir(exist_ok=True)
        cands, info = O._kernel(cur, caps, a.objective, a.seed + 1000 * st, a.seconds, sd, a.bindir)
        got = None
        for nc in cands:
            nc = clean(nc); ok, inf = verify(nc)
            if not ok: print('verify fail', inf); continue
            m = metrics(nc)
            if m[0] > A or m[1] > AD: continue      # hard caps on every retained state
            if better(m, cm, caps) or m == cm:
                got = (nc, m)
        rec['stages'].append({'stage': st, 'm': got[1] if got else None, 't': round(time.time() - t0, 1),
                              'kernel_bin': info.get('kernel_bin'), 't_last': info.get('t_last_improvement')})
        if got and better(got[1], cm, caps):
            cur, cm = got
            (out / 'best.bfx').write_text(core.to_kernel(cur))
        print('stage', st, 'best', cm, 'elapsed %.0f' % (time.time() - t0), flush=True)
        json.dump(rec, open(out / 'kern.json', 'w'), indent=1)
    rec['best_m'] = cm; rec['elapsed_s'] = round(time.time() - t0, 1)
    if not (out / 'best.bfx').exists(): (out / 'best.bfx').write_text(core.to_kernel(cur))
    json.dump(rec, open(out / 'kern.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
