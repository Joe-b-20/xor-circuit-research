"""Which members of a published last layer can a K-member layer over E keep?  (track G, exact)

A K-member layer over E that keeps the subset X of a published layer S needs
    d(X) := dim(T + E + span X) - dim(E + span X)  <=  K - |X|
(the K - |X| new products add at most that many dimensions).  This enumerates all 2^|S| subsets,
reports for every size the minimum d(X), and lists the subsets with slack K - |X| - d(X) >= 0
ordered by |X| (largest first): those are the only exact SAT neighbourhoods (free = K - |X|) that
are not trivially infeasible.

usage: python3 subsets.py --l1 FILE --inv FILE --layer FILE --k K [--out OUT.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent / 'C'))
import gf                                             # noqa: E402
from aes_prob import sbox_tables                      # noqa: E402
from ll_prob import prefix_pairs                      # noqa: E402
from lns_sat import layer_products                    # noqa: E402
import qmc                                            # noqa: E402

ONES = (1 << 256) - 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--l1', required=True); ap.add_argument('--inv', required=True)
    ap.add_argument('--layer', required=True); ap.add_argument('--k', type=int, required=True)
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    E = [ONES] + list(gf.X) + [x & y for x, y in prefix_pairs(a.l1, a.inv)]
    En = qmc.Normal(E)
    T = [En.nf(t) for t in sbox_tables()]
    S = [En.nf(x & y) for x, y in layer_products(a.layer)]
    n = len(S)
    # quotient coordinates of T and S mod E
    Tn = qmc.Normal(T)
    dT = Tn.dim()
    best = {}
    feas = []
    for X in range(1 << n):
        vecs = [S[i] for i in range(n) if (X >> i) & 1]
        sx = qmc.Normal(vecs)
        # d(X) = dim(T + X) - dim(X)
        both = qmc.Normal(vecs + T)
        d = both.dim() - sx.dim()
        k = bin(X).count('1')
        if k not in best or d < best[k]: best[k] = d
        if d <= a.k - k:
            feas.append((k, d, X))
    feas.sort(key=lambda t: (-t[0], t[1]))
    res = {'deficit_T_mod_E': dT, 'n': n, 'K': a.k,
           'min_d_by_size': {k: best[k] for k in sorted(best)},
           'generic_d_by_size': {k: max(0, dT - max(0, k - (n - dT))) for k in sorted(best)},
           'max_keep': feas[0][0] if feas else None,
           'n_feasible': len(feas),
           'top': [{'keep': [i + 1 for i in range(n) if (X >> i) & 1], 'size': k, 'd': d, 'free': a.k - k}
                   for k, d, X in feas]}
    print(json.dumps({k: v for k, v in res.items() if k != 'top'}))
    for t in res['top'][:10]: print(json.dumps(t))
    if a.out: Path(a.out).write_text(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
