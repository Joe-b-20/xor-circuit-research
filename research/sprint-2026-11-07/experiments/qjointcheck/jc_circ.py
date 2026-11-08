#!/usr/bin/env python3
"""qjointcheck/jc_circ.py -- (a) the new rows on the 13 package controls + N real circuits (4 orbit steps each) with
my own odd-graph extraction (types, missing-label sets, full-met labels, m_i; stress.Circuit is used only for the
masks / parities and for canonical_transpose), in the strong per-helper forms and as the LP rows of lp_qjc.jc_rows
with the phase's type counts and a = A; (b) synthetic two-hub phases with A >= 1 built from MY limit configurations
(jc_geo): realizable kinds (F_joint independent) must satisfy every row; excluded kinds (J1) must be dependent and
violate LIM; plus (0,2)-(0,2) same-label pairs and a three-hub chain.
usage: python3 jc_circ.py [N_REAL]
"""
import sys, json, glob, time, itertools
from math import comb
from collections import Counter, defaultdict
from pathlib import Path
SPRINT = Path.home()/'xs-campaigns/2026-11-07-sprint'
sys.path.insert(0, str(SPRINT/'lb76/pkg_copy/source/lower_bounds/checks'))
sys.path.insert(0, str(SPRINT/'bridge'))
sys.path.insert(0, str(SPRINT/'qjointcheck'))
from stress import Circuit  # noqa: E402
from profile_real import reconstruct  # noqa: E402
import lp_qjc  # noqa: E402
from jc_geo import Geo, indep, HB  # noqa: E402
OUT = SPRINT/'qjointcheck'

def extract(C):
    n = C.n; B = set(range(32)) | set(C.out_index)
    H = [v for v in range(32, n) if C.odd[v] and v not in C.out_index]
    edges = []
    for k, (a, b) in enumerate(C.gates):
        s = 32 + k
        if C.odd[a] and C.odd[b]: edges.append((a, b, s))
        elif C.odd[a] != C.odd[b]:
            o, e = (a, b) if C.odd[a] else (b, a); edges.append((o, s, e))
    evens = [v for v in range(32, n) if not C.odd[v]]
    bb = {}
    for p, q_, e in edges:
        if p in B and q_ in B:
            assert e not in bb, 'two B-B edges with one label'; bb[e] = (p, q_)
    q = sum(1 for e in evens if e not in bb)
    inc = defaultdict(list)
    for p, q_, e in edges: inc[p].append((q_, e)); inc[q_].append((p, e))
    typ = {}; L = {}
    for v in H:
        r = u = vv = 0; ms = set()
        for w, e in inc[v]:
            if w in B:
                if e in bb: r += 1
                else: u += 1; ms.add(e)
            else: vv += 1
        assert len(ms) == u
        typ[v] = (r, u, vv); L[v] = ms
    for v1, v2 in itertools.combinations(H, 2): assert len(L[v1] & L[v2]) <= 1, 'Lemma 4.6'
    full = {v for v in H if typ[v][0] == 3}
    fullmet = set().union(*[L[f] for f in full]) if full else set()
    a = len(fullmet); assert a == sum(typ[f][1] for f in full), 'Lemma 4.5'
    m = {v: len(L[v] & fullmet) for v in H}
    return dict(ori=C.ori, q=q, a=a, typ=typ, m=m, full=full, L=L)

