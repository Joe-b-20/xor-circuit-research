#!/usr/bin/env python3
"""qjointcheck/jc_geo.py -- own implementation of the finite geometry behind finite fact J1 (qjoint/REPORT.md
section 3) and of the joint family F_joint (section 2).  Nothing is imported from qjoint/qj_geo.py or
qhub/hub2.py; the boundary is parsed from the repository matrix file and cross-checked once against
stress.BOUNDARY.  Coordinates (python ints over GF(2)):
    bits 0..63     boundary B[0..63]  (B[0..31] inputs, B[32..63] rows of M / columns of M)
    bits 64..71    hub coordinates H_0..H_7
    bits 72+j      full helper with global index j (j < 112)
Elimination: incremental lowest-set-bit pivots (qj_geo pivots on the highest bit).

Families:
    full(f)            = { H_f + T : T one of the three boundary triples of the full value f }
    hub(k, h, R, S)    = { H_k + T : T in R } u { H_k + H_f + P(h + f) : f in S }           (P = the unique pair)
    F_joint(configs,X) = union of full(f) over all f in any S_k, union of hub(k, .), plus
                         { H_k + H_k' + P(h_k + h_k') : (k, k') in X }.
A LIMIT configuration is (h, R, S) with |R| = r <= 2, |S| = 3 - r, F(h, R, S) = full(S) u hub(h, R, S) independent.

Modes:  python3 jc_geo.py j1 [M,Mt]        finite fact J1 over all pairs of limit configurations (both sharing kinds),
                                            plus the realizable limit-limit kinds and an H2 spot check
        python3 jc_geo.py partners [M,Mt]  the full partner enumeration of qj_limit.py (all partner classes <= 3)
"""
import sys, json, time, itertools
from collections import defaultdict, Counter
from pathlib import Path
REPO = Path.home()/'xor-circuit-research'
OUT = Path.home()/'xs-campaigns/2026-11-07-sprint/qjointcheck'

def HB(k): return 1 << (64 + k)
def FB(j): return 1 << (72 + j)

def read_boundary(ori):
    lines = [l.split() for l in open(REPO/'circuits/aes-mixcolumns/aes-mixcolumns.mat.txt') if l.strip()]
    assert lines[1] == ['32', '32']
    rows = [[int(x) for x in l] for l in lines[2:34]]
    assert len(rows) == 32 and all(len(r) == 32 for r in rows)
    if ori == 'M':
        masks = [sum(b << j for j, b in enumerate(r)) for r in rows]
    else:
        masks = [sum(rows[i][j] << i for i in range(32)) for j in range(32)]
    B = [1 << i for i in range(32)] + masks
    assert len(set(B)) == 64 and all(bin(v).count('1') % 2 for v in B)
    return B

def rank(vs):
    piv = {}
    r = 0
    for v in vs:
        while v:
            lb = v & -v
            p = piv.get(lb)
            if p is None:
                piv[lb] = v; r += 1; break
            v ^= p
    return r

def indep(vs): return rank(vs) == len(vs)

