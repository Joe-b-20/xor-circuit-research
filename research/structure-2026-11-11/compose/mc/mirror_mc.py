"""CHECK (not a proof): mirror of a MixColumns circuit, split at arc cuts of the 8 sheet-groups.

Mirror bit 4*j + c = primal output (c, j) (group j = sheet j). Mirror row of primal input (c, k)
= column (c, k) of the matrix; in groups: R^k_c = E_c(w^k) + p_c(w^(k+1)) for k < 7 and
R^7_c = E_c(w^7) + p_c(w^0) + p_c(w^1) + p_c(w^3) + p_c(w^4), p_c = u_(c-1) + u_c (verified below).
Transposition: each primal node with fan-out F becomes F - 1 mirror gates (summation order fwd/rev).
Reduced mirror = drop zero values and repeated values (first occurrence kept).
Classification at an arc S (omega = part on S), as compose/ring/ring_cuts.py:
 first (new omega), entry (exactly one operand with omega 0; label = that operand's value),
 h (other duplicate), ordinary far (both operands omega 0), exit (omega 0, operands omega != 0).
"""
import os
import sys
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "rotation", "mc"))
import mc  # noqa: E402

WIN = [frozenset([k, k + 1]) for k in range(7)] + [frozenset([7, 0, 1, 3, 4])]
NAMES = {0b0011: "s0", 0b0110: "s1", 0b1100: "s2", 0b1001: "s3", 0b0101: "d0", 0b1010: "d1", 0b1111: "t",
         0b0001: "e0", 0b0010: "e1", 0b0100: "e2", 0b1000: "e3",
         0b1110: "E0", 0b1101: "E1", 0b1011: "E2", 0b0111: "E3"}


def gnib(v, j):
    return (v >> (4 * j)) & 15


def groups(v):
    return frozenset(j for j in range(8) if gnib(v, j))


def desc(v):
    return " ".join("%d:%s" % (j, NAMES[gnib(v, j)]) for j in range(8) if gnib(v, j)) or "0"


def mirror_rows():
    rows = {}
    for c in range(4):
        for k in range(8):
            i = 8 * c + k
            r = 0
            for cc in range(4):
                for j in range(8):
                    if (mc.TARGETS[8 * cc + j] >> i) & 1:
                        r |= 1 << (4 * j + cc)
            rows[(c, k)] = r
    return rows


ROWS = mirror_rows()


def _check_rows():
    def E(c):
        return 15 ^ (1 << c)

    def p(c):
        return (1 << ((c - 1) % 4)) | (1 << c)
    for c in range(4):
        for k in range(8):
            want = E(c) << (4 * k)
            nbrs = [k + 1] if k < 7 else [0, 1, 3, 4]
            for j in nbrs:
                want ^= p(c) << (4 * j)
            assert ROWS[(c, k)] == want, (c, k)


_check_rows()


