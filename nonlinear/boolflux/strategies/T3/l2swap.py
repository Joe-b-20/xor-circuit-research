#!/usr/bin/env python3
"""T3: level-2 product exchange with structured operands.
For each level-2 AND P_i, a' ranges over all functions c + l(N) + s(x) (c const, l in the 4-dim N-span,
s x-linear: 2 * 16 * 256 = 8192), and b' over S1 = span{1, signals of AND level <= 1}. Necessary and
sufficient for keeping every needed level-<=2 function (Q's and the 8-dim V-space; drop2.py shows the
needed span mod W_i is <P_i> for every i): a'b' = P_i mod W_i, W_i = S1 + other level-2 ANDs. For fixed
a' linear in b'. Counts the solutions with b' also of the form c + l(N) + s(x) (cheap operands) and
lists them. [C] for this operand form.
    python3 l2swap.py CIRCUIT [--out OUT.json]"""
import argparse
import json
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core                                              # noqa: E402
from boolflux.hub.common import load, metrics, ONES, _gpow, _bit_tables  # noqa: E402
from pairs import and_levels, Basis                                    # noqa: E402
from prodswap import RBasis, gauss_solve, comb                         # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument('circuit'); ap.add_argument('--out')
a = ap.parse_args()
c = load(a.circuit); n = c.n; t = c.tables(); al = and_levels(c); NS = n + len(c.gates)
X = core.input_tables(8)
Nb = Basis([v for v in _bit_tables(lambda x: _gpow(x, 17)) if v not in (0, ONES)]).gens
S1 = Basis([ONES] + [t[s] for s in range(NS) if al[s] <= 1]); sg = S1.gens
A2 = [g for g in range(n, NS) if c.gates[g - n][0] == 8 and al[g] == 2]


def forms():
    out = []
    for k in range(16):
        l = 0
        for j in range(4):
            if (k >> j) & 1: l ^= Nb[j]
        for m in range(256):
            s = 0
            for i in range(8):
                if (m >> i) & 1: s ^= X[i]
            out.append(l ^ s)          # constant handled by complement (a' and 1+a' give a'b' and b'+a'b')
    return out


F = forms()
Fset = set(F) | {f ^ ONES for f in F}
res = {}
for g in A2:
    W = RBasis(sg + [t[h] for h in A2 if h != g])
    Pr, _ = W.reduce(t[g])
    sols = []
    for av in F:
        if av in (0,): continue
        cols = [W.reduce(av & s)[0] for s in sg]
        r = gauss_solve(cols, Pr)
        if r is None: continue
        part, null = r
        # enumerate b' (dim small?) and keep structured ones
        if len(null) > 14:
            sols.append((av, 'dim%d' % len(null))); continue
        for k in range(1 << len(null)):
            m = part
            for q, v in enumerate(null):
                if (k >> q) & 1: m ^= v
            bv = comb(sg, m)
            if bv in Fset:
                sols.append((av, bv))
    op, x, y = c.gates[g - n]
    triv = {t[x], t[y], t[x] ^ t[y], t[x] ^ ONES, t[y] ^ ONES, t[x] ^ t[y] ^ ONES}
    nontriv = [s for s in sols if s[0] not in triv]
    print('s%d: a-candidates with a structured b: %d (non-trivial a: %d)' % (g, len(sols), len(nontriv)), flush=True)
    res[g] = [(hex(s[0])[:12], str(s[1])[:12]) for s in nontriv[:20]]
if a.out: Path(a.out).write_text(json.dumps(res))