class Geo:
    def __init__(self, ori):
        self.ori = ori
        B = read_boundary(ori); self.B = B; self.Bset = set(B)
        try:
            sys.path.insert(0, str(Path.home()/'xs-campaigns/2026-11-07-sprint/lb76/pkg_copy/source/lower_bounds/checks'))
            from stress import BOUNDARY
            assert BOUNDARY[ori] == B, 'boundary differs from stress.BOUNDARY'
        except ImportError:
            print('(stress not importable, cross-check skipped)')
        PM = {}
        for i, j in itertools.combinations(range(64), 2):
            v = B[i] ^ B[j]; assert v not in PM, 'F2 fails'; PM[v] = (1 << i) | (1 << j)
        assert len(PM) == 2016
        self.PM = PM
        trip = defaultdict(list)
        for i, j, k in itertools.combinations(range(64), 3):
            trip[B[i] ^ B[j] ^ B[k]].append((1 << i) | (1 << j) | (1 << k))
        self.trip = trip
        self.f3 = Counter(len(t) for t in trip.values())
        self.fulls = sorted(v for v, t in trip.items() if len(t) == 3)
        self.fidx = {f: j for j, f in enumerate(self.fulls)}
        N = defaultdict(set)
        for f in self.fulls:
            for p in PM:
                h = f ^ p
                if h not in self.Bset: N[h].add(f)
        self.N = {h: sorted(s) for h, s in N.items()}
        assert all(bin(h).count('1') % 2 for h in self.N)

    def full(self, f): return [T | FB(self.fidx[f]) for T in self.trip[f]]
    def hub(self, k, h, R, S): return [T | HB(k) for T in R] + [HB(k) | FB(self.fidx[f]) | self.PM[h ^ f] for f in S]
    def joint(self, configs, X=()):
        vs = []
        for f in sorted({f for _, _, S in configs for f in S}): vs += self.full(f)
        for k, (h, R, S) in enumerate(configs): vs += self.hub(k, h, R, S)
        for k, k2 in X: vs.append(HB(k) | HB(k2) | self.PM[configs[k][0] ^ configs[k2][0]])
        return vs
    def single_ok(self, h, R, S): return indep(self.joint([(h, R, S)]))

    def limit_configs(self):
        """all (h, R, S) with |R| = r, |S| = 3 - r, F(h, R, S) independent, r = 0, 1, 2; plus an H2 spot check:
        no configuration with |S| = 4 - r is independent at a value owning a limit configuration (hereditary)."""
        lim = {0: [], 1: [], 2: []}; h2viol = 0
        for h, Nh in self.N.items():
            reps = self.trip.get(h, [])
            for r in (0, 1, 2):
                if len(reps) < r or len(Nh) < 3 - r: continue
                found = False
                for R in (itertools.combinations(reps, r) if r else [()]):
                    for S in itertools.combinations(Nh, 3 - r):
                        if self.single_ok(h, R, S): lim[r].append((h, R, S)); found = True
                if found and len(Nh) >= 4 - r:
                    for R in (itertools.combinations(reps, r) if r else [()]):
                        for S in itertools.combinations(Nh, 4 - r):
                            if self.single_ok(h, R, S): h2viol += 1
        return lim, h2viol

def cls(c): return (len(c[1]), len(c[2]))

