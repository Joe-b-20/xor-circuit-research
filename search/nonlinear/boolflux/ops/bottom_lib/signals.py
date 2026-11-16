"""Signal helpers for the bottom library: simulation, ANF, quadratic parts, levels (gate and AND) of every signal."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core  # noqa: E402

NB = 256
ONES = (1 << NB) - 1
VAR = [sum(1 << x for x in range(NB) if (x >> i) & 1) for i in range(8)]   # x_i (bit i of input)


def load(f):
    return core.read_ncff(f) if f.endswith('.txt') else core.from_kernel(open(f).read())


def sim(c):
    """tables, gate levels, AND levels for every signal (inputs first)."""
    n = c.n
    T = list(VAR[:n]); lg = [0] * n; la = [0] * n
    for op, a, b in c.gates:
        T.append(core.op_apply(op, T[a], T[b], ONES))
        lg.append(1 + max(lg[a], lg[b]))
        la.append((1 if op in core.NONLINEAR_OPS else 0) + max(la[a], la[b]))
    return T, lg, la


def anf(t):
    """ANF coefficients as a 256-bit int (bit m = monomial with variable set m)."""
    a = [(t >> x) & 1 for x in range(NB)]
    for i in range(8):
        s = 1 << i
        for x in range(NB):
            if x & s: a[x] ^= a[x ^ s]
    return sum(1 << m for m in range(NB) if a[m])


def deg(t):
    A = anf(t)
    return max((bin(m).count('1') for m in range(NB) if (A >> m) & 1), default=-1)


PAIRS = [(i, j) for i in range(8) for j in range(i + 1, 8)]
PIDX = {p: k for k, p in enumerate(PAIRS)}


def quad(t):
    """28-bit quadratic part (bit k = monomial x_i x_j, PAIRS[k])."""
    A = anf(t)
    return sum(1 << k for k, (i, j) in enumerate(PAIRS) if (A >> ((1 << i) | (1 << j))) & 1)


def lin_table(mask):
    """table of the linear form sum_{i in mask} x_i."""
    t = 0
    for i in range(8):
        if (mask >> i) & 1: t ^= VAR[i]
    return t


def wedge(l, m):
    """quadratic part of l(x) * m(x) for linear masks l, m (28-bit)."""
    w = 0
    for i in range(8):
        if not (l >> i) & 1: continue
        for j in range(8):
            if not (m >> j) & 1 or i == j: continue
            k = PIDX[(min(i, j), max(i, j))]
            w ^= 1 << k
    # each unordered pair counted from (i in l, j in m) and (j in l, i in m)
    return w


def wedge2(l, m):
    w = 0
    for i in range(8):
        for j in range(8):
            if i != j and (l >> i) & 1 and (m >> j) & 1:
                w ^= 1 << PIDX[(min(i, j), max(i, j))]
    return w
