"""Exact SAT resynthesis of multi-output windows (track D).

A window W is a convex set of k gates of the current circuit.  Its cut inputs are the signals
outside W read by W (optionally plus extra divisor signals outside the transitive fanout of W);
its outputs are the gates of W read outside W or driving a primary output.

Flexibility is the exact Boolean relation of the window: for every S-box input x and every
vector v of window-output values, simulate the rest of the circuit with the window outputs
forced to v; v is allowed at x iff all 8 S-box outputs are correct at x.  Inputs x with the
same window-input pattern p must share the window's output, so the allowed set at p is the
intersection over those x.  Patterns that never occur are free.  This captures satisfiability
and (multi-output, compatible-by-construction) observability don't-cares exactly.

Exact synthesis: SAT model of an r-gate program over the window inputs with gate types
{AND, XOR, XNOR, NOT}, simulated on the occurring patterns only, outputs chosen among inputs and
new gates, output values constrained by the relation, plus unary gate-depth / AND-depth
variables against per-output required levels (from the rest of the circuit and the caps) and
a cardinality bound on AND gates.  See README.md for the clause list.
"""
from __future__ import annotations

import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parents[1]                     # nonlinear/boolflux
sys.path.insert(0, str(PKG.parent))       # nonlinear
from boolflux import core, targets        # noqa: E402

from pysat.card import CardEnc, EncType   # noqa: E402
from pysat.formula import IDPool          # noqa: E402
from pysat.solvers import Solver          # noqa: E402

AND, XOR, XNOR, NOT = 8, 6, 9, 3
LIB = (AND, XOR, XNOR, NOT)
N = 256
ONES = (1 << N) - 1


def target_tables():
    return core.tables_from_values(8, 8, targets.aes_sbox())


TGT = None


def tgt():
    global TGT
    if TGT is None:
        TGT = target_tables()
    return TGT


class State:
    """Analysis of the current circuit: tables, levels, fanouts, tails."""

    def __init__(self, c: core.Circuit):
        self.c = c
        n = c.n
        self.n = n
        self.S = n + len(c.gates)
        self.tab = c.tables()
        self.lg = [0] * self.S
        self.la = [0] * self.S
        self.fo = [[] for _ in range(self.S)]
        for j, (op, a, b) in enumerate(c.gates):
            s = n + j
            self.lg[s] = 1 + max(self.lg[a], self.lg[b])
            self.la[s] = (1 if op == AND else 0) + max(self.la[a], self.la[b])
            self.fo[a].append(s)
            if b != a:
                self.fo[b].append(s)
        self.ispo = [False] * self.S
        for s in c.outputs:
            self.ispo[s] = True
        # tails: longest path (gate count / AND count) from signal to any primary output
        NEG = -10 ** 6
        self.tg = [NEG] * self.S
        self.ta = [NEG] * self.S
        for s in range(self.S - 1, -1, -1):
            tg = 0 if self.ispo[s] else NEG
            ta = 0 if self.ispo[s] else NEG
            for f in self.fo[s]:
                tg = max(tg, 1 + self.tg[f])
                ta = max(ta, (1 if c.gates[f - n][0] == AND else 0) + self.ta[f])
            self.tg[s] = tg
            self.ta[s] = ta
        m = c.metrics()
        self.G, self.A, self.GD, self.AD = m['G'], m['A'], m['GD'], m['AD']

    def op(self, s):
        return self.c.gates[s - self.n][0]

    def fanin(self, s):
        op, a, b = self.c.gates[s - self.n]
        return (a,) if (op == NOT or a == b) else (a, b)


# ---------------------------------------------------------------------------------------------
# window selection

