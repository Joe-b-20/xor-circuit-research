#!/usr/bin/env python3
"""recon-check: OWN re-derivation (standard library, from AES byte arithmetic) of the finite facts behind the push5/push6 rows.
Boundary conventions as the package (finite_facts.py): inputs = unit vectors (indices 0..31), outputs = rows of M (orientation
'M') or of M^T (orientation 'Mt') (indices 32..63); output j has class j mod 8.

Stages (each prints its counts; expected values from the archive texts in brackets):
  base   : Sidon pairs (2,016 distinct), triple multiplicities (max 3; 40,704/360/80 M, 40,320/504/112 Mt), repeated (440/616)
           and full (80/112) values, one output-bit class per repeated value (88 per class), core C = 20/28, rank-4 excess span
           per class, full pairs: 48 independent pairs per class with 18 distinct reference pairs and 4 outputs in the union,
           palettes of 48 pairs per class pairwise disjoint, full-pair incompatibility (360/504 rank-5 pairs with a pair difference)
  contact: contact-pair fact (11,520/16,992 pairs of distinct repeated values with a boundary-pair difference; endpoints in the
           32 inputs + core; output endpoints in the class of one of the two values; two-class labels only in adjacent classes)
  code   : Mt short code: zero-sum boundary subsets of weight 6/8/10/12 (84/276/1,300/8,112), ranks 28/29/29/32, 736 weight-12
           words nonzero mod R10; |P| = 30,340, |P3| = 6,160 (M for information: 248/1,476/10,216 at 8/10/12, rank 32 at <= 8)
  F1F2   : 4,250,400 unordered 4+4+4 splits of the 736 words: 3,361,744 / 763,992 / 124,664 / 0 with 0/1/2/3 parts in P;
           score-two splits grouped by the third value: 5,143 active (2,599 rank 1, 2,544 rank 2, none rank 3); P3: 228, all rank 1
  F3     : 340,032 unordered 6+6 splits: 47,184 with a repeated triple in each half, 8,804 active d, all rank 1; strong: 2,880 / 320
  F5     : 4,800 full-pair pivots with d outside P and the pair values (504 in pairs, 912 in P): every row Fd + Fa + Fb with
           a, b in P (917,376) or a a pair value, b in P (199,184) reduces to zero mod R10
usage: python3 finite_facts_check.py [stages...]   (default: base contact code F1F2 F3 F5)
"""
import sys, json, time
from itertools import combinations
from collections import Counter, defaultdict
sys.dont_write_bytecode = True
T0 = time.time()
def log(*a): print(f"[{time.time()-T0:7.1f}s]", *a, flush=True)


# ---------------------------------------------------------------- AES MixColumns over GF(2^8), x^8 + x^4 + x^3 + x + 1
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
    coef = [2, 3, 1, 1]; rows = [0] * 32
    for col in range(4):
        for k in range(4):
            c, ib = coef[k], (col + k) % 4
            for in_bit in range(8):
                v = gmul(c, 1 << in_bit)
                for out_bit in range(8):
                    if (v >> out_bit) & 1: rows[col * 8 + out_bit] ^= 1 << (ib * 8 + in_bit)
    return rows
ROWS = mixcolumns_rows()
COLS = [sum(((ROWS[r] >> c) & 1) << r for r in range(32)) for c in range(32)]
UNITS = [1 << i for i in range(32)]
def apply(rows, u): return sum((bin(rows[r] & u).count("1") & 1) << r for r in range(32))
assert apply(ROWS, (0xd4 | 0xbf << 8 | 0x5d << 16 | 0x30 << 24)) == (0x04 | 0x66 << 8 | 0x81 << 16 | 0xe5 << 24)   # FIPS-197 example
BOUND = {"M": UNITS + ROWS, "Mt": UNITS + COLS}
pc = lambda x: bin(x).count("1")


