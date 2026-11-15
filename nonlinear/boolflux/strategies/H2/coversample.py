"""Sample many distinct 9-product level-1 covers of V_N (span of N = x^17 coordinates) with track C's
exact SAT encoding (strategies/C/stage1.py, c free, lex order), incrementally blocking each found
operand assignment; deduplicate by span mod affine.  Optional: product 0 fixed to an orbit
representative (--rep i) for diversity.
usage: coversample.py OUT.json COUNT [--rep i] [--seconds S]
Each cover = list of 9 (lmask, mmask) with bit a = coefficient of input U_a."""
import sys, os, json, time, argparse
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'C'))
import stage1, qmc
from pysat.solvers import Solver
from h2lib import Basis
import a28parse as AP

ap = argparse.ArgumentParser()
ap.add_argument('out'); ap.add_argument('count', type=int)
ap.add_argument('--rep', type=int, default=-1); ap.add_argument('--seconds', type=float, default=3600)
a = ap.parse_args()
R1 = None
if a.rep >= 0:
    reps = stage1.orbit_reps(); la, lb, _ = reps[a.rep]; R1 = (la, lb)
f = stage1.encode(9, R1)
Lv = [list(range(1 + 8 * j, 9 + 8 * j)) for j in range(9)]
Mv = [list(range(73 + 8 * j, 81 + 8 * j)) for j in range(9)]
U = AP.XT
aff = Basis()
for v in [AP.ONE] + AP.BITS: aff.add(v)
def lin(mask):
    t = 0
    for b in range(8):
        if mask >> b & 1: t ^= U[b]
    return t
covers = []; keys = set(); t0 = time.time(); nsol = 0
with Solver(name='cadical153', bootstrap_with=f.cl) as S:
    while len(covers) < a.count and time.time() - t0 < a.seconds:
        if not S.solve(): break
        nsol += 1
        model = set(x for x in S.get_model() if x > 0)
        prods = []
        block = []
        for j in range(9):
            lm = sum(1 << b for b in range(8) if Lv[j][b] in model)
            mm = sum(1 << b for b in range(8) if Mv[j][b] in model)
            prods.append((lm, mm))
            block += [-v if v in model else v for v in Lv[j] + Mv[j]]
        S.add_clause(block)
        E = Basis()
        for lm, mm in prods: E.add(aff.full_reduce(lin(lm) & lin(mm))[0])
        vs = [r[0] for r in E.rows.values()]
        piv = [v.bit_length() - 1 for v in vs]
        for i in range(len(vs)):
            for j in range(len(vs)):
                if i != j and (vs[j] >> piv[i]) & 1: vs[j] ^= vs[i]
        k = tuple(sorted(vs))
        if k in keys: continue
        keys.add(k); covers.append(prods)
        print('cover', len(covers), 'sat-solutions', nsol, 'time %.0f' % (time.time() - t0), flush=True)
        json.dump(covers, open(a.out, 'w'))
print('done covers', len(covers), 'solutions', nsol)
