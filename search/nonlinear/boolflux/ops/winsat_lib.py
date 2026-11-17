"""Window exact resynthesis (agent R1, 2026-11-15).

A *window* W is a convex set of gates (no path leaves W and re-enters it).  Its inputs are the
signals outside W read by W gates; its outputs are the W gates read outside W or used as primary
outputs.  Because W is convex, the arrival times (gate level, AND level) of its inputs and the
required times of its outputs (computed from the unchanged consumers, caps D and DA) do not depend
on W's internals.  The *care set* is the set of window-input patterns that occur over all 256
circuit inputs; the window outputs are only needed on those patterns.

`synth` asks SAT (pysat CaDiCaL 1.9.5, conflict budget) for a chain of at most r gates over
{AND, XOR, XNOR, NOT} (NOT = XNOR with a constant-0 node, as NIST writes it) with at most amax
ANDs that realises every window output on the care set and meets every output's gate-level and
AND-level deadline (order-encoded levels).  Patterns are added lazily (CEGAR: solve on a subset,
check the decoded chain on the full care set, add counterexamples).  UNSAT on a subset is UNSAT.
Symmetry breaking: colexicographic order of consecutive independent steps (Knuth 7.1.2), valid
also with unused steps.  The query is monotone in r (unused steps allowed).

`splice` puts the chain in place of W (non-W gates outside TFO(W) first, then the chain, then
TFO(W)), removes dead gates (window-input cones that lost their last reader die too) and merges
functionally identical gates (kept only if it is not worse).
"""
from __future__ import annotations

import random
import time

try:                    # pysat (python-sat) is needed by Synth only: the window code and AND removal
    from pysat.card import CardEnc, EncType      # (winsat_andrm.py, hub/ops/op_andrm.py) run without it
    from pysat.formula import IDPool
    from pysat.solvers import Solver
    HAVE_PYSAT = True
except ImportError:
    CardEnc = EncType = IDPool = Solver = None
    HAVE_PYSAT = False

AND, XOR, XNOR, NOT = 8, 6, 9, 3
INF = 10 ** 6


class Net:
    def __init__(self, c):
        self.c = c; n = c.n; self.n = n; G = c.gates; S = n + len(G); self.S = S
        lv = [0] * S; al = [0] * S; fo = [[] for _ in range(S)]; ins = [()] * S
        for j, (op, a, b) in enumerate(G):
            s = n + j
            ins[s] = (a,) if a == b else (a, b)
            lv[s] = 1 + max(lv[a], lv[b]); al[s] = (op == AND) + max(al[a], al[b])
            for i in ins[s]: fo[i].append(s)
        self.lv, self.al, self.fo, self.ins = lv, al, fo, ins
        self.isout = set(c.outputs)
        self.tab = c.tables()
        self.GD = max(lv[o] for o in c.outputs); self.AD = max(al[o] for o in c.outputs)
        self.A = sum(1 for g in G if g[0] == AND); self.G = len(G)
        self.ands = [n + j for j, g in enumerate(G) if g[0] == AND]

    def op(self, s):
        return self.c.gates[s - self.n][0]

    def tfo(self, W):
        lo = min(W); out = set()
        for s in range(lo + 1, self.S):
            if s in W: continue
            if any(i in W or i in out for i in self.ins[s]): out.add(s)
        return out

    def tfi(self, W):
        hi = max(W); need = set()
        for s in sorted(W, reverse=True): need.update(self.ins[s])
        out = set()
        for s in range(hi, self.n - 1, -1):
            if s in W or s not in need: continue
            if s >= self.n: out.add(s); need.update(self.ins[s])
        return out

    def close(self, W):
        W = set(W)
        while True:
            add = (self.tfo(W) & self.tfi(W)) - W
            if not add: return W
            W |= add

    def info(self, W):
        ins = sorted({i for s in W for i in self.ins[s] if i not in W})
        outs = sorted(s for s in W if s in self.isout or any(f not in W for f in self.fo[s]))
        return ins, outs

    def req_ex(self, W, D, DA):
        """required gate / AND levels with W's internal edges removed (W gates get them from non-W readers)"""
        rq = [INF] * self.S; ra = [INF] * self.S
        for o in self.c.outputs: rq[o] = min(rq[o], D); ra[o] = min(ra[o], DA)
        for s in range(self.S - 1, self.n - 1, -1):
            if s in W: continue
            isand = self.op(s) == AND
            for i in self.ins[s]:
                if rq[s] - 1 < rq[i]: rq[i] = rq[s] - 1
                v = ra[s] - isand
                if v < ra[i]: ra[i] = v
        return rq, ra

    def outside_ok(self, W, T, rq, ra):
        for s in range(self.S):
            if s in W or s in T: continue
            if self.lv[s] > rq[s] or self.al[s] > ra[s]: return False
        return True


