#!/usr/bin/env python3
"""For each last-layer ('F') AND of a circuit: which tower-model GF(4)-norm member (gamma, lam, mu)
it equals modulo the circuit's own E = span(1, x, stage-L and stage-M ANDs).  Uses H2's tower model.
usage: members.py FILE"""
import sys, os
sys.path.insert(0, os.path.expanduser('~/xcr-boolflux/nonlinear/boolflux/strategies/H2'))
from h2lib import Basis
import a28parse as AP, tbuild as TB, tsearch as TS
from tower import m4, tau, W, MUL, INV16, norm

f = sys.argv[1]
_, ANDS = AP.load(f)
E = Basis()
for v in [AP.ONE] + AP.BITS + [A['out'] for A in ANDS if A['stage'] in 'LM']:
    E.add(v)
LRx = [TB.LR(x) for x in range(256)]
Dx = [norm(*lr) for lr in LRx]
lams = TS.all_lams(); mus = TS.all_mus()
lv = {lc: [TS.lam_val(lc, *LRx[x]) for x in range(256)] for lc in lams}
F = [(i, A) for i, A in enumerate(ANDS) if A['stage'] == 'F']
targets = {E.full_reduce(A['out'])[0]: i for i, A in F}
found = {}
for g in range(16):
    vx = [INV16[Dx[x]] ^ MUL[g][Dx[x]] for x in range(256)]
    for lc in lams:
        L = lv[lc]
        for mc in mus:
            mv = [TS.mu_val(mc, vx[x]) for x in range(256)]
            t = TB.T256(lambda x: (tau(L[x]) ^ tau(m4(W, mv[x]))) & (tau(m4(W, L[x])) ^ tau(mv[x])))
            r = E.full_reduce(t)[0]
            if r in targets:
                found.setdefault(targets[r], []).append((g, lc, mc))
stages = ''.join(A['stage'] for A in ANDS)
print(os.path.basename(f), 'stages', stages, 'F count', len(F))
for i, A in F:
    m = found.get(i)
    print('AND', i, 'member' if m else 'NON-MEMBER', sorted(set(g for g, _, _ in m)) if m else '')
