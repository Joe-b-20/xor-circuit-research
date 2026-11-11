"""Search for a gap L_cyc < L among 7x7 matrices of the MixColumns flavour (driver for exact7.c).

Usage: python3 n7_study.py COUNT SEED [EXTRA]

Each sample is a random circuit with 7 inputs, EXTRA (default 3) intermediate gates and 7 output gates
whose matrix A is invertible with every row and column of odd weight and every row of weight >= 3.
So L(A) <= G := 7 + EXTRA, and by Theorem C of REPORT.md  L_cyc(A^-1) = L_cyc(A) <= G.
exact7.c then decides by exhaustive enumeration whether A^-1 has a circuit with at most G gates.
If it has none, A^-1 is a flavoured matrix with L_cyc <= G < L.  The script also verifies the sanity
case of the 6x6 inverse pair of the report (padded with a seventh input) when COUNT = 0.
"""
import random
import subprocess
import sys

N = 7


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
    return b


def min_relation(rows, n):
    from itertools import combinations
    best = 2 * n + 1
    for k in range(1, n + 1):
        for sub in combinations(rows, k):
            x = 0
            for r in sub:
                x ^= r
            best = min(best, k + bin(x).count("1"))
    return best


def run(mats, n, kmax, cyc):
    inp = "".join("%d %d %s\n" % (n, len(m), " ".join(map(str, m))) for m in mats)
    out = subprocess.run(["./exact7.bin", str(kmax), str(cyc)], input=inp, capture_output=True, text=True, check=True).stdout
    return [tuple(map(int, line.split("|")[0].split())) for line in out.strip().split("\n")]


def sample(rng, extra):
    while True:
        vals = [1 << i for i in range(N)]
        ok = True
        for _ in range(extra):
            a, b = rng.sample(range(len(vals)), 2)
            v = vals[a] ^ vals[b]
            if v in vals:
                ok = False
                break
            vals.append(v)
        if not ok:
            continue
        outs = []
        for _ in range(N - 1):
            pairs = set()
            for a in range(len(vals)):
                for b in range(a):
                    v = vals[a] ^ vals[b]
                    w = bin(v).count("1")
                    if w % 2 == 1 and w >= 3 and v not in vals:
                        pairs.add(v)
            if not pairs:
                ok = False
                break
            v = rng.choice(sorted(pairs))
            vals.append(v)
            outs.append(v)
        if not ok:
            continue
        # the last output is forced by "every column has odd weight"; it must be one more gate
        t = (1 << N) - 1
        for r in outs:
            t ^= r
        if bin(t).count("1") < 3 or t in vals:
            continue
        if not any((t ^ v) in vals for v in vals):
            continue
        outs.append(t)
        if inverse(outs, N) is None:
            continue
        return outs


def main():
    count, seed = int(sys.argv[1]), int(sys.argv[2])
    extra = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    if count == 0:
        vec = lambda s: sum(1 << j for j, ch in enumerate(s) if ch == "1")
        B = [vec(s) for s in ["010001", "001100", "100110", "000011", "101000", "110010"]] + [1 << 6]
        print("sanity (expected (7, 7) and (7, 8)):", run([B, inverse(B, 7)], 7, 3, 1))
        return
    rng = random.Random(seed)
    mats = []
    seen = set()
    while len(mats) < count:
        A = sample(rng, extra)
        key = tuple(sorted(A))
        if key in seen:
            continue
        seen.add(key)
        mats.append(A)
    G = N + extra
    invs = [inverse(A, N) for A in mats]
    res = run(invs, N, extra, 0)
    hist = {}
    gaps = 0
    for A, Ai, (_, L) in zip(mats, invs, res):
        d = min_relation(A, N)
        key = (d, "L(A^-1) <= %d" % G if L >= 0 else "L(A^-1) > %d" % G)
        hist[key] = hist.get(key, 0) + 1
        if L < 0:
            gaps += 1
            print("GAP: A =", A, " A^-1 =", Ai, " L(A) <= %d, L_cyc(A^-1) <= %d < L(A^-1); min relation weight %d" % (G, G, d))
    print("n = 7, %d flavoured matrices A with a %d-gate circuit; A^-1 without a circuit of <= %d gates: %d"
          % (count, G, G, gaps))
    for key in sorted(hist):
        print("   min relation weight %d, %s: %d" % (key[0], key[1], hist[key]))


if __name__ == "__main__":
    main()
