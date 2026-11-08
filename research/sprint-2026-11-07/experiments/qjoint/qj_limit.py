#!/usr/bin/env python3
"""qjoint/qj_limit.py -- which helpers can share a missing label with a LIMIT hub (a non-full helper with r + m = 3,
i.e. m = 3 - r full-met labels, the maximum of Lemma H2)?

For every limit configuration (h, R, S) (|R| = r, |S| = 3 - r, F(h,R,S) independent; the attaining values of finite
fact H2) and every partner helper value h' (odd, non-boundary) with partner configuration (R', S'), |S'| = m' <= 3 - r':
  (a) hub-only sharing: h' = h + p, p in PV (the shared label is l = h + b = h' + b', {b, b'} = P(p)); joint family
      F(h,R,S) u F(h',R',S') u {H + H' + P(p)}; by Lemma 4.6 the two share no other label, so common full helpers
      g in S n S' must be met at different labels (pairs P(h+g), P(h'+g) disjoint);
  (b) same-label sharing: the partner meets the same full-met label l = f + c (f in S, c in P(h+f)) through its own end
      b' (h' = l + b', b' not in P(h+f)); joint family F(h,R,S) u F(h',R',S'), f in S', other common g met at different
      labels; no hub-only mixed vector (Lemma 4.6).
Partners of class r' + m' = 1 (a single private vector, or none) are included for completeness.  Output: for each
orientation and limit class (r, 3-r) the histogram over limit configurations of the largest partner class r' + m'
admitting an independent joint family, by sharing mode, and the counts behind finite fact J1 (REPORT.md section 3).
usage: python3 qj_limit.py [M,Mt]
"""
import sys, json, time, itertools
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, str(Path.home()/'xs-campaigns/2026-11-07-sprint/qjoint'))
from qj_geo import Geo, FULLC, HUBC, independent  # noqa: E402
OUT = Path.home()/'xs-campaigns/2026-11-07-sprint/qjoint'

def hub_family(G, k, h, R, S):
    return [T | HUBC(k) for T in R] + [HUBC(k) | FULLC(G.fidx[f]) | G.pairmask[h ^ f] for f in S]

def partner_configs(G, h2, forced_f=None, maxm=3):
    """all (r', R', S') with F(h2,R',S') independent, |S'| <= 3 - r', forced_f in S' if given; hereditary DFS on S'."""
    reps = G.trip.get(h2, []); Nh = G.N.get(h2, [])
    out = []
    for r2 in range(0, 3):
        if r2 > len(reps): break
        for R2 in (itertools.combinations(reps, r2) if r2 else [()]):
            base = [T | HUBC(1) for T in R2]
            cands = [f for f in Nh if f != forced_f]
            start = [forced_f] if forced_f is not None else []
            if forced_f is not None and forced_f not in Nh: continue
            def vs_of(S2):
                vs = list(base)
                for f in S2: vs += G.full_vectors(f); vs.append(HUBC(1) | FULLC(G.fidx[f]) | G.pairmask[h2 ^ f])
                return vs
            def dfs(i, S2):
                if start or S2 or True:
                    if len(S2) + r2 >= 1 and (forced_f is None or forced_f in S2):
                        out.append((r2, R2, tuple(S2)))
                if len(S2) >= min(maxm, 3 - r2): return
                for j in range(i, len(cands)):
                    S3 = S2 + [cands[j]]
                    if independent(vs_of(S3)): dfs(j + 1, S3)
            if start and not independent(vs_of(start)): continue
            dfs(0, list(start))
    # r2 = 0, S2 = () (class 0) is skipped by the len >= 1 test
    return out

