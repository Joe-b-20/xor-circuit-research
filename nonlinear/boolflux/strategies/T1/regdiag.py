#!/usr/bin/env python3
"""Region SLP diagnostic: for each AND-level layer k of a circuit, the layer's linear gates R, its pure linear
map (distinct targets with >= 2 leaves, constants dropped) and XORFlux `quick` (gates objective, no depth cap)
on that map.  Prints current layer gates vs XORFlux best (an XOR count for the same linear map; constants
and single-leaf targets cost extra NOTs in the circuit, counted separately).

    python3 regdiag.py FILE_OR_ID GD SECONDS LAYERS(e.g. 0,1,3,4)
"""
import json, random, subprocess, sys, tempfile
from pathlib import Path
PKG = Path('/home/joebachir20/xcr-boolflux/nonlinear/boolflux')
sys.path.insert(0, str(PKG.parent)); sys.path.insert(0, str(PKG / 'strategies' / 'F'))
from boolflux.hub.common import core, metrics   # noqa: E402
import linres as LR                              # noqa: E402

AR = Path('/home/joebachir20/xs-campaigns/2026-11-14-hub/long/archive')
f, D, sec, layers = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), [int(x) for x in sys.argv[4].split(',')]
p = Path(f) if '/' in f else AR / (f + '.bfx')
c = core.from_kernel(p.read_text(), p.stem)
print(p.stem, metrics(c), flush=True)
for k in layers:
    R, lv, req, fo = LR.region_of(c, D, 'layer:%d' % k, random.Random(1))
    leaves, form, tg = LR.extract(c, R, fo)
    rows = sorted({form[t] & ~1 for t in tg if bin(form[t] & ~1).count('1') > 1})
    nots = sum(1 for s in R if c.gates[s - c.n][0] == 3)
    L = len(leaves)
    wd = Path(tempfile.mkdtemp(prefix='regdiag-'))
    mat = wd / 'region.mat.txt'
    mat.write_text('1\n%d %d\n' % (len(rows), L) + ''.join(' '.join('1' if (r >> (1 + j)) & 1 else '0' for j in range(L)) + '\n' for r in rows))
    cmd = [sys.executable, str(LR.XORFLUX), 'quick', str(mat), '--seconds', str(sec), '--seed', '1', '--out', str(wd / 'xf')]
    r = subprocess.run(cmd, capture_output=True, text=True)
    best = None
    try:
        recs = [json.loads(l) for l in (wd / 'xf' / 'workers' / 'quick-00' / 'records.jsonl').read_text().splitlines() if l.strip()]
        best = min((x['gates'], x['depth']) for x in recs)
    except Exception as ex:
        best = 'error %s %s' % (ex, (r.stdout + r.stderr)[-300:])
    wsum = sum(bin(x).count('1') - 1 for x in rows)
    print('layer %d: gates %d (NOT %d) leaves %d targets %d distinct-rows %d naive %d xorflux %s' %
          (k, len(R), nots, L, len(tg), len(rows), wsum, best), flush=True)
