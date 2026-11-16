#!/usr/bin/env python3
"""Small-depth synthesis of the GF(2^4) inversion block of the BP-style AES circuits.

Inputs x0..x3 (the four inversion inputs, level 0 here).  Targets (16-bit truth tables, from
invspec.py on NIST 116@GD15 / 127@GD14, which share them): y0..y3 and y0^y2, y1^y3 at depth
<= d1, and y0^y1, y2^y3, y0^y1^y2^y3 at depth <= d2.  Gates AND, XOR, XNOR, NOT (cost 1 each).

Search: R_k = functions of depth <= k with every decomposition (op, a, b), a, b in R_{k-1}.
State = one chosen decomposition per function; needed set = DFS from the targets; cost =
|needed| (+ penalty for depth over the target's limit).  Simulated annealing over choices.

    python3 invsyn.py --d1 3 --d2 4 --iters 200000 --seed 1 [--extra x0^x1,...]
"""
import argparse
import math
import random
import sys
from pathlib import Path

M = 0xFFFF
X = [0xAAAA, 0xCCCC, 0xF0F0, 0xFF00]      # x_k = bit k of the index
Y = [0x74cc, 0x7a2a, 0xcf48, 0xa2f8]


def targets(d1, d2, sums4=False):
    y0, y1, y2, y3 = Y
    t = [(y0, d1), (y1, d1), (y2, d1), (y3, d1), (y0 ^ y2, d1), (y1 ^ y3, d1)]
    if d2 <= d1 or sums4:
        t += [(y0 ^ y1, d2), (y2 ^ y3, d2), (y0 ^ y1 ^ y2 ^ y3, d2)]
    return t


def levels(maxd, base):
    """depth[f] for every function reachable within maxd levels from base (depth 0)."""
    depth = {f: 0 for f in base}
    layers = [set(base)]
    for d in range(1, maxd + 1):
        prev = [f for f, k in depth.items() if k <= d - 1]
        new = set()
        for i, a in enumerate(prev):
            na = a ^ M
            if na not in depth: new.add(na)
            for b in prev[i:]:
                for f in (a & b, a ^ b, (a ^ b) ^ M):
                    if f not in depth: new.add(f)
        for f in new: depth[f] = d
        layers.append(new)
        print('depth %d: %d new functions (total %d)' % (d, len(new), len(depth)), file=sys.stderr)
    return depth


