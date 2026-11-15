#!/usr/bin/env python3
"""Build circuits from gadget.py solutions: the 117's 12 standard products + the gadget's k products +
its corrections; linear terms from the exact residual.  gbuild.py REF CIRC SOLS.json OUTDIR [--nb 4]"""
import json, random, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import bottom as BT, flip as FL, qflip as QF, build as BD  # noqa
from boolflux import core  # noqa

ref, circ, solf, out = sys.argv[1:5]
nb = int(sys.argv[sys.argv.index('--nb') + 1]) if '--nb' in sys.argv else 4
out = Path(out); out.mkdir(parents=True, exist_ok=True)
rc, Yt = FL.ref_basis(ref)
c = BT.load(circ)
free, fixed, lin = QF.decompose(c, Yt)
def mixed(f): return (f >> 9) and (f >> 1) & 0xFF
std = [t for t in free if not mixed(t[0]) and not mixed(t[1])]
goal = QF.total(free, fixed, lin)
for n, sol in enumerate(json.load(open(solf))):
    fr = std + [tuple(p) for p in sol['prods']]
    fx = [(L, R, sol['cors'].get(str(k), sol['cors'].get(k, 0))) for k, (L, R, w) in enumerate(fixed)]
    cur = QF.total(fr, fx, [0] * 8)
    ln = []
    ok = True
    for o in range(8):
        if list(goal[o][0]) != list(cur[o][0]): ok = False
        ln.append(goal[o][1] ^ cur[o][1])
    if not ok: print(n, 'quadratic residual nonzero'); continue
    best = None
    for s in range(nb):
        cc = BD.build(c, Yt, fr, fx, ln, random.Random(s))
        m = cc.metrics(BD.MODEL)
        if best is None or (m['G'], m['GD']) < best[0]: best = ((m['G'], m['GD']), cc, m)
    (G, GD), cc, m = best
    assert cc.value_table() == BD.AES
    nm = 'gad-%s-%d-a%d-g%d-gd%d.circ.txt' % (Path(solf).stem, n, m['A'], G, GD)
    (out / nm).write_text(core.write_ncff(cc, BD.MODEL, comments=['P3 gbuild.py from %s solution %d' % (solf, n)]))
    print(nm, 'new operands', sol['new_operands'], 'A', m['A'], 'G', G, 'GD', GD, 'lin terms', sum(1 for l in ln if l >> 1))