def mode_j1(G):
    t0 = time.time()
    lim, h2viol = G.limit_configs()
    print(f'{G.ori}: F3 {dict(G.f3)}; {len(G.fulls)} full values; {len(G.N)} hub values with N(h) nonempty; '
          f'limit configurations r=0/1/2: {len(lim[0])} / {len(lim[1])} / {len(lim[2])} at '
          f'{len({c[0] for c in lim[0]})} / {len({c[0] for c in lim[1]})} / {len({c[0] for c in lim[2]})} values; '
          f'H2 violations (|S| = 4 - r independent): {h2viol}; {time.time()-t0:.0f}s', flush=True)
    allc = [c for r in (0, 1, 2) for c in lim[r]]
    res = dict(ori=G.ori, n_limit={r: len(lim[r]) for r in lim}, h2viol=h2viol)
    # ---- (A) hub-only sharing between two limit hubs: h1 + h2 in PV, mixed vector added; NO 4.6 pre-skip
    hub_only = Counter(); hub_only_skipdep = Counter(); ex_ho = {}
    pv_pairs_r2_values = 0
    r2vals = sorted({c[0] for c in lim[2]})
    for a, b in itertools.combinations(r2vals, 2):
        if (a ^ b) in G.PM: pv_pairs_r2_values += 1
    nA = 0
    for c1, c2 in itertools.combinations(allc, 2):
        h1, R1, S1 = c1; h2, R2, S2 = c2
        if h1 == h2 or (h1 ^ h2) not in G.PM: continue
        nA += 1
        key = tuple(sorted((cls(c1), cls(c2))))
        ok = indep(G.joint([c1, c2], X=[(0, 1)]))
        hub_only[(key, ok)] += 1
        # would qj_limit's pre-skip (a common full helper with intersecting pairs) have skipped it?  those must be dependent
        if any(G.PM[h1 ^ g] & G.PM[h2 ^ g] for g in set(S1) & set(S2)):
            hub_only_skipdep[ok] += 1
        if ok and key not in ex_ho: ex_ho[key] = (c1, c2)
    print(f'{G.ori}: (A) hub-only sharing, pairs of limit configurations with h1 + h2 in PV: {nA}; independent by class pair: '
          f'{ {k: v for (k, ok), v in sorted(hub_only.items(), key=str) if ok} }; dependent: { {k: v for (k, ok), v in sorted(hub_only.items(), key=str) if not ok} }; '
          f'pairs qj_limit would pre-skip: {dict(hub_only_skipdep)} (independent ones must be 0); '
          f'r = 2 limit VALUES {len(r2vals)}, value pairs with XOR in PV {pv_pairs_r2_values}; {time.time()-t0:.0f}s', flush=True)
    res['A_hub_only'] = {str(k): v for k, v in hub_only.items()}; res['A_pairs'] = nA; res['A_r2_values'] = len(r2vals); res['A_r2_pv_pairs'] = pv_pairs_r2_values
    # ---- (B) sharing a full helper f: per common f (qj_pairs counts per f), intersecting pairs = same-label possible,
    #          disjoint pairs = different labels (realizable kinds); also different labels + hub-only label
    same = Counter(); diff = Counter(); diffho = Counter(); ex_same = {}; ex_diff = {}; nB = 0
    byf = defaultdict(list)
    for i, c in enumerate(allc):
        for f in c[2]: byf[f].append(i)
    for f, lst in byf.items():
        for i, j in itertools.combinations(lst, 2):
            c1 = allc[i]; c2 = allc[j]; h1, R1, S1 = c1; h2, R2, S2 = c2
            if h1 == h2: continue
            nB += 1
            key = tuple(sorted((cls(c1), cls(c2))))
            inter = bool(G.PM[h1 ^ f] & G.PM[h2 ^ f])
            vs = G.joint([c1, c2])
            ok = indep(vs)
            if inter:
                same[(key, ok)] += 1
                if ok and key not in ex_same: ex_same[key] = (c1, c2, f)
            else:
                diff[(key, ok)] += 1
                if ok and key not in ex_diff: ex_diff[key] = (c1, c2, f)
                if (h1 ^ h2) in G.PM:
                    ok2 = indep(vs + [HB(0) | HB(1) | G.PM[h1 ^ h2]])
                    diffho[(key, ok2)] += 1
    def show(cn):
        return ('indep ' + str({k: v for (k, ok), v in sorted(cn.items(), key=str) if ok}) + ' dep ' +
                str({k: v for (k, ok), v in sorted(cn.items(), key=str) if not ok}))
    print(f'{G.ori}: (B) pairs of limit configurations sharing a full helper (counted per common f): {nB}', flush=True)
    print(f'{G.ori}:   intersecting pairs at f (same label possible): {show(same)}')
    print(f'{G.ori}:   disjoint pairs at f (different labels): {show(diff)}')
    print(f'{G.ori}:   different labels + shared hub-only label: {show(diffho)}; {time.time()-t0:.0f}s', flush=True)
    res['B_same'] = {str(k): v for k, v in same.items()}; res['B_diff'] = {str(k): v for k, v in diff.items()}; res['B_diffho'] = {str(k): v for k, v in diffho.items()}
    j1_ho = sum(v for (k, ok), v in hub_only.items() if ok) == 0
    j1_same = sum(v for (k, ok), v in same.items() if ok) == 0
    print(f'{G.ori}: J1 hub-only part {"HOLDS" if j1_ho else "FAILS"}; J1 full-met (same label) part {"HOLDS" if j1_same else "FAILS"}', flush=True)
    res['J1_hub_only'] = j1_ho; res['J1_same_label'] = j1_same
    fmt = lambda c: dict(h=hex(c[0]), R=[hex(T) for T in c[1]], S=[hex(f) for f in c[2]])
    res['examples_diff'] = {str(k): dict(c1=fmt(v[0]), c2=fmt(v[1]), f=hex(v[2])) for k, v in ex_diff.items()}
    # ---- (C) 4.6 configurations are automatically dependent: two shared labels (intersecting at two common f's,
    #          or hub-only + intersecting at a common f) -- checked on the pairs above
    n46 = 0; n46dep = 0
    for c1, c2 in itertools.combinations(allc, 2):
        h1, R1, S1 = c1; h2, R2, S2 = c2
        if h1 == h2: continue
        common = [g for g in set(S1) & set(S2) if G.PM[h1 ^ g] & G.PM[h2 ^ g]]
        if len(common) >= 2:
            n46 += 1; n46dep += (not indep(G.joint([c1, c2])))
        if len(common) >= 1 and (h1 ^ h2) in G.PM:
            n46 += 1; n46dep += (not indep(G.joint([c1, c2], X=[(0, 1)])))
    print(f'{G.ori}: (C) Lemma-4.6 configurations among limit pairs: {n46}, of them dependent as predicted: {n46dep}; {time.time()-t0:.0f}s', flush=True)
    res['C_46'] = [n46, n46dep]
    json.dump(res, open(OUT/f'jc_j1_{G.ori}.json', 'w'), indent=1)
    return lim

