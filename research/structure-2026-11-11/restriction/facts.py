"""Finite facts about MixColumns used in REPORT.md (weights, distances, merge obstruction, Sergeev bound).

Usage: python3 research/structure-2026-11-11/restriction/facts.py
Standard library only; every check is a direct computation of weights or ranks (no search).
"""
from itertools import combinations
from math import comb

from common import N, apply, inverse, rank, read_matrix, transpose, wt

M = read_matrix()
MT = transpose(M)
FAM = [sum(1 << (k + 8 * b) for b in range(4)) for k in range(8)]   # bit families
ALL = (1 << N) - 1


def short_words(rows, maxw):
    """All nonzero codewords (u, Mu) of weight <= maxw of the graph code of `rows` (maxw <= 10)."""
    inv = inverse(rows)
    half = maxw // 2
    words = set()
    for k in range(1, half + 1):
        for s in combinations(range(N), k):
            u = sum(1 << j for j in s)
            mu = apply(rows, u)
            if wt(u) + wt(mu) <= maxw:
                words.add((u, mu))
            # output half of weight k: u = M^{-1} v
            v = u
            uu = apply(inv, v)
            if wt(uu) + wt(v) <= maxw:
                words.add((uu, v))
    return words


def main():
    rw = sorted({wt(r) for r in M})
    cw = sorted({wt(c) for c in MT})
    print("row weights", rw, "column weights", cw, "M*1 == 1:", apply(M, ALL) == ALL)
    print("rank M =", rank(M))
    for name, rows in (("M", M), ("M^T", MT)):
        ws = short_words(rows, 8)
        hist = {}
        for u, v in ws:
            hist[wt(u) + wt(v)] = hist.get(wt(u) + wt(v), 0) + 1
        print(f"graph code of {name}: words of weight <= 8 by weight: {dict(sorted(hist.items()))}")
    print("bit families fixed by M:", all(apply(M, f) == f for f in FAM))

    # pairwise row distances
    dist = [wt(M[a] ^ M[b]) for a, b in combinations(range(N), 2)]
    print("min row distance", min(dist), "#pairs at distance 4:", dist.count(4))
    # each weight-4 vector is r_a + r_b for at most one pair
    diffs = [M[a] ^ M[b] for a, b in combinations(range(N), 2) if wt(M[a] ^ M[b]) == 4]
    print("distinct weight-4 row differences:", len(set(diffs)), "of", len(diffs))
    # weight-5 rows containing a given 4-set: at most one
    w5 = [r for r in M if wt(r) == 5]
    four = {}
    for r in w5:
        for s in combinations([j for j in range(N) if r >> j & 1], 4):
            key = sum(1 << j for j in s)
            four[key] = four.get(key, 0) + 1
    print("#weight-5 rows:", len(w5), " max #weight-5 rows through one 4-set:", max(four.values()))

    # merge obstruction: weight-5 rows with two disjoint within-family pairs in the support
    fam_of = [j % 8 for j in range(N)]
    obstr = []
    for i, r in enumerate(M):
        if wt(r) != 5:
            continue
        sup = [j for j in range(N) if r >> j & 1]
        pairs = [(p, q) for p, q in combinations(sup, 2) if fam_of[p] == fam_of[q]]
        for (p, q), (s, t) in combinations(pairs, 2):
            if len({p, q, s, t}) == 4:
                obstr.append((i, (p, q), (s, t)))
    rows_hit = sorted({o[0] for o in obstr})
    print(f"weight-5 rows killed (made a unit) by two within-family merges: {len(rows_hit)} rows;"
          f" example row y{obstr[0][0]} = {[j for j in range(N) if M[obstr[0][0]] >> j & 1]},"
          f" merges x{obstr[0][1][0]}~x{obstr[0][1][1]}, x{obstr[0][2][0]}~x{obstr[0][2][1]}")
    # coincidence obstruction: r_a + r_b of weight 4 = union of two within-family pairs
    coinc = []
    for a, b in combinations(range(N), 2):
        d = M[a] ^ M[b]
        if wt(d) != 4:
            continue
        sup = [j for j in range(N) if d >> j & 1]
        for (p, q) in combinations(sup, 2):
            rest = [j for j in sup if j not in (p, q)]
            if fam_of[p] == fam_of[q] and fam_of[rest[0]] == fam_of[rest[1]]:
                coinc.append((a, b, (p, q), tuple(rest)))
                break
    print(f"row pairs merged into one by two within-family merges: {len(coinc)}"
          + (f"; example y{coinc[0][0]},y{coinc[0][1]} via {coinc[0][2]},{coinc[0][3]}" if coinc else ""))
    # single merge never loses a row
    worst = min(wt(r) - 2 for r in M)
    print("after one merge: min row weight >=", worst, "; min row distance >=", min(dist) - 2)

    # Sergeev 2025 (author's slides): L*(B) >= n + (2k-4)/(2k-1) n^(1-1/k) - m, ind(B) >= 2k >= 6
    best = max(((2 * k - 4) / (2 * k - 1) * 32 ** (1 - 1 / k), k) for k in range(3, 17))
    print(f"Sergeev bound for M (n=m=32, ind=32): L(M) >= L*(M) >= {best[0]:.2f} at k={best[1]}")

    # class bound n+m-floor((n+m)/d)+1 and MixColumns bound
    print("class bound (d=6): n+m-floor(64/6)+1 =", 64 - 64 // 6 + 1, "; MixColumns (c=8): 64-8+1 =", 57)
    print("subsets C(32,<=4) per side used:", sum(comb(32, k) for k in range(5)))


if __name__ == "__main__":
    main()
