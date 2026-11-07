#!/usr/bin/env python3
"""Independent recomputation of the finite facts behind the odd-helper theorems.

Everything is rebuilt from the repo matrix file (not from the checkers' AES arithmetic),
with plain Python ints as GF(2) vectors.  Stages (argv): facts pairs h0 h1 all.

Formal coordinates: bit i (0..63) = boundary signal i (inputs 0..31, outputs 32..63),
bit 64 = helper u, bits 65.. = hidden values.  A "relation" is a formal vector whose
actual masks XOR to zero.
"""
import sys, json, time, itertools
from collections import Counter, defaultdict

MAT = "/home/joebachir20/xor-circuit-research/circuits/aes-mixcolumns/aes-mixcolumns.mat.txt"
OUT = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/oddh/indep_results.json"
results = {}

def rank(rows):
    basis = {}
    r = 0
    for x in rows:
        while x:
            p = x.bit_length() - 1
            b = basis.get(p)
            if b is None:
                basis[p] = x; r += 1; break
            x ^= b
    return r

class Basis:
    def __init__(self, rows=()):
        self.b = {}; self.n = 0
        for x in rows: self.add(x)
    def add(self, x):
        while x:
            p = x.bit_length() - 1
            b = self.b.get(p)
            if b is None:
                self.b[p] = x; self.n += 1; return True
            x ^= b
        return False
    def reduce(self, x):
        while x:
            p = x.bit_length() - 1
            b = self.b.get(p)
            if b is None: return x
            x ^= b
        return 0
    def copy(self):
        c = Basis(); c.b = dict(self.b); c.n = self.n; return c

# ---------------- matrix and boundary ----------------
lines = [l.split() for l in open(MAT) if l.strip()]
assert lines[1] == ["32", "32"]
rowsM = [[int(t) for t in l] for l in lines[2:34]]
assert len(rowsM) == 32 and all(len(r) == 32 for r in rowsM)
OUTM = [sum(rowsM[o][i] << i for i in range(32)) for o in range(32)]   # mask of output o over inputs

# cross-check against byte arithmetic (02,03,01,01 ; 0x11b), as in the checkers
def mul(a, b):
    r = 0
    while b:
        if b & 1: r ^= a
        a <<= 1
        if a & 256: a ^= 0x11b
        b >>= 1
    return r