def partner_configs(G, h2, forced=None):
    """all (R2, S2), |R2| = r2 <= 2, 1 <= r2 + |S2|, |S2| <= 3 - r2, F(h2, R2, S2) independent (hereditary DFS on S2),
    with forced in S2 when given."""
    reps = G.trip.get(h2, []); Nh = G.N.get(h2, [])
    if forced is not None and forced not in Nh: return []
    out = []
    for r2 in range(0, 3):
        if r2 > len(reps): break
        for R2 in (itertools.combinations(reps, r2) if r2 else [()]):
            start = [forced] if forced is not None else []
            if start and not G.single_ok(h2, R2, tuple(start)): continue
            cands = [f for f in Nh if f != forced]
            def dfs(i, S2):
                if r2 + len(S2) >= 1: out.append((R2, tuple(S2)))
                if len(S2) >= 3 - r2: return
                for j in range(i, len(cands)):
                    S3 = S2 + [cands[j]]
                    if G.single_ok(h2, R2, tuple(S3)): dfs(j + 1, S3)
            dfs(0, list(start))
    return out

def mode_partners(G, lim):
    """qj_limit.py's enumeration redone: for every limit configuration, every partner (any class <= 3), both sharing
    kinds, NO pre-skip; histogram of the largest independent partner class and the independent partner classes."""
    t0 = time.time(); res = {}
    for r in (0, 1, 2):
        hist_a = Counter(); hist_b = Counter(); cls_a = Counter(); cls_b = Counter(); ntest = 0
        for (h, R, S) in lim[r]:
            best_a = best_b = 0
            for p in G.PM:
                h2 = h ^ p
                if h2 in G.Bset or h2 == h: continue
                for (R2, S2) in partner_configs(G, h2):
                    ntest += 1
                    if indep(G.joint([(h, R, S), (h2, R2, S2)], X=[(0, 1)])):
                        c = len(R2) + len(S2); cls_a[(len(R2), len(S2))] += 1; best_a = max(best_a, c)
            for f in S:
                P = G.PM[h ^ f]
                for ci in range(64):
                    if not (P >> ci) & 1: continue
                    l = f ^ G.B[ci]
                    for bi in range(64):
                        if (P >> bi) & 1: continue
                        h2 = l ^ G.B[bi]
                        if h2 in G.Bset or h2 == h: continue
                        for (R2, S2) in partner_configs(G, h2, forced=f):
                            ntest += 1
                            if indep(G.joint([(h, R, S), (h2, R2, S2)])):
                                c = len(R2) + len(S2); cls_b[(len(R2), len(S2))] += 1; best_b = max(best_b, c)
            hist_a[best_a] += 1; hist_b[best_b] += 1
        print(f'{G.ori} r={r}: {len(lim[r])} limit configurations, {ntest} joint tests; largest independent partner class: '
              f'hub-only {dict(sorted(hist_a.items()))}, same-label {dict(sorted(hist_b.items()))}; independent partner classes: '
              f'hub-only {dict(sorted(cls_a.items()))}, same-label {dict(sorted(cls_b.items()))}; {time.time()-t0:.0f}s', flush=True)
        res[r] = dict(best_hubonly=dict(hist_a), best_samelabel=dict(hist_b), cls_hubonly={str(k): v for k, v in cls_a.items()},
                      cls_samelabel={str(k): v for k, v in cls_b.items()}, ntest=ntest)
    j1 = all(max(list(res[r]['best_hubonly']) + list(res[r]['best_samelabel'])) <= 2 for r in res)
    print(f'{G.ori}: partner enumeration: J1 {"HOLDS" if j1 else "FAILS"}')
    json.dump(dict(ori=G.ori, J1=j1, res=res), open(OUT/f'jc_partners_{G.ori}.json', 'w'), indent=1)

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'j1'
    oris = sys.argv[2].split(',') if len(sys.argv) > 2 else ['M', 'Mt']
    for o in oris:
        G = Geo(o)
        lim = mode_j1(G)
        if mode == 'partners': mode_partners(G, lim)
