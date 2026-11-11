"""Small verifications quoted in REPORT.md:  python3 checks.py

 (1) the pooled partitions with m + 1 blocks (singletons p_j with steps in {1,2}) are valid, m = 2..40;
 (2) the values with three boundary-triple representations for m = 5, in sheet language;
 (3) Q_2 is the double map D_T, T = P + P^2 on Z_4;
 (4) an 18-gate circuit for the run map F_2 (section 3.2) and the gates killed / dead when the
     last block is set to zero (exactly 8 killed, none dead: the elimination count is attained);
 (5) the restriction identities: Q_m with one block set to zero is the run map F_(m-1).
"""
import itertools
from collections import defaultdict

import qm
import run_sat


def pooled_labelling(m):
    """Steps p_(j+1) - p_j in {1,2} with total = 0 mod 4."""
    total = next(t for t in range(m, 2 * m + 1) if t % 4 == 0)
    twos = total - m
    steps = [2] * twos + [1] * (m - twos)
    p = [0]
    for st in steps[:-1]:
        p.append((p[-1] + st) % 4)
    assert (p[-1] + steps[-1]) % 4 == p[0]
    lab = {}
    for j in range(m):
        for c in range(4):
            lab[4 * j + c] = 0 if c == p[j] else 1 + j
    return lab, p


def valid(m, lab):
    for r in qm.rows(m):
        cnt = defaultdict(int)
        for i in range(4 * m):
            if (r >> i) & 1:
                cnt[lab[i]] += 1
        if sum(1 for v in cnt.values() if v & 1) != 1:
            return False
    return True


def check1():
    ok = all(valid(m, pooled_labelling(m)[0]) for m in range(2, 41))
    print("(1) pooled partitions with m+1 blocks valid for m = 2..40:", ok)


NAMES = {0b0011: "s0", 0b0110: "s1", 0b1100: "s2", 0b1001: "s3", 0b0101: "d0", 0b1010: "d1", 0b1111: "t",
         0b0001: "e0", 0b0010: "e1", 0b0100: "e2", 0b1000: "e3",
         0b1110: "E0", 0b1101: "E1", 0b1011: "E2", 0b0111: "E3"}


def desc(v, m):
    return " ".join(f"{j}:{NAMES[(v >> (4 * j)) & 15]}" for j in range(m) if (v >> (4 * j)) & 15)


def check2():
    m = 5
    n = 4 * m
    R = qm.rows(m)
    B = [(f"e{i % 4}({i // 4})", 1 << i) for i in range(n)] + [(f"o{i % 4}({i // 4})", R[i]) for i in range(n)]
    reps = defaultdict(list)
    for a, b, c in itertools.combinations(range(len(B)), 3):
        reps[B[a][1] ^ B[b][1] ^ B[c][1]].append((B[a][0], B[b][0], B[c][0]))
    full = {v: t for v, t in reps.items() if len(t) >= 3}
    print(f"(2) m = 5: {len(full)} values with three triple representations; those meeting blocks 1 and 2 only, sheet 2:")
    for v, t in sorted(full.items()):
        blocks = {j for j in range(m) if (v >> (4 * j)) & 15}
        if blocks == {1, 2}:
            print("     ", desc(v, m), "  =  " + "  =  ".join("+".join(x) for x in t))


def check3():
    R = qm.rows(2)
    # u_a = input (a+1, 0), v_a = input (a+3, 1), w_a = u_a + v_a; U_a = o(a,0), V_a = o(a+2,1)
    ok = True
    for a in range(4):
        u = qm.bit(a + 1, 0)
        v = qm.bit(a + 3, 1)
        w = lambda b: qm.bit(b + 1, 0) | qm.bit(b + 3, 1)
        Tw = w(a + 1) ^ w(a + 2)
        ok &= R[4 * 0 + a] == u ^ Tw
        ok &= R[4 * 1 + (a + 2) % 4] == v ^ Tw
    print("(3) Q_2 = double map D_T with T[a] = {a+1, a+2} (u_a = in(a+1,0), v_a = in(a+3,1)):", ok)


