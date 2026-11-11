#!/usr/bin/env python3
"""naive_q3.py -- deliberately naive enumeration of the smallest sub-case for the brute-force control (PILOT_BRIEF.md
section 3): two hubs of type (r,u) = (2,2) sharing exactly one label, no other helpers (A = 0).  Nested loops over the
WHOLE domain (every value with >= 2 triples, every pair of its triples, every end), no rotation, no incremental basis, no
rank filter: R1, R3 by construction, R7 checked once per complete configuration by a full rank computation
(geo_q3.rank_hi).  Output: the set of canonical forms frozenset{(mask, frozenset(triples), frozenset(label values))}.
"""
import sys, itertools, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import geo_q3


def enumerate_two_22(geo, verbose=True):
    B = geo.B; Bset = geo.Bset; Bidx = geo.Bidx; trip = geo.trip
    rep = {h: T for h, T in trip.items() if len(T) >= 2}
    out = set(); n_inner = 0; n_rank = 0; t0 = time.time()
    H1 = 1 << 64; H2 = 1 << 65
    for h1, T1 in rep.items():
        for R1 in itertools.combinations(T1, 2):
            for b1 in B:
                l1 = h1 ^ b1                                   # the shared label
                for b1p in B:
                    if b1p == b1: continue
                    l2 = h1 ^ b1p                              # hub 1's private label
                    for b2 in B:
                        if b2 == b1: continue
                        h2 = l1 ^ b2
                        n_inner += 1
                        if h2 in Bset or h2 == h1 or h2 not in rep: continue
                        for R2 in itertools.combinations(rep[h2], 2):
                            for b2p in B:
                                if b2p == b2: continue
                                l3 = h2 ^ b2p                  # hub 2's private label
                                if l3 == l1 or l3 == l2: continue
                                vecs = [T | H1 for T in R1] + [T | H2 for T in R2] + [H1 | H2 | (1 << Bidx[b1]) | (1 << Bidx[b2])]
                                n_rank += 1
                                if geo_q3.rank_hi(vecs) == 5:
                                    out.add(frozenset([(h1, frozenset(R1), frozenset((l1, l2))), (h2, frozenset(R2), frozenset((l1, l3)))]))
    if verbose:
        print(f"naive: {len(rep)} repeated values, {n_inner} inner iterations, {n_rank} rank tests, {len(out)} distinct configurations, {time.time()-t0:.0f}s", flush=True)
    return out


if __name__ == "__main__":
    G = geo_q3.GeoQ("Mt")
    enumerate_two_22(G)
