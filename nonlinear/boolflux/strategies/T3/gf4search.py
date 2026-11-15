#!/usr/bin/env python3
"""T3: search the level-3 GF(4)-coordinate choices of an AD3 circuit (see gf4basis.py).

Model: R targets = {Tr(c x^84) : c in C_a}, C_a = rho^a L, L = GF(2)-span of 4 GF(4)-independent
elements l_1..l_4 (one per GF(4)-point of GF(256)); class bases aligned: c in {rho^a l_i}.
For each choice: (1) check the 8 outputs lie in span{1, Q_a R_c} (exact), (2) region-2 price = greedy
SLP (nearest target first, exact XOR distances <= 3 from the base = signals of AND level <= 1 + the
level-2 ANDs + everything already built), (3) bottom price = Paar greedy on the 8 x 12 output matrix.
    python3 gf4search.py CIRCUIT [--rank 3000] [--top 40] [--json OUT]
"""
import argparse
import itertools
import json
import sys
import time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux.hub.common import load, metrics, _gmul, ONES          # noqa: E402
from pairs import and_levels, Basis                                 # noqa: E402
from prodswap import RBasis                                         # noqa: E402
from gf4basis import RT, QT, dists                                  # noqa: E402

norm = lambda v: min(v, v ^ ONES)


class SLP:
    """greedy: repeatedly build the target with the smallest XOR distance from the current set"""
    def __init__(self, base):
        self.S = list({norm(b) for b in base}); self.Sset = set(self.S)
        self.P = {}
        for u, v in itertools.combinations(self.S, 2):
            w = norm(u ^ v)
            if w not in self.P: self.P[w] = (u, v)

    def copy(self):
        o = SLP.__new__(SLP); o.S = list(self.S); o.Sset = set(self.Sset); o.P = dict(self.P); return o

    def add(self, e):
        e = norm(e)
        if e in self.Sset: return
        for u in self.S:
            w = norm(u ^ e)
            if w not in self.P: self.P[w] = (u, e)
        self.S.append(e); self.Sset.add(e)

    def dist(self, t, deep=True):
        t = norm(t)
        if t in self.Sset: return 0, []
        if t in self.P: return 1, []
        for u in self.S:
            w = norm(t ^ u)
            if w in self.P: return 2, [w]
        if deep:
            for w in self.P:
                if norm(t ^ w) in self.P: return 3, [w, norm(t ^ w)]
        return 4, None

    def build(self, targets):
        todo = [norm(t) for t in targets]; total = 0
        while todo:
            best = None
            for t in todo:
                d, mids = self.dist(t, deep=False)
                if best is None or d < best[0]: best = (d, t, mids)
                if d == 0: break
            if best[0] >= 3:
                best = None
                for t in todo:
                    d, mids = self.dist(t, deep=True)
                    if best is None or d < best[0]: best = (d, t, mids)
            d, t, mids = best
            if d == 4:
                # expensive target: build via greedy pair steps toward it (cost estimate 4)
                total += 4; self.add(t); todo.remove(t); continue
            total += d
            for w in mids: self.add(w)
            self.add(t); todo.remove(t)
        return total


