#!/usr/bin/env python3
"""Grind near-miss circuits with the gate kernel (hub ops._kernel, op_polish settings): rounds of polish under own
caps and pulls (GD cap - 1 or - 2), chaining every non-dominated-within-the-run result; every result not dominated
by the archive's cell minima + the pinned NIST set is aes_checked and saved to FOUND with a JSON sidecar.

    grind.py CAMPAIGN FOUND SECONDS_TOTAL ROUND_SECONDS SEED FILE.bfx [FILE.bfx ...]
"""
import json, random, sys, time
from pathlib import Path
sys.path.insert(0, '/home/joebachir20/xcr-boolflux/nonlinear'); sys.path.insert(0, '/home/joebachir20/xcr-boolflux/nonlinear/boolflux/campaigns')
from boolflux import core
from boolflux.hub.archive import Archive
from boolflux.hub.common import leq, published, metrics, code_version
from boolflux.hub.ops import _kernel
import aes_check

camp, found, total, rs, seed = sys.argv[1], Path(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5])
files = sys.argv[6:]
found.mkdir(parents=True, exist_ok=True)
ar = Archive(camp); pts = ar.points() + list(published())
rng = random.Random(seed)
work = found.parent / ('grind-work-%d' % seed); work.mkdir(exist_ok=True)
pool = [(core.from_kernel(Path(f).read_text()), f) for f in files]
ref = pool[0][0].output_tables()
best = {}                                   # (A, AD, GD) -> (G, circuit, origin)
for c, f in pool:
    m = metrics(c); k = (m[0], m[1], m[3])
    if k not in best or m[2] < best[k][0]: best[k] = (m[2], c, f)
t_end = time.time() + total; n = 0
while time.time() < t_end:
    k = rng.choice(sorted(best)); G, c, origin = best[k]
    A, AD, GD = k
    caps = {'A': A, 'AD': AD, 'GD': GD}; kind = 'polish'
    if rng.random() < 0.5:
        caps['GD'] = GD - rng.choice([1, 1, 2]); kind = 'pull'
    n += 1; out = work / ('r%04d' % n); out.mkdir(exist_ok=True)
    cands, info = _kernel(c, caps, 'a,ad,cost,gd', rng.randrange(1, 1 << 30), min(rs, max(2, t_end - time.time())), out, camp)
    for x in cands:
        if x.output_tables() != ref: continue
        m = metrics(x); kk = (m[0], m[1], m[3])
        if m[0] > A or m[1] > AD or m[3] > caps['GD']: continue
        if kk not in best or m[2] < best[kk][0]:
            best[kk] = (m[2], x, '%s <- %s(%s)' % (out.name, kind, origin))
            new = not any(leq(u, m) for u in pts)
            rec = {'m': list(m), 'kind': kind, 'round': out.name, 'from': origin, 'new_vs_archive_and_nist': new, 't': time.strftime('%H:%M:%S')}
            if new:
                p = found / ('r1-grind-%s.bfx' % '-'.join(map(str, m))); p.write_text(core.to_kernel(x))
                r = aes_check.check(str(p))
                rec.update({'file': str(p), 'aes_check_ok': r['ok'], 'aes_check_new_point': r['new_point']})
                p.with_suffix('.json').write_text(json.dumps({'how': 'mc1.py window AND removal + kernel polish/pull grind (grind.py)', 'seed': seed,
                                                              'code_version': code_version(), **rec}, indent=1))
            print(json.dumps(rec), flush=True)
print(json.dumps({'end': True, 'rounds': n, 'cells': {'%d/%d/%d' % k: v[0] for k, v in sorted(best.items())}}), flush=True)
