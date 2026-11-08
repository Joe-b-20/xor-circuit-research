#!/usr/bin/env python3
"""qhubcheck/circ_qhc.py -- re-check of Lemma H2 / row HUB2 / PK4-PK5 / C1 on real circuits with own code, plus
synthetic local configurations with m >= 1 (which no known circuit has).

Reused from elsewhere: stress.Circuit (parsing, masks, normalization asserts, canonical_transpose) and
bridge/profile_real.reconstruct (gate lists from the 88-gate value lists of bridge/profiles.json).  Everything
checked here (odd graph, labels, represented/missing, types, full helpers, full-met labels, m_i, A, the C1 family,
the mixed-vector family, the rows) is computed in this file from the definitions of PROOF.md section 4.

Part A (circuits): 13 package controls + 40 real 88-gate circuits (every 7th of the 303 of profiles.json, ymax
reconstruction), 4 orbit steps each (phase = circuit, its canonical transpose, ...).
Part B (synthetic): for the nine witnesses of qhub section 3.3 and for random maximal configurations, build the
gate-equation vectors of the local configuration (references, represented H-B equations, the two missing H-B
equations per full-met label), verify rank(gate equations) = #represented labels + m + rank(F) (the content of the
C1 elimination), that the elimination's result equals F(h, R, S), and evaluate Lemma H2 / HUB2 on the synthetic
phase.  Mutation: configurations with m = 4 - r (qreal's cap-4 hub values at r = 0) must give dependent gate equations.
usage: nice -n 10 python3 circ_qhc.py
"""
import sys, json, glob, itertools, time, random
from collections import Counter, defaultdict
from pathlib import Path
SPRINT = Path.home()/'xs-campaigns/2026-11-07-sprint'
sys.path.insert(0, str(SPRINT/'lb76/pkg_copy/source/lower_bounds/checks'))
sys.path.insert(0, str(SPRINT/'bridge'))
sys.path.insert(0, str(SPRINT/'qhubcheck'))
from stress import Circuit  # noqa: E402
from profile_real import reconstruct  # noqa: E402
from h2_check import boundary, Basis, rank_of, setup, tmask, HUBBIT, FBIT, WITNESSES, cap_and_witnesses  # noqa: E402
OUT = SPRINT/'qhubcheck'
PAIRVAL = {o: {a ^ b for a, b in itertools.combinations(boundary(o), 2)} for o in ('M', 'Mt')}

