#!/usr/bin/env python3
"""Write one conjugate (conj.py) of FILE as a verified start: BP top resynthesis (T2/bp.py, several runs),
trb top/bottom passes.   mkconj.py FILE LAM K OUT.circ.txt [--top-runs 12]"""
import random, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[3]))
sys.path.append(str(HERE.parents[1] / 'F')); sys.path.append(str(HERE.parents[1] / 'T2'))
import conj as CJ  # noqa
import bp  # noqa
from boolflux import core  # noqa

f, lam, k, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
runs = int(sys.argv[sys.argv.index('--top-runs') + 1]) if '--top-runs' in sys.argv else 12
c = CJ.BT.load(f)
cc = CJ.conj_circuit(c, lam, k)
best, info = bp.optimise(cc, 99, 'top', random.Random(lam * 8 + k), runs, log=lambda *x: None)
if best is not None: cc = best
cc = CJ.resynth(cc, random.Random(1), 2)
assert cc.value_table() == CJ.AES
m = cc.metrics(CJ.MODEL)
Path(out).write_text(core.write_ncff(cc, CJ.MODEL, comments=['P3 mkconj.py: conjugate lam %d k %d of %s' % (lam, k, f)]))
print(out, m['A'], m['AD'], m['G'], m['GD'])