def paar(rows, ncols):
    """cancellation-free Paar greedy: rows = list of int masks over ncols inputs; returns XOR count"""
    rows = [r for r in rows]; cols = ncols; cnt = 0
    while True:
        best = None; bc = 1
        for i in range(cols):
            for j in range(i + 1, cols):
                m = (1 << i) | (1 << j)
                k = sum(1 for r in rows if r & m == m)
                if k > bc: bc = k; best = m
        if best is None: break
        cnt += 1
        nb = 1 << cols; cols += 1
        rows = [(r & ~best) | nb if r & best == best else r for r in rows]
    for r in rows:
        w = bin(r).count('1')
        if w > 1: cnt += w - 1
    return cnt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circuit'); ap.add_argument('--rank', type=int, default=3000)
    ap.add_argument('--top', type=int, default=40); ap.add_argument('--json')
    args = ap.parse_args()
    c = load(args.circuit); n = c.n; t = c.tables(); al = and_levels(c); NS = n + len(c.gates)
    m0 = metrics(c)
    base = [t[s] for s in range(NS) if al[s] <= 1] + [t[g] for g in range(n, NS) if c.gates[g - n][0] == 8 and al[g] == 2]
    outs = [t[s] for s in c.outputs]
    # current classes and the Q <-> class pairing
    inv = {}
    for k, v in RT.items(): inv[v] = k; inv[v ^ ONES] = k
    invq = {}
    for w, v in QT.items(): invq.setdefault(v, w); invq.setdefault(v ^ ONES, w)
    cur = {}
    for g in range(n, NS):
        op, a, b = c.gates[g - n]
        if op != 8 or al[g] != 3: continue
        q = [s for s in (a, b) if t[s] in invq][0]; r = [s for s in (a, b) if t[s] in inv][0]
        cur.setdefault(invq[t[q]], []).append(inv[t[r]])
    ws = sorted(cur)
    Qf = {w: QT[w] for w in ws}
    # rho: scalar mapping class of ws[0] to ws[1]
    l0 = cur[ws[0]]
    rho = None
    for lam in range(2, 256):
        if _gmul(lam, _gmul(lam, lam)) == 1 and lam != 1:
            s1 = {_gmul(lam, z) for z in l0}
            sp1 = set()
            # compare spans
            def span(v):
                e = [0]
                for b in v: e += [x ^ b for x in e]
                return set(e)
            if span(s1) == span(cur[ws[1]]): rho = lam
    print(m0, 'classes', [(w, cur[w]) for w in ws], 'rho', rho)
    rho2 = _gmul(rho, rho)
    scal = [1, rho, rho2]
    # Q-part of region 2: price once (constant across choices)
    slp0 = SLP(base)
    qcost = slp0.copy().build([Qf[w] for w in ws])

    def admissible(Ls):
        prods = [Qf[w] & RT[_gmul(sc, l)] for w, sc in zip(ws, scal) for l in Ls]
        B = Basis([ONES] + prods)
        return all(B.reduce(o) == 0 for o in outs), prods

    def bottom(prods):
        Rb = RBasis([ONES] + prods)
        rows = []
        for o in outs:
            r, m = Rb.reduce(o); assert r == 0
            rows.append(m >> 1)
        return paar(rows, len(prods))

    def price(Ls, slp_base):
        s = slp_base.copy(); s0 = s
        rc = s.build([Qf[w] for w in ws] + [RT[_gmul(sc, l)] for sc in scal for l in Ls])
        return rc

    okc, prods = admissible(l0)
    cur_r = price(l0, slp0); cur_b = bottom(prods)
    print('current: admissible %s, region-2 price (Q+R) %d (Q alone %d), bottom price %d' % (okc, cur_r, qcost, cur_b))
    # GF(4)-points: representatives of GF(4)* orbits
    pts = []; seen = set()
    for z in range(1, 256):
        if z in seen: continue
        orb = {z, _gmul(rho, z), _gmul(rho2, z)}
        seen |= orb; pts.append(z)
    # additive pre-price per point: distances of its 3 R's
    d = dists(base, RT)
    pp = {p: sorted(d[_gmul(sc, p)] for sc in scal) for p in pts}
    # GF(4)-independence: span over GF(4) of points; use GF(2) span of {p, rho p}
    def indep(ps):
        B = Basis([]); k = 0
        for p in ps:
            for sc in (1, rho):
                if not B.add(_gmul(sc, p)): return False
        return True
    t0 = time.time()
    cands = []
    for combo in itertools.combinations(pts, 4):
        a = sum(pp[p][0] + pp[p][1] for p in combo)
        cands.append((a, combo))
    cands.sort()
    print('point quadruples', len(cands), 'additive price range', cands[0][0], cands[-1][0], '%.0fs' % (time.time() - t0))
    res = []
    for a, combo in cands[:args.rank]:
        if not indep(combo): continue
        okc, prods = admissible(list(combo))
        if not okc: continue
        r = price(list(combo), slp0); b = bottom(prods)
        res.append((r + b, r, b, a, combo))
    res.sort()
    print('evaluated %d admissible (%.0fs)' % (len(res), time.time() - t0))
    for x in res[:args.top]: print(x)
    if args.json:
        Path(args.json).write_text(json.dumps({'circuit': args.circuit, 'current': [cur_r, cur_b], 'rho': rho, 'ws': ws,
                                               'res': res[:500]}))


if __name__ == '__main__':
    main()
