#!/usr/bin/env python3
"""P2: depth-optimal rebuild of a circuit on its own AND skeleton (P2 dsynth, parent reuse limited to
signals that are fast enough): GD = the skeleton bound.   python3 rebuild.py IN OUT.circ.txt"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import cover28   # noqa: E402
import dsynth    # noqa: E402
from boolflux import core, skeleton, targets   # noqa: E402

c = core.read_ncff(sys.argv[1])
sk = skeleton.extract(c)
b, arr, ol = cover28.bound(sk['ands'], sk['outputs'], c.n)
c2 = dsynth.synth({'ands': sk['ands'], 'outputs': sk['outputs']}, parent=c, arr=arr)
assert tuple(c2.value_table()) == tuple(targets.aes_sbox())
m = core.Model.load('nist'); mt = c2.metrics(m)
print(sys.argv[1], 'bound', b, '->', mt['A'], mt['AD'], mt['G'], mt['GD'])
Path(sys.argv[2]).write_text(core.write_ncff(c2, m, comments=['P2 rebuild.py (depth-optimal on own skeleton) of %s' % sys.argv[1]]))
