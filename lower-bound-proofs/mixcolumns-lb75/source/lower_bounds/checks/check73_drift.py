#!/usr/bin/env python3
"""Independent standard-library check of the steady-transpose 73 bound.

Enumerates the complete relaxed steady gate-count domain at G=72 and
independently reconstructs the boundary weight-six relation ranks needed
to exclude its sole zero-drift profile. Imports no research implementation.
"""
from itertools import combinations
from collections import defaultdict
from pathlib import Path
import json


def rank(vectors):
    basis = {}
    for v in vectors:
        while v:
            bit = v & -v
            if bit not in basis:
                basis[bit] = v
                break
            v ^= basis[bit]
    return len(basis)


def multiply(a, b):
    polynomial = 0
    for j in range(8):
        if (b >> j) & 1:
            polynomial ^= a << j
    for j in range(14, 7, -1):
        if (polynomial >> j) & 1:
            polynomial ^= 0x11B << (j-8)
    return polynomial


def boundaries():
    coefficients = ((2, 3, 1, 1), (1, 2, 3, 1),
                    (1, 1, 2, 3), (3, 1, 1, 2))
    columns = [sum(multiply(coefficients[o][i//8], 1 << (i%8)) << (8*o)
                   for o in range(4)) for i in range(32)]
    rows = [sum(((col >> j) & 1) << i for i, col in enumerate(columns))
            for j in range(32)]
    units = [1 << i for i in range(32)]
    return {'M': units+rows, 'Mt': units+columns}


def rho6(boundary):
    assert len(set(boundary)) == 64
    assert all(v.bit_count() % 2 for v in boundary)
    assert len({a ^ b for a, b in combinations(boundary, 2)}) == 2016
    triples = defaultdict(list)
    for i, j, k in combinations(range(64), 3):
        triples[boundary[i] ^ boundary[j] ^ boundary[k]].append(
            (1 << i) | (1 << j) | (1 << k))
    six = {a ^ b for group in triples.values() for a, b in combinations(group, 2)}
    assert all(v.bit_count() == 6 for v in six)
    return dict(weight_six_relations=len(six), rank=rank(six))


def minimum_s(G, x, y):
    target = 96-2*G+2*x+y
    return next(s for s in range(200) if max(s, s*(s-1)//2) >= target)


def main():
    G = 72
    survivors = []
    feasible_profiles = 0
    positive_drifts = []
    for a in range(24, G-44):
        for b in range(24, G-31):
            for Y in range(G-31-a):
                for Z in range(min(Y, G-32-b)+1):
                    difference = Y-Z
                    upper_a = 3*G-128-3*a-2*difference
                    upper_b = 3*G-128-3*b+2*difference
                    lower_a = minimum_s(G, a, Y)
                    lower_b = minimum_s(G, b, Z)
                    if lower_a > upper_a or lower_b > upper_b:
                        continue
                    feasible_profiles += 1
                    drift = lower_a+lower_b+192-2*G-a-b
                    if drift <= 0:
                        survivors.append([a, b, Y, Z, lower_a, lower_b])
                    else:
                        positive_drifts.append(drift)
    assert survivors == [[24, 24, 0, 0, 0, 0]]
    ranks = {name: rho6(B) for name, B in boundaries().items()}
    assert ranks == {'M': {'weight_six_relations': 60, 'rank': 20},
                     'Mt': {'weight_six_relations': 84, 'rank': 28}}
    assert all(result['rank'] < 32 for result in ranks.values())
    result = dict(gate_count_excluded=G,
                  profiles_passing_scalar_ranges=feasible_profiles,
                  nonpositive_drift_profiles=survivors,
                  minimum_positive_drift=min(positive_drifts),
                  boundary_rank_checks=ranks,
                  sole_profile_requires_boundary_rank_at_least=32)
    Path(__file__).with_name('DRIFT73_VERIFIED.json').write_text(
        json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
