"""Exhaustive small neighbourhoods of known GF(4)-norm last layers, graph model, stage 1 free
(agent H1). From layer L (layers.json): remove r members, add a members from the 1275 (z, zeta),
giving k = |L| - r + a; every resulting set is tested with cond27's conditions R1 (n-block),
R2/R3 (feasible with n only), R4 (x-junk J) for EVERY gamma (16 values), and R5 (9-cover of U,
exact enum for dim U >= 7; SAT with a time limit for dim U = 6) for those with J <= 3.
A set passing R1-R5 = a 9 + 5 + k circuit (to be built and aes_checked).

usage: python3 nbhd.py --layer I --remove R --add A [--chunk C/NC] [--cover-limit S] [--out F]
"""
import argparse
import itertools
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cond27                                 # noqa: E402
from cond27 import gf, MU5                    # noqa: E402

GAMMAS = ['none'] + [str(17 * i) for i in range(15)]
ALL = [(z, zt) for z in range(1, 256) for zt in MU5]

import qmc                                    # noqa: E402
NQ = qmc.Normal(cond27.A_BASE + cond27.QUAD)  # modulo aff + N + n + Quad   (R2)
NA = qmc.Normal(cond27.A_BASE)                # modulo aff + N + n          (R4)
TQ = [NQ.nf(t) for t in cond27.T]
TA = [NA.nf(t) for t in cond27.T]
_cache = {}


def red(m, g):
    key = (m, g)
    if key not in _cache:
        t = cond27.member_table(m[0], m[1], g)
        _cache[key] = (NQ.nf(t), NA.nf(t))
    return _cache[key]


def fast_junk(S, g):
    """(feasible R2/R3, J) via cached reductions; identical to cond27.junk's first two fields"""
    rs = [red(m, g) for m in S]
    sq = gf.Span([r[0] for r in rs]); d0 = sq.dim()
    for t in TQ: sq.add(t)
    if sq.dim() != d0: return False, None
    sa = gf.Span([r[1] for r in rs]); d1 = sa.dim()
    for t in TA: sa.add(t)
    return True, sa.dim() - d1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--layer', type=int, required=True)
    ap.add_argument('--remove', type=int, default=1)
    ap.add_argument('--add', type=int, default=1)
    ap.add_argument('--chunk', default='0/1')
    ap.add_argument('--cover-limit', type=float, default=30)
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    t0 = time.time()
    L = json.load(open('/home/joebachir20/xs-campaigns/2026-11-15-study/H1/layers.json'))[a.layer]
    base = [tuple(m) for m in L['members']]
    ci, cn = map(int, a.chunk.split('/'))
    log = open(a.out, 'a') if a.out else sys.stdout
    stats = {'sets': 0, 'R1': 0, 'feasible': 0, 'J<=3': 0, 'R5': 0}
    seen = set()
    rem_list = list(itertools.combinations(range(len(base)), a.remove))
    for ri, rem in enumerate(rem_list):
        if ri % cn != ci: continue
        keep = [m for i, m in enumerate(base) if i not in rem]
        pool = [m for m in ALL if m not in base]
        for add in itertools.combinations(pool, a.add):
            S = tuple(sorted(keep + list(add)))
            if S in seen: continue
            seen.add(S); stats['sets'] += 1
            if not cond27.r1(S): continue
            stats['R1'] += 1
            for g in GAMMAS:
                feas, J = fast_junk(S, g)
                if not feas: continue
                if J <= 3:
                    feas2, J2, qs, dD = cond27.junk(S, g)     # slow exact path (q-parts)
                    assert feas2 and J2 == J
                else:
                    dD = None
                stats['feasible'] += 1
                stats.setdefault('Jhist', {})
                stats['Jhist'][str(J)] = stats['Jhist'].get(str(J), 0) + 1
                if J > 5: continue
                rec = {'layer': a.layer, 'removed': [base[i] for i in rem], 'added': list(add),
                       'gamma': g, 'k': len(S), 'J': J, 'dimD': dD}
                if J <= 3:
                    stats['J<=3'] += 1
                    dU, ok = cond27.cover(qs, a.cover_limit)
                    rec.update({'dimU': dU, 'R5': ok})
                    if ok:
                        stats['R5'] += 1
                        rec['event'] = 'CANDIDATE'
                    elif ok is None:          # SAT branch timed out: undecided, never 'not coverable'
                        stats['undecided'] = stats.get('undecided', 0) + 1
                        rec['event'] = 'UNDECIDED'
                print(json.dumps(rec), file=log, flush=True)
    print(json.dumps({'event': 'done', 'layer': a.layer, 'files': L['files'][:2], 'gamma0': L['gamma'],
                      'remove': a.remove, 'add': a.add, 'chunk': a.chunk, **stats,
                      'secs': round(time.time() - t0, 1)}), file=log, flush=True)


if __name__ == '__main__':
    main()
