#!/usr/bin/env python3
"""Breathe cycles: windows shrink G with the gate-depth cap relaxed to D+relax, then the gate
kernel repairs the depth back to D (penalised repair, then annealing), then windows polish at D.

    python3 breathe.py --start FILE --out DIR --cap-gd D [--cap-a A] [--cap-ad AD] --hours H
           [--relax 1] [--t-relax 300] [--t-kernel 300] [--t-polish 120] [--seed 1]

Keeps the best circuit within the caps (lexicographic G, A); each cycle starts from the best or,
with probability --p-cur, from the last cycle's result.  Logs DIR/breathe.jsonl.
"""
import argparse
import json
import random
import subprocess
import sys
import time
from pathlib import Path

import kern
import wresyn as R
from boolflux import core

HERE = Path(__file__).resolve().parent
MODEL = core.Model.load('nist')


def win_run(start_path, out, seconds, seed, cap_gd, cap_ad, cap_a, extra=()):
    cmd = [sys.executable, str(HERE / 'run.py'), '--start', str(start_path), '--out', str(out),
           '--seconds', str(seconds), '--seed', str(seed), '--cap-gd', str(cap_gd),
           '--cap-ad', str(cap_ad), '--cap-a', str(cap_a)] + list(extra)
    subprocess.run(cmd, capture_output=True, text=True, timeout=seconds + 600)
    return core.read_ncff(str(Path(out) / 'cur.circ.txt'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--cap-gd', type=int, required=True)
    ap.add_argument('--cap-a', type=int)
    ap.add_argument('--cap-ad', type=int)
    ap.add_argument('--hours', type=float, default=1.0)
    ap.add_argument('--relax', type=int, default=1)
    ap.add_argument('--t-relax', type=float, default=300)
    ap.add_argument('--t-kernel', type=float, default=300)
    ap.add_argument('--t-polish', type=float, default=120)
    ap.add_argument('--p-cur', type=float, default=0.5)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--win-args', default='')
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    start = core.read_ncff(args.start).live()
    assert R.correct(start)
    m0 = start.metrics()
    D = args.cap_gd
    A = args.cap_a if args.cap_a is not None else m0['A']
    AD = args.cap_ad if args.cap_ad is not None else m0['AD']
    best = start
    bm = m0
    last = start
    t0 = time.time()
    logf = open(out / 'breathe.jsonl', 'a')
    extra = args.win_args.split()

    def log(d):
        d['t'] = round(time.time() - t0, 1)
        logf.write(json.dumps(d) + '\n')
        logf.flush()

    log({'event': 'start', 'args': vars(args), 'metrics': [m0['G'], m0['A'], m0['GD'], m0['AD']]})
    cyc = 0
    while time.time() - t0 < args.hours * 3600:
        cyc += 1
        base = last if rng.random() < args.p_cur else best
        cd = out / ('c%03d' % cyc)
        cd.mkdir(exist_ok=True)
        bp = cd / 'base.circ.txt'
        bp.write_text(core.write_ncff(base, MODEL), encoding='utf-8')
        seed = rng.randrange(1 << 30)
        # 1. relaxed window shrink
        X = win_run(bp, cd / 'relax', args.t_relax, seed, D + args.relax, AD, A, extra)
        mx = X.metrics()
        # 2. kernel repair + anneal at D
        Y, _ = kern.kernel(X, cd, 'kern', args.t_kernel, seed, cap_gd=D, cap_ad=AD, cap_a=A)
        my = Y.metrics()
        rec = {'event': 'cycle', 'cyc': cyc, 'seed': seed, 'base': [base.metrics()[k] for k in ('G', 'A', 'GD', 'AD')],
               'relaxed': [mx[k] for k in ('G', 'A', 'GD', 'AD')], 'kernel': [my[k] for k in ('G', 'A', 'GD', 'AD')]}
        if my['GD'] <= D and my['A'] <= A and my['AD'] <= AD and R.correct(Y):
            yp = cd / 'kern.circ.txt'
            yp.write_text(core.write_ncff(Y, MODEL), encoding='utf-8')
            Z = win_run(yp, cd / 'polish', args.t_polish, seed + 1, D, AD, A, extra)
            mz = Z.metrics()
            rec['polish'] = [mz[k] for k in ('G', 'A', 'GD', 'AD')]
            if R.correct(Z) and mz['GD'] <= D and mz['A'] <= A and mz['AD'] <= AD:
                last = Z
                if (mz['G'], mz['A']) < (bm['G'], bm['A']):
                    best, bm = Z, mz
                    name = 'best-g%d-a%d-gd%d-ad%d' % (mz['G'], mz['A'], mz['GD'], mz['AD'])
                    (out / (name + '.circ.txt')).write_text(
                        core.write_ncff(Z, MODEL, comments=['track D breathe cycle %d from %s' % (cyc, Path(args.start).name)]),
                        encoding='utf-8')
                    (out / (name + '.json')).write_text(json.dumps({
                        'start': str(Path(args.start).resolve()), 'command': ' '.join(sys.argv), 'seed': args.seed,
                        'cycle': cyc, 'cycle_seed': seed, 'cycle_dir': str(cd), 'time_to_result_s': round(time.time() - t0, 1),
                        'metrics': [mz[k] for k in ('G', 'A', 'GD', 'AD')]}, indent=1) + '\n', encoding='utf-8')
                    rec['new_best'] = True
        log(rec)
    log({'event': 'end', 'best': [bm[k] for k in ('G', 'A', 'GD', 'AD')]})


if __name__ == '__main__':
    main()
