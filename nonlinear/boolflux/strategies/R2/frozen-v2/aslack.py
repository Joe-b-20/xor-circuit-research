"""Affine-slack window redesign (agent R2, 2026-11-15).

A window = a set S of k ANDs at one AND level L (an antichain) together with D, the linear gates
reachable from S through linear gates only.  Targets T = signals of S u D read outside S u D (or
outputs).  The window does NOT have to reproduce its old outputs: every target t only has to stay
computable as

    f_t = fixed_t + g_t,   g_t in span(1, C, q_1..q_m)

where fixed_t = the part of t's original affine form (over D's leaves) on leaves that depend on S or
sit above level L (kept as is), C = "slack" signals (independent of S, AND level <= L), and the new
ANDs q_j = a_j * b_j have affine operands over O = signals independent of S with AND level <= L-1.
Over GF(2)^256 (truth tables as Python ints): with V = span(1, C) and R = span{g_t mod V} (dim r),
the requirement is span{q_j mod V} contains R, so m >= r new ANDs.  m < k lowers A by k - m.

Search: for a fixed operand a, b -> a*b mod V is linear in b, so the operands b in O whose product
lands in V + R form a subspace, found by one Gaussian elimination (W = V + R pivots tagged with R
coordinates).  Products are picked greedily (cheapest first, randomised) until their R-tags span
GF(2)^r.  Then every target's new form is solved, its V-part decoded sparsely over C (random-order
elimination, several tries; also as "old V-part + correction"), and only the window's linear logic is
re-synthesised (shared-pair merging + level-ordered combination), the rest of the circuit untouched.
"""
from __future__ import annotations

import random
from boolflux import core

ONES = (1 << 256) - 1
AND, XOR, XNOR, NOT = 8, 6, 9, 3
NL = core.NONLINEAR_OPS


# ---------------------------------------------------------------------------------------------
class Info:
    """static analysis of a circuit"""

    def __init__(self, c):
        self.c = c; n = c.n; self.n = n; self.NS = n + len(c.gates)
        self.tabs = c.tables()
        self.al = [0] * n; self.lg = [0] * n
        self.readers = [[] for _ in range(self.NS)]
        for j, (op, a, b) in enumerate(c.gates):
            s = n + j
            self.al.append((1 if op in NL else 0) + max(self.al[a], self.al[b]))
            self.lg.append(1 + max(self.lg[a], self.lg[b]))
            self.readers[a].append(s)
            if b != a: self.readers[b].append(s)
        self.isout = set(c.outputs)
        self.ands = [n + j for j, g in enumerate(c.gates) if g[0] in NL]
        self.bylevel = {}
        for s in self.ands: self.bylevel.setdefault(self.al[s], []).append(s)

    def op(self, s):
        return self.c.gates[s - self.n][0] if s >= self.n else None

    def ins(self, s):
        op, a, b = self.c.gates[s - self.n]
        return (a,) if (op == NOT or a == b) else (a, b)

    def tfo(self, S):
        seen = set(S); st = list(S)
        while st:
            s = st.pop()
            for r in self.readers[s]:
                if r not in seen: seen.add(r); st.append(r)
        return seen

    def lin_cone(self, s):
        """s and every linear gate feeding s through linear gates; leaves (ANDs/inputs) included"""
        out = set(); st = [s]
        while st:
            x = st.pop()
            if x in out: continue
            out.add(x)
            if x >= self.n and self.op(x) not in NL: st.extend(self.ins(x))
        return out


# ---- GF(2) elimination helpers ---------------------------------------------------------------
def insert(piv, x, tag=0, mask=0):
    """leading-bit echelon dict pivot -> (row, tag, mask).  Returns (rem, tag, mask) after reduction;
    inserts if rem != 0."""
    while x:
        p = x.bit_length() - 1
        e = piv.get(p)
        if e is None:
            piv[p] = (x, tag, mask); return x, tag, mask
        x ^= e[0]; tag ^= e[1]; mask ^= e[2]
    return 0, tag, mask


def reduce(piv, x, tag=0, mask=0):
    while x:
        p = x.bit_length() - 1
        e = piv.get(p)
        if e is None: return x, tag, mask
        x ^= e[0]; tag ^= e[1]; mask ^= e[2]
    return 0, tag, mask


