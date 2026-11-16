#!/usr/bin/env python3
"""Exact operand-pair re-choice for AND gates (same product, both operands may change).

For an AND gate g = AND(a, b) at AND level L of circuit C, let S = span{1, signals of AND level < L}
(all affine functions the operands could be without changing the AND structure). The pairs (a', b')
in S x S with a' b' = a b are:
    a' in A' = {v in S : v = 1 on supp(P)}                (affine subspace, P = ab)
    b' in B'(a') = {v in S : v = P on supp(a')}           (affine subspace, for each a')
This is exact (all pairs, for the fixed product P and fixed span S).
Costs: an operand that is an existing signal (or its complement) costs 0 new gates, XOR of two existing
signals 1, of three 2 (meet in the middle). Candidates are materialised as circuits (new XOR/XNOR
gates, AND rewired, dead gates removed, topological order) and reported with their G/GD.

    python3 pairs.py CIRCUIT [--levels 3] [--maxdim 14] [--emit DIR]
"""
import argparse
import itertools
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
from boolflux import core                                   # noqa: E402
from boolflux.hub.common import load, metrics, verify, cid  # noqa: E402

ONES = (1 << 256) - 1
MODEL = core.Model.load('nist')


def and_levels(c):
    n = c.n; al = [0] * n
    for op, a, b in c.gates:
        al.append((1 if op == 8 else 0) + max(al[a], al[b]))
    return al


class Basis:
    """GF(2) span of 256-bit ints with coordinates w.r.t. the given generators"""
    def __init__(self, gens):
        self.gens = []; self.piv = []    # rows: (pivot, vec, coordmask)
        for v in gens: self.add(v)

    def add(self, v):
        m = 1 << len(self.gens); w = v
        for p, r, rm in self.piv:
            if (w >> p) & 1: w ^= r; m ^= rm
        if w == 0: return False
        self.gens.append(v)
        # store with the new generator's index bit
        self.piv.append((w.bit_length() - 1, w, m)); self.piv.sort(key=lambda t: -t[0])
        return True

    def reduce(self, v):
        for p, r, rm in self.piv:
            if (v >> p) & 1: v ^= r
        return v


def solve_affine(gens, pts, rhs_fn):
    """coefficient vectors c (over gens) with sum c_i gens_i (x) = rhs(x) for x in pts.
    returns (particular, nullspace basis) as lists of int masks over gens, or None."""
    k = len(gens)
    rows = []
    for x in pts:
        r = 0
        for i, g in enumerate(gens):
            if (g >> x) & 1: r |= 1 << i
        rows.append((r, rhs_fn(x)))
    # elimination
    piv = {}
    for r, y in rows:
        for p in sorted(piv, reverse=True):
            if (r >> p) & 1: r ^= piv[p][0]; y ^= piv[p][1]
        if r == 0:
            if y: return None
            continue
        p = r.bit_length() - 1
        for q in list(piv):
            if (piv[q][0] >> p) & 1: piv[q] = (piv[q][0] ^ r, piv[q][1] ^ y)
        piv[p] = (r, y)
    part = 0
    for p, (r, y) in piv.items():
        if y: part |= 1 << p
    free = [i for i in range(k) if i not in piv]
    null = []
    for f in free:
        v = 1 << f
        for p, (r, y) in piv.items():
            if (r >> f) & 1: v |= 1 << p
        null.append(v)
    return part, null


def combine(gens, mask):
    v = 0; i = 0
    while mask:
        if mask & 1: v ^= gens[i]
        mask >>= 1; i += 1
    return v


def support(t):
    return [x for x in range(256) if (t >> x) & 1]


class Cost:
    """cheapest XOR expression of a function over existing signals (up to complement)"""
    def __init__(self, sigs):
        self.sig = {}
        for s, t in sigs:
            for u in (t, t ^ ONES):
                if u not in self.sig: self.sig[u] = (s,)
        items = list({t: s for s, t in sigs}.items())
        self.pair = {}
        for (t1, s1), (t2, s2) in itertools.combinations(items, 2):
            u = t1 ^ t2
            for w in (u, u ^ ONES):
                if w not in self.pair and w not in self.sig: self.pair[w] = (s1, s2)
        self.items = items

    def best(self, t, maxc=2):
        if t in self.sig: return 0, self.sig[t]
        if t in self.pair: return 1, self.pair[t]
        if maxc >= 2:
            for t1, s1 in self.items:
                w = t ^ t1
                if w in self.pair: return 2, self.pair[w] + (s1,)
        return None

    def best_in(self, part, lin_basis, maxc=1):
        """cheapest member of the affine subspace part + span(lin_basis) (lin_basis: Basis)"""
        best = None
        pr = lin_basis.reduce(part)
        for t, ex in self.sig.items():
            if lin_basis.reduce(t) == pr: return 0, ex, t
        if maxc >= 1:
            for t, ex in self.pair.items():
                if lin_basis.reduce(t) == pr:
                    return 1, ex, t
        return best


