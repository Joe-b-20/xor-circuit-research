"""join+ : a join that adds the missing products.  When some cut functions of Y are not in the span of
X's front, Y's own ANDs of level <= LY are added to the front one at a time (in Y's order, each only if
its operand functions are already in the current span, i.e. buildable by XORs), until every cut
function is in the span; additions that turn out unnecessary are dropped (reverse pass).  The added
ANDs make a hybrid front (X's products + some of Y's), so families whose interfaces differ (e.g. the
A28/A29 backs, whose operands need their own stage-1 products, on BP-family fronts) can be joined at
the price of a few ANDs.  Result = augmented X + interface XORs + Y's back (join.join), verified on
admission.
"""
from __future__ import annotations

from .common import core, ONES
from . import join as J


def _span_rows(tabs):
    rows = []
    for t in tabs:
        for p, r in rows:
            if (t >> p) & 1: t ^= r
        if t: rows.append((t.bit_length() - 1, t)); rows.sort(key=lambda x: -x[0])
    return rows


def _in(rows, t):
    for p, r in rows:
        if (t >> p) & 1: t ^= r
    return t == 0


def augment(X, LX, Y, LY, max_add=4):
    """returns (augmented circuit X', LX', added Y AND signals) or None"""
    n = X.c.n
    base = [ONES] + [X.t[i] for i in range(n)] + [X.t[n + j] for j, g in enumerate(X.c.gates)
                                                    if g[0] in core.NONLINEAR_OPS and X.l[n + j] <= LX]
    # cut functions of Y
    cut = set()
    for j, (op, a, b) in enumerate(Y.c.gates):
        if Y.l[n + j] > LY:
            for o in (a, b):
                if o >= n and Y.l[o] <= LY: cut.add(Y.t[o])
    for o in Y.c.outputs:
        if o >= n and Y.l[o] <= LY: cut.add(Y.t[o])
    rows = _span_rows(base)
    missing = [t for t in cut if not _in(rows, t)]
    if not missing: return None                       # plain join covers it
    yands = [n + j for j, g in enumerate(Y.c.gates) if g[0] in core.NONLINEAR_OPS and Y.l[n + j] <= LY]
    added = []
    for s in yands:
        if not [t for t in cut if not _in(rows, t)]: break
        op, a, b = Y.c.gates[s - n]
        if _in(rows, Y.t[s]): continue
        if not (_in(rows, Y.t[a]) and _in(rows, Y.t[b])): continue
        added.append(s); rows = _span_rows(base + [Y.t[x] for x in added])
    if [t for t in cut if not _in(rows, t)]: return None
    for s in list(reversed(added)):                    # drop unnecessary additions (keep buildability)
        trial = [x for x in added if x != s]
        r2 = _span_rows(base + [Y.t[x] for x in trial])
        ok = all(_in(r2, t) for t in cut)
        if ok:
            # every remaining addition must still be buildable from what precedes it
            rr = _span_rows(base); good = True
            for x in trial:
                op, a, b = Y.c.gates[x - n]
                if not (_in(rr, Y.t[a]) and _in(rr, Y.t[b])): good = False; break
                rr = _span_rows(base + [Y.t[y] for y in trial[:trial.index(x) + 1]])
            if good: added = trial
    if not added or len(added) > max_add: return None
    # build X' = X + (operand XORs + AND) for every added product, operands from the current front span
    gates = list(X.c.gates); cur = core.Circuit(n, X.c.m, gates, list(X.c.outputs))
    LXp = LX
    for s in added:
        P = J.Prepared(cur)
        L = LXp
        F = J.Front(cur, P.t, P.l, L)
        op, a, b = Y.c.gates[s - n]
        sigs = []
        for t in (Y.t[a], Y.t[b]):
            f = F.form(t)
            if f is None: return None
            if f in F.have: sigs.append(F.have[f]); continue
            base_f = f & ~1
            g0 = len(gates)
            sg = J._build(n, base_f, gates, F.have)
            if sg is None: return None
            if f & 1:
                gates.append((3, sg, sg)); sg = n + len(gates) - 1
            sigs.append(sg)
        gates.append((op, sigs[0], sigs[1]))
        cur = core.Circuit(n, X.c.m, gates, list(X.c.outputs))
        lv = J.levels(cur); LXp = max(LXp, lv[n + len(gates) - 1])
    return cur, LXp, added


def joinplus_all(X, Y, max_add=4):
    for LY in range(1, Y.AD):
        for LX in sorted({min(LY, X.AD - 1), X.AD - 1}):
            if LX < 1: continue
            r = augment(X, LX, Y, LY, max_add)
            if r is None: continue
            Xp, LXp, added = r
            P = J.Prepared(Xp)
            c, nint = J.join(P.front(LXp), Y, LY)
            if c is not None: yield c, LX, LY, nint, len(added)
