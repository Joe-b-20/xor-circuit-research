#!/usr/bin/env python3
"""T4: anatomy of an AD4 circuit's AND skeleton: each AND's operands as forms over
(const, inputs, earlier ANDs), with AND level and gate level.   python3 anat.py FILE"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core, skeleton  # noqa

def lv_tables(c):
    n = c.n; lg = [0]*n; la = [0]*n
    for op, a, b in c.gates:
        lg.append(1+max(lg[a], lg[b])); la.append((1 if op in core.NONLINEAR_OPS else 0)+max(la[a], la[b]))
    return lg, la

def main(f):
    c = core.read_ncff(f) if f.endswith('.txt') else core.from_kernel(open(f).read())
    sk = skeleton.extract(c); n = c.n
    lg, la = lv_tables(c)
    andsig = [n+j for j, g in enumerate(c.gates) if g[0] in core.NONLINEAR_OPS]
    names = ['1'] + ['x%d' % i for i in range(n)] + ['a%d' % k for k in range(len(andsig))]
    def fmt(F):
        return '+'.join(names[p] for p in range(len(names)) if (F >> p) & 1) or '0'
    for k, (L, R) in enumerate(sk['ands']):
        s = andsig[k]
        print('a%-3d AL%d GL%-2d  L=%s   R=%s' % (k, la[s], lg[s], fmt(L), fmt(R)))
    for j, F in enumerate(sk['outputs']):
        print('y%d GL%d = %s' % (j, lg[c.outputs[j]], fmt(F)))
main(sys.argv[1])
