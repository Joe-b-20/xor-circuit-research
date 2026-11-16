#!/usr/bin/env python3
"""T3: product exchange at the last AND level with output-layer compensation.

For a level-L AND P_i = AND(a, b) whose output feeds only XOR logic (the last AND level), let
S = span{1, signals of AND level < L} and W_i = S + span{P_j : j != i, same level}.  The outputs stay
in span{new products} + S iff the replacement P' = a' b' (a', b' in S) satisfies P' = P_i (mod W_i).
For fixed a' this is linear in b'.  We enumerate cheap a' (existing signal, XOR of 2 or 3 existing
signals), solve for b', keep cheap b', materialise:
    P_i is replaced in the old output logic by  P' + sum_{j in J} P_j + s   (s in S, cheapest expr),
then dead gates are removed.  The kernel polish afterwards reshapes the output layer.

    python3 prodswap.py CIRCUIT --emit DIR [--amax 1] [--bmax 1] [--dmax 12]
"""
import argparse
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[4]))
from boolflux import core                                    # noqa: E402
from boolflux.hub.common import load, metrics, cid           # noqa: E402
from pairs import Basis, Cost, and_levels, ONES              # noqa: E402


class RBasis:
    """reduction basis with tracking of which generators were used (coordinate masks)"""
    def __init__(self, gens):
        self.piv = []; self.gens = []
        for v in gens: self.add(v)

    def add(self, v):
        m = 1 << len(self.gens); w = v
        for p, r, rm in self.piv:
            if (w >> p) & 1: w ^= r; m ^= rm
        self.gens.append(v)
        if w == 0: return False
        self.piv.append((w.bit_length() - 1, w, m)); self.piv.sort(key=lambda t: -t[0])
        return True

    def reduce(self, v):
        m = 0
        for p, r, rm in self.piv:
            if (v >> p) & 1: v ^= r; m ^= rm
        return v, m


def gauss_solve(cols, target):
    """find all masks c with XOR_{j in c} cols[j] == target (cols: ints). returns (part, nullmasks) or None"""
    piv = []      # (pivotbit, vec, mask)
    null = []
    for j, v in enumerate(cols):
        m = 1 << j
        for p, r, rm in piv:
            if (v >> p) & 1: v ^= r; m ^= rm
        if v == 0: null.append(m); continue
        piv.append((v.bit_length() - 1, v, m)); piv.sort(key=lambda t: -t[0])
    m = 0; v = target
    for p, r, rm in piv:
        if (v >> p) & 1: v ^= r; m ^= rm
    if v: return None
    return m, null


def comb(vals, mask):
    v = 0; i = 0
    while mask:
        if mask & 1: v ^= vals[i]
        mask >>= 1; i += 1
    return v


def expr_gates(t, ex, tab, nid, newg):
    """append gates computing tab = XOR(ex) (up to complement); returns signal"""
    if len(ex) == 1:
        s = ex[0]
        if t[s] == tab: return s, nid
        newg.append((3, s, s)); return nid, nid + 1
    cur = ex[0]; acc = t[cur]
    for k, s in enumerate(ex[1:]):
        last = k == len(ex) - 2
        val = acc ^ t[s]
        if last and val != tab:
            newg.append((9, cur, s)); val ^= ONES
        else:
            newg.append((6, cur, s))
        cur = nid; nid += 1; acc = val
    assert acc == tab
    return cur, nid


def topo(n, m, allg, outputs, name):
    N = n + len(allg); order = []; state = [0] * N
    stack = []
    for o in outputs:
        stack.append((o, 0))
        while stack:
            s, ph = stack.pop()
            if s < n or state[s] == 2: continue
            if ph == 0:
                if state[s] == 1: raise ValueError('cycle')
                state[s] = 1; stack.append((s, 1))
                op, a, b = allg[s - n]
                stack.append((b, 0)); stack.append((a, 0))
            else:
                if state[s] != 2: state[s] = 2; order.append(s)
    new = {i: i for i in range(n)}; gl = []
    for s in order:
        op, a, b = allg[s - n]
        new[s] = n + len(gl); gl.append((op, new[a], new[b]))
    return core.Circuit(n, m, gl, [new[s] for s in outputs], name)


