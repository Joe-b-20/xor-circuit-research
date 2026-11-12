"""Small checks of hand constructions used in the report (no search).

1. Four inputs: with the two helpers x1+x2 and x3+x4 every vector of weight >= 2 is a helper or
   the sum of two elements of {units, helpers}; hence L(B) <= m*(B) + 2 for every B on 4 inputs.
2. The bound d <= 2^r - r - 1 of the span lemma is attained: three mixers x_i + y_i and all
   their subset sums (r = 3, d = 4, w = 3).
3. Helper counts h = L - m* of the cyclic-system examples (L values from ../cyclic/REPORT.md,
   which were decided there; here only m* is computed and the explicit circuit of Example 1 is
   verified).
"""
from itertools import combinations
from ledger import ledger, masks


def check_four_inputs():
    units = [1 << i for i in range(4)]
    helpers = [0b0011, 0b1100]
    avail = units + helpers
    one_step = {a ^ b for a, b in combinations(avail, 2)} | set(helpers)
    targets = [v for v in range(1, 16) if bin(v).count("1") >= 2]
    missing = [v for v in targets if v not in one_step]
    print("1. four inputs: %d vectors of weight >= 2, not reachable in one step: %s"
          % (len(targets), missing))


def check_subset_sums():
    nX = nY = 3
    # inputs 0..2 = x, 3..5 = y; mixers m_i = x_i + y_i  (gates 6, 7, 8)
    gates = [(0, 3), (1, 4), (2, 5)]
    gates += [(6, 7), (6, 8), (7, 8)]          # gates 9, 10, 11: pair sums
    gates += [(9, 8)]                          # gate 12: triple sum
    L = ledger(nX, nY, gates)
    r = min(L["rX"], L["rY"])
    print("2. subset sums of 3 mixers: classes %s; d=%d w=%d r=%d bound 2^r-r-1=%d; floating=%d"
          % (L["cls"], L["d"], L["w"], r, 2 ** r - r - 1, L["floating"]))


def rows_to_masks(rows):
    out = []
    for s in rows:
        m = 0
        for i, ch in enumerate(s):
            if ch == "1":
                m |= 1 << i
        out.append(m)
    return out


def mstar(rows):
    return len({m for m in rows_to_masks(rows) if bin(m).count("1") >= 2})


def check_cyclic_examples():
    ex1 = ["11100", "11110", "11111", "01111", "00111", "11011"]
    # explicit 7-gate circuit: g1=x1+x2, g2=g1+x3, g3=g2+x4, g4=g3+x5, g5=g4+x1, g6=g5+x2, g7=g4+x3
    gates = [(0, 1), (5, 2), (6, 3), (7, 4), (8, 0), (9, 1), (8, 2)]
    sig = set(masks(5, gates))
    ok = all(m in sig for m in rows_to_masks(ex1))
    print("3. Example 1: 7-gate circuit computes all rows: %s; m* = %d, L = 7 -> h = %d"
          % (ok, mstar(ex1), 7 - mstar(ex1)))
    ex2A = ["100101", "111110", "100111", "110111", "011010", "011110"]
    print("   Example 2: A = B^-1: m* = %d, L = 8 (cyclic/REPORT.md) -> h = %d"
          % (mstar(ex2A), 8 - mstar(ex2A)))
    ex3B = ["0101010", "1110000", "1010001", "0110001", "1011000", "0001110", "0010011"]
    ex3A = ["1110101", "1101101", "0111000", "1001001", "0101111", "1100100", "1011101"]
    print("   Example 3: B: m* = %d, L <= 10 -> h <= %d;  A = B^-1: m* = %d, L = 11 -> h = %d"
          % (mstar(ex3B), 10 - mstar(ex3B), mstar(ex3A), 11 - mstar(ex3A)))


if __name__ == "__main__":
    check_four_inputs()
    check_subset_sums()
    check_cyclic_examples()