def phase(C):
    """own odd graph and all derived data for one phase"""
    n = C.n; odd = C.odd; mask = C.mask
    B = set(range(32)) | set(C.out_index); H = [v for v in range(32, n) if odd[v] and v not in C.out_index]
    edges = []                                   # (p, q, label)
    for k, (a, b) in enumerate(C.gates):
        s = 32 + k
        if odd[a] and odd[b]: edges.append((a, b, s))
        elif odd[a] != odd[b]:
            o = a if odd[a] else b; edges.append((o, s, a if not odd[a] else b))
    evens = [v for v in range(32, n) if not odd[v]]
    bb = {}
    for p, q_, l in edges:
        if p in B and q_ in B:
            assert l not in bb; bb[l] = (p, q_)
    missing = [l for l in evens if l not in bb]; q = len(missing)
    Bidx = {v: i for i, v in enumerate(sorted(B))}; Hidx = {v: i for i, v in enumerate(H)}
    at = defaultdict(list)                       # helper -> [(other end, label)]
    for p, q_, l in edges:
        if p in H: at[p].append((q_, l))
        if q_ in H: at[q_].append((p, l))
    typ = {}; rep = {}; missHB = defaultdict(list)   # label -> [(helper, boundary end)]
    for v in H:
        r = u = w = 0; rep[v] = []
        for o, l in at[v]:
            if o in B and l in bb:
                r += 1; b1, b2 = bb[l]
                assert mask[v] == mask[o] ^ mask[b1] ^ mask[b2] and o not in (b1, b2)
                rep[v].append(tuple(sorted((Bidx[o], Bidx[b1], Bidx[b2]))))
            elif o in B: u += 1; missHB[l].append((v, o))
            else: w += 1
        typ[v] = (r, u, w)
    full = [v for v in H if typ[v][0] == 3]
    # full-met labels and m_i
    fullmet = {}
    for l, lst in missHB.items():
        fs = [v for v, o in lst if v in full]
        assert len(fs) <= 1, 'Lemma 4.5 violated'
        if fs: fullmet[l] = fs[0]
    A = len(fullmet); assert A == sum(typ[v][1] for v in full)
    m = Counter()
    for l, f in fullmet.items():
        for v, o in missHB[l]:
            if v != f: m[v] += 1
    # the pair identity for every pair of helpers sharing a missing label through H-B edges, and N(h) membership for full-met
    pair_ok = 0; pair_bad = 0
    for l, lst in missHB.items():
        for (v1, o1), (v2, o2) in itertools.combinations(lst, 2):
            if (mask[v1] ^ mask[v2]) == (mask[o1] ^ mask[o2]) and (mask[v1] ^ mask[v2]) in PAIRVAL[C.ori]: pair_ok += 1
            else: pair_bad += 1
    # C1 families at non-full helpers with m_i >= 1 (vacuous on known circuits) and the surrogate mixed family
    rep_rows = [tmask(T) | (1 << (100 + Hidx[v])) for v in H for T in rep[v]]
    mixed = []
    for l, lst in missHB.items():
        (v1, o1) = lst[0]
        for (v2, o2) in lst[1:]:
            mixed.append((1 << Bidx[o1]) | (1 << Bidx[o2]) | (1 << (100 + Hidx[v1])) | (1 << (100 + Hidx[v2])))
    indep = rank_of(rep_rows + mixed) == len(rep_rows) + len(mixed)
    c1_fail = 0
    for v in H:
        if typ[v][0] <= 2 and m[v] >= 1:
            fs = [fullmet[l] for l, lst in missHB.items() if l in fullmet and any(x == v for x, _ in lst)]
            rows = [tmask(T) | HUBBIT for T in rep[v]]
            for j, f in enumerate(fs):
                rows += [tmask(T) | FBIT(j) for T in rep[f]]
                l = next(l for l, lst in missHB.items() if l in fullmet and fullmet[l] == f and any(x == v for x, _ in lst))
                ends = {o for x, o in missHB[l] if x in (v, f)}
                rows.append(sum(1 << Bidx[o] for o in ends) | FBIT(j) | HUBBIT)
            if rank_of(rows) < len(rows): c1_fail += 1
    # rows
    viol = []
    for v in H:
        r, u, w = typ[v]
        if r + m[v] > 3: viol.append(('H2', v, typ[v], m[v]))
        if r <= 2 and u > (3 - r) + (q - A): viol.append(('HUB2', v, typ[v], m[v], q, A))
        if r == 3 and m[v] > 0: viol.append(('4.5', v))
    n3u = sum(1 for v in H if typ[v][1] >= 3); cu = Counter(typ[v][1] for v in H)
    if q == 4 and n3u > 1: viol.append(('PK4', n3u))
    if q == 5 and cu[3] + 2 * cu[4] + 2 * cu[5] > 2: viol.append(('PK5', dict(cu)))
    if q == 6 and cu[3] + 3 * cu[4] + 4 * cu[5] + 4 * cu[6] > 4: viol.append(('L23-6', dict(cu)))
    if q == 7 and 2 * cu[3] + 7 * cu[4] + 12 * cu[5] + 14 * cu[6] + 14 * cu[7] > 14: viol.append(('L23-7', dict(cu)))
    # Lemma 4.6 (own check) and the pairwise-<=1 premise of Lemma 10.4
    ms = {v: {l for l, lst in missHB.items() if any(x == v for x, _ in lst)} for v in H}
    for v1, v2 in itertools.combinations(H, 2):
        if len(ms[v1] & ms[v2]) > 1: viol.append(('4.6', v1, v2))
    slack = min(((3 - typ[v][0]) + (q - A) - typ[v][1] for v in H if typ[v][0] <= 2), default=None)
    return dict(ori=C.ori, q=q, z=sum(typ[v][2] for v in H) // 2, h=len(H), n3=len(full), A=A, max_m=max(m.values(), default=0),
                hub2_slack=slack, viol=viol, mixed_indep=indep, n_mixed=len(mixed), pair_ok=pair_ok, pair_bad=pair_bad, c1_fail=c1_fail,
                types=Counter(typ.values()))

