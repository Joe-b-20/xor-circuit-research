#!/usr/bin/env python3
"""Splice search: a base circuit whose signals may be replaced by equal-function signals of
donor circuits (with their cones), under a gate-depth cap (track F).

The pinned AES circuits share many exact functions (top-layer forms, GF(2^4) inversion inputs
and outputs, products) at different gate levels: e.g. the inversion inputs are at level 6 in
NIST 116@GD15 and at level 5 in 127@GD14 / 133@GD13 / 141@GD12.  A base circuit B is rebuilt
in gate order; for each of B's gates, a choice says "B's own gate" or "copy donor signal
(circuit k, signal s) with its cone".  Every added gate goes through function hashing (a
function already present at no greater level is reused), so B's and the donors' common
signals merge.  Local search over the choices (single flips, annealed), objective
G + penalty for gate depth over the cap.

    python3 splice.py --cap 14 --base FILE --pool GLOB ... --iters 20000 --seed 1 --out OUT.circ.txt
"""
import argparse
import glob
import math
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2])); sys.path.insert(0, str(HERE))
from boolflux import core, targets   # noqa: E402
from union import load_pool, AESTAB, NIST   # noqa: E402

ONES = (1 << 256) - 1


def levels(c):
    lv = [0] * c.n
    for op, a, b in c.gates: lv.append(1 + max(lv[a], lv[b]))
    return lv


class Splicer:
    def __init__(self, base, donors, D):
        self.B = base; self.D = D
        self.donors = donors                      # list of Circuit
        self.dt = [d.tables() for d in donors]; self.dl = [levels(d) for d in donors]
        self.bt = base.tables(); self.bl = levels(base)
        idx = {}
        for k, (tt, ll) in enumerate(zip(self.dt, self.dl)):
            best = {}
            for s in range(8, len(tt)):
                t = tt[s]
                if t not in best or ll[s] < ll[best[t]]: best[t] = s
            for t, s in best.items(): idx.setdefault(t, []).append((ll[s], k, s))
        self.opts = []
        for s in range(8, len(self.bt)):
            o = sorted(set(idx.get(self.bt[s], [])))
            self.opts.append([(k, ds) for l, k, ds in o])
        self.n = base.n

    def build(self, choice):
        n = self.n
        gates = []; tabs = list(core.input_tables(n)); lv = [0] * n
        fmap = {t: i for i, t in enumerate(tabs)}
        def add(op, a, b):
            t = core.op_apply(op, tabs[a], tabs[b], ONES)
            l = 1 + max(lv[a], lv[b])
            h = fmap.get(t)
            if h is not None and lv[h] <= l: return h
            s = n + len(gates); gates.append((op, a, b)); tabs.append(t); lv.append(l)
            if h is None or l < lv[h]: fmap[t] = s
            return s
        memo = {}
        def copy(k, s):
            if s < n: return s
            key = (k, s)
            if key in memo: return memo[key]
            # iterative DFS over the donor cone
            stack = [s]
            while stack:
                x = stack[-1]
                if (k, x) in memo or x < n: stack.pop(); continue
                op, a, b = self.donors[k].gates[x - n]
                pend = [y for y in (a, b) if y >= n and (k, y) not in memo]
                if pend: stack += pend; continue
                ma = a if a < n else memo[(k, a)]; mb = b if b < n else memo[(k, b)]
                memo[(k, x)] = add(op, ma, mb); stack.pop()
            return memo[key]
        mp = list(range(n))
        for j, (op, a, b) in enumerate(self.B.gates):
            ch = choice[j]
            if ch is None: mp.append(add(op, mp[a], mp[b]))
            else: mp.append(copy(*ch))
        c = core.Circuit(n, self.B.m, gates, [mp[o] for o in self.B.outputs], 'splice',
                         ['U%d' % i for i in range(8)], ['S%d' % i for i in range(8)]).live()
        return c

    def score(self, c):
        lv = levels(c)
        ol = [lv[o] for o in c.outputs]
        ex = sum(max(0, l - self.D) for l in ol)
        return len(c.gates) + 1000 * max(0, max(ol) - self.D) + 20 * ex, max(ol)


def search(sp, iters, seed, init='greedy', T0=0.6, log=None, deadline=None):
    rng = random.Random(seed)
    J = len(sp.B.gates)
    choice = [None] * J
    if init == 'greedy':
        for j in range(J):
            if sp.opts[j]:
                k, ds = sp.opts[j][0]
                if sp.dl[k][ds] < sp.bl[sp.n + j]: choice[j] = (k, ds)
    elif init == 'random':
        for j in range(J):
            if sp.opts[j] and rng.random() < 0.5: choice[j] = rng.choice(sp.opts[j])
    cur = sp.build(choice); cs, cgd = sp.score(cur)
    best = (cs, cur, list(choice))
    movable = [j for j in range(J) if sp.opts[j]]
    t0 = time.time()
    for it in range(iters):
        if deadline and time.time() > deadline: break
        j = rng.choice(movable)
        old = choice[j]
        opts = [None] + sp.opts[j]
        new = rng.choice(opts)
        if new == old: continue
        choice[j] = new
        c = sp.build(choice); s, gd = sp.score(c)
        T = T0 * (1 - it / iters)
        if s <= cs or (T > 0 and rng.random() < math.exp(-(s - cs) / T)):
            cur, cs = c, s
            if s < best[0]:
                best = (s, c, list(choice))
                if log: log('it %d score %d G=%d GD=%d (%.1f s)' % (it, s, len(c.gates), gd, time.time() - t0))
        else:
            choice[j] = old
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cap', type=int, required=True)
    ap.add_argument('--base', required=True)
    ap.add_argument('--pool', nargs='+', required=True)
    ap.add_argument('--iters', type=int, default=20000)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--init', default='greedy')
    ap.add_argument('--T0', type=float, default=0.6)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    pool = [c for f, c in load_pool(a.pool)]
    base = core.read_ncff(a.base)
    sp = Splicer(base, pool, a.cap)
    log = lambda s: print(s, file=sys.stderr, flush=True)
    s, c, ch = search(sp, a.iters, a.seed, a.init, a.T0, log)
    m = c.metrics(NIST); ok = c.value_table() == AESTAB
    print('best: score %d G=%d A=%d GD=%d AD=%d ok=%s' % (s, m['G'], m['A'], m['GD'], m['AD'], ok))
    if ok:
        Path(a.out).write_text(core.write_ncff(c, NIST, comments=['splice: base %s cap %d seed %d' % (Path(a.base).name, a.cap, a.seed)]), encoding='utf-8')


if __name__ == '__main__':
    main()