def inverse_rows(rows):
    """rows of A^{-1} over GF(2) (row c = the set of output rows whose XOR is the unit input vector e_c)."""
    n = 32; m = [(rows[r], 1 << r) for r in range(n)]   # (row over inputs, which outputs were combined)
    piv = []
    for c in range(n):
        k = next(i for i in range(len(piv), n) if (m[i][0] >> c) & 1)
        m[len(piv)], m[k] = m[k], m[len(piv)]
        pr = m[len(piv)]
        for i in range(n):
            if i != len(piv) and (m[i][0] >> c) & 1: m[i] = (m[i][0] ^ pr[0], m[i][1] ^ pr[1])
        piv.append(c)
    inv = [0] * n
    for i in range(n): inv[piv[i]] = m[i][1]
    return inv


class Basis:
    """XOR echelon basis over GF(2) on Python ints (highest bit pivots)."""
    def __init__(self): self.piv = {}
    def reduce(self, v):
        while v:
            hb = v.bit_length() - 1
            if hb not in self.piv: return v
            v ^= self.piv[hb]
        return 0
    def add(self, v):
        v = self.reduce(v)
        if v: self.piv[v.bit_length() - 1] = v; return True
        return False
    def dim(self): return len(self.piv)
def rank(vecs):
    b = Basis()
    for v in vecs: b.add(v)
    return b.dim()
def qrank(r10, vecs):
    """rank of vecs modulo the span of the basis r10: new pivots when they are added to a copy of r10."""
    b = Basis(); b.piv = dict(r10.piv); n = 0
    for v in vecs:
        if b.add(v): n += 1
    return n


OUT = {}
def stage_base(ori):
    B = BOUND[ori]; n = 64
    cls = lambda i: (i - 32) % 8 if i >= 32 else None
    pairs = {}
    for i, j in combinations(range(n), 2):
        v = B[i] ^ B[j]; assert v not in pairs and v, "Sidon violated"; pairs[v] = (i, j)
    trip = defaultdict(list)
    for i, j, k in combinations(range(n), 3): trip[B[i] ^ B[j] ^ B[k]].append((i, j, k))
    mult = Counter(len(t) for t in trip.values()); assert max(mult) <= 3
    rep = {v: t for v, t in trip.items() if len(t) >= 2}; full = {v: t for v, t in trip.items() if len(t) == 3}
    # class fact: every output coordinate of every triple form of a repeated value has the same class
    klass = {}
    for v, forms in rep.items():
        ks = {cls(i) for f in forms for i in f if i >= 32}
        assert len(ks) == 1, ("repeated value with output coordinates in two classes", v, ks)
        klass[v] = ks.pop()
    per_class = Counter(klass.values()); full_per_class = Counter(klass[v] for v in full)
    core = sorted({i for v, forms in rep.items() for f in forms for i in f if i >= 32})
    # rank-4 excess span per class (full values: T1+T2, T1+T3 as 64-bit index words)
    word = lambda f: sum(1 << i for i in f)
    exc_rank = {}
    for k in sorted(set(klass.values())):
        vecs = []
        for v in full:
            if klass[v] != k: continue
            f1, f2, f3 = (word(f) for f in full[v]); vecs += [f1 ^ f2, f1 ^ f3]
        exc_rank[k] = rank(vecs)
    # full pairs: helper relations h + T (66 coordinates: bit 64 = helper a, bit 65 = helper b)
    indep_per_class = Counter(); bad18 = 0; bad_union = 0; rank5_pairdiff = 0; rank6_nopair = 0; other = 0
    palette = defaultdict(set)
    for v in full:
        for f in full[v]:
            for a, b in combinations(f, 2): palette[klass[v]].add((a, b))
    for v1, v2 in combinations(sorted(full), 2):
        rows = [word(f) | (1 << 64) for f in full[v1]] + [word(f) | (1 << 65) for f in full[v2]]
        r = rank(rows); pd = (v1 ^ v2) in pairs
        if r == 5 and pd: rank5_pairdiff += 1
        elif r == 6 and not pd: rank6_nopair += 1
        else: other += 1
        if klass[v1] == klass[v2] and r == 6:
            indep_per_class[klass[v1]] += 1
            prs = [(a, b) for f in full[v1] + full[v2] for a, b in combinations(f, 2)]
            if len(set(prs)) != 18: bad18 += 1
            union = set().union(*[set(f) for f in full[v1] + full[v2]])
            if sum(1 for i in union if i >= 32) != 4 or sum(1 for i in union if i < 32) != 8: bad_union += 1
    pal_sizes = {k: len(s) for k, s in palette.items()}
    pal_disjoint = all(not (palette[a] & palette[b]) for a, b in combinations(sorted(palette), 2))
    # the singleton census of section 4: output coordinates per full value (o in {2,3,4}) and the minimum OO count 5 - o
    o_hist = Counter(len({i for f in full[v] for i in f if i >= 32}) for v in full)
    res = dict(pairs=len(pairs), triple_multiplicity_hist={str(k): v for k, v in sorted(mult.items())}, repeated=len(rep), full=len(full),
               classes=sorted(set(klass.values())), repeated_per_class=dict(sorted(per_class.items())), full_per_class=dict(sorted(full_per_class.items())),
               core_outputs=len(core), core_classes=sorted({cls(i) for i in core}), excess_rank_per_class=exc_rank,
               independent_full_pairs_per_class=dict(sorted(indep_per_class.items())), independent_full_pairs=sum(indep_per_class.values()),
               pairs_with_18_distinct_references_failing=bad18, pairs_with_union_not_4_outputs_8_inputs=bad_union,
               full_pairs_rank5_with_pair_difference=rank5_pairdiff, full_pairs_rank6_no_pair_difference=rank6_nopair, full_pairs_other=other,
               palette_sizes=pal_sizes, palettes_pairwise_disjoint=pal_disjoint, full_output_count_hist={str(k): v for k, v in sorted(o_hist.items())})
    log(ori, "base:", json.dumps(res))
    return res, dict(B=B, pairs=pairs, trip=trip, rep=rep, full=full, klass=klass, core=set(core), cls=cls)


