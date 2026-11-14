#!/usr/bin/env python3
"""Hub vs memetic splice arm (equal CPUs): new frontier points (not dominated by the published pin, nor by
the common seed pool, nor strictly inside the arm), per CPU-hour, mechanism, cross-dominance.

    python3 compare.py HUBDIR MEMDIR SEEDARCHIVE CPUS_EACH [--check]
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from boolflux import core                               # noqa: E402
from boolflux.hub.archive import Archive                # noqa: E402
from boolflux.hub.common import metrics, leq, published  # noqa: E402

hub, mem, seed = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); ncpu = int(sys.argv[4])
check = '--check' in sys.argv
pub = list(published())
base = Archive(seed).points() + pub


def frontier(items):
    allm = [m for m, *_ in items]
    out = {}
    for m, src, i, c in items:
        if any(leq(u, m) for u in base): continue
        if any(u != m and leq(u, m) for u in allm): continue
        out.setdefault(m, (src, i, c))
    return out


H = Archive(hub)
hi = [((r['A'], r['AD'], r['G'], r['GD']), r['operator'], i, None) for i, r in H.rec.items() if r['operator'] != 'seed']
ev = [json.loads(l) for l in (hub / 'events.jsonl').read_text().splitlines()]
st = [e for e in ev if e.get('ev') == 'start'][-1]['ts']; en = ev[-1]['ts']
mi = []
for f in (mem / 'admitted').glob('*.bfx'):
    o = json.loads(f.with_suffix('.json').read_text())['origin']
    mi.append((tuple(metrics(core.from_kernel(f.read_text(), f.stem))), 'join' if o['kind'] == 'splice' else 'polish', f.stem, None))
mev = [json.loads(l) for l in (mem / 'log.jsonl').read_text().splitlines()]
mh = (mev[-1]['ts'] - mev[0]['ts']) / 3600
hh = (en - st) / 3600
fh, fm = frontier(hi), frontier(mi)
res = {}
for name, fr, items, hours in (('hub', fh, hi, hh), ('memetic', fm, mi, mh)):
    other = fm if name == 'hub' else fh
    by = {}
    for m, (src, i, c) in fr.items(): by[src] = by.get(src, 0) + 1
    res[name] = {'hours': round(hours, 2), 'cpu_h': round(hours * ncpu, 2), 'admissions': len(items),
                 'frontier_points': len(fr), 'per_cpu_h': round(len(fr) / (hours * ncpu), 2) if hours else None,
                 'by_mechanism': by,
                 'not_dominated_by_other': sum(1 for m in fr if not any(leq(u, m) for u in other)),
                 'points': sorted(['%d/%d/%d/%d %s' % (*m, s[0]) for m, s in fr.items()])}
print(json.dumps(res, indent=1))
if check:
    import subprocess
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'campaigns'))
    import aes_check
    for name, fr, d in (('hub', fh, hub / 'archive'), ('memetic', fm, mem / 'admitted')):
        okn = 0
        for m, (src, i, c) in fr.items():
            p = d / (i + '.bfx')
            r = aes_check.check(str(p))
            okn += bool(r['ok'] and r['new_point'])
        print(name, 'aes_check ok+new: %d / %d' % (okn, len(fr)))
