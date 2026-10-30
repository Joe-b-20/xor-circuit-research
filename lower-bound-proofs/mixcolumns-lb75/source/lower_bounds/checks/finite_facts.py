#!/usr/bin/env python3
"""Independent recomputation of every finite premise of the 75 proof.

Written from the proof documents (not from the bundle's code). Standard library only.
Each section prints the number it finds and asserts the value the proof relies on.
"""
import itertools, sys, time, json
from collections import Counter, defaultdict

T0 = time.time()
def log(*a):
    print(f"[{time.time()-T0:7.1f}s]", *a, flush=True)

# ---------------------------------------------------------------- AES matrix
def xtime(a):
    a <<= 1
    return (a ^ 0x11B) & 0xFF if a & 0x100 else a & 0xFF
def gmul(a, b):
    r = 0
    for i in range(8):
        if (b >> i) & 1:
            t = a
            for _ in range(i): t = xtime(t)
            r ^= t
    return r & 0xFF

def mixcolumns_rows():
    coef = [2, 3, 1, 1]
    rows = [0] * 32
    for col in range(4):
        for k in range(4):
            c, ib = coef[k], (col + k) % 4
            for in_bit in range(8):
                v = gmul(c, 1 << in_bit)
                for out_bit in range(8):
                    if (v >> out_bit) & 1:
                        rows[col * 8 + out_bit] ^= 1 << (ib * 8 + in_bit)
    return rows

ROWS = mixcolumns_rows()                     # row r as mask over input bits
COLS = [sum(((ROWS[r] >> c) & 1) << r for r in range(32)) for c in range(32)]  # column c as mask over output bits
UNITS = [1 << i for i in range(32)]

def apply(rows, u):   # y = A u  where rows[r] is the mask of row r
    return sum((bin(rows[r] & u).count('1') & 1) << r for r in range(32))

# sanity: FIPS example column, and M*1 = 1
assert apply(ROWS, 0xd4bf5d30 & 0 | (0xd4 | 0xbf << 8 | 0x5d << 16 | 0x30 << 24)) == (0x04 | 0x66 << 8 | 0x81 << 16 | 0xe5 << 24)
assert apply(ROWS, 0xFFFFFFFF) == 0xFFFFFFFF

def rank(vectors):
    piv = {}
    for v in vectors:
        while v:
            h = v.bit_length() - 1
            if h in piv: v ^= piv[h]
            else:
                piv[h] = v; break
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
    def reduce_full(self, v):
        # canonical coset representative when the basis is fully reduced: clear EVERY pivot bit
        for h in sorted(self.piv, reverse=True):
            if (v >> h) & 1: v ^= self.piv[h]
        return v
    def fully_reduce(self):
        # reduced echelon form: no pivot bit occurs in any other basis vector, so reduce() is a canonical coset map
        for h in sorted(self.piv):
            for g in self.piv:
                if g != h and (self.piv[g] >> h) & 1: self.piv[g] ^= self.piv[h]
        return self

def inverse_rows(rows):
    """rows of A^{-1} given rows of A (32x32 over GF(2))."""
    aug = [rows[r] | (1 << (32 + r)) for r in range(32)]
    # Gauss-Jordan on the first 32 columns
    for c in range(32):
        p = next(r for r in range(c, 32) if (aug[r] >> c) & 1)
        aug[c], aug[p] = aug[p], aug[c]
        for r in range(32):
            if r != c and (aug[r] >> c) & 1: aug[r] ^= aug[c]
    return [aug[r] >> 32 for r in range(32)]

INV_ROWS = inverse_rows(ROWS)
for _ in range(50):
    import random
    u = random.getrandbits(32)
    assert apply(INV_ROWS, apply(ROWS, u)) == u

RESULTS = {}