def materialise(c, g, ops_new):
    """rewire AND gate index g (signal number) to operands given as (table, expr) where expr is a tuple of
    existing signals whose XOR (maybe complemented) equals table; returns a new live, topologically
    ordered circuit"""
    t = c.tables(); n = c.n
    gates = [list(x) for x in c.gates]
    newg = []    # (op, a, b) appended at the end, referencing old signals or new ones
    nid = n + len(gates)
    opsig = []
    for tab, ex in ops_new:
        if len(ex) == 1:
            s = ex[0]
            if t[s] == tab: opsig.append(s); continue
            newg.append((3, s, s)); opsig.append(nid); nid += 1; continue
        cur = ex[0]; acc = t[cur]
        for k, s in enumerate(ex[1:]):
            last = (k == len(ex) - 2)
            val = acc ^ t[s]
            if last and val != tab:
                newg.append((9, cur, s)); val ^= ONES
            else:
                newg.append((6, cur, s))
            cur = nid; nid += 1; acc = val
        assert acc == tab
        opsig.append(cur)
    gi = g - n
    gates[gi] = [8, opsig[0], opsig[1]]
    allg = [tuple(x) for x in gates] + newg
    # topological re-order
    N = n + len(allg)
    order = []; state = [0] * N
    sys.setrecursionlimit(10000)
    def visit(s):
        if s < n or state[s] == 2: return
        assert state[s] != 1, 'cycle'
        state[s] = 1
        op, a, b = allg[s - n]
        visit(a); visit(b)
        state[s] = 2; order.append(s)
    for s in c.outputs: visit(s)
    new = {i: i for i in range(n)}
    gl = []
    for s in order:
        op, a, b = allg[s - n]
        new[s] = n + len(gl); gl.append((op, new[a], new[b]))
    return core.Circuit(n, c.m, gl, [new[s] for s in c.outputs], c.name)


def analyse(c, levels=(3,), maxdim=14, maxc=2, verbose=True):
    t = c.tables(); n = c.n; al = and_levels(c)
    out = []
    G0 = metrics(c)
    for g in range(n, n + len(c.gates)):
        op, a, b = c.gates[g - n]
        if op != 8 or al[g] not in levels: continue
        L = al[g]
        lower = [s for s in range(n + len(c.gates)) if al[s] < L]
        gens_raw = [ONES] + [t[s] for s in lower]
        B = Basis(gens_raw); gens = B.gens
        cost = Cost([(s, t[s]) for s in lower])
        P = t[g]; sP = support(P)
        stats = []
        for role in (0, 1):
            r = solve_affine(gens, sP, lambda x: 1)
            if r is None: stats.append(None); continue
            part, null = r
            stats.append(len(null))
            if role == 1: break
        dimA = stats[0]
        res = {'g': g, 'L': L, 'dimS': len(gens), 'dimA': dimA, 'cands': []}
        if dimA is not None and dimA <= maxdim:
            part, null = solve_affine(gens, sP, lambda x: 1)
            seen = set()
            for k in range(1 << len(null)):
                m = part
                for i, v in enumerate(null):
                    if (k >> i) & 1: m ^= v
                av = combine(gens, m)
                ca = cost.best(av, maxc)
                if ca is None: continue
                # B'(a') = {v in S: v = P on supp(a')}
                pts = support(av)
                rb = solve_affine(gens, pts, lambda x: (P >> x) & 1)
                if rb is None: continue
                bpart, bnull = rb
                bp = combine(gens, bpart)
                lb = Basis([combine(gens, v) for v in bnull])
                cb = cost.best_in(bp, lb, maxc=1)
                if cb is None: continue
                key = frozenset([av, cb[2]])
                if key in seen: continue
                seen.add(key)
                if {av, cb[2]} == {t[a], t[b]}: continue
                res['cands'].append((ca[0] + cb[0], (av, ca[1]), (cb[2], cb[1])))
        res['cands'].sort(key=lambda x: x[0])
        out.append(res)
        if verbose:
            print('AND s%d level %d: dim S %d, dim A\' %s, cheap alternative pairs %d (costs %s)' % (
                g, L, len(gens), dimA, len(res['cands']), sorted(x[0] for x in res['cands'])[:12]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circuit')
    ap.add_argument('--levels', default='3')
    ap.add_argument('--maxdim', type=int, default=14)
    ap.add_argument('--maxc', type=int, default=2)
    ap.add_argument('--emit')
    args = ap.parse_args()
    c = load(args.circuit)
    m0 = metrics(c)
    print('start', m0)
    res = analyse(c, tuple(int(x) for x in args.levels.split(',')), args.maxdim, args.maxc)
    em = Path(args.emit) if args.emit else None
    if em: em.mkdir(parents=True, exist_ok=True)
    hist = {}
    for r in res:
        for cst, A_, B_ in r['cands']:
            nc = materialise(c, r['g'], [A_, B_])
            m = metrics(nc)
            assert nc.value_table() == c.value_table()
            hist[(m[2] - m0[2], m[3] - m0[3])] = hist.get((m[2] - m0[2], m[3] - m0[3]), 0) + 1
            if em and m[2] <= m0[2] + 1 and m[1] <= m0[1]:
                (em / ('s%d-%s-g%d-gd%d.bfx' % (r['g'], cid(nc), m[2], m[3]))).write_text(core.to_kernel(nc))
    print('dG,dGD histogram:', sorted(hist.items()))


if __name__ == '__main__':
    main()
