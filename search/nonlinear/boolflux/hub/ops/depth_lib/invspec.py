#!/usr/bin/env python3
"""Extract the GF(2^4) inversion interface of a BP-style AES circuit.

Finds the 4 inversion inputs (the four level-1 XOR signals feeding the two AND-level-2 gates)
and the inversion outputs (linear signals after AND level 3 used as AND-level-4 operands), and
checks that every output is a function of the 4 inputs only.  Prints the 16-bit truth tables
(over the 4 input bits, index i = sum bit_k << k for input k) and levels.

    python3 invspec.py FILE
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3])); sys.path.insert(0, str(HERE))
from boolflux import core   # noqa: E402
from depth import analyse   # noqa: E402


def spec(c):
    n = c.n
    lv, al, req, GD, D, region, fo = analyse(c, 99)
    tabs = c.tables()
    a2 = [s for s in range(n, n + len(c.gates)) if c.gates[s - n][0] == 8 and al[s] == 2]
    ins = []
    for s in a2:
        for x in c.gates[s - n][1:]:
            if x not in ins and al[x] == 1 and c.gates[x - n][0] != 8: ins.append(x)
    # outputs: linear signals with al == 3 that feed an AND of level 4
    outs = []
    for s in range(n, n + len(c.gates)):
        if c.gates[s - n][0] == 8 and al[s] == 4:
            for x in c.gates[s - n][1:]:
                if al[x] == 3 and x not in outs: outs.append(x)
    return ins, outs, tabs, lv


def project(ins, outs, tabs):
    """Truth tables over the 4 inversion inputs; None if a signal is not a function of them."""
    res = []
    for s in outs:
        t = [None] * 16
        for x in range(256):
            k = sum(((tabs[ins[i]] >> x) & 1) << i for i in range(len(ins)))
            v = (tabs[s] >> x) & 1
            if t[k] is None: t[k] = v
            elif t[k] != v: return None
        res.append(sum((v or 0) << k for k, v in enumerate(t)))
    return res


if __name__ == '__main__':
    c = core.read_ncff(sys.argv[1])
    ins, outs, tabs, lv = spec(c)
    print('inversion inputs', ins, 'levels', [lv[s] for s in ins])
    print('inversion outputs', outs, 'levels', [lv[s] for s in outs])
    # complete the input set to 4 if needed
    pr = project(ins[:4], outs, tabs)
    print('projected tables:', None if pr is None else ['%04x' % t for t in pr])
