#!/usr/bin/env python3
"""T3: randomised Boyar-Peralta distance heuristic for the bottom layer (8 outputs over the 12
level-3 products), many restarts; prints the best XOR count found (an upper bound, [H] as a minimum).
    python3 bpbottom.py CIRCUIT [CIRCUIT ...] --restarts 200 --seed 1"""
import argparse
import random
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux.hub.common import load, metrics       # noqa: E402
from bottomsat import matrix                          # noqa: E402

INF = 99


def dist_table(base, nb):
    N = 1 << nb; idx = np.arange(N)
    d = np.full(N, INF, dtype=np.int16)
    cur = np.zeros(N, dtype=bool); cur[list(base)] = True
    d[cur] = 0; k = 0
    while True:
        k += 1
        nxt = np.zeros(N, dtype=bool)
        for b in base: nxt |= cur[idx ^ b]
        new = nxt & (d == INF)
        if not new.any(): break
        d[new] = k; cur = nxt
        if k > 12: break
    return d


def bp(rows, nb, rng):
    base = [1 << i for i in range(nb)]; T = list(rows); cnt = 0
    while True:
        d = dist_table(base, nb)
        dt = [int(d[t]) for t in T]
        if all(x == 0 for x in dt): return cnt
        best = None; cands = []
        for i in range(len(base)):
            for j in range(i + 1, len(base)):
                e = base[i] ^ base[j]
                if e in base: continue
                nd = [0 if t == e else min(int(d[t]), int(d[t ^ e]) + 1) for t in T]
                key = (sum(nd), -sum(x * x for x in nd))
                if best is None or key < best:
                    best = key; cands = [e]
                elif key == best:
                    cands.append(e)
        base.append(rng.choice(cands)); cnt += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='+'); ap.add_argument('--restarts', type=int, default=100)
    ap.add_argument('--seed', type=int, default=1)
    a = ap.parse_args(); rng = random.Random(a.seed)
    for f in a.files:
        c = load(f); prods, arr, rows = matrix(c)
        res = [bp(rows, 12, rng) for _ in range(a.restarts)]
        print(Path(f).name, metrics(c), 'bottom BP best %d (hist %s)' % (min(res), sorted(set(res))), flush=True)


if __name__ == '__main__':
    main()
