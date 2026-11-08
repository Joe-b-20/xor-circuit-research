#!/usr/bin/env python3
"""qjoint/qj_vert.py -- dump and classify the load-bearing vertices of the final (batch 1-3) LP systems.

For every one of the 551 load-bearing keys (qhubcheck/lp_qhc_keysfull_GstarN1HUB2DARKPKFM.json, field load_bearing)
and every LP-feasible (hub case, dark case) pair of the variant GstarN1HUB2DARKPKFM (lp_qhc.system, unchanged):
  * three LP vertices (zero objective; fewest non-full helpers with u >= 1; most of them),
  * one integer solution of the case system (HiGHS MILP, all columns integer) if one exists,
and the hub / full-helper structure of each solution:
  n3      = sum_{r=3} n                      full helpers
  nf1     = sum_{r=3, u>=1} n                full helpers meeting missing labels
  A       = sum_{r=3} u n                    full-met labels (exactly one full helper each, Lemma 4.5)
  hubs    = types (r<3, u>=1) with their counts; for each, m_lb = max(0, u - (q - A)) is the least number of its
            missing labels that are full-met (row HUB2: u <= (3 - r) + (q - A)), m_ub = min(u, 3 - r) (Lemma H2)
  H1      = number of hubs with m_lb >= 1 (hubs that must meet full helpers)
  I_lb    = sum n * m_lb                     (hub, full-met label) incidences, lower bound
  share_lb= max(0, I_lb - nf1)               if > 0 some full helper is met by >= 2 hubs (a hub meets each full
            helper at most once, Lemma 4.6), i.e. hubs share full helpers
  pairs   = sum C(u,2) n vs C(q,2)           L5 slack (0: every pair of missing labels co-occurs at exactly one helper)
Output: vertices.json (everything), vert_summary.log (per-key lines and the classification tables).
"""
import sys, json, time
from math import comb
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from scipy.optimize import linprog, milp, LinearConstraint, Bounds
SPRINT = Path.home()/'xs-campaigns/2026-11-07-sprint'
sys.path.insert(0, str(SPRINT/'qhubcheck'))
import lp_qhc  # noqa: E402
OUT = SPRINT/'qjoint'
V = 'GstarN1HUB2DARKPKFM'

def mats(cols, EQ, LE):
    idx = {c: i for i, c in enumerate(cols)}
    def mat(rows):
        A = np.zeros((len(rows), len(cols)))
        for i, (row, _) in enumerate(rows):
            for k, val in row.items(): A[i, idx[k]] = val
        return A, np.array([b for _, b in rows], float)
    return mat(EQ), mat(LE)

def lp_vertex(cols, M, c):
    (A_eq, b_eq), (A_ub, b_ub) = M
    r = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method='highs')
    return r.x if r.status == 0 else None

def int_solution(cols, M, c):
    (A_eq, b_eq), (A_ub, b_ub) = M
    cons = []
    if len(b_eq): cons.append(LinearConstraint(A_eq, b_eq, b_eq))
    if len(b_ub): cons.append(LinearConstraint(A_ub, -np.inf, b_ub))
    r = milp(c, constraints=cons, integrality=np.ones(len(cols)), bounds=Bounds(0, np.inf), options=dict(time_limit=20))
    if r.status == 0 and r.x is not None: return np.round(r.x).astype(int)
    return None

def classify(cols, x, q, tol=1e-7):
    t = {c: float(v) for c, v in zip(cols, x) if isinstance(c, tuple) and v > tol}
    aux = {c: round(float(v), 3) for c, v in zip(cols, x) if not isinstance(c, tuple) and v > tol}
    n3 = sum(v for (r, u, vv), v in t.items() if r == 3)
    nf1 = sum(v for (r, u, vv), v in t.items() if r == 3 and u >= 1)
    A = sum(u * v for (r, u, vv), v in t.items() if r == 3)
    hubs = {}
    for (r, u, vv), v in t.items():
        if r < 3 and u >= 1:
            m_lb = max(0, u - (q - A)); m_ub = min(u, 3 - r)
            hubs[(r, u, vv)] = dict(n=round(v, 3), m_lb=round(m_lb, 3), m_ub=m_ub)
    H1 = sum(d['n'] for d in hubs.values() if d['m_lb'] > tol)
    I_lb = sum(d['n'] * d['m_lb'] for d in hubs.values())
    share_lb = max(0.0, I_lb - nf1)
    pairs = sum(comb(u, 2) * v for (r, u, vv), v in t.items())
    nhub_tot = sum(d['n'] for d in hubs.values())
    return dict(types={str(k): round(v, 3) for k, v in sorted(t.items())}, aux=aux, n3=round(n3, 3), nf1=round(nf1, 3), A=round(A, 3),
                hubs={str(k): d for k, d in sorted(hubs.items())}, H1=round(H1, 3), I_lb=round(I_lb, 3), share_lb=round(share_lb, 3),
                nhub=round(nhub_tot, 3), L5_slack=round(comb(q, 2) - pairs, 3), max_u_hub=max([k[1] for k in hubs] or [0]))

