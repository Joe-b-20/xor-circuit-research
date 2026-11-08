#!/usr/bin/env python3
"""qhubcheck/h2_check.py -- independent recomputation of finite fact H2 (qhub/REPORT.md sections 2-3).

Everything is implemented from the definitions in PROOF.md (sections 1, 4) and the statement of H2, not from
hub2.py / hub2_check.py:
  * boundary B = 32 unit vectors + the 32 rows of M (orientation M) or the 32 columns of M (M^T), parsed from the
    repository's circuits/aes-mixcolumns/aes-mixcolumns.mat.txt (cross-checked once against stress.BOUNDARY);
  * pair value = XOR of two distinct boundary masks (F2: 2016 distinct, each with a unique pair);
  * triple representations of v = 3-subsets of B with XOR v; full value = exactly three of them (F3);
  * N(h) = { f full : h ^ f is a pair value } for odd h not in B;
  * F(h, R, S) = {H_f + T : f in S, T triple of f} u {H_i + T : T in R} u {H_i + H_f + P_f : f in S} with
    P_f the unique boundary pair of XOR h ^ f;
  * cap_r(h) = max |S| over r-subsets R of the triples of h and S subset of N(h) with F(h, R, S) independent.
Independence: incremental GF(2) basis with LOWEST-bit pivots (hub2.py pivots on the highest bit, hub2_check.py uses
batch elimination), coordinates: boundary index i -> bit i, hub -> bit 100, full helper j (position in S) -> bit 101+j.
Also: (a) H1 cross-check (the 3m vectors H_f + T alone): max cap must be 4 (qreal/qrealcheck);
      (b) the nine explicit witnesses of qhub section 3.3: membership, independence, m = 3 - r, boundary excess X
          (minimum over apex choices, as qhub defines it, AND a constrained version in which a represented apex may
          not be the end of a missing edge and no represented label may equal a missing label), O1 matching;
      (c) X and O1 for every hub value attaining 3 - r (all maximal S);
      (d) mutation tests: the one-swap configuration must be dependent; a family with m = 4 - r must never pass.
usage: nice -n 10 python3 h2_check.py [M,Mt]
"""
import sys, json, time, itertools
from collections import defaultdict, Counter
from pathlib import Path
REPO = Path.home()/'xor-circuit-research'
OUT = Path.home()/'xs-campaigns/2026-11-07-sprint/qhubcheck'
HUBBIT = 1 << 100
def FBIT(j): return 1 << (101 + j)

def read_matrix():
    lines = [l.split() for l in open(REPO/'circuits/aes-mixcolumns/aes-mixcolumns.mat.txt') if l.strip()]
    assert lines[1] == ['32', '32'], lines[:2]
    rows = [[int(x) for x in l] for l in lines[2:34]]
    assert len(rows) == 32 and all(len(r) == 32 for r in rows)
    rowmask = [sum(b << j for j, b in enumerate(r)) for r in rows]
    colmask = [sum(rows[i][j] << i for i in range(32)) for j in range(32)]
    return rowmask, colmask

def boundary(ori):
    rows, cols = read_matrix()
    return [1 << i for i in range(32)] + (rows if ori == 'M' else cols)

class Basis:
    """GF(2) basis; pivot = lowest set bit of the stored row (rows are never modified after insertion)."""
    def __init__(self): self.p = {}
    def add(self, v):
        while v:
            lb = v & -v
            if lb in self.p: v ^= self.p[lb]
            else: self.p[lb] = v; return lb
        return None
    def remove(self, lb): del self.p[lb]

def rank_of(rows):
    b = Basis(); return sum(1 for v in rows if b.add(v) is not None)

def setup(ori):
    B = boundary(ori)
    try:
        sys.path.insert(0, str(Path.home()/'xs-campaigns/2026-11-07-sprint/lb76/pkg_copy/source/lower_bounds/checks'))
        from stress import BOUNDARY
        assert BOUNDARY[ori] == B, 'boundary differs from stress.BOUNDARY'
    except ImportError:
        print('  (stress.BOUNDARY not importable; skipped the cross-check)')
    assert len(set(B)) == 64 and all(bin(v).count('1') % 2 == 1 for v in B)
    pair = {}
    for i, j in itertools.combinations(range(64), 2):
        v = B[i] ^ B[j]; assert v not in pair, 'F2 fails'; pair[v] = (i, j)
    assert len(pair) == 2016
    trip = defaultdict(list)
    for i, j, k in itertools.combinations(range(64), 3):
        trip[B[i] ^ B[j] ^ B[k]].append((i, j, k))
    f3 = Counter(len(t) for t in trip.values())
    full = sorted(v for v, t in trip.items() if len(t) == 3)
    Bset = set(B)
    N = defaultdict(set)
    for f in full:
        for p in pair:
            h = f ^ p
            if h not in Bset: N[h].add(f)
    N = {h: sorted(fs) for h, fs in N.items()}
    assert all(bin(h).count('1') % 2 == 1 for h in N)
    return B, pair, trip, dict(f3), full, N