def orbit(gates, steps=4):
    C = Circuit(gates, 'M'); recs = []
    for s in range(steps):
        I = C.analyse(); rec = phase(C); rec['step'] = s; assert rec['q'] == I['q'] and rec['h'] == I['h'] and rec['z'] == I['z']
        recs.append(rec)
        if s + 1 < steps: C, _ = C.canonical_transpose(I)
    return recs

def part_a():
    t0 = time.time(); out = []
    for fn in sorted(glob.glob(str(SPRINT/'lb76/pkg_copy/source/circuits/*.json'))):
        dd = json.load(open(fn)); g = dd['gates'] if isinstance(dd, dict) else dd
        out.append(dict(tag='ctrl:' + Path(fn).name, phases=orbit(g)))
    res = [r for r in json.load(open(SPRINT/'bridge/profiles.json'))['results'] if 'error' not in r]
    picked = res[::7][:40]
    for r in picked:
        gates, order, info = reconstruct(r['values'], 'ymax', 0, True)
        out.append(dict(tag=r['tag'], phases=orbit(gates)))
    ph = [p for r in out for p in r['phases']]
    print(f'A: {len(out)} circuits ({len(picked)} real), {len(ph)} phases; q range {min(p["q"] for p in ph)}..{max(p["q"] for p in ph)}; '
          f'orientation counts {dict(Counter(p["ori"] for p in ph))}')
    print(f'   violations (H2, HUB2, 4.5, 4.6, PK4, PK5, L23): {sum(len(p["viol"]) for p in ph)}; examples {[p["viol"][:2] for p in ph if p["viol"]][:3]}')
    print(f'   max m_i: {max(p["max_m"] for p in ph)}; max A: {max(p["A"] for p in ph)}; HUB2 slack min {min(p["hub2_slack"] for p in ph if p["hub2_slack"] is not None)}')
    print(f'   pair identity h_i + h_j = b + c at shared missing labels: ok {sum(p["pair_ok"] for p in ph)}, bad {sum(p["pair_bad"] for p in ph)}')
    print(f'   mixed-vector family independent on {sum(p["mixed_indep"] for p in ph)} / {len(ph)} phases (mixed vectors per phase min {min(p["n_mixed"] for p in ph)} max {max(p["n_mixed"] for p in ph)}); '
          f'C1 failures at helpers with m >= 1: {sum(p["c1_fail"] for p in ph)} (vacuous when max m_i = 0)')
    print(f'   phases with q in 4..7: {dict(Counter(p["q"] for p in ph if 4 <= p["q"] <= 7))}; helpers with u >= 3 per phase max {max(sum(c for (r, u, v), c in p["types"].items() if u >= 3) for p in ph)}')
    json.dump([dict(tag=r['tag'], phases=[{k: (v if k != 'types' else {str(t): c for t, c in v.items()}) for k, v in p.items()} for p in r['phases']]) for r in out],
              open(OUT/'circ_qhc.json', 'w'))
    print(f'   {time.time()-t0:.0f}s', flush=True)

# ---------------- Part B: synthetic local configurations
def gate_equations(h, R, S, trip, pair, B, apex, ends):
    """Formal gate-equation vectors of the local configuration.  Coordinates: boundary i -> bit i, hub -> bit 100,
    full helper j -> bit 101+j, even label L (represented: by its pair; missing: by j) -> bits 200+.
    apex[(owner, T)] = the H-B neighbour of the triple; ends[j] = (hub's end b_j, f_j's end c_j) of P_j.
    Returns (rows, #represented labels, m)."""
    rows = []; labels = {}
    def lab(key):
        if key not in labels: labels[key] = 1 << (200 + len(labels))
        return labels[key]
    trips = [('hub', T) for T in R] + [(j, T) for j, f in enumerate(S) for T in trip[f]]
    for owner, T in trips:
        a = apex[(owner, T)]; b, c = [v for v in T if v != a]
        L = lab(('rep', tuple(sorted((b, c)))))
        rows.append(L | (1 << b) | (1 << c))                                   # B-B reference (deduplicated below)
        rows.append(L | (1 << a) | (HUBBIT if owner == 'hub' else FBIT(owner)))  # represented H-B equation
    nrep = len(labels)
    for j, (b, c) in enumerate(ends):
        L = lab(('miss', j))
        rows.append(L | (1 << b) | HUBBIT); rows.append(L | (1 << c) | FBIT(j))   # the two missing H-B equations
    rows = list(dict.fromkeys(rows))
    return rows, nrep, len(S)

