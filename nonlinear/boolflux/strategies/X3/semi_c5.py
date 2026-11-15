"""X3 semi_c5.py: x^5-junk (C2 = A1 A2^4 + A1^4 A2) and x^3-, x^9-junk (C1, C3) of pairs of tensors in one T_b-coset:
does the x^5 part cancel in the pair?  (If it always cancelled, K-ratio products would not reach the x^5 dimensions.)"""
import os
from collections import Counter, defaultdict
from gfinv import gmul, gpow
D = os.path.expanduser('~/xs-campaigns/2026-11-15-study/X3/')
def C(a, b, d):
    return gmul(a, gpow(b, 1 << d, 8), 8) ^ gmul(gpow(a, 1 << d, 8), b, 8)
cos = defaultdict(list)
for ln in open(D + 'semi_members.tsv'):
    if ln[0] == '#': continue
    p = ln.rstrip('\n').split('\t'); cos[p[1]].append((int(p[3], 16), int(p[4], 16), p[7] + p[8]))
st = Counter()
for c, v in cos.items():
    for i in range(len(v)):
        for j in range(i + 1, len(v)):
            a, b = v[i], v[j]
            c2 = C(a[0], a[1], 2) ^ C(b[0], b[1], 2)
            st[(len(v), a[2], b[2], 'x5 cancels' if c2 == 0 else 'x5 stays')] += 1
for k, n in sorted(st.items()): print(k, n)
