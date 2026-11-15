#!/usr/bin/env python3
"""T4: area-oriented synthesis of a skeleton reusing a parent circuit's gates (skeleton.synthesize
with parent=), for a low-gate start that the kernel then repairs to the depth cap.
    python3 parsyn.py SKEL.json PARENT.circ.txt OUT.circ.txt"""
import sys, json
sys.path.insert(0, '../../..')
from boolflux import core, skeleton, targets
d = json.load(open(sys.argv[1]))
sk = {'n': 8, 'm': 8, 'ands': [(int(L, 16), int(R, 16)) for L, R in d['ands']], 'outputs': [int(F, 16) for F in d['outputs']]}
par = core.read_ncff(sys.argv[2])
c = skeleton.synthesize(sk, {8, 6, 9, 3}, name='t4-parsyn', parent=par)
assert tuple(c.value_table()) == tuple(targets.aes_sbox())
model = core.Model.load('nist'); m = c.metrics(model)
print(json.dumps({k: m[k] for k in ('A', 'AD', 'G', 'GD')}))
open(sys.argv[3], 'w').write(core.write_ncff(c, model, comments=['T4 parsyn of %s with parent %s' % (sys.argv[1], sys.argv[2])]))
