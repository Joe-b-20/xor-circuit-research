"""CHECK (not a proof): mirrors of recorded rotation-ring circuits Q_m and their exits across arc cuts.

Usage: python3 ring_cuts.py CIRCUIT M [order]   (order = fwd | rev: summation order in the transposition)
Primal: inputs 4j+c, outputs E_c(b_j)+s_c(b_{j-1}). Mirror must contain R^j_c = E_c(w^j)+p_c(w^{j+1}).
For an arc S (groups k..k+r-1), omega = part on S. Classify reduced mirror gates:
 first (new omega), entry (one operand omega=0), h (other duplicate), ordinary far, exit.
Reports near = f + h, far = |P| + e, label rank, exit values with their group support,
and for each exit the least number of labels summing to its value (honest cost +1), by span lookup.
"""
import os
import sys
from itertools import combinations


def E4(c):
    return 15 ^ (1 << (c % 4))


def S4(c):
    return (1 << (c % 4)) | (1 << ((c + 1) % 4))


def read(path):
    ls = [l.split("#")[0].strip() for l in open(path)]
    ls = [l for l in ls if l]
    n, k = map(int, ls[0].split())
    return n, [tuple(map(int, l.split()[:2])) for l in ls[1:1 + k]]


def mirror(n, gates, M, order):
    vals = [1 << i for i in range(n)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    outg = {}
    for j in range(M):
        for c in range(4):
            r = (E4(c) << (4 * j)) | (S4(c) << (4 * ((j - 1) % M)))
            outg[(c, j)] = min(i for i in range(n, len(vals)) if vals[i] == r)
    readers = {}
    for gi, (a, b) in enumerate(gates):
        for o in (a, b):
            readers.setdefault(o, []).append(n + gi)
    term = {}
    for (c, j), g in outg.items():
        term.setdefault(g, []).append(4 * j + c)
    Tm = [1 << i for i in range(n)]
    Tops = [None] * n
    adj = {}
    for v in reversed(range(len(vals))):
        idxs = list(term.get(v, [])) + [adj[r] for r in readers.get(v, [])]
        if order == "rev":
            idxs = idxs[::-1]
        acc = idxs[0]
        for x in idxs[1:]:
            Tm.append(Tm[acc] ^ Tm[x])
            Tops.append((acc, x))
            acc = len(Tm) - 1
        adj[v] = acc
    for j in range(M):
        for c in range(4):
            want = (E4(c) << (4 * j)) | (S4((c - 1) % 4) << (4 * ((j + 1) % M)))
            assert Tm[adj[4 * j + c]] == want
    seen = set(1 << i for i in range(n))
    red = []
    for i in range(n, len(Tm)):
        v = Tm[i]
        if v == 0 or v in seen:
            continue
        seen.add(v)
        red.append((v, Tm[Tops[i][0]], Tm[Tops[i][1]]))
    return len(Tm) - n, red


def rank(vs):
    basis = []
    for v in vs:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
    return len(basis)


def main():
    path, M = sys.argv[1], int(sys.argv[2])
    order = sys.argv[3] if len(sys.argv) > 3 else "fwd"
    n, gates = read(path)
    tot, red = mirror(n, gates, M, order)
    print("%s m=%d order=%s: primal %d, mirror %d, reduced %d" % (os.path.basename(path), M, order,
                                                                 len(gates), tot, len(red)))

    def fmt(v):
        return "|".join(format((v >> (4 * j)) & 15, "04b")[::-1] for j in range(M))

    def groups(v):
        return [j for j in range(M) if (v >> (4 * j)) & 15]

    gw = [len(groups(v)) for v, a, b in red]
    print("sum of group weights %d; histogram %s" % (sum(gw), {w: gw.count(w) for w in sorted(set(gw))}))

    def win(g):
        return len(g) == 1 or (len(g) == 2 and ((g[1] - g[0]) % M == 1 or (g[0] - g[1]) % M == 1))
    print("reduced mirror gates outside every window {j,j+1}: %d" % sum(1 for v, a, b in red if not win(groups(v))))
    for r in range(1, M):
        for k in range(M):
            S = [(k + t) % M for t in range(r)]
            low = sum(15 << (4 * j) for j in S)
            first = set(1 << (4 * j + i) for j in S for i in range(4))
            f = e = h = Nord = 0
            labels, exits = [], []
            for idx, (v, a, b) in enumerate(red):
                om, oa, ob = v & low, a & low, b & low
                if om == 0:
                    if oa:
                        exits.append((idx, v, a, b))
                    else:
                        Nord += 1
                elif om in first:
                    if (oa == 0) != (ob == 0):
                        e += 1
                        labels.append((idx, a if oa == 0 else b))
                    else:
                        h += 1
                else:
                    first.add(om)
                    f += 1
            near, far = f + h, Nord + len(exits) + e
            line = "arc %s: f %d e %d h %d ordfar %d exits %d | near %d far %d | rank(labels) %d" % (
                S, f, e, h, Nord, len(exits), near, far, rank([x for _, x in labels]))
            print(line)
            for idx, v, a, b in exits:
                lab = sorted(set(x for i, x in labels if i < idx))
                best = None
                for t in range(1, min(len(lab), 5) + 1):
                    for cmb in combinations(lab, t):
                        x = 0
                        for c in cmb:
                            x ^= c
                        if x == v:
                            best = t
                            break
                    if best:
                        break
                print("    exit %s groups %s  (=%s + %s)  min#labels %s" % (fmt(v), groups(v), fmt(a), fmt(b), best))


if __name__ == "__main__":
    main()
