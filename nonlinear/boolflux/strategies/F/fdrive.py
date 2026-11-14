#!/usr/bin/env python3
"""Track-F driver: one search job on one CPU, a schedule of stages, wall budget, JSONL log.

    python3 fdrive.py --start FILE --cap 14 --cap-ad 4 --mode MODE --seconds 3600 --seed 1 \
        --out DIR [--stage-iters 200000] [--relax 1]

Modes
  gate     plain gate kernel under the hard caps, restarted from the job's best every stage
           (the baseline: same kernel, same CPU time)
  osc      depth oscillation: kernel under cap D+relax (gates may drop, depth rises), then the
           kernel's penalised repair back to cap D, then the kernel under cap D; repeat
  trb      timing-driven regional rebuild (trb.py) of a random linear region of the best
           circuit within exact required levels for cap D (stays feasible), then kernel under D
  mix      alternate gate / osc / trb stages

Every stage's output is read back and checked on all 256 inputs; the best feasible circuit
(G, then GD) is kept in OUT/best.circ.txt; improvements are logged with wall time.
"""
import argparse
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2])); sys.path.insert(0, str(HERE))
from boolflux import core, targets   # noqa: E402

AESTAB = targets.aes_sbox()
MODEL = core.Model.load(str(core.MODELS / 'nist.json'))
SNAP = Path.home() / 'xs-campaigns/2026-11-13-aes/F/snap/boolflux'
BFX = Path(os.environ.get('F_BFX', str(SNAP / 'kernel' / 'bfx')))
DEFAULTS = {'T0': 0.6, 'Tperiod_it': 20000, 'stall_it': 60000, 'uphill': 1.0, 'max_excess': 8,
            'mv.resub1': 1, 'mv.resub2': 2, 'mv.resub3': 1, 'dmax': 220, 'pdiv': 90,
            'nl_samples': 12, 'cand_cap': 40, 'fraig': 1, 'w.cost': 1.0, 'w.g': 0.0, 'w.a': 0.0,
            'w.gd': 1e-4, 'w.ad': 0.0}


CAP_A = None


def metrics(c):
    m = c.metrics(MODEL); return m['G'], m['A'], m['GD'], m['AD']