def popc(x):
    return bin(x).count('1')


def sparse_decode(gens, x, rng, tries=6, prefer=None, lv=None):
    """x in span(gens) (gens[0] = ONES).  Returns the best mask found over elimination orders (bit i =
    gens[i]): fewest generators, then lowest max gate level (lv[i]); None if not in span.  With lv, half
    of the orders insert shallow generators first (noisy), so the solution uses shallow signals."""
    best = None; bk = None
    for t in range(tries):
        idx = list(range(len(gens)))
        rng.shuffle(idx)
        if lv is not None and t % 2 == 0:
            idx.sort(key=lambda i: lv[i] + rng.random() * 3)
        if t == 1 and prefer:
            pf = [i for i in idx if i in prefer]; idx = pf + [i for i in idx if i not in prefer]
        piv = {}
        for i in idx: insert(piv, gens[i], 0, 1 << i)
        rem, _, m = reduce(piv, x)
        if rem: return None
        k = (popc(m & ~1), max([lv[i] for i in range(1, len(gens)) if (m >> i) & 1] or [0]) if lv else 0)
        if best is None or k < bk: best = m; bk = k
    return best


# ---------------------------------------------------------------------------------------------
class Window:
    def __init__(self, I: Info, S, mode='wide', rng=None, ddepth=None, lower=0):
        self.I = I; self.S = list(S); self.L = I.al[S[0]]; self.mode = mode; self.ddepth = ddepth; self.lower = lower
        n = I.n; L = self.L
        T = I.tfo(S); self.T = T
        D = set(); st = [(s, 0) for s in S]      # linear closure downstream of S, optionally depth-limited
        while st:
            s, d = st.pop(0)
            if ddepth is not None and d >= ddepth: continue
            for r in I.readers[s]:
                if r not in D and I.op(r) not in NL: D.add(r); st.append((r, d + 1))
        self.D = D; Rg = set(S) | D; self.Rg = Rg
        self.targets = sorted(s for s in Rg if s in I.isout or any(r not in Rg for r in I.readers[s]))
        # symbolic forms over terms: term ids = signal ids (const = -1 -> bit 0 handled separately)
        leaves = sorted({x for s in D for x in I.ins(s) if x not in Rg})
        self.leaves = leaves
        forms = {s: (0, frozenset([s])) for s in S}         # (const, set of term signals)
        for s in sorted(D):
            op = I.op(s); cst = 1 if op in (XNOR, NOT) else 0; terms = set()
            for x in I.ins(s):
                if x in forms:
                    c2, t2 = forms[x]; cst ^= c2; terms ^= set(t2)
                else:
                    terms ^= {x}
            if op == NOT: pass
            forms[s] = (cst, frozenset(terms))
        self.forms = forms
        indep = lambda x: x not in T
        # slack signals C (level <= L, independent of S) and operand signals O (level <= L-1)
        if mode == 'wide':
            cand = [x for x in range(I.NS) if indep(x) and I.al[x] <= L - lower]
        else:   # local: D leaves + operand cones
            loc = set(x for x in leaves if indep(x) and I.al[x] <= L - lower)
            for s in S:
                for x in I.ins(s): loc |= I.lin_cone(x)
            cand = sorted(x for x in loc if indep(x) and I.al[x] <= L - lower)
        # drop duplicate / constant tables, keep the shallowest signal per table
        bytab = {}
        for x in sorted(cand, key=lambda x: (I.lg[x], x)):
            t = I.tabs[x]
            if t in (0, ONES) or t in bytab or (t ^ ONES) in bytab: continue
            bytab[t] = x
        self.C = sorted(bytab.values())
        self.O = [x for x in self.C if I.al[x] <= L - 1 - lower]
        self.cset = set(self.C)
        # split each target's form: fixed part (dependent or high leaves) + g part (const, C leaves, S)
        self.fixed = {}; self.gtab = {}; self.wform = {}; self.eS = {}
        for t in self.targets:
            cst, terms = forms[t]
            fx = frozenset(x for x in terms if x not in S and x not in self.cset)
            self.fixed[t] = fx
            g = ONES if cst else 0
            w = set()
            for x in terms:
                if x in fx: continue
                g ^= I.tabs[x]
                if x not in S: w.add(x)
            self.gtab[t] = g; self.wform[t] = (cst, frozenset(w)); self.eS[t] = frozenset(x for x in terms if x in S)
        # W = V + R with R tags
        self.Vg = [ONES] + [I.tabs[x] for x in self.C]
        self.Vlv = [0] + [I.lg[x] for x in self.C]
        self.Og = [ONES] + [I.tabs[x] for x in self.O]
        self.Olv = [0] + [I.lg[x] for x in self.O]
        piv = {}
        for v in self.Vg: insert(piv, v)
        self.dimV = len(piv)
        r = 0; self.etag = {}
        for t in self.targets:
            rem, tag, _ = reduce(piv, self.gtab[t])
            if rem:
                piv[rem.bit_length() - 1] = (rem, 1 << r, 0); tag ^= 1 << r; r += 1
            self.etag[t] = tag
        self.W = piv; self.r = r
        # original products' tags (diagnostic) and rank of products mod V
        pv = {}
        for v in self.Vg: insert(pv, v)
        self.dimP = sum(1 for s in S if insert(pv, I.tabs[s])[0])

    # ---- product search ----------------------------------------------------------------------
    def products(self, rng, n_a=200, tries=3, exhaustive_dim=0):
        """candidate products (cost, a_form, b_form, tag, table) with nonzero R-tag; forms = (const, frozenset)"""
        I = self.I; O = self.O
        if not O or self.r == 0: return []
        otabs = [I.tabs[x] for x in O]
        # operand candidates a: single signals (both polarities), some pairs
        acands = [(0, frozenset([x])) for x in O] + [(1, frozenset([x])) for x in O]
        orig_ops = set()
        for s in self.S:
            for x in I.ins(s): orig_ops.add(x)
        # basis of span(O), shallow signals first
        bp = {}; basis = []
        for x in sorted(O, key=lambda x: (I.lg[x], x)):
            if insert(bp, I.tabs[x])[0]: basis.append(x)
        self.dimO = len(basis)
        if len(basis) <= exhaustive_dim:      # every non-constant affine operand (exact within this window)
            acands = []
            for msk in range(1, 1 << len(basis)):
                f = frozenset(basis[i] for i in range(len(basis)) if (msk >> i) & 1)
                acands.append((0, f)); acands.append((1, f))
            self.exhaustive = True
        else:
            self.exhaustive = False
            npair = max(0, n_a - len(acands))
            for _ in range(npair):
                x, y = rng.sample(O, 2); acands.append((rng.randrange(2), frozenset([x, y])))
            rng.shuffle(acands)
            acands.sort(key=lambda f: (0 if any(x in orig_ops for x in f[1]) else 1, len(f[1])))
            acands = acands[:n_a]
        out = {}
        for af in acands:
            at = ONES if af[0] else 0
            for x in af[1]: at ^= I.tabs[x]
            if at in (0, ONES): continue
            items = [at] + [at & t for t in otabs]          # b = 1 (const) and b = O_i
            for _ in range(1 if self.exhaustive else tries):
                order = list(range(len(items))); rng.shuffle(order)
                piv = dict(self.W)
                for i in order:
                    rem, tag, mask = insert(piv, items[i], 0, 1 << i)
                    if rem == 0 and tag:
                        cst = mask & 1
                        bf = frozenset(O[j - 1] for j in range(1, len(items)) if (mask >> j) & 1)
                        if not bf: continue        # b constant: product = a (linear)
                        bt = ONES if cst else 0
                        for x in bf: bt ^= I.tabs[x]
                        if bt in (0, ONES): continue
                        cost = (len(af[1]) - 1 + (1 if af[0] else 0)) + (len(bf) - 1 + cst)
                        key = (tag, min(at, bt), max(at, bt))
                        if key not in out or out[key][0] > cost:
                            out[key] = (cost, af, (cst, bf), tag, at & bt)
        return list(out.values())

    def extended(self, ztabs):
        """copy whose required space is R + span(z mod V) (free products z): solutions then have
        m = r + e products with e = number of independent z"""
        import copy
        w2 = copy.copy(self); piv = dict(self.W); rr = self.r
        for z in ztabs:
            rem, tag, _ = reduce(piv, z)
            if rem: piv[rem.bit_length() - 1] = (rem, 1 << rr, 0); rr += 1
        w2.W = piv; w2.r = rr
        return w2

    def random_product(self, rng):
        I = self.I
        def rnd():
            f = frozenset(rng.sample(self.O, min(len(self.O), rng.choice([1, 1, 2, 2, 3]))))
            t = 0
            for x in f: t ^= I.tabs[x]
            return t
        return rnd() & rnd()

    def pick(self, prods, rng, m=None, noise=1.0):
        """greedy spanning set of tags: cheapest (noisy) first"""
        r = self.r
        ps = sorted(prods, key=lambda p: p[0] + noise * rng.random() * 2)
        piv = {}; chosen = []
        for p in ps:
            rem, _, _ = insert(piv, p[3], 0, 0)
            if rem: chosen.append(p)
            if len(chosen) == r: break
        if len(chosen) < r: return None
        return [self.refine(p, rng) for p in chosen]

    def refine(self, p, rng):
        I = self.I; out = []
        for f in (p[1], p[2]):
            t = ONES if f[0] else 0
            for x in f[1]: t ^= I.tabs[x]
            m = sparse_decode(self.Og, t, rng, tries=4, lv=self.Olv)
            if m is None: out.append(f); continue
            g = (m & 1, frozenset(self.O[i - 1] for i in range(1, len(self.Og)) if (m >> i) & 1))
            out.append(g if len(g[1]) <= len(f[1]) else f)
        return (p[0], out[0], out[1], p[3], p[4])

    # ---- target forms ------------------------------------------------------------------------
    def target_rows(self, chosen, rng):
        """per target: (const, C-terms, q indices, fixed terms) or None"""
        I = self.I
        qp = {}
        for j, p in enumerate(chosen): insert(qp, p[3], 0, 1 << j)
        gidx = {x: i + 1 for i, x in enumerate(self.C)}
        rows = {}
        for t in self.targets:
            rem, _, qm = reduce(qp, self.etag[t])
            if rem: return None
            v = self.gtab[t]
            for j in range(len(chosen)):
                if (qm >> j) & 1: v ^= chosen[j][4]
            # option 1: direct decode of v; option 2: old V-part + decoded correction
            best = None
            m1 = sparse_decode(self.Vg, v, rng, lv=self.Vlv)
            if m1 is not None:
                best = (m1 & 1, frozenset(self.C[i - 1] for i in range(1, len(self.Vg)) if (m1 >> i) & 1))
            cst, w = self.wform[t]
            wt = ONES if cst else 0
            for x in w: wt ^= I.tabs[x]
            d = v ^ wt
            m2 = sparse_decode(self.Vg, d, rng, tries=4, lv=self.Vlv)
            if m2 is not None:
                f2 = frozenset(self.C[i - 1] for i in range(1, len(self.Vg)) if (m2 >> i) & 1)
                cand = ((m2 & 1) ^ cst, frozenset(set(w) ^ set(f2)))
                if best is None or len(cand[1]) < len(best[1]): best = cand
            if best is None: return None
            rows[t] = (best[0], best[1], frozenset(j for j in range(len(chosen)) if (qm >> j) & 1), self.fixed[t])
        return rows