def check4():
    # blocks a = 0, b = 1; signals 0..3 = a0..a3, 4..7 = b0..b3
    a = lambda c: c % 4
    b = lambda c: 4 + c % 4
    g = []
    idx = {}

    def gate(name, x, y):
        g.append((x, y))
        idx[name] = 8 + len(g) - 1
        return idx[name]

    s2a = gate("s2a", a(2), a(3))
    d0a = gate("d0a", a(0), a(2))
    d1a = gate("d1a", a(1), a(3))
    gate("E0a", a(1), s2a)
    gate("E1a", a(0), s2a)
    gate("E2a", a(0), d1a)
    gate("E3a", a(1), d0a)
    s0b = gate("s0b", b(0), b(1))
    s1b = gate("s1b", b(1), b(2))
    s3b = gate("s3b", b(0), b(3))
    gate("s2b", b(2), b(3))
    g4 = gate("g4", b(2), s2a)          # (s2(a), e2(b))
    g5 = gate("g5", d0a, s0b)           # (d0(a), s0(b))
    g6 = gate("g6", s3b, g4)            # (s2(a), E1(b))
    gate("o3", g4, g5)                  # (s3(a), E3(b))
    o1 = gate("o1", d1a, g6)            # (s1(a), E1(b))
    gate("o2", s1b, g6)                 # (s2(a), E2(b))
    gate("o0", g5, o1)                  # (s0(a), E0(b))
    targets = run_sat.run_targets(2)
    ok = qm.computes(8, g, targets)
    vals = qm.masks(8, g)
    print(f"(4) 18-gate circuit computes F_2: {ok} ({len(g)} gates)")
    # zero block b: V-part = low nibble
    first = {}
    killed = []
    for name, s in idx.items():
        v = vals[s] & 15
        if v == 0 or qm.popcount(v) == 1 or v in first:
            killed.append(name)
        else:
            first[v] = name
    print("     killed when block b = 0 (zero, unit or repeated restriction):", killed, len(killed))
    rep = {vals[s] & 15: first.get(vals[s] & 15) for s in idx.values()}
    # dead gates of the restricted circuit: not needed for the outputs of F_1 on block a
    need = {t & 15 for t in targets if (t & 15) and qm.popcount(t & 15) > 1}
    need |= {m for m in [qm.s(c, 0) for c in range(4)]}
    live = set()
    order = list(idx.items())
    opmask = {name: (vals[g[s - 8][0]] & 15, vals[g[s - 8][1]] & 15) for name, s in order}
    stack = [first[v] for v in need if v in first]
    while stack:
        nm = stack.pop()
        if nm in live:
            continue
        live.add(nm)
        for v in opmask[nm]:
            if v in first:
                stack.append(first[v])
    dead = [nm for nm in first.values() if nm not in live]
    print("     surviving gates:", len(first), " of which dead for F_1:", dead)


def check5():
    ok = True
    for m in range(4, 9):
        R = qm.rows(m)
        keep = sum(15 << (4 * j) for j in range(m - 1))        # zero block m-1
        got = {r & keep for r in R} - {0}
        want = set(run_sat.run_targets(m - 1))
        ok &= got == want
    print("(5) Q_m with block m-1 set to zero has exactly the outputs of F_(m-1), m = 4..8:", ok)


def check6():
    """AES MixColumns (repository matrix, bit i = bit i%8 of byte i//8) equals Q_T for T = shift + (1,7),(3,7),(4,7)."""
    import os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "circuits", "aes-mixcolumns",
                        "aes-mixcolumns.mat.txt")
    tokens = " ".join(l.split("#")[0].split("%")[0] for l in open(path).read().splitlines()).split()
    nr, nc = int(tokens[1]), int(tokens[2])
    bits = list(map(int, tokens[3:3 + nr * nc]))
    T = qm.shift_T(8)
    for j in (1, 3, 4):
        T[j] ^= 1 << 7
    R = qm.rows_T(T)
    ok = True
    for c in range(4):
        for j in range(8):
            row = 8 * c + j                      # repository index of output (byte c, bit j)
            mask = 0
            for cc in range(4):
                for jj in range(8):
                    if bits[row * nc + 8 * cc + jj]:
                        mask |= qm.bit(cc, jj)
            ok &= mask == R[4 * j + c]
    print("(6) MixColumns = Q_T with T = shift + entries (1,7), (3,7), (4,7):", ok)


if __name__ == "__main__":
    check6()
    check1()
    check2()
    check3()
    check4()
    check5()
