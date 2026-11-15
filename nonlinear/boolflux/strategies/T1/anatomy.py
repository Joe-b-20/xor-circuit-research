#!/usr/bin/env python3
"""anatomy of circuits: per AND level, #ANDs and #linear gates; output depths; gates on depth-critical paths"""
import sys
from pathlib import Path
PKG = Path('/home/joebachir20/xcr-boolflux/nonlinear/boolflux')
sys.path.insert(0, str(PKG.parent))
from boolflux.hub.common import core, metrics   # noqa: E402
AR = Path('/home/joebachir20/xs-campaigns/2026-11-14-hub/long/archive')
for i in sys.argv[1:]:
    p = Path(i) if '/' in i else AR / (i + '.bfx')
    c = core.from_kernel(p.read_text(), p.stem)
    n = c.n; lv = [0] * n; al = [0] * n
    for op, a, b in c.gates:
        nl = op in core.NONLINEAR_OPS
        lv.append(max(lv[a], lv[b]) + 1)
        al.append(max(al[a], al[b]) + (1 if nl else 0))
    A, AD, G, GD = metrics(c)
    ands = [0] * (AD + 1); lin = [0] * (AD + 1)
    for j, (op, a, b) in enumerate(c.gates):
        if op in core.NONLINEAR_OPS: ands[al[n + j]] += 1
        else: lin[al[n + j]] += 1
    od = sorted(lv[o] for o in c.outputs)
    # required times / slack
    N = n + len(c.gates); req = [10 ** 9] * N
    for o in c.outputs: req[o] = min(req[o], GD)
    for j in range(len(c.gates) - 1, -1, -1):
        op, a, b = c.gates[j]; s = n + j
        for x in (a, b): req[x] = min(req[x], req[s] - 1)
    crit = sum(1 for j in range(len(c.gates)) if req[n + j] == lv[n + j])
    nots = sum(1 for g in c.gates if g[0] == 3)
    print('%s %d/%d/%d/%d ANDs/level %s linear/level %s NOT %d outdepths %s critical gates %d' %
          (p.stem, A, AD, G, GD, ands[1:], lin, nots, od, crit))
