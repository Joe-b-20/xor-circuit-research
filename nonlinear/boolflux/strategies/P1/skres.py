#!/usr/bin/env python3
"""P1 skeleton re-synthesis probe: keep a circuit's AND skeleton (the 28 AND functions as affine forms
over inputs and earlier ANDs; A and AD are fixed by it), throw away its XOR layers, rebuild them
depth-first, then let the gate kernel recover sharing under the hard caps.

    python3 skres.py START --cap GD --cap-ad AD --seconds S --seed K --out DIR [--synth huff|req|skel]

synth: huff = T4 depthsynth (Huffman tree per form, meets the skeleton depth bound, little sharing);
       req  = T4 reqsynth (required-time greedy reuse at cap GD);
       skel = boolflux.skeleton.synthesize (greedy reuse, no depth control).
The rebuilt circuit has exactly the start's A and AD (same AND functions).  Kernel: hub kernel,
caps A = start A, AD = cap-ad, GD = cap, objective a,cost,gd, chained runs of S/3 s from the best.
Writes DIR/log.jsonl and DIR/best.circ.txt (best feasible).
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

PKG = Path('/home/joebachir20/xcr-boolflux/nonlinear/boolflux')
sys.path.insert(0, str(PKG.parent)); sys.path.insert(0, str(PKG / 'strategies' / 'T4'))
from boolflux import core, targets, skeleton as SK          # noqa: E402
from boolflux.hub import ops as HO                          # noqa: E402
from boolflux.hub.common import metrics, MODEL              # noqa: E402

TAB = tuple(targets.aes_sbox())


def rebuild(c, how, cap):
    sk = SK.extract(c)
    if how == 'huff':
        import depthsynth
        return depthsynth.synth({'ands': sk['ands'], 'outputs': sk['outputs']})
    if how == 'req':
        import reqsynth
        return reqsynth.synth({'ands': sk['ands'], 'outputs': sk['outputs']}, cap=cap)
    return SK.synthesize(sk, MODEL.ops())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('start'); ap.add_argument('--cap', type=int, required=True)
    ap.add_argument('--cap-ad', type=int, required=True); ap.add_argument('--seconds', type=float, default=300)
    ap.add_argument('--seed', type=int, default=1); ap.add_argument('--out', required=True)
    ap.add_argument('--synth', default='huff'); ap.add_argument('--chunks', type=int, default=3)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    log = open(out / 'log.jsonl', 'a')
    t = Path(a.start).read_text()
    c0 = core.from_kernel(t) if a.start.endswith('.bfx') else core.read_ncff(t)
    m0 = metrics(c0)
    r = rebuild(c0, a.synth, a.cap)
    assert tuple(r.value_table()) == TAB
    mr = metrics(r)
    T0 = time.time()
    log.write(json.dumps({'event': 'rebuild', 'start': a.start, 'm0': m0, 'synth': a.synth, 'm': mr}) + '\n'); log.flush()
    print('start', m0, 'rebuilt', mr, flush=True)
    assert mr[0] == m0[0] and mr[1] <= a.cap_ad
    rng = random.Random(a.seed)
    caps = {'A': m0[0], 'AD': a.cap_ad, 'GD': a.cap}
    best = r if mr[3] <= a.cap else None; cur = r
    for k in range(a.chunks):
        HO.KDEFAULTS['T0'] = rng.choice([0.3, 0.6, 1.0])
        sd = rng.randrange(1 << 30)
        d = out / ('k%d' % k); d.mkdir(exist_ok=True)
        cs, info = HO._kernel(cur, caps, 'a,cost,gd', sd, a.seconds / a.chunks, d, str(out))
        if not cs: continue
        x = cs[0]; mx = metrics(x)
        assert tuple(x.value_table()) == TAB
        log.write(json.dumps({'event': 'kernel', 'k': k, 'seed': sd, 'T0': HO.KDEFAULTS['T0'], 'caps': caps,
                              'm': mx, 't': round(time.time() - T0, 1)}) + '\n'); log.flush()
        print('kernel', k, mx, round(time.time() - T0), flush=True)
        if mx[0] <= m0[0] and mx[1] <= a.cap_ad and mx[3] <= a.cap and (best is None or (mx[2], mx[3]) < metrics(best)[2:]):
            best = x
            (out / 'best.circ.txt').write_text(core.write_ncff(x, MODEL, comments=['P1 skres %s from %s' % (a.synth, a.start)]))
        cur = x
    print('best', metrics(best) if best else None)


if __name__ == '__main__':
    main()
