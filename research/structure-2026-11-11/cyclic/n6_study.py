"""Exact L and L_cyc for small invertible matrices with 6 inputs (driver for exact6.c).

Usage: python3 n6_study.py MODE [COUNT] [SEED]
  MODE = test      the n = 5 example and two sanity cases
  MODE = circ      all invertible 6x6 circulants with odd row weight, and their inverses
  MODE = flavour   COUNT random invertible 6x6 matrices with all rows and columns of odd weight,
                   rows of weight >= 3, and their inverses
  MODE = flavour_all   every such matrix, as a set of 6 distinct rows (exhaustive)
  MODE = example   the inverse-pair example of the report
  MODE = rows3 | rows4 | rows5   COUNT random sets of 3, 4 or 5 distinct non-unit target vectors
  MODE = random    COUNT random invertible 6x6 matrices and their inverses
For each matrix A the C program gives L_cyc(A) and L(A) exactly (exhaustive enumeration); the script
prints L_cyc(A), L(A), L_cyc(A^-1), L(A^-1) and the minimum weight d of a linear relation among the
2n vectors "units and rows".  It reports every case with L_cyc < L or L(A) != L(A^-1).
"""
import random
import subprocess
import sys
from itertools import combinations

N = 6


def inverse(rows, n):
    a = list(rows)
    b = [1 << i for i in range(n)]
    for col in range(n):
        p = next((i for i in range(col, n) if (a[i] >> col) & 1), None)
        if p is None:
            return None
        a[p], a[col] = a[col], a[p]
        b[p], b[col] = b[col], b[p]
        for i in range(n):
            if i != col and (a[i] >> col) & 1:
                a[i] ^= a[col]
                b[i] ^= b[col]
    # now sum_j b[i][j] * rows[j] = e_i  (b = A^-1 acting on rows)
    return b


def transpose(rows, n):
    return [sum(((rows[i] >> j) & 1) << i for i in range(n)) for j in range(n)]


def min_relation(rows, n):
    best = 2 * n + 1
    for k in range(1, n + 1):
        for sub in combinations(rows, k):
            x = 0
            for r in sub:
                x ^= r
            best = min(best, k + bin(x).count("1"))
    return best


def show(rows, n):
    return " ".join("".join("1" if (r >> j) & 1 else "0" for j in range(n)) for r in rows)


def run(mats, n, kmax=7):
    inp = "".join("%d %d %s\n" % (n, len(m), " ".join(map(str, m))) for m in mats)
    out = subprocess.run(["./exact6.bin", str(kmax)], input=inp, capture_output=True, text=True, check=True).stdout
    res = []
    for line in out.strip().split("\n"):
        head = line.split("|")[0].split()
        res.append((int(head[0]), int(head[1]), line))
    return res


def study(mats, n, label):
    inv = [inverse(m, n) for m in mats]
    r1 = run(mats, n)
    r2 = run(inv, n)
    gaps = diffs = bad = 0
    hist = {}
    for m, mi, a, b in zip(mats, inv, r1, r2):
        key = (a[0], a[1], b[0], b[1], min_relation(m, n))
        hist[key] = hist.get(key, 0) + 1
        if a[0] != b[0]:
            bad += 1
        if a[0] < a[1] or b[0] < b[1]:
            gaps += 1
            print("GAP   A = [%s]  L_cyc=%d L=%d ; A^-1 = [%s] L_cyc=%d L=%d" % (show(m, n), a[0], a[1], show(mi, n), b[0], b[1]))
            print("      ", a[2])
            print("      ", b[2])
        elif a[1] != b[1]:
            diffs += 1
    print("%s: %d matrices; L_cyc(A) != L_cyc(A^-1): %d (theorem: 0); with L_cyc < L for A or A^-1: %d; "
          "L(A) != L(A^-1): %d" % (label, len(mats), bad, gaps, diffs + sum(1 for a, b in zip(r1, r2) if a[1] != b[1] and (a[0] < a[1] or b[0] < b[1]))))
    print("histogram (L_cyc(A), L(A), L_cyc(A^-1), L(A^-1), min relation weight): count")
    for key in sorted(hist):
        print("   ", key, hist[key])


def main():
    mode = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    rng = random.Random(seed)
    if mode == "test":
        vec = lambda s: sum(1 << j for j, ch in enumerate(s) if ch == "1")
        Q = [vec(s) for s in ["11100", "11110", "11111", "01111", "00111", "11011"]]
        print(run([Q, Q[:2] + Q[3:], [7, 11, 13, 14]], 5)[0][:2], "expected (6, 7)")
        print(run([Q[:2] + Q[3:]], 5)[0][:2], "expected (6, 7)")
        print(run([[7, 11, 13, 14]], 4)[0][:2], "J - I, n = 4")
        return
    if mode == "circ":
        mats = []
        for first in range(1, 1 << N):
            w = bin(first).count("1")
            if w % 2 == 0 or w < 3:
                continue
            rows = [((first << s) | (first >> (N - s))) & ((1 << N) - 1) for s in range(N)]
            if inverse(rows, N) is None:
                continue
            if any(sorted(rows) == sorted(m) for m in mats):
                continue
            mats.append(rows)
        study(mats, N, "circulants")
        return
    if mode == "flavour_all":
        oddv = [v for v in range(1, 1 << N) if bin(v).count("1") in (3, 5)]
        mats = []
        for rows in combinations(oddv, N):
            if any(bin(c).count("1") % 2 == 0 for c in transpose(rows, N)):
                continue
            if inverse(rows, N) is None:
                continue
            mats.append(list(rows))
        study(mats, N, "all flavoured row sets")
        return
    if mode == "example":
        vec = lambda s: sum(1 << j for j, ch in enumerate(s) if ch == "1")
        B = [vec(s) for s in ["010001", "001100", "100110", "000011", "101000", "110010"]]
        study([B], N, "inverse-pair example")
        return
    if mode.startswith("rows"):
        m = int(mode[4:])
        pts = [v for v in range(1, 1 << N) if v & (v - 1)]
        sets = [rng.sample(pts, m) for _ in range(count)]
        res = run(sets, N, 6)
        hist = {}
        for M, (lc, l, line) in zip(sets, res):
            hist[(lc, l)] = hist.get((lc, l), 0) + 1
            if lc < l or l < 0:
                print("GAP  M = [%s]  %s" % (show(M, N), line))
        print("random target sets with %d rows, n = %d: %d samples; histogram (L_cyc, L): count" % (m, N, count))
        for key in sorted(hist):
            print("   ", key, hist[key])
        return
    mats = []
    while len(mats) < count:
        if mode == "flavour":
            rows = []
            for _ in range(N):
                w = rng.choice([3, 3, 5])
                rows.append(sum(1 << j for j in rng.sample(range(N), w)))
            if len(set(rows)) < N or any(bin(c).count("1") % 2 == 0 for c in transpose(rows, N)):
                continue
        else:
            rows = [rng.randrange(1, 1 << N) for _ in range(N)]
        if inverse(rows, N) is None:
            continue
        mats.append(rows)
    study(mats, N, mode)


if __name__ == "__main__":
    main()
