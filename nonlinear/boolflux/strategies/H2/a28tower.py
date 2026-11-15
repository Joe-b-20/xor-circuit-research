"""Identify the last-layer ANDs of a published A28 file as tower-model members (lam, mu) for
v = Q + gamma' D, then check the relaxed-model cover with free = file's level-1 products."""
import sys, pickle, os, itertools
from h2lib import Basis
import a28parse as AP, tbuild as TB, tsearch as TS
from tower import m4, tau, W, MUL, INV16, norm, tab, VAR, ONE

f = sys.argv[1]; gam = int(sys.argv[2])
_, ANDS = AP.load(f)
E = Basis()
for v in [AP.ONE] + AP.BITS + [A['out'] for A in ANDS if A['stage'] in 'LM']: E.add(v)
LRx = [TB.LR(x) for x in range(256)]
Dx = [norm(*lr) for lr in LRx]
vx = [INV16[Dx[x]] ^ MUL[gam][Dx[x]] for x in range(256)]
real = {}
for lc in TS.all_lams():
    for mc in TS.all_mus():
        t = TB.T256(lambda x: (tau(TS.lam_val(lc, *LRx[x])) ^ tau(m4(W, TS.mu_val(mc, vx[x])))) &
                    (tau(m4(W, TS.lam_val(lc, *LRx[x]))) ^ tau(TS.mu_val(mc, vx[x]))))
        real.setdefault(E.full_reduce(t)[0], (lc, mc))
mem = []
for A in ANDS:
    if A['stage'] != 'F': continue
    r = E.full_reduce(A['out'])[0]
    mem.append(real.get(r))
print('identified members:', sum(1 for m in mem if m), 'of', len(mem))
print(mem)
if all(mem):
    inv = {lr: x for x, lr in enumerate(LRx)}
    free = [ONE] + VAR + TS.allowed_vquads(gam)
    for A in ANDS:
        if A['stage'] == 'L':
            o = A['out']; free.append(tab(lambda L, R, v, o=o: (o >> inv[(L, R)]) & 1))
    FB = Basis()
    for v in free: FB.add(v)
    for lc, mc in mem: FB.add(TS.member_table(lc, mc))
    print('targets covered in relaxed tower model:', all(FB.contains(t) for t in TS.targets(gam)))
