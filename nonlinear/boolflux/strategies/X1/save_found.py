#!/usr/bin/env python3
"""Save circuits to found/ after aes_check (two verifiers, 256 inputs): NCFF + .bfx + JSON sidecar.

    python3 save_found.py reduce CAMPAIGN_DIR FOUND_DIR [--amax 31]   static dep/merge reductions of archive members
    python3 save_found.py files FOUND_DIR METHOD FILE...             given .bfx / .circ.txt files
"""
import json, sys, time, subprocess
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[1] / 'campaigns'))
import x1patch as XP
import aes_check
from boolflux.hub.common import metrics, sbox, load, MODEL, code_version
from boolflux.hub.archive import Archive
from boolflux import core


def save(c, found, side):
    m = metrics(c)
    name = 'aes-sbox-a%d-ad%d-g%d-gd%d-x1' % m
    k = 0
    while (found / ('%s-%d.bfx' % (name, k))).exists():
        if (found / ('%s-%d.bfx' % (name, k))).read_text() == core.to_kernel(c): return None
        k += 1
    base = found / ('%s-%d' % (name, k))
    base.with_suffix('.bfx').write_text(core.to_kernel(c))
    r = aes_check.check(str(base.with_suffix('.bfx')))
    if not r['ok']:
        base.with_suffix('.bfx').rename(base.with_suffix('.FAILED.bfx')); print('FAILED', base); return None
    c.name = base.name
    Path(str(base) + '.circ.txt').write_text(core.write_ncff(c, MODEL, comments=['agent X1 (AND merge/dep move), %s' % side.get('method', '')]))
    side = dict(side); side.update({'metrics': list(m), 'aes_check_ok': True, 'new_point_vs_published': bool(r.get('new_point')),
                                    'code_version': code_version(), 'time': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())})
    base.with_suffix('.json').write_text(json.dumps(side, indent=1, default=str))
    return base.name, m, bool(r.get('new_point'))


if sys.argv[1] == 'reduce':
    ar = Archive(sys.argv[2]); found = Path(sys.argv[3]); found.mkdir(parents=True, exist_ok=True)
    amax = int(sys.argv[sys.argv.index('--amax') + 1]) if '--amax' in sys.argv else 31
    seen = set()
    for i, r in sorted(ar.rec.items(), key=lambda x: (x[1]['A'], x[1]['AD'], x[1]['GD'], x[1]['G'])):
        if r['A'] > amax: continue
        c = ar.circuit(i)
        cs = [(metrics(nc), d, nc) for nc, d in XP.static_candidates(c) if tuple(nc.value_table()) == sbox()]
        if not cs: continue
        cs.sort(key=lambda x: x[0])
        mm, d, nc = cs[0]
        if (tuple(metrics(c)), mm) in seen: continue
        seen.add((tuple(metrics(c)), mm))
        res = save(nc, found, {'method': 'x1patch static %s on hub archive member' % d['kind'], 'source': i,
                               'source_metrics': list(metrics(c)), 'source_operator': r['operator'], 'detail': d, 'seed': None})
        print(i, metrics(c), '->', res, flush=True)
else:
    found = Path(sys.argv[2]); found.mkdir(parents=True, exist_ok=True)
    for f in sys.argv[4:]:
        c = load(f)
        sp = Path(f).with_suffix('.json')
        side = json.loads(sp.read_text()) if sp.exists() else {}
        side['method'] = sys.argv[3]; side['file'] = f
        print(f, save(c, found, side), flush=True)
