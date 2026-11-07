#!/usr/bin/env python3
"""Check finite fact H2 and row HUB2 on the 13 package controls and the 303 real circuits (4 orbit steps each,
1,264 phases), with the package's own Circuit / analyse / canonical_transpose (as qreal/qr_circ.py).

Per phase and per helper i:  m_i = number of missing labels at i that also have an H-B edge at a full helper.
  H2:   r_i + m_i <= 3 for every helper (full helpers: m_i = 0 by Lemma 4.5).
  HUB2 row (LP form, with A = sum_{r=3} u = number of full-met labels):  u_i <= (3 - r_i) + (q - A) for r_i <= 2.
  C1 on the circuit: for every non-full helper i with m_i >= 1 the family {H_f + T} u {H_i + T_i} u
        {H_i + H_f + P} is independent (vacuous when m_i = 0); as a non-vacuous surrogate, the independence of
        ALL represented relations together with t_l - 1 mixed vectors H_i + H_j + P_l per missing label l met by t_l helpers through H-B
        edges (P_l = the pair of their two boundary ends; a spanning path of the t_l equations), the same argument.
usage: python3 qh_circ.py [N_REAL]
"""
import sys, json, glob, itertools, time
from collections import Counter, defaultdict
from pathlib import Path
SPRINT = Path.home()/'xs-campaigns/2026-11-07-sprint'
sys.path.insert(0, str(SPRINT/'lb76/pkg_copy/source/lower_bounds/checks'))
sys.path.insert(0, str(SPRINT/'bridge'))
from stress import Circuit, rank  # noqa: E402
from profile_real import reconstruct  # noqa: E402
OUT = SPRINT/'qhub'

def phase_facts(C, I):
    B = I['B']; H = set(I['H']); Hs = I['H']
    Bidx = {v: i for i, v in enumerate(sorted(B))}; Hidx = {v: i for i, v in enumerate(Hs)}
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
    missing = {e for e in evens if e not in bb}
    hedges = {v: [] for v in H}
    for p, q_, e in edges:
        for v in (p, q_):
            if v in H: hedges[v].append((q_ if v == p else p, e))
    typ = {}; rep_rows = []; miss_at = defaultdict(list)     # missing label -> [(helper, boundary end)]
    for v in H:
        r = u = vv = 0
        for o, e in hedges[v]:
            if o in B and e in bb:
                r += 1; b1, b2 = bb[e]
                rep_rows.append((1 << Bidx[o]) | (1 << Bidx[b1]) | (1 << Bidx[b2]) | (1 << (64 + Hidx[v])))
            elif o in B: u += 1; miss_at[e].append((v, o))
            else: vv += 1
        typ[v] = (r, u, vv)
    full = {v for v in H if typ[v][0] == 3}
    q = I['q']
    A = sum(typ[v][1] for v in full)
    # per helper m_i
    m = Counter()
    for e, lst in miss_at.items():
        fulls_here = [v for v, o in lst if v in full]
        assert len(fulls_here) <= 1
        if fulls_here:
            for v, o in lst:
                if v not in full: m[v] += 1
    h2_viol = sum(1 for v in H if typ[v][0] + m[v] > 3)
    row_slack = min((3 - typ[v][0]) + (q - A) - typ[v][1] for v in H if typ[v][0] <= 2) if any(typ[v][0] <= 2 for v in H) else 99
    # mixed vectors of every pair sharing a missing label
    mixed = []
    for e, lst in miss_at.items():
        # t_l H-B equations H_i + B_b + E_l at label l give t_l - 1 independent sums (a spanning path), not C(t_l, 2)
        (v1, o1) = lst[0]
        for (v2, o2) in lst[1:]:
            mixed.append((1 << Bidx[o1]) | (1 << Bidx[o2]) | (1 << (64 + Hidx[v1])) | (1 << (64 + Hidx[v2])))
    indep = rank(rep_rows + mixed) == len(rep_rows) + len(mixed)
    return dict(ori=C.ori, q=q, A=A, n3=len(full), h2_viol=h2_viol, row_slack=row_slack, max_m=max(m.values()) if m else 0,
                n_mixed=len(mixed), indep=indep, shared_pairs=len(mixed))

def orbit(gates, steps=4):
    C = Circuit(gates, 'M'); recs = []
    for step in range(steps):
        I = C.analyse(); rec = dict(step=step); rec.update(phase_facts(C, I)); recs.append(rec)
        if step + 1 < steps: C, _ = C.canonical_transpose(I)
    return recs

def main():
    nreal = int(sys.argv[1]) if len(sys.argv) > 1 else 10 ** 9
    t0 = time.time(); out = []
    for fn in sorted(glob.glob(str(SPRINT/'lb76/pkg_copy/source/circuits/*.json'))):
        dd = json.load(open(fn)); g = dd['gates'] if isinstance(dd, dict) else dd
        out.append(dict(tag='ctrl:' + Path(fn).name, phases=orbit(g)))
    d = json.load(open(SPRINT/'bridge/profiles.json'))
    for i, r in enumerate([r for r in d['results'] if 'error' not in r][:nreal]):
        gates, order, info = reconstruct(r['values'], 'ymax', 0, True)
        out.append(dict(tag=r['tag'], phases=orbit(gates)))
    ph = [p for r in out for p in r['phases']]
    print(f'{len(out)} circuits, {len(ph)} phases')
    print(f'  H2 violations (r_i + m_i > 3): {sum(p["h2_viol"] for p in ph)} (must be 0); max m_i over all helpers: {max(p["max_m"] for p in ph)}; max A: {max(p["A"] for p in ph)}')
    print(f'  HUB2 row min slack over non-full helpers: {min(p["row_slack"] for p in ph)} (>= 0 required)')
    print(f'  mixed-vector independence (represented relations + H_i+H_j+P at every shared missing label): failures {sum(1 for p in ph if not p["indep"])} (must be 0); '
          f'pairs sharing a missing label per phase: min {min(p["n_mixed"] for p in ph)} median {sorted(p["n_mixed"] for p in ph)[len(ph)//2]} max {max(p["n_mixed"] for p in ph)}')
    json.dump(out, open(OUT/'qh_circ.json', 'w'))
    print(f'total {time.time()-t0:.0f}s')

if __name__ == '__main__':
    main()
