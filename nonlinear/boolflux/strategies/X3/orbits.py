"""X3: orbit representatives of 2-dim spaces of linear forms on GF(2^n) under x -> a x and Frobenius
(the symmetries of inversion that act linearly on inputs AND outputs).  Prints 'a b size' (bit masks of forms)."""
import sys
from gfinv import gmul
n = int(sys.argv[1]); N = 1 << n
def mat(f):   # columns: images of basis vectors
    return [f(1 << j) for j in range(n)]
def form_image(u, cols):   # form u(x)=parity(u&x); (u o M)(e_j) = parity(u & cols[j])
    return sum((bin(u & cols[j]).count('1') & 1) << j for j in range(n))
gens = [mat(lambda x: gmul(x, 2, n)), mat(lambda x: gmul(x, x, n))]
seen = {}; reps = []
for a in range(1, N):
    for b in range(a + 1, N):
        if (a ^ b) < b: continue
        S = frozenset((a, b, a ^ b))
        if S in seen: continue
        orb = {S}; st = [S]
        while st:
            s = st.pop()
            for g in gens:
                t = frozenset(form_image(u, g) for u in s)
                if t not in orb: orb.add(t); st.append(t)
        for s in orb: seen[s] = 1
        reps.append((a, b, len(orb)))
for r in reps: print(*r)
