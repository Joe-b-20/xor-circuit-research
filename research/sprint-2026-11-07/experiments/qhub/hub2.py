#!/usr/bin/env python3
"""hub2.py -- refined hub capacity (qhub, 2026-11-07).

Setting (PROOF.md sections 4, 10; qreal/REPORT.md section 1).  A helper i of type (r, u, v) with r <= 2 whose
missing labels l_1..l_m (edges i-b_j, l_j = h + b_j) are *full-met* (l_j also has an H-B edge f_j-c_j at a full
helper f_j, l_j = f_j + c_j) forces h + f_j = b_j + c_j to be a boundary-pair value P_j (pair determined by F2),
so f_j in N(h) = { f full : h + f in PV }, the f_j distinct (Lemma 4.6) and P_j pairwise disjoint.

Conditions enumerated here for a candidate (h, r, R, S), R = the r represented triples of the hub (subset of the
triple representations of h), S = {f_1..f_m} subset of N(h):

 C1 [proved]  the family  F = {H_f + T : f in S, T triple of f}  u  {H_i + T : T in R}  u
              {H_i + H_f + B_b + B_c : f in S, {b,c} = P_f}  is linearly independent (rank 4m + r).
              Proof: the B-B reference equations, the represented H-B equations of the f's and of i, and the
              missing H-B equations i-b_j and f_j-c_j are gate equations, hence independent (Lemma 1.1 / proof
              of Lemma 4.4); add each reference to its H-B equations and drop the references (E_l of a
              represented label then occurs only in its reference); replace f_j's missing equation by the sum of
              the two missing equations of l_j and drop the hub's (E_{l_j} then occurs only there).  Invertible
              operations and deletions of rows carrying a private coordinate preserve independence.
              (H1 of qreal used only the 3m vectors H_f + T.)
 C3 [proved]  Lemma O1 (qreal section 2): every full helper owns >= 2 outputs in two distinct triples, the hub
              owns >= r - 1 outputs in distinct represented triples, all owned outputs distinct: a flow problem.
 X  [proved lower bound]  the configuration's own edges give every boundary vertex v a degree deg(v); the
              phase has d_v >= deg(v), so E_B(phase) = sum_B (d_v - 2)_+ >= X := min over apex choices of
              sum_B (deg(v) - 2)_+.  (Each (f, T) contributes one H-B edge at its apex and the B-B edge of the
              other two elements; two triples sharing a pair may share that B-B edge; the missing edges i-b_j,
              f_j-c_j are distinct H-B edges.)  On a tail pair with shortfall sigma, E_B,e + E_B,o <= sigma
              (two-phase identity, qreal section 5), so X <= sigma is necessary.

Output: for each orientation and r = 0, 1, 2: cap_r(h) under C1 (+C3), histogram over h, and the maximum m
attainable with X <= sigma for sigma = 0..3 and unrestricted; witnesses; JSON tables for the LP.
usage: python3 hub2.py [M,Mt] [--no-o1]
"""
import sys, json, itertools, time
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, str(Path.home()/'xs-campaigns/2026-11-07-sprint/lb76/pkg_copy/source/lower_bounds/checks'))
from stress import BOUNDARY  # noqa: E402
OUT = Path.home()/'xs-campaigns/2026-11-07-sprint/qhub'
HUB = 1 << 64            # coordinate of the hub helper
def FC(j): return 1 << (65 + j)   # coordinate of full helper j
INF = 99

class Basis:
    """incremental GF(2) basis with undo"""
    def __init__(self): self.piv = {}; self.stack = []
    def add(self, v):
        while v:
            hb = v.bit_length() - 1
            if hb in self.piv: v ^= self.piv[hb]
            else: self.piv[hb] = v; self.stack.append(hb); return True
        return False
    def mark(self): return len(self.stack)
    def undo(self, m):
        while len(self.stack) > m: del self.piv[self.stack.pop()]

def bits(m):
    while m:
        b = m & -m; yield b.bit_length() - 1; m ^= b

