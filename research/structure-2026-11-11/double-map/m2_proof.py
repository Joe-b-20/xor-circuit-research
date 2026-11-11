"""Finite facts used in the proof that L(M2) = 26 (REPORT.md, Theorem D).

usage: python3 m2_proof.py            (about a minute, standard library only)

F1  rho_4(B) = 14 for the 32 boundary masks of M2 (16 inputs, 16 outputs); delta = 16 - 14 = 2.
F2  for every odd mask H outside B (32,736 masks): r(H) := rho_4(B + H) - rho_4(B) <= 2.
    r(H) = 0 if H is not the XOR of three boundary masks; otherwise 1 + the rank, modulo the span of the
    weight-4 relations of B, of the differences of its triple representations.
Also prints the histogram of r(H) and of the number of triple representations.
"""
import collections

import geom


def rank_basis(vecs):
    basis = []
    for v in vecs:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
    basis.sort(reverse=True)
    return basis


def reduce(v, basis):
    for b in basis:
        v = min(v, v ^ b)
    return v


def weight4_relations(points):
    pairs = {}
    n = len(points)
    for i in range(n):
        for j in range(i + 1, n):
            pairs.setdefault(points[i] ^ points[j], []).append((i, j))
    rels = []
    for d, lst in pairs.items():
        i0, j0 = lst[0]
        for (i, j) in lst[1:]:
            rels.append((1 << i0) | (1 << j0) | (1 << i) | (1 << j))
    return rels


def main():
    T = geom.m2_T()
    m = len(T)
    B = geom.boundary(T)
    assert len(set(B)) == 4 * m
    idx = {b: i for i, b in enumerate(B)}
    R4 = rank_basis(weight4_relations(B))
    print("F1: rho_4(B) =", len(R4), " delta =", 2 * m - len(R4))
    # sanity: full relation space has dimension 2m
    hist_r = collections.Counter()
    hist_t = collections.Counter()
    worst = []
    nB = len(B)
    for H in range(1, 1 << (2 * m)):
        if bin(H).count("1") % 2 == 0 or H in idx:
            continue
        triples = []
        for i in range(nB):
            x = H ^ B[i]
            for j in range(i + 1, nB):
                y = x ^ B[j]
                k = idx.get(y)
                if k is not None and k > j:
                    triples.append((1 << i) | (1 << j) | (1 << k))
        hist_t[len(triples)] += 1
        if not triples:
            hist_r[0] += 1
            continue
        diffs = [reduce(t ^ triples[0], R4) for t in triples[1:]]
        r = 1 + len(rank_basis([d for d in diffs if d]))
        hist_r[r] += 1
        if r >= 3:
            worst.append((H, len(triples), r))
    print("F2: histogram of r(H) over the odd masks outside B:", dict(sorted(hist_r.items())))
    print("    histogram of the number of triple representations:", dict(sorted(hist_t.items())))
    print("    max r(H) =", max(hist_r), " masks with r(H) >= 3:", len(worst))
    for H, nt, r in worst[:20]:
        print(f"      H={H:04x} triples={nt} r={r}")


if __name__ == "__main__":
    main()
