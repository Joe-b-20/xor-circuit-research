"""Driver: random 'clean' n x n matrices (every row and column of odd weight >= 3, rows distinct, columns
distinct); for X and X^T enumerate ALL minimum cyclic sets (exhaustive, ./lmin), take random bases of
triples, and run the order-free lemma checks of audit_test.py on each minimum based system."""
import sys, random, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_test import Based, min_cyclic_sets, random_bases, test_system, orbit, Fail, peel_and_W
n = int(sys.argv[1]); count = int(sys.argv[2]); per = int(sys.argv[3]); seed = int(sys.argv[4])
rng = random.Random(seed)
def transpose(A):
    return [sum(((A[i] >> j) & 1) << i for i in range(n)) for j in range(n)]
def clean(X):
    if len(set(X)) < n or len(set(transpose(X))) < n: return False
    return all(bin(r).count('1') % 2 == 1 and bin(r).count('1') >= 3 for r in X + transpose(X))
counters = dict(systems=0, duals=0, double_duals=0, noncircuit_bases=0, deg2_stars=0)
done = 0; noncirc_sets = 0; tried = 0
while done < count:
    X = [rng.randrange(1, 1 << n) for _ in range(n)]
    if not clean(X): continue
    tried += 1
    for name, R in [('X', X), ('X^T', transpose(X))]:
        kmin, sets = min_cyclic_sets(n, R)
        if kmin is None: break
        noncirc_sets += sum(1 for _, kd in sets if kd == 'noncirc')
        pick = [s for s in sets if s[1] == 'noncirc'][:10]
        if not pick and len(sys.argv) > 5: break
        pick += rng.sample(sets, min(3, len(sets)))
        for extras, kind in pick:
            S = sorted(set([1 << i for i in range(n)] + R + extras))
            for T in random_bases(S, n, per, rng):
                C = Based(n, R, S, T)
                try:
                    test_system(C, rng, counters)
                    orbit(C, rng, counters=counters)
                except Fail as e:
                    print("FAIL", name, R, extras, T, e, flush=True); raise
        print(name, R, "L_cyc =", len(set(R)) + kmin, "min sets:", len(sets), flush=True)
    else:
        done += 1
print("matrices:", done, "non-circuit minimum SETS met:", noncirc_sets, counters)