def maxflow_o1(fulltrips, hubtrips, r):
    """O1 feasibility: each full helper needs 2 of its 3 triples matched to distinct outputs inside the triple,
    the hub needs r - 1 of its r triples; outputs are boundary indices 32..63.  Simple augmenting-path flow."""
    need = [(2, ts) for ts in fulltrips] + ([(r - 1, hubtrips)] if r >= 2 else [])
    # nodes: 's', ('h',k), ('t',k,t), ('o',o), 'z'
    cap = defaultdict(lambda: defaultdict(int))
    total = 0
    for k, (nd, ts) in enumerate(need):
        if nd <= 0: continue
        total += nd
        cap['s'][('h', k)] += nd
        for ti, T in enumerate(ts):
            cap[('h', k)][('t', k, ti)] += 1
            for o in bits(T):
                if o >= 32:
                    cap[('t', k, ti)][('o', o)] += 1
                    cap[('o', o)]['z'] = 1
    flow = 0
    while flow < total:
        # BFS augmenting path
        prev = {'s': None}; dq = ['s']; found = False
        while dq and not found:
            u = dq.pop(0)
            for w, c in cap[u].items():
                if c > 0 and w not in prev:
                    prev[w] = u; dq.append(w)
                    if w == 'z': found = True; break
        if not found: return False
        w = 'z'
        while prev[w] is not None:
            u = prev[w]; cap[u][w] -= 1; cap[w][u] += 1; w = u
        flow += 1
    return True

def excess(trips, pairs, exact_limit=7):
    """minimal boundary excess X over apex choices.  trips: list of triple masks (full helpers' 3m + hub's r);
    pairs: the m disjoint pair masks P_j (each gives one H-B edge at both ends)."""
    deg = Counter()
    for T in trips:
        for v in bits(T): deg[v] += 1
    for P in pairs:
        for v in bits(P): deg[v] += 1
    # triples sharing exactly two elements may share the B-B edge of that pair (when both choose the third as apex)
    share = [(a, b) for a, b in itertools.combinations(range(len(trips)), 2) if bin(trips[a] & trips[b]).count('1') == 2]
    if not share:
        return sum(max(0, d - 2) for d in deg.values()), True
    inv = sorted({i for ab in share for i in ab})
    if len(inv) > exact_limit:
        corr = Counter()
        for a, b in share:
            for v in bits(trips[a] & trips[b]): corr[v] += 1
        return sum(max(0, deg[v] - corr[v] - 2) for v in deg), False
    best = INF
    for apex in itertools.product(*[list(bits(trips[i])) for i in inv]):
        chosen = {}
        for i, a in zip(inv, apex): chosen[i] = trips[i] & ~(1 << a)
        d2 = Counter(deg)
        seen = {}
        for i in inv:
            P = chosen[i]
            if P in seen:           # shared B-B edge: counted twice in deg, is one edge
                for v in bits(P): d2[v] -= 1
            else: seen[P] = i
        best = min(best, sum(max(0, d - 2) for d in d2.values()))
    return best, True

