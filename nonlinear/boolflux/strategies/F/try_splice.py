#!/usr/bin/env python3
"""Direct splices: base B, donor A; substitute B's signals in chosen regions by A's equal functions.
    python3 try_splice.py CAP BASE DONOR [DONOR2 ...]
"""
import itertools
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2])); sys.path.insert(0, str(HERE))
from boolflux import core   # noqa: E402
from splice import Splicer, levels   # noqa: E402
from depth import analyse   # noqa: E402
from union import AESTAB, NIST   # noqa: E402

D = int(sys.argv[1]); B = core.read_ncff(sys.argv[2]); donors = [core.read_ncff(f) for f in sys.argv[3:]]
sp = Splicer(B, donors, D)
lv, al, req, GD, _, region, fo = analyse(B, D)
regs = sorted({region(s) for s in range(8, 8 + len(B.gates))}, key=lambda r: (r[1:], r[0]))
print('base', Path(sys.argv[2]).name, 'G', len(B.gates), 'regions', regs)
res = []
for k in range(len(donors)):
    for r1 in range(len(regs)):
        for r2 in range(r1, len(regs)):
            sel = set(regs[r1:r2 + 1])
            for mode in ('any', 'lower-or-equal'):
                ch = [None] * len(B.gates)
                for j in range(len(B.gates)):
                    if region(8 + j) not in sel: continue
                    for (kk, ds) in sp.opts[j]:
                        if kk != k: continue
                        if mode == 'lower-or-equal' and sp.dl[kk][ds] > lv[8 + j]: continue
                        ch[j] = (kk, ds); break
                c = sp.build(ch); s, gd = sp.score(c)
                ok = c.value_table() == AESTAB
                res.append((s, len(c.gates), gd, k, '+'.join(regs[r1:r2 + 1]), mode, ok))
res.sort()
for r in res[:15]: print(r)
for r in res:
    if r[4] in ("L1", "A1+L1", "L0+A1+L1", "L0+A1+L1+A2", "L0"): print("  ", r)
import os
if os.environ.get("SPLICE_OUT"):
    # rebuild the best feasible result and save it
    want = os.environ.get("SPLICE_REGION")
    for s_, g_, gd_, k, regname, mode, ok in res:
        if gd_ <= D and ok and (not want or regname == want):
            sel = set(regname.split("+"))
            ch = [None] * len(B.gates)
            for j in range(len(B.gates)):
                if region(8 + j) not in sel: continue
                for (kk, ds) in sp.opts[j]:
                    if kk != k: continue
                    if mode == "lower-or-equal" and sp.dl[kk][ds] > lv[8 + j]: continue
                    ch[j] = (kk, ds); break
            c = sp.build(ch)
            Path(os.environ["SPLICE_OUT"]).write_text(core.write_ncff(c, NIST))
            print("saved", regname, mode, len(c.gates), "GD", sp.score(c)[1])
            break
