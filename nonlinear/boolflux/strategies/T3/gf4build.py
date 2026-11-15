#!/usr/bin/env python3
"""T3: materialise a level-3 GF(4)-coordinate choice of an AD3 circuit as a full circuit.

Keeps every gate of AND level <= 1 and the level-2 ANDs (with their cones) of the source circuit, rebuilds
the region-2 XOR logic (3 Q's + 12 R's) with a recorded greedy SLP, the 12 level-3 ANDs
Q_a * R(rho^a l_i), and the output layer from the 8 x 12 matrix (Paar greedy, recorded). Verified on all
256 inputs (core value table == source's).
    python3 gf4build.py CIRCUIT --points l1,l2,l3,l4 --out FILE.bfx
"""
import argparse
import itertools
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core                                            # noqa: E402
from boolflux.hub.common import load, metrics, _gmul, ONES           # noqa: E402
from pairs import and_levels, Basis                                  # noqa: E402
from prodswap import RBasis, topo                                    # noqa: E402
from gf4basis import RT, QT                                          # noqa: E402

norm = lambda v: min(v, v ^ ONES)


class Builder:
    """signals with exact tables; XOR network built greedily, every new gate recorded"""
    def __init__(self, n, gates, tabs, base_sigs):
        self.n = n; self.gates = list(gates); self.tab = dict(tabs)
        self.nid = n + len(gates)
        self.sig = {}                       # norm table -> signal
        for s in base_sigs: self.sig.setdefault(norm(self.tab[s]), s)
        self.P = {}
        keys = list(self.sig)
        for u, v in itertools.combinations(keys, 2):
            w = norm(u ^ v)
            if w not in self.sig and w not in self.P: self.P[w] = (u, v)

    def _new(self, op, a, b):
        s = self.nid; self.nid += 1
        self.gates.append((op, a, b))
        ta, tb = self.tab[a], self.tab[b]
        self.tab[s] = (ta ^ tb) if op == 6 else (ta ^ tb ^ ONES) if op == 9 else (ta & tb) if op == 8 else (ta ^ ONES)
        return s

    def add_xor(self, u, v):
        """new signal with norm table u^v from existing norm tables u, v"""
        s = self._new(6, self.sig[u], self.sig[v])
        self._register(s); return s

    def _register(self, s):
        e = norm(self.tab[s])
        if e in self.sig: return
        for u in list(self.sig):
            w = norm(u ^ e)
            if w not in self.sig and w not in self.P: self.P[w] = (u, e)
        self.sig[e] = s
        self.P.pop(e, None)

    def get(self, t):
        """signal with exactly table t, building it (greedy distance <= 3, else basis expansion)"""
        e = norm(t)
        if e not in self.sig:
            if e in self.P:
                u, v = self.P[e]; self.add_xor(u, v)
            else:
                done = False
                for u in list(self.sig):
                    w = norm(e ^ u)
                    if w in self.P:
                        a, b = self.P[w]; self.add_xor(a, b); self.add_xor(w, u); done = True; break
                if not done:
                    for w in list(self.P):
                        w2 = norm(e ^ w)
                        if w2 in self.P:
                            a, b = self.P[w]; self.add_xor(a, b)
                            a, b = self.P[w2]
                            if w2 not in self.sig: self.add_xor(a, b)
                            self.add_xor(w, w2); done = True; break
                if not done:
                    keys = list(self.sig)
                    R = RBasis(keys)
                    r, m = R.reduce(e)
                    assert r == 0, 'target outside span'
                    terms = [keys[i] for i in range(len(keys)) if (m >> i) & 1]
                    acc = terms[0]
                    for x in terms[1:]:
                        nxt = norm(acc ^ x)
                        if nxt not in self.sig: self.add_xor(acc, x)
                        acc = nxt
        s = self.sig[e]
        if self.tab[s] != t:
            s = self._new(3, s, s)
        return s

    def dist(self, t, deep=True):
        e = norm(t)
        if e in self.sig: return 0
        if e in self.P: return 1
        for u in self.sig:
            if norm(e ^ u) in self.P: return 2
        if deep:
            for w in self.P:
                if norm(e ^ w) in self.P: return 3
        return 4

    def build_all(self, targets):
        """greedy nearest-first; returns signals in target order"""
        todo = list(range(len(targets))); out = {}
        while todo:
            best = None
            for i in todo:
                d = self.dist(targets[i], deep=False)
                if best is None or d < best[0]: best = (d, i)
                if d == 0: break
            if best[0] >= 3:
                for i in todo:
                    d = self.dist(targets[i], deep=True)
                    if d < best[0]: best = (d, i)
            i = best[1]; out[i] = self.get(targets[i]); todo.remove(i)
        return [out[i] for i in range(len(targets))]


