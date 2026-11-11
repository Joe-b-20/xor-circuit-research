"""Independent check (pure Python, no C code) of the two invertible examples of REPORT.md.

Usage: python3 examples_verify.py        (about one minute)

Example 2 (n = 6):  B has a 7-gate circuit; A = B^-1 has L_cyc(A) = 7 < 8 = L(A).
Example 3 (n = 7, MixColumns flavour: invertible, every row and column of odd weight, rows of weight
            >= 3, no linear relation of weight < 4 among the 14 vectors "units and rows"):
            B has a 10-gate circuit; A = B^-1 has L_cyc(A) = 10 < 11 = L(A).
For each example the script checks
  - A * B = identity, the flavour conditions (example 3) and the minimum relation weight;
  - the circuit of B gate by gate;
  - that the mask set of that circuit, rewritten in the coordinates given by the rows of B, is a set
    containing the units and the rows of A whose collinear triples have full rank (a cyclic system for A);
  - by exhaustive enumeration of the extra vectors: no cyclic system for A is smaller, and no circuit
    for A has as few gates; and an explicit circuit for A with one more gate.
"""
from itertools import combinations

from min_example import closure, is_circuit, is_cyclic, show, tri_rank, triangles, vec


def inverse(rows, n):
    a = list(rows)
    b = [1 << i for i in range(n)]
    for col in range(n):
        p = next(i for i in range(col, n) if (a[i] >> col) & 1)
        a[p], a[col] = a[col], a[p]
        b[p], b[col] = b[col], b[p]
        for i in range(n):
            if i != col and (a[i] >> col) & 1:
                a[i] ^= a[col]
                b[i] ^= b[col]
    return b


def coords(v, rows, n):
    """c with v = sum_j c_j rows[j]  (v as a combination of the rows)."""
    inv = inverse(rows, n)      # sum_j inv[i]_j rows[j] = e_i
    c = 0
    for i in range(n):
        if (v >> i) & 1:
            c ^= inv[i]
    return c


def min_relation(rows, n):
    best = 2 * n + 1
    for k in range(1, n + 1):
        for sub in combinations(rows, k):
            x = 0
            for r in sub:
                x ^= r
            best = min(best, k + bin(x).count("1"))
    return best


def no_small_system(rows, n, k_cyc, k_circ):
    """True, True if no cyclic system has <= len(rows)+k_cyc elements and no circuit <= len(rows)+k_circ."""
    units = [1 << j for j in range(n)]
    cand = [v for v in range(1, 1 << n) if v & (v - 1) and v not in rows]
    light = set(v for v in cand if bin(v).count("1") == 2)
    need_light = all(bin(r).count("1") >= 3 for r in rows)   # then the first gate is an extra of weight 2
    ok_cyc = ok_circ = True
    for k in range(max(k_cyc, k_circ) + 1):
        for X in combinations(cand, k):
            S = units + list(rows) + list(X)
            if k <= k_cyc and is_cyclic(S, n):
                ok_cyc = False
            if k <= k_circ and (not need_light or light.intersection(X)) and is_circuit(S, n):
                ok_circ = False
    return ok_cyc, ok_circ


def check(name, n, Bstr, gatesB, extraA, flavour):
    print("==", name, "==")
    B = [vec(s) for s in Bstr]
    A = inverse(B, n)        # row i of A: e_i = sum_j A[i]_j * (row j of B)
    # A*B = I  (rows of A combine rows of B to units)
    for i in range(n):
        x = 0
        for j in range(n):
            if (A[i] >> j) & 1:
                x ^= B[j]
        assert x == 1 << i
    print("B rows:", [show(v, n) for v in B])
    print("A = B^-1 rows:", [show(v, n) for v in A])
    for name_, M in (("B", B), ("A", A)):
        cols = [sum((r >> j) & 1 for r in M) for j in range(n)]
        print("  %s: row weights %s, column weights %s, minimum relation weight %d"
              % (name_, [bin(r).count("1") for r in M], cols, min_relation(M, n)))
        if flavour:
            assert all(bin(r).count("1") % 2 == 1 and bin(r).count("1") >= 3 for r in M)
            assert all(c % 2 == 1 for c in cols)
    # the circuit of B
    units = [1 << j for j in range(n)]
    have = set(units)
    for g, a, b in gatesB:
        assert vec(a) in have and vec(b) in have and vec(a) ^ vec(b) == vec(g) and vec(g) not in have
        have.add(vec(g))
    assert set(B) <= have
    G = len(gatesB)
    print("circuit of B with %d gates verified" % G)
    # read from the outputs: coordinates with respect to the rows of B
    S = sorted(coords(v, B, n) for v in have)
    assert set(units) <= set(S) and set(A) <= set(S) and len(S) == n + G
    assert is_cyclic(S, n)
    cl = closure(S, units)
    print("the same masks in output coordinates: %d vectors, contain the units and the rows of A; "
          "triple rank %d = %d; closure of the units has %d of %d elements"
          % (len(S), tri_rank(S), len(S) - n, len(cl), len(S)))
    assert not is_circuit(S, n)
    # exact values for A
    k = G - n
    ok_cyc, ok_circ = no_small_system(A, n, k - 1, k)
    assert ok_cyc and ok_circ
    print("exhaustive: no cyclic system for A with fewer than %d elements; no circuit for A with %d gates" % (G, G))
    SA = units + A + [vec(s) for s in extraA]
    assert len(set(SA)) == len(SA) and is_circuit(SA, n)
    print("explicit circuit set for A with %d gates verified (extras %s)" % (len(SA) - n, extraA))
    print("=> L(B) <= %d,  L_cyc(A) = %d,  L(A) = %d\n" % (G, G, G + 1))


def main():
    check("Example 2 (n = 6)", 6,
          ["010001", "001100", "100110", "000011", "101000", "110010"],
          [("010001", "010000", "000001"), ("001100", "001000", "000100"), ("000011", "000010", "000001"),
           ("101000", "100000", "001000"), ("100010", "100000", "000010"), ("100110", "100010", "000100"),
           ("110010", "100010", "010000")],
          ["011000", "100100"], False)
    # Example 3: B = [42, 7, 69, 70, 13, 56, 100] as integers (bit j = input j+1)
    b3 = ["0101010", "1110000", "1010001", "0110001", "1011000", "0001110", "0010011"]
    assert [vec(s) for s in b3] == [42, 7, 69, 70, 13, 56, 100]
    t1, t2, t3 = "1010000", "0001010", "0010001"
    check("Example 3 (n = 7, MixColumns flavour)", 7, b3,
          [(t1, "1000000", "0010000"), (t2, "0001000", "0000010"), (t3, "0010000", "0000001"),
           ("0101010", t2, "0100000"), ("1110000", t1, "0100000"), ("1010001", t1, "0000001"),
           ("0110001", t3, "0100000"), ("1011000", t1, "0001000"), ("0001110", t2, "0000100"),
           ("0010011", t3, "0000010")],
          [show(v, 7) for v in (3, 6, 83, 90)], True)


if __name__ == "__main__":
    main()