# ---------------------------------------------------------------- boundaries
BOUND = {'M': UNITS + ROWS, 'Mt': UNITS + COLS}
for name, B in list(BOUND.items()):
    assert len(set(B)) == 64 and all(bin(b).count('1') & 1 for b in B)
    pairs = Counter(B[i] ^ B[j] for i, j in itertools.combinations(range(64), 2))
    assert len(pairs) == 2016, name
    trip = defaultdict(list)
    for i, j, k in itertools.combinations(range(64), 3):
        trip[B[i] ^ B[j] ^ B[k]].append((1 << i) | (1 << j) | (1 << k))
    hist = Counter(len(v) for v in trip.values())
    log(name, 'triple multiplicity histogram', dict(hist))
    RESULTS[name + '_triple_hist'] = dict(hist)
    if name == 'M': assert hist == {1: 40704, 2: 360, 3: 80}
    else: assert hist == {1: 40320, 2: 504, 3: 112}
    # weight-6 zero-sum sets and rho6
    six = set()
    for v, ts in trip.items():
        for a, b in itertools.combinations(ts, 2):
            assert a & b == 0
            six.add(a | b)
    r6 = rank(list(six))
    log(name, 'weight-6 relations', len(six), 'rho6 =', r6)
    RESULTS[name + '_six'] = len(six); RESULTS[name + '_rho6'] = r6
    assert (len(six), r6) == ((60, 20) if name == 'M' else (84, 28))
    BOUND[name + '_trip'] = trip
    BOUND[name + '_six'] = six
    BOUND[name + '_pairvals'] = set(pairs)

# ---------------------------------------------------------------- relation codes by weight (graph codes)
def graph_code_words(rows, inv_rows, maxw):
    """All nonzero words (u, A u) of total weight <= maxw, as 64-bit formal vectors (low 32 = u, high 32 = Au)."""
    half = maxw // 2
    words = set()
    for k in range(1, half + 1):
        for comb in itertools.combinations(range(32), k):
            u = sum(1 << i for i in comb)
            v = apply(rows, u)
            if k + bin(v).count('1') <= maxw: words.add(u | (v << 32))
            w = apply(inv_rows, u)         # output half of weight k
            if k + bin(w).count('1') <= maxw: words.add(w | (u << 32))
    return words

# relation code for boundary(Mt) = graph code of M  (words (u, Mu) = zero-sum subsets {units of u} ∪ {columns of Mu})
log('enumerating graph code words of M up to weight 12 ...')
GM12 = graph_code_words(ROWS, INV_ROWS, 12)
wh = Counter(bin(w).count('1') for w in GM12)
log('graph code (u,Mu) weights:', dict(sorted(wh.items())))
assert wh[6] == 84 and wh[8] == 276 and wh[10] == 1300 and wh[12] == 8112
GMt8 = graph_code_words(COLS, inverse_rows(COLS), 8)
wh2 = Counter(bin(w).count('1') for w in GMt8)
log('graph code (u,M^T u) weights:', dict(sorted(wh2.items())))
assert wh2[6] == 60 and wh2[8] == 248
RESULTS['gc_M'] = dict(sorted(wh.items())); RESULTS['gc_Mt'] = dict(sorted(wh2.items()))

# The relation code of boundary(A) (units + rows of A) is {(A^T w, w)} = the graph code of A^{-T}; for A = M^T this is
# {(Mv, v)}: the words (u, Mu) with the two halves SWAPPED (unit part = Mu, column part = u).  Same for M with (u, M^T u).
def swap(w): return ((w & 0xFFFFFFFF) << 32) | (w >> 32)
GM12 = {swap(w) for w in GM12}
GMt8 = {swap(w) for w in GMt8}
Bt = BOUND['Mt']
def word_is_relation(word, B):
    s = 0
    for i in range(64):
        if (word >> i) & 1: s ^= B[i]
    return s == 0
assert all(word_is_relation(w, Bt) for w in GM12)
assert all(word_is_relation(w, BOUND['M']) for w in GMt8)
# the weight-6 words coincide with the six-sets found by triples
assert {w for w in GM12 if bin(w).count('1') == 6} == BOUND['Mt_six']
assert {w for w in GMt8 if bin(w).count('1') == 6} == BOUND['M_six']

R8t = Basis()
for w in GM12:
    if bin(w).count('1') <= 8: R8t.add(w)
R10t = Basis()
for w in GM12:
    if bin(w).count('1') <= 10: R10t.add(w)
