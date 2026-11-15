#!/usr/bin/env python3
"""P2: AND-skeleton depth bound of every GF(2^8) conjugate (P3's conj, copied as conj_p3.py) of a
circuit.  The conjugate keeps the AND structure; its AND functions as forms over the NEW inputs
differ (forms f -> f o G), and outputs pass through Mout, so the skeleton bound can change.

    python3 conjskel.py FILE OUT.json
"""
import json
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2])); sys.path.insert(0, str(HERE.parent / 'F'))
import conj_p3 as CJ   # noqa: E402
import skeldepth   # noqa: E402
from boolflux import core   # noqa: E402

f, outp = sys.argv[1], sys.argv[2]
c = CJ.BT.load(f) if hasattr(CJ.BT, 'load') else core.read_ncff(f)
res = []
for k in range(8):
    for lam in range(1, 256):
        cc = CJ.conj_circuit(c, lam, k)
        andlv, olv, _, _ = skeldepth.bound(cc)
        res.append((max(olv), sum(olv), lam, k, max(andlv[:9]) if andlv else None))
res.sort()
from collections import Counter
print(Path(f).name, 'bound histogram', sorted(Counter(r[0] for r in res).items()))
print('best', res[:15])
json.dump(res, open(outp, 'w'))