def stage_contact(ori, S):
    B, pairs, rep, klass, core, cls = S["B"], S["pairs"], S["rep"], S["klass"], S["core"], S["cls"]
    reps = sorted(rep); n_pairs = 0; bad_core = 0; bad_class = 0; two_class = Counter(); labels_two = defaultdict(set)
    allowed = set(range(32)) | core
    for H, K in combinations(reps, 2):
        d = H ^ K
        if d not in pairs: continue
        n_pairs += 1; i, j = pairs[d]
        if not (i in allowed and j in allowed): bad_core += 1
        for e in (i, j):
            if e >= 32 and cls(e) not in (klass[H], klass[K]): bad_class += 1
        if klass[H] != klass[K]:
            two_class[tuple(sorted((klass[H], klass[K])))] += 1
            labels_two[tuple(sorted((klass[H], klass[K])))].add(H ^ B[i])      # the label e = H + B_i = K + B_j
    # a label with contacts in two classes: which class pairs occur; never three classes
    label_classes = defaultdict(set)
    for H in reps:
        for i in range(64):
            e = H ^ B[i]
            label_classes[e].add(klass[H])
    max_classes = max(len(s) for s in label_classes.values())
    res = dict(candidate_pairs=len(reps) * (len(reps) - 1) // 2, pairs_with_boundary_pair_difference=n_pairs, endpoints_outside_inputs_plus_core=bad_core,
               output_endpoints_outside_the_two_classes=bad_class, two_class_pairs={f"{a}-{b}": c for (a, b), c in sorted(two_class.items())},
               labels_with_contacts_in_two_classes={f"{a}-{b}": len(s) for (a, b), s in sorted(labels_two.items())},
               max_classes_per_label_all_conceivable_contacts=max_classes)
    log(ori, "contact:", json.dumps(res))
    return res


