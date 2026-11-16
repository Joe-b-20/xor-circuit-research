"""Join (stage transplant with linear interface).

Front of X = X's signals of AND level <= LX; back of Y = Y's gates above AND level LY.  The cut of Y
(signals of level <= LY read above LY, or outputs) must lie in the affine span of X's front (inputs +
X's ANDs of level <= LX); each cut function is rebuilt greedily from X's existing linear signals
(largest overlap first; XNOR/NOT for the constant).  Result = X front + interface gates + Y back, dead
gates removed.  Exact by construction (every cut signal keeps its truth table); still verified on
admission.
"""
from __future__ import annotations

from .common import core, ONES

XOR, XNOR, NOT = 6, 9, 3


def levels(c):
    la = [0] * c.n
    for op, a, b in c.gates:
        la.append(max(la[a], la[b]) + (1 if op in core.NONLINEAR_OPS else 0))
    return la


class Prepared:
    def __init__(self, c, ident=None):
        self.c = c; self.id = ident; self.t = c.tables(); self.l = levels(c)
        self.AD = max((self.l[o] for o in c.outputs), default=0)
        self._fronts = {}

    def front(self, LX):
        if LX not in self._fronts: self._fronts[LX] = Front(self.c, self.t, self.l, LX)
        return self._fronts[LX]


class Front:
    def __init__(self, X, tx, lx, LX):
        n = X.n; self.X = X; self.n = n
        basis = [ONES] + [tx[i] for i in range(n)]
        for j, (op, a, b) in enumerate(X.gates):
            s = n + j
            if op in core.NONLINEAR_OPS and lx[s] <= LX: basis.append(tx[s])
        self.piv = []
        for i, t in enumerate(basis):
            f = 1 << i
            for p, rt, rf in self.piv:
                if (t >> p) & 1: t ^= rt; f ^= rf
            if t:
                self.piv.append((t.bit_length() - 1, t, f)); self.piv.sort(key=lambda r: -r[0])
        self.have = {}
        for s in range(n + len(X.gates)):
            if lx[s] <= LX:
                f = self.form(tx[s])
                if f is not None and f not in self.have: self.have[f] = s

    def form(self, t):
        f = 0
        for p, rt, rf in self.piv:
            if (t >> p) & 1: t ^= rt; f ^= rf
        return f if t == 0 else None


def _build(n, f, gates, have):
    if f in have: return have[f]
    parts = []; rest = f
    while rest:
        best = None; bg = 0
        for fm, s in have.items():
            if fm & 1: continue
            g = bin(rest).count('1') - bin(rest ^ fm).count('1')
            if g > bg: best, bg = (fm, s), g
        if best is None: return None
        parts.append(best); rest ^= best[0]
    af, asg = parts[0]
    for fm, s in parts[1:]:
        af ^= fm
        if af in have: asg = have[af]
        else:
            gates.append((XOR, asg, s)); asg = n + len(gates) - 1; have[af] = asg
    return asg


def join(front, Y, LY):
    """front: Front of X; Y: Prepared.  Returns (circuit, interface gate count) or (None, None)."""
    n = Y.c.n; X = front.X
    gates = list(X.gates); have = dict(front.have)
    need = [False] * (n + len(Y.c.gates))
    for j, (op, a, b) in enumerate(Y.c.gates):
        if Y.l[n + j] > LY:
            for o in (a, b):
                if o >= n and Y.l[o] <= LY: need[o] = True
    for o in Y.c.outputs:
        if o >= n and Y.l[o] <= LY: need[o] = True
    ymap = list(range(n)) + [None] * len(Y.c.gates)
    nint = 0
    for s in range(n, n + len(Y.c.gates)):
        if not need[s]: continue
        f = front.form(Y.t[s])
        if f is None: return None, None
        if f in have: ymap[s] = have[f]; continue
        base = f & ~1
        if base == 0: return None, None
        g0 = len(gates)
        sg = _build(n, base, gates, have)
        if sg is None: return None, None
        if f & 1:
            if f in have: sg = have[f]
            elif sg >= n and sg - n >= g0 and gates[sg - n][0] == XOR:
                op, a, b = gates[sg - n]; gates[sg - n] = (XNOR, a, b); have.pop(base, None); have[f] = sg
            else:
                gates.append((NOT, sg, sg)); sg = n + len(gates) - 1; have[f] = sg
        nint += len(gates) - g0
        ymap[s] = sg
    for j, (op, a, b) in enumerate(Y.c.gates):
        s = n + j
        if Y.l[s] <= LY: continue
        if ymap[a] is None or ymap[b] is None: return None, None
        gates.append((op, ymap[a], ymap[b])); ymap[s] = n + len(gates) - 1
    outs = [ymap[o] for o in Y.c.outputs]
    if any(o is None for o in outs): return None, None
    return core.Circuit(n, Y.c.m, gates, outs).live(), nint


def join_all(X, Y):
    """every cut level LY of Y, LX in {LY, AD_X - 1}: yields (circuit, LX, LY, interface)"""
    for LY in range(1, Y.AD):
        for LX in sorted({min(LY, X.AD - 1), X.AD - 1}):
            if LX < 1: continue
            c, nint = join(X.front(LX), Y, LY)
            if c is not None: yield c, LX, LY, nint