log('Mt: rho8 =', R8t.dim(), 'rho10 =', R10t.dim())
assert R8t.dim() == 29 and R10t.dim() == 29
W12 = [w for w in GM12 if bin(w).count('1') == 12]
W12nz = [w for w in W12 if R10t.reduce(w)]
log('Mt: weight-12 words nonzero mod R10:', len(W12nz))
assert len(W12nz) == 736
R12t = R10t.copy()
for w in W12: R12t.add(w)
log('Mt: rho12 =', R12t.dim())
RESULTS['Mt_rho8'] = 29; RESULTS['Mt_rho10'] = 29; RESULTS['Mt_rho12'] = R12t.dim()
# M side: weight <= 8 relations have full rank 32? (FULL_ELIMINATION says "whose corresponding space has full rank 32")
R8m = Basis()
for w in GMt8: R8m.add(w)
log('M: rho8 =', R8m.dim())
RESULTS['M_rho8'] = R8m.dim()

# ---------------------------------------------------------------- full-helper incompatibilities
def helper_rows(B, trip, hval, hidx):
    """formal rows H_hidx + T for each triple T of value hval; coordinates 0..63 boundary, 64+hidx helper"""
    return [t | (1 << (64 + hidx)) for t in trip[hval]]

for name in ('M', 'Mt'):
    B = BOUND[name]; trip = BOUND[name + '_trip']; pv = BOUND[name + '_pairvals']
    strong = [v for v, ts in trip.items() if len(ts) == 3]
    assert len(strong) == (80 if name == 'M' else 112)
    adj = Counter(); nonadj = Counter()
    for a, b in itertools.combinations(strong, 2):
        r = rank(helper_rows(B, trip, a, 0) + helper_rows(B, trip, b, 1))
        if (a ^ b) in pv: adj[r] += 1
        else: nonadj[r] += 1
    log(name, 'full-helper pairs: adjacent ranks', dict(adj), 'nonadjacent ranks', dict(nonadj))
    assert set(adj) == {5} and set(nonadj) == {6}
    assert adj[5] == (360 if name == 'M' else 504) and nonadj[6] == (2800 if name == 'M' else 5712)
    # (ii) two disjoint pairs with equal difference: 12 rows rank <= 10
    bydiff = defaultdict(list)
    for a, b in itertools.combinations(strong, 2): bydiff[a ^ b].append((a, b))
    hist2 = Counter()
    for d, ps in bydiff.items():
        for (a, b), (c, e) in itertools.combinations(ps, 2):
            if len({a, b, c, e}) < 4: continue
            r = rank(helper_rows(B, trip, a, 0) + helper_rows(B, trip, b, 1) + helper_rows(B, trip, c, 2) + helper_rows(B, trip, e, 3))
            hist2[r] += 1
    log(name, 'two disjoint full pairs with equal difference: rank histogram', dict(hist2))
    assert hist2 == ({7: 180, 8: 720, 10: 288} if name == 'M' else {7: 252, 8: 1008, 10: 576})
    # (iii) a+b = e and c in e+B: 9 rows rank 8
    Bset = set(B); hist3 = Counter(); strongset = set(strong)
    for a, b in itertools.combinations(strong, 2):
        e = a ^ b
        for c in strong:
            if c in (a, b): continue
            if (c ^ e) in Bset:
                r = rank(helper_rows(B, trip, a, 0) + helper_rows(B, trip, b, 1) + helper_rows(B, trip, c, 2))
                hist3[r] += 1
    log(name, 'full pair + third full in e+B: rank histogram', dict(hist3))
    assert hist3 == ({8: 432} if name == 'M' else {8: 864})
    BOUND[name + '_strong'] = strong
    RESULTS[name + '_full_pairs'] = {'adjacent': dict(adj), 'nonadjacent': dict(nonadj), 'disjoint_pairs': dict(hist2), 'third': dict(hist3)}

