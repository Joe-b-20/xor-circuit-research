"""Exhaustive 2-swap neighbourhood of a known 13-member GF(4)-norm layer (agent H1).

From layer L (layers.json): remove 2 members, add 2 of the other 1262 (z, zeta); for each of the
6 parity spaces (gamma none and the 5 gamma groups) test the n-block + parity condition
rank([A | Y]) = rank(A) + 8 with A = (z | parity mod Pi) incrementally; survivors get the exact
nfast.test (junk lower bound Jlb) for each gamma of the group; sets with Jlb <= 3 are re-checked on
truth tables with cond27 (R2-R4) and the exact 9-cover test (R5). A pass = 9 + 5 + 13 = 27.
usage: python3 swap2.py --layer I --pairs A:B (indices into the 78 removed pairs) --out F"""
import argparse
import itertools
import json
import sys
import time
import numpy as np
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import nfast                                     # noqa: E402
from nfast import MU5, IDX, mul, echelon, reduce_mod   # noqa: E402
from xag import gf                               # noqa: E402

GROUPS = {'none': ['none'], '0': ['0', '85', '170'], '17': ['17', '102', '187'],
          '34': ['34', '119', '204'], '51': ['51', '136', '221'], '68': ['68', '153', '238']}
ALL = [(z, zt) for z in range(1, 256) for zt in MU5]


def vec(m, piv):
    z, zt = m
    par = reduce_mod(1 << IDX[zt], piv)
    Y = mul(z, gf.INV[zt])
    return z | (par << 8), Y           # A part (13 bits), Y (8 bits)


def add_row(rows, v):
    for r in rows:
        if v ^ r < v: v ^= r
    if v:
        rows = sorted(rows + [v], reverse=True)
    return rows, v != 0


def vreduce(x, rows):
    x = x.copy()
    for r in rows:
        h = r.bit_length() - 1
        x ^= ((x >> h) & 1) * r
    return x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--layer', type=int, required=True)
    ap.add_argument('--pairs', default='0:78')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    t0 = time.time()
    L = json.load(open('/home/joebachir20/xs-campaigns/2026-11-15-study/H1/layers.json'))[a.layer]
    base = [tuple(m) for m in L['members']]
    pool = [m for m in ALL if m not in base]
    p0, p1 = map(int, a.pairs.split(':'))
    pairs = list(itertools.combinations(range(len(base)), 2))[p0:p1]
    log = open(a.out, 'a')
    st = {'sets': 0, 'nblock': 0, 'Jlb<=5': 0, 'Jlb<=3': 0, 'R5': 0}
    for gname, gammas in GROUPS.items():
        piv = echelon(nfast.pi_basis(gammas[0]))
        V = {m: vec(m, piv) for m in ALL}
        for rem in pairs:
            keep = [m for i, m in enumerate(base) if i not in rem]
            rA = []; rAY = []
            for m in keep:
                A, Y = V[m]
                rA, _ = add_row(rA, A); rAY, _ = add_row(rAY, A | (Y << 13))
            PA = np.array([V[m][0] for m in pool], dtype=np.int64)
            PAY = np.array([V[m][0] | (V[m][1] << 13) for m in pool], dtype=np.int64)
            for i1 in range(len(pool)):
                m1 = pool[i1]; A1, Y1 = V[m1]
                rA1, _ = add_row(rA, A1); rAY1, _ = add_row(rAY, A1 | (Y1 << 13))
                xa = vreduce(PA[i1 + 1:], rA1); xay = vreduce(PAY[i1 + 1:], rAY1)
                rkA = len(rA1) + (xa != 0); rkAY = len(rAY1) + (xay != 0)
                st['sets'] += len(pool) - i1 - 1
                for j in np.nonzero(rkAY == rkA + 8)[0]:
                    i2 = i1 + 1 + int(j); m2 = pool[i2]
                    st['nblock'] += 1
                    S = keep + [m1, m2]
                    for g in gammas:
                        r = nfast.test(S, g)
                        if not r['ok'] or r['Jlb'] > 5: continue
                        st['Jlb<=5'] += 1
                        rec = {'layer': a.layer, 'removed': [base[i] for i in rem], 'added': [m1, m2],
                               'gamma': g, **r}
                        if r['Jlb'] <= 3:
                            st['Jlb<=3'] += 1
                            import cond27
                            out = cond27.evaluate(S, g, do_cover=True, limit=60)
                            rec['cond27'] = out
                            if out.get('R5'):
                                st['R5'] += 1; rec['event'] = 'CANDIDATE'
                            elif 'R5' in out and out['R5'] is None:   # SAT timeout: undecided
                                st['undecided'] = st.get('undecided', 0) + 1; rec['event'] = 'UNDECIDED'
                        print(json.dumps(rec), file=log, flush=True)
    print(json.dumps({'event': 'done', 'layer': a.layer, 'pairs': a.pairs, **st,
                      'secs': round(time.time() - t0, 1)}), file=log, flush=True)


if __name__ == '__main__':
    main()
