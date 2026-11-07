#!/usr/bin/env python3
"""qcheck: independent recomputation of the finite facts behind the qbound claims.

Written from PROOF.md / qbound REPORT.md statements only (nothing imported from qbound or the package).
Matrix read from ~/xor-circuit-research/circuits/aes-mixcolumns/aes-mixcolumns.mat.txt.
Checks: F2 (Sidon), F3 (triple multiplicities), F5 (six-sets, rho6), F4 (adjacent full pairs rank 5, others 6),
F6 (rank C_l <= 7 for every label value, histogram), S1 (sigma(P) histogram, sigma = rank(C_l)-1 for pair values,
every 4-form of a pair value disjoint from the pair, no pair with sigma = 1, rich pairs by kind, top(m)),
N3max (explicit set of rho6/2 full values whose 3*rho6/2 relations are independent; upper bound rho6/2 from L12).
"""
import itertools, sys, json, random, time
from collections import Counter, defaultdict
from pathlib import Path
T0 = time.time()
def log(*a): print(f'[{time.time()-T0:6.1f}s]', *a, flush=True)

MAT = Path.home()/'xor-circuit-research/circuits/aes-mixcolumns/aes-mixcolumns.mat.txt'
lines = [l.split() for l in open(MAT).read().strip().split('\n') if l.strip()]
lines = lines[lines.index(['32', '32']):]        # the file starts with a count line '1'
assert lines[0] == ['32', '32'], lines[0]
ROWS = [sum(int(b) << c for c, b in enumerate(l)) for l in lines[1:33]]   # row r as mask over input bits
COLS = [sum(((ROWS[r] >> c) & 1) << r for r in range(32)) for c in range(32)]
assert len(ROWS) == 32 and all(bin(r).count('1') in (5, 7) for r in ROWS)
assert all(bin(c).count('1') in (5, 11) for c in COLS)
UNITS = [1 << i for i in range(32)]
BND = {'M': UNITS + ROWS, 'Mt': UNITS + COLS}
RHO6_EXP = {'M': 20, 'Mt': 28}

def rank(vs):
    piv = {}
    for v in vs:
        while v:
            h = v.bit_length() - 1
            if h in piv: v ^= piv[h]
            else: piv[h] = v; break
    return len(piv)
class Basis:
    def __init__(self): self.piv = {}
    def reduce(self, v):
        while v:
            h = v.bit_length() - 1
            if h in self.piv: v ^= self.piv[h]
            else: return v
        return 0
    def add(self, v):
        v = self.reduce(v)
        if v: self.piv[v.bit_length() - 1] = v; return True
        return False
    def dim(self): return len(self.piv)
    def copy(self):
        b = Basis(); b.piv = dict(self.piv); return b
def wt(v): return bin(v).count('1')