# ---------------------------------------------------------------- label capacity c_e (2- and 4-forms)
for name in ('M', 'Mt'):
    B = BOUND[name]
    forms = defaultdict(list)       # e -> list of formal boundary subsets (64-bit) of size 2 or 4 with XOR e
    for i, j in itertools.combinations(range(64), 2):
        forms[B[i] ^ B[j]].append((1 << i) | (1 << j))
    for c in itertools.combinations(range(64), 4):
        forms[B[c[0]] ^ B[c[1]] ^ B[c[2]] ^ B[c[3]]].append(sum(1 << i for i in c))
    assert sum(len(v) for v in forms.values()) == 637392
    cap = {}
    for e, fs in forms.items():
        cap[e] = rank([f | (1 << 64) for f in fs])   # rows E_e + D
    hist = Counter(cap.values())
    log(name, 'label capacity histogram', dict(sorted(hist.items())))
    assert max(hist) == 7
    if name == 'M': assert hist == {1: 578900, 2: 18032, 3: 5846, 4: 778, 5: 200, 6: 108, 7: 10}
    else: assert hist == {1: 561014, 2: 22830, 3: 7678, 4: 1273, 5: 234, 6: 216, 7: 6}
    BOUND[name + '_forms'] = forms; BOUND[name + '_cap'] = cap
    RESULTS[name + '_cap_hist'] = dict(sorted(hist.items()))

# ---------------------------------------------------------------- weighted capacity: (3,2,2) seven-row cases all dependent
for name in ('M', 'Mt'):
    B = BOUND[name]; Bset = set(B); trip = BOUND[name + '_trip']; strong = BOUND[name + '_strong']
    repeated = {v for v, ts in trip.items() if len(ts) >= 2}
    assert len(repeated) == (440 if name == 'M' else 616)
    bidx = {b: i for i, b in enumerate(B)}
    cases = 0; dependent = 0
    for h3 in strong:
        for b in B:
            e = h3 ^ b
            rows3 = [(t ^ (1 << bidx[b])) | (1 << 64) for t in trip[h3]]      # E_e + T + B_b  (symmetric difference)
            others = [h for h in repeated if h != h3 and (h ^ e) in Bset]
            for h1, h2 in itertools.combinations(others, 2):
                b1 = bidx[h1 ^ e]; b2 = bidx[h2 ^ e]
                for p1 in itertools.combinations(trip[h1], 2):
                    for p2 in itertools.combinations(trip[h2], 2):
                        rows = rows3 + [(t ^ (1 << b1)) | (1 << 64) for t in p1] + [(t ^ (1 << b2)) | (1 << 64) for t in p2]
                        cases += 1
                        if rank(rows) < 7: dependent += 1
    log(name, '(3,2,2) seven-row cases', cases, 'dependent', dependent)
    assert cases == dependent == (51840 if name == 'M' else 75600)
    RESULTS[name + '_322_cases'] = cases
    BOUND[name + '_repeated'] = repeated

# ---------------------------------------------------------------- quotient table (J, k_e) and dark/active facts
for name in ('M', 'Mt'):
    B = BOUND[name]; forms = BOUND[name + '_forms']; cap = BOUND[name + '_cap']
    six = BOUND[name + '_six']
    R6 = Basis()
    for w in six: R6.add(w)
    assert R6.dim() == (20 if name == 'M' else 28)
    def K_e(e):
        fs = forms[e]; return [fs[0] ^ f for f in fs[1:]]
    J = R6.copy()
    if name == 'M':
        for e in forms:
            if cap[e] == 7:
                for d in K_e(e): J.add(d)
    log(name, 'dim J =', J.dim())
    assert J.dim() == (24 if name == 'M' else 28)
    table = Counter(); active = {}
    for e, fs in forms.items():
        if len(fs) < 2: continue
        Jc = J.copy(); k = 0
        for d in K_e(e):
            if Jc.add(d): k += 1
        if k: table[(cap[e], k)] += 1; active[e] = k
        assert cap[e] + 2 * k <= 7
    log(name, 'quotient table (c_e,k_e):', dict(table))
    assert table == ({(2, 1): 845, (3, 2): 44, (4, 1): 1} if name == 'M' else {(2, 1): 102, (4, 1): 1})
    # positive-k labels have no repeated-helper neighbour
    repeated = BOUND[name + '_repeated']; Bset = set(B)
    bad = sum(1 for e in active for h in repeated if (h ^ e) in Bset)
    log(name, 'active labels with a repeated-helper neighbour:', bad)
    assert bad == 0
    RESULTS[name + '_quotient_table'] = {str(k): v for k, v in table.items()}
    BOUND[name + '_R6'] = R6