# ---------------------------------------------------------------------------------------------
# window selection
def _valid(net, W, K, maxo):
    ins, outs = net.info(W)
    return len(ins) <= K and 1 <= len(outs) <= maxo, ins, outs


def grow(net, seeds, rng, K=8, maxo=4, maxg=9, ming=3, fanin_only=False, stop_at_and=False, crit=None, steps=40, greedy=0.0):
    """randomised growth from seeds; returns the last valid convex window with >= ming gates (prefers larger)"""
    W = net.close(seeds)
    if len(W) > maxg: return None
    best = None
    ok, ins, outs = _valid(net, W, K, maxo)
    if ok and len(W) >= ming: best = set(W)
    tried = set()
    for _ in range(steps):
        cand = set()
        for s in W:
            for i in net.ins[s]:
                if i >= net.n and i not in W: cand.add(i)
            if not fanin_only:
                for f in net.fo[s]:
                    if f not in W: cand.add(f)
        cand -= tried
        if stop_at_and and rng.random() < 0.8:
            c2 = {x for x in cand if net.op(x) != AND}
            if c2: cand = c2
        if crit is not None and rng.random() < 0.8:
            c2 = {x for x in cand if x in crit}
            if c2: cand = c2
        if not cand: break
        if greedy and rng.random() < greedy:
            # MFFC-like growth: the candidate whose addition leaves the fewest outputs, then fewest inputs
            sc = []
            for x in sorted(cand):
                W2 = net.close(W | {x})
                if len(W2) > maxg: continue
                i2, o2 = net.info(W2)
                sc.append((len(o2), len(i2), rng.random(), x))
            if not sc: break
            x = min(sc)[3]
        else:
            x = rng.choice(sorted(cand))
        tried.add(x)
        W2 = net.close(W | {x})
        if len(W2) > maxg: continue
        ins2, outs2 = net.info(W2)
        if len(ins2) > K + 2: continue          # allow temporary excess (growth can lower the input count)
        W = W2
        ok, ins, outs = _valid(net, W, K, maxo)
        if ok and len(W) >= ming: best = set(W)
        if best is not None and len(best) >= maxg: break
        if best is not None and rng.random() < 0.08: break
    return best


def critical(net, D):
    rq = [INF] * net.S
    for o in net.c.outputs: rq[o] = min(rq[o], D)
    for s in range(net.S - 1, net.n - 1, -1):
        for i in net.ins[s]: rq[i] = min(rq[i], rq[s] - 1)
    return {s for s in range(net.n, net.S) if net.lv[s] >= rq[s]}