def enum_cuts(st: State, K: int, L: int, rng: random.Random):
    """Priority cuts: for each signal up to L cuts (frozensets of signals) of size <= K."""
    n = st.n
    cuts = [None] * st.S
    for i in range(n):
        cuts[i] = [frozenset([i])]
    for s in range(n, st.S):
        fi = st.fanin(s)
        res = set()
        if len(fi) == 1:
            res.update(cuts[fi[0]])
        else:
            for ca in cuts[fi[0]]:
                for cb in cuts[fi[1]]:
                    u = ca | cb
                    if len(u) <= K:
                        res.add(u)
        res = list(res)
        if len(res) > L - 1:
            # keep the larger cuts preferentially (bigger cones), random tie-break
            rng.shuffle(res)
            res.sort(key=lambda u: -len(u))
            res = res[:L // 2] + rng.sample(res[L // 2:], min(L - 1 - L // 2, len(res) - L // 2))
        res.append(frozenset([s]))
        cuts[s] = res
    return cuts


def cut_window(st: State, root: int, cut, kmax: int, rng: random.Random, sib=True):
    """Window = cone of root over cut, plus (if sib) other gates computable from the cut whose
    level does not exceed the root's; trimmed to kmax, then made convex."""
    n = st.n
    inside = set()
    cutset = set(cut)
    # cone
    stack = [root]
    while stack:
        s = stack.pop()
        if s in inside or s in cutset or s < n:
            continue
        inside.add(s)
        stack.extend(st.fanin(s))
    cone = set(inside)
    if sib:
        lo = min(cone)
        extra = []
        closure = set()
        for s in range(lo, root + 1):
            if s in cutset:
                continue
            if all(a in cutset or a in closure or a in cone for a in st.fanin(s)):
                closure.add(s)
                if s not in cone and st.lg[s] <= st.lg[root]:
                    extra.append(s)
        rng.shuffle(extra)
        for s in extra:
            if len(inside) >= kmax:
                break
            # only add if its fanins are in cut or inside (keeps the window inside the closure)
            if all(a in cutset or a in inside for a in st.fanin(s)):
                inside.add(s)
    if len(inside) > kmax + 4 or len(inside) < 2:
        return None
    W = convexify(st, inside)
    if W is None or len(W) > kmax + 4:
        return None
    return W


def grow_window(st: State, seed: int, k: int, rng: random.Random, cmax: int, bias_fanin=0.6,
                crit=None):
    """Random connected window of up to k gates grown from gate signal `seed`."""
    n = st.n
    W = {seed}
    tries = 0
    while len(W) < k and tries < 4 * k:
        tries += 1
        cand_in = set()
        cand_out = set()
        for s in W:
            for a in st.fanin(s):
                if a >= n and a not in W:
                    cand_in.add(a)
            for f in st.fo[s]:
                if f not in W:
                    cand_out.add(f)
        if crit is not None:
            ci = [a for a in cand_in if crit[a]]
            co = [f for f in cand_out if crit[f]]
            if (ci or co) and rng.random() < 0.7:
                cand_in, cand_out = set(ci), set(co)
        pool = None
        if cand_in and (not cand_out or rng.random() < bias_fanin):
            pool = cand_in
        elif cand_out:
            pool = cand_out
        if not pool:
            break
        W.add(rng.choice(sorted(pool)))
        W = convexify(st, W)
        if W is None:
            return None
    if W is None or len(W) > k + 3:
        return None
    return W


def convexify(st: State, W):
    """Add every outside gate lying on a path between two window gates."""
    n = st.n
    for _ in range(10):
        lo = min(W)
        # forward reach from W through outside gates
        fwd = set()
        stack = [f for s in W for f in st.fo[s] if f not in W]
        while stack:
            s = stack.pop()
            if s in fwd:
                continue
            fwd.add(s)
            stack.extend(f for f in st.fo[s] if f not in W and f not in fwd)
        if not fwd:
            return W
        # backward reach from W through outside gates (only gates >= lo can be on a path)
        bwd = set()
        stack = [a for s in W for a in st.fanin(s) if a >= n and a not in W and a >= lo]
        while stack:
            s = stack.pop()
            if s in bwd:
                continue
            bwd.add(s)
            stack.extend(a for a in st.fanin(s) if a >= n and a not in W and a >= lo and a not in bwd)
        both = fwd & bwd
        if not both:
            return W
        W = W | both
    return None


class Window:
    pass


def analyse(st: State, W, ndiv=0, rng=None, mmax=8, cmax=12, capGD=None, capAD=None,
            tcrit=None):
    """Cut inputs, outputs, patterns, relation and timing of window W. None if out of limits."""
    n = st.n
    c = st.c
    Wl = sorted(W)
    ins = []
    for s in Wl:
        for a in st.fanin(s):
            if a not in W and a not in ins:
                ins.append(a)
    outs = [s for s in Wl if st.ispo[s] or any(f not in W for f in st.fo[s])]
    if len(outs) > mmax or len(outs) == 0 or len(ins) > cmax:
        return None
    # transitive fanout of the window (outside gates), topological order
    tfo = set()
    stack = [f for s in outs for f in st.fo[s] if f not in W]
    while stack:
        s = stack.pop()
        if s in tfo:
            continue
        tfo.add(s)
        stack.extend(st.fo[s])
    tfo_l = sorted(tfo)
    # extra divisors: signals outside W and its TFO, near the window inputs
    divs = []
    if ndiv > 0 and rng is not None:
        near = set()
        for a in ins:
            if a >= n:
                near.update(st.fanin(a))
            near.update(st.fo[a])
        for s in W:
            for a in st.fanin(s):
                if a >= n:
                    for b in st.fanin(a):
                        if b >= n:
                            near.update(st.fanin(b))
        near = [s for s in near if s not in W and s not in tfo and s not in ins]
        if capGD is not None:
            near = [s for s in near if st.lg[s] < capGD]
        rng.shuffle(near)
        divs = near[:ndiv]
    allin = ins + divs
    if len(allin) > cmax + ndiv:
        return None
    if rng is not None:
        rng.shuffle(allin)
        ins_set = set(ins)
    # window-input patterns
    tabs = [st.tab[s] for s in allin]
    pat_of = [0] * N
    for j, t in enumerate(tabs):
        for x in range(N):
            if (t >> x) & 1:
                pat_of[x] |= 1 << j
    classes = {}
    for x in range(N):
        classes.setdefault(pat_of[x], 0)
        classes[pat_of[x]] |= 1 << x
    pats = sorted(classes)
    m = len(outs)
    # relation: ok mask per output vector v
    T = tgt()
    base = st.tab
    oks = []
    gates = c.gates
    for v in range(1 << m):
        vals = {}
        for i, s in enumerate(outs):
            vals[s] = ONES if (v >> i) & 1 else 0
        for s in tfo_l:
            op, a, b = gates[s - n]
            va = vals[a] if a in vals else base[a]
            vb = vals[b] if b in vals else base[b]
            if op == AND:
                r = va & vb
            elif op == XOR:
                r = va ^ vb
            elif op == XNOR:
                r = ~(va ^ vb) & ONES
            elif op == NOT:
                r = ~va & ONES
            else:
                r = core.op_apply(op, va, vb, ONES)
            vals[s] = r
        ok = ONES
        for j, s in enumerate(c.outputs):
            vs = vals[s] if s in vals else base[s]
            ok &= ~(vs ^ T[j])
        oks.append(ok & ONES)
    orig_v = {}
    allowed = []
    for p in pats:
        X = classes[p]
        al = [v for v in range(1 << m) if (oks[v] & X) == X]
        allowed.append(al)
    # sanity: original output vector allowed
    for pi, p in enumerate(pats):
        X = classes[p]
        x0 = (X & -X).bit_length() - 1
        v0 = 0
        for i, s in enumerate(outs):
            if (base[s] >> x0) & 1:
                v0 |= 1 << i
        assert v0 in allowed[pi], 'relation excludes original'
        orig_v[p] = v0
    w = Window()
    w.gates = Wl
    w.ins = allin
    w.ncut = len(ins)
    w.outs = outs
    w.pats = pats
    w.allowed = allowed
    w.k = len(Wl)
    w.a = sum(1 for s in Wl if st.op(s) == AND)
    w.old_ops = [st.op(s) for s in Wl]
    w.rep = [(classes[p] & -classes[p]).bit_length() - 1 for p in pats]
    w.internal = [s for s in Wl if s not in outs]
    w.arr_g = [st.lg[s] for s in allin]
    w.arr_a = [st.la[s] for s in allin]
    # required levels
    capG = capGD if capGD is not None else st.GD
    capA = capAD if capAD is not None else st.AD
    w.req_g = []
    w.req_a = []
    for s in outs:
        tg = 0 if st.ispo[s] else -10 ** 6
        ta = 0 if st.ispo[s] else -10 ** 6
        for f in st.fo[s]:
            if f not in W:
                tg = max(tg, 1 + st.tg[f])
                ta = max(ta, (1 if st.op(f) == AND else 0) + st.ta[f])
        w.req_g.append(capG - tg)
        w.req_a.append(capA - ta)
    w.nfree = sum(1 for al in allowed if len(al) > 1)
    return w


# ---------------------------------------------------------------------------------------------
# SAT encoding

def pattern_clauses(w, r, pool, p, nots=True):
    """Simulation, output-value and relation clauses of one pattern index p."""
    V = pool.id
    cl = []
    c = len(w.ins)
    S = c + r
    m = len(w.outs)
    inval = [(w.pats[p] >> j) & 1 for j in range(c)]
    for i in range(r):
        g = c + i
        tA, tX, tXN = V(('t', i, AND)), V(('t', i, XOR)), V(('t', i, XNOR))
        a = V(('a', i, p))
        b = V(('b', i, p))
        xv = V(('x', g, p))
        for j in range(g):
            Lj = V(('l', i, j))
            Rj = V(('r', i, j))
            if j < c:
                v = inval[j]
                cl.append([-Lj, a if v else -a])
                cl.append([-Rj, b if v else -b])
            else:
                xj = V(('x', j, p))
                cl.append([-Lj, -xj, a])
                cl.append([-Lj, xj, -a])
                cl.append([-Rj, -xj, b])
                cl.append([-Rj, xj, -b])
        cl.append([-tA, -xv, a])
        cl.append([-tA, -xv, b])
        cl.append([-tA, xv, -a, -b])
        cl.append([-tX, -xv, a, b])
        cl.append([-tX, -xv, -a, -b])
        cl.append([-tX, xv, -a, b])
        cl.append([-tX, xv, a, -b])
        cl.append([-tXN, xv, a, b])
        cl.append([-tXN, xv, -a, -b])
        cl.append([-tXN, -xv, -a, b])
        cl.append([-tXN, -xv, a, -b])
        if nots:
            tN = V(('t', i, NOT))
            cl.append([-tN, xv, a])
            cl.append([-tN, -xv, -a])
    for o in range(m):
        y = V(('y', o, p))
        for s in range(S):
            ws = V(('w', o, s))
            if s < c:
                cl.append([-ws, y if inval[s] else -y])
            else:
                xs = V(('x', s, p))
                cl.append([-ws, -xs, y])
                cl.append([-ws, xs, -y])
    full = 1 << m
    al = w.allowed[p]
    if len(al) < full:
        alset = set(al)
        fixed = {}
        for o in range(m):
            bits = {(v >> o) & 1 for v in al}
            if len(bits) == 1:
                fixed[o] = bits.pop()
                y = V(('y', o, p))
                cl.append([y if fixed[o] else -y])
        for v in range(full):
            if v in alset:
                continue
            if any(((v >> o) & 1) != fv for o, fv in fixed.items()):
                continue
            cl.append([(-V(('y', o, p)) if (v >> o) & 1 else V(('y', o, p))) for o in range(m) if o not in fixed])
    return cl


def encode(w, r, amax, use_depth=True, use_ad=True, nots=True, req_g=None, req_a=None, colex=True,
           forbid=(), pidx=None):
    """CNF for: an r-gate program over w.ins realising the window relation on the patterns
    pidx (default all)."""
    pool = IDPool()
    V = pool.id
    cl = []
    c = len(w.ins)
    P = len(w.pats)
    S = c + r
    req_g = req_g if req_g is not None else w.req_g
    req_a = req_a if req_a is not None else w.req_a
    m = len(w.outs)
    plist = list(range(P)) if pidx is None else list(pidx)

    def x(s, p):
        return V(('x', s, p))

    types = (AND, XOR, XNOR, NOT) if nots else (AND, XOR, XNOR)
    for i in range(r):
        g = c + i
        # operand selection
        L = [V(('l', i, j)) for j in range(g)]
        R = [V(('r', i, j)) for j in range(g)]
        T = [V(('t', i, t)) for t in types]
        for lits in (L, R, T):
            enc = CardEnc.equals(lits=lits, bound=1, vpool=pool, encoding=EncType.pairwise
                                 if len(lits) <= 6 else EncType.seqcounter)
            cl.extend(enc.clauses)
        tN = V(('t', i, NOT)) if nots else None
        for j in range(g):
            for kk in range(j + 1):
                if nots:
                    cl.append([-L[j], -R[kk], tN])     # binary gates: l < r
                else:
                    cl.append([-L[j], -R[kk]])
            if nots:
                cl.append([-tN, -L[j], R[j]])          # NOT: r = l
    # outputs
    Wsel = []
    for o in range(m):
        lits = [V(('w', o, s)) for s in range(S)]
        Wsel.append(lits)
        enc = CardEnc.equals(lits=lits, bound=1, vpool=pool, encoding=EncType.seqcounter)
        cl.extend(enc.clauses)
    # simulation + relation on the chosen patterns
    for p in plist:
        cl.extend(pattern_clauses(w, r, pool, p, nots))
    # forbidden functions: no new gate equals any vector in forbid (one bit per pattern)
    for fv in forbid:
        for i in range(r):
            cl.append([(-x(c + i, p) if fv[p] else x(c + i, p)) for p in plist])
    # every gate used
    for i in range(r):
        g = c + i
        lits = [V(('l', i2, g)) for i2 in range(i + 1, r)] + \
               [V(('r', i2, g)) for i2 in range(i + 1, r)] + [Wsel[o][g] for o in range(m)]
        cl.append(lits)
    # symmetry breaking: adjacent independent gates in co-lexicographic order of (r, l)
    if colex:
        for i in range(r - 1):
            g = c + i
            gi1 = g + 1
            u1 = V(('l', i + 1, g))
            u2 = V(('r', i + 1, g))
            for ra in range(g):
                for rb in range(g):
                    if ra > rb:
                        cl.append([u1, u2, -V(('r', i, ra)), -V(('r', i + 1, rb))])
                    elif ra == rb:
                        for la in range(ra + 1):
                            for lb in range(la):
                                cl.append([u1, u2, -V(('r', i, ra)), -V(('r', i + 1, rb)),
                                           -V(('l', i, la)), -V(('l', i + 1, lb))])
    # depth (gate levels), unary: D(s, l) = level(s) >= l
    if use_depth:
        Lmax = max(req_g)
        if Lmax < 1 and r > 0:
            return None
        for i in range(r):
            g = c + i

            def D(s, l):
                return V(('D', s, l))
            cl.append([D(g, 1)])
            for l in range(1, Lmax + 1):
                cl.append([-D(g, l + 1), D(g, l)])
            cl.append([-D(g, Lmax + 1)])
            for j in range(g):
                for sel in (V(('l', i, j)), V(('r', i, j))):
                    if j < c:
                        need = w.arr_g[j] + 1
                        if need > Lmax:
                            cl.append([-sel])
                        else:
                            cl.append([-sel, D(g, need)])
                    else:
                        for l in range(1, Lmax + 1):
                            cl.append([-sel, -D(j, l), D(g, l + 1)])
        for o in range(m):
            for s in range(S):
                if s < c:
                    if w.arr_g[s] > req_g[o]:
                        cl.append([-Wsel[o][s]])
                else:
                    if req_g[o] < 1:
                        cl.append([-Wsel[o][s]])
                    elif req_g[o] + 1 <= Lmax + 1:
                        cl.append([-Wsel[o][s], -V(('D', s, req_g[o] + 1))])
    if use_ad:
        LA = max(req_a)
        for i in range(r):
            g = c + i

            def E(s, l):
                return V(('E', s, l))
            tA = V(('t', i, AND))
            if LA < 1:
                cl.append([-tA])
            else:
                cl.append([-tA, E(g, 1)])
            for l in range(1, LA + 1):
                cl.append([-E(g, l + 1), E(g, l)])
            cl.append([-E(g, LA + 1)])
            for j in range(g):
                for sel in (V(('l', i, j)), V(('r', i, j))):
                    if j < c:
                        aj = w.arr_a[j]
                        if aj > LA:
                            cl.append([-sel])
                            continue
                        if aj >= 1:
                            cl.append([-sel, E(g, aj)])
                        if aj + 1 > LA:
                            cl.append([-sel, -tA])
                        else:
                            cl.append([-sel, -tA, E(g, aj + 1)])
                    else:
                        for l in range(1, LA + 1):
                            cl.append([-sel, -E(j, l), E(g, l)])
                            cl.append([-sel, -E(j, l), -tA, E(g, l + 1)])
        for o in range(m):
            for s in range(S):
                if s < c:
                    if w.arr_a[s] > req_a[o]:
                        cl.append([-Wsel[o][s]])
                else:
                    if req_a[o] < 0:
                        cl.append([-Wsel[o][s]])
                    elif req_a[o] + 1 <= LA + 1:
                        cl.append([-Wsel[o][s], -V(('E', s, req_a[o] + 1))])
    # AND count
    if amax is not None:
        tAs = [V(('t', i, AND)) for i in range(r)]
        if amax <= 0:
            cl.extend([[-t] for t in tAs])
        elif amax < r:
            enc = CardEnc.atmost(lits=tAs, bound=amax, vpool=pool, encoding=EncType.seqcounter)
            cl.extend(enc.clauses)
    return pool, cl, types


def eval_prog(w, prog, outsel, p):
    ci = len(w.ins)
    pv = w.pats[p]
    vals = [(pv >> j) & 1 for j in range(ci)]
    for (t, a, b) in prog:
        va, vb = vals[a], vals[b]
        vals.append(va & vb if t == AND else va ^ vb if t == XOR else 1 - (va ^ vb) if t == XNOR else 1 - va)
    v = 0
    for o, s in enumerate(outsel):
        v |= vals[s] << o
    return v


def solve(w, r, amax, budget=20000, solver="cadical195", cegis=False, seed_pats=12, rng=None, **kw):
    """Return (status, program) with status True/False/None (budget).  With cegis, start from a
    few constrained patterns and add failing ones (incrementally) until the program is correct on
    all patterns; UNSAT on a subset proves UNSAT.  The conflict budget is shared by all rounds."""
    P = len(w.pats)
    full = 1 << len(w.outs)
    if kw.get('forbid'):
        cegis = False
    cons = [p for p in range(P) if len(w.allowed[p]) < full]
    if cegis and len(cons) > seed_pats:
        rr = rng or random.Random(P * 7919 + r)
        pidx = rr.sample(cons, seed_pats)
    else:
        pidx = None
        cegis = False
    enc = encode(w, r, amax, pidx=pidx, **kw)
    if enc is None:
        return False, None
    pool, cl, types = enc
    s = Solver(name=solver, bootstrap_with=cl)
    c = len(w.ins)
    V = pool.id
    left = budget
    used = set(pidx or ())
    try:
        while True:
            if budget:
                s.conf_budget(max(1, left))
                res = s.solve_limited()
                try:
                    left = budget - int(s.accum_stats().get('conflicts', 0))
                except Exception:
                    left -= budget // 4
            else:
                res = s.solve()
            if not res:
                return res, None
            model = set(l for l in s.get_model() if l > 0)
            prog, outsel = decode(model, V, types, c, r, len(w.outs))
            if not cegis:
                break
            bad = [p for p in cons if p not in used and eval_prog(w, prog, outsel, p) not in w.allowed[p]]
            if not bad:
                break
            add = bad[:3] + ([bad[len(bad) // 2]] if len(bad) > 6 else [])
            for p in add:
                used.add(p)
                for cc in pattern_clauses(w, r, pool, p, kw.get('nots', True)):
                    s.add_clause(cc)
            if budget and left <= 0:
                return None, None
    finally:
        s.delete()
    return True, (prog, outsel)


def decode(model, V, types, c, r, m):
    prog = []
    for i in range(r):
        g = c + i
        t = [tt for tt in types if V(('t', i, tt)) in model][0]
        l = [j for j in range(g) if V(('l', i, j)) in model][0]
        rr = [j for j in range(g) if V(('r', i, j)) in model][0]
        prog.append((t, l, rr))
    outsel = [[s_ for s_ in range(c + r) if V(('w', o, s_)) in model][0] for o in range(m)]
    return prog, outsel


# ---------------------------------------------------------------------------------------------
# replacement

def apply(st: State, w, prog, outsel):
    """New circuit with window w replaced by prog (topologically re-sorted, dead gates dropped)."""
    c = st.c
    n = c.n
    Wset = set(w.gates)
    # node ids: ('o', s) original signal, ('w', i) new gate
    nodes = {}
    ci = len(w.ins)

    def win_sig(j):
        return ('o', w.ins[j]) if j < ci else ('w', j - ci)
    for i, (t, a, b) in enumerate(prog):
        nodes[('w', i)] = (t, win_sig(a), win_sig(b if t != NOT else a))
    remap = {}
    for o, s in enumerate(w.outs):
        remap[s] = win_sig(outsel[o])

    def ref(s):
        if s in remap:
            return remap[s]
        return ('o', s)
    for j, (op, a, b) in enumerate(c.gates):
        s = n + j
        if s in Wset:
            continue
        nodes[('o', s)] = (op, ref(a), ref(b))
    outs = [ref(s) for s in c.outputs]
    # DFS topological order from outputs
    order = []
    seen = set()
    for root in outs:
        stack = [(root, 0)]
        while stack:
            u, st_ = stack.pop()
            if u in seen and st_ == 0:
                continue
            if u[0] == 'o' and u[1] < n:
                seen.add(u)
                continue
            if st_ == 0:
                seen.add(u)
                stack.append((u, 1))
                op, a, b = nodes[u]
                for v in (b, a):
                    if v not in seen:
                        stack.append((v, 0))
            else:
                order.append(u)
    idx = {('o', i): i for i in range(n)}
    gates = []
    for u in order:
        op, a, b = nodes[u]
        idx[u] = n + len(gates)
        gates.append(core.canonical(op, idx[a], idx[b]) if op != NOT else (NOT, idx[a], idx[a]))
    nc = core.Circuit(n, c.m, gates, [idx[u] for u in outs], c.name, c.in_names, c.out_names)
    return nc


def correct(c):
    return c.value_table() == targets.aes_sbox()


def sim_check(w, prog, outsel, st):
    """Check the program on the window patterns against the relation (cheap pre-check)."""
    ci = len(w.ins)
    for pi, p in enumerate(w.pats):
        vals = [(p >> j) & 1 for j in range(ci)]
        for (t, a, b) in prog:
            va, vb = vals[a], vals[b]
            vals.append(va & vb if t == AND else va ^ vb if t == XOR else 1 - (va ^ vb) if t == XNOR else 1 - va)
        v = 0
        for o, s in enumerate(outsel):
            v |= vals[s] << o
        if v not in w.allowed[pi]:
            return False
    return True
