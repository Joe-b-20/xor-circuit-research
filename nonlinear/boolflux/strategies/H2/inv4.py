"""Is a level-1 span invariant under x -> w x (w in GF(4)*)?  (then gamma ~ w gamma)."""
import sys
from h2lib import Basis, gmul, gpow
import a28parse as AP
w = gpow(3, 85)
def comp(t):  # t(w x)
    return sum(1 << x for x in range(256) if (t >> gmul(w, x)) & 1)
for f in sys.argv[1:]:
    _, A = AP.load(f)
    L = [a['out'] for a in A if a['stage'] == 'L']
    B = Basis()
    for v in [AP.ONE] + AP.BITS + L: B.add(v)
    print(f.split('/')[-1][:40], len(L), 'invariant:', all(B.contains(comp(t)) for t in L))