def pick_window(net, strategy, rng, K=8, maxo=4, maxg=9, greedy=0.5, ming=3):
    n = net.n
    if strategy == 'and' and net.ands:
        g = rng.choice(net.ands)
        return grow(net, {g}, rng, K, maxo, maxg, fanin_only=rng.random() < 0.6, stop_at_and=True, greedy=greedy, ming=ming)
    if strategy == 'pair' and len(net.ands) >= 2:
        # two ANDs sharing an operand or an operand's operand
        for _ in range(20):
            g = rng.choice(net.ands)
            near = set(net.ins[g])
            for i in list(near):
                if i >= n: near.update(net.ins[i])
            mates = set()
            for i in near:
                for f in net.fo[i]:
                    if f != g and net.op(f) == AND: mates.add(f)
                    elif f != g:
                        for f2 in net.fo[f]:
                            if f2 != g and net.op(f2) == AND: mates.add(f2)
            if mates:
                h = rng.choice(sorted(mates))
                return grow(net, {g, h}, rng, K, maxo, maxg, fanin_only=rng.random() < 0.5, stop_at_and=True, greedy=greedy, ming=ming)
        return None
    if strategy == 'reconv':
        g = rng.randrange(n, net.S)
        return grow(net, {g}, rng, K, maxo, maxg, fanin_only=True, greedy=greedy, ming=ming)
    if strategy == 'crit':
        cr = critical(net, net.GD)
        if not cr: return None
        g = rng.choice(sorted(cr))
        return grow(net, {g}, rng, K, maxo, maxg, crit=cr, greedy=greedy, ming=ming)
    if strategy == 'mffc':
        return mffc_window(net, rng.randrange(n, net.S), rng, K, maxo, maxg)
    if strategy == 'bigmffc':       # idea 09: roots drawn by MFFC size (the kernel's most productive targets, U1 3.3)
        sz = mffc_sizes(net)
        roots = [s for s in range(n, net.S) if sz[s] >= 3]
        if not roots: return None
        root = rng.choices(roots, [min(sz[s], maxg) - 2 for s in roots])[0]
        cone = mffc_of(net, root)
        if len(cone) > maxg:           # keep the root and its nearest fan-in part of the cone
            cone = set(sorted(cone, reverse=True)[:maxg])
        return grow(net, cone, rng, K, maxo, maxg, greedy=greedy, ming=ming)
    if strategy == 'and2':          # idea 09: an AND and an AND that reads it (across one AND level), with the XORs between
        for _ in range(20):
            g = rng.choice(net.ands) if net.ands else None
            if g is None: return None
            path = {g}; fr = [(f, (f,)) for f in net.fo[g]]; hit = None
            for _d in range(3):
                nxt = []
                for f, pth in fr:
                    if f in net.ands: hit = pth; break
                    nxt += [(f2, pth + (f2,)) for f2 in net.fo[f]]
                if hit: break
                fr = nxt
            if hit:
                return grow(net, path | set(hit), rng, K, maxo, maxg, greedy=greedy, ming=ming)
        return None
    if strategy == 'viol':          # idea 09: a gate on a critical path (gate level = required level) and its critical fan-in
        cr = critical(net, net.GD)
        if not cr: return None
        g = rng.choice(sorted(cr))
        seeds = {g}
        for i in net.ins[g]:
            if i >= n and i in cr: seeds.add(i)
        return grow(net, seeds, rng, K, maxo, maxg, crit=cr, fanin_only=rng.random() < 0.5, greedy=greedy, ming=ming)
    g = rng.randrange(n, net.S)
    return grow(net, {g}, rng, K, maxo, maxg, greedy=greedy, ming=ming)


def mffc_of(net, root):
    """maximum fanout-free cone of root: root plus the gates all of whose readers are in the cone
    (primary outputs other than root excluded)"""
    n = net.n; cone = {root}
    for s in range(root - 1, n - 1, -1):
        if s in net.isout or not net.fo[s]: continue
        if all(f in cone for f in net.fo[s]):
            # only gates in root's fan-in can be in the cone
            cone.add(s)
    # keep the part connected to root through fan-in edges
    keep = {root}; st = [root]
    while st:
        v = st.pop()
        for i in net.ins[v]:
            if i in cone and i not in keep: keep.add(i); st.append(i)
    return keep


def mffc_sizes(net):
    if getattr(net, '_mffc', None) is None:
        net._mffc = {s: len(mffc_of(net, s)) for s in range(net.n, net.S)}
    return net._mffc


