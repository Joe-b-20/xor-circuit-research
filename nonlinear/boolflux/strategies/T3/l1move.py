#!/usr/bin/env python3
"""T3: level-1 product exchange move. For each level-1 AND P_i and each pair (a', b') of x-linear forms
with a'b' = P_i mod (affine + other level-1 ANDs) (exhaustive, l1swap.py), materialise: a', b' built from
the existing level-0 signals (cheapest XOR expression, up to 3 signals; else skipped), P' = AND(a', b'),
the old consumers of P_i fed with P' + (other level-1 ANDs) + (affine part), dead gates removed.
Everything above level 1 is unchanged as functions, so AD, A stay. Writes the built circuits.
    python3 l1move.py CIRCUIT --emit DIR"""
import argparse
import itertools
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core                                    # noqa: E402
from boolflux.hub.common import load, metrics, ONES, cid     # noqa: E402
from pairs import and_levels, Cost                           # noqa: E402
from prodswap import RBasis, materialise                     # noqa: E402

def l1_variants(c):
    n = c.n; t = c.tables(); al = and_levels(c); NS = n + len(c.gates)
    vt = c.value_table()
    X = core.input_tables(8)
    lin = []
    for m in range(1, 256):
        v = 0
        for i in range(8):
            if (m >> i) & 1: v ^= X[i]
        lin.append(v)
    lower = [s for s in range(NS) if al[s] < 1]
    cost = Cost([(s, t[s]) for s in lower])
    A1 = [g for g in range(n, NS) if c.gates[g - n][0] == 8 and al[g] == 1]
    out = []; seen = set()
    for g in A1:
        W = RBasis([ONES] + X + [t[h] for h in A1 if h != g])
        Pr, _ = W.reduce(t[g])
        op, x, y = c.gates[g - n]
        for i, u in enumerate(lin):
            for v in lin[i:]:
                if W.reduce(u & v)[0] != Pr: continue
                if (u & v) == t[g]: continue
                cu = cost.best(u, 2); cv = cost.best(v, 2)
                if cu is None or cv is None: continue
                # complement variants of the operands (affine): try both polarities of each
                for pu, pv in itertools.product((u, u ^ ONES), (v, v ^ ONES)):
                    eu = cost.best(pu, 2); ev = cost.best(pv, 2)
                    if eu is None or ev is None: continue
                    try:
                        nc = materialise(c, g, (pu, eu[1]), (pv, ev[1]), cost)
                    except Exception as e:
                        continue
                    if nc is None or nc.value_table() != vt: continue
                    mm = metrics(nc); k = cid(nc)
                    if k in seen: continue
                    seen.add(k); out.append((mm[2], mm[3], g, k, nc))
    out.sort(key=lambda r: (r[0], r[1]))
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('circuit'); ap.add_argument('--emit')
    a = ap.parse_args()
    c = load(a.circuit); m0 = metrics(c)
    out = l1_variants(c)
    from collections import Counter
    print(m0, 'built', len(out), 'dG histogram', sorted(Counter(r[0] - m0[2] for r in out).items()))
    print('best', [(r[0], r[1], 's%d' % r[2]) for r in out[:12]])
    if a.emit:
        d = Path(a.emit); d.mkdir(parents=True, exist_ok=True)
        for g_, gd, gi, k, nc in out[:40]:
            (d / ('a35-ad3-g%d-gd%d-%s.bfx' % (g_, gd, k))).write_text(core.to_kernel(nc))


if __name__ == '__main__':
    main()