def mirror(gates, order="fwd"):
    n = 32
    vals = [1 << i for i in range(n)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    outg = {}
    for c in range(4):
        for j in range(8):
            outg[(c, j)] = min(i for i in range(n, len(vals)) if vals[i] == mc.TARGETS[8 * c + j])
    readers = {}
    for gi, (a, b) in enumerate(gates):
        for o in (a, b):
            readers.setdefault(o, []).append(n + gi)
    term = {}
    for (c, j), g in outg.items():
        term.setdefault(g, []).append(4 * j + c)
    Tm = [1 << i for i in range(n)]
    Tops = [None] * n
    origin = [None] * n
    adj = {}
    for v in reversed(range(len(vals))):
        idxs = list(term.get(v, [])) + [adj[r] for r in readers.get(v, [])]
        if not idxs:
            adj[v] = None
            continue
        idxs = [x for x in idxs if x is not None]
        if order == "rev":
            idxs = idxs[::-1]
        acc = idxs[0]
        for x in idxs[1:]:
            Tm.append(Tm[acc] ^ Tm[x])
            Tops.append((acc, x))
            origin.append(v)
            acc = len(Tm) - 1
        adj[v] = acc
    for c in range(4):
        for k in range(8):
            assert Tm[adj[8 * c + k]] == ROWS[(c, k)]
    seen = set(1 << i for i in range(n))
    red = []
    for i in range(n, len(Tm)):
        v = Tm[i]
        if v == 0 or v in seen:
            continue
        seen.add(v)
        red.append(dict(v=v, a=Tm[Tops[i][0]], b=Tm[Tops[i][1]], prim=origin[i]))
    return len(Tm) - n, red, vals


def required_near(S):
    """Required rows meeting S and S^c (their omega and s parts)."""
    low = sum(15 << (4 * j) for j in S)
    out = []
    for (c, k), r in ROWS.items():
        if r & low and r & ~low:
            out.append(((c, k), r & low, r & ~low))
    return out


def rank(vs):
    basis = []
    for v in vs:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
    return len(basis)


def honest(labels, v, tmax=6):
    lab = sorted(set(labels))
    for t in range(1, min(len(lab), tmax) + 1):
        for cmb in combinations(lab, t):
            x = 0
            for y in cmb:
                x ^= y
            if x == v:
                return t
    return None


def split(red, S):
    low = sum(15 << (4 * j) for j in S)
    first = set(1 << (4 * j + i) for j in S for i in range(4))
    st = dict(f=0, e=0, h=0, N=0)
    labels, exits, kinds = [], [], []
    for idx, g in enumerate(red):
        om, oa, ob = g["v"] & low, g["a"] & low, g["b"] & low
        if om == 0:
            if oa:
                exits.append((idx, g))
                kinds.append("x")
            else:
                st["N"] += 1
                kinds.append("N")
        elif om in first:
            if (oa == 0) != (ob == 0):
                st["e"] += 1
                labels.append((idx, g["a"] if oa == 0 else g["b"]))
                kinds.append("e")
            else:
                st["h"] += 1
                kinds.append("h")
        else:
            first.add(om)
            st["f"] += 1
            kinds.append("f")
    st["x"] = len(exits)
    st["near"] = st["f"] + st["h"]
    st["far"] = st["N"] + st["x"] + st["e"]
    st["rank"] = rank([x for _, x in labels])
    return st, labels, exits, kinds


def main():
    path = sys.argv[1]
    order = sys.argv[2] if len(sys.argv) > 2 else "fwd"
    gates = mc.parse_ncff(path)
    tot, red, _ = mirror(gates, order)
    print("%s order=%s: primal %d mirror %d reduced %d" % (os.path.basename(path), order, len(gates), tot, len(red)))
    outside = [g for g in red if not any(groups(g["v"]) <= w for w in WIN)]
    print("reduced mirror gates in no row window: %d %s" % (len(outside), [desc(g["v"]) for g in outside][:6]))
    for r in (1, 2, 3):
        for k in range(8):
            S = [(k + t) % 8 for t in range(r)]
            st, labels, exits, _ = split(red, S)
            print("arc %s: f %(f)d e %(e)d h %(h)d N %(N)d x %(x)d | near %(near)d far %(far)d rank %(rank)d" % st
                  % () if False else "arc %s: f %d e %d h %d N %d x %d | near %d far %d rank %d" % (
                      S, st["f"], st["e"], st["h"], st["N"], st["x"], st["near"], st["far"], st["rank"]))
            for idx, g in exits:
                lab = [x for i, x in labels if i < idx]
                inwin = [k2 for k2, w in enumerate(WIN) if groups(g["v"]) <= w]
                print("    exit [%s] groups %s in-window %s honest %s prim g%s" % (
                    desc(g["v"]), sorted(groups(g["v"])), inwin, honest(lab, g["v"]), g["prim"]))


if __name__ == "__main__":
    main()
