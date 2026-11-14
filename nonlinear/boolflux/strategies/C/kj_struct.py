"""Structured k+J search: members restricted to z = zeta*Y in a fixed subspace Z of F
(NOTES.md section 9), so the n-block kernel is automatic. Outer loop over Z (the A28 Z first,
then random Z of the given dims), inner simulated annealing on S inside the pool.
Grade-0 residue is hard (5-AND inversion of the AD5 file). Every visited set with cost <= 18 and
k <= 13 and zero kernel junk is tested for a level-1 cover with l = 27 - 5 - k products
(cover_enum, exact for l - 4 - J <= 2); hits are written to --hits.

usage: python3 kj_struct.py --dims 5,4 --zs 50 --iters 20000 --seed 1 --log-sets FILE --hits FILE
"""
from __future__ import annotations

import argparse
import json
import math
import random
import time

import gf
import cover_enum
import wsat
from fam_check import gp
from kj_search import Model, AD5
from structure import analyse

MU5 = [gp(51 * i) for i in range(5)]
CUBE_ROOT = {}
for e in range(0, 255, 17):
    s = gp(e); CUBE_ROOT.setdefault(gf.power(s, 3), s)


def zspan(basis):
    out = [0]
    for b in basis: out += [v ^ b for v in out]
    return [v for v in out if v]


def a28_Z():
    c, ands, outs, tt = analyse(AD5)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dims', default='5,4')
    ap.add_argument('--zs', type=int, default=50)
    ap.add_argument('--iters', type=int, default=20000)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--temp', type=float, default=0.5)
    ap.add_argument('--gamma', default='17')
    ap.add_argument('--log-sets', default=None)
    ap.add_argument('--hits', default=None)
    ap.add_argument('--a28first', action='store_true')
    a = ap.parse_args()
    rnd = random.Random(a.seed)
    M = Model(gp(int(a.gamma)) if a.gamma != 'none' else None, 'hard')
    Nf = wsat.n_forms()
    qsp = wsat.quad_form_coords(M)
    tested = set()
    t0 = time.time()
    dims = [int(x) for x in a.dims.split(',')]
    a28z = [gp(e) for e in (155, 140, 173, 209, 248)]   # A28 z-values (span dim 5)
    for zi in range(a.zs):
        if zi == 0 and a.a28first:
            Zb = a28z
        else:
            r = rnd.choice(dims)
            while True:
                Zb = [rnd.randrange(1, 256) for _ in range(r)]
                if gf.Span(Zb).dim() == r: break
        Zall = zspan(Zb)
        pool = []
        for z in Zall:
            for zeta in MU5:
                s = CUBE_ROOT[zeta]
                Y = gf.mul(gf.INV[zeta], z); A = gf.mul(Y, gf.INV[s])
                tab = wsat.member_table(M, A, s)
                pool.append(((A, s), M.hard.nf(tab), M.soft.nf(tab), tab))

        def ev(S):
            ok, J, d = M.cost([pool[i][1] for i in S], [pool[i][2] for i in S])
            return ((len(S) + J) if ok else (len(S) + 8 + 3 * d)), ok, J

        S = rnd.sample(range(len(pool)), min(len(pool), 13))
        cur, _, _ = ev(S); best = cur
        for it in range(a.iters):
            T = list(S); mv = rnd.random()
            if mv < 0.3 and len(T) > 9: T.pop(rnd.randrange(len(T)))
            elif mv < 0.55: T.append(rnd.randrange(len(pool)))
            else: T[rnd.randrange(len(T))] = rnd.randrange(len(pool))
            if len(set(T)) < len(T): continue
            c, ok, J = ev(T)
            if c <= cur or rnd.random() < math.exp(-(c - cur) / a.temp):
                S, cur = T, c
                best = min(best, c)
                if ok and c <= 18 and len(T) <= 13:
                    key = (tuple(Zb), tuple(sorted(T)))
                    if key in tested: continue
                    tested.add(key)
                    tabs = [pool[i][3] for i in T]
                    okr, res, kj, _ = wsat.residuals(M, tabs)
                    rec = {'k': len(T), 'J': J, 'cost': c, 'kernel': len(kj),
                           'members': [pool[i][0] for i in sorted(T)], 'Z': Zb}
                    if not kj:
                        rho = wsat.to_forms(qsp, res)
                        U = []
                        sp = gf.Span()
                        for v in Nf + rho:
                            if sp.add(v): U.append(v)
                        l = 27 - 5 - len(T)
                        if l - len(U) <= 2:
                            info, found = cover_enum.run(U, l)
                            rec['cover'] = {'l': l, 'd': len(U), 'found': info['found'],
                                            'max_bucket': info['max_bucket'][:3], 'skipped': info.get('skipped', False)}
                            if info['found'] and a.hits:
                                with open(a.hits, 'a') as fh:
                                    fh.write(json.dumps(rec) + '\n')
                    if a.log_sets:
                        with open(a.log_sets, 'a') as fh:
                            fh.write(json.dumps(rec) + '\n')
        print(json.dumps({'event': 'Z', 'zi': zi, 'dimZ': len(Zb), 'pool': len(pool),
                          'best': best, 'tested': len(tested),
                          'secs': round(time.time() - t0, 1)}), flush=True)


if __name__ == '__main__':
    main()
