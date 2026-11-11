"""Section 2: compare identity (2.1) with the F20 ledger G >= 64 + x + 2h + p - r (= 88 + 2h + p - r at x = 24).

F20 (sprint oddh/REPORT.md 2.2-2.3): O = odd signals; an even gate value is hidden if it is not the XOR
of two elements of O (as masks), p = number of hidden values; r = rank of all true four-term relations
on O (4-subsets of O with XOR 0, as vectors in F_2^O).
(2.1) rewritten: G = 2n + x + 2h + q0 - K, q0 = even signals labelling no edge,
K = sum_p r_p + z_r + sum_{missing l, e_l >= 1} (e_l - 1).
The ledger follows from (2.1) iff q0 - K >= p - r; we print p, q0, K, r.
"""
from collections import defaultdict

from lib import CIRC, load, par, Span
from sec2_identity import analyse

for mapdir, fname in (("aes-mixcolumns", "aes-mixcolumns-xor88-depth5.circ.txt"),
                      ("aes-mixcolumns", "aes-mixcolumns-xor89-depth4.circ.txt"),
                      ("aes-invmixcolumns", "aes-invmixcolumns-xor88-depth17.circ.txt"),
                      ("small-scale-aes", "small-scale-aes-xor42-depth5.circ.txt")):
    d = CIRC / mapdir
    n, gates, outs, vals, rows = load(d / fname, next(d.glob("*.mat.txt")))
    a = analyse(n, gates, outs, vals)
    O = [k for k in vals if par(vals[k])]
    idx = {k: i for i, k in enumerate(O)}
    pair = defaultdict(list)
    for i in range(len(O)):
        for j in range(i + 1, len(O)):
            pair[vals[O[i]] ^ vals[O[j]]].append((i, j))
    sp = Span()
    for v, prs in pair.items():
        for s in range(len(prs)):
            for t in range(s + 1, len(prs)):
                (i, j), (k, l) = prs[s], prs[t]
                if len({i, j, k, l}) == 4:
                    sp.add((1 << i) | (1 << j) | (1 << k) | (1 << l))
    r = sp.dim()
    evens = [g for g, _, _ in gates if not par(vals[g])]
    p = sum(1 for g in evens if vals[g] not in pair)
    K = 2 * a["h"] + a["q0"] - (a["G"] - 2 * n - a["x"])
    print(f"{fname}: G={a['G']} x={a['x']} h={a['h']} p={p} q0={a['q0']} K={K} r={r}  "
          f"ledger value 2n+x+2h+p-r={2 * n + a['x'] + 2 * a['h'] + p - r}  (2.1) => ledger: {a['q0'] - K >= p - r}")