# ---------------------------------------------------------------- high-excess labels (Q), and <=2 per strong helper
for name in ('M', 'Mt'):
    B = BOUND[name]; Bset = set(B); trip = BOUND[name + '_trip']; repeated = BOUND[name + '_repeated']; strong = BOUND[name + '_strong']
    bidx = {b: i for i, b in enumerate(B)}
    # labels meeting any repeated helper
    labels = defaultdict(list)
    for h in repeated:
        for b in B: labels[h ^ b].append(h)
    log(name, 'labels meeting a repeated helper:', len(labels))
    assert len(labels) == (22436 if name == 'M' else 30766)
    def max_excess(e, hs):
        best = 0
        groups = []
        for h in hs:
            b = bidx[h ^ e]
            rows = [(t ^ (1 << b)) | (1 << 64) for t in trip[h]]
            groups.append(rows)
        tail = [0] * (len(groups) + 1)
        for i in range(len(groups) - 1, -1, -1): tail[i] = tail[i + 1] + len(groups[i]) - 1
        # choose for each helper a subset of its rows of size >=2 (excess size-1); rows must stay independent
        def rec(i, basis, exc):
            nonlocal best
            if exc > best: best = exc
            if i == len(groups) or exc + tail[i] <= best: return
            g = groups[i]
            for k in range(len(g), 1, -1):
                for sub in itertools.combinations(g, k):
                    nb = basis.copy(); ok = True
                    for row in sub:
                        if not nb.add(row): ok = False; break
                    if ok: rec(i + 1, nb, exc + k - 1)
            rec(i + 1, basis, exc)
        rec(0, Basis(), 0)
        return best
    exc_hist = Counter(); Q = []
    for e, hs in labels.items():
        m = max_excess(e, hs); exc_hist[m] += 1
        if m == 3: Q.append(e)
    log(name, 'max local excess histogram:', dict(sorted(exc_hist.items())))
    assert max(exc_hist) == 3
    assert exc_hist == ({1: 17736, 2: 4604, 3: 96} if name == 'M' else {1: 24186, 2: 6388, 3: 192})
    Qset = set(Q)
    per_strong = max(sum(1 for b in B if (h ^ b) in Qset) for h in strong)
    log(name, '|Q| =', len(Q), 'rank of Q masks =', rank(Q), 'max Q labels per strong helper =', per_strong)
    assert per_strong == 2 and rank(Q) == (15 if name == 'M' else 27)
    RESULTS[name + '_Q'] = len(Q)
    BOUND[name + '_Q'] = Qset

# ---------------------------------------------------------------- conditional capacity (+2 exception for M, none for Mt)
for name in ('M', 'Mt'):
    B = BOUND[name]; Bset = set(B); trip = BOUND[name + '_trip']; cap = BOUND[name + '_cap']; strong = BOUND[name + '_strong']
    seven = [e for e, c in cap.items() if c == 7]
    meet = {e: [h for h in strong if (h ^ e) in Bset] for e in seven}
    log(name, 'rank-7 labels:', [hex(e) for e in seven], 'full helpers meeting them:', {hex(e): [hex(h) for h in hs] for e, hs in meet.items() if hs})
    if name == 'Mt':
        assert all(not hs for hs in meet.values())
    else:
        met = [e for e, hs in meet.items() if hs]
        assert len(met) == 4 and all(len(meet[e]) == 1 for e in met)
        hvals = sorted({meet[e][0] for e in met})
        assert hvals == [0x181, 0x18100, 0x1810000, 0x81000001]
        for a, b, c in itertools.combinations(hvals, 3):
            r = rank(helper_rows(B, trip, a, 0) + helper_rows(B, trip, b, 1) + helper_rows(B, trip, c, 2))
            assert r == 7, (hex(a), hex(b), hex(c), r)
        log('M: any three of the four exceptional full helpers have 9 rows of rank 7 -> at most two simultaneously full')