def tmask(T): return sum(1 << i for i in T)

def cap_and_witnesses(h, R, fs, trip, pair, mixed=True):
    """max |S| with F(h, R, S) independent, and all S of that size (S subsets of fs, index-increasing DFS)."""
    basis = Basis()
    for T in R:
        assert basis.add(tmask(T) | HUBBIT) is not None, 'hub triples dependent'
    best = [0]; wits = []
    def rec(start, S):
        if len(S) > best[0]: best[0] = len(S); wits.clear()
        if len(S) == best[0] and len(wits) < 200: wits.append(tuple(S))
        for idx in range(start, len(fs)):
            f = fs[idx]; j = len(S)
            vecs = [tmask(T) | FBIT(j) for T in trip[f]]
            if mixed: vecs.append(tmask(pair[h ^ f]) | FBIT(j) | HUBBIT)
            lbs = []; ok = True
            for v in vecs:
                lb = basis.add(v)
                if lb is None: ok = False; break
                lbs.append(lb)
            if ok: rec(idx + 1, S + [f])
            for lb in reversed(lbs): basis.remove(lb)
    rec(0, [])
    return best[0], wits

def family_rows(h, R, S, trip, pair):
    rows = [tmask(T) | HUBBIT for T in R]
    for j, f in enumerate(S):
        rows += [tmask(T) | FBIT(j) for T in trip[f]]
        rows.append(tmask(pair[h ^ f]) | FBIT(j) | HUBBIT)
    return rows

def excess(h, R, S, trip, pair, B, constrained):
    """minimum boundary excess X = min over apex choices of sum_B (deg(v) - 2)_+ for the configuration's own edges.
    Each triple (owner, T) with apex a gives the H-B edge owner-a and the B-B edge of T \\ {a}; B-B edges with the same
    pair are one edge (one B-B edge per label, Lemma 4.1); the missing edges hub-b_j, f_j-c_j add 1 at both ends.
    Exact: apex choices are enumerated jointly for the triples that share a pair with another triple; the other
    triples contribute 1 at each element whatever the apex.  constrained=True additionally forbids a represented apex
    at the end of a missing edge of the same helper and a represented label equal to a missing label (both would make
    one edge carry two labels), trying both assignments of the ends of every P_j."""
    trips = [('hub', T) for T in R] + [(j, T) for j, f in enumerate(S) for T in trip[f]]
    pairs = [pair[h ^ f] for f in S]
    n = len(trips)
    shared = set()
    for a, b in itertools.combinations(range(n), 2):
        if len(set(trips[a][1]) & set(trips[b][1])) == 2: shared.add(a); shared.add(b)
    shared = sorted(shared); free = [i for i in range(n) if i not in shared]
    ends_options = [[(b, c), (c, b)] for (b, c) in pairs] if constrained else [[(b, c)] for (b, c) in pairs]
    best = None
    for ends in itertools.product(*ends_options):   # ends[j] = (hub's end b_j, f_j's end c_j)
        missing = {h ^ B[b] for (b, c) in ends}
        def allowed(owner, T, a):
            if not constrained: return True
            if owner == 'hub' and a in [e[0] for e in ends]: return False
            if owner != 'hub' and a == ends[owner][1]: return False
            b, c = [v for v in T if v != a]
            return (B[b] ^ B[c]) not in missing
        base = Counter()
        for (b, c) in ends: base[b] += 1; base[c] += 1
        ok = True
        for i in free:
            owner, T = trips[i]
            if not any(allowed(owner, T, a) for a in T): ok = False; break
            for v in T: base[v] += 1
        if not ok: continue
        for apex in itertools.product(*[list(trips[i][1]) for i in shared]):
            deg = Counter(base); bb = set(); good = True
            for i, a in zip(shared, apex):
                owner, T = trips[i]
                if not allowed(owner, T, a): good = False; break
                deg[a] += 1
                bb.add(tuple(sorted(v for v in T if v != a)))
            if not good: continue
            for (b, c) in bb: deg[b] += 1; deg[c] += 1
            X = sum(max(0, d - 2) for d in deg.values())
            if best is None or X < best: best = X
    return best