def check_phase(ph):
    q, a, typ, m, full, L = ph['q'], ph['a'], ph['typ'], ph['m'], ph['full'], ph['L']
    top = lp_qjc.fm_table(ph['ori'])[0]
    nonfull = [v for v in typ if v not in full]
    v_ = {}
    v_['P1'] = sum(comb(m[v], 2) for v in nonfull) + sum(comb(typ[f][1], 2) for f in full) - comb(a, 2)
    v_['P2'] = sum(m[v] * (typ[v][1] - m[v]) for v in nonfull) - a * (q - a)
    v_['P3'] = sum(comb(typ[v][1] - m[v], 2) for v in nonfull) - comb(q - a, 2)
    v_['P4f'] = sum(1 for v in typ if (typ[v][1] if v in full else m[v]) >= 3) - lp_qjc.pack3(a)
    v_['P4h'] = sum(1 for v in nonfull if typ[v][1] - m[v] >= 3) - lp_qjc.pack3(q - a)
    v_['P5'] = sum(typ[v][0] * m[v] for v in nonfull) - (top[a] - 3 * a)
    v_['H2'] = max([typ[v][0] + m[v] - 3 for v in nonfull] or [-3])
    lim = [v for v in nonfull if typ[v][0] + m[v] == 3]
    v_['J1'] = sum(1 for x, y in itertools.combinations(lim, 2) if L[x] & L[y])
    # LIM strong form: limit hubs carrying every hub-only label
    limfull = [v for v in lim if typ[v][1] == (3 - typ[v][0]) + (q - a)]
    v_['LIM'] = (sum(typ[v][1] for v in limfull) - q) if a == q else (len(limfull) - 1)
    cnt = Counter(typ.values()); types = sorted(cnt)
    def vec(fn): return {t: float(fn(*t)) for t in types if fn(*t) != 0}
    for name, (row, rhs) in zip(['LP_P1', 'LP_P2', 'LP_P3', 'LP_P4f', 'LP_P4h', 'LP_P5', 'LP_LIM'], lp_qjc.jc_rows(types, q, a, ph['ori'], vec, True)):
        v_[name] = sum(c * cnt[t] for t, c in row.items()) - rhs
    return v_, len(lim)

def orbit(gates, steps=4):
    C = Circuit(gates, 'M'); recs = []
    for step in range(steps):
        I = C.analyse(); ph = extract(C)
        assert ph['q'] == I['q'], (ph['q'], I['q'])
        v_, nlim = check_phase(ph)
        recs.append(dict(step=step, ori=ph['ori'], q=ph['q'], a=ph['a'], nlim=nlim, viol=v_))
        if step + 1 < steps: C, _ = C.canonical_transpose(I)
    return recs

def synthetic(G, configs, X=()):
    """phase of a joint configuration alone: hubs k with (h, R, S); X = hub pairs sharing a hub-only label.
    Full-met labels: one per (hub, f) incidence, merged when two hubs meet f with intersecting pairs at f's end
    (same label).  Types: hub (r, m + e, 0), full f (3, #labels at f, 0).  Returns (phase, independent?)."""
    labels_at_f = defaultdict(set); L = {}; hubs = {}
    for k, (h, R, S) in enumerate(configs):
        L[('h', k)] = set()
        for f in S:
            P = G.PM[h ^ f]
            # choose f's end: the vertex shared with another hub's pair at f if any (same label), else the lower bit
            ends = [c for c in range(64) if (P >> c) & 1]
            c = ends[0]
            for k2, (h2, R2, S2) in enumerate(configs):
                if k2 != k and f in S2 and (G.PM[h2 ^ f] & P): c = (G.PM[h2 ^ f] & P).bit_length() - 1
            lab = ('fm', f, c); labels_at_f[f].add(lab); L[('h', k)].add(lab)
    for k, k2 in X:
        lab = ('ho', k, k2); L[('h', k)].add(lab); L[('h', k2)].add(lab)
    fulls = sorted({f for _, _, S in configs for f in S})
    typ = {}; m = {}
    for f in fulls:
        typ[('f', f)] = (3, len(labels_at_f[f]), 0); L[('f', f)] = set(labels_at_f[f]); m[('f', f)] = len(labels_at_f[f])
    fullmet = {lab for f in fulls for lab in labels_at_f[f]}
    for k, (h, R, S) in enumerate(configs):
        typ[('h', k)] = (len(R), len(L[('h', k)]), 0); m[('h', k)] = len(L[('h', k)] & fullmet)
    alllab = set().union(*L.values())
    ph = dict(ori=G.ori, q=len(alllab), a=len(fullmet), typ=typ, m=m, full={('f', f) for f in fulls}, L=L)
    return ph, indep(G.joint(configs, X))

