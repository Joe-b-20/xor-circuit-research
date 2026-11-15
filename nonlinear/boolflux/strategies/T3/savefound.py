#!/usr/bin/env python3
"""T3: write a verified circuit to found/ as NCFF + JSON sidecar.  savefound.py SRC.bfx OUTDIR 'how' [k=v ...]"""
import json, sys, time, subprocess
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2])); sys.path.insert(0, str(HERE.parents[1] / 'campaigns'))
from boolflux import core
from boolflux.hub.common import load, metrics, cid, code_version
import aes_check
c = load(sys.argv[1]); out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
m = metrics(c); k = cid(c)
name = 'aes-sbox-a%d-ad%d-g%d-gd%d-%s' % (m + (k,))
f = out / (name + '.circ.txt')
f.write_text(core.write_ncff(c, core.Model.load('nist'), comments=['T3 (2026-11-15): ' + sys.argv[3]]))
ac = aes_check.check(str(f))
side = {'metrics': m, 'id': k, 'made_by': sys.argv[3], 'source_file': sys.argv[1], 'code_version': code_version(),
        'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'aes_check': ac}
for kv in sys.argv[4:]:
    a, b = kv.split('=', 1); side[a] = b
(out / (name + '.json')).write_text(json.dumps(side, indent=1, default=str))
print(f, ac['ok'], ac.get('new_point'))
