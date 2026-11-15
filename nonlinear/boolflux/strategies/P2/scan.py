#!/usr/bin/env python3
"""P2 start scan: every archive circuit within the T02 (A<=28, AD<=4) or T06 (A<=34, AD<=4)
hard limits, with metrics and F's AND-skeleton depth bound (skeldepth.bound).

    python3 scan.py OUT.jsonl [GDMAX]

The skeleton bound is the minimum gate depth of ANY circuit with the same AND functions
(as affine forms over inputs and earlier ANDs) [C for that skeleton]; it says nothing about
circuits with other AND functions.
"""
import glob
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2])); sys.path.insert(0, str(HERE.parent / 'F'))
from boolflux import core, targets   # noqa: E402
import skeldepth   # noqa: E402

H = Path.home()
AES = targets.aes_sbox()
pats = [str(H / 'xcr-boolflux/nonlinear/nist/aes-sbox/*.circ.txt'),
        str(H / 'xs-campaigns/2026-11-15-study/best-1400/*.circ.txt'),
        str(H / 'xcr-boolflux/nonlinear/boolflux/results/aes/*.circ.txt'),
        str(H / 'xs-campaigns/2026-11-15-study/*/found/*.circ.txt'),
        str(H / 'xs-campaigns/2026-11-15-targets/*/found/*.circ.txt'),
        str(H / 'xs-campaigns/2026-11-13-aes/*/found/*.circ.txt'),
        str(H / 'xs-campaigns/2026-11-14-hub/*/archive/*.bfx')]
out = sys.argv[1]
gdmax = int(sys.argv[2]) if len(sys.argv) > 2 else 17
seen = {}
rows = []
for pat in pats:
    for f in sorted(glob.glob(pat)):
        try:
            if f.endswith('.bfx'):
                c = core.from_kernel(open(f).read(), f)
            else:
                c = core.read_ncff(f)
        except Exception as e:
            continue
        m = c.metrics()
        A, AD, G, GD = m['A'], m['AD'], m['G'], m['GD']
        if AD > 4 or A > 34 or GD > gdmax:
            continue
        key = hashlib.sha256(core.to_kernel(c).encode()).hexdigest()[:16]
        if key in seen:
            seen[key]['files'] += 1
            continue
        if c.output_tables() != AES and c.value_table() != AES:
            # targets.aes_sbox() format: check value table
            pass
        try:
            andlv, olv, ands, outf = skeldepth.bound(c)
            sb = max(olv)
        except Exception as e:
            sb = None
        r = {'file': f, 'key': key, 'A': A, 'AD': AD, 'G': G, 'GD': GD, 'skel': sb, 'files': 1,
             'T02': A <= 28, 'T06': A <= 34}
        seen[key] = r
        rows.append(r)
rows.sort(key=lambda r: (r['A'], r['GD'], r['G']))
with open(out, 'w') as fh:
    for r in rows:
        fh.write(json.dumps(r) + '\n')
print(len(rows), 'rows')
