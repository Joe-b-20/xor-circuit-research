#!/usr/bin/env python3
"""Control for breathe.py: the gate kernel alone (same copy, caps, lex cost,a,gd) from the same
start for the same wall time, as consecutive kernel runs restarted from the best.

    python3 control.py --start FILE --out DIR --cap-gd D --seconds S [--chunk 300] [--seed 1]
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

import kern
import wresyn as R
from boolflux import core

MODEL = core.Model.load('nist')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--cap-gd', type=int, required=True)
    ap.add_argument('--seconds', type=float, required=True)
    ap.add_argument('--chunk', type=float, default=300)
    ap.add_argument('--seed', type=int, default=1)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(a.seed)
    best = core.read_ncff(a.start).live()
    m0 = best.metrics()
    A, AD = m0['A'], m0['AD']
    bm = m0
    t0 = time.time()
    logf = open(out / 'control.jsonl', 'a')
    k = 0
    while time.time() - t0 < a.seconds:
        k += 1
        sec = min(a.chunk, max(10, a.seconds - (time.time() - t0)))
        seed = rng.randrange(1 << 30)
        Y, _ = kern.kernel(best, out, 'k%03d' % k, sec, seed, cap_gd=a.cap_gd, cap_ad=AD, cap_a=A)
        my = Y.metrics()
        ok = R.correct(Y) and my['GD'] <= a.cap_gd and my['A'] <= A and my['AD'] <= AD
        rec = {'chunk': k, 'seed': seed, 'result': [my[x] for x in ('G', 'A', 'GD', 'AD')], 'ok': ok,
               't': round(time.time() - t0, 1)}
        if ok and (my['G'], my['A']) < (bm['G'], bm['A']):
            best, bm = Y, my
            name = 'best-g%d-a%d-gd%d-ad%d' % (my['G'], my['A'], my['GD'], my['AD'])
            (out / (name + '.circ.txt')).write_text(core.write_ncff(Y, MODEL), encoding='utf-8')
            (out / (name + '.json')).write_text(json.dumps({'start': a.start, 'command': ' '.join(sys.argv),
                                                            'chunk': k, 'seed': seed, 'time_to_result_s': rec['t']}) + '\n')
            rec['new_best'] = True
        logf.write(json.dumps(rec) + '\n')
        logf.flush()
    logf.write(json.dumps({'event': 'end', 'best': [bm[x] for x in ('G', 'A', 'GD', 'AD')]}) + '\n')


if __name__ == '__main__':
    main()