# ---------------------------------------------------------------------------------------------
def rebuild(W: Window, chosen, rows, rng):
    """new circuit: kept gates = all outside S u D, in order; window logic re-synthesised lazily."""
    I = W.I; c = I.c; n = c.n
    gates = []; lvl = list(I.lg[:n])
    remap = {i: i for i in range(n)}          # old signal -> new signal (kept gates and inputs)
    # term keys: ('s', old) for existing signals, ('q', j) for new ANDs, ('m', k) merged pairs
    sig = {}

    def avail(k):
        if k in sig: return True
        if k[0] == 's' and k[1] in remap: sig[k] = remap[k[1]]; return True
        return False

    def emit(op, a, b):
        gates.append((op, a, b)); s = n + len(gates) - 1
        lvl.append(1 + max(lvl[a], lvl[b])); return s

    # rows: operands of q_j and targets
    R = []          # [kind, id, const, set of term keys]
    for j, p in enumerate(chosen):
        for side, f in (('a', p[1]), ('b', p[2])):
            R.append(['op', (j, side), f[0], {('s', x) for x in f[1]}])
    for t, (cst, cterms, qs, fx) in rows.items():
        R.append(['t', t, cst, {('s', x) for x in cterms} | {('q', j) for j in qs} | {('s', x) for x in fx}])
    # shared pair merging (Paar-like, count >= 2, ties random)
    merges = []; mk = 0
    while True:
        cnt = {}
        for row in R:
            ts = sorted(row[3], key=str)
            for i in range(len(ts)):
                for k in range(i + 1, len(ts)): cnt[(ts[i], ts[k])] = cnt.get((ts[i], ts[k]), 0) + 1
        if not cnt: break
        mx = max(cnt.values())
        if mx < 2: break
        best = [p for p, v in cnt.items() if v == mx]
        pr = rng.choice(best); key = ('m', mk); mk += 1; merges.append((key, pr[0], pr[1]))
        for row in R:
            if pr[0] in row[3] and pr[1] in row[3]: row[3] -= {pr[0], pr[1]}; row[3].add(key)
    done_rows = set(); qsig = {}

    def build_row(row):
        ts = list(row[3])
        if not ts: return None
        ts.sort(key=lambda k: lvl[sig[k]])
        while len(ts) > 1:
            a, b = ts[0], ts[1]
            s = emit(XOR, sig[a], sig[b]); k = ('x', s); sig[k] = s
            ts = sorted(ts[2:] + [k], key=lambda k: lvl[sig[k]])
        s = sig[ts[0]]
        if row[2]:
            if s >= n and gates[s - n][0] == XOR and ts[0][0] == 'x':
                op, a, b = gates[s - n]; gates[s - n] = (XNOR, a, b)
            else:
                s = emit(NOT, s, s)
        return s

    def progress():
        moved = True
        while moved:
            moved = False
            for key, a, b in merges:
                if key not in sig and avail(a) and avail(b):
                    sig[key] = emit(XOR, sig[a], sig[b]); moved = True
            for idx, row in enumerate(R):
                if idx in done_rows: continue
                if all(avail(k) for k in row[3]):
                    s = build_row(row)
                    if s is None: raise ValueError('empty row')
                    done_rows.add(idx); moved = True
                    if row[0] == 'op':
                        j, side = row[1]; qsig.setdefault(j, {})[side] = s
                        if len(qsig[j]) == 2:
                            sig[('q', j)] = emit(AND, qsig[j]['a'], qsig[j]['b'])
                    else:
                        remap[row[1]] = s
    progress()
    pending = [n + j for j in range(len(c.gates)) if n + j not in W.Rg]
    while pending:
        moved = False; rest = []
        for s in pending:
            op, a, b = c.gates[s - n]
            if a in remap and b in remap:
                remap[s] = emit(op, remap[a], remap[b]); moved = True
                progress()
            else:
                rest.append(s)
        pending = rest
        if not moved: return None
    if any(o not in remap for o in c.outputs): return None
    nc = core.Circuit(n, c.m, gates, [remap[o] for o in c.outputs]).live()
    return nc


# ---------------------------------------------------------------------------------------------
def choose_S(I: Info, rng, kmin=2, kmax=5):
    levels = [L for L, v in I.bylevel.items() if len(v) >= kmin]
    if not levels: return None
    L = rng.choice(levels); ands = I.bylevel[L]
    k = rng.randint(kmin, min(kmax, len(ands)))
    seed = rng.choice(ands)
    # affinity: shared operand-cone leaves + shared downstream readers (2 linear steps)
    def up(s):
        u = set()
        for x in I.ins(s): u |= I.lin_cone(x)
        return u
    def down(s):
        d = set(I.readers[s])
        for r in list(d):
            if I.op(r) not in NL: d |= set(I.readers[r])
        return d
    us, ds = up(seed), down(seed)
    others = [a for a in ands if a != seed]
    mode = rng.random()
    if mode < 0.25:
        rng.shuffle(others); pick = others[:k - 1]
    else:
        sc = [(len(up(a) & us) + 2 * len(down(a) & ds) + rng.random() * 2, a) for a in others]
        sc.sort(reverse=True); pick = [a for _, a in sc[:k - 1]]
    return [seed] + pick
