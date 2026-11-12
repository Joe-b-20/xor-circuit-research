"""CHECK (phase 8, main agent): window collapse against double charges.

For sheet j let A_j = ancestors of sheet j's rows, F_j = gates of A_j nonzero on block j, and pi_j the
projection keeping blocks {j-1, j} (zeroing the rest, including block 7 for sheets 1, 3, 4). Lemma W
(CANCEL.md) gives |F_j| - 10 >= c_j := |F_j| - #(distinct non-input values in pi_j(F_j)).
Reports E = sum_j (|F_j| - 10), C = sum_j c_j, R = sum_g (m(g) - 1)^+, U, and the double-charged gates that
are NOT collapsed in any charging sheet's projection ("survivors": a gate g in F_j counts as collapsed at j if
pi_j(g) is an input or equals pi_j of an EARLIER gate of F_j). Works for MixColumns (kste corpus, recorded)
and for the rotation model files (rotation/circuits/q*_*.txt, with M given). Read-only; no search.
usage: python3 collapse.py --mc STRIDE | python3 collapse.py --q FILE M
"""
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "joint"))
sys.path.insert(0, os.path.join(HERE, "..", "compose", "compat"))


def analyse(n, g, vals, rows, blockmask, m):
    """rows: dict (c, j) -> value; blockmask(j) -> mask of block j; m = number of blocks."""
    idx = {v: i for i, v in enumerate(vals)}
    A, F = {}, {}
    for j in range(m):
        st, S = [idx[rows[(c, j)]] for c in range(4)], set()
        while st:
            s = st.pop()
            if s < n or s in S:
                continue
            S.add(s)
            st.extend(g[s - n])
        A[j] = S
        F[j] = {x for x in S if vals[x] & blockmask(j)}
    mult = Counter(x for j in range(m) for x in F[j])
    E = sum(len(F[j]) - 10 for j in range(m))
    R = sum(v - 1 for v in mult.values() if v > 1)
    U = len(g) - len(mult)
    C = 0
    collapsed = {}
    inputs = set(vals[:n])
    for j in range(m):
        keep = blockmask(j) | blockmask((j - 1) % m)
        seen = set()
        for x in sorted(F[j]):
            p = vals[x] & keep
            if p in inputs or p in seen:
                C += 1
                collapsed.setdefault(x, set()).add(j)
            seen.add(p)
    surv = [x for x, k in mult.items() if k > 1 and not collapsed.get(x)]
    part = sum(1 for x, k in mult.items() if k > 1 and 0 < len(collapsed.get(x, ())) < k - 1)
    return E, C, R, U, surv, part, [len(F[j]) for j in range(m)]


def mc(stride):
    from jstats import get
    from clib import KSTE, ROWS, bm, check, values
    specs = ["r88", "r89", "r97"]
    for fn in sorted(os.listdir(KSTE)):
        if fn.startswith("circuits_"):
            k = sum(1 for l in open(os.path.join(KSTE, fn)) if l.strip())
            specs += ["%s:%d" % (fn, i) for i in range(1, k + 1, stride)]
    rows = {(i, t): ROWS[(i, t)] for i in range(4) for t in range(8)}
    tally = Counter()
    worst = None
    for s in specs:
        g = get(s)
        if not all(check(g)):
            continue
        vals = values(g)
        E, C, R, U, surv, part, Fs = analyse(32, g, vals, {(c, j): rows[(c, j)] for c in range(4) for j in range(8)}, bm, 8)
        tally[(E, C, R, U, len(surv), part)] += 1
        if worst is None or C - R < worst[0]:
            worst = (C - R, s, E, C, R, U, surv, Fs)
    print("MixColumns sample: (E, C, R, U, #double charges collapsed nowhere, #partially collapsed): circuits")
    for k, v in sorted(tally.items(), key=lambda kv: -kv[1])[:20]:
        print("   ", k, v)
    print("  C - R range:", min(k[1] - k[2] for k in tally), "..", max(k[1] - k[2] for k in tally),
          "  E - C range:", min(k[0] - k[1] for k in tally), "..", max(k[0] - k[1] for k in tally))
    print("  smallest C - R:", worst[:6], "survivors", worst[6], "|F_j|", worst[7])


def q(path, m):
    ls = [l.split("#")[0].strip() for l in open(path)]
    ls = [l for l in ls if l]
    n, k = map(int, ls[0].split())
    g = [tuple(map(int, l.split()[:2])) for l in ls[1:1 + k]]
    vals = [1 << i for i in range(n)]
    for a, b in g:
        vals.append(vals[a] ^ vals[b])
    E4 = lambda c: 15 ^ (1 << c)
    S4 = lambda c: (1 << c) | (1 << ((c + 1) % 4))
    rows = {(c, j): (E4(c) << (4 * j)) | (S4(c) << (4 * ((j - 1) % m))) for j in range(m) for c in range(4)}
    E, C, R, U, surv, part, Fs = analyse(n, g, vals, rows, lambda j: 15 << (4 * j), m)
    print("%s: G=%d |F_j|=%s E=%d C=%d R=%d U=%d; double charges collapsed nowhere: %s; partially: %d"
          % (path, len(g), Fs, E, C, R, U, surv, part))


if __name__ == "__main__":
    if sys.argv[1] == "--mc":
        mc(int(sys.argv[2]))
    else:
        q(sys.argv[2], int(sys.argv[3]))
