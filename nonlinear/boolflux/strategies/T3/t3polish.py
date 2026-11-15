#!/usr/bin/env python3
"""T3: G-first kernel descents under hard caps, with a local pool (chained descents).

    t3polish.py --out DIR --starts F1 F2 ... [--caps 35,3,26] [--objective cost,gd]
                [--seconds 300] [--hours H] [--seed S] [--pool-gd 20-26]

Loop: pick a start from the pool (initial starts + every improved circuit kept per GD value),
run the repo gate kernel (hub.ops._kernel, private binary in DIR/bin) with the caps, verify the
result (hub.common.verify: core + independent verifier), log a jsonl line, keep it in the pool if it
lowers G at its GD (or ties with a new structure, up to 4 per GD), and write any circuit meeting
the target (default A<=35, AD<=3, G<=138, GD<=26) to DIR/found/ with a JSON sidecar.
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core                       # noqa: E402
from boolflux.hub import ops as O               # noqa: E402
from boolflux.hub.common import verify, metrics, code_version, cid, load   # noqa: E402

MODEL = core.Model.load('nist')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--starts', nargs='+', required=True)
    ap.add_argument('--caps', default='35,3,26')
    ap.add_argument('--target', default='35,3,138,26')
    ap.add_argument('--objective', default='cost,gd')
    ap.add_argument('--seconds', type=float, default=300)
    ap.add_argument('--hours', type=float, default=1.0)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--keep', type=int, default=4)
    ap.add_argument('--kset', default='', help='extra kernel settings k=v,k=v')
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    (out / 'found').mkdir(exist_ok=True); (out / 'pool').mkdir(exist_ok=True)
    capA, capAD, capGD = (int(x) for x in args.caps.split(','))
    tA, tAD, tG, tGD = (int(x) for x in args.target.split(','))
    caps = {'A': capA, 'AD': capAD, 'GD': capGD}
    rng = random.Random(args.seed)
    for kv in filter(None, args.kset.split(',')):
        k, v = kv.split('='); O.KDEFAULTS[k] = float(v) if '.' in v else int(v)
    pool = {}      # GD -> list of (G, id, circuit)
    for f in args.starts:
        c = load(f); m = metrics(c)
        pool.setdefault(m[3], []).append((m[2], cid(c), c, f))
    log = open(out / 'runs.jsonl', 'a')
    t_end = time.time() + 3600 * args.hours
    it = 0
    ver = code_version()
    while time.time() < t_end:
        it += 1
        # choose a start: half the time the min-G member over all GD values, else uniform
        allm = [x for v in pool.values() for x in v]
        if rng.random() < 0.5:
            gmin = min(x[0] for x in allm)
            cand = [x for x in allm if x[0] <= gmin + 1]
        else:
            cand = allm
        G0, id0, c0, src = rng.choice(cand)
        seed = rng.randrange(1 << 30)
        job = out / 'jobs' / ('%05d' % it); job.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        cands, info = O._kernel(c0, caps, args.objective, seed, args.seconds, job, out)
        rec = {'it': it, 'start': id0, 'start_src': src, 'start_m': metrics(c0), 'seed': seed, 'caps': caps,
               'objective': args.objective, 'seconds': args.seconds, 'wall': round(time.time() - t0, 1),
               't_last_improvement': info.get('t_last_improvement'), 'code': ver}
        if cands:
            c = cands[0]; m = metrics(c); rec['m'] = m
            ok, vinfo = verify(c); rec['ok'] = ok
            if ok and m[0] <= capA and m[1] <= capAD and m[3] <= capGD:
                lst = pool.setdefault(m[3], [])
                k = cid(c)
                if all(k != x[1] for x in lst):
                    gbest = min([x[0] for x in lst], default=999)
                    if m[2] <= gbest:
                        lst.append((m[2], k, c, 'it%d' % it)); lst.sort(key=lambda x: x[0])
                        del lst[args.keep:]
                        (out / 'pool' / ('a%d-ad%d-g%d-gd%d-%s.circ.txt' % (m + (k,)))).write_text(core.write_ncff(c, MODEL))
                        rec['pooled'] = True
                if m[0] <= tA and m[1] <= tAD and m[2] <= tG and m[3] <= tGD:
                    name = 'aes-sbox-a%d-ad%d-g%d-gd%d-%s' % (m + (k,))
                    (out / 'found' / (name + '.circ.txt')).write_text(core.write_ncff(c, MODEL))
                    (out / 'found' / (name + '.json')).write_text(json.dumps(
                        {'metrics': m, 'made_by': 'strategies/T3/t3polish.py (repo gate kernel, hub.ops._kernel)',
                         'start': src, 'start_metrics': metrics(c0), 'seed': seed, 'caps': caps,
                         'objective': args.objective, 'seconds': args.seconds, 'code_version': ver,
                         'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'verify': vinfo}, indent=1))
                    rec['found'] = name
        log.write(json.dumps(rec) + '\n'); log.flush()
        # keep job dirs small: drop the kernel log body
        try:
            (job / 'kernel.log').write_text('\n'.join((job / 'kernel.log').read_text().splitlines()[-20:]))
        except Exception:
            pass


if __name__ == '__main__':
    main()
