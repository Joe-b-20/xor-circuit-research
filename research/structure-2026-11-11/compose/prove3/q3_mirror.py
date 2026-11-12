"""CHECK (not a proof): mirror of the recorded 28-gate Q_3 circuit, and its fibre/exit structure.

Primal: rotation/circuits/q3_28.txt, inputs 4j+c (block j, unit c), outputs E_c(b_j)+s_c(b_{j-1}).
Mirror T: one input per output (c,j) -> bit 4j+c; it must contain R^j_c = E_c(w^j) + p_c(w^{j+1}).
For each group k we report, with omega = part on w^k: first gates, duplicates, pure gates, entries,
exits, and the values of the exits.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CIRC = os.path.join(HERE, "..", "..", "rotation", "circuits", "q3_28.txt")
M = 3


def E4(c):
    return 15 ^ (1 << (c % 4))


def S4(c):
    return (1 << (c % 4)) | (1 << ((c + 1) % 4))


def read():
    ls = [l.split("#")[0].strip() for l in open(CIRC)]
    ls = [l for l in ls if l]
    n, k = map(int, ls[0].split())
    return n, [tuple(map(int, l.split()[:2])) for l in ls[1:1 + k]]


def main():
    n, gates = read()
    vals = [1 << i for i in range(n)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    rows = {}
    for j in range(M):
        for c in range(4):
            rows[(c, j)] = (E4(c) << (4 * j)) | (S4(c) << (4 * ((j - 1) % M)))
    outg = {}
    for key, r in rows.items():
        outg[key] = min(i for i in range(n, len(vals)) if vals[i] == r)
    # transpose: adjoint of signal = XOR of adjoints of readers (+ terminal)
    readers = {}
    for gi, (a, b) in enumerate(gates):
        for o in (a, b):
            readers.setdefault(o, []).append(n + gi)
    term = {}
    for (c, j), g in outg.items():
        term.setdefault(g, []).append(4 * j + c)
    Tm = [1 << i for i in range(n)]  # mirror inputs = outputs (c,j)
    Tops = [None] * n
    adj = {}
    for v in reversed(range(len(vals))):
        cs = [Tm_idx for Tm_idx in [adj[r] for r in readers.get(v, [])]]
        cs = [("t", t) for t in term.get(v, [])] + [("s", x) for x in cs]
        idxs = [x for kind, x in cs]
        assert idxs, v
        acc = idxs[0]
        for x in idxs[1:]:
            Tm.append(Tm[acc] ^ Tm[x])
            Tops.append((acc, x))
            acc = len(Tm) - 1
        adj[v] = acc
    print("mirror gates", len(Tm) - n)
    for j in range(M):
        for c in range(4):
            want = (E4(c) << (4 * j)) | (S4((c - 1) % 4) << (4 * ((j + 1) % M)))
            got = Tm[adj[4 * j + c]]
            assert got == want, (c, j, bin(got), bin(want))
    print("adjoints of units are R^j_c = E_c(w^j) + p_c(w^{j+1}): ok")
    # reduce
    seen = set(1 << i for i in range(n))
    red = []
    for i in range(n, len(Tm)):
        v = Tm[i]
        if v == 0 or v in seen:
            continue
        seen.add(v)
        red.append((v, Tm[Tops[i][0]], Tm[Tops[i][1]]))
    print("reduced mirror gates", len(red))

    def fmt(v):
        return "|".join(format((v >> (4 * j)) & 15, "04b")[::-1] for j in range(M))
    for v, a, b in red:
        print("  ", fmt(v), "=", fmt(a), "+", fmt(b))
    for k in range(M):
        low = 15 << (4 * k)
        first = set(1 << (4 * k + i) for i in range(4))
        f = D = N = 0
        ent, exits = [], []
        for v, a, b in red:
            om, oa, ob = v & low, a & low, b & low
            if om == 0:
                N += 1
                if oa:
                    exits.append(fmt(v))
            elif om in first:
                D += 1
                if (oa == 0) != (ob == 0):
                    ent.append(fmt(a if oa == 0 else b))
            else:
                first.add(om)
                f += 1
        print("omega = w^%d: f %d D %d N %d entries %d exits %d" % (k, f, D, N, len(ent), len(exits)))
        print("    labels:", ent)
        print("    exits :", exits)


if __name__ == "__main__":
    main()