def eliminate(rows):
    """the C1 elimination: add each reference to the H-B rows of its label, drop references; add the hub's missing row to
    the full helper's, drop the hub's; return the surviving rows (should be F(h, R, S))."""
    refs = {}; others = []
    for v in rows:
        L = v >> 200
        if L and bin(v & ((1 << 100) - 1)).count('1') == 2 and not (v >> 100) & ((1 << 100) - 1): refs[L] = v
        else: others.append(v)
    out = []; miss = defaultdict(list)
    for v in others:
        L = v >> 200
        if L in refs: out.append(v ^ refs[L])
        else: miss[L].append(v)
    for L, pr in miss.items():
        assert len(pr) == 2
        hubrow = next(v for v in pr if v & HUBBIT); other = next(v for v in pr if not v & HUBBIT)
        out.append(hubrow ^ other)
    assert all(v >> 200 == 0 for v in out)
    return out

def part_b():
    random.seed(7)
    for ori in ('M', 'Mt'):
        B, pair, trip, f3, full, N = setup(ori)
        confs = []
        for (o, r, h, Rm, S) in WITNESSES:
            if o == ori: confs.append((h, tuple(tuple(i for i in range(64) if (mm >> i) & 1) for mm in Rm), S, 'witness'))
        # random maximal configurations (cap = 3 - r) and cap-4 H1 configurations as mutations
        hs = list(N)
        random.shuffle(hs)
        got = {0: 0, 1: 0, 2: 0}
        for h in hs:
            reps = trip.get(h, [])
            for r in (0, 1, 2):
                if got[r] >= 15 or len(reps) < r: continue
                for R in (itertools.combinations(reps, r) if r else [()]):
                    c, ws = cap_and_witnesses(h, R, N[h], trip, pair)
                    if c == 3 - r: confs.append((h, R, list(ws[0]), 'random-max')); got[r] += 1; break
            if all(v >= 15 for v in got.values()): break
        muts = []
        for h in hs:
            c, ws = cap_and_witnesses(h, (), N[h], trip, pair, mixed=False)
            if c == 4: muts.append((h, (), list(ws[0]), 'H1-cap4-mutation'))
            if len(muts) >= 8: break
        stats = Counter()
        for h, R, S, kind in confs + muts:
            r = len(R); m = len(S)
            # one apex/end choice (any: C1 does not depend on it); random
            trips = [('hub', T) for T in R] + [(j, T) for j, f in enumerate(S) for T in trip[f]]
            apex = {(o_, T): random.choice(T) for o_, T in trips}
            ends = [pair[h ^ f] if random.random() < 0.5 else pair[h ^ f][::-1] for f in S]
            rows, nrep, mm = gate_equations(h, R, S, trip, pair, B, apex, ends)
            rk = rank_of(rows)
            Fam = sorted(eliminate(rows))
            Fexp = sorted([tmask(T) | HUBBIT for T in R] + [tmask(T) | FBIT(j) for j, f in enumerate(S) for T in trip[f]]
                          + [tmask(pair[h ^ f]) | FBIT(j) | HUBBIT for j, f in enumerate(S)])
            same = Fam == Fexp
            rkF = rank_of(Fexp)
            identity = (rk == nrep + mm + rkF)
            indep_gates = (rk == len(rows))
            # synthetic phase: hub (r, m, 0), full helpers (3, 1, 0); q = m missing labels, A = m
            q = m; A = m
            h2 = r + m <= 3; hub2 = m <= (3 - r) + (q - A)
            stats[(kind, r, 'gates independent' if indep_gates else 'gates DEPENDENT', 'H2 ok' if h2 else 'H2 VIOLATED', 'HUB2 ok' if hub2 else 'HUB2 VIOLATED',
                   'elimination = F' if same else 'elimination != F', 'rank identity' if identity else 'rank identity FAILS')] += 1
        print(f'B ({ori}): synthetic local configurations:')
        for k, c in sorted(stats.items(), key=str): print(f'   {c:3d} x {k}')

if __name__ == '__main__':
    part_a(); part_b()
