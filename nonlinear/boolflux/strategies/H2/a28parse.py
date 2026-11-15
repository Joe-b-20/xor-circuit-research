"""Parse published circuits into (AND operand tables, stage classification) over the 256 inputs.

Conventions as core.py: point p = input byte x (U_i = bit 7-i), tables are 256-bit ints.
Stages: 'L' (operands affine in x), 'M' (operands functions of N = x^17, not affine in x),
'F' (the rest).
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core
from h2lib import Basis, gpow, INV, SBOX

ONE = (1 << 256) - 1
XT = core.input_tables(8)            # U0..U7 tables (U_i = bit 7-i of x)
BITS = [XT[7 - i] for i in range(8)]  # BITS[i] = bit i of x
NVAL = [gpow(x, 17) for x in range(256)]
nVAL = [INV[v] for v in NVAL]


def tab(f):
    t = 0
    for x in range(256):
        if f(x) & 1: t |= 1 << x
    return t


Ntabs = [tab(lambda x, i=i: NVAL[x] >> i) for i in range(8)]   # coords of N in poly basis (8 bits, span 4)
ntabs = [tab(lambda x, i=i: nVAL[x] >> i) for i in range(8)]
INVtabs = [tab(lambda x, i=i: INV[x] >> i) for i in range(8)]
Stabs = [tab(lambda x, i=i: SBOX[x] >> (7 - i)) for i in range(8)]   # S0..S7 msb first


def span_basis(vs):
    B = Basis()
    for v in vs: B.add(v)
    return B


AFF_X = span_basis([ONE] + BITS)
SUBK = sorted(set(NVAL))


def is_fun_of_N(t):
    seen = {}
    for x in range(256):
        k = NVAL[x]; b = (t >> x) & 1
        if seen.setdefault(k, b) != b: return False
    return True


def load(path):
    c = core.read_ncff(path)
    vals = c.tables()
    ands = []
    lev = [0] * c.n
    for j, (op, a, b) in enumerate(c.gates):
        s = c.n + j
        la = max(lev[a], lev[b])
        if op == 8:
            lev.append(la + 1)
            ands.append({'sig': s, 'a': vals[a], 'b': vals[b], 'out': vals[s], 'level': la + 1})
        else:
            lev.append(la)
    for A in ands:
        if AFF_X.contains(A['a']) or AFF_X.contains(A['a'] ^ ONE):
            if AFF_X.contains(A['b']) or AFF_X.contains(A['b'] ^ ONE):
                A['stage'] = 'L'; continue
        if is_fun_of_N(A['a']) and is_fun_of_N(A['b']):
            A['stage'] = 'M'; continue
        A['stage'] = 'F'
    return c, ands


if __name__ == '__main__':
    for f in sys.argv[1:]:
        c, ands = load(f)
        print(Path(f).name, 'ANDs', len(ands), ''.join(A['stage'] for A in ands),
              [A['level'] for A in ands])