OUT = {}
for name in ('M', 'Mt'):
    B = BND[name]; res = {}
    assert len(set(B)) == 64 and all(wt(b) & 1 for b in B)
    # F2
    pv = Counter(B[i] ^ B[j] for i, j in itertools.combinations(range(64), 2))
    assert len(pv) == 2016 and max(pv.values()) == 1, 'F2 fails'
    pairval = {B[i] ^ B[j]: (1 << i) | (1 << j) for i, j in itertools.combinations(range(64), 2)}
    pairvals = set(pairval)
    log(name, 'F2 Sidon ok: 2016 distinct pair values')
    # F3
    trip = defaultdict(list)
    for i, j, k in itertools.combinations(range(64), 3):
        trip[B[i] ^ B[j] ^ B[k]].append((1 << i) | (1 << j) | (1 << k))
    h3 = Counter(len(t) for t in trip.values())
    log(name, 'F3 triple histogram', dict(sorted(h3.items())))
    assert h3 == ({1: 40704, 2: 360, 3: 80} if name == 'M' else {1: 40320, 2: 504, 3: 112})
    full = {v: ts for v, ts in trip.items() if len(ts) == 3}
    repeated = {v: ts for v, ts in trip.items() if len(ts) >= 2}
    # pair values are never triple values? (an odd value cannot equal an even pair value: parity) - sanity
    assert not (set(trip) & pairvals)
    # F5: six-sets
    six = set()
    for v, ts in repeated.items():
        for a, b in itertools.combinations(ts, 2):
            assert a & b == 0, 'two triples of one value share an element (contradicts F2)'
            six.add(a | b)
    R6 = Basis()
    for s in six: R6.add(s)
    rho6 = R6.dim()
    log(name, 'F5 six-sets', len(six), 'rho6', rho6)
    assert (len(six), rho6) == ((60, 20) if name == 'M' else (84, 28))
    # every zero-sum 6-subset arises this way: check by direct enumeration of weight-6 zero-sum sets via triples is complete:
    # a zero-sum 6-set splits into a triple and its complement with equal XOR, so it is counted. (no extra enumeration needed)
    # F4: adjacent full pairs
    adjr = Counter(); nonr = Counter()
    for a, b in itertools.combinations(sorted(full), 2):
        rows = [t | (1 << 64) for t in full[a]] + [t | (1 << 65) for t in full[b]]
        r = rank(rows)
        (adjr if (a ^ b) in pairvals else nonr)[r] += 1
    log(name, 'F4 adjacent full pairs rank hist', dict(adjr), 'non-adjacent', dict(nonr))
    assert set(adjr) == {5} and set(nonr) == {6}
    assert adjr[5] == (360 if name == 'M' else 504)
    # forms: 2- and 4-subsets by XOR value
    forms = defaultdict(list)
    for i, j in itertools.combinations(range(64), 2): forms[B[i] ^ B[j]].append((1 << i) | (1 << j))
    for c in itertools.combinations(range(64), 4):
        forms[B[c[0]] ^ B[c[1]] ^ B[c[2]] ^ B[c[3]]].append((1 << c[0]) | (1 << c[1]) | (1 << c[2]) | (1 << c[3]))
    assert sum(len(f) for f in forms.values()) == 2016 + 635376 == 637392
    capl = {l: rank([f | (1 << 64) for f in fs]) for l, fs in forms.items()}
    h6 = Counter(capl.values())
    log(name, 'F6 rank(C_l) histogram', dict(sorted(h6.items())), 'max', max(h6))
    assert max(h6) == 7
    assert h6 == ({1: 578900, 2: 18032, 3: 5846, 4: 778, 5: 200, 6: 108, 7: 10} if name == 'M' else {1: 561014, 2: 22830, 3: 7678, 4: 1273, 5: 234, 6: 216, 7: 6})
    # S1: sigma(P) = rank of six-sets containing P
    sigma = {}; nsix = {}
    sixl = list(six)
    for i, j in itertools.combinations(range(64), 2):
        P = (1 << i) | (1 << j)
        S = [s for s in sixl if s & P == P]
        sigma[(i, j)] = rank(S); nsix[(i, j)] = len(S)
    hs = Counter(sigma.values()); hn = Counter(nsix.values())
    log(name, 'S1 sigma histogram', dict(sorted(hs.items())), '; #six-sets through pair', dict(sorted(hn.items())))
    assert 1 not in hs, 'a pair with sigma = 1 exists: Corollary S2 would fail'
    # sigma = rank(C_l) - 1 for the pair value l, and every 4-form of l is disjoint from P
    bad = 0
    for (i, j), s in sigma.items():
        P = (1 << i) | (1 << j); l = B[i] ^ B[j]
        fs = forms[l]
        two = [f for f in fs if wt(f) == 2]; four = [f for f in fs if wt(f) == 4]
        assert two == [P]
        assert all(f & P == 0 for f in four), 'a 4-form of a pair value meets the pair'
        assert {f | P for f in four} == {s6 for s6 in sixl if s6 & P == P}
        if capl[l] - 1 != s: bad += 1
    assert bad == 0
    log(name, 'S1: sigma(P) = rank(C_l) - 1 for all 2016 pair values; 4-forms disjoint from the pair: ok')
    kind = Counter()
    for (i, j), s in sigma.items():
        k = ('in' if i < 32 else 'out') + '-' + ('in' if j < 32 else 'out'); kind[(k, s)] += 1
    rich = {k: sum(v for (kk, s), v in kind.items() if kk == k and s >= 2) for k in ('in-in', 'in-out', 'out-out')}
    log(name, 'rich pairs (sigma>=2) by kind', rich, 'total', sum(rich.values()))
    sig_sorted = sorted(sigma.values(), reverse=True)
    top = [sum(sig_sorted[:m]) for m in range(65)]
    log(name, 'top(m) m=0..40 step 4:', [top[m] for m in range(0, 41, 4)])
    # REPORT formula for top: M 5m (m<=12), 60+4(m-12) (<=18), 84+3(m-18); Mt 5m (<=24), 120+4(m-24) (<=36), 168+3(m-36)
    def top_formula(m):
        if name == 'M':
            return 5 * m if m <= 12 else (60 + 4 * (m - 12) if m <= 18 else 84 + 3 * (m - 18))
        return 5 * m if m <= 24 else (120 + 4 * (m - 24) if m <= 36 else 168 + 3 * (m - 36))
    mism = [m for m in range(0, 45) if top[m] != top_formula(m)]
    log(name, 'top(m) formula mismatches for m<=44:', mism)
    # N3max: explicit set of rho6/2 full values with independent relations
    vals = sorted(full)
    lines_ = {v: (full[v][0] ^ full[v][1], full[v][0] ^ full[v][2]) for v in vals}
    allr = rank([x for v in vals for x in lines_[v]])
    log(name, 'rank of the span of all full-value six-set lines', allr, '(upper bound n3 <= rho6/2 =', rho6 // 2, 'by L12)')
    assert allr == rho6
    rng = random.Random(7); best = []
    for it in range(3000):
        order = vals[:]; rng.shuffle(order)
        bs = Basis(); S = []
        for v in order:
            a, b = lines_[v]; t = bs.copy()
            if t.add(a) and t.add(b): bs = t; S.append(v)
        if len(S) > len(best): best = S
        if len(best) == rho6 // 2: break
    log(name, 'N3max: explicit independent full set of size', len(best), [hex(v) for v in best])
    assert len(best) == rho6 // 2
    # verify directly: the 3|S| relation vectors H_s + T are independent and no two values are adjacent (Lemma 4.5)
    rows = [t | (1 << (64 + k)) for k, v in enumerate(best) for t in full[v]]
    assert rank(rows) == 3 * len(best), 'explicit set: relations dependent'
    assert all((a ^ b) not in pairvals for a, b in itertools.combinations(best, 2)), 'explicit set has an adjacent pair'
    # also: F8-style sanity on the set: all pairs non-adjacent (done); pairwise relation rank 6
    log(name, 'N3max verified: 3*%d relations independent, pairwise non-adjacent' % len(best))
    res.update(rho6=rho6, six=len(six), sigma_hist=dict(hs), rich_by_kind=rich, top=top, n3max=len(best), n3max_set=[hex(v) for v in best],
               cap_hist=dict(h6), F4_adjacent=dict(adjr), F4_nonadjacent=dict(nonr))
    OUT[name] = res
json.dump(OUT, open(Path.home()/'xs-campaigns/2026-11-07-sprint/qcheck/ff_check.json', 'w'), indent=1)
log('ALL FINITE-FACT CHECKS PASSED')
