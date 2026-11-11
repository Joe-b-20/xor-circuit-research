"""Section 1, the negative remark about several points (MixColumns).

1. Best single point. For x != 0 put z = 1 + x. Since every row is odd, M1 = 1 and
   wt(x) + wt(Mx) = 64 - w(z), w(z) = wt(z) + wt(Mz) the weight of the graph-code word of z.
   So the single-point bound at x is 64 - w(z) - c(1+z). It exceeds 56 only if w(z) = 6 and
   c(1+z) = 1 (w(z) is even and >= 6 for z != 0). We enumerate every z of weight <= 5, list the
   words of weight <= 6, and for each weight-6 word exhibit a valid partition of supp(1+z) with
   >= 2 blocks (a lower bound for c), by a greedy 'finest partition' closure.
2. Several points, LP relaxation. For points x_1..x_k (independent), classes = live patterns
   sigma in F_2^k; for each nonzero a, point x_a = sum a_i x_i gives
       sum_{sigma.a = 1} N_sigma >= wt(M x_a),   sum_{sigma.a = 0} N_sigma >= wt(x_a) - c(x_a).
   We replace c by a greedy lower bound (this only raises the right-hand sides, so an LP optimum
   <= 56 computed this way is a rigorous upper bound for the true LP optimum) and solve with scipy.
   Also: the four-inequality system quoted in RECORD section 1 versus the full six-inequality one.
"""
import itertools
import random
import sys

from lib import CIRC, read_matrix, wt, par

random.seed(7)
rows, n = read_matrix(CIRC / "aes-mixcolumns/aes-mixcolumns.mat.txt")
cols = [sum(((rows[o] >> i) & 1) << o for o in range(32)) for i in range(32)]
FULL = (1 << 32) - 1


def Mv(u):
    r = 0
    i = 0
    while u:
        if u & 1:
            r ^= cols[i]
        u >>= 1
        i += 1
    return r


FAMILIES = [sum(1 << (8 * c + j) for c in range(4)) for j in range(8)]
BYTES = [0xFF << (8 * c) for c in range(4)]


def repair(blocks, rws, rng):
    blocks = [b for b in blocks if b]
    while True:
        bad = None
        for r in rws:
            odd = [b for b in blocks if par(r & b)]
            if len(odd) >= 2:
                bad = odd
                break
        if bad is None:
            return blocks
        a, b = rng.sample(bad, 2)
        blocks = [q for q in blocks if q != a and q != b] + [a | b]


def greedy_partition(x, rws=None, trials=12):
    """A valid partition of supp(x) (every row odd on at most one block), best of several
    randomized repairs from different starts. Its size is a LOWER bound for c(x)."""
    rws = rows if rws is None else rws
    rng = random.Random(x)
    starts = [[1 << i for i in range(x.bit_length()) if (x >> i) & 1],
              [f & x for f in FAMILIES], [bt & x for bt in BYTES]]
    best = None
    for t in range(trials):
        bl = repair(list(starts[t % 3]), rws, rng)
        if best is None or len(bl) > len(best):
            best = bl
    return best


def check_partition(x, blocks, rws=None):
    rws = rows if rws is None else rws
    if sum(blocks) != x or any(b == 0 for b in blocks):
        return False
    for r in rws:
        if sum(par(r & b) for b in blocks) > 1:
            return False
    return True


def part1():
    words = {}
    for k in range(1, 6):
        for S in itertools.combinations(range(32), k):
            z = sum(1 << i for i in S)
            w = k + wt(Mv(z))
            if w <= 6:
                words.setdefault(w, []).append(z)
    print("graph-code words of weight <= 6:", {w: len(v) for w, v in sorted(words.items())})
    worst = None
    for z in words.get(6, []):
        x = FULL ^ z
        bl = greedy_partition(x)
        assert check_partition(x, bl)
        c = len(bl)
        b = 64 - 6 - c
        if worst is None or b > worst[0]:
            worst = (b, hex(z), c)
    print("max over weight-6 words z of 64 - 6 - c_greedy(1+z):", worst, "-> single-point bound <= 56 everywhere"
          if worst[0] <= 56 else "-> NOT settled")
    bl = greedy_partition(FULL)
    print("c_greedy(all-ones) =", len(bl), "(F1 says c(1) = 8)")


def lp_value(points):
    from scipy.optimize import linprog
    k = len(points)
    classes = list(itertools.product((0, 1), repeat=k))
    A, b = [], []
    for a in itertools.product((0, 1), repeat=k):
        if not any(a):
            continue
        xa = 0
        for ai, xi in zip(a, points):
            if ai:
                xa ^= xi
        if xa == 0:
            continue
        L = wt(Mv(xa))
        c = len(greedy_partition(xa))
        D = wt(xa) - c
        dot = [sum(s * t for s, t in zip(sig, a)) & 1 for sig in classes]
        A.append([-1 if d else 0 for d in dot]); b.append(-L)
        A.append([0 if d else -1 for d in dot]); b.append(-D)
    res = linprog([1] * len(classes), A_ub=A, b_ub=b, bounds=[(0, None)] * len(classes), method="highs")
    return res.fun


def rand_point(dens):
    return sum(1 << i for i in range(32) if random.random() < dens) or 1


def part2(samples):
    # the record's four-inequality system vs the full six for x1 = all-ones
    print("two points with x1 = all-ones: full six-inequality LP over random x2")
    mx = 0
    for _ in range(samples):
        x2 = rand_point(random.choice([0.05, 0.3, 0.5, 0.7, 0.95]))
        if x2 == FULL:
            continue
        v = lp_value([FULL, x2])
        mx = max(mx, v)
    print("  max LP value (upper bound on the true LP optimum):", mx)
    for k in (2, 3):
        mx, arg = 0, None
        for _ in range(samples):
            pts = [rand_point(random.choice([0.3, 0.5, 0.7, 0.9, 0.97])) for _ in range(k)]
            if random.random() < 0.5:
                pts[0] = FULL
            v = lp_value(pts)
            if v > mx:
                mx, arg = v, [hex(p) for p in pts]
        print(f"  k = {k} random points: max LP value {mx} at {arg}")


if __name__ == "__main__":
    part1()
    part2(int(sys.argv[1]) if len(sys.argv) > 1 else 300)
