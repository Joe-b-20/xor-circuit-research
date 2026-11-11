#!/usr/bin/env python3
"""Finite fact candidate: which pairs of ANCHORED hubs (r = 1 or 2 represented triples, m = 0 full-met labels) can share
a HUB-ONLY missing label?  (A MEASUREMENT of GF(2) ranks; the mathematics that makes it a necessary condition is Lemma J
of Addendum D with K = {k, k'}, S_k = S_k' = empty, X = {(k, k')}: the family
      { H + T : T in R } u { H' + T' : T' in R' } u { H + H' + P(h + h') }
is linearly independent in every normalized circuit in which hubs with masks h, h', represented triple sets R, R'
share a hub-only label; by D.1 the shared label forces h + h' to be a pair value.)
Uses the geometry primitives of qjointcheck/jc_geo.py (own boundary parse of the repository matrix, lowest-bit pivots).
Adding full helpers met by either hub (m >= 1) only adds vectors, so m = 0 is the weakest case: a class pair (r, r') with
0 independent (h, h', R, R') here can never share a hub-only label whatever the m's.
Output: share_pairs.json with, per orientation and class pair, the number of value pairs (h, h') with h + h' a pair value
and the number of (h, h', R, R') choices with an independent family; the independent pairs are listed.
"""
import sys, json, time, itertools
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, str(Path.home() / "xs-campaigns/2026-11-07-sprint/qjointcheck"))
import jc_geo  # noqa: E402

OUT = Path(__file__).resolve().parent / "share_pairs.json"


def run(ori):
    t0 = time.time()
    G = jc_geo.Geo(ori)
    trip = G.trip; PM = G.PM
    V = {h: t for h, t in trip.items() if len(t) >= 1}          # values with >= 1 triple (masks of r >= 1 helpers)
    V2 = {h for h, t in trip.items() if len(t) >= 2}
    print(ori, "values with >=1 triple", len(V), ">=2 triples", len(V2), "full", len(G.fulls), f"{time.time()-t0:.0f}s", flush=True)
    H, Hp = jc_geo.HB(0), jc_geo.HB(1)
    pairs = Counter(); indep_choices = Counter(); indep_pairs = defaultdict(set); dep_only_pairs = Counter()
    witnesses = defaultdict(list)
    for h, th in V.items():
        for p, P in PM.items():
            hp = h ^ p
            if hp <= h or hp not in V: continue
            thp = V[hp]
            for r in (1, 2):
                if len(th) < r: continue
                for rp in (1, 2):
                    if len(thp) < rp: continue
                    cls = (r, rp) if r <= rp else (rp, r)
                    pairs[cls] += 1
                    found = False
                    for R in itertools.combinations(th, r):
                        for Rp in itertools.combinations(thp, rp):
                            fam = [H ^ T for T in R] + [Hp ^ T for T in Rp] + [H ^ Hp ^ P]
                            if jc_geo.indep(fam):
                                indep_choices[cls] += 1; found = True
                                if len(witnesses[cls]) < 5: witnesses[cls].append([h, hp, list(R), list(Rp), P])
                    if found: indep_pairs[cls].add((h, hp))
                    else: dep_only_pairs[cls] += 1
    res = {}
    for cls in sorted(pairs):
        res[str(cls)] = {"value_pairs_with_pair_value_xor": pairs[cls], "independent_choices": indep_choices[cls],
                         "value_pairs_with_some_independent_choice": len(indep_pairs[cls]),
                         "value_pairs_never_independent": dep_only_pairs[cls], "witnesses": witnesses[cls]}
        print(ori, cls, res[str(cls)] | {"witnesses": "..."}, flush=True)
    # per-value degree in the sharable graph for r = 2 (how many r = 2 partners can an r = 2 hub share a hub-only label with)
    deg = Counter()
    for h, hp in indep_pairs[(2, 2)]: deg[h] += 1; deg[hp] += 1
    res["r2_r2_degree_hist"] = sorted(Counter(deg.values()).items())
    res["r2_r2_values_with_partner"] = len(deg)
    res["seconds"] = round(time.time() - t0)
    print(ori, "r2-r2 sharable graph: values with a partner", len(deg), "degree hist", res["r2_r2_degree_hist"], f"{time.time()-t0:.0f}s", flush=True)
    return res


if __name__ == "__main__":
    out = {ori: run(ori) for ori in ("M", "Mt")}
    json.dump(out, open(OUT, "w"), indent=1)
