"""Exact L(D_T) for all zero-diagonal T of size m up to simultaneous permutation and transposition.

usage: python3 opt_small.py m [--pair] [--limit N] [--reduced-only]
  prints one line per class: T, rank data, valid-partition data, L, eps = L - 3m, profile of the witness.
  --pair also computes the optimum restricted to pair-partition circuits.
"""
import sys
import time

import dmap


def main():
    m = int(sys.argv[1])
    pair = "--pair" in sys.argv
    red_only = "--reduced-only" in sys.argv
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    offdiag = [(j, k) for j in range(m) for k in range(m) if j != k]
    classes = {}
    for bits in range(1 << len(offdiag)):
        T = [0] * m
        for idx, (j, k) in enumerate(offdiag):
            if (bits >> idx) & 1:
                T[j] |= 1 << k
        T = tuple(T)
        if red_only and not dmap.reduced(T):
            continue
        c = dmap.canon(T)
        classes[c] = classes.get(c, 0) + 1
    print(f"# m={m}: {len(classes)} classes", flush=True)
    n = 2 * m
    done = 0
    t_all = time.time()
    for T in sorted(classes, key=lambda t: (sum(bin(r).count('1') for r in t), t)):
        rows = dmap.dmap_rows(T)
        targets = [r for r in rows if bin(r).count("1") > 1]
        red = dmap.reduced(T)
        nz_rows = sum(1 for r in T if r)
        t0 = time.time()
        lo = len(targets)
        L, circ = dmap.optimum(targets, n, lo, 4 * m + 6) if targets else (0, [])
        x, y, odd, blocks = dmap.profile(circ, n)
        line = f"{dmap.tstr(T):<24} red={int(red)} rk={dmap.rank_f2(T)} L={L} eps={L - 3 * m if red else 'na'} " \
               f"x={x} y={y} h={odd - len(targets)} c={len(blocks)}"
        if pair and targets:
            Lp, _ = dmap.optimum(targets, n, L, 4 * m + 6, pair_m=m)
            line += f" Lpair={Lp}"
        line += f" t={time.time() - t0:.1f}s"
        print(line, flush=True)
        done += 1
        if limit and done >= limit:
            break
    print(f"# total {time.time() - t_all:.1f}s", flush=True)


if __name__ == "__main__":
    main()
