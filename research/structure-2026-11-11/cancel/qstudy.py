"""CHECK (phase 8, main agent): anatomy of the recorded rotation-model circuits Q_m (m = 2, 3, 4).
Reads rotation/circuits/q{m}_{n}.txt, verifies it computes Q_m (rows E_c on block j plus s_c on block j-1,
blocks mod m), and reports per sheet the charged family F_j (ancestors of sheet j nonzero on block j), the
double charges, the gates shared outside window intersections, and the exits (cancellations of a whole block)
on the ancestor sets. Read-only evaluation of given circuits; no search.
usage: python3 qstudy.py FILE M
"""
import sys
from collections import Counter


def E(c):
    return 15 ^ (1 << c)


def S(c):
    return (1 << c) | (1 << ((c + 1) % 4))


def nib(v, j):
    return (v >> (4 * j)) & 15


def blocks(v, m):
    return frozenset(j for j in range(m) if nib(v, j))


def desc(v, m):
    return " ".join("%d:%s" % (j, format(nib(v, j), "04b")[::-1]) for j in range(m) if nib(v, j))


def main(path, m):
    ls = [l.split("#")[0].strip() for l in open(path)]
    ls = [l for l in ls if l]
    n, k = map(int, ls[0].split())
    g = [tuple(map(int, l.split()[:2])) for l in ls[1:1 + k]]
    vals = [1 << i for i in range(n)]
    for a, b in g:
        vals.append(vals[a] ^ vals[b])
    rows = {}
    for j in range(m):
        for c in range(4):
            rows[(c, j)] = (E(c) << (4 * j)) | (S(c) << (4 * ((j - 1) % m)))
    idx = {v: i for i, v in enumerate(vals)}
    assert all(r in idx for r in rows.values()), "orientation"
    win = {j: blocks(rows[(0, j)], m) for j in range(m)}
    anc = {}
    for j in range(m):
        st, A = [idx[rows[(c, j)]] for c in range(4)], set()
        while st:
            s = st.pop()
            if s < n or s in A:
                continue
            A.add(s)
            st.extend(g[s - n])
        anc[j] = A
    F = {j: {x for x in anc[j] if nib(vals[x], j)} for j in range(m)}
    mult = Counter(x for j in range(m) for x in F[j])
    U = len(g) - len(set().union(*F.values()))
    Eo = sum(len(F[j]) - 10 for j in range(m))
    R = sum(v - 1 for v in mult.values() if v > 1)
    print("%s: G=%d windows %s" % (path, len(g), {j: sorted(win[j]) for j in range(m)}))
    print("  |F_j| =", [len(F[j]) for j in range(m)], " E=%d R=%d U=%d  G = 10m + E - R + U = %d" % (Eo, R, U, 10 * m + Eo - R + U))
    exits = []
    for gi, (a, b) in enumerate(g):
        x = n + gi
        lost = (blocks(vals[a], m) | blocks(vals[b], m)) - blocks(vals[x], m)
        if lost:
            exits.append((x, sorted(lost)))
    print("  exits (gate, cancelled blocks):", exits)
    for x, lost in exits:
        a, b = g[x - n]
        for nm, s in (("exit", x), ("op", a), ("op", b)):
            print("     %-4s g%-3d %-22s serves %s charged %s" % (nm, s, desc(vals[s], m),
                  [j for j in range(m) if s in anc[j]], [j for j in range(m) if s in F[j]]))
    for x in range(n, n + len(g)):
        S_ = [j for j in range(m) if x in anc[j]]
        ch = [j for j in range(m) if x in F[j]]
        if len(S_) >= 2 or len(ch) >= 2:
            inter = set.intersection(*[set(win[j]) for j in S_]) if S_ else set()
            print("  g%-3d %-22s serves %s charged %s %s" % (x, desc(vals[x], m), S_, ch,
                  "" if blocks(vals[x], m) <= inter else "OUTSIDE window intersection"))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
