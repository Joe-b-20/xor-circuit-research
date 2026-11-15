"""12 members + 1 product (agent H1): over E = (stage 1 of file S) + (middle of file M) and
X = (last layer of file L) minus member i, if d(X) = 1, search EVERY single product l*m with l, m
in O (= span(1, x, N, n)) or O2 (= O + the middle's products) closing the missing dimension
(H2's fix1.search, exact Gray code + linear solve). A solution = 9 + 5 + 12 + 1 = 27 ANDs.
usage: python3 fix12.py S M L I [O|O2]"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'H2'))
sys.path.insert(0, str(HERE))
import a28parse as AP                      # H2 (read-only use)
from fix1 import search, dedupe_O          # H2 (read-only use)
import xag

S, M, L, i = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
which = sys.argv[5] if len(sys.argv) > 5 else 'O'


def roles(f):
    c, ands, outs, ot = xag.parse(f)
    return [(xag.role(A), A['tab']) for A in ands]


s1 = [t for r, t in roles(S) if r == 'S1']
mid = [t for r, t in roles(M) if r == 'MID']
last = [t for r, t in roles(L) if r not in ('S1', 'MID')]
X = last[:i] + last[i + 1:]
Obase = dedupe_O([AP.ONE] + AP.BITS + AP.Ntabs + AP.ntabs)
O = Obase if which == 'O' else dedupe_O(Obase + mid)
d, sols = search(s1 + mid + X, O, maxsol=10 ** 9, verbose=False)
cls = {}
for l, m, lt, mt in sols:
    xl = bool(l & 0x1fe); xm = bool(m & 0x1fe)
    key = ('x' if xl else '') + ('N' if l >> 9 else '') + '*' + ('x' if xm else '') + ('N' if m >> 9 else '')
    cls[key] = cls.get(key, 0) + 1
print('S=%s M=%s L=%s drop=%d O=%s(dim %d): missing dims %d, solutions %d %s' % (
    Path(S).name[9:24], Path(M).name[9:24], Path(L).name[9:24], i, which, len(O), d, len(sols), cls),
    flush=True)
if sols:
    print('SOLUTIONS (l-mask, m-mask over O):', [(hex(a), hex(b)) for a, b, _, _ in sols[:20]], flush=True)
