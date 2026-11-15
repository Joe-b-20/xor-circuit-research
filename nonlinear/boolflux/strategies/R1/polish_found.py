#!/usr/bin/env python3
"""Polish mc1 AND-removal results with the gate kernel (hub ops._kernel, op_polish settings, own caps), check
each result against an archive's cell minima + the pinned NIST set, aes_check every non-dominated one and save
it to FOUND with a JSON sidecar.

    polish_found.py CAMPAIGN FOUND SECONDS AMAX JSONL [JSONL ...]   (circuits with A <= AMAX, by A then G)
"""
import json, random, sys, time
from pathlib import Path
sys.path.insert(0, '/home/joebachir20/xcr-boolflux/nonlinear'); sys.path.insert(0, '/home/joebachir20/xcr-boolflux/nonlinear/boolflux/campaigns')
from boolflux import core
from boolflux.hub.archive import Archive
from boolflux.hub.common import leq, published, metrics, code_version
from boolflux.hub.ops import _kernel
import aes_check

camp, found, secs, amax = sys.argv[1], Path(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
found.mkdir(parents=True, exist_ok=True)
ar = Archive(camp); pts = ar.points() + list(published())
rows = {}
for fn in sys.argv[5:]:
    for l in open(fn):
        d = json.loads(l)
        if 'm_new' in d and d.get('ok') and d['m_new'][0] <= amax:
            rows.setdefault(tuple(d['m_new']), d)
rng = random.Random(5)
work = Path(found).parent / 'polish-work'; work.mkdir(exist_ok=True)
for m, d in sorted(rows.items()):
    c = core.from_kernel(Path(d['file']).read_text())
    A, AD, G, GD = metrics(c)
    out = work / Path(d['file']).stem; out.mkdir(exist_ok=True)
    t0 = time.time()
    cands, info = _kernel(c, {'A': A, 'AD': AD, 'GD': GD}, 'a,ad,cost,gd', rng.randrange(1, 1 << 30), secs, out, camp)
    best = cands[0] if cands else c
    mb = metrics(best)
    for x, mx, tag in ((c, m, 'raw'), (best, mb, 'polished')):
        new = not any(leq(u, mx) for u in pts)
        rec = {'from_id': d['id'], 'from_m': d['m'], 'raw_m': list(m), 'm': list(mx), 'stage': tag, 'new_vs_archive_and_nist': new,
               'polish_s': round(time.time() - t0, 1)}
        if new:
            p = found / ('r1-%s-%s.bfx' % (tag, '-'.join(map(str, mx)))); p.write_text(core.to_kernel(x))
            r = aes_check.check(str(p))
            rec.update({'file': str(p), 'aes_check_ok': r['ok'], 'aes_check_new_point': r['new_point']})
            (p.with_suffix('.json')).write_text(json.dumps({'how': 'mc1.py window AND removal (+ kernel polish %s s, own caps)' % secs if tag == 'polished' else 'mc1.py window AND removal',
                                                           'source_circuit': d['id'], 'source_metrics': d['m'], 'window': d.get('W'),
                                                           'code_version': code_version(), 'time': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()), **rec}, indent=1))
        print(json.dumps(rec), flush=True)
