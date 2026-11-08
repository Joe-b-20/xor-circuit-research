#!/usr/bin/env python3
"""qcert4 stress extension: the new rows (exact hub case A = a with Lemma P's rows P1-P5 and row LIM; finite fact J1)
on real circuits and on synthetic two-hub phases.  Positive controls only, never a premise.

Part A (circuits): the 13 package controls and the 303 real circuits of bridge/profiles.json (bridge reconstruction
reconstruct(values, 'ymax')), orbit steps 0-3 with the package's Circuit / analyse / canonical_transpose (as
qcert3/stress_ext3.py).  Own odd-graph extraction (types, missing-label sets L_i, full-met labels, m_i, A).  Per phase:
  strong forms   P1-P5 per helper with the actual m_i; H2 r_i + m_i <= 3; J1 (no two limit hubs share a label);
                 LIM strong (limit hubs carrying all q - A hub-only labels: <= 1 if A < q, label-disjoint if A = q);
                 HUB2 column deletion (no non-full helper with u > 3 - r + q - A)
  LP forms       the joint rows of hub case A = a with the phase's type counts, built by BOTH implementations
                 (gen_certs4.joint_rows closed forms, check_cases4.joint_column brute force), asserted identical on
                 every type met, lhs <= rhs
  relaxation     per helper: m_i in the interval of its type, each LP coefficient <= the helper's actual term
Part B (synthetic): qjointcheck's two-hub phases (jc_circ.synthetic on jc_geo's limit configurations, every kind:
hub-only sharing, same full-met label, different labels at a shared full helper, sub-limit (0,2)-(0,2) same-label
pairs), up to CAP phases per kind.  Realizable phases (F_joint independent) must satisfy every strong and LP row;
J1-excluded kinds (both hubs at the limit, sharing a label) must be dependent and violate the LP row LIM.
usage: PYTHONDONTWRITEBYTECODE=1 python3 stress_ext4.py [N_REAL] [CAP]
"""
import sys, json, glob, time, itertools
sys.dont_write_bytecode = True
from math import comb
from collections import Counter, defaultdict
from pathlib import Path
SPRINT = Path.home() / 'xs-campaigns/2026-11-07-sprint'
HERE = SPRINT / 'qcert4'
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(SPRINT / 'lb76/pkg_copy/source/lower_bounds/checks'))
sys.path.insert(0, str(SPRINT / 'bridge'))
import gen_certs4 as gen        # noqa: E402
import check_cases4 as chk      # noqa: E402
from stress import Circuit      # noqa: E402
from profile_real import reconstruct  # noqa: E402


def extract(C, I):
    B = set(I['B']); H = list(I['H'])
    edges = []
    for k, (a, b) in enumerate(C.gates):
        s = 32 + k
        if C.odd[a] and C.odd[b]: edges.append((a, b, s))
        elif C.odd[a] != C.odd[b]:
            o, e = (a, b) if C.odd[a] else (b, a); edges.append((o, s, e))
    bb = {}
    for p, p2, e in edges:
        if p in B and p2 in B: assert e not in bb; bb[e] = (p, p2)
    evens = [v for v in range(32, C.n) if not C.odd[v]]
    q = sum(1 for e in evens if e not in bb); assert q == I['q'], (q, I['q'])
    inc = defaultdict(list)
    for p, p2, e in edges: inc[p].append((p2, e)); inc[p2].append((p, e))
    typ = {}; L = {}
    for v in H:
        r = u = vv = 0; ms = set()
        for w, e in inc[v]:
            if w in B:
                if e in bb: r += 1
                else: u += 1; ms.add(e)
            else: vv += 1
        assert len(ms) == u, 'Lemma 4.1'
        typ[v] = (r, u, vv); L[v] = ms
    full = {v for v in H if typ[v][0] == 3}
    fullmet = set().union(*[L[f] for f in full]) if full else set()
    a = len(fullmet); assert a == sum(typ[f][1] for f in full), 'Lemma 4.5'
    m = {v: len(L[v] & fullmet) for v in H}
    return dict(ori=C.ori, q=q, a=a, typ=typ, m=m, full=full, L=L)