def short_code(ori, maxw=12):
    """all zero-sum boundary subsets (64-bit index words) of weight <= maxw: a word is (S outputs, T inputs) with XOR_S row = 1_T;
    enumerate |S| <= maxw/2 and |T| <= maxw/2 (one of them is <= 6)."""
    rows = ROWS if ori == "M" else COLS
    inv = inverse_rows(rows)             # inv[c] = set of outputs whose XOR is e_c
    words = set()
    half = maxw // 2
    for k in range(1, half + 1):
        for S in combinations(range(32), k):
            T = 0
            for j in S: T ^= rows[j]
            if k + pc(T) <= maxw: words.add(T | (sum(1 << (32 + j) for j in S)))
        for Tset in combinations(range(32), k):
            Smask = 0; T = 0
            for c in Tset: Smask ^= inv[c]; T |= 1 << c
            if k + pc(Smask) <= maxw: words.add(T | (Smask << 32))
    return words


def stage_code(ori, S):
    words = short_code(ori)
    byw = defaultdict(list)
    for w in words: byw[pc(w)].append(w)
    hist = {w: len(byw[w]) for w in sorted(byw)}
    ranks = {}; b = Basis()
    for w in sorted(byw):
        for v in byw[w]: b.add(v)
        ranks[w] = b.dim()
    r10 = Basis()
    for w in sorted(byw):
        if w <= 10:
            for v in byw[w]: r10.add(v)
    active = [v for v in byw.get(12, []) if r10.reduce(v)]
    B, pairs, rep, full = S["B"], S["pairs"], S["rep"], S["full"]
    P = {H ^ B[i] for H in rep for i in range(64)} - set(pairs)
    P3 = {H ^ B[i] for H in full for i in range(64)} - set(pairs)
    res = dict(weight_hist=hist, cumulative_rank=ranks, dim_R10=r10.dim(), weight12_nonzero_mod_R10=len(active), P=len(P), P3=len(P3))
    log(ori, "code:", json.dumps(res))
    S.update(r10=r10, active=active, P=P, P3=P3)
    return res


def stage_F1F2(ori, S):
    B, r10, active, P, P3 = S["B"], S["r10"], S["active"], S["P"], S["P3"]
    score = Counter(); byw = defaultdict(list); byw3 = defaultdict(list); n_splits = 0
    for word in active:
        idx = [i for i in range(64) if (word >> i) & 1]; assert len(idx) == 12
        red = r10.reduce(word); assert red
        val = {}
        for c in combinations(idx, 4):
            x = 0
            for i in c: x ^= B[i]
            val[c] = x
        first = idx[0]; rest = idx[1:]
        for c1 in combinations(rest, 3):
            A = (first,) + c1
            rem = [i for i in rest if i not in c1]
            f2 = rem[0]
            for c2 in combinations(rem[1:], 3):
                Bq = (f2,) + c2
                Cq = tuple(i for i in rem[1:] if i not in c2)
                n_splits += 1
                vals = (val[A], val[Bq], val[Cq])
                inP = [v in P for v in vals]; s = sum(inP); score[s] += 1
                if s == 2:
                    w = vals[inP.index(False)]; byw[w].append(red)
                inP3 = [v in P3 for v in vals]
                if sum(inP3) == 2:
                    w = vals[inP3.index(False)]; byw3[w].append(red)
    rk = Counter(qrank(r10, v) for v in byw.values()); rk3 = Counter(qrank(r10, v) for v in byw3.values())
    res = dict(splits=n_splits, splits_by_parts_in_P={str(k): v for k, v in sorted(score.items())}, F1_three_parts_in_P=score.get(3, 0),
               F2_active_w=len(byw), F2_rank_hist={str(k): v for k, v in sorted(rk.items())}, F2_P3_active_w=len(byw3), F2_P3_rank_hist={str(k): v for k, v in sorted(rk3.items())})
    log(ori, "F1F2:", json.dumps(res))
    return res