def o1_ok(R, S, trip, r):
    """Lemma O1 as a matching: each full helper owns two distinct outputs (indices 32..63) in two distinct triples,
    the hub owns r - 1 outputs in distinct triples of R; all owned outputs distinct.  Backtracking."""
    demands = [(2, trip[f]) for f in S] + ([(r - 1, list(R))] if r >= 2 else [])
    used = set()
    def rec(k):
        if k == len(demands): return True
        need, ts = demands[k]
        for chosen in itertools.combinations(range(len(ts)), need):
            opts = [[o for o in ts[t] if o >= 32 and o not in used] for t in chosen]
            for pick in itertools.product(*opts):
                if len(set(pick)) < need: continue
                used.update(pick)
                if rec(k + 1): return True
                used.difference_update(pick)
        return False
    return rec(0)

WITNESSES = [  # qhub REPORT section 3.3 (R as 64-bit masks over boundary indices, S as full values)
    ('M', 0, 0x80800080, [], [0x181, 0x406000, 0x80800040]),
    ('M', 0, 0x40404000, [], [0x2030, 0x20404000, 0x80004080]),
    ('M', 1, 0x2020200, [0x2020200], [0x181, 0x4000204]),
    ('M', 1, 0x80800080, [0x80800080], [0x181, 0x404020]),
    ('M', 2, 0x80800080, [0x80800080, 0x800000404000], [0x181]),
    ('Mt', 0, 0x2020200, [], [0x301, 0x60200, 0x4080004]),
    ('Mt', 0, 0x20202, [], [0x602, 0x1000003, 0x4040800]),
    ('Mt', 1, 0x2020200, [0x204000004], [0x301, 0x60200]),
    ('Mt', 2, 0x2020200, [0x204000004, 0x2020200], [0x301]),
]

