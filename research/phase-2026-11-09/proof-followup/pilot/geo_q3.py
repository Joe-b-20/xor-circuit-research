#!/usr/bin/env python3
"""geo_q3.py -- finite geometry for the q = 3 pilot (PILOT_SPEC.md section 2).  Reuses the primitives of
~/xs-campaigns/2026-11-07-sprint/qjointcheck/jc_geo.py (own boundary parse of the repository matrix, triples, pair map
PM, full values, N(h), GF(2) rank with lowest-bit pivots) and adds:
  * the FORMS of a label value l: the 2- and 4-subsets D of B with XOR l (as 64-bit masks); Lambda_1 = {l : forms(l) != {}}
    (every bright label of a normalized circuit lies in Lambda_1: the anchored carrier (h, T, b) gives D = T xor {b});
    rank(C_l) = GF(2) rank of {E + D : D in forms(l)} = rank of the differences + 1 (finite fact F6 recomputed);
  * the anchored-carrier candidates of a label l: (h = l + b, T) with T a triple of h, for every b in B with l + b not in B;
  * the byte rotation rho (bit i -> bit i+8 mod 32), the check rho(B) = B, orbits of label values.
Coordinates (python ints over GF(2)): bits 0..63 boundary (B[0..31] inputs, B[32..63] outputs), bits 64+ helper coordinates
H_i (one per helper of a configuration, assigned by the caller).
"""
import sys, itertools, json, time
from collections import defaultdict, Counter
from pathlib import Path
sys.path.insert(0, str(Path.home() / "xs-campaigns/2026-11-07-sprint/qjointcheck"))
import jc_geo  # noqa: E402

rank = jc_geo.rank
indep = jc_geo.indep


def rank_hi(vs):
    """second, independently written GF(2) rank: Gaussian elimination with HIGHEST-bit pivots (jc_geo pivots on the lowest bit)."""
    rows = []
    for v in vs:
        for p in rows:
            if v ^ p < v: v ^= p
        if v: rows.append(v); rows.sort(reverse=True)
    return len(rows)


def indep_hi(vs): return rank_hi(vs) == len(vs)


def rot(m):
    """byte rotation of a 32-bit mask: bit i -> bit (i + 8) mod 32."""
    return ((m << 8) | (m >> 24)) & 0xFFFFFFFF


class GeoQ(jc_geo.Geo):
    def __init__(self, ori):
        t0 = time.time()
        super().__init__(ori)
        B = self.B
        self.Bidx = {b: i for i, b in enumerate(B)}
        # forms: label value -> list of boundary-subset masks (2-subsets and 4-subsets with that XOR)
        forms = defaultdict(list)
        for i, j in itertools.combinations(range(64), 2):
            forms[B[i] ^ B[j]].append((1 << i) | (1 << j))
        for i, j, k, l in itertools.combinations(range(64), 4):
            forms[B[i] ^ B[j] ^ B[k] ^ B[l]].append((1 << i) | (1 << j) | (1 << k) | (1 << l))
        self.forms = dict(forms)
        self.rankC = {l: 1 + rank([D ^ ds[0] for D in ds[1:]]) for l, ds in self.forms.items()}
        self.rank_hist = Counter(self.rankC.values())
        self.by_rank = defaultdict(list)
        for l, r in self.rankC.items(): self.by_rank[r].append(l)
        # rotation: check rho(B) = B and that rho commutes with the map (rho M rho^-1 = M) through the boundary sets
        self.rotB = all(rot(b) in self.Bset for b in B)
        self.rot_inputs = all(rot(B[i]) in set(B[:32]) for i in range(32))
        self.rot_outputs = all(rot(B[i]) in set(B[32:]) for i in range(32, 64))
        self.seconds = round(time.time() - t0, 1)

    def label_rank(self, l): return self.rankC.get(l, 0)

    def carriers(self, l, r):
        """anchored-carrier candidates of label l with r represented triples: [(b, h, [triple subsets R of size r])]."""
        out = []
        for b in self.B:
            h = l ^ b
            if h in self.Bset: continue
            T = self.trip.get(h, [])
            if len(T) < r: continue
            out.append((b, h, [tuple(R) for R in itertools.combinations(T, r)]))
        return out

    def orbit(self, l):
        o = {l}; x = rot(l)
        while x not in o: o.add(x); x = rot(x)
        return o

    def is_rep(self, l): return l == min(self.orbit(l))

    def reps(self, values): return [l for l in values if self.is_rep(l)]


if __name__ == "__main__":
    for ori in sys.argv[1:] or ["Mt"]:
        G = GeoQ(ori)
        print(ori, "F3", dict(G.f3), "full values", len(G.fulls), "pair values", len(G.PM), "hub values with N(h) nonempty", len(G.N))
        print(ori, "Lambda_1 size", len(G.forms), "rank(C_l) histogram", sorted(G.rank_hist.items()))
        print(ori, "rotation maps B to B:", G.rotB, "inputs to inputs:", G.rot_inputs, "outputs to outputs:", G.rot_outputs)
        for r in range(1, 8):
            vals = [l for l, rk in G.rankC.items() if rk >= r]
            print(ori, f"labels with rank >= {r}: {len(vals)}, orbit representatives {len(G.reps(vals))}")
        tv = [h for h, t in G.trip.items()]
        print(ori, "triple values", len(tv), "orbit reps", len(G.reps(tv)), "values with >= 2 triples", sum(1 for t in G.trip.values() if len(t) >= 2))
        print(ori, f"{G.seconds}s")