# ---------------------------------------------------------------- dark label capacity for Mt: K6_e mod R10
B = BOUND['Mt']; bidx = {b: i for i, b in enumerate(B)}
Rq = R10t.copy().fully_reduce()
assert Rq.dim() == 29 and all(not Rq.reduce_full(w) for w in GM12 if bin(w).count('1') <= 10)
assert rank([Rq.reduce_full(w) for w in GM12]) == 3
K6 = defaultdict(Basis); splits = 0
for w in W12nz:
    cls = Rq.reduce_full(w)
    assert cls and cls.bit_length() <= 64
    bits = [i for i in range(64) if (w >> i) & 1]
    assert len(bits) == 12
    for half in itertools.combinations(bits[1:], 5):          # fix bits[0] in the first half to avoid double counting
        D = (1 << bits[0]) | sum(1 << i for i in half)
        e = 0
        for i in half: e ^= B[i]
        e ^= B[bits[0]]
        K6[e].add(cls); splits += 1
log('Mt: 6+6 splits', splits)
assert splits == 736 * 462
dims = Counter(bb.dim() for bb in K6.values())
log('Mt: dim K6_e mod R10 histogram:', dict(dims))
assert dims == {1: 193172, 2: 5712}
activeK = set(K6)
# no active e has a 2/4 form
forms_t = BOUND['Mt_forms']
assert not any(e in forms_t for e in activeK)
log('Mt: no active six-form label has a two/four form: OK')
# repeated-helper pairs
rep_t = sorted(BOUND['Mt_repeated'])
assert len(rep_t) == 616
pairs_per_active = Counter()
for a, b in itertools.combinations(rep_t, 2):
    if (a ^ b) in activeK: pairs_per_active[a ^ b] += 1
log('Mt: active labels meeting repeated-helper pairs:', len(pairs_per_active), 'max pairs per label:', max(pairs_per_active.values()))
assert len(pairs_per_active) == 632 and max(pairs_per_active.values()) == 1
RESULTS['Mt_K6_dims'] = dict(dims); RESULTS['Mt_active_pairs'] = len(pairs_per_active)

# ---------------------------------------------------------------- no nine-part partition of the graph codes (x >= 24)
def no_nine_partition(rows, inv_rows, tag):
    words = sorted(graph_code_words(rows, inv_rows, 8), key=lambda w: (bin(w).count('1'), w))
    assert all(bin(w).count('1') in (6, 8) for w in words)
    n = len(words); wt = [bin(w).count('1') for w in words]
    nodes = 0; leaves = 0; found = 0
    # rank of A[rows outside O, columns in I]
    def shortened_dim(rem):
        I = [c for c in range(32) if (rem >> c) & 1]
        Orows = [r for r in range(32) if not (rem >> (32 + r)) & 1]   # rows OUTSIDE O
        vecs = []
        for r in Orows:
            v = 0
            for k, c in enumerate(I):
                if (rows[r] >> c) & 1: v |= 1 << k
            vecs.append(v)
        return len(I) - rank(vecs)
    def dfs(start, used, depth, lastw):
        nonlocal nodes, leaves, found
        nodes += 1
        if depth == 7:
            rem = ((1 << 64) - 1) ^ used
            leaves += 1
            assert bin(rem).count('1') >= 2 * lastw or True
            if shortened_dim(rem) >= 2: found += 1
            return
        remaining = 64 - bin(used).count('1')
        k = 9 - depth
        for i in range(start, n):
            if wt[i] < lastw: continue
            if wt[i] * k > remaining: break
            if words[i] & used: continue
            dfs(i + 1, used | words[i], depth + 1, wt[i])
    dfs(0, 0, 0, 0)
    log(tag, 'nine-part search: words', n, 'nodes', nodes, 'leaves', leaves, 'splits found', found)
    assert found == 0
    return nodes, leaves
RESULTS['nine_M'] = no_nine_partition(ROWS, INV_ROWS, 'M (u,Mu)')
RESULTS['nine_Mt'] = no_nine_partition(COLS, inverse_rows(COLS), 'Mt (u,M^T u)')
# eight parts exist
eight = [0x01010101 << j for j in range(8)]
assert all(apply(ROWS, b) == b for b in eight)
log('eight-part partition exists (bit families fixed by M): OK')

json.dump(RESULTS, open(__file__.replace('.py', '.json'), 'w'), indent=1, default=str)
log('ALL FINITE PREMISES RECOMPUTED AND MATCH')
