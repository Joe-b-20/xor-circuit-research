#!/usr/bin/env python3
"""T3: Boyar-Peralta (distance-reduction, random ties) re-synthesis of the region-1 XOR logic of an AD3
circuit in exact coordinates, with the level-2 AND operand pairs re-chosen among the 3 equivalent pairs
(a, b), (a, a+b+1), (b, a+b+1).

Coordinates: S1 = span{x_0..x_7, the 11 level-1 ANDs} (constant dropped: XNOR is free), 19 bits.
Base (free): x, every region-0 signal (linear), the level-1 ANDs. Targets: the 24 level-2 operands
(per AND one of its 3 pairs) + the region-1 signals read by region 2 or higher (fixed).
Prints the XOR count of the published choice and of random operand choices (an upper bound on the
region-1 cost for that choice; depth ignored).
    python3 bp1.py CIRCUIT [--restarts 3] [--choices 50] [--seed 1]"""
import argparse
import random
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core                                 # noqa: E402
from boolflux.hub.common import load, metrics, ONES      # noqa: E402
from pairs import and_levels                              # noqa: E402
from prodswap import RBasis                               # noqa: E402

INF = 99


def coords(c):
    n = c.n; t = c.tables(); al = and_levels(c); NS = n + len(c.gates)
    X = core.input_tables(8)
    A1 = [g for g in range(n, NS) if c.gates[g - n][0] == 8 and al[g] == 1]
    R = RBasis([ONES] + X + [t[g] for g in A1])     # gens 0 = const, 1..8 = x, 9.. = A1
    def co(v):
        r, m = R.reduce(v)
        assert r == 0
        return (m >> 1)                               # drop constant
    return R, co, A1


def dist_table(base, nb, maxd=12):
    N = 1 << nb; idx = np.arange(N, dtype=np.int64)
    d = np.full(N, INF, dtype=np.int8)
    b = np.array(sorted(set(base)), dtype=np.int64)
    cur = np.zeros(N, dtype=bool); cur[b] = True; d[cur] = 0
    k = 0
    while k < maxd:
        k += 1
        nxt = np.zeros(N, dtype=bool)
        for e in b: nxt |= cur[idx ^ e]
        new = nxt & (d == INF)
        if not new.any(): break
        d[new] = k; cur = new | cur if False else nxt
    return d


def bp(base, targets, nb, rng):
    base = list(dict.fromkeys(base)); T = [t for t in dict.fromkeys(targets) if t]
    cnt = 0
    while True:
        bs = set(base)
        todo = [t for t in T if t not in bs]
        if not todo: return cnt
        d = dist_table(base, nb)
        # immediate distance-1 targets
        one = [t for t in todo if d[t] == 1]
        if one:
            base.append(one[0]); cnt += 1; continue
        bl = np.array(base, dtype=np.int64)
        tl = np.array(todo, dtype=np.int64)
        dt = d[tl].astype(np.int32)
        best = None; cands = []
        # candidates: all pair sums
        for i in range(len(bl)):
            es = bl[i] ^ bl[i + 1:]
            if len(es) == 0: continue
            # new distance for each target: min(dt, d[t ^ e] + 1), 0 if t == e
            nd = np.minimum(dt[None, :], d[tl[None, :] ^ es[:, None]].astype(np.int32) + 1)
            nd = np.where(tl[None, :] == es[:, None], 0, nd)
            s1 = nd.sum(axis=1); s2 = (nd * nd).sum(axis=1)
            for k in range(len(es)):
                key = (int(s1[k]), -int(s2[k]))
                if best is None or key < best: best = key; cands = [int(es[k])]
                elif key == best: cands.append(int(es[k]))
        e = rng.choice(cands)
        base.append(e); cnt += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circuit'); ap.add_argument('--restarts', type=int, default=3)
    ap.add_argument('--choices', type=int, default=20); ap.add_argument('--seed', type=int, default=1)
    a = ap.parse_args(); rng = random.Random(a.seed)
    c = load(a.circuit); n = c.n; t = c.tables(); al = and_levels(c); NS = n + len(c.gates)
    R, co, A1 = coords(c)
    nb = 8 + len(A1)
    region0 = [s for s in range(NS) if al[s] == 0]
    base = [co(t[s]) for s in region0] + [co(t[g]) for g in A1]
    A2 = [g for g in range(n, NS) if c.gates[g - n][0] == 8 and al[g] == 2]
    cnt1 = sum(1 for g in range(n, NS) if c.gates[g - n][0] != 8 and al[g] == 1)
    # region-1 signals read by region >= 2 XORs (not AND operands)
    ext = set()
    for g in range(n, NS):
        op, x, y = c.gates[g - n]
        if op != 8 and al[g] >= 2:
            for s in (x, y):
                if al[s] == 1 and c.gates[s - n][0] != 8: ext.add(s)
    ext_t = [co(t[s]) for s in ext]
    pairs = []
    for g in A2:
        op, x, y = c.gates[g - n]
        u, v = co(t[x]), co(t[y])
        pairs.append([(u, v), (u, u ^ v), (v, u ^ v)])
    print(metrics(c), 'region-1 XORs now %d; targets: 24 operands + %d external; base %d' % (cnt1, len(ext_t), len(set(base))), flush=True)
    def run(choice):
        tg = [p for k, ch in zip(choice, pairs) for p in ch[k]] + ext_t
        return min(bp(base, tg, nb, random.Random(rng.randrange(1 << 30))) for _ in range(a.restarts))
    r0 = run([0] * len(A2))
    print('published operand pairs: BP region-1 XORs %d' % r0, flush=True)
    best = r0
    for _ in range(a.choices):
        ch = [rng.randrange(3) for _ in A2]
        r = run(ch)
        if r < best: best = r
        print('choice %s: %d (best %d)' % (''.join(map(str, ch)), r, best), flush=True)


if __name__ == '__main__':
    main()
