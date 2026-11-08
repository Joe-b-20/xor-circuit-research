#!/usr/bin/env python3
"""qcert4: the rows (by name) with nonzero multipliers in the certificates of given keys (default: the five M^T q = 1
keys killed by the integer split alone), from the generator's row names.  No LP."""
import sys, json
sys.dont_write_bytecode = True
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen_certs4 as gen      # noqa: E402
d = json.load(open(HERE / 'CERTIFICATES_CASES75_B4.json'))
want = [tuple(json.loads(a)) for a in sys.argv[1:]] or [(12, 5, F, 'Mt', 1, 4) for F in range(1, 6)]
for e in d['certificates']:
    key = tuple(e['key'])
    if key not in want: continue
    hub = tuple(e['hub']) if e['hub'] else None
    types, aux, A, B, names, n_pkg, n_b1, n_flat = gen.ext_system4(key, hub, e['dark'])
    print(key, 'A =', e['A'], 'qD =', e['qD'], ':', [(names[j], w) for j, w in enumerate(e['weights']) if w])
