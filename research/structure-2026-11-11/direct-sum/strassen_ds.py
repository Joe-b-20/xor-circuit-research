"""Hand-designed circuit for A (+) A from one level of the Strassen-Winograd scheme.

A is a fixed n x n matrix over GF(2), n = 2k.  Inputs: x (X side), y (Y side).
C = A [x | y]: block B11 = x_top, B21 = x_bot, B12 = y_top, B22 = y_bot.  The seven
block products M_i = (fixed k x k matrix) * (k-vector) are realised by naive row circuits.
The circuit is verified to compute A x and A y, and its ledger is printed.

This is an illustration of the sharing mechanism (where mixed signals come from, how they
are separated), not a counterexample: neither circuit compared here is claimed optimal.
"""
import random
import sys
from ledger import ledger, check_identities


class Circ:
    def __init__(self, n):
        self.n = n
        self.gates = []
        self.mask = [1 << i for i in range(n)]

    def add(self, a, b):
        if a is None:
            return b
        if b is None:
            return a
        self.gates.append((a, b))
        self.mask.append(self.mask[a] ^ self.mask[b])
        return self.n + len(self.gates) - 1

    def vadd(self, u, v):
        return [self.add(a, b) for a, b in zip(u, v)]

    def matvec(self, M, v):
        out = []
        for row in M:
            acc = None
            for j, bit in enumerate(row):
                if bit:
                    acc = self.add(acc, v[j])
            out.append(acc)
        return out


def madd(*Ms):
    k = len(Ms[0])
    return [[sum(M[i][j] for M in Ms) % 2 for j in range(k)] for i in range(k)]


def blocks(A, k):
    return ([r[:k] for r in A[:k]], [r[k:] for r in A[:k]],
            [r[:k] for r in A[k:]], [r[k:] for r in A[k:]])


def naive_cost(A):
    return sum(max(sum(r) - 1, 0) for r in A)


def build(A):
    n = len(A)
    k = n // 2
    A11, A12, A21, A22 = blocks(A, k)
    C = Circ(2 * n)
    x = list(range(n))
    y = list(range(n, 2 * n))
    B11, B21, B12, B22 = x[:k], x[k:], y[:k], y[k:]
    S1 = madd(A21, A22)
    S2 = madd(S1, A11)
    S3 = madd(A11, A21)
    S4 = madd(A12, S2)
    T1 = C.vadd(B12, B11)        # mixers
    T2 = C.vadd(B22, T1)
    T3 = C.vadd(B22, B12)
    T4 = C.vadd(T2, B21)
    M1 = C.matvec(A11, B11)
    M2 = C.matvec(A12, B21)
    M3 = C.matvec(S4, B22)
    M4 = C.matvec(A22, T4)
    M5 = C.matvec(S1, T1)
    M6 = C.matvec(S2, T2)
    M7 = C.matvec(S3, T3)
    U1 = C.vadd(M1, M2)          # C11
    U2 = C.vadd(M1, M6)
    U3 = C.vadd(U2, M7)
    U4 = C.vadd(U2, M5)
    U5 = C.vadd(U4, M3)          # C12
    U6 = C.vadd(U3, M4)          # C21
    U7 = C.vadd(U3, M5)          # C22
    outX = U1 + U6
    outY = U5 + U7
    return C, outX, outY


def rowmask(row, shift):
    m = 0
    for j, b in enumerate(row):
        if b:
            m |= 1 << (j + shift)
    return m


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 64
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    rng = random.Random(seed)
    A = [[rng.randint(0, 1) for _ in range(n)] for _ in range(n)]
    C, outX, outY = build(A)
    ok = True
    for r in range(n):
        if C.mask[outX[r]] != rowmask(A[r], 0):
            ok = False
        if C.mask[outY[r]] != rowmask(A[r], n):
            ok = False
    G = len(C.gates)
    L = ledger(n, n, C.gates)
    o1, o2, o3 = check_identities(L)
    print("n = %d, seed %d: circuit computes A x and A y: %s" % (n, seed, ok))
    print("gates (Strassen-Winograd level + naive blocks): %d" % G)
    print("two naive row circuits for A: %d" % (2 * naive_cost(A)))
    print("ledger: N_X=%d N_Y=%d d=%d w=%d c=%d beta=%d floating=%d rY=%d rX=%d"
          % (L["NX"], L["NY"], L["d"], L["w"], L["c"], L["beta"], L["floating"],
             L["rY"], L["rX"]))
    print("identities: G=NX+NY-d+w %s; Euler %s; d-bound %s; span lemma %s"
          % (o1, o2, o3, L["lemma_ok"]))
    # unmixing gates: pure result with a mixed operand; type (i) other operand pure on other side
    nn = 2 * n
    mX = (1 << n) - 1
    sig = L["sig"]
    t1 = t2 = 0
    for kk, (i, j) in enumerate(C.gates):
        v = sig[nn + kk]
        if v & mX and v >> n:
            continue
        a, b = sig[i], sig[j]
        am = bool(a & mX) and bool(a >> n)
        bm = bool(b & mX) and bool(b >> n)
        if am and bm:
            t2 += 1
        elif am or bm:
            t1 += 1
    print("unmixing gates: type (i) mixed+pure %d, type (ii) mixed+mixed %d" % (t1, t2))


if __name__ == "__main__":
    main()
