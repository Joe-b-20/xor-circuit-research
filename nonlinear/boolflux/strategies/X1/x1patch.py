"""X1 local patches: remove an AND from a circuit while keeping the rest of its XOR network.

  dep    the truth table of a product is an XOR of other atoms (1, inputs, products that do not depend
         on it): the AND gate is replaced by an XOR tree over existing signals ("AND-free redundancy").
  merge  two ANDs read by exactly the same affine forms (AND operands / outputs) and sharing an operand
         direction a (modulo constants): p_i + p_j = a*(b_i + b_j) + affine; one AND instead of two.
Both are exact identities; every candidate is nevertheless re-checked on all 256 inputs by the caller.
"""
from __future__ import annotations

import heapq
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import x1lib as X          # noqa: E402
from boolflux import core  # noqa: E402

XOR, XNOR, NOT, AND = 6, 9, 3, 8


class Info:
    """circuit + its product program with the signal <-> atom correspondence"""

    def __init__(self, c):
        self.c = c; n = c.n
        self.form = [1 << (i + 1) for i in range(n)]
        self.bit_sig = {}; self.sig_bit = {}
        p = X.Prog(n, c.m); nb = n + 1
        self.glev = [0] * n; self.alev = [0] * n
        for g, (op, a, b) in enumerate(c.gates):
            s = n + g
            self.glev.append(1 + max(self.glev[a], self.glev[b]))
            self.alev.append(max(self.alev[a], self.alev[b]) + (1 if op == AND else 0))
            if op == XOR: self.form.append(self.form[a] ^ self.form[b])
            elif op == XNOR: self.form.append(self.form[a] ^ self.form[b] ^ 1)
            elif op == NOT: self.form.append(self.form[a] ^ 1)
            elif op == AND:
                p.ands[nb] = [self.form[a], self.form[b]]; self.form.append(1 << nb)
                self.bit_sig[nb] = s; self.sig_bit[s] = nb; nb += 1
            else:
                raise ValueError('gate op %d not supported' % op)
        p.outs = [self.form[s] for s in c.outputs]
        self.p = p
        # atoms -> signals (inputs and AND gates)
        self.atom_sig = {i + 1: i for i in range(n)}
        self.atom_sig.update(self.bit_sig)

    def tfo(self, s):
        c = self.c; n = c.n; dep = [False] * (n + len(c.gates)); dep[s] = True
        for g, (op, a, b) in enumerate(c.gates):
            if dep[a] or dep[b]: dep[n + g] = True
        return dep


def rebuild(c, override):
    """New circuit where old signal s (key of override) is computed by override[s] instead.
    Node: int = old signal; ('x', (nodes...), const) = XOR of nodes plus const; ('a', node, node) = AND."""
    n = c.n; gates = []; lev = [0] * n
    memo = {}; gcache = {}; onstack = set()

    def gate(op, a, b):
        if op != NOT and a > b: a, b = b, a
        key = (op, a, b)
        if key in gcache: return gcache[key]
        gates.append(key); lev.append(1 + max(lev[a], lev[b]))
        gcache[key] = n + len(gates) - 1
        return gcache[key]

    def xor_many(items, const):
        """items: list of emitted ('c', v) / ('s', sig)"""
        cnt = {}
        for k, v in items:
            if k == 'c': const ^= v
            else: cnt[v] = cnt.get(v, 0) ^ 1
        sigs = [s for s, v in cnt.items() if v]
        if not sigs: return ('c', const)
        h = [(lev[s], s) for s in sigs]; heapq.heapify(h)
        while len(h) > 1:
            l1, s1 = heapq.heappop(h); l2, s2 = heapq.heappop(h)
            if len(h) == 0 and const:
                s = gate(XNOR, s1, s2); const = 0
            else:
                s = gate(XOR, s1, s2)
            heapq.heappush(h, (lev[s], s))
        s = h[0][1]
        if const: s = gate(NOT, s, s)
        return ('s', s)

    def emit(node):
        if node in memo: return memo[node]
        if node in onstack: raise ValueError('cycle')
        onstack.add(node)
        if isinstance(node, int):
            if node in override: r = emit(override[node])
            elif node < n: r = ('s', node)
            else:
                op, a, b = c.gates[node - n]
                if op == NOT:
                    r = xor_many([emit(a)], 1)
                elif op in (XOR, XNOR):
                    r = xor_many([emit(a), emit(b)], 1 if op == XNOR else 0)
                else:
                    r = and2(emit(a), emit(b))
        elif node[0] == 'x':
            r = xor_many([emit(x) for x in node[1]], node[2])
        else:
            r = and2(emit(node[1]), emit(node[2]))
        onstack.discard(node)
        memo[node] = r
        return r

    def and2(ea, eb):
        if ea[0] == 'c': return eb if ea[1] else ('c', 0)
        if eb[0] == 'c': return ea if eb[1] else ('c', 0)
        if ea[1] == eb[1]: return ea
        return ('s', gate(AND, ea[1], eb[1]))

    import sys as _s
    _s.setrecursionlimit(max(10000, _s.getrecursionlimit()))
    outs = []
    for o in c.outputs:
        k, v = emit(o)
        if k == 'c': raise ValueError('constant output')
        outs.append(v)
    return core.Circuit(n, c.m, gates, outs, c.name, list(c.in_names), list(c.out_names)).live()


