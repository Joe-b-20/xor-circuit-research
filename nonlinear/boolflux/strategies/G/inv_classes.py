"""Which 5-dim product spans do 5-AND GF(16)-inversion circuits have?  (track G, sampling)

Every 5-AND circuit computing n = N^-1 (4-bit inputs = N coordinates, the basis of inv_fit.py)
has products spanning (mod affine) span(n) + <v>.  This samples many circuits with nlb from random
starts and records the class of v modulo span(1, N, n) (an element of a 7-dim quotient).

usage: python3 inv_classes.py RUNS SECS OUT.json
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent / 'C'))
from nlbprob import Problem, Span, product_tables      # noqa: E402
import inv_fit as IF                                   # noqa: E402
from ll_prob import ninv_coords                        # noqa: E402


def main():
    runs, secs, out = int(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
    idx, _ = IF.coord_index()
    n16 = [IF.to16(t, idx) for t in ninv_coords()]
    P = Problem(4)
    for _ in range(5): P.add_slot()
    P.add_group(n16)
    base = Span()
    for t in P.free + n16: base.add(t, 0)
    # reduced representative of a class mod span(1, N, n)
    piv = sorted(base.rows, reverse=True)

    def rep(v):
        for p in piv:
            if (v >> p) & 1: v ^= base.rows[p][0]
        return v
    classes = {}
    td = tempfile.mkdtemp()
    pf = os.path.join(td, 'inv.prob'); P.write(pf)
    for s in range(1, runs + 1):
        pre = os.path.join(td, 'r%d' % s)
        subprocess.run([str(HERE / 'nlb'), pf, pre, str(s), str(secs), 'init=0', 'report=1000'])
        if not os.path.exists(pre + '.sol'): continue
        lines = Path(pre + '.sol').read_text().split('\n')
        ops = [tuple(int(v, 16) for v in lines[1 + k].split()) for k in range(5)]
        tabs = product_tables(P.free, ops)[len(P.free):]
        S = Span()
        for t in P.free + n16: S.add(t, 0)
        extra = [t for t in tabs if S.add(t, 0)]
        if len(extra) != 1: continue
        r = rep(extra[0])
        classes[r] = classes.get(r, 0) + 1
    Path(out).write_text(json.dumps({'runs': runs, 'classes': {'%x' % k: v for k, v in classes.items()}}, indent=1))
    print(json.dumps({'runs': runs, 'n_classes': len(classes), 'counts': sorted(classes.values(), reverse=True)}))


if __name__ == '__main__':
    main()