def evaluate(ph, stats, tag):
    """strong forms, both LP forms (asserted identical), per-helper relaxation; returns {row: lhs - rhs}."""
    q, a, typ, m, full, L, ori = ph['q'], ph['a'], ph['typ'], ph['m'], ph['full'], ph['L'], ph['ori']
    key = (0, 0, 0, ori, q, 0)
    nonfull = [v for v in typ if v not in full]
    top = chk.c3.fm_top(ori, a)
    out = {}
    out['P1'] = sum(comb(m[v], 2) for v in nonfull) + sum(comb(typ[f][1], 2) for f in full) - comb(a, 2)
    out['P2'] = sum(m[v] * (typ[v][1] - m[v]) for v in nonfull) - a * (q - a)
    out['P3'] = sum(comb(typ[v][1] - m[v], 2) for v in nonfull) - comb(q - a, 2)
    out['P4f'] = sum(1 for v in typ if (typ[v][1] if v in full else m[v]) >= 3) - chk.packing_bound(a)
    out['P4h'] = sum(1 for v in nonfull if typ[v][1] - m[v] >= 3) - chk.packing_bound(q - a)
    out['P5'] = sum(typ[v][0] * m[v] for v in nonfull) - (top - 3 * a)
    out['H2'] = max([typ[v][0] + m[v] - 3 for v in nonfull] or [-3])
    out['HUB2'] = max([typ[v][1] - (3 - typ[v][0] + q - a) for v in nonfull] or [-99])
    lim = [v for v in nonfull if typ[v][0] + m[v] == 3]
    out['J1'] = sum(1 for x, y in itertools.combinations(lim, 2) if L[x] & L[y])
    limall = [v for v in lim if typ[v][1] - m[v] == q - a]
    out['LIM'] = (sum(typ[v][1] for v in limall) - q) if a == q else (len(limall) - 1)
    if out['HUB2'] > 0:            # a type outside the case's columns: the LP rows are not defined for it
        stats['outside_columns'][tag] += 1; return out
    cnt = Counter(typ.values()); types = sorted(cnt)
    grows = gen.joint_rows(key, a, types)
    ccon = chk.joint_constants(key, a)
    assert [b for _, _, b in grows] == ccon, ('constants differ', key, a)
    for j, t in enumerate(types):
        cc = chk.joint_column(key, a, *t)
        assert [coef[j] for _, coef, _ in grows] == cc, ('joint column differs', key, a, t)
    for (name, coef, b), nm in zip(grows, chk.JOINT):
        out['LP_' + nm] = sum(c * cnt[t] for c, t in zip(coef, types)) - b
    # per-helper relaxation: m_i in the interval; LP coefficient <= actual term
    for v in nonfull:
        r, u, _ = typ[v]; mi = m[v]; e = u - mi
        I = chk.m_interval(q, a, r, u)
        assert mi in I, ('m outside its interval', tag, typ[v], mi, q, a)
        cc = chk.joint_column(key, a, *typ[v])
        actual = [comb(mi, 2), mi * e, comb(e, 2), int(mi >= 3), int(e >= 3), r * mi]
        assert all(x <= y for x, y in zip(cc[:6], actual)), ('LP coefficient above the actual term', tag, typ[v], mi, cc, actual)
        if cc[6]: assert mi == 3 - r and e == q - a, ('limit type not a limit hub carrying every hub-only label', tag, typ[v], mi)
        stats['helpers_checked'][tag] += 1
    return out


