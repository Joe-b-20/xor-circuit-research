"""Probe: dual (Theorem C(iii)) of a minimum based cyclic system of Example 3's A, whose transpose has a unit row."""
import random, sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from audit_test import Based, min_cyclic_sets, random_bases, par, rank_f2, triples
from examples import is_cyclic, closure

def vec(s): return sum(1 << i for i, ch in enumerate(s) if ch == '1')
n = 7
A = [vec(s) for s in ['1110101', '1101101', '0111000', '1001001', '0101111', '1100100', '1011101']]
AT = [sum(((A[i] >> j) & 1) << i for i in range(n)) for j in range(n)]
kmin, sets = min_cyclic_sets(n, A)
print("A: kmin", kmin, "sets", sets)
rng = random.Random(3)
extras = sets[0][0]
S = sorted(set([1 << i for i in range(n)] + A + extras))
T = random_bases(S, n, 1, rng)[0]
C = Based(n, A, S, T)
C.validate()
u, o = C.adjoint()
print("o == columns of A:", o == AT)
print("D_v:", {v: C.D(v) for v in S})
# raw dual values: u_t, z_j, o_i
vals = u + [1 << j for j in range(n)] + o
print("number of variables u,z,o:", len(vals), " distinct:", len(set(vals)))
dup = [(i, o[i]) for i in range(n) if o[i] in set(1 << j for j in range(n))]
print("outputs o_i equal to an input z_j:", dup)
# distinct nonzero values of the whole dual (with canonical split new vars) -> cyclic set for A^T?
from audit_test import dual, Fail
try:
    Dd, origins, nd2 = dual(C, 'canonical', rng)
    print("dual ok", Dd.G)
except Fail as e:
    print("dual check failed:", e)
# rebuild value set by hand (including new variables of a simple chain split)
allv = set(vals)
for v in S:
    terms = [u[k] for k in C.memb[v]] + [1 << j for j, r in enumerate(A) if r == v] + ([o[v.bit_length() - 1]] if v in C.unitset else [])
    acc = 0
    for t in terms[:-2]:
        acc ^= t
        allv.add(acc)
allv.discard(0)
print("distinct nonzero dual values:", len(allv), " size = |S'| - 7 =", len(allv) - 7,
      " contains units:", all((1 << j) in allv for j in range(n)), " contains rows of A^T:", all(r in allv for r in AT))
print("is cyclic:", is_cyclic(allv, n), " L_cyc(A^T) claimed 10")