def main(ori):
    t0 = time.time()
    G = Geo(ori); cap = G.load_cap()
    res = {}
    for r in (0, 1, 2):
        lim_vals = sorted(h for h, c in cap[r].items() if c == 3 - r)
        configs = []
        for h in lim_vals:
            for R in (itertools.combinations(G.trip[h], r) if r else [()]):
                for S in itertools.combinations(G.N[h], 3 - r):
                    vs = [v for f in S for v in G.full_vectors(f)] + hub_family(G, 0, h, R, S)
                    if independent(vs): configs.append((h, R, S))
        print(f'{ori} r={r}: {len(lim_vals)} limit values, {len(configs)} limit configurations; {time.time()-t0:.0f}s', flush=True)
        hist_a = Counter(); hist_b = Counter(); cls_a = Counter(); cls_b = Counter(); ex = {}
        ntest = 0
        for (h, R, S) in configs:
            base = [v for f in S for v in G.full_vectors(f)] + hub_family(G, 0, h, R, S)
            fullS = set(S)
            best_a = 0; best_b = 0
            # (a) hub-only sharing
            for p in G.pairmask:
                h2 = h ^ p
                if h2 in G.Bset or h2 == h: continue
                for (r2, R2, S2) in partner_configs(G, h2):
                    # Lemma 4.6: no second shared label: common full helpers at different labels
                    if any(G.pairmask[h ^ g] & G.pairmask[h2 ^ g] for g in S2 if g in fullS): continue
                    vs = list(base) + [v for g in S2 if g not in fullS for v in G.full_vectors(g)] + hub_family(G, 1, h2, R2, S2)
                    vs.append(HUBC(0) | HUBC(1) | G.pairmask[p])
                    ntest += 1
                    if independent(vs):
                        c = r2 + len(S2); cls_a[(r2, len(S2))] += 1
                        if c > best_a: best_a = c; ex[('a', r, c)] = dict(h=hex(h), R=[hex(T) for T in R], S=[hex(f) for f in S], h2=hex(h2), r2=r2, S2=[hex(g) for g in S2])
            # (b) same-label sharing
            for f in S:
                P = G.pairmask[h ^ f]
                for c_end in [b for b in range(64) if (P >> b) & 1]:
                    cmask = G.B[c_end]; l = f ^ cmask
                    for b2 in range(64):
                        if (P >> b2) & 1: continue
                        h2 = l ^ G.B[b2]
                        if h2 in G.Bset or h2 == h: continue
                        for (r2, R2, S2) in partner_configs(G, h2, forced_f=f):
                            if any(G.pairmask[h ^ g] & G.pairmask[h2 ^ g] for g in S2 if g in fullS and g != f): continue
                            vs = list(base) + [v for g in S2 if g not in fullS for v in G.full_vectors(g)] + hub_family(G, 1, h2, R2, S2)
                            ntest += 1
                            if independent(vs):
                                c = r2 + len(S2); cls_b[(r2, len(S2))] += 1
                                if c > best_b: best_b = c; ex[('b', r, c)] = dict(h=hex(h), R=[hex(T) for T in R], S=[hex(f) for f in S], f=hex(f), h2=hex(h2), r2=r2, S2=[hex(g) for g in S2])
            hist_a[best_a] += 1; hist_b[best_b] += 1
        print(f'{ori} r={r}: {ntest} joint tests; largest partner class (r2 + m2) per limit configuration: hub-only sharing {dict(sorted(hist_a.items()))}, '
              f'same-label sharing {dict(sorted(hist_b.items()))}; independent partner classes (r2, m2): hub-only {dict(sorted(cls_a.items()))}, same-label {dict(sorted(cls_b.items()))}; {time.time()-t0:.0f}s', flush=True)
        res[r] = dict(limit_values=len(lim_vals), configs=len(configs), best_hubonly=dict(hist_a), best_samelabel=dict(hist_b),
                      classes_hubonly={str(k): v for k, v in cls_a.items()}, classes_samelabel={str(k): v for k, v in cls_b.items()},
                      examples={str(k): v for k, v in ex.items()})
    j1 = all(max(list(res[r]['best_hubonly']) + list(res[r]['best_samelabel'])) <= 2 for r in res)
    print(f'{ori}: J1 (no limit hub shares a missing label with another limit hub, r2 + m2 = 3): {"HOLDS" if j1 else "FAILS"}')
    json.dump(dict(ori=ori, J1=j1, res=res), open(OUT/f'limit_{ori}.json', 'w'), indent=1)

if __name__ == '__main__':
    for o in (sys.argv[1].split(',') if len(sys.argv) > 1 else ['M', 'Mt']): main(o)