def paar_build(B, inputs, rows, targets):
    """rows: masks over inputs (signals); builds each row's XOR with Paar greedy; returns output signals
    with exact tables targets (complement fixed by a final XNOR/NOT)"""
    cols = list(inputs); rows = list(rows)
    while True:
        best = None; bc = 1
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                m = (1 << i) | (1 << j)
                k = sum(1 for r in rows if r & m == m)
                if k > bc: bc = k; best = (i, j, m)
        if best is None: break
        i, j, m = best
        s = B._new(6, cols[i], cols[j]); nb = 1 << len(cols); cols.append(s)
        rows = [(r & ~m) | nb if r & m == m else r for r in rows]
    outs = []
    for r, tt in zip(rows, targets):
        terms = [cols[i] for i in range(len(cols)) if (r >> i) & 1]
        if not terms:
            raise ValueError('empty row')
        acc = terms[0]
        for k, x in enumerate(terms[1:]):
            last = k == len(terms) - 2
            v = B.tab[acc] ^ B.tab[x]
            acc = B._new(9 if (last and v != tt) else 6, acc, x)
        if B.tab[acc] != tt: acc = B._new(3, acc, acc)
        outs.append(acc)
    return outs


def build(c, points, rho=None, ws=None, keep2=False):
    n = c.n; t = c.tables(); al = and_levels(c); NS = n + len(c.gates)
    inv = {}
    for k, v in RT.items(): inv[v] = k; inv[v ^ ONES] = k
    invq = {}
    for w, v in QT.items(): invq.setdefault(v, w)
    cur = {}
    for g in range(n, NS):
        op, a, b = c.gates[g - n]
        if op != 8 or al[g] != 3: continue
        q = [s for s in (a, b) if t[s] in invq][0]; r = [s for s in (a, b) if t[s] in inv][0]
        cur.setdefault(invq[t[q]], []).append(inv[t[r]])
    ws = sorted(cur)
    # rho: GF(4) scalar with class(ws[1]) = rho * class(ws[0]) (as spans)
    def span(v):
        e = [0]
        for b in v: e += [x ^ b for x in e]
        return set(e)
    rho = [lam for lam in range(2, 256) if _gmul(lam, _gmul(lam, lam)) == 1
           and span([_gmul(lam, z) for z in cur[ws[0]]]) == span(cur[ws[1]])][0]
    scal = [1, rho, _gmul(rho, rho)]
    # keep: gates of AND level <= 1 and level-2 ANDs with their cones
    keep_out = [g for g in range(n, NS) if al[g] <= 1 or (c.gates[g - n][0] == 8 and al[g] == 2) or (keep2 and al[g] == 2)]
    sub = core.Circuit(n, len(keep_out), list(c.gates), keep_out).live()
    st = sub.tables()
    lower = list(range(sub.n + len(sub.gates)))
    tabs = {s: st[s] for s in lower}
    B = Builder(n, sub.gates, tabs, lower)
    Qs = [QT[w] for w in ws]
    Rs = [RT[_gmul(sc, l)] for sc in scal for l in points]
    sigs = B.build_all(Qs + Rs)
    qs, rs = sigs[:3], sigs[3:]
    prods = []
    for a in range(3):
        for i in range(4):
            prods.append(B._new(8, qs[a], rs[4 * a + i]))
    outs_t = [t[s] for s in c.outputs]
    Rb = RBasis([ONES] + [B.tab[p] for p in prods])
    rows = []
    for o in outs_t:
        r, m = Rb.reduce(o); assert r == 0, 'outputs not in span'
        rows.append(m >> 1)
    outs = paar_build(B, prods, rows, outs_t)
    nc = core.Circuit(n, c.m, B.gates, outs, 'gf4').live()
    assert nc.value_table() == c.value_table()
    return nc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circuit'); ap.add_argument('--points', required=True); ap.add_argument('--out'); ap.add_argument('--keep2', action='store_true')
    args = ap.parse_args()
    c = load(args.circuit)
    pts = [int(x) for x in args.points.split(',')]
    nc = build(c, pts, keep2=args.keep2)
    print(metrics(c), '->', metrics(nc))
    if args.out: Path(args.out).write_text(core.to_kernel(nc))


if __name__ == '__main__':
    main()
