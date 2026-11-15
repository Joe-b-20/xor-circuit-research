#!/usr/bin/env python3
"""bottom transplant test (track F botsplice): bases = A28 AD4 near-B circuits, donors = all AD4 archive
circuits with A <= 30; print results with A <= 28"""
import json, sys, time
from pathlib import Path
PKG = Path('/home/joebachir20/xcr-boolflux/nonlinear/boolflux')
sys.path.insert(0, str(PKG.parent)); sys.path.insert(0, str(PKG / 'hub' / 'ops' / 'f_lib'))
from boolflux.hub.common import core, metrics, sbox   # noqa: E402
import botsplice                                       # noqa: E402
AR = Path('/home/joebachir20/xs-campaigns/2026-11-14-hub/long/archive')
recs = [json.loads(f.read_text()) for f in AR.glob('*.json') if f.name != 'cells.json']
bases = [r['id'] for r in recs if r['A'] == 28 and r['AD'] == 4 and r['G'] <= 135]
donors = [r['id'] for r in recs if r['A'] <= 30 and r['AD'] == 4 and r['G'] <= 140]
ld = lambda i: core.from_kernel((AR / (i + '.bfx')).read_text(), i)
print('bases', len(bases), 'donors', len(donors), flush=True)
t0 = time.time(); res = {}; err = 0; wrong = 0
for b in bases:
    B = ld(b)
    for d in donors:
        if d == b: continue
        try: nc = botsplice.build(B, ld(d))
        except Exception: err += 1; continue
        if tuple(nc.value_table()) != sbox(): wrong += 1; continue
        m = metrics(nc)
        res[m] = res.get(m, 0) + 1
    if time.time() - t0 > 100: break
print('time', round(time.time() - t0), 'errors', err, 'wrong', wrong)
print(sorted((m, k) for m, k in res.items() if m[0] <= 28)[:20])