def mffc_window(net, root, rng, K=8, maxo=4, maxg=9):
    """root plus fan-in gates whose readers are all inside (maximum fanout-free cone, in random BFS
    order, bounded by maxg and K): one output; then, with p 0.5, extend by up to two fan-in gates with
    outside readers (2-3 outputs).  Returns the largest valid window seen."""
    n = net.n
    W = {root}; best = None
    for _ in range(4 * maxg):
        fr = [i for s in W for i in net.ins[s] if i >= n and i not in W and i not in net.isout
              and all(f in W for f in net.fo[i])]
        if not fr: break
        x = rng.choice(sorted(set(fr)))
        W2 = W | {x}
        if len(W2) > maxg: break
        W = W2
        ok, ins, outs = _valid(net, W, K, maxo)
        if ok and len(W) >= 3: best = set(W)
    if rng.random() < 0.5:
        for _ in range(2):
            fr = sorted({i for s in W for i in net.ins[s] if i >= n and i not in W})
            if not fr or len(W) >= maxg: break
            W2 = net.close(W | {rng.choice(fr)})
            if len(W2) > maxg: break
            W = W2
            ok, ins, outs = _valid(net, W, K, maxo)
            if ok and len(W) >= 3 and (best is None or len(W) > len(best)): best = set(W)
    return best


# ---------------------------------------------------------------------------------------------
# exact synthesis on a care set
def care(net, ins, outs):
    """distinct window-input patterns over all 256 inputs; per pattern the input bits and output bits"""
    N = 1 << net.n
    tin = [net.tab[i] for i in ins]; tout = [net.tab[o] for o in outs]
    seen = {}
    for x in range(N):
        key = 0
        for b, t in enumerate(tin):
            key |= ((t >> x) & 1) << b
        if key not in seen:
            seen[key] = tuple((t >> x) & 1 for t in tout)
    pats = sorted(seen)
    P = len(pats)
    vin = [sum(((p >> b) & 1) << t for t, p in enumerate(pats)) for b in range(len(ins))]
    tg = [sum(seen[p][h] << t for t, p in enumerate(pats)) for h in range(len(outs))]
    return P, vin, tg


def relation(net, W, ins, outs, T=None, odc=True):
    """Boolean relation of the window: for every output vector v (bit h = output h) the 256-bit mask of
    circuit inputs x at which forcing the window outputs to v keeps every primary output correct
    (exact multi-output observability; odc=False: only the original vector).  Projected to window-input
    patterns: okp[v] bit t = v allowed at every x of pattern t.  Patterns that allow every v are dropped.
    Returns P, vin (per input a P-bit int), okp (2^m P-bit ints), tg (original outputs, P-bit ints)."""
    n = net.n; N = 1 << n; ONES = (1 << N) - 1; m = len(outs)
    T = net.tfo(W) if T is None else T
    tout = [net.tab[o] for o in outs]
    ok = []
    for v in range(1 << m):
        if not odc:
            e = ONES
            for h in range(m): e &= tout[h] if (v >> h) & 1 else ~tout[h] & ONES
            ok.append(e); continue
        val = {o: (ONES if (v >> h) & 1 else 0) for h, o in enumerate(outs)}
        for s in sorted(T):
            op, a, b = net.c.gates[s - n]
            x = val.get(a, net.tab[a]); y = val.get(b, net.tab[b])
            if op == AND: r = x & y
            elif op == XOR: r = x ^ y
            elif op == XNOR: r = ~(x ^ y) & ONES
            elif op == NOT: r = ~x & ONES
            else:
                from boolflux.core import op_apply
                r = op_apply(op, x, y, ONES)
            val[s] = r
        e = ONES
        for o in net.c.outputs:
            if o in val: e &= ~(val[o] ^ net.tab[o]) & ONES
        ok.append(e)
    tin = [net.tab[i] for i in ins]
    pat = {}; px = []
    for x in range(N):
        key = 0
        for b, t in enumerate(tin): key |= ((t >> x) & 1) << b
        px.append(key); pat.setdefault(key, None)
    keys = sorted(pat)
    allow = {kk: (1 << (1 << m)) - 1 for kk in keys}      # per pattern: bit v = v allowed
    for x in range(N):
        bits = 0
        for v in range(1 << m): bits |= ((ok[v] >> x) & 1) << v
        allow[px[x]] &= bits
    full = (1 << (1 << m)) - 1
    keys = [kk for kk in keys if allow[kk] != full]
    P = len(keys)
    vin = [sum(((p >> b) & 1) << t for t, p in enumerate(keys)) for b in range(len(ins))]
    okp = [sum(((allow[p] >> v) & 1) << t for t, p in enumerate(keys)) for v in range(1 << m)]
    rep = {}
    for x in range(N): rep.setdefault(px[x], x)
    tg = [sum(((tout[h] >> rep[p]) & 1) << t for t, p in enumerate(keys)) for h in range(m)]
    return P, vin, okp, tg


