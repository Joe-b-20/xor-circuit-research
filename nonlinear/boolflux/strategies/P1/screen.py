#!/usr/bin/env python3
"""P1 systematic screen: one kernel run per start at the target caps, then long polishes of the best.

    python3 screen.py --target T03 --data DIR --name scr11 --starts starts.json --ref reftuples.json \
        --sel 'AD<=5,G<=131,GD>=21' --cap 20 --sec 60 --top 8 --polish-sec 300 --seed 7

Phase 1: every selected start (distinct circuit) -> kernel caps (A 28, AD target AD, GD cap), --sec s.
Phase 2: the --top best distinct outputs (by G, GD) -> two chained kernel runs of --polish-sec s at
the same caps, two seeds each.  Every output is verified (hub common.verify) and logged; outputs not
dominated by the reference tuples go to DATA/found/ with the BRIEF sidecar (via p1run.Worker.save_front).
Hard limits: start must satisfy A <= 28, AD <= target AD; every kernel call has caps A 28 and AD.
"""
import argparse
import json
import os
import random
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p1run   # noqa: E402
from p1run import core, metrics, verify, HO, cid   # noqa: E402


def sel_ok(m, sel):
    names = {'A': m[0], 'AD': m[1], 'G': m[2], 'GD': m[3]}
    for cond in sel.split(','):
        for op in ('<=', '>=', '=='):
            if op in cond:
                k, v = cond.split(op); x = names[k.strip()]; v = int(v)
                if (op == '<=' and not x <= v) or (op == '>=' and not x >= v) or (op == '==' and x != v): return False
                break
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--target', required=True); ap.add_argument('--data', required=True)
    ap.add_argument('--name', required=True); ap.add_argument('--starts', required=True)
    ap.add_argument('--ref', required=True); ap.add_argument('--sel', required=True)
    ap.add_argument('--cap', type=int, required=True); ap.add_argument('--sec', type=float, default=60)
    ap.add_argument('--top', type=int, default=8); ap.add_argument('--polish-sec', type=float, default=300)
    ap.add_argument('--seed', type=int, default=7); ap.add_argument('--extra', action='append', default=[])
    a = ap.parse_args()
    # reuse the worker's admission / saving machinery (pool, shared dir, found/ sidecars)
    wa = argparse.Namespace(target=a.target, seed=a.seed, hours=0, data=a.data, name=a.name, starts=a.starts,
                            ops='polish', gslack=12, gdslack=8, deep_sec=0, ref=a.ref)
    W = p1run.Worker(wa)
    rng = random.Random(a.seed)
    rows = [r for r in json.loads(Path(a.starts).read_text()) if sel_ok((r['A'], r['AD'], r['G'], r['GD']), a.sel)]
    for ex in a.extra:            # extra start files (e.g. found/ circuits of this campaign)
        for p in sorted(Path(ex).glob('*.circ.txt')) + sorted(Path(ex).glob('*.bfx')):
            t = p.read_text(); c = core.from_kernel(t) if p.suffix == '.bfx' else core.read_ncff(t); m = metrics(c)
            if sel_ok(m, a.sel):
                import hashlib
                rows.append({'A': m[0], 'AD': m[1], 'G': m[2], 'GD': m[3], 'path': str(p),
                             'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
    rows.sort(key=lambda r: (r['G'], r['GD']))
    W.emit({'event': 'screen_start', 'argv': sys.argv, 'n': len(rows)})
    res = []
    caps = W.caps(a.cap)
    for j, r in enumerate(rows):
        t = Path(r['path']).read_text()
        c = core.from_kernel(t) if r['path'].endswith('.bfx') else core.read_ncff(t)
        m = metrics(c)
        if not W.legal(m): continue
        lin = {'root': r['path'], 'root_sha256': r['sha256'], 'root_m': m, 'chain': []}
        W.ks = []
        t0 = time.time()
        x = W.kernel(c, caps, a.sec, 'scr')
        step = {'op': 'screen', 'worker': a.name, 'steps': list(W.ks)}
        nl = dict(lin, chain=[step])
        mx = metrics(x) if x else None
        adm = W.admit(x, 'screen(%s)' % r['path'], nl) if x else None
        W.emit({'screen': j, 'start': r['path'], 'm0': m, 'out': mx, 'adm': adm, 'wall': round(time.time() - t0, 1),
                'kernel': W.ks})
        if x is not None and mx[3] <= a.cap: res.append((mx[2], mx[3], j, x, nl))
    res.sort(key=lambda z: (z[0], z[1]))
    seen = set(); top = []
    for z in res:
        k = cid(z[3])
        if k in seen: continue
        seen.add(k); top.append(z)
        if len(top) >= a.top: break
    W.emit({'event': 'screen_phase1_done', 'top': [(z[0], z[1], z[2]) for z in top]})
    for G, GD, j, x, nl in top:
        for s in range(2):
            cur = x; chain = list(nl['chain'])
            for k in range(2):
                W.ks = []
                y = W.kernel(cur, caps, a.polish_sec, 'pol')
                if y is None: break
                chain = chain + [{'op': 'screen-polish', 'worker': a.name, 'steps': list(W.ks)}]
                adm = W.admit(y, 'screen-polish', dict(nl, chain=chain))
                W.emit({'polish': j, 'rep': s, 'k': k, 'in': metrics(cur), 'out': metrics(y), 'adm': adm, 'kernel': W.ks})
                cur = y
    W.emit({'event': 'screen_done'})


if __name__ == '__main__':
    main()
