r"""Exact few-product completion (agent H1). E = stage 1 of S + middle of M (+ optional extra files'
products), X = last layer of L minus the members listed in --drop. With d = dim(T + E + X) -
dim(E + X) in {1, 2}, search EVERY product p = l*m, l, m in O (O = span(1, x, N, n), or O2 = O +
middle products) whose projection pi(p) modulo E + X lies in T-bar = pi(T) \ 0. A layer
X + (d products) works iff the reachable pi-values span T-bar, because with exactly d new products
each must project into T-bar (NOTES 8). Gray code over l in chunks [A, B) of 2^dim(O).
Semi-members (X3) can never be such products: their tensor has nonzero class-15/111 parts, which
nothing else in the circuit can cancel (NOTES 8 [P]); the search is over ALL products anyway.
usage: python3 fixk.py --S F --M F --L F --drop i,j --O O|O2 --chunk A:B [--out FILE]"""
import argparse
import json
import sys
import time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'C'))
sys.path.insert(0, str(HERE))
import gf                      # noqa: E402
import qmc                     # noqa: E402
import xag                     # noqa: E402


def roles(f):
    c, ands, outs, ot = xag.parse(f)
    return [(xag.role(A), A['tab']) for A in ands], ot


def basis(vs):
    S = gf.Span(); out = []
    for v in vs:
        if S.add(v): out.append(v)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--S'); ap.add_argument('--M'); ap.add_argument('--L')
    ap.add_argument('--drop', default=''); ap.add_argument('--O', default='O')
    ap.add_argument('--chunk', default='0:0'); ap.add_argument('--out', default=None)
    a = ap.parse_args()
    t0 = time.time()
    rS, T = roles(a.S); rM, _ = roles(a.M); rL, _ = roles(a.L)
    s1 = [t for r, t in rS if r == 'S1']; mid = [t for r, t in rM if r == 'MID']
    last = [t for r, t in rL if r not in ('S1', 'MID')]
    drop = {int(i) for i in a.drop.split(',') if i != ''}
    X = [t for i, t in enumerate(last) if i not in drop]
    EX = qmc.Normal([gf.ONES] + list(gf.X) + s1 + mid + X)
    Tb = basis([EX.nf(t) for t in T])
    d = len(Tb)
    if a.O == 'OV':                   # aff(x) + all functions of N (X3's operand model)
        O = basis([gf.ONES] + list(gf.X) + xag.V0)
    else:
        O = basis([gf.ONES] + list(gf.X) + xag.NC + xag.nC + (mid if a.O == 'O2' else []))
    k = len(O)
    A0, B0 = map(int, a.chunk.split(':'))
    if B0 == 0: B0 = 1 << k
    rec = {'S': Path(a.S).name[9:30], 'M': Path(a.M).name[9:30], 'L': Path(a.L).name[9:30],
           'drop': sorted(drop), 'O': a.O, 'dimO': k, 'd': d, 'chunk': [A0, B0]}
    if d == 0 or d > 2:
        rec['note'] = 'd not in {1,2}'; print(json.dumps(rec)); return
    R = [[EX.nf(O[i] & O[j]) for j in range(k)] for i in range(k)]
    # T-bar elements and a fixed echelon of T-bar for membership
    tbar = [Tb[0]] if d == 1 else [Tb[0], Tb[1], Tb[0] ^ Tb[1]]
    reach = set(); sols = []
    g0 = A0
    l = g0 ^ (g0 >> 1)
    cur = [0] * k
    for i in range(k):
        if l >> i & 1:
            for j in range(k): cur[j] ^= R[i][j]
    for g in range(A0, B0):
        if g > A0:
            i = ((g ^ (g >> 1)) ^ l).bit_length() - 1
            l ^= 1 << i
            Ri = R[i]
            for j in range(k): cur[j] ^= Ri[j]
        if g == 0: continue
        S = gf.Span()
        for j in range(k):
            if cur[j]: S.add(cur[j], 1 << j)
        for tv in tbar:
            if tv in reach and len(sols) > 50: continue
            r, tag = S.reduce(tv)
            if r == 0:
                reach.add(tv)
                if len(sols) < 200: sols.append((hex(l), hex(tag), tbar.index(tv)))
    rec.update({'reached': len(reach), 'complete': (len(reach) >= 1 and d == 1) or
                (d == 2 and len(reach) >= 2), 'nsol_kept': len(sols), 'sols': sols[:10],
                'secs': round(time.time() - t0, 1)})
    rec['total_last'] = len(X) + d
    rec['reach_idx'] = sorted(tbar.index(t) for t in reach)
    if rec['complete'] and len(X) + d <= 13: rec['event'] = 'CANDIDATE'
    line = json.dumps(rec)
    print(line, flush=True)
    if a.out: open(a.out, 'a').write(line + '\n')


if __name__ == '__main__':
    main()