def run(c, amax=1, bmax=1, dmax=12, verbose=True, only=None, tlimit=None, level=None):
    t = c.tables(); n = c.n; al = and_levels(c)
    NS = n + len(c.gates)
    L = level or max(al[s] for s in c.outputs)
    top = [g for g in range(n, NS) if c.gates[g - n][0] == 8 and al[g] == L]
    lower = [s for s in range(NS) if al[s] < L]
    S = Basis([ONES] + [t[s] for s in lower]); sg = S.gens
    cost = Cost([(s, t[s]) for s in lower])
    acands = []
    for tab, ex in cost.sig.items():
        if tab & 1 == 0: acands.append((0, tab, ex))     # one per complement class
    if amax >= 1:
        for tab, ex in cost.pair.items():
            if tab & 1 == 0: acands.append((1, tab, ex))
    results = []
    t0 = time.time()
    for i in top:
        if only is not None and i not in only: continue
        others = [j for j in top if j != i]
        W = RBasis(sg + [t[j] for j in others])        # coords: 0..len(sg)-1 = S basis, then others
        ns = len(sg)
        Pr, Pm = W.reduce(t[i])
        if Pr == 0:
            print('product s%d is redundant (in W_i)' % i); continue
        cnt = 0; kept = 0
        for ca, av, aex in acands:
            if tlimit and time.time() - t0 > tlimit: break
            cols = [W.reduce(av & s)[0] for s in sg]
            r = gauss_solve(cols, Pr)
            if r is None: continue
            cnt += 1
            part, null = r
            if len(null) > dmax: continue
            # enumerate b' in the affine set, keep cheap ones
            for k in range(1 << len(null)):
                m = part
                for q, v in enumerate(null):
                    if (k >> q) & 1: m ^= v
                bv = comb(sg, m)
                if bv in (0, ONES): continue
                cb = cost.best(bv, bmax)
                if cb is None: continue
                newP = av & bv
                if newP == t[i]: continue          # same product (trivial re-choice)
                results.append((ca + cb[0], i, (av, aex), (bv, cb[1])))
                kept += 1
        if verbose:
            print('product s%d: a-candidates with a solution %d, cheap pairs %d (%.0fs)' % (i, cnt, kept, time.time() - t0))
    return results, (top, lower, S, cost)


def materialise(c, i, A_, B_, cost):
    """replace product i by AND(a', b'), feed old consumers of i with P' + sum P_j + s"""
    t = c.tables(); n = c.n; al = and_levels(c); NS = n + len(c.gates)
    L = al[i]
    top = [g for g in range(n, NS) if c.gates[g - n][0] == 8 and al[g] == L]
    lower = [s for s in range(NS) if al[s] < L]
    others = [j for j in top if j != i]
    newg = []; nid = NS
    sa, nid = expr_gates(t, A_[1], A_[0], nid, newg)
    sb, nid = expr_gates(t, B_[1], B_[0], nid, newg)
    newg.append((8, sa, sb)); sp = nid; nid += 1
    Pn = A_[0] & B_[0]
    diff = Pn ^ t[i]                                # = sum_{J} P_j + s
    # find J: express diff in W = S + others
    sb_ = Basis([ONES] + [t[s] for s in lower]); sg = sb_.gens
    W = RBasis(sg + [t[j] for j in others])
    r, m = W.reduce(diff); assert r == 0
    ns = len(sg)
    J = [others[q - ns] for q in range(ns, ns + len(others)) if (m >> q) & 1]
    srem = diff
    for j in J: srem ^= t[j]
    # srem in S: cheapest expression
    terms = [sp] + J; acc = Pn
    for j in J: acc ^= t[j]
    cur = sp
    seq = J[:]
    flip = False
    if srem in (0, ONES):
        seq_s = []
    else:
        ce = cost.best(srem, 2)
        if ce is None:
            return None            # s needs > 3 existing signals: skip
        seq_s = list(ce[1])
    tabs = {s: t[s] for s in range(NS)}
    tabs[sp] = Pn
    ops = seq + seq_s
    target = t[i]
    if not ops:
        if flip:
            newg.append((3, cur, cur)); cur = nid; nid += 1
    else:
        run = Pn; cur = sp
        for k, s in enumerate(ops):
            last = k == len(ops) - 1
            v = run ^ tabs[s]
            if last and v != target:
                newg.append((9, cur, s)); v ^= ONES
            else:
                newg.append((6, cur, s))
            cur = nid; nid += 1; run = v
        if run != target:
            newg.append((3, cur, cur)); cur = nid; nid += 1
    # rewire consumers of i to cur
    allg = []
    for g in range(n, NS):
        op, a, b = c.gates[g - n]
        if g != i:
            a = cur if a == i else a; b = cur if b == i else b
        allg.append((op, a, b))
    allg += newg
    outs = [cur if s == i else s for s in c.outputs]
    nc = topo(n, c.m, allg, outs, c.name)
    return nc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circuit')
    ap.add_argument('--emit')
    ap.add_argument('--amax', type=int, default=1)
    ap.add_argument('--bmax', type=int, default=1)
    ap.add_argument('--dmax', type=int, default=12)
    ap.add_argument('--slack', type=int, default=2)
    ap.add_argument('--tlimit', type=float); ap.add_argument('--level', type=int)
    args = ap.parse_args()
    c = load(args.circuit); m0 = metrics(c); vt = c.value_table()
    print('start', m0)
    res, (top, lower, S, cost) = run(c, args.amax, args.bmax, args.dmax, tlimit=args.tlimit, level=args.level)
    em = Path(args.emit) if args.emit else None
    if em: em.mkdir(parents=True, exist_ok=True)
    hist = {}; seen = set()
    for cst, i, A_, B_ in res:
        nc = materialise(c, i, A_, B_, cost)
        if nc is None: continue
        assert nc.value_table() == vt
        m = metrics(nc)
        k = (m[2] - m0[2], m[3] - m0[3]); hist[k] = hist.get(k, 0) + 1
        h = cid(nc)
        if em and m[2] <= m0[2] + args.slack and m[1] <= m0[1] and h not in seen:
            seen.add(h)
            (em / ('s%d-%s-g%d-gd%d.bfx' % (i, h, m[2], m[3]))).write_text(core.to_kernel(nc))
    print('dG,dGD histogram:', sorted(hist.items()))
    print('emitted', len(seen))


if __name__ == '__main__':
    main()
