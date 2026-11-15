#!/usr/bin/env python3
"""P2 "skeleton pull" driver: relax -> skeleton rebuild -> polish.

Each round: kernel under cap D+relax from the current best (gates drop, depth rises); if the
relaxed circuit's AND-skeleton depth bound is <= D, rebuild it with T4's depthsynth reusing the
relaxed circuit's gates (parent mode; every form that is too slow becomes a Huffman tree), which
gives a GD <= D circuit with the relaxed circuit's AND functions; then kernel under cap D.
The best feasible circuit (G, then GD) under hard caps (A, AD, GD <= D) is kept in OUT/best.circ.txt.

    python3 sp.py --start FILE --cap D --cap-a A --cap-ad AD --seconds T --seed S --out DIR [--relax 1]
"""
import argparse
import json
import os
import random
import sys
import time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2])); sys.path.insert(0, str(HERE.parent / 'F')); sys.path.insert(0, str(HERE.parent / 'T4'))
import fdrive   # noqa: E402
import skeldepth   # noqa: E402
import dsynth   # noqa: E402
sys.path.insert(0, str(HERE))
import cover28   # noqa: E402
from boolflux import core, skeleton   # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', required=True); ap.add_argument('--cap', type=int, required=True)
    ap.add_argument('--cap-a', type=int, required=True); ap.add_argument('--cap-ad', type=int, default=4)
    ap.add_argument('--seconds', type=float, default=3600); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--relax', type=int, default=1); ap.add_argument('--iters', type=int, default=100000)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    fdrive.CAP_A = a.cap_a
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True); wd = out / 'work'; wd.mkdir(exist_ok=True)
    rng = random.Random(a.seed)
    start = core.read_ncff(a.start)
    assert start.value_table() == fdrive.AESTAB
    D = a.cap
    M = fdrive.metrics
    feas = lambda c: M(c)[2] <= D and M(c)[3] <= a.cap_ad and M(c)[1] <= a.cap_a
    best = start
    log = open(out / 'log.jsonl', 'a'); T0 = time.time()
    def note(kind, c, r, extra=None):
        G, A, GD, AD = M(c)
        rec = {'t': round(time.time() - T0, 2), 'kind': kind, 'round': r, 'G': G, 'A': A, 'GD': GD, 'AD': AD}
        if extra: rec.update(extra)
        log.write(json.dumps(rec) + '\n'); log.flush()
    note('start', start, 0, {'file': a.start, 'cap': D, 'seed': a.seed, 'mode': 'skeleton-pull'})
    if feas(start): (out / 'best.circ.txt').write_text(core.write_ncff(start, fdrive.MODEL))
    def offer(c, r, how):
        nonlocal best
        if c.value_table() != fdrive.AESTAB: raise RuntimeError('wrong function ' + how)
        if feas(c) and (M(c)[0], M(c)[2]) < (M(best)[0], M(best)[2]):
            best = c
            (out / 'best.circ.txt').write_text(core.write_ncff(c, fdrive.MODEL, comments=[
                'P2 sp.py seed %d round %d (%s) t=%.1f s' % (a.seed, r, how, time.time() - T0)]))
            note('best', c, r, {'how': how})
    r = 0
    base = start
    while time.time() - T0 < a.seconds - 5:
        r += 1
        rem = a.seconds - (time.time() - T0)
        ks = a.seed * 100000 + r
        c1, _ = fdrive.kernel(base, wd, 'r%da' % r, D + a.relax, a.cap_ad, a.iters, ks, seconds=min(rem, 120))
        if M(c1)[1] > a.cap_a or M(c1)[3] > a.cap_ad:
            note('relaxed-capviol', c1, r); base = best; continue
        andlv, olv, _, _ = skeldepth.bound(c1)
        note('relaxed', c1, r, {'skel': max(olv)})
        if max(olv) > D:
            base = best if rng.random() < 0.5 else c1
            continue
        sk = skeleton.extract(c1)
        _, arr, _ = cover28.bound(sk['ands'], sk['outputs'], c1.n)
        c2 = dsynth.synth({'ands': sk['ands'], 'outputs': sk['outputs']}, parent=c1, arr=arr)
        note('rebuilt', c2, r)
        rem = a.seconds - (time.time() - T0)
        if rem < 5: break
        c3, _ = fdrive.kernel(c2, wd, 'r%db' % r, D, a.cap_ad, a.iters, ks + 7, seconds=min(rem, 240))
        note('polished', c3, r)
        offer(c3, r, 'skeleton-pull')
        base = c3 if feas(c3) and M(c3)[0] <= M(best)[0] + 3 else best
    note('end', best, r)


if __name__ == '__main__':
    main()
