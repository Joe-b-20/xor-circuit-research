"""CHECK (phase 7, main agent): corpus sample statistics of the pure-block decomposition. Read-only, no search.

For every STRIDE-th line of the kste corpus files and the recorded circuits: G, number of pure gates (value on
one block), T1 (non-pure, one pure operand), T2 (two pure operands on different blocks), T0 (no pure operand),
sum_b D_b, nonlocal removals (sum over b), dead gates. Prints a Counter of the tuples and ranges.
usage: python3 jscan.py STRIDE
"""
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from jclass import restrict  # noqa: E402
sys.path.insert(0, os.path.join(HERE, "..", "compose", "compat"))
from clib import KSTE, blocks, bm, check, load, values  # noqa: E402


def stats(g):
    vals = values(g)
    n = len(vals)
    pure = lambda s: len(blocks(vals[s])) == 1
    P = T0 = T1 = T2 = 0
    for x in range(32, n):
        a, c = g[x - 32]
        if pure(x):
            P += 1
            continue
        pb = {min(blocks(vals[s])) for s in (a, c) if pure(s)}
        if len(pb) == 0:
            T0 += 1
        elif len(pb) == 1:
            T1 += 1
        else:
            T2 += 1
    sumD = nonloc = dead = 0
    for b in range(8):
        rem, use = restrict(g, vals, b)
        sumD += len(rem)
        dead += len(g) - len(rem) - len(use)
        for x in rem:
            a, c = g[x - 32]
            if not any(vals[s] & ~bm(b) == 0 for s in (a, c, x)):
                nonloc += 1
    return len(g), P, T1, T2, T0, sumD, nonloc, dead


def main():
    stride = int(sys.argv[1])
    specs = ["r88", "r89", "r97"]
    for fn in sorted(os.listdir(KSTE)):
        if not fn.startswith("circuits_"):
            continue
        n = sum(1 for l in open(os.path.join(KSTE, fn)) if l.strip())
        specs += ["%s:%d" % (fn, i) for i in range(1, n + 1, stride)]
    cnt = Counter()
    rng = {}
    for s in specs:
        g = load(s)
        ok, red = check(g)
        if not (ok and red):
            continue
        t = stats(g)
        cnt[t] += 1
        keys = ["G", "pure", "T1", "T2", "T0", "sumD", "nonlocal", "dead"]
        for k, v in zip(keys, t):
            lo, hi = rng.get(k, (v, v))
            rng[k] = (min(lo, v), max(hi, v))
        if s[0] == "r":
            print(s, dict(zip(keys, t)))
    print("circuits:", sum(cnt.values()))
    for k, v in rng.items():
        print("  %-9s %s" % (k, v))
    nl = Counter(t[6] for t in cnt.elements())
    print("  nonlocal removals per circuit:", dict(sorted(nl.items())))
    sd = Counter(t[5] - t[0] for t in cnt.elements())
    print("  sumD - G:", dict(sorted(sd.items())))
    print("  most common (G,pure,T1,T2,T0,sumD,nonlocal,dead):")
    for t, v in cnt.most_common(8):
        print("   ", t, v)


if __name__ == "__main__":
    main()
