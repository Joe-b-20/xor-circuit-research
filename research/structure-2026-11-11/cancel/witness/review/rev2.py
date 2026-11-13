"""Review, part 2: (a) the naive reuse rule can leave dead gates (prune them; charges unchanged);
(b) an explicit remainder order in which a remainder prefix equals an output: union changes;
(c) dual test (construction for M^T, pruned, transposed back to M).
Direct construction and evaluation only.  usage: python3 rev2.py
"""
import random
from rev import mixcolumns, construct, analyse, evaluate, transpose


def prune(n, gates, roots_vals):
    vals = evaluate(n, gates)
    pos = {}
    for i, v in enumerate(vals):
        pos.setdefault(v, i)
    keep, st = set(), [pos[v] for v in roots_vals]
    while st:
        x = st.pop()
        if x < n or x in keep:
            continue
        keep.add(x)
        st += list(gates[x - n])
    order = sorted(keep)
    new = {i: i for i in range(n)}
    out = []
    for x in order:
        a, b = gates[x - n]
        out.append((new[a], new[b]))
        new[x] = n + len(out) - 1
    return out


M = mixcolumns()
bm = {j: sum(1 << (8 * k + j) for k in range(4)) for j in range(8)}
unit = lambda w: w // 8
blk = lambda w: w % 8
K = ["G", "distinct", "fully_live", "union", "charged_nonoutputs", "charged_outputs", "E", "R", "U"]

zc = [sum(1 << (8 * c + j) for j in range(8)) for c in range(4)]
H = [zc[(c + 1) % 4] ^ zc[(c + 2) % 4] ^ zc[(c + 3) % 4] for c in range(4)]


def main():
    print("(a) reverse-wire order, before/after pruning dead gates")
    g, ng, hits = construct(32, unit, blk, M, lambda k, ws: sorted(ws, reverse=True))
    r, *_ = analyse(32, g, M, bm); print("  raw   ", {k: r[k] for k in K})
    g2 = prune(32, g, list(M.values()))
    r, *_ = analyse(32, g2, M, bm); print("  pruned", {k: r[k] for k in K})

    print("(b) orders in which a remainder prefix equals an output value")
    for (yk, rk) in [((0, 0), (1, 7)), ((1, 7), (0, 0))]:
        ysup = [w for w in range(32) if M[yk] >> w & 1]
        if any(not (H[rk[0]] ^ M[rk]) >> w & 1 for w in ysup):
            print("  ", yk, rk, "not included"); continue
        def od(key, ws, yk=yk, rk=rk, ysup=ysup):
            if key == rk:
                return ysup + [w for w in sorted(ws) if w not in ysup]
            return sorted(ws, key=lambda w: (w % 8, w // 8))
        g, ng, hits = construct(32, unit, blk, M, od)
        g = prune(32, g, list(M.values()))
        r, vals, outnode, F = analyse(32, g, M, bm)
        print("  y'=%s inside r%s (rows built in sorted order):" % (yk, rk), "hits", hits, {k: r[k] for k in K})

    print("(c) dual test: construction for M^T (wire order), pruned, transposed to M")
    MT = {(k, b): sum(1 << (8 * c + j) for (c, j) in M if M[(c, j)] >> (8 * k + b) & 1) for k in range(4) for b in range(8)}
    keys = sorted(M)
    for nm, od in [("wire", lambda k, ws: sorted(ws)), ("block", lambda k, ws: sorted(ws, key=lambda w: (w % 8, w // 8)))]:
        g, ng, hits = construct(32, unit, blk, MT, od)
        r0, *_ = analyse(32, g, MT, bm)
        g = prune(32, g, list(MT.values()))
        rS, vals, outnode, F = analyse(32, g, MT, bm)
        print("  S (%s) raw G %d live %s; pruned:" % (nm, r0["G"], r0["fully_live"]), {k: rS[k] for k in K}, "hits", len(hits))
        onl = [outnode[k] for k in keys]
        for pol in ["reader", "outfirst", "reverse", "rand"]:
            tg, tout = transpose(32, g, onl, pol, random.Random(5))
            rT, *_ = analyse(32, tg, M, bm, given={(c, j): tout[8 * c + j] for c in range(4) for j in range(8)})
            print("    S^T for M,", pol, {k: rT[k] for k in ["G", "fully_live", "union", "E", "R", "U", "dup_values"]})


if __name__ == "__main__":
    main()