def main(oris):
    report = {}
    for ori in oris:
        t0 = time.time()
        B, pair, trip, f3, full, N = setup(ori)
        print(f'{ori}: F3 histogram {f3}; {len(full)} full values; {len(N)} odd non-boundary h with N(h) nonempty; '
              f'|N(h)| histogram {dict(sorted(Counter(len(v) for v in N.values()).items()))}; {time.time()-t0:.1f}s', flush=True)
        rep = {}
        # (a) H1 cross-check: 3m vectors only, r = 0
        h1 = {}
        for h, fs in N.items():
            h1[h] = cap_and_witnesses(h, (), fs, trip, pair, mixed=False)[0]
        hh = Counter(h1.values())
        print(f'{ori}: H1 cross-check (3m vectors only): cap histogram {dict(sorted(hh.items()))}, max {max(hh)}; '
              f'cap-4 values {[hex(h) for h in sorted(h1) if h1[h] == 4]}', flush=True)
        rep['H1_hist'] = dict(hh)
        # H2 proper
        attain = {}
        for r in (0, 1, 2):
            caps = {}; wit = {}
            for h, fs in N.items():
                reps = trip.get(h, [])
                if len(reps) < r: continue
                bestc = 0; bw = []
                for R in (itertools.combinations(reps, r) if r else [()]):
                    c, ws = cap_and_witnesses(h, R, fs, trip, pair)
                    if c > bestc: bestc = c; bw = []
                    if c == bestc: bw += [(R, S) for S in ws]
                caps[h] = bestc; wit[h] = bw
            hist = Counter(caps.values())
            att = sorted(h for h, c in caps.items() if c == 3 - r)
            viol = sorted(h for h, c in caps.items() if c > 3 - r)
            print(f'{ori} r={r}: {len(caps)} hub values; cap_r histogram {dict(sorted(hist.items()))}; max {max(hist)}; '
                  f'attaining 3-r: {len(att)}; VIOLATIONS of cap <= 3-r: {len(viol)} {[hex(h) for h in viol[:5]]}', flush=True)
            # (c) X / O1 for all maximal configurations at the attaining hub values
            xs = Counter(); xc = Counter(); o1bad = 0; n_conf = 0; attain0 = set(); attain0c = set()
            for h in att:
                for R, S in wit[h]:
                    n_conf += 1
                    X = excess(h, R, S, trip, pair, B, False); Xc = excess(h, R, S, trip, pair, B, True)
                    xs[X] += 1; xc[Xc if Xc is not None else 'none'] += 1
                    if not o1_ok(R, S, trip, r): o1bad += 1
                    if X == 0: attain0.add(h)
                    if Xc == 0: attain0c.add(h)
            print(f'{ori} r={r}:   maximal configurations at attaining values: {n_conf}; X histogram (qhub definition) {dict(sorted(xs.items()))}; '
                  f'constrained-X histogram {dict(sorted(xc.items(), key=str))}; O1 failures {o1bad}; '
                  f'hub values attaining 3-r with X = 0: {len(attain0)}; with constrained X = 0: {len(attain0c)}', flush=True)
            rep[f'r{r}'] = dict(hist=dict(hist), attaining=[hex(h) for h in att], violations=[hex(h) for h in viol], n_maximal_configs=n_conf,
                                X_hist={str(k): v for k, v in xs.items()}, Xc_hist={str(k): v for k, v in xc.items()}, o1_failures=o1bad,
                                attaining_X0=len(attain0), attaining_Xc0=len(attain0c))
            attain[r] = (caps, wit)
        # (b) the explicit witnesses
        for (o, r, h, Rm, S) in WITNESSES:
            if o != ori: continue
            Bset = set(B)
            R = tuple(tuple(i for i in range(64) if (m >> i) & 1) for m in Rm)
            okmem = (h not in Bset and bin(h).count('1') % 2 == 1 and all(f in full for f in S) and all(f in N.get(h, []) for f in S)
                     and all(len(T) == 3 and B[T[0]] ^ B[T[1]] ^ B[T[2]] == h for T in R) and len(set(R)) == r)
            rows = family_rows(h, R, S, trip, pair)
            indep = rank_of(rows) == len(rows) == 4 * len(S) + r
            X = excess(h, R, S, trip, pair, B, False); Xc = excess(h, R, S, trip, pair, B, True)
            o1 = o1_ok(R, S, trip, r)
            pairs_disjoint = len({v for f in S for v in pair[h ^ f]}) == 2 * len(S)
            print(f'{ori} witness r={r} h={hex(h)} R={[hex(m) for m in Rm]} S={[hex(f) for f in S]}: membership {okmem}, '
                  f'independent (rank {rank_of(rows)} of {len(rows)}) {indep}, m = 3-r {len(S) == 3 - r}, pairs disjoint {pairs_disjoint}, '
                  f'X = {X}, constrained X = {Xc}, O1 {o1}', flush=True)
            rep.setdefault('witnesses', []).append(dict(r=r, h=hex(h), membership=okmem, independent=indep, X=X, Xc=Xc, o1=o1))
        # (d) mutation tests
        # one-swap: h = f + b + c where T = {c, d, e} is a triple of f and h = {d, e, b}: must be dependent at r = 1
        found = 0; dep = 0
        for f in full:
            for T in trip[f]:
                for c in T:
                    d, e = [v for v in T if v != c]
                    for b in range(64):
                        if b in T: continue
                        h = B[d] ^ B[e] ^ B[b]
                        if h in set(B) or f not in N.get(h, []): continue
                        if pair[h ^ f] != tuple(sorted((b, c))): continue
                        found += 1
                        rows = family_rows(h, ((d, e, b) if (d < e < b) else tuple(sorted((d, e, b))),), [f], trip, pair)
                        if rank_of(rows) < len(rows): dep += 1
                        break
                    if found >= 50: break
                if found >= 50: break
            if found >= 50: break
        print(f'{ori}: mutation (one-swap configurations must be dependent): {found} tested, {dep} dependent')
        # a supposed m = 4 - r family must be dependent for every h: implied by the histograms (max = 3 - r); also test
        # that the checker CAN report independence of size 3 - r (done above) and dependence when a mixed vector is duplicated
        h0 = int(rep['r0']['attaining'][0], 16); R0, S0 = attain[0][1][h0][0]
        rows = family_rows(h0, R0, S0, trip, pair); rows.append(rows[-1])
        print(f'{ori}: mutation (duplicated mixed vector) dependent: {rank_of(rows) < len(rows)}; {time.time()-t0:.0f}s total', flush=True)
        report[ori] = rep
    json.dump(report, open(OUT/'h2_check.json', 'w'), indent=1)
    print('RESULT max cap_r:', {o: {r: max(int(k) for k in report[o][f"r{r}"]["hist"]) for r in (0, 1, 2)} for o in report})

if __name__ == '__main__':
    main(sys.argv[1].split(',') if len(sys.argv) > 1 else ['M', 'Mt'])
