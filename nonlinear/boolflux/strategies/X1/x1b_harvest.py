#!/usr/bin/env python3
"""X1b harvest: verify circuits with campaigns/aes_check.py and save them to a found/ directory with
.bfx, .circ.txt and a JSON sidecar (source sidecar merged in, span hash and level profile added).

    python3 x1b_harvest.py FOUND_DIR TAG FILE...
Name: aes-sbox-aA-adD-gG-gdGD-x1b-TAG-<span hash>-<k>.  Files that fail the check are listed, not saved."""
import json, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[1] / 'campaigns'))
import x1b_family as F
import aes_check
from boolflux.hub.common import load, metrics, MODEL, code_version
from boolflux import core

NIST = Path('/home/joebachir20/xcr-boolflux/nonlinear/nist/aes-sbox')
REFS = [NIST / 'aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt', NIST / 'aes-sbox-a28-ad4-g131-gd31-xx103-43.circ.txt']

out = Path(sys.argv[1]); tag = sys.argv[2]; out.mkdir(parents=True, exist_ok=True)
refs = [F.analyse_c(load(r)) for r in REFS]
for k, f in enumerate(sys.argv[3:]):
    f = Path(f); c = load(f); m = metrics(c); fi = F.analyse_c(c)
    name = 'aes-sbox-a%d-ad%d-g%d-gd%d-x1b-%s-%s-%d' % (m + (tag, fi['span'], k))
    bp = out / (name + '.bfx'); bp.write_text(core.to_kernel(c))
    r = aes_check.check(str(bp))
    if not r['ok']:
        bp.rename(out / (name + '.FAILED')); print('FAILED', f); continue
    c.name = name
    (out / (name + '.circ.txt')).write_text(core.write_ncff(c, MODEL, comments=['agent X1/X1b, harvested from %s' % f.name]))
    side = {}
    sj = f.with_suffix('.json') if f.suffix == '.bfx' else Path(str(f).replace('.circ.txt', '.json'))
    if sj.exists():
        try: side = json.loads(sj.read_text())
        except Exception: side = {}
    side.update({'harvested_from': str(f), 'metrics': m, 'span': fi['span'], 'levels': fi['levels'], 'span_L': fi['span_L'],
                 'shared_with_refs': {r.name: F.inter(fi, q) for r, q in zip(REFS, refs)},
                 'aes_check_ok': True, 'new_point_vs_published': bool(r.get('new_point')),
                 'harvest_code_version': code_version(), 'harvest_time': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())})
    (out / (name + '.json')).write_text(json.dumps(side, indent=1))
    print('OK', name, 'levels', fi['levels'], 'shared', side['shared_with_refs'], 'new_point', side['new_point_vs_published'])