def main():
    t0 = time.time()
    keys = [tuple(k) for k in json.load(open(SPRINT/'qhubcheck/lp_qhc_keysfull_GstarN1HUB2DARKPKFM.json'))['load_bearing']]
    lp_qhc.VARIANT[0] = V
    out = []; log = open(OUT/'vert_summary.log', 'w')
    def P(*a):
        print(*a, flush=True); print(*a, file=log, flush=True)
    P(f'{len(keys)} load-bearing keys, variant {V}')
    n_int_keys = 0
    for ki, key in enumerate(keys):
        h, y, F, q, z, ori = key
        rec = dict(key=list(key), cases=[])
        anyint = False
        for hc in lp_qhc.hub_cases(V, q):
            cols0, EQ0, LE0 = lp_qhc.system(h, y, F, q, z, ori, V, hc, None)
            if not lp_qhc.lp_ok(cols0, EQ0, LE0): continue
            for dc in lp_qhc.dark_cases(V, q):
                cols, EQ, LE = lp_qhc.system(h, y, F, q, z, ori, V, hc, dc)
                M = mats(cols, EQ, LE)
                x0 = lp_vertex(cols, M, np.zeros(len(cols)))
                if x0 is None: continue
                chub = np.array([1.0 if isinstance(c, tuple) and c[0] < 3 and c[1] >= 1 else 0.0 for c in cols])
                verts = {'zero': classify(cols, x0, q)}
                x1 = lp_vertex(cols, M, chub); verts['min_hubs'] = classify(cols, x1, q)
                x2 = lp_vertex(cols, M, -chub); verts['max_hubs'] = classify(cols, x2, q)
                xi = int_solution(cols, M, chub)
                xi2 = int_solution(cols, M, -chub) if xi is not None else None
                ints = {}
                if xi is not None: ints['min_hubs'] = classify(cols, xi, q); anyint = True
                if xi2 is not None: ints['max_hubs'] = classify(cols, xi2, q)
                rec['cases'].append(dict(hub=list(hc) if hc else None, dark=dc, lp=verts, int=ints))
        if anyint: n_int_keys += 1
        out.append(rec)
        cs = rec['cases']
        summ = []
        for c in cs:
            iv = c['int'].get('min_hubs')
            tag = f"A={c['hub'][1] if c['hub'] else '-'}{'' if not c['hub'] or c['hub'][0]=='eq' else '<='} d={c['dark']}"
            if iv: tag += f" INT[n3={iv['n3']} A={iv['A']} hubs={iv['nhub']} H1={iv['H1']} I={iv['I_lb']} share>={iv['share_lb']} L5s={iv['L5_slack']}]"
            else: tag += ' noINT'
            summ.append(tag)
        P(f'[{ki+1}/{len(keys)}] key {key}: {len(cs)} feasible cases: ' + ' | '.join(summ) + f'  ({time.time()-t0:.0f}s)')
    json.dump(out, open(OUT/'vertices.json', 'w'))
    # classification tables over integer solutions (min_hubs and max_hubs) and over LP vertices
    P('\n== classification ==')
    P(f'keys with an integer-feasible case: {n_int_keys} of {len(keys)}')
    for src, lab in ((lambda c: list(c['int'].values()), 'integer solutions'), (lambda c: list(c['lp'].values()), 'LP vertices')):
        cnt_share = Counter(); cnt_H1 = Counter(); cnt_hubtypes = Counter(); cnt_shape = Counter(); keys_share = set(); keys_noshare = set()
        cnt_Aq = Counter(); cnt_L5 = Counter()
        for rec in out:
            q = rec['key'][3]; ori = rec['key'][5]
            for c in rec['cases']:
                for v in src(c):
                    cnt_share[(ori, q, v['share_lb'] > 0)] += 1
                    cnt_H1[(ori, q, min(int(round(v['H1'])), 6))] += 1
                    cnt_Aq[(ori, q, round(v['A'], 2))] += 1
                    cnt_L5[(ori, q, round(v['L5_slack'], 2))] += 1
                    for k, d in v['hubs'].items():
                        if d['m_lb'] > 0: cnt_hubtypes[(ori, k, d['m_lb'])] += 1
                    shape = tuple(sorted((k, round(d['n'], 1), round(d['m_lb'], 1)) for k, d in v['hubs'].items() if d['m_lb'] > 0))
                    cnt_shape[(ori, q, shape)] += 1
                    (keys_share if v['share_lb'] > 0 else keys_noshare).add(tuple(rec['key']))
        P(f'\n-- {lab} --')
        P('share_lb > 0 (hubs forced to share full helpers) by (ori, q):', sorted(cnt_share.items()))
        P('keys with some solution forcing sharing:', len(keys_share), '; keys with some solution not forcing sharing:', len(keys_noshare),
          '; keys with ALL solutions forcing sharing:', len(keys_share - keys_noshare))
        P('number of hubs that must meet full helpers (H1, capped 6) by (ori, q):', sorted(cnt_H1.items()))
        P('A by (ori, q):', sorted(cnt_Aq.items()))
        P('L5 slack by (ori, q):', sorted(cnt_L5.items()))
        P('hub types with m_lb >= 1 (ori, type, m_lb): count:', sorted(cnt_hubtypes.items(), key=lambda kv: -kv[1])[:40])
        P('most frequent hub shapes (ori, q, ((type, n, m_lb), ...)):')
        for k, v in sorted(cnt_shape.items(), key=lambda kv: -kv[1])[:40]: P('   ', v, k)
    P(f'total {time.time()-t0:.0f}s')

if __name__ == '__main__':
    main()
