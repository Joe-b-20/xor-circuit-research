"""AND merge / split moves on the product program of a circuit.

Representation ("product program").  Atoms: bit 0 = constant 1, bits 1..n = inputs, every AND gets
its own bit.  Every linear signal is an affine form = bitmask over atoms.  The program is
    ands[bit] = [L, R]   (the AND computes L*R, L and R forms over other atoms)
    outs      = [form, ...]
The XOR network is forgotten; it is rebuilt from the forms when a circuit is materialised.

Exact identities used (all over GF(2), functions on the 2^n inputs):
  flip    p_i = a*b_i + l_i, p_j = a*b_j + l_j (a shared factor modulo constants; l affine in the
          operands).  New product q = a*(b_i + b_j); then p_i = q + p_j + l_i + l_j.  p_i is
          replaced by q everywhere (substitution in every form that reads p_i).  The number of
          ANDs is unchanged; p_j is now read wherever p_i was read (in addition to its own uses).
          If p_i and p_j were read by exactly the same forms, p_j is no longer read: -1 AND (merge).
  split   p_i = a*b = a*(b + c) + a*c for any form c that does not depend on p_i: +1 AND.
  dep     a linear dependency between the truth tables of {1, inputs, products} removes one AND.
Invariant (checked): a flip does not change span{1, inputs, products} (as functions); a split adds one
dimension.  So flips alone only reach circuits whose products are sums of the original products
plus affine functions; dependencies cannot appear by flips if there were none.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PKG.parent))
from boolflux import core  # noqa: E402

XOR, XNOR, NOT, AND = 6, 9, 3, 8


def bits(m):
    while m:
        b = m & -m
        yield b.bit_length() - 1
        m ^= b


class Prog:
    def __init__(self, n, m):
        self.n = n; self.m = m
        self.ands = {}            # bit -> [L, R]
        self.outs = []
        self.nextbit = n + 1

    def copy(self):
        p = Prog(self.n, self.m)
        p.ands = {k: list(v) for k, v in self.ands.items()}
        p.outs = list(self.outs); p.nextbit = self.nextbit
        return p

    @property
    def A(self):
        return len(self.ands)

    def newbit(self):
        used = self.ands
        b = self.n + 1
        while b in used: b += 1
        return b

    # ---- structure -----------------------------------------------------------------------
    def pmask(self):
        m = 0
        for k in self.ands: m |= 1 << k
        return m

    def topo(self):
        """product bits in dependency order (raises on a cycle)"""
        pm = self.pmask(); order = []; state = {}
        for root in sorted(self.ands):
            if root in state: continue
            stack = [(root, None)]
            while stack:
                k, it = stack[-1]
                if it is None:
                    if state.get(k) == 2: stack.pop(); continue
                    state[k] = 1
                    it = iter(list(bits((self.ands[k][0] | self.ands[k][1]) & pm)))
                    stack[-1] = (k, it)
                for d in it:
                    s = state.get(d)
                    if s == 1: raise ValueError('cycle')
                    if s is None:
                        stack.append((d, None)); break
                else:
                    state[k] = 2; order.append(k); stack.pop()
        return order

    def depends(self, j, i):
        """does product j depend (transitively) on product i"""
        pm = self.pmask(); seen = 0; todo = (self.ands[j][0] | self.ands[j][1]) & pm
        ib = 1 << i
        while todo:
            if todo & ib: return True
            b = todo & -todo; todo ^= b
            if seen & b: continue
            seen |= b
            L, R = self.ands[b.bit_length() - 1]
            todo |= (L | R) & pm & ~seen
        return False

    def tfo(self, i):
        """mask of products depending on product i"""
        m = 0
        for k in self.topo():
            L, R = self.ands[k]
            if (L | R) & (m | (1 << i)): m |= 1 << k
        return m

    def and_levels(self):
        lv = {}
        for k in self.topo():
            L, R = self.ands[k]
            lv[k] = 1 + max([lv[d] for d in bits((L | R) & self.pmask())] + [0])
        return lv

    # ---- tables --------------------------------------------------------------------------
    def tables(self):
        n = self.n; ones = (1 << (1 << n)) - 1
        T = {0: ones}
        for i, t in enumerate(core.input_tables(n)): T[i + 1] = t

        def ft(f):
            t = 0
            for b in bits(f): t ^= T[b]
            return t
        for k in self.topo():
            L, R = self.ands[k]
            T[k] = ft(L) & ft(R)
        return T, ft

    def out_tables(self):
        T, ft = self.tables()
        return [ft(o) for o in self.outs]

    # ---- reductions ------------------------------------------------------------------------
    def forms(self):
        for k, (L, R) in self.ands.items():
            yield L; yield R
        yield from self.outs

    def remove_dead(self):
        n = 0
        while True:
            used = 0
            for f in self.forms(): used |= f
            dead = [k for k in self.ands if not (used >> k) & 1]
            if not dead: return n
            for k in dead: del self.ands[k]; n += 1

    def substitute(self, i, delta, keep=False):
        """every form reading bit i gets ^= delta (and loses bit i unless keep)"""
        ib = 1 << i; d = delta if keep else delta ^ ib
        for k, LR in self.ands.items():
            if LR[0] & ib: LR[0] ^= d
            if LR[1] & ib: LR[1] ^= d
        self.outs = [o ^ d if o & ib else o for o in self.outs]

    def remove_dependent(self):
        """Gaussian elimination on the tables of 1, inputs, products (dependency order): a product
        whose table is a combination of earlier atoms is substituted away.  Returns number removed."""
        removed = 0
        while True:
            T, ft = self.tables()
            piv = []      # (pivot position, table, combination mask)
            hit = None
            for b in list(range(self.n + 1)) + self.topo():
                t = T[b]; f = 1 << b
                for p, rt, rf in piv:
                    if (t >> p) & 1: t ^= rt; f ^= rf
                if t:
                    piv.append((t.bit_length() - 1, t, f))
                elif b > self.n:
                    hit = (b, f ^ (1 << b)); break
            if hit is None: return removed
            b, delta = hit
            self.substitute(b, delta)
            del self.ands[b]; removed += 1
            self.remove_dead()

    def reduce(self):
        r = self.remove_dead()
        r += self.remove_dependent()
        return r

    # ---- moves -------------------------------------------------------------------------------
    @staticmethod
    def span3(L, R):
        L0 = L & ~1; R0 = R & ~1
        return (L0, R0, L0 ^ R0)

    @staticmethod
    def factor(L, R, a):
        """(b, lam) with L*R = a*b + lam, for a in span3(L, R)"""
        L0 = L & ~1; R0 = R & ~1
        if a == L0: return R, (R if L & 1 else 0)
        if a == R0: return L, (L if R & 1 else 0)
        assert a == L0 ^ R0
        return L, (0 if (L ^ R) & 1 else L)

    def flip(self, i, j, a):
        """replace product i by q = a*(b_i + b_j); p_i = q + p_j + lam_i + lam_j.  Caller guarantees
        that j does not depend on i.  Returns False (nothing changed) if q would be affine."""
        Li, Ri = self.ands[i]; Lj, Rj = self.ands[j]
        bi, li = self.factor(Li, Ri, a); bj, lj = self.factor(Lj, Rj, a)
        b = bi ^ bj
        b0 = b & ~1
        if b0 == 0 or b0 == a: return False
        self.substitute(i, (1 << j) ^ li ^ lj, keep=True)
        self.ands[i] = [a, b]
        return True

    def split(self, i, a, c):
        """p_i = a*b = a*(b + c) + a*c: new product a*c read wherever p_i is read.  a in span3 of i,
        c a form not depending on p_i (caller checks).  Returns the new bit, or None if degenerate."""
        Li, Ri = self.ands[i]
        bi, li = self.factor(Li, Ri, a)
        b = bi ^ c
        if (b & ~1) in (0, a) or (c & ~1) in (0, a): return None
        k = self.newbit()
        self.substitute(i, (1 << k) ^ li, keep=True)
        self.ands[i] = [a, b]
        self.ands[k] = [a, c]
        return k

    def usage(self):
        """bit -> frozenset of form indices reading it"""
        u = {k: set() for k in self.ands}
        pm = self.pmask()
        for idx, f in enumerate(self.forms()):
            for b in bits(f & pm): u[b].add(idx)
        return {k: frozenset(v) for k, v in u.items()}


# ---- circuit <-> program -------------------------------------------------------------------------
def extract(c):
    n = c.n; p = Prog(n, c.m)
    form = [1 << (i + 1) for i in range(n)]
    nb = n + 1
    for op, a, b in c.gates:
        if op == XOR: form.append(form[a] ^ form[b])
        elif op == XNOR: form.append(form[a] ^ form[b] ^ 1)
        elif op == NOT: form.append(form[a] ^ 1)
        elif op == AND:
            p.ands[nb] = [form[a], form[b]]; form.append(1 << nb); nb += 1
        else:
            raise ValueError('gate op %d not supported (NIST library only)' % op)
    p.outs = [form[s] for s in c.outputs]
    p.remove_dead()
    return p


def materialise(p, rng=None, share=True):
    """core.Circuit computing the program: Paar pair sharing over all needed forms, then emission in
    dependency order (depth-greedy chains)."""
    rng = rng or random.Random(1)
    n = p.n
    order = p.topo()
    need = []
    for k in order: need += [p.ands[k][0], p.ands[k][1]]
    need += p.outs
    rows = {}
    for f in need:
        f0 = f & ~1
        if f0 not in rows: rows[f0] = set(bits(f0))
    nxt = max(list(p.ands) + [n]) + 1
    merges = {}      # term -> (u, v)
    if share:
        rl = list(rows.values())
        while True:
            cnt = {}
            for r in rl:
                if len(r) < 2: continue
                bs = sorted(r)
                for x in range(len(bs)):
                    bx = bs[x]
                    for y in range(x + 1, len(bs)):
                        key = (bx, bs[y]); cnt[key] = cnt.get(key, 0) + 1
            if not cnt: break
            mx = max(cnt.values())
            if mx < 2: break
            best = [pr for pr, v in cnt.items() if v == mx]
            u, v = rng.choice(best)
            t = nxt; nxt += 1; merges[t] = (u, v)
            for r in rl:
                if u in r and v in r: r.discard(u); r.discard(v); r.add(t)
    gates = []; sig = {}; lvl = {}
    for i in range(n): sig[i + 1] = i; lvl[i + 1] = 0
    fcache = {}

    def emit(op, a, b, la):
        gates.append((op, a, b)); return n + len(gates) - 1

    def term(t):
        if t in sig: return sig[t]
        if t in merges:
            u, v = merges[t]; su = term(u); sv = term(v)
            sig[t] = emit(XOR, su, sv, 0); lvl[t] = 1 + max(lvl[u], lvl[v])
        else:
            L, R = p.ands[t]; sl, ll = form(L); sr, lr = form(R)
            sig[t] = emit(AND, sl, sr, 0); lvl[t] = 1 + max(ll, lr)
        return sig[t]

    def form(f):
        if f in fcache: return fcache[f]
        if (f ^ 1) in fcache:
            s, l = fcache[f ^ 1]
            fcache[f] = (emit(NOT, s, s, 0), l + 1)
            return fcache[f]
        f0 = f & ~1
        ts = sorted(rows[f0]) if f0 in rows else sorted(bits(f0))
        if not ts: raise ValueError('constant form')
        items = []
        for t in ts:
            s = term(t); items.append((lvl[t], s))
        items.sort()
        made = False
        while len(items) > 1:
            (l1, s1), (l2, s2) = items[0], items[1]
            s = emit(XOR, s1, s2, 0); made = True
            items = sorted(items[2:] + [(1 + max(l1, l2), s)])
        l, s = items[0]
        if f & 1:
            if made:
                op, a, b = gates[s - n]; gates[s - n] = (XNOR, a, b)
            else:
                s = emit(NOT, s, s, 0); l += 1
            fcache[f] = (s, l)
        else:
            fcache[f] = (s, l)
            # the plain form may be asked later with the constant: handled by a separate NOT then
        return fcache[f]

    # forms with constant that were built with XNOR must not be reused as the plain form: build plain first
    plain_needed = {f for f in need if not f & 1}
    outs = []
    for k in order: term(k)
    for o in p.outs: outs.append(form(o)[0])
    c = core.Circuit(n, p.m, gates, outs)
    return c.live()


def check(p, target_tables):
    return p.out_tables() == list(target_tables)