def main():
    nreal = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    t0 = time.time(); out = []
    for fn in sorted(glob.glob(str(SPRINT/'lb76/pkg_copy/source/circuits/*.json'))):
        dd = json.load(open(fn)); g = dd['gates'] if isinstance(dd, dict) else dd
        out.append(dict(tag='ctrl:' + Path(fn).name, phases=orbit(g)))
    d = json.load(open(SPRINT/'bridge/profiles.json'))
    for r in [r for r in d['results'] if 'error' not in r][:nreal]:
        gates, order, info = reconstruct(r['values'], 'ymax', 0, True)
        out.append(dict(tag=r['tag'], phases=orbit(gates)))
    ph = [p for r in out for p in r['phases']]
    print(f'{len(out)} circuits, {len(ph)} phases; q histogram {sorted(Counter(p["q"] for p in ph).items())}; A histogram {sorted(Counter(p["a"] for p in ph).items())}; '
          f'limit hubs per phase max {max(p["nlim"] for p in ph)}; {time.time()-t0:.0f}s')
    for nm in ph[0]['viol']:
        vals = [p['viol'][nm] for p in ph]
        print(f'  {nm:7s}: violations {sum(1 for v in vals if v > 0)}; max (lhs - rhs) {max(vals)}; min slack {-max(vals)}')
    json.dump(out, open(OUT/'jc_circ.json', 'w'))
    # ---- synthetic configurations with A >= 1
    print('synthetic two-hub phases (own limit configurations):')
    summary = {}
    for ori in ('M', 'Mt'):
        G = Geo(ori); lim, _ = G.limit_configs()
        allc = [c for r in (0, 1, 2) for c in lim[r]]
        kinds = defaultdict(list)       # kind -> list of (configs, X)
        byf = defaultdict(list)
        for i, c in enumerate(allc):
            for f in c[2]: byf[f].append(i)
        for f, lst in byf.items():
            for i, j in itertools.combinations(lst, 2):
                c1, c2 = allc[i], allc[j]
                if c1[0] == c2[0]: continue
                inter = bool(G.PM[c1[0] ^ f] & G.PM[c2[0] ^ f])
                key = tuple(sorted(((len(c1[1]), len(c1[2])), (len(c2[1]), len(c2[2])))))
                kinds[('same-label' if inter else 'diff-labels', key)].append(([c1, c2], ()))
        for c1, c2 in itertools.combinations(allc, 2):
            if c1[0] != c2[0] and (c1[0] ^ c2[0]) in G.PM:
                key = tuple(sorted(((len(c1[1]), len(c1[2])), (len(c2[1]), len(c2[2])))))
                kinds[('hub-only', key)].append(([c1, c2], ((0, 1),)))
        # sub-limit (0,2)-(0,2) same-label pairs from (0,3) limit configurations with one f dropped
        sub = sorted({(h, (), S2) for (h, R, S) in lim[0] for S2 in itertools.combinations(S, 2)})
        byf2 = defaultdict(list)
        for i, c in enumerate(sub):
            for f in c[2]: byf2[f].append(i)
        for f, lst in byf2.items():
            for i, j in itertools.combinations(lst, 2):
                c1, c2 = sub[i], sub[j]
                if c1[0] != c2[0] and (G.PM[c1[0] ^ f] & G.PM[c2[0] ^ f]): kinds[('same-label', ((0, 2), (0, 2)))].append(([c1, c2], ()))
        # three limit hubs pairwise sharing distinct full helpers at different labels (a chain) when available
        for kind in sorted(kinds, key=str):
            lst = kinds[kind]
            n_ind = 0; row_viol = Counter(); n = 0; worst = {}
            for configs, X in lst[:3000]:
                ph, ok = synthetic(G, configs, X); n += 1
                v_, _ = check_phase(ph)
                if ok:
                    n_ind += 1
                    for k, v in v_.items():
                        if v > 0: row_viol[k] += 1
                        worst[k] = max(worst.get(k, -99), v)
                else:
                    for k, v in v_.items():
                        if k == 'LIM' and v > 0: row_viol['LIM@dep'] += 1
            tag = f'{ori} {kind}'
            summary[tag] = dict(tested=n, independent=n_ind, violations_on_independent=dict(row_viol), max_lhs_minus_rhs_on_independent=worst)
            print(f'  {tag}: tested {n}, independent {n_ind}; row violations on independent phases {dict((k, v) for k, v in row_viol.items() if k != "LIM@dep")}; '
                  f'LIM violated on dependent (excluded) phases {row_viol.get("LIM@dep", 0)}; tightest rows on independent: '
                  f'{ {k: v for k, v in worst.items() if v >= -1} }')
    json.dump(summary, open(OUT/'jc_synthetic.json', 'w'), indent=1)
    print(f'total {time.time()-t0:.0f}s')

if __name__ == '__main__':
    main()