def orbit(gates, stats, tag, steps=4):
    C = Circuit(gates, 'M'); recs = []
    for step in range(steps):
        I = C.analyse(); ph = extract(C, I)
        v = evaluate(ph, stats, tag)
        recs.append(dict(step=step, ori=ph['ori'], q=ph['q'], a=ph['a'], nlim=sum(1 for x in ph['typ'] if x not in ph['full'] and ph['typ'][x][0] + ph['m'][x] == 3), viol=v))
        if step + 1 < steps: C, _ = C.canonical_transpose(I)
    return recs


def main():
    nreal = int(sys.argv[1]) if len(sys.argv) > 1 else 10 ** 9
    CAP = int(sys.argv[2]) if len(sys.argv) > 2 else 6000
    t0 = time.time(); stats = {'helpers_checked': Counter(), 'outside_columns': Counter()}
    out = {'A': {}, 'B': {}}
    recs = []
    for fn in sorted(glob.glob(str(SPRINT / 'lb76/pkg_copy/source/circuits/*.json'))):
        dd = json.load(open(fn)); g = dd['gates'] if isinstance(dd, dict) else dd
        recs.append(('ctrl', Path(fn).name, orbit(g, stats, 'ctrl')))
    d = json.load(open(SPRINT / 'bridge/profiles.json'))
    for r in [r for r in d['results'] if 'error' not in r][:nreal]:
        gates, order, info = reconstruct(r['values'], 'ymax', 0, True)
        recs.append(('real', r['tag'], orbit(gates, stats, 'real')))
    ph = [(src, p) for src, _, rs in recs for p in rs]
    print(f'Part A: {len(recs)} circuits ({sum(1 for s, _, _ in recs if s == "ctrl")} controls), {len(ph)} phases; q {sorted(Counter(p["q"] for _, p in ph).items())}; '
          f'A {sorted(Counter(p["a"] for _, p in ph).items())}; limit hubs per phase max {max(p["nlim"] for _, p in ph)}; helpers checked {dict(stats["helpers_checked"])}; {time.time()-t0:.0f}s', flush=True)
    rows = list(ph[0][1]['viol'])
    A = {}
    for nm in rows:
        for src in ('ctrl', 'real'):
            vals = [p['viol'][nm] for s, p in ph if s == src]
            A[f'{nm} {src}'] = dict(violations=sum(1 for v in vals if v > 0), min_slack=-max(vals))
        print(f'  {nm:7s}: violations ctrl {A[nm + " ctrl"]["violations"]}, real {A[nm + " real"]["violations"]}; min slack ctrl {A[nm + " ctrl"]["min_slack"]}, real {A[nm + " real"]["min_slack"]}')
    nviol_A = sum(v['violations'] for v in A.values())
    out['A'] = dict(circuits=len(recs), phases=len(ph), rows=A, violations=nviol_A, helpers_checked=dict(stats['helpers_checked']))
    # ---------------- Part B: synthetic two-hub phases (qjointcheck's builder, read only)
    sys.path.insert(0, str(SPRINT / 'qjointcheck'))
    import jc_circ                      # noqa: E402  (imports qjointcheck's lp_qjc / jc_geo; nothing is written)
    from jc_geo import Geo              # noqa: E402
    summary = {}; nviol_B = 0; n_excl_not_flagged = 0; tB = time.time()
    for ori in ('M', 'Mt'):
        Gg = Geo(ori); lim, _ = Gg.limit_configs()
        allc = [c for r in (0, 1, 2) for c in lim[r]]
        kinds = defaultdict(list); byf = defaultdict(list)
        for i, c in enumerate(allc):
            for f in c[2]: byf[f].append(i)
        for f, lst in byf.items():
            for i, j in itertools.combinations(lst, 2):
                c1, c2 = allc[i], allc[j]
                if c1[0] == c2[0]: continue
                inter = bool(Gg.PM[c1[0] ^ f] & Gg.PM[c2[0] ^ f])
                k_ = tuple(sorted(((len(c1[1]), len(c1[2])), (len(c2[1]), len(c2[2])))))
                kinds[('same-label' if inter else 'diff-labels', k_)].append(([c1, c2], ()))
        for c1, c2 in itertools.combinations(allc, 2):
            if c1[0] != c2[0] and (c1[0] ^ c2[0]) in Gg.PM:
                k_ = tuple(sorted(((len(c1[1]), len(c1[2])), (len(c2[1]), len(c2[2])))))
                kinds[('hub-only', k_)].append(([c1, c2], ((0, 1),)))
        sub = sorted({(h, (), S2) for (h, R, S) in lim[0] for S2 in itertools.combinations(S, 2)})
        byf2 = defaultdict(list)
        for i, c in enumerate(sub):
            for f in c[2]: byf2[f].append(i)
        for f, lst in byf2.items():
            for i, j in itertools.combinations(lst, 2):
                c1, c2 = sub[i], sub[j]
                if c1[0] != c2[0] and (Gg.PM[c1[0] ^ f] & Gg.PM[c2[0] ^ f]): kinds[('same-label', ((0, 2), (0, 2)))].append(([c1, c2], ()))
        for kind in sorted(kinds, key=str):
            lst = kinds[kind]; n = n_ind = 0; viol = Counter(); worst = {}; lim_flag = 0; n_dep = 0
            for configs, X in lst[:CAP]:
                ph_, ok = jc_circ.synthetic(Gg, configs, X); n += 1
                v = evaluate(ph_, stats, 'synthetic')
                if ok:
                    n_ind += 1
                    for k_, x in v.items():
                        if x > 0: viol[k_] += 1
                        worst[k_] = max(worst.get(k_, -99), x)
                else:
                    n_dep += 1
                    if v.get('LP_LIM', 0) > 0: lim_flag += 1
            both_limit = all(sum(p) == 3 for p in kind[1]) and kind[0] in ('hub-only', 'same-label')
            if both_limit:
                assert n_ind == 0, ('a J1-excluded kind has an independent phase', ori, kind)
                n_excl_not_flagged += n_dep - lim_flag
            nviol_B += sum(viol.values())
            tag = f'{ori} {kind[0]} {kind[1]}'
            summary[tag] = dict(available=len(lst), tested=n, independent=n_ind, dependent=n_dep, violations_on_independent=dict(viol),
                                tight_on_independent={k_: x for k_, x in worst.items() if x >= -1}, lp_lim_violated_on_dependent=lim_flag, j1_excluded_kind=both_limit)
            print(f'  {tag}: available {len(lst)}, tested {n}, independent {n_ind}; violations on independent {dict(viol)}; '
                  f'J1-excluded kind {both_limit}: LP LIM violated on {lim_flag} of {n_dep} dependent', flush=True)
    out['B'] = dict(kinds=summary, violations_on_independent=nviol_B, excluded_phases_not_flagged_by_LIM=n_excl_not_flagged, cap=CAP,
                    phases=sum(s['tested'] for s in summary.values()), independent=sum(s['independent'] for s in summary.values()),
                    helpers_checked=stats['helpers_checked']['synthetic'], outside_columns=dict(stats['outside_columns']), seconds=time.time() - tB)
    print(f'Part B: {out["B"]["phases"]} synthetic phases ({out["B"]["independent"]} independent), violations on independent {nviol_B}, '
          f'J1-excluded phases not flagged by LIM {n_excl_not_flagged}, phases with a type outside the case columns {dict(stats["outside_columns"])}; {time.time()-tB:.0f}s')
    json.dump(out, open(HERE / 'stress_ext4.json', 'w'), indent=1, default=str)
    ok = nviol_A == 0 and nviol_B == 0 and n_excl_not_flagged == 0
    print('STRESS EXT4', 'PASSED' if ok else 'FAILED', f': {len(recs)} circuits, {len(ph)} phases, 0 violations; {out["B"]["phases"]} synthetic phases; {time.time()-t0:.0f}s' if ok else '')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
