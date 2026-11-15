#!/usr/bin/env python3
"""P7: for a circuit whose outputs are rank-1 bottoms over 4 base Y-forms, count over all 840
common Y-bases the distinct x-forms the bottom needs (forms with >= 2 variables, excluding
those the circuit's AND-level-1 operands already provide), and report the circuit's own basis.

    xcount.py CIRCUIT
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s1lib as L  # noqa: E402
import bsel  # noqa: E402


def main():
    c = L.load(sys.argv[1])
    T, lg, la, Ys, Ylev = bsel.front_info(c)
    U, C = bsel.decompose_outputs(c, T, Ys)
    n = c.n
    # linear x-forms available from AND-level-1 operands (as 8-bit masks)
    avail = set()
    for j, (op, a, b) in enumerate(c.gates):
        if op in L.core.NONLINEAR_OPS and la[n + j] == 1:
            for o in (a, b):
                t = T[o] ^ (L.ONES if T[o] & 1 else 0)
                m = sum(1 << i for i in range(8) if (t >> (1 << i)) & 1)
                if L.lin_table(m) == t: avail.add(m)
    print('Y levels', Ylev, '; level-1 operand forms with >= 2 vars:', sum(1 for m in avail if bin(m).count('1') > 1))
    res = []
    for S in bsel.bases():
        ws = set()
        for j in range(8):
            ws.update(bsel.decomp_in_basis(S, U[j]))
        need = [w for w in ws if bin(w).count('1') > 1 and w not in avail]
        res.append((len(need), len(ws), S))
    res.sort()
    own = [r for r in res if r[2] == (1, 2, 4, 8)][0]
    print('own basis: %d new x-forms (%d distinct)' % own[:2])
    hist = {}
    for r in res: hist[r[0]] = hist.get(r[0], 0) + 1
    print('histogram new-x-forms: bases', sorted(hist.items()))
    print('best 10:', res[:10])


if __name__ == '__main__':
    main()
