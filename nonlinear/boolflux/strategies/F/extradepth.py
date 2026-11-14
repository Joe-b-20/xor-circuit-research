#!/usr/bin/env python3
"""Earliest level of XOR combinations of the inversion inputs in a BP-style circuit (track F).
For each nonempty subset of the 4 inversion inputs, the affine form over the skeleton basis and
its Huffman depth from the ASAP arrivals (lower bound, achievable without sharing)."""
import itertools
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2])); sys.path.insert(0, str(HERE))
from boolflux import core   # noqa: E402
from skelxf import Skel, gate_forms, bits   # noqa: E402
from skeldepth import huff   # noqa: E402
from invspec import spec   # noqa: E402

c = core.read_ncff(sys.argv[1])
ins, outs, tabs, lv = spec(c)
ins = ins[:4]
form = gate_forms(c)
sk = Skel.from_circuit(c)
arr = sk.arrivals()
for r in (1, 2, 3, 4):
    for ks in itertools.combinations(range(4), r):
        f = 0
        for k in ks: f ^= form[ins[k]]
        t = [p for p in bits(f) if p > 0]
        print('x' + '^x'.join(map(str, ks)), 'terms', len(t), 'arrivals', sorted((arr[p] for p in t), reverse=True), 'depth', huff([arr[p] for p in t], bool(f & 1)))