# ---- dependencies ---------------------------------------------------------------------------------
def null_space(I):
    """basis of the linear dependencies between the tables of 1, inputs and products (masks over atoms)"""
    p = I.p; T, ft = p.tables()
    piv = []; null = []
    for b in list(range(p.n + 1)) + p.topo():
        t = T[b]; f = 1 << b
        for pp, rt, rf in piv:
            if (t >> pp) & 1: t ^= rt; f ^= rf
        if t: piv.append((t.bit_length() - 1, t, f))
        else: null.append(f)
    return null


def cover(I, delta, banned):
    """signals whose XOR (plus const) has atom form delta: greedy, largest weight reduction first, then
    shallowest.  banned[s] = True for signals that may not be used."""
    rem = delta & ~1; const = delta & 1; chosen = []
    cands = [(s, I.form[s] & ~1, I.form[s] & 1) for s in range(len(I.form)) if not banned[s] and I.form[s] & ~1]
    while rem:
        w = bin(rem).count('1'); best = None
        for s, f0, fc in cands:
            g = w - bin(rem ^ f0).count('1')
            if g <= 0: continue
            key = (-g, I.glev[s])
            if best is None or key < best[0]: best = (key, s, f0, fc)
        if best is None: return None
        _, s, f0, fc = best
        rem ^= f0; const ^= fc; chosen.append(s)
    return chosen, const


def dep_candidates(I, max_combo_dim=5):
    """circuits with one AND fewer from table dependencies; list of (circuit, description)"""
    p = I.p; null = null_space(I)
    if not null: return []
    vecs = []
    if len(null) <= max_combo_dim:
        for m in range(1, 1 << len(null)):
            v = 0
            for k in range(len(null)):
                if (m >> k) & 1: v ^= null[k]
            vecs.append(v)
    else:
        vecs = list(null)
    pm = p.pmask(); out = []; seen = set()
    lv = p.and_levels()
    for v in vecs:
        prods = list(X.bits(v & pm))
        for b in prods:
            if any(o != b and p.depends(o, b) for o in prods): continue
            delta = v ^ (1 << b)
            if (b, delta) in seen: continue
            seen.add((b, delta))
            sb = I.bit_sig[b]
            banned = I.tfo(sb)
            cv = cover(I, delta, banned)
            if cv is None: continue
            sigs, const = cv
            try:
                nc = rebuild(I.c, {sb: ('x', tuple(sigs), const)})
            except ValueError:
                continue
            out.append((nc, {'kind': 'dep', 'removed_and_level': lv[b], 'terms': len(sigs),
                             'max_term_and_level': max([lv.get(a, 0) for a in X.bits(delta & pm)] + [0])}))
    return out


# ---- merges ---------------------------------------------------------------------------------------
def express(target, basis):
    """target form as XOR of a subset of basis [(node, form)] plus a constant -> ('x', nodes, const) or None"""
    k = len(basis)
    best = None
    for m in range(1 << k):
        f = 0
        for x in range(k):
            if (m >> x) & 1: f ^= basis[x][1]
        if (f ^ target) & ~1 == 0:
            nodes = tuple(basis[x][0] for x in range(k) if (m >> x) & 1)
            if best is None or len(nodes) < len(best[1]): best = ('x', nodes, (f ^ target) & 1)
    return best


def merge_candidates(I):
    p = I.p; c = I.c; n = c.n
    u = p.usage(); groups = {}
    for k, s in u.items(): groups.setdefault(s, []).append(k)
    out = []
    for g in groups.values():
        if len(g) < 2: continue
        for x in range(len(g)):
            for y in range(x + 1, len(g)):
                i, j = g[x], g[y]
                Li, Ri = p.ands[i]; Lj, Rj = p.ands[j]
                common = set(X.Prog.span3(Li, Ri)) & set(X.Prog.span3(Lj, Rj))
                si, sj = I.bit_sig[i], I.bit_sig[j]
                basis = [(c.gates[si - n][1], Li), (c.gates[si - n][2], Ri), (c.gates[sj - n][1], Lj), (c.gates[sj - n][2], Rj)]
                for a in common:
                    bi, li = X.Prog.factor(Li, Ri, a); bj, lj = X.Prog.factor(Lj, Rj, a)
                    b = bi ^ bj
                    if (b & ~1) in (0, a): continue
                    na = express(a, basis); nb = express(b, basis); nl = express(li ^ lj, basis)
                    if na is None or nb is None or nl is None: continue
                    q = ('a', na, nb)
                    try:
                        nc = rebuild(c, {si: ('x', (q,) + nl[1], nl[2]), sj: ('x', (), 0)})
                    except ValueError:
                        continue
                    out.append((nc, {'kind': 'merge'}))
    return out


def static_candidates(c):
    I = Info(c)
    return dep_candidates(I) + merge_candidates(I)