def check_rel(y, okp, P):
    """P-bit mask of patterns at which the output vector y (list of P-bit ints) is not allowed"""
    mask = (1 << P) - 1; bad = 0; m = len(y)
    for v in range(1 << m):
        e = mask
        for h in range(m): e &= y[h] if (v >> h) & 1 else ~y[h] & mask
        bad |= e & ~okp[v]
    return bad


def simulate(chain, k, vin, mask):
    v = [0] + list(vin)
    for op, j, l in chain:
        a, b = v[j], v[l]
        if op == AND: v.append(a & b)
        elif op == XOR: v.append(a ^ b)
        elif op == XNOR: v.append(~(a ^ b) & mask)
        else: v.append(~a & mask)
    return v


class Synth:
    def __init__(self, k, P, vin, okp, arr, arra, rq, ra, r, amax, forbid_in=(), seed=1, solver='cadical195', strong=False):
        if not HAVE_PYSAT: raise ImportError('winsat_lib.Synth needs pysat (pip install python-sat)')
        self.k, self.P, self.vin, self.okp, self.r, self.amax = k, P, vin, okp, r, amax
        self.arr = [0] + list(arr); self.arra = [0] + list(arra)
        self.rq, self.ra = rq, ra
        self.m = len(rq); self.mask = (1 << P) - 1
        # per output: patterns at which value 1 (0) is allowed by some allowed vector
        can1 = [0] * self.m; can0 = [0] * self.m
        for v, e in enumerate(okp):
            for h in range(self.m):
                if (v >> h) & 1: can1[h] |= e
                else: can0[h] |= e
        self.pool = IDPool(); self.cl = []
        self.seedr = random.Random(seed)
        V = self.pool.id
        nn = 1 + k + r; self.nn = nn
        self.Lmax = max(rq); self.LAmax = max(ra)
        # steps
        self.pairs = {}
        for i in range(k + 1, nn):
            ps = [(j, l) for l in range(1, i) for j in range(0, l)]   # colex: sorted by (l, j)
            self.pairs[i] = ps
        self.s = {(i, p): V(('s', i, p)) for i in self.pairs for p in self.pairs[i]}
        self.tX = {i: V(('tX', i)) for i in self.pairs}; self.tN = {i: V(('tN', i)) for i in self.pairs}
        self.a = {i: V(('a', i)) for i in self.pairs}
        cl = self.cl
        for i in self.pairs:
            tX, tN, a = self.tX[i], self.tN[i], self.a[i]
            cl += [[-tX, -tN], [tX, tN, a], [-a, -tX], [-a, -tN]]
            lits = [self.s[(i, p)] for p in self.pairs[i]]
            enc = CardEnc.equals(lits, 1, vpool=self.pool, encoding=EncType.seqcounter)
            cl += enc.clauses
            for (j, l) in self.pairs[i]:
                if j == 0: cl.append([-self.s[(i, (j, l))], tN])
        if amax < r:
            enc = CardEnc.atmost([self.a[i] for i in self.pairs], amax, vpool=self.pool, encoding=EncType.seqcounter)
            cl += enc.clauses
        # gate levels (order encoding: u(i, L) = level of i >= L), AND levels likewise
        Lm, LAm = self.Lmax, self.LAmax
        self.u = {(i, L): V(('u', i, L)) for i in self.pairs for L in range(1, Lm + 2)}
        self.ua = {(i, L): V(('ua', i, L)) for i in self.pairs for L in range(1, LAm + 2)}
        for i in self.pairs:
            cl.append([-self.u[(i, Lm + 1)]]); cl.append([-self.ua[(i, LAm + 1)]])
            for L in range(1, Lm + 1): cl.append([-self.u[(i, L + 1)], self.u[(i, L)]])
            for L in range(1, LAm + 1): cl.append([-self.ua[(i, L + 1)], self.ua[(i, L)]])
            ai = self.a[i]
            for (j, l) in self.pairs[i]:
                sv = self.s[(i, (j, l))]
                for v in (j, l):
                    if v > k:
                        for L in range(1, Lm + 1): cl.append([-sv, -self.u[(v, L)], self.u[(i, L + 1)]])
                        for L in range(1, LAm + 1):
                            cl.append([-sv, -self.ua[(v, L)], self.ua[(i, L)]])
                            cl.append([-sv, -self.ua[(v, L)], -ai, self.ua[(i, L + 1)]])
                    else:
                        lv = self.arr[v] + 1
                        if lv > Lm: cl.append([-sv])
                        else: cl.append([-sv, self.u[(i, lv)]])
                        la = self.arra[v]
                        if la > LAm: cl.append([-sv])
                        else:
                            if la >= 1: cl.append([-sv, self.ua[(i, la)]])
                            cl.append([-sv, -ai, self.ua[(i, la + 1)]])
        # strong mode (idea 09): dead steps first in a fixed form, every live step used, no redundant steps
        steps = sorted(self.pairs)
        vmin = min(range(1, k + 1), key=lambda v: (self.arr[v], self.arra[v])) if k else None
        if strong and (vmin is None or self.arr[vmin] + 1 > Lm or r < 1):
            strong = False
        self.strong = strong
        self.d = {}
        if strong:
            dpair = (0, vmin)
            self.d = {i: V(('d', i)) for i in steps}
        # colex symmetry breaking between consecutive steps (not after a dead step in strong mode)
        for i in range(k + 1, nn - 1):
            ps = self.pairs[i]; le = [V(('le', i, q)) for q in range(len(ps))]
            for q in range(len(ps)):
                cl.append([-le[q], self.s[(i, ps[q])]] + ([le[q - 1]] if q else []))
            idx = {p: q for q, p in enumerate(ps)}
            for p2 in self.pairs[i + 1]:
                if i in p2: continue
                q = idx.get(p2)
                if q is None: continue
                cl.append([-self.s[(i + 1, p2)], le[q]] + ([self.d[i]] if strong else []))
        # outputs
        self.o = {}
        for h in range(self.m):
            lits = []
            for v in range(1, nn):
                ov = V(('o', h, v)); self.o[(h, v)] = ov; lits.append(ov)
                if v <= k:
                    vv = vin[v - 1]
                    if ((vv & ~can1[h] & self.mask) or (~vv & ~can0[h] & self.mask) or self.arr[v] > rq[h] or self.arra[v] > ra[h] or (h, v) in forbid_in):
                        cl.append([-ov])
                else:
                    if rq[h] + 1 <= Lm + 1: cl.append([-ov, -self.u[(v, rq[h] + 1)]])
                    if ra[h] + 1 <= LAm + 1: cl.append([-ov, -self.ua[(v, ra[h] + 1)]])
            enc = CardEnc.equals(lits, 1, vpool=self.pool, encoding=EncType.seqcounter)
            cl += enc.clauses
        if strong:
            # Every chain of <= r steps can be written with its dead steps first (each as NOT of input vmin,
            # the earliest window input) and live steps after them, each read by a later step or an output;
            # steps whose function another step or operand already has are removable (fewer live steps,
            # no later arrival), so these clauses keep at least one optimal chain of every query.
            d = self.d
            for idx_, i in enumerate(steps):
                if idx_ + 1 < len(steps): cl.append([-d[steps[idx_ + 1]], d[i]])     # dead(i+1) -> dead(i)
                cl.append([-d[i], self.s[(i, dpair)]]); cl.append([-d[i], self.tN[i]])
                users = [self.s[(i2, p)] for i2 in steps if i2 > i for p in self.pairs[i2] if i in p]
                users += [self.o[(h, i)] for h in range(self.m)]
                cl.append([d[i]] + users)                                             # live -> used
                for u_ in users: cl.append([-d[i], -u_])                              # dead -> unused
            for i in steps:
                for (j, l) in self.pairs[i]:
                    if l <= k: continue
                    sv = self.s[(i, (j, l))]
                    for p in self.pairs[l]:
                        if j not in p: continue
                        sl = self.s[(l, p)]
                        # X(j, X(j, y)) = y and N(j, N(j, y)) = y; AND(j, AND(j, y)) = AND(j, y)
                        cl.append([-sv, -sl, -self.tX[i], -self.tX[l]])
                        cl.append([-sv, -sl, -self.tN[i], -self.tN[l]])
                        cl.append([-sv, -sl, -self.a[i], -self.a[l]])
            for x_, i in enumerate(steps):                                            # no duplicate live steps
                for i2 in steps[x_ + 1:]:
                    for p in self.pairs[i]:
                        s1, s2 = self.s[(i, p)], self.s[(i2, p)]
                        for t1, t2 in ((self.tX[i], self.tX[i2]), (self.tN[i], self.tN[i2]), (self.a[i], self.a[i2])):
                            cl.append([-s1, -s2, -t1, -t2, d[i]])
        self.S = Solver(name=solver, bootstrap_with=cl)
        self.cl = None
        self.pats = []

    def add_pattern(self, t):
        V = self.pool.id; k = self.k
        ival = [0] + [(x >> t) & 1 for x in self.vin]
        x = {i: V(('x', i, t)) for i in self.pairs}
        cl = []
        for i in self.pairs:
            xi = x[i]; tX, tN = self.tX[i], self.tN[i]
            fl = {(0, 0): tN, (0, 1): tX, (1, 0): tX, (1, 1): -tX}
            for (j, l) in self.pairs[i]:
                sv = self.s[(i, (j, l))]
                for p in (0, 1):
                    if j <= k:
                        if ival[j] != p: continue
                        cj = []
                    else:
                        cj = [x[j] if p == 0 else -x[j]]
                    for q in (0, 1):
                        if l <= k:
                            if ival[l] != q: continue
                            cq = []
                        else:
                            cq = [x[l] if q == 0 else -x[l]]
                        f = fl[(p, q)]
                        base = [-sv] + cj + cq
                        cl.append(base + [-xi, f]); cl.append(base + [xi, -f])
        y = [V(('y', h, t)) for h in range(self.m)]
        for h in range(self.m):
            for v in range(1, self.nn):
                ov = self.o[(h, v)]
                if v <= k: cl.append([-ov, y[h] if ival[v] else -y[h]])
                else: cl.append([-ov, -x[v], y[h]]); cl.append([-ov, x[v], -y[h]])
        allowed = [v for v, e in enumerate(self.okp) if (e >> t) & 1]
        fixed = [h for h in range(self.m) if len({(v >> h) & 1 for v in allowed}) == 1]
        for h in fixed:                                  # output bits equal over all allowed vectors: units
            cl.append([y[h] if (allowed[0] >> h) & 1 else -y[h]])
        fm = sum(1 << h for h in fixed)
        for v, e in enumerate(self.okp):
            if not (e >> t) & 1 and not any(((v ^ allowed[0]) >> h) & 1 for h in fixed):
                cl.append([-y[h] if (v >> h) & 1 else y[h] for h in range(self.m) if not (fm >> h) & 1])
        for c in cl: self.S.add_clause(c)
        self.pats.append(t)

    def decode(self):
        mdl = set(l for l in self.S.get_model() if l > 0)
        chain = []
        for i in sorted(self.pairs):
            p = next(p for p in self.pairs[i] if self.s[(i, p)] in mdl)
            j, l = p
            if self.tN[i] in mdl: op = XNOR
            elif self.tX[i] in mdl: op = XOR
            else: op = AND
            if j == 0:
                assert op == XNOR
                chain.append((NOT, l, l))
            else:
                chain.append((op, j, l))
        outmap = [next(v for v in range(1, self.nn) if self.o[(h, v)] in mdl) for h in range(self.m)]
        return chain, outmap

    def run(self, budget, init=16, deadline=None):
        """-> ('sat', chain, outmap) | ('unsat',) | ('unknown',)"""
        P = self.P
        order = list(range(P)); self.seedr.shuffle(order)
        for t in order[:min(init, P)]: self.add_pattern(t)
        while True:
            self.S.conf_budget(budget)
            r = self.S.solve_limited()
            if r is None: return ('unknown',)
            if r is False: return ('unsat',)
            chain, outmap = self.decode()
            v = simulate(chain, self.k, self.vin, self.mask)
            bad = check_rel([v[outmap[h]] for h in range(self.m)], self.okp, self.P)
            if not bad: return ('sat', chain, outmap)
            new = [t for t in order if (bad >> t) & 1 and t not in self.pats][:4]
            assert new
            for t in new: self.add_pattern(t)
            if deadline and time.time() > deadline: return ('unknown',)

    def close(self):
        self.S.delete()