def analyse(ori, use_o1=True):
    t0 = time.time()
    B = BOUNDARY[ori]; Bset = set(B)
    trip = defaultdict(list)
    for i, j, k in itertools.combinations(range(64), 3):
        trip[B[i] ^ B[j] ^ B[k]].append((1 << i) | (1 << j) | (1 << k))
    full = {v: ts for v, ts in trip.items() if len(ts) == 3}
    fulls = sorted(full)
    pairmask = {}
    for i, j in itertools.combinations(range(64), 2): pairmask[B[i] ^ B[j]] = (1 << i) | (1 << j)
    assert len(pairmask) == 2016
    N = defaultdict(list)
    for f in fulls:
        for p, pm in pairmask.items(): N[f ^ p].append(f)
    N = {h: sorted(fs) for h, fs in N.items() if h not in Bset}
    print(f'{ori}: {len(fulls)} full values, {len(N)} odd non-boundary h with N(h) nonempty; {time.time()-t0:.1f}s', flush=True)
    results = {}     # (r) -> dict h -> record
    hist = {}
    for r in (0, 1, 2):
        rec = {}
        cnt_h = 0
        for h, fs in N.items():
            reps = trip.get(h, [])
            if len(reps) < r or (r == 0 and False): continue
            if r >= 1 and not reps: continue
            Rchoices = list(itertools.combinations(reps, r)) if r else [()]
            best = dict(c1=0, c13=0, sig={s: 0 for s in range(4)}, sig_c1={s: 0 for s in range(4)}, wit={}, Xmin_by_m={})
            for R in Rchoices:
                basis = Basis()
                for T in R: assert basis.add(T | HUB)
                m0 = basis.mark()
                # DFS over subsets of fs (index-increasing), independence is hereditary
                def dfs(start, S):
                    m = len(S)
                    if m:
                        trips = [T for f in S for T in full[f]] + list(R)
                        pairs = [pairmask[h ^ f] for f in S]
                        X, exact = excess(trips, pairs)
                        o1 = maxflow_o1([full[f] for f in S], list(R), r) if use_o1 else True
                        if m > best['c1']: best['c1'] = m
                        if o1 and m > best['c13']: best['c13'] = m; best['wit'] = dict(R=[hex(T) for T in R], S=[hex(f) for f in S], X=X, exact=exact)
                        for s in range(4):
                            if X <= s:
                                if m > best['sig_c1'][s]: best['sig_c1'][s] = m
                                if o1 and m > best['sig'][s]:
                                    best['sig'][s] = m; best['wit%d' % s] = dict(R=[hex(T) for T in R], S=[hex(f) for f in S], X=X, exact=exact)
                        best['Xmin_by_m'][m] = min(best['Xmin_by_m'].get(m, INF), X)
                    for idx in range(start, len(fs)):
                        f = fs[idx]; j = m
                        mk = basis.mark(); ok = True
                        for T in full[f]:
                            if not basis.add(T | FC(j)): ok = False; break
                        if ok and not basis.add(HUB | FC(j) | pairmask[h ^ f]): ok = False
                        if ok: dfs(idx + 1, S + [f])
                        basis.undo(mk)
                dfs(0, [])
                basis.undo(m0)
            rec[h] = best
            cnt_h += 1
        results[r] = rec
        hc1 = Counter(b['c1'] for b in rec.values()); hc13 = Counter(b['c13'] for b in rec.values())
        hs = {s: Counter(b['sig'][s] for b in rec.values()) for s in range(4)}
        hs1 = {s: Counter(b['sig_c1'][s] for b in rec.values()) for s in range(4)}
        print(f'{ori} r={r}: {cnt_h} hub values; cap under C1: {dict(sorted(hc1.items()))}; under C1+O1: {dict(sorted(hc13.items()))}')
        for s in range(4):
            print(f'{ori} r={r}:   with X <= {s}: C1 {dict(sorted(hs1[s].items()))}; C1+O1 {dict(sorted(hs[s].items()))}')
        ext = max(rec.values(), key=lambda b: b['c13'])
        print(f'{ori} r={r}:   K_r = {max(hc13)} (C1+O1), K_r(sigma=0..3) = {[max(hs[s]) for s in range(4)]}; example witness {ext["wit"]}; {time.time()-t0:.0f}s', flush=True)
        hist[r] = dict(c1=dict(hc1), c13=dict(hc13), sig={s: dict(hs[s]) for s in range(4)}, sig_c1={s: dict(hs1[s]) for s in range(4)},
                       K=max(hc13), K_sigma=[max(hs[s]) for s in range(4)], K_c1=max(hc1), K_c1_sigma=[max(hs1[s]) for s in range(4)])
        # witnesses of the extreme capacities
        hist[r]['witnesses'] = [dict(h=hex(h), **{k: v for k, v in b.items() if k.startswith('wit')}) for h, b in rec.items() if b['c13'] == max(hc13)][:6]
        hist[r]['witnesses_sigma0'] = [dict(h=hex(h), wit=b.get('wit0')) for h, b in rec.items() if b['sig'][0] == max(hs[0])][:6]
    json.dump(dict(ori=ori, use_o1=use_o1, table=hist,
                   cap={r: {str(h): dict(c1=b['c1'], c13=b['c13'], sig=b['sig'], Xmin=b['Xmin_by_m']) for h, b in results[r].items() if b['c1'] >= 1} for r in results}),
              open(OUT/f'hub2_{ori}.json', 'w'))
    print(f'{ori}: done {time.time()-t0:.0f}s', flush=True)
    return hist

if __name__ == '__main__':
    oris = sys.argv[1].split(',') if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else ['M', 'Mt']
    use_o1 = '--no-o1' not in sys.argv
    res = {o: analyse(o, use_o1) for o in oris}
    print('RESULT K_r (C1+O1) by orientation and r:', {o: {r: h[r]['K'] for r in h} for o, h in res.items()})
    print('RESULT K_r(sigma=0..3):', {o: {r: h[r]['K_sigma'] for r in h} for o, h in res.items()})
