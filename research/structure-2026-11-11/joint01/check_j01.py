"""Checks for the J_01 hand argument.  Verifies given objects and finite linear-algebra facts only.
No search over circuits.  The hand proofs do not depend on this file.

Vectors of the mirror: 8 bits, low nibble = omega (over w_0..w_3), high nibble = s (over w'_0..w'_3).
A_i = (E_i | p_i), B_i = (0 | E_i), p_i = u_(i-1) + u_i, X(v) = (v | v).

Part 1: the linear-algebra facts used in the proof of "L >= 11", for every basis {v1, v2, v3} of the even space:
   N   no required vector (A_i, X_m; with B_i in the T version) is the sum of two named vectors
       (named = inputs and required vectors);
   F2  the sum of two required vectors of S is never (unit | 0) or (even | 0); the seven required vectors are
       independent;
   F3  every vector beta has at most one representation  beta = required + w_i  or  beta = required + required
       (unordered), and none if beta = (even | 0).
Part 2: a given mirror circuit T with tau = 3 and 19 gates (K = 22): evaluated and checked.
Part 3: its 12 gates with omega != 0 are a circuit S for A_0..A_3 and three independent diagonal vectors (L <= 12).
"""
from itertools import combinations

U = [1, 2, 4, 8]
EVEN = [v for v in range(1, 16) if bin(v).count("1") % 2 == 0]
E = [15 ^ U[i] for i in range(4)]
P = [U[(i - 1) % 4] | U[i] for i in range(4)]
W = [U[i] for i in range(4)]
WP = [U[i] << 4 for i in range(4)]
A = [E[i] | (P[i] << 4) for i in range(4)]
B = [E[i] << 4 for i in range(4)]


def rank(vs):
    basis = []
    for v in vs:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
    return len(basis)


def part1():
    nb = 0
    for vs in combinations(EVEN, 3):
        if rank(vs) < 3:
            continue
        nb += 1
        X = [v | (v << 4) for v in vs]
        req_s = A + X
        named_s = W + req_s
        req_t = A + B + X
        named_t = W + WP + req_t
        for x, y in combinations(named_s, 2):
            assert (x ^ y) not in req_s, "N (S)"
        for x, y in combinations(named_t, 2):
            assert (x ^ y) not in req_t, "N (T)"
        assert rank(req_s) == 7, "independence"
        for x, y in combinations(req_s, 2):
            d = x ^ y                     # never (unit | 0) and never (even | 0); (triple | 0) does occur
            assert not (d >> 4 == 0 and (d & 15) not in E), "F2"
        for beta in range(1, 256):
            if beta & 15 == 0 or beta in named_s:
                continue
            reps = sum(1 for t in req_s for w in W if t ^ w == beta)
            reps += sum(1 for x, y in combinations(req_s, 2) if x ^ y == beta)
            assert reps <= 1, "F3"
            if beta >> 4 == 0 and bin(beta & 15).count("1") % 2 == 0:
                assert reps == 0, "F3 pure even"
    print("part 1: N, F2, independence, F3 hold for all %d bases of the even space" % nb)


def part2():
    names = {}
    order = []

    def gate(name, x, y):
        names[name] = names[x] ^ names[y]
        order.append(name)

    for i in range(4):
        names["w%d" % i] = W[i]
        names["v%d" % i] = WP[i]          # v_i stands for w'_i
    # gates with omega = 0 (seven): three even vectors and the four B_i
    gate("P13", "v1", "v3")
    gate("P03", "v0", "v3")
    gate("P12", "v1", "v2")
    gate("B0", "P12", "v3")
    gate("B1", "P03", "v2")
    gate("B2", "P13", "v0")
    gate("B3", "P12", "v0")
    # gates with omega != 0 (twelve)
    gate("m", "w1", "w2")            # (12 | 0)
    gate("a", "w2", "P13")           # (2 | 13)    entry
    gate("b", "w3", "P03")           # (3 | 03)    entry
    gate("X12", "m", "P12")          # (12 | 12)   entry, export
    gate("c", "a", "w3")             # (23 | 13)
    gate("X03", "w0", "b")           # (03 | 03)   export
    gate("d", "X12", "P13")          # (12 | 23)   entry
    gate("A3", "d", "w0")
    gate("A0", "m", "b")
    gate("A1", "X03", "a")
    gate("A2", "A3", "c")
    gate("X23", "c", "P12")          # (23 | 23)   entry, export
    for i in range(4):
        assert names["A%d" % i] == A[i], "A%d" % i
        assert names["B%d" % i] == B[i], "B%d" % i
    exports = [names[x] for x in ("X12", "X03", "X23")]
    diag = [e | (e << 4) for e in (0b0011, 0b0110, 0b1100)]
    assert all(x & 15 == x >> 4 for x in exports) and rank(exports) == 3 and rank(exports + diag) == 3
    vals = [names[g] for g in order]
    assert len(set(vals)) == len(vals) and 0 not in vals
    n1 = sum(1 for v in vals if v & 15)
    print("part 2: T has %d gates (%d with omega = 0, %d with omega != 0), contains A_i, B_i and three exports "
          "spanning the diagonal space: K = |T| + tau = %d" % (len(order), len(order) - n1, n1, len(order) + 3))
    print("part 3: the %d gates with omega != 0 read only w_i, each other and vectors (0 | s): L <= %d" % (n1, n1))


if __name__ == "__main__":
    part1()
    part2()