# ---------------------------------------------------------------------------------------------
def prune(chain, outmap, k):
    """drop unused steps; renumber"""
    nn = 1 + k + len(chain)
    used = [False] * nn
    for v in outmap: used[v] = True
    for idx in range(len(chain) - 1, -1, -1):
        i = 1 + k + idx
        if used[i]:
            op, j, l = chain[idx]; used[j] = True; used[l] = True
    new = list(range(1 + k)); out = []
    for idx, (op, j, l) in enumerate(chain):
        i = 1 + k + idx
        if used[i]:
            new.append(1 + k + len(out)); out.append((op, new[j], new[l]))
        else:
            new.append(None)
    return out, [new[v] for v in outmap]


def splice(c, net, W, ins, outs, chain, outmap):
    from boolflux.core import Circuit
    n = c.n; T = net.tfo(W)
    gates = []; new = list(range(n)) + [None] * (net.S - n)

    def emit(op, a, b):
        gates.append((op, a, b)); return n + len(gates) - 1
    for s in range(n, net.S):
        if s in W or s in T: continue
        op, a, b = c.gates[s - n]; new[s] = emit(op, new[a], new[b])
    loc = [None] + [new[i] for i in ins]
    for op, j, l in chain:
        loc.append(emit(op, loc[j], loc[l]))
    for h, o in enumerate(outs): new[o] = loc[outmap[h]]
    for s in sorted(T):
        op, a, b = c.gates[s - n]; new[s] = emit(op, new[a], new[b])
    nc = Circuit(n, c.m, gates, [new[o] for o in c.outputs], c.name, c.in_names, c.out_names)
    return nc.live()


def merge_dups(c):
    from boolflux.core import Circuit
    tabs = c.tables(); n = c.n
    first = {}
    for i in range(n): first.setdefault(tabs[i], i)
    rep = list(range(n)); gates = []
    for j, (op, a, b) in enumerate(c.gates):
        t = tabs[n + j]
        if t in first:
            rep.append(first[t]); continue
        s = n + len(gates); gates.append((op, rep[a], rep[b])); rep.append(s); first[t] = s
    return Circuit(n, c.m, gates, [rep[o] for o in c.outputs], c.name, c.in_names, c.out_names).live()