def kernel(c, wd, tag, cap_gd, cap_ad, iters, seed, extra=None, seconds=3600):
    cfg = dict(DEFAULTS)
    for op, v in MODEL.cost.items(): cfg['cost.%d' % op] = v
    cfg['cap.gd'] = cap_gd
    if cap_ad is not None: cfg['cap.ad'] = cap_ad
    if CAP_A is not None: cfg['cap.a'] = CAP_A
    if extra: cfg.update(extra)
    if os.environ.get("F_LEX"): cfg["lex"] = os.environ["F_LEX"]
    sp = wd / ('%s.in' % tag); op_ = wd / ('%s.out' % tag); cp = wd / ('%s.cfg' % tag)
    sp.write_text(core.to_kernel(c))
    cfg.update({'in': sp, 'out': op_, 'seed': seed, 'iters': iters, 'seconds': seconds})
    cp.write_text(''.join('%s %s\n' % kv for kv in cfg.items()))
    r = subprocess.run([str(BFX), str(cp)], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError('bfx failed: ' + (r.stdout + r.stderr)[-600:])
    out = core.from_kernel(op_.read_text())
    for p in (sp, op_, cp):
        try: p.unlink()
        except OSError: pass
    return out, r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', required=True); ap.add_argument('--cap', type=int, required=True)
    ap.add_argument('--cap-ad', type=int, default=4); ap.add_argument('--mode', default='gate')
    ap.add_argument('--seconds', type=float, default=3600); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--stage-iters', type=int, default=200000); ap.add_argument('--relax', type=int, default=1)
    ap.add_argument('--repair-iters', type=int, default=100000)
    ap.add_argument('--trb-regions', default='bottom,top,mid,random')
    ap.add_argument('--cap-a', type=int, default=None)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    global CAP_A
    CAP_A = a.cap_a
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    wd = out / 'work'; wd.mkdir(exist_ok=True)
    rng = random.Random(a.seed)
    start = core.read_ncff(a.start)
    assert start.value_table() == AESTAB
    D = a.cap
    feas = lambda c: metrics(c)[2] <= D and metrics(c)[3] <= a.cap_ad and (a.cap_a is None or metrics(c)[1] <= a.cap_a)
    key = lambda c: (0 if feas(c) else 1, metrics(c)[0], metrics(c)[2])
    best = start; cur = start
    log = open(out / 'log.jsonl', 'a')
    T0 = time.time()
    def note(kind, c, stage, extra=None):
        G, A, GD, AD = metrics(c)
        rec = {'t': round(time.time() - T0, 2), 'kind': kind, 'stage': stage, 'G': G, 'A': A, 'GD': GD, 'AD': AD}
        if extra: rec.update(extra)
        log.write(json.dumps(rec) + '\n'); log.flush()
    note('start', start, 0, {'file': a.start, 'mode': a.mode, 'cap': D, 'seed': a.seed,
                            'bfx': str(BFX), 'lex': os.environ.get('F_LEX', '')})
    def offer(c, stage, how):
        nonlocal best
        if c.value_table() != AESTAB: raise RuntimeError('wrong function after ' + how)
        if key(c) < key(best):
            best = c
            (out / 'best.circ.txt').write_text(core.write_ncff(c, MODEL, comments=[
                'track F fdrive mode %s seed %d stage %d (%s) t=%.1f s' % (a.mode, a.seed, stage, how, time.time() - T0)]))
            note('best', c, stage, {'how': how})
    if feas(start):
        (out / 'best.circ.txt').write_text(core.write_ncff(start, MODEL))
    stage = 0
    while time.time() - T0 < a.seconds - 1:
        stage += 1
        rem = a.seconds - (time.time() - T0)
        kseed = a.seed * 100000 + stage
        mode = a.mode
        if mode == 'mix': mode = ['gate', 'osc', 'trb'][stage % 3]
        base = best if feas(best) else cur
        if mode == 'fresh':          # short independent restarts from the start (track D finding)
            base = start; mode = 'gate'
        if mode == 'gate':
            c, _ = kernel(base, wd, 's%d' % stage, D, a.cap_ad, a.stage_iters, kseed, seconds=rem)
            note('stage-gate', c, stage)      # logging only
            offer(c, stage, 'gate'); cur = c
        elif mode == 'osc':
            c1, _ = kernel(base, wd, 's%da' % stage, D + a.relax, a.cap_ad, a.stage_iters // 2, kseed, seconds=rem / 2)
            note('osc-relaxed', c1, stage)
            rem = a.seconds - (time.time() - T0)
            c2, _ = kernel(c1, wd, 's%db' % stage, D, a.cap_ad, a.repair_iters, kseed + 7, seconds=max(1, rem))
            note('osc-repaired', c2, stage)
            offer(c2, stage, 'osc-repair')
            if feas(c2):
                rem = a.seconds - (time.time() - T0)
                c3, _ = kernel(c2, wd, 's%dc' % stage, D, a.cap_ad, a.stage_iters // 2, kseed + 13, seconds=max(1, rem))
                offer(c3, stage, 'osc-gate'); cur = c3
            else:
                cur = c2
        elif mode == 'trb':
            import trb
            reg = rng.choice(a.trb_regions.split(','))
            c1, info = trb.rebuild(base, D, reg, rng)
            note('trb', c1, stage, {'region': reg, **info})
            rem = a.seconds - (time.time() - T0)
            c2, _ = kernel(c1, wd, 's%d' % stage, D, a.cap_ad, a.stage_iters, kseed, seconds=max(1, rem))
            offer(c2, stage, 'trb-%s' % reg); cur = c2
    note('end', best, stage)


if __name__ == '__main__':
    main()
