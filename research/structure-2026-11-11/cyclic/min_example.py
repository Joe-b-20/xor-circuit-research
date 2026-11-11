"""Verify the smallest counterexample to L_cyc = L, independently of enum5.c.

Usage: python3 min_example.py

Example (n = 5).  Q = {11100, 11110, 11111, 01111, 00111, 11011} (strings list the coefficients of
inputs 1..5).  S = units + Q is a cyclic system of size 6 and is not a circuit, and the target set
M = Q has L_cyc(M) = 6 < 7 = L(M).  The 5-row subset M5 = Q minus {11111} has the same values.
The script checks, by exhaustive enumeration written independently of the C program:
  (a) the collinear triples of S and their rank (= 6 = |S| - 5);
  (b) the closure of the unit vectors inside S (= the unit vectors only);
  (c) L(M) and L_cyc(M) exactly, for M = Q and M = M5, by trying every set of extra vectors;
  (d) the same statements for every one of the 2^11 sets at n = 4 (no non-circuit cyclic system).
"""
from itertools import combinations


def vec(s):
    return sum(1 << j for j, ch in enumerate(s) if ch == "1")


def show(v, n):
    return "".join("1" if (v >> j) & 1 else "0" for j in range(n))


def triangles(S):
    Sset = set(S)
    out = []
    for a, b in combinations(sorted(Sset), 2):
        c = a ^ b
        if c > b and c in Sset:
            out.append((a, b, c))
    return out


def rank_rows(rows):
    basis = {}
    r = 0
    for x in rows:
        while x:
            h = x.bit_length() - 1
            if h in basis:
                x ^= basis[h]
            else:
                basis[h] = x
                r += 1
                break
    return r


def tri_rank(S):
    pos = {v: i for i, v in enumerate(sorted(S))}
    return rank_rows([(1 << pos[a]) | (1 << pos[b]) | (1 << pos[c]) for a, b, c in triangles(S)])


def closure(S, start):
    Sset = set(S)
    C = set(start)
    changed = True
    while changed:
        changed = False
        for v in Sset - C:
            if any((v ^ a) in C and (v ^ a) != a for a in C):
                C.add(v)
                changed = True
    return C


def is_cyclic(S, n):
    return tri_rank(S) == len(S) - n


def is_circuit(S, n):
    units = [1 << j for j in range(n)]
    return closure(S, units) == set(S)


def exact(M, n, kmax):
    """(L_cyc, L) of the target set M by exhaustive enumeration of the extra vectors."""
    units = [1 << j for j in range(n)]
    T = sorted(set(v for v in M if v and v & (v - 1)))
    cand = [v for v in range(1, 1 << n) if v & (v - 1) and v not in T]
    lcyc = lcirc = None
    for k in range(kmax + 1):
        for X in combinations(cand, k):
            S = units + T + list(X)
            if lcyc is None and is_cyclic(S, n):
                lcyc = len(T) + k
            if is_circuit(S, n):
                lcirc = len(T) + k
                break
        if lcirc is not None:
            break
    return lcyc, lcirc


def main():
    n = 5
    units = [1 << j for j in range(n)]
    Q = [vec(s) for s in ["11100", "11110", "11111", "01111", "00111", "11011"]]
    S = units + Q
    tris = triangles(S)
    print("n = 5, S = units +", [show(v, n) for v in Q])
    print("collinear triples of S:")
    for t in tris:
        print("   ", [show(v, n) for v in t])
    print("rank of the triples:", tri_rank(S), " |S| - n =", len(S) - n)
    assert is_cyclic(S, n)
    cl = closure(S, units)
    print("closure of the units inside S:", sorted(show(v, n) for v in cl))
    assert cl == set(units) and not is_circuit(S, n)
    lc, l = exact(Q, n, 3)
    print("M = Q (6 rows):        L_cyc = %d, L = %d" % (lc, l))
    assert (lc, l) == (6, 7)
    M5 = [v for v in Q if v != vec("11111")]
    lc, l = exact(M5, n, 3)
    print("M = Q - {11111} (5 rows): L_cyc = %d, L = %d" % (lc, l))
    assert (lc, l) == (6, 7)
    # an explicit 7-gate circuit for Q
    gates = [("11000", "10000", "01000"), ("11100", "11000", "00100"), ("11110", "11100", "00010"),
             ("11111", "11110", "00001"), ("01111", "11111", "10000"), ("00111", "01111", "01000"),
             ("11011", "11111", "00100")]
    have = set(units)
    for g, a, b in gates:
        assert vec(a) in have and vec(b) in have and vec(a) ^ vec(b) == vec(g)
        have.add(vec(g))
    assert set(Q) <= have
    print("explicit 7-gate circuit for Q verified")

    # n = 4: every cyclic set is a circuit set
    n = 4
    units = [1 << j for j in range(n)]
    pts = [v for v in range(1, 16) if v & (v - 1)]
    ncyc = ncirc = 0
    for mask in range(1 << len(pts)):
        S = units + [p for i, p in enumerate(pts) if (mask >> i) & 1]
        cy, ci = is_cyclic(S, n), is_circuit(S, n)
        assert cy or not ci
        ncyc += cy
        ncirc += ci
    print("n = 4: cyclic sets %d, circuit sets %d (all 2^11 subsets tried)" % (ncyc, ncirc))
    assert ncyc == ncirc

    # orbits of the size-6 non-circuit cyclic sets at n = 5 under coordinate permutations
    try:
        from itertools import permutations
        sets = []
        for line in open("n5_noncircuit_small.txt"):
            head, body = line.split(":")
            if head.split()[0] == "6":
                sets.append(frozenset(vec(s) for s in body.split()))
        def perm(v, p):
            return sum(1 << p[j] for j in range(5) if (v >> j) & 1)
        seen, orbits = set(), 0
        for X in sets:
            if X in seen:
                continue
            orbits += 1
            for p in permutations(range(5)):
                seen.add(frozenset(perm(v, p) for v in X))
        print("n = 5: %d non-circuit cyclic sets of size 6 in %d orbit(s) under S_5" % (len(sets), orbits))
        print("       the example is one of them:", frozenset(Q) in set(sets))
    except FileNotFoundError:
        print("(n5_noncircuit_small.txt not present; run run_enum5.sh first for the orbit count)")


if __name__ == "__main__":
    main()