C = [[2,3,1,1],[1,2,3,1],[1,1,2,3],[3,1,1,2]]
OUT2 = [0]*32
for o in range(32):
    for i in range(32):
        if (mul(C[o//8][i//8], 1 << (i % 8)) >> (o % 8)) & 1: OUT2[o] |= 1 << i
assert OUT2 == OUTM, "repo matrix disagrees with byte-arithmetic MixColumns"

B = [1 << i for i in range(32)] + OUTM
Bset = set(B); Bidx = {b: i for i, b in enumerate(B)}
assert len(Bset) == 64 and all(bin(b).count("1") % 2 == 1 for b in B)
def rho(x): return ((x << 8) | (x >> 24)) & 0xffffffff
assert set(rho(b) for b in B) == Bset, "byte rotation does not preserve the boundary"

# pairs, triples, quads (formal vectors over 64 boundary coordinates)
P = {}
for i in range(64):
    for j in range(i+1, 64):
        v = B[i] ^ B[j]
        assert v not in P, "Sidon fails"
        P[v] = (1 << i) | (1 << j)
T = defaultdict(list)
for i in range(64):
    for j in range(i+1, 64):
        for k in range(j+1, 64):
            T[B[i]^B[j]^B[k]].append((1<<i)|(1<<j)|(1<<k))
T = dict(T)
assert not (set(T) & Bset) and 0 not in T
R6rows = []
for v, L in T.items():
    for a in range(len(L)):
        for b in range(a+1, len(L)):
            R6rows.append(L[a] ^ L[b])
R6 = Basis(R6rows)

def w(v): return len(T.get(v, ()))

def stage_facts():
    tm = Counter(len(L) for L in T.values())
    results["sidon_pairs"] = len(P)
    results["triple_multiplicity_hist"] = dict(tm)
    results["R6_distinct_six_relations"] = len(set(R6rows))
    results["R6_rank"] = R6.n
    print("pairs", len(P), "triple mult", dict(tm), "six-relations", len(set(R6rows)), "rank R6", R6.n)
    assert len(P) == 2016 and dict(tm) == {1: 40704, 2: 360, 3: 80} and R6.n == 20
    # 4-relations among B: none (Sidon) => r(h=0)=0
    # quad / pair value families and their difference ranks mod R6 (capacity for h=0)
    global Q
    Q = defaultdict(list)
    for v, f in P.items(): Q[v].append(f)
    for i, j, k, l in itertools.combinations(range(64), 4):
        Q[B[i]^B[j]^B[k]^B[l]].append((1<<i)|(1<<j)|(1<<k)|(1<<l))
    Q = dict(Q)
    nsub = sum(len(L) for L in Q.values())
    caphist = Counter()
    global ACTIVE, CAP0
    ACTIVE = {}; CAP0 = {}
    for v, L in Q.items():
        if len(L) >= 2:
            bs = R6.copy()
            for f in L[1:]: bs.add(f ^ L[0])
            c = bs.n - R6.n
            if c:
                caphist[c] += 1; ACTIVE[v] = c
                # a pair value has only one representation modulo R6? check
                if v in P: assert False, "pair value with extra 4-reps not in R6"
    results["two_four_subsets"] = nsub
    results["quad_capacity_hist_h0"] = dict(caphist)
    results["active_labels"] = len(ACTIVE)
    print("2/4-subsets", nsub, "quad difference ranks mod R6", dict(caphist), "active", len(ACTIVE))
    assert nsub == 637392 and dict(caphist) == {1: 2046, 2: 291, 3: 36}
    # pair values: any 4-rep of a pair value differs from the pair by a <=6 relation: check directly
    bad = 0
    for v, f in P.items():
        for g in Q[v]:
            if g != f and R6.reduce(g ^ f): bad += 1
    results["pair_value_extra_reps_outside_R6"] = bad
    assert bad == 0

def stage_pairs():
    """Rebuild the r>=4 candidate domain of section 4 and the exact 4-relation ranks."""
    t0 = time.time()
    high = [v for v, L in T.items() if len(L) >= 2]
    assert len(high) == 440
    cand = set()
    Tkeys = list(T.keys())
    for u in high:
        wu = w(u)
        for v in Tkeys:
            if v != u and wu + len(T[v]) >= 4:
                cand.add((min(u,v) << 32) | max(u,v))
        for p in P:
            v = u ^ p
            if v != u and v not in Bset and wu + w(v) >= 3:
                cand.add((min(u,v) << 32) | max(u,v))
    print("candidates", len(cand), "gen time", round(time.time()-t0,1))
    hist = Counter(); detail = Counter(); maxr = 0
    for key in cand:
        u, v = key >> 32, key & 0xffffffff
        rows = [f | (1 << 64) for f in T.get(u, ())] + [f | (1 << 65) for f in T.get(v, ())]
        d = 0
        if (u ^ v) in P:
            rows.append(P[u ^ v] | (3 << 64)); d = 1
        r = rank(rows)
        hist[r] += 1; maxr = max(maxr, r)
        detail[(min(w(u),w(v)), max(w(u),w(v)), d, r)] += 1
    results["candidate_pairs"] = len(cand)
    results["pair_rank_hist"] = dict(hist)
    results["pair_rank_detail"] = {str(k): n for k, n in sorted(detail.items())}
    results["max_pair_rank"] = maxr
    print("rank hist", dict(hist), "max", maxr, "time", round(time.time()-t0,1))
    assert len(cand) == 3592052 and dict(hist) == {3: 113892, 4: 3444740, 5: 30572, 6: 2848}

def exposed_vec0(s):
    """h=0: formal 2-vector if s is a boundary pair value."""
    return P.get(s)

def stage_h0():
    """h=0, p=3 equality case: three capacity-3 labels with all pair sums exposed; joint rank mod R6 must be < 15."""
    labs = [v for v, c in ACTIVE.items() if c == 3]
    assert len(labs) == 36
    info = {}
    for v in labs:
        L = Q[v]; bs = R6.copy(); diffs = []
        for f in L[1:]:
            if bs.add(f ^ L[0]): diffs.append(f ^ L[0])
        info[v] = (L[0], diffs)
    tri = 0; hist = Counter(); maxr = 0
    pair_edges = 0
    for a, b, c in itertools.combinations(labs, 3):
        pab, pac, pbc = P.get(a^b), P.get(a^c), P.get(b^c)
        npairs = (pab is not None) + (pac is not None) + (pbc is not None)
        if npairs == 0: continue
        pair_edges += 1
        # H <= sum(1+c_i) + npairs = 12 + npairs ; need H >= 15 -> npairs == 3 ; compute exactly anyway
        rows = list(R6.b.values())
        for t, (ref, diffs) in zip((a,b,c), (info[a], info[b], info[c])):
            rows.append(ref | (1 << (65 + (a,b,c).index(t))))
            rows += diffs
        for (x, y), pv in (((0,1), pab), ((0,2), pac), ((1,2), pbc)):
            if pv is not None: rows.append(pv | (1 << (65+x)) | (1 << (65+y)))
        H = rank(rows) - R6.n
        hist[(npairs, H)] += 1; maxr = max(maxr, H); tri += 1
    results["h0_cap3_labels"] = len(labs)
    results["h0_triangles_with_some_exposed_pair"] = tri
    results["h0_triangle_hist_(npairs,H)"] = {str(k): n for k, n in sorted(hist.items())}
    results["h0_max_H"] = maxr
    print("h0: 36 labels; triples with >=1 exposed pair", tri, "hist", dict(hist), "max H", maxr, "(need <15)")

def five_reps(u):
    """All formal 5-subsets of B with XOR u (each found via its 2+3 splits; deduplicated)."""
    out = set()
    for pv, pf in P.items():
        for tf in T.get(u ^ pv, ()):
            if tf & pf == 0: out.add(tf | pf)
    return out

def stage_h1():
    """h=1 with p=3 (the only open case for G<=90): u full (w=3). For each rotation orbit of full u:
    d(u)=dim S6(B+u)/R6, labels with capacity c(w)>=1 mod S6, and all triangles with
    3+sum c + exposed pairs >= 16-d(u); exact joint rank must be < 16-d(u)."""
    full = sorted(v for v, L in T.items() if len(L) == 3)
    assert len(full) == 80
    reps = sorted(set(min(v, rho(v), rho(rho(v)), rho(rho(rho(v)))) for v in full))
    results["h1_full_orbits"] = len(reps)
    print("h1: full values", len(full), "orbits", len(reps))
    # also: d(u) for all repeated values (needed for p=2 case: d(u)<=3 when w>=2)
    dmax_rep = 0
    for u in (v for v, L in T.items() if len(L) >= 2):
        bs = R6.copy()
        for f in T[u]: bs.add(f | (1 << 64))
        for f in five_reps(u): bs.add(f | (1 << 64))
        dmax_rep = max(dmax_rep, bs.n - R6.n)
    results["h1_max_d_over_repeated_values"] = dmax_rep
    print("max d(u) over the 440 repeated values:", dmax_rep)
    summary = []
    UBIT = 1 << 64
    for u in reps:
        t0 = time.time()
        S6 = R6.copy()
        for f in T[u]: S6.add(f | UBIT)
        for f in five_reps(u): S6.add(f | UBIT)
        d = S6.n - R6.n
        R = 16 - d                      # required hidden rank modulo S6(O)
        # exposed even values: boundary pairs and u+b
        def expvec(s):
            f = P.get(s)
            if f is not None: return f
            if (s ^ u) in Bidx: return UBIT | (1 << Bidx[s ^ u])
            return None
        # candidate labels with c(w)>=1: active quad labels, or u+triple values that also have a quad rep
        candl = set(ACTIVE)
        for tv in T:
            wv = tv ^ u
            if wv in Q: candl.add(wv)
        A = {}
        for wv in candl:
            if wv == 0 or expvec(wv) is not None: continue
            L = list(Q.get(wv, ())) + [f | UBIT for f in T.get(wv ^ u, ())]
            if len(L) < 2: continue
            bs = S6.copy(); diffs = []
            for f in L[1:]:
                if bs.add(f ^ L[0]): diffs.append(f ^ L[0])
            if diffs: A[wv] = (len(diffs), L[0], diffs)
        chist = Counter(c for c, _, _ in A.values())
        cmax = max(chist)
        labs = sorted(A, key=lambda v: -A[v][0])
        # enumerate triangles in A^3 with 3 + sum c + pairs >= R  (pairs<=3)
        n_checked = 0; Hmax = -1; Hhist = Counter()
        def joint(tr, pv):
            rows = list(S6.b.values())
            for i, wv in enumerate(tr):
                c, ref, diffs = A[wv]
                rows.append(ref | (1 << (65 + i))); rows += diffs
            for (x, y), f in pv.items():
                rows.append(f | (1 << (65+x)) | (1 << (65+y)))
            return rank(rows) - S6.n
        n = len(labs)
        for i in range(n):
            ci = A[labs[i]][0]
            if 3 + ci + 2*cmax + 3 < R: break
            for j in range(i+1, n):
                cj = A[labs[j]][0]
                if 3 + ci + cj + cmax + 3 < R: break
                pij = expvec(labs[i] ^ labs[j])
                base = 3 + ci + cj + (pij is not None)
                for k in range(j+1, n):
                    ck = A[labs[k]][0]
                    if base + ck + 2 < R: break
                    pik = expvec(labs[i] ^ labs[k]); pjk = expvec(labs[j] ^ labs[k])
                    if base + ck + (pik is not None) + (pjk is not None) < R: continue
                    pv = {}
                    if pij is not None: pv[(0,1)] = pij
                    if pik is not None: pv[(0,2)] = pik
                    if pjk is not None: pv[(1,2)] = pjk
                    H = joint((labs[i], labs[j], labs[k]), pv)
                    n_checked += 1; Hhist[H] += 1; Hmax = max(Hmax, H)
        # third label with c=0 (not in A): needs c_i+c_j+pairs >= R-3 with pairs<=3 -> c_i+c_j >= R-6
        n0 = 0; H0max = -1
        if 2*cmax >= R - 6:
            EXP = list(P) + [u ^ b for b in B]
            for i in range(n):
                ci = A[labs[i]][0]
                if ci + cmax < R - 6: break
                for j in range(i+1, n):
                    cj = A[labs[j]][0]
                    if ci + cj < R - 6: break
                    pij = expvec(labs[i] ^ labs[j])
                    need = R - 3 - ci - cj - (pij is not None)   # pairs needed from the third label (<=2)
                    if need > 2: continue
                    cands = set(labs[i] ^ s for s in EXP)
                    if need == 2: cands &= set(labs[j] ^ s for s in EXP)
                    else: cands |= set(labs[j] ^ s for s in EXP)
                    for wv in cands:
                        if wv == 0 or wv in A or expvec(wv) is not None: continue
                        pik = expvec(labs[i] ^ wv); pjk = expvec(labs[j] ^ wv)
                        if 3 + ci + cj + (pij is not None) + (pik is not None) + (pjk is not None) < R: continue
                        L = list(Q.get(wv, ())) + [f | UBIT for f in T.get(wv ^ u, ())]
                        if not L: continue   # a label with no 4-representation at all cannot appear in a one-hidden equation
                        rows = list(S6.b.values())
                        for ii, (c, ref, diffs) in enumerate((A[labs[i]], A[labs[j]])):
                            rows.append(ref | (1 << (65 + ii))); rows += diffs
                        rows.append(L[0] | (1 << 67))
                        for f in L[1:]: rows.append(f ^ L[0])
                        if pij is not None: rows.append(pij | (1<<65) | (1<<66))
                        if pik is not None: rows.append(pik | (1<<65) | (1<<67))
                        if pjk is not None: rows.append(pjk | (1<<66) | (1<<67))
                        H = rank(rows) - S6.n
                        n0 += 1; H0max = max(H0max, H)
        ok = (Hmax < R) and (H0max < R)
        rec = {"u": u, "d": d, "required_H": R, "labels_c>=1": len(A), "cap_hist": dict(chist),
               "triangles_checked": n_checked, "H_hist": dict(Hhist), "H_max": Hmax,
               "c0_third_checked": n0, "H_max_c0": H0max, "excluded": ok, "sec": round(time.time()-t0,1)}
        summary.append(rec); print(rec, flush=True)
    results["h1_orbits"] = summary
    results["h1_all_excluded"] = all(r["excluded"] for r in summary)

def stage_h1tab():
    """Single-helper short-relation table: d(u) = dim S6(B+u)/R6.
    Needed: d(u) <= 12 for every odd u (h=1,p=0) and d(u) <= 8 whenever w(u)>=1 (h=1,p=1);
    the archive claims d<=7 (w=0), 5 (w=1), 3 (w>=2)."""
    import numpy as np
    t0 = time.time()
    # exact d(u) for every boundary-triple value (w>=1): 41,144 values
    dh = Counter()
    for u, L in T.items():
        bs = R6.copy()
        for f in L: bs.add(f | (1 << 64))
        for f in five_reps(u): bs.add(f | (1 << 64))
        dh[(len(L), bs.n - R6.n)] += 1
    results["h1_d_table_w>=1_(w,d):count"] = {str(k): n for k, n in sorted(dh.items())}
    print("d(u) table for w>=1:", dict(sorted(dh.items())), round(time.time()-t0,1), "s", flush=True)
    # w=0 values: d(u) <= number of 5-subset representations; count multiplicities of all C(64,5) XORs
    Barr = np.array(B, dtype=np.uint32)
    vals = []
    for i, j, k in itertools.combinations(range(64), 3):
        base = B[i] ^ B[j] ^ B[k]
        rest = Barr[k+1:]
        if len(rest) < 2: continue
        a = rest[:, None] ^ rest[None, :]
        iu = np.triu_indices(len(rest), 1)
        vals.append(a[iu] ^ np.uint32(base))
    vals = np.concatenate(vals)
    assert len(vals) == 7624512
    uniq, cnt = np.unique(vals, return_counts=True)
    wset = set(T)
    mult = Counter()
    big = []
    for v, c in zip(uniq.tolist(), cnt.tolist()):
        if v in wset: continue
        mult[c] += 1
        if c >= 7: big.append(v)
    results["five_subset_multiplicity_hist_w0"] = dict(sorted(mult.items()))
    print("5-subset multiplicities among w=0 values:", dict(sorted(mult.items())), flush=True)
    dmax0 = 0; d0h = Counter()
    for u in big:
        bs = R6.copy()
        for f in five_reps(u): bs.add(f | (1 << 64))
        d = bs.n - R6.n; d0h[d] += 1; dmax0 = max(dmax0, d)
    results["h1_w0_values_with_>=7_reps"] = len(big)
    results["h1_w0_exact_d_hist_for_those"] = dict(sorted(d0h.items()))
    results["h1_max_d_w0"] = max(dmax0, max((c for c in mult if c < 7), default=0))
    print("w=0 values with >=7 reps:", len(big), "exact d hist", dict(sorted(d0h.items())),
          "=> max d over all w=0 values <=", results["h1_max_d_w0"], round(time.time()-t0,1), "s")

if __name__ == "__main__":
    stages = sys.argv[1:] or ["all"]
    if "all" in stages: stages = ["facts", "pairs", "h0", "h1"]
    t0 = time.time()
    stage_facts() if "facts" in stages or True else None
    for s in stages:
        if s == "pairs": stage_pairs()
        if s == "h0": stage_h0()
        if s == "h1": stage_h1()
        if s == "h1tab": stage_h1tab()
    try:
        old = json.load(open(OUT))
        old.update(results); results = old
    except Exception:
        pass
    results["total_seconds"] = round(time.time()-t0, 1)
    json.dump(results, open(OUT, "w"), indent=1)
    print("done", results["total_seconds"], "s ->", OUT)
