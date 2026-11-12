"""CHECK (phase 7, main agent): the reader decomposition of the block columns of MixColumns.

Definitions (block b = the 4 wires {8c+b}; V_b = vectors supported on block b):
  P_b = gates with value in V_b ("pure-b gates");
  R_b = gates NOT in V_b having an operand in V_b ("readers"); each has exactly one such operand p_b(g);
  omega'(p): within-pure path vector (omega'(x_{b,k}) = e_k; pure-b gate p = a + c: sum over its pure-b operands);
  rho(g) in F_2^rows: parity of the number of paths from g to each of the 32 output nodes.
Reader identity (proved in READERS.md): for every unit k of block b,
  column (b,k) of M = sum over g in R_b with omega'(p_b(g))_k = 1 of rho(g).
This script VERIFIES the identity on each given circuit and reports, with the sheet partition of the rows:
  rank_b = sum over sheets j of rank(col_b(M) restricted to sheet j)  (7 for b < 7, 16 for b = 7: total 65);
  t_b(g) = number of sheets j in the support of col_b(M) met by rho(g);  X_b = sum_g (t_b(g) - 1)^+;
  slack_b = |R_b| - rank_b + X_b >= 0;  and the gate identity G = sum_b(|P_b| + |R_b|) - #{lambda = 2} + #{lambda = 0}.
usage: python3 readers.py SPEC [SPEC ...]  |  python3 readers.py --scan STRIDE
"""
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from jstats import get  # noqa: E402
sys.path.insert(0, os.path.join(HERE, "..", "compose", "compat"))
from clib import KSTE, ROWS, bm, check, desc, values  # noqa: E402

RKEYS = sorted(ROWS)  # (byte i, bit t); sheet = t


def rank(vs):
    basis = []
    for v in vs:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
    return len(basis)


def nib(v, b):
    return sum(((v >> (8 * c + b)) & 1) << c for c in range(4))


def analyse(g, verbose=False):
    vals = values(g)
    n = len(vals)
    node_of_row = {}
    for r in RKEYS:
        node_of_row[r] = vals.index(ROWS[r], 32)
    # rho via reverse topological order: rho(v) = [v is row] + sum over readers
    readers = [[] for _ in range(n)]
    for gi, (a, c) in enumerate(g):
        readers[a].append(32 + gi)
        readers[c].append(32 + gi)
    rowbit = {node_of_row[r]: 1 << i for i, r in enumerate(RKEYS)}
    rho = [0] * n
    for v in range(n - 1, -1, -1):
        x = rowbit.get(v, 0)
        for w in readers[v]:
            x ^= rho[w]
        rho[v] = x
    sheet_mask = {j: sum(1 << i for i, r in enumerate(RKEYS) if r[1] == j) for j in range(8)}
    pureb = lambda v, b: vals[v] != 0 and vals[v] & ~bm(b) == 0
    out = {}
    lam = Counter()
    for x in range(32, n):
        a, c = g[x - 32]
        L = {b for b in range(8) if pureb(x, b) or pureb(a, b) or pureb(c, b)}
        lam[len(L)] += 1
    tot = Counter()
    for b in range(8):
        om = {}
        for k in range(4):
            om[8 * k + b] = 1 << k
        P, R = [], []
        for x in range(32, n):
            a, c = g[x - 32]
            if pureb(x, b):
                P.append(x)
                om[x] = (om[a] if pureb(a, b) else 0) ^ (om[c] if pureb(c, b) else 0)
            elif pureb(a, b) or pureb(c, b):
                R.append((x, a if pureb(a, b) else c))
        # verify identity
        for k in range(4):
            col = sum(1 << i for i, r in enumerate(RKEYS) if ROWS[r] >> (8 * k + b) & 1)
            s = 0
            for x, p in R:
                if om[p] >> k & 1:
                    s ^= rho[x]
            assert s == col, ("identity fails", b, k)
        supp = [j for j in range(8) if any(ROWS[(i, j)] & bm(b) for i in range(4))]
        rk = 0
        for j in supp:
            rk += rank([sum(((ROWS[(i, j)] >> (8 * k + b)) & 1) << i for i in range(4)) for k in range(4)])
        X = 0
        multi = []
        for x, p in R:
            t = sum(1 for j in supp if rho[x] & sheet_mask[j])
            if t > 1:
                X += t - 1
                multi.append((x, [j for j in supp if rho[x] & sheet_mask[j]]))
        slack = len(R) - rk + X
        assert slack >= 0
        out[b] = (len(P), len(R), rk, X, slack, multi)
        tot["multi%d" % b] = multi
        tot["P"] += len(P)
        tot["R"] += len(R)
        tot["rank"] += rk
        tot["X"] += X
        tot["slack"] += slack
    G = len(g)
    assert G == tot["P"] + tot["R"] - lam[2] - 2 * lam[3] + lam[0], (G, tot, lam)
    if verbose:
        for b in range(8):
            P, R, rk, X, sl, multi = out[b]
            print("  b=%d |P_b|=%d |R_b|=%d rank=%d X=%d slack=%d multi-sheet readers: %s" % (
                b, P, R, rk, X, sl, "; ".join("g%d %s sheets %s" % (x, desc(vals[x]), js) for x, js in multi)))
    return G, tot, lam


def main():
    if sys.argv[1] == "--scan":
        stride = int(sys.argv[2])
        specs = ["r88", "r89", "r97"]
        for fn in sorted(os.listdir(KSTE)):
            if fn.startswith("circuits_"):
                m = sum(1 for l in open(os.path.join(KSTE, fn)) if l.strip())
                specs += ["%s:%d" % (fn, i) for i in range(1, m + 1, stride)]
        cnt = Counter()
        types = Counter()
        for s in specs:
            g = get(s)
            ok, red = check(g)
            if not (ok and red):
                continue
            G, tot, lam = analyse(g)
            seen = set()
            for b in range(8):
                for x, js in tot["multi%d" % b]:
                    seen.add((b, tuple(js)))
            for t in seen:
                types[t] += 1
            rest = G - tot["R"]
            cnt[(G, tot["R"], tot["X"], tot["slack"], tot["P"], lam[2], lam[0], rest)] += 1
        print("circuits:", sum(cnt.values()))
        print("(G, sum|R_b|, X, slack, P, #lambda2, #lambda0, G - sum|R_b|): count")
        for k, v in sorted(cnt.items(), key=lambda kv: -kv[1])[:25]:
            print("  ", k, v)
        for name, idx in (("sum|R_b|", 1), ("X", 2), ("slack", 3), ("G-sum|R_b|", 7)):
            print("  %s distribution:" % name, dict(sorted(Counter(k[idx] for k in cnt.elements()).items())))
        pair = Counter((k[2], k[3]) for k in cnt.elements())
        print("  (X, slack) pairs:", dict(sorted(pair.items())))
        print("  multi-sheet reader types (block, sheets met): number of circuits containing one")
        for t, v in sorted(types.items()):
            print("    ", t, v)
        return
    for s in sys.argv[1:]:
        g = get(s)
        ok, red = check(g)
        print("== %s valid=%s reduced=%s" % (s, ok, red))
        G, tot, lam = analyse(g, verbose=True)
        print("  G=%d sum|P_b|=%d sum|R_b|=%d rank total=%d X=%d slack=%d lambda=%s" % (
            G, tot["P"], tot["R"], tot["rank"], tot["X"], tot["slack"], dict(sorted(lam.items()))))


if __name__ == "__main__":
    main()
