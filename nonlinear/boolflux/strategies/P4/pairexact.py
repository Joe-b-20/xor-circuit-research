"""P4: exact bottom XOR count for every per-pair operand choice (3^9), by the transposition principle.

bottom(c) = XOR(M_c) = XOR(M_c^T) + n - 8, n = number of non-zero columns (products used);
XOR(M_c^T) = (#distinct non-unit non-zero columns) + (min helpers H), from minh_c (closure,
exhaustive over helper sets).  Valid for any XOR circuit (cancellation allowed); no depth limit.
Also: lower bound on the pre-inversion 10 + rank X'(c) (section 2.2), forms count.

    python3 pairexact.py CIRC HMAX > out.jsonl
"""
import itertools
import json
import subprocess
import sys
from pathlib import Path

import bottomvar
import pairscan
import preinj

HERE = Path(__file__).resolve().parent


def main():
    path, hmax = sys.argv[1], int(sys.argv[2])
    gates, s, lvl1, pairs, X, P = pairscan.setup(path)
    _, col = bottomvar.bottom_columns(path)
    recs = []
    lines = [str(hmax)]
    for c in itertools.product(range(3), repeat=9):
        cols = bottomvar.matrix(col, c)
        nz = [v for v in cols if v]
        nt = sorted({v for v in nz if v & (v - 1)})
        forms, Xp = pairscan.choice(pairs, X, P, c)
        nf = len({f for f in forms if bin(f).count('1') > 1})
        recs.append((c, len(nz), len(nt), nf, preinj.rank(Xp)))
        lines.append(' '.join(map(str, [len(nt)] + nt)))
    r = subprocess.run([str(HERE / 'minh_c')], input='\n'.join(lines) + '\n', capture_output=True, text=True)
    hs = [int(x) for x in r.stdout.split()]
    assert len(hs) == len(recs), (len(hs), len(recs), r.stderr[:200])
    hist = {}
    for (c, n, nt, nf, rk), h in zip(recs, hs):
        bottom = nt + h + n - 8 if h <= hmax else None
        lb = None if bottom is None else nf + 10 + rk + 13 + bottom   # top >= nf (no helpers), inv 13
        key = (bottom, nf, rk)
        hist[str(key)] = hist.get(str(key), 0) + 1
        print(json.dumps(dict(c=''.join(map(str, c)), n=n, nt=nt, H=h, bottom=bottom, nforms=nf, rankX=rk,
                              lb_linear_top_nohelpers=lb)), flush=True)
    print(json.dumps(dict(hist=hist)), flush=True)


if __name__ == '__main__':
    main()