class Syn:
    def __init__(self, tg, maxd, base, rng):
        self.tg = tg; self.rng = rng; self.base = set(base)
        self.depth = levels(maxd, base)
        self.byd = {}
        for f, d in self.depth.items(): self.byd.setdefault(d, []).append(f)
        self.dec_cache = {}
        self.choice = {}

    def decs(self, f, maxdepth):
        """All decompositions of f with both operands of depth <= maxdepth - 1."""
        key = (f, maxdepth)
        if key in self.dec_cache: return self.dec_cache[key]
        R = [g for g, d in self.depth.items() if d <= maxdepth - 1]
        Rs = set(R)
        out = []
        if (f ^ M) in Rs: out.append((3, f ^ M, f ^ M))
        for a in R:
            b = f ^ a
            if b in Rs and a <= b: out.append((6, a, b))
            b = f ^ a ^ M
            if b in Rs and a <= b: out.append((9, a, b))
        if maxdepth >= 4:      # deep targets (pair sums): linear roots only, bounded memory
            self.dec_cache[key] = out
            return out
        sup = [a for a in R if a & f == f]
        sups = set(sup)
        for i, a in enumerate(sup):
            # b must contain f and a&b == f: b's bits outside f must avoid a's bits outside f
            for b in sup[i:]:
                if a & b == f: out.append((8, a, b))
        self.dec_cache[key] = out
        return out

    def eval(self, choice):
        need = {}; stack = []
        # required depth per needed function = min over uses
        for f, d in self.tg: stack.append((f, d))
        req = {}
        while stack:
            f, d = stack.pop()
            if f in self.base: continue
            if f in req and req[f] <= d: continue
            req[f] = d
            op, a, b = choice[f]
            stack.append((a, d - 1));
            if b != a: stack.append((b, d - 1))
        # depth check
        dep = {}
        def D(f):
            if f in self.base: return 0
            if f in dep: return dep[f]
            op, a, b = choice[f]
            dep[f] = 1 + max(D(a), D(b)); return dep[f]
        viol = sum(max(0, D(f) - d) for f, d in self.tg)
        viol += sum(max(0, D(f) - d) for f, d in req.items())
        self._ch = choice
        extra, _ = self.complete(req)
        return len(req) + extra, viol, req

    def complete(self, req):
        """Late linear targets self.late = [(table, depth)], depth 4 or 5, in depth order:
        free if present; else one XOR/XNOR of two available signals of depth <= d-1 (cost 1);
        else (u ^ v) ^ w with u, v of depth <= d-2 and w of depth <= d-1 (cost 2, the inner XOR
        becomes available); else penalty 4."""
        late = getattr(self, 'late', [])
        if not late: return 0, []
        dep = getattr(self, '_dep', None)
        avail = {}
        for f in self.base: avail[f] = 0
        # true depths of the needed nodes
        memo = {}
        def D(f):
            if f in self.base: return 0
            if f in memo: return memo[f]
            op, x, y = self._ch[f]
            memo[f] = 1 + max(D(x), D(y)); return memo[f]
        for f in req: avail[f] = D(f)
        cost = 0; gates = []
        for t, d in sorted(late, key=lambda x: x[1]):
            if t in avail and avail[t] <= d: continue
            ok1 = {f for f, dd in avail.items() if dd <= d - 1}
            hit = None
            for x in ok1:
                if (t ^ x) in ok1: hit = (6, x, t ^ x); break
                if (t ^ x ^ M) in ok1: hit = (9, x, t ^ x ^ M); break
            if hit:
                gates.append((hit[0], t, hit[1], hit[2])); avail[t] = d; cost += 1; continue
            ok2 = [f for f, dd in avail.items() if dd <= d - 2]
            done = False
            for i, u in enumerate(ok2):
                for v in ok2[i + 1:]:
                    w = t ^ u ^ v
                    for op, ww in ((6, w), (9, w ^ M)):
                        if ww in ok1:
                            p = u ^ v
                            gates.append((6, p, u, v)); gates.append((op, t, p, ww))
                            avail[p] = d - 1; avail[t] = d; cost += 2; done = True; break
                    if done: break
                if done: break
            if not done:
                cost += 4; gates.append((None, t, None, None))
        return cost, gates

    def init(self):
        ch = {}
        def pick(f, d):
            if f in self.base or f in ch: return
            ds = self.decs(f, d)
            if not ds: ds = self.decs(f, self.depth.get(f, 99))
            # prefer the shallowest
            e = min(ds, key=lambda e: (max(self.depth[e[1]], self.depth[e[2]]), self.rng.random()))
            ch[f] = e
            pick(e[1], d - 1); pick(e[2], d - 1)
        for f, d in self.tg: pick(f, d)
        return ch

    def anneal(self, iters, T0=1.0):
        ch = self.init()
        cost, viol, req = self.eval(ch)
        score = cost + 10 * viol
        best = (score, cost, viol, dict(ch))
        for it in range(iters):
            T = T0 * (1 - it / iters) + 0.05
            f = self.rng.choice(list(req))
            d = req[f]
            ds = self.decs(f, d)
            if not ds: continue
            e = self.rng.choice(ds)
            old = ch[f]
            if e == old: continue
            ch[f] = e
            added = []
            def ensure(g, dd):
                if g in self.base or g in ch: return
                es = self.decs(g, dd)
                if not es: es = self.decs(g, max(1, self.depth.get(g, 99)))
                ee = self.rng.choice(es); ch[g] = ee; added.append(g)
                ensure(ee[1], dd - 1); ensure(ee[2], dd - 1)
            ensure(e[1], d - 1); ensure(e[2], d - 1)
            c2, v2, r2 = self.eval(ch)
            s2 = c2 + 10 * v2
            if s2 <= score or self.rng.random() < math.exp(-(s2 - score) / T):
                score, cost, viol, req = s2, c2, v2, r2
                if s2 < best[0]:
                    best = (s2, c2, v2, {k: ch[k] for k in r2})
                    print('it %d cost %d viol %d' % (it, c2, v2), file=sys.stderr, flush=True)
            else:
                ch[f] = old
                for g in added: ch.pop(g, None)
        return best


NAMES = {6: 'XOR', 9: 'XNOR', 8: 'AND', 3: 'NOT'}


def show(best, base):
    s, cost, viol, ch = best
    names = {X[k]: 'x%d' % k for k in range(4)}
    for f in base:
        if f not in names: names[f] = 'e%04x' % f
    order = []
    def visit(f):
        if f in names and f not in ch: return
        if f in order: return
        op, a, b = ch[f]; visit(a); visit(b); order.append(f)
    for f in ch: visit(f)
    for f in order:
        names.setdefault(f, 'g%04x' % f)
    for f in order:
        op, a, b = ch[f]
        print('  %-5s %s = %s %s' % (NAMES[op], names[f], names[a], '' if op == 3 else names[b]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--d1', type=int, default=3); ap.add_argument('--d2', type=int, default=4)
    ap.add_argument('--iters', type=int, default=100000); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--extra', default='', help='extra level-0 inputs, e.g. 0^1,2^3 (XORs of inputs)')
    a = ap.parse_args()
    base = list(X)
    for e in [x for x in a.extra.split(',') if x]:
        v = 0
        for k in e.split('^'): v ^= X[int(k)]
        base.append(v)
    tg = targets(a.d1, a.d2)
    syn = Syn(tg, max(d for f, d in tg) - 1, base, random.Random(a.seed))
    best = syn.anneal(a.iters)
    have = set(best[3])
    y0, y1, y2, y3 = Y
    sums = [s for s in (y0 ^ y1, y2 ^ y3, y0 ^ y1 ^ y2 ^ y3) if s not in have]
    print('best cost %d viol %d (+%d pair-sum XORs = %d) (extra inputs %s)' % (best[1], best[2], len(sums), best[1] + len(sums), a.extra or '-'))
    show(best, base)


if __name__ == '__main__':
    main()