def stage_F3(ori, S):
    B, r10, active, rep, full = S["B"], S["r10"], S["active"], S["rep"], S["full"]
    n = 0; qual = 0; byd = defaultdict(list); qual3 = 0; byd3 = defaultdict(list)
    for word in active:
        idx = [i for i in range(64) if (word >> i) & 1]; red = r10.reduce(word)
        first = idx[0]; rest = idx[1:]
        def has_triple(half, pool):
            for t in combinations(half, 3):
                if (B[t[0]] ^ B[t[1]] ^ B[t[2]]) in pool: return True
            return False
        for c in combinations(rest, 5):
            h1 = (first,) + c; h2 = tuple(i for i in rest if i not in c); n += 1
            d = 0
            for i in h1: d ^= B[i]
            if has_triple(h1, rep) and has_triple(h2, rep): qual += 1; byd[d].append(red)
            if has_triple(h1, full) and has_triple(h2, full): qual3 += 1; byd3[d].append(red)
    rk = Counter(qrank(r10, v) for v in byd.values()); rk3 = Counter(qrank(r10, v) for v in byd3.values())
    res = dict(splits_6_6=n, qualifying_splits=qual, active_d=len(byd), rank_hist={str(k): v for k, v in sorted(rk.items())},
               strong_qualifying=qual3, strong_active_d=len(byd3), strong_rank_hist={str(k): v for k, v in sorted(rk3.items())})
    log(ori, "F3:", json.dumps(res))
    return res


def stage_F5(ori, S):
    B, r10, pairs, rep, full, P = S["B"], S["r10"], S["pairs"], S["rep"], S["full"], S["P"]
    word = lambda f: sum(1 << i for i in f)
    form = {}                                   # one chosen 4-form (index word) per value of P: first repeated triple + one coordinate
    for H in sorted(rep):
        tw = word(rep[H][0])
        for i in range(64):
            v = H ^ B[i]
            if v in P and v not in form: form[v] = tw ^ (1 << i)
    assert set(form) == P
    Plist = sorted(P); Pset = P
    fulls = sorted(full); n_pair = n_P = n_rest = 0; nPP = nRP = 0; nonzero = 0; d_values = set(); d_multi = Counter()
    for H1, H2 in combinations(fulls, 2):
        d = H1 ^ H2
        if d in pairs: n_pair += 1; continue
        if d in Pset: n_P += 1; continue
        n_rest += 1; d_multi[d] += 1
        Fd = word(full[H1][0]) ^ word(full[H2][0])
        for a in Plist:
            b = a ^ d
            if b in Pset and a < b:
                nPP += 1
                if r10.reduce(Fd ^ form[a] ^ form[b]): nonzero += 1
        for a, (i, j) in pairs.items():
            b = a ^ d
            if b in Pset:
                nRP += 1
                if r10.reduce(Fd ^ (1 << i) ^ (1 << j) ^ form[b]): nonzero += 1
    res = dict(full_pairs=len(fulls) * (len(fulls) - 1) // 2, d_in_pairs=n_pair, d_in_P=n_P, pivots=n_rest, distinct_d=len(d_multi),
               d_with_two_full_pairs=sum(1 for v in d_multi.values() if v == 2), PP_alternatives=nPP, RP_alternatives=nRP, nonzero_remainders=nonzero)
    log(ori, "F5:", json.dumps(res))
    return res


if __name__ == "__main__":
    stages = sys.argv[1:] or ["base", "contact", "code", "F1F2", "F3", "F5"]
    out = {}
    for ori in ("M", "Mt"):
        res, S = stage_base(ori); out[ori] = {"base": res}
        if "contact" in stages: out[ori]["contact"] = stage_contact(ori, S)
        if "code" in stages: out[ori]["code"] = stage_code(ori, S)
        if ori == "Mt":
            if "F1F2" in stages: out[ori]["F1F2"] = stage_F1F2(ori, S)
            if "F3" in stages: out[ori]["F3"] = stage_F3(ori, S)
            if "F5" in stages: out[ori]["F5"] = stage_F5(ori, S)
    out["seconds"] = round(time.time() - T0, 1)
    json.dump(out, open(__file__.replace(".py", ".json"), "w"), indent=1)
    log("done")
