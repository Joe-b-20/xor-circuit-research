#!/usr/bin/env python3
"""Front walk (goal D): re-optimise the front of a back donor Y (signals of AND level <= LY) as a separate
multi-output circuit whose outputs are Y's cut signals, under PER-OUTPUT gate-depth deadlines (Y's
required times for cap D; bfx_dl = kernel + output offsets), A cap = #front ANDs, AD cap = LY; every
kernel result is joined back in front of Y's back (hub/join.join, cut found by truth table) and the
complete circuit is measured; goal-meeting circuits are checked with aes_check.py and saved to FOUND.

  frontwalk.py --y Y --ly 1 --cap 19 --starts F1 [F2 ...] (circuits containing the cut functions)
               --job-s 120 --total-s 3600 --out DIR --goal 32,4,116,19 --found DIR [--archive DIR] [--seed S]
"""
import argparse
import hashlib
import json
import random
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2])); sys.path.insert(0, str(HERE))
from boolflux.hub.common import core, metrics, targets, code_version  # noqa: E402
from boolflux.hub import join as J  # noqa: E402
import front as FR  # noqa: E402
import walk as WK  # noqa: E402


def front_from(c, cut_tabs):
    """front circuit (outputs = signals of c with the cut truth tables) or None"""
    t = c.tables(); idx = {}
    for s in range(c.n + len(c.gates) - 1, -1, -1): idx[t[s]] = s
    outs = []
    for tt in cut_tabs:
        if tt not in idx: return None
        outs.append(idx[tt])
    return core.Circuit(c.n, len(outs), list(c.gates), outs).live()


def out_levels(f):
    gl = [0] * f.n
    for op, a, b in f.gates: gl.append(1 + max(gl[a], gl[b]))
    return [gl[o] for o in f.outputs]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--y', required=True); ap.add_argument('--ly', type=int, default=1)
    ap.add_argument('--cap', type=int, required=True); ap.add_argument('--starts', nargs='+', required=True)
    ap.add_argument('--archive'); ap.add_argument('--job-s', type=float, default=120)
    ap.add_argument('--total-s', type=float, default=3600); ap.add_argument('--out', required=True)
    ap.add_argument('--goal', required=True); ap.add_argument('--found', required=True)
    ap.add_argument('--seed', type=int, default=1); ap.add_argument('--slack', type=int, default=0,
                    help='extra levels added to every deadline (explore, then judge the joined circuit)')
    a = ap.parse_args()
    goal = tuple(int(x) for x in a.goal.split(','))
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True); found = Path(a.found); found.mkdir(parents=True, exist_ok=True)
    kb = HERE / 'bfx_dl'
    Y = FR.load(a.y, a.archive); need, gl, req, lv = FR.cut(Y, a.ly, a.cap)
    ty = Y.tables(); cut_tabs = [ty[s] for s in need]
    dl = [req[s] + a.slack for s in need]
    D = max(dl); off = [D - d for d in dl]
    YP = J.Prepared(Y, 'Y')
    pool = []
    for s in a.starts:
        f = front_from(FR.load(s, a.archive), cut_tabs)
        if f is None: print('no cut in', s); continue
        pool.append((s, f))
    assert pool
    nA = sum(1 for op, x, y in pool[0][1].gates if op == 8)
    caps = (nA, a.ly, D)
    extra = {'outoff': ','.join(map(str, off))}
    rng = random.Random(a.seed); log = open(out / 'log.jsonl', 'a')
    log.write(json.dumps({'event': 'start', 'argv': sys.argv, 'deadlines': dl, 'caps': caps, 'code_version': code_version(),
                          'starts': [(s, metrics(f), max(l - d for l, d in zip(out_levels(f), dl))) for s, f in pool]}) + '\n')
    elite = {core.to_kernel(f): ((max(l - d for l, d in zip(out_levels(f), dl)) > 0, len(f.gates)), s) for s, f in pool}
    t0 = time.time(); it = 0
    while time.time() - t0 < a.total_s - 15:
        it += 1
        items = sorted(elite.items(), key=lambda kv: kv[1][0])
        topk = items[0][1][0]; top = [kv for kv in items if kv[1][0] == topk]
        k0 = rng.choice(top)[0] if rng.random() < 0.8 else rng.choice(items)[0]
        f = core.from_kernel(k0, 'f')
        seed = a.seed * 100000 + it
        res, t_imp = WK.run_kernel(kb, f, caps, 'cost', seed, min(a.job_s, a.total_s - (time.time() - t0)), out / 'job', extra)
        rec = {'it': it, 'seed': seed, 'start_g': len(f.gates)}
        if res is None: log.write(json.dumps(rec) + '\n'); log.flush(); continue
        exc = max(l - d for l, d in zip(out_levels(res), dl))
        rec.update({'front_g': len(res.gates), 'front_excess': exc})
        if exc <= 0:
            k = core.to_kernel(res)
            if k not in elite: elite[k] = ((False, len(res.gates)), 'it%d' % it)
            j, nint = J.join(J.Prepared(res, 'F').front(a.ly), YP, a.ly)
            if j is not None and j.value_table() == targets.aes_sbox():
                m = metrics(j); rec['joined'] = m; rec['nint'] = nint
                if all(v <= g for v, g in zip(m, goal)):
                    kk = core.to_kernel(j); h = hashlib.sha1(kk.encode()).hexdigest()[:12]
                    p = found / ('T2-front-a%d-ad%d-g%d-gd%d-%s.bfx' % (m + (h,)))
                    if not p.exists():
                        p.write_text(kk); ok, txt = WK.aes_check(p)
                        (found / (p.stem + '.json')).write_text(json.dumps({
                            'file': p.name, 'metrics': dict(zip(('A', 'AD', 'G', 'GD'), m)), 'aes_check_ok': ok, 'aes_check': txt,
                            'method': 'T2 frontwalk.py: front of Y re-optimised by bfx_dl under per-output deadlines, joined to Y back',
                            'Y': a.y, 'LY': a.ly, 'cap': a.cap, 'seed': seed, 'job': it, 'argv': sys.argv,
                            'code_version': code_version(), 'time_utc': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}, indent=1))
                        print('FOUND', p, ok, flush=True); rec['found'] = p.name
        log.write(json.dumps(rec) + '\n'); log.flush()
        print(it, rec, flush=True)


if __name__ == '__main__':
    main()
