#!/usr/bin/env python3
"""qjoint/qj_circ.py -- check the qjoint rows on the 13 package controls and the 303 real circuits (4 orbit steps each,
1,264 phases), with the package's own Circuit / analyse / canonical_transpose (as qhub/qh_circ.py, whose phase
extraction is reused verbatim for types, missing labels and m_i).

Per phase, with a = A (the actual number of full-met labels), the strong (per-helper) forms:
  P1  sum_{non-full} C(m_i,2) + sum_{full} C(u_f,2) <= C(a,2)         P2  sum_{non-full} m_i (u_i - m_i) <= a (q - a)
  P3  sum_{non-full} C(u_i - m_i, 2) <= C(q - a, 2)                   P4  #{helpers with >= 3 full-met labels} <= D3(a),
                                                                          #{non-full with >= 3 hub-only labels} <= D3(q - a)
  P5  sum_{non-full} r_i m_i <= top(a) - 3a                           J1  no two limit hubs (r + m = 3, r < 3) share a label
and the LP rows exactly as implemented (qj_lp.joint_rows with the phase's type counts and a = A), incl. LIM.
usage: python3 qj_circ.py [N_REAL]
"""
import sys, json, glob, time
from math import comb
from collections import Counter, defaultdict
from pathlib import Path
SPRINT = Path.home()/'xs-campaigns/2026-11-07-sprint'
sys.path.insert(0, str(SPRINT/'lb76/pkg_copy/source/lower_bounds/checks'))
sys.path.insert(0, str(SPRINT/'bridge'))
sys.path.insert(0, str(SPRINT/'qjoint'))
from stress import Circuit  # noqa: E402
from profile_real import reconstruct  # noqa: E402
import qj_lp  # noqa: E402
OUT = SPRINT/'qjoint'
qj_lp.VARIANT[0] = 'GstarN1HUB2DARKPKFMJOINTLIM'

def phase_facts(C, I):
    B = I['B']; H = set(I['H'])
    edges = []
    for k, (a, b) in enumerate(C.gates):
        s = 32 + k
        if C.odd[a] and C.odd[b]: edges.append((a, b, s))
        elif C.odd[a] != C.odd[b]:
            o, e = (a, b) if C.odd[a] else (b, a); edges.append((o, s, e))
    evens = [v for v in range(32, C.n) if not C.odd[v]]
    bb = {}
    for p, q_, e in edges:
        if p in B and q_ in B: bb[e] = (p, q_)
    hedges = {v: [] for v in H}
    for p, q_, e in edges:
        for v in (p, q_):
            if v in H: hedges[v].append((q_ if v == p else p, e))
    typ = {}; miss_at = defaultdict(list); labels_of = defaultdict(set)
    for v in H:
        r = u = vv = 0
        for o, e in hedges[v]:
            if o in B and e in bb: r += 1
            elif o in B: u += 1; miss_at[e].append(v); labels_of[v].add(e)
            else: vv += 1
        typ[v] = (r, u, vv)
    full = {v for v in H if typ[v][0] == 3}
    fullmet = {e for e, lst in miss_at.items() if any(v in full for v in lst)}
    q = I['q']; a = len(fullmet)
    assert a == sum(typ[v][1] for v in full)
    m = {v: len(labels_of[v] & fullmet) for v in H}
    return dict(ori=C.ori, q=q, a=a, typ=typ, m=m, full=full, labels_of=labels_of)

def check(ph):
    q, a, typ, m, full, lab = ph['q'], ph['a'], ph['typ'], ph['m'], ph['full'], ph['labels_of']
    ori = ph['ori']; top, _ = qj_lp.fm_table(ori)
    nonfull = [v for v in typ if v not in full]
    viol = {}
    viol['P1'] = sum(comb(m[v], 2) for v in nonfull) + sum(comb(typ[v][1], 2) for v in full) - comb(a, 2)
    viol['P2'] = sum(m[v] * (typ[v][1] - m[v]) for v in nonfull) - a * (q - a)
    viol['P3'] = sum(comb(typ[v][1] - m[v], 2) for v in nonfull) - comb(q - a, 2)
    viol['P4f'] = sum(1 for v in typ if (m[v] if v not in full else typ[v][1]) >= 3) - qj_lp.D3(a)
    viol['P4h'] = sum(1 for v in nonfull if typ[v][1] - m[v] >= 3) - qj_lp.D3(q - a)
    viol['P5'] = sum(typ[v][0] * m[v] for v in nonfull) - (top[a] - 3 * a)
    lim = [v for v in nonfull if typ[v][0] + m[v] == 3]
    viol['J1'] = sum(1 for i in range(len(lim)) for j in range(i + 1, len(lim)) if lab[lim[i]] & lab[lim[j]])
    viol['H2'] = max([typ[v][0] + m[v] - 3 for v in nonfull] or [-3])
    # the LP rows as implemented, with the phase's type counts
    cnt = Counter(typ.values()); types = sorted(cnt)
    def vec(fn): return {t: float(fn(*t)) for t in types if fn(*t) != 0}
    for name, (row, rhs) in zip(['LP_P1', 'LP_P2', 'LP_P3', 'LP_P4f', 'LP_P4h', 'LP_P5', 'LP_LIM'], qj_lp.joint_rows(types, q, a, ori, vec)):
        viol[name] = sum(c * cnt[t] for t, c in row.items()) - rhs
    return viol, len(lim)

def orbit(gates, steps=4):
    C = Circuit(gates, 'M'); recs = []
    for step in range(steps):
        I = C.analyse(); ph = phase_facts(C, I); viol, nlim = check(ph)
        recs.append(dict(step=step, ori=ph['ori'], q=ph['q'], a=ph['a'], nlim=nlim, viol=viol))
        if step + 1 < steps: C, _ = C.canonical_transpose(I)
    return recs

def main():
    nreal = int(sys.argv[1]) if len(sys.argv) > 1 else 10 ** 9
    t0 = time.time(); out = []
    for fn in sorted(glob.glob(str(SPRINT/'lb76/pkg_copy/source/circuits/*.json'))):
        dd = json.load(open(fn)); g = dd['gates'] if isinstance(dd, dict) else dd
        out.append(dict(tag='ctrl:' + Path(fn).name, phases=orbit(g)))
    d = json.load(open(SPRINT/'bridge/profiles.json'))
    for r in [r for r in d['results'] if 'error' not in r][:nreal]:
        gates, order, info = reconstruct(r['values'], 'ymax', 0, True)
        out.append(dict(tag=r['tag'], phases=orbit(gates)))
    ph = [p for r in out for p in r['phases']]
    print(f'{len(out)} circuits, {len(ph)} phases; A histogram {sorted(Counter(p["a"] for p in ph).items())}; limit hubs per phase max {max(p["nlim"] for p in ph)}')
    names = list(ph[0]['viol'])
    for nm in names:
        vals = [p['viol'][nm] for p in ph]
        print(f'  {nm:7s}: violations {sum(1 for v in vals if v > 0)} ; max (lhs - rhs) {max(vals)} ; min slack {-max(vals)}')
    json.dump(out, open(OUT/'qj_circ.json', 'w'))
    print(f'total {time.time()-t0:.0f}s')

if __name__ == '__main__':
    main()
