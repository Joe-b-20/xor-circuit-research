#!/usr/bin/env python3
"""Direct checks of fixed constructions and quotient ranks, without search."""

import json

from check_joint_supply import Circuit, coordinate_circuit, rank


def xor_all(values):
    value = 0
    for term in values:
        value ^= term
    return value


def echelon(values):
    basis = {}
    for value in values:
        while value:
            pivot = value.bit_length() - 1
            if pivot in basis:
                value ^= basis[pivot]
            else:
                basis[pivot] = value
                break
    return basis


def remainder(value, basis):
    for pivot in sorted(basis, reverse=True):
        if value & (1 << pivot):
            value ^= basis[pivot]
    return value


def collision_space(dictionary, target_basis):
    representatives = {}
    generators = []
    for value in dictionary:
        color = remainder(value, target_basis)
        if not color:
            generators.append(value)
        elif color in representatives:
            generators.append(value ^ representatives[color])
        else:
            representatives[color] = value
    return rank(generators), set(representatives)


def check_trace(circ, targets):
    basis = echelon(targets)
    initial = circ.values[:circ.initial_count]
    initial_rank, initial_colors = collision_space(initial, basis)
    previous_rank, previous_colors = initial_rank, initial_colors
    outside = new_colors = growth = stagnant_repeats = 0
    for index, value in enumerate(circ.values[circ.initial_count:], circ.initial_count):
        current_rank, current_colors = collision_space(circ.values[:index+1], basis)
        gain = current_rank - previous_rank
        color = remainder(value, basis)
        if not color:
            assert gain == 0 and current_colors == previous_colors
        else:
            outside += 1
            if color not in previous_colors:
                new_colors += 1
                assert gain == 0
            else:
                assert gain in (0, 1)
                growth += gain
                stagnant_repeats += 1-gain
        previous_rank, previous_colors = current_rank, current_colors
    assert previous_rank == len(basis)
    deficit = len(basis)-initial_rank
    assert growth == deficit
    assert new_colors == len(previous_colors)-len(initial_colors)
    assert outside == new_colors+deficit+stagnant_repeats
    return dict(gates=len(circ.gates), target_span_dimension=len(basis),
                initial_collision_rank=initial_rank, missing_directions=deficit,
                outside_gates=outside, new_colors=new_colors,
                independent_collisions=growth, stagnant_repeats=stagnant_repeats,
                chronological_identity_verified=True)


def sharp_coordinate_examples():
    r = 3
    triples = coordinate_circuit(1+2*r)
    triple_targets = []
    for i in range(r):
        pair = triples.add(0, 1+2*i)
        output = triples.add(pair, 2+2*i)
        triple_targets.append(triples.values[output])
    triple_trace = check_trace(triples, triple_targets)
    assert triple_trace['outside_gates'] == r == r+3-3

    pairs = coordinate_circuit(2*(r+1))
    supplied = [pairs.add(2*i, 2*i+1) for i in range(r+1)]
    pair_targets = [pairs.values[pairs.add(supplied[0], supplied[i])]
                    for i in range(1, r+1)]
    pair_trace = check_trace(pairs, pair_targets)
    assert pair_trace['outside_gates'] == r+1 == r+4-3

    distance = 7
    parity = coordinate_circuit(distance)
    current = 0
    for i in range(1, distance):
        current = parity.add(current, i)
    parity_trace = check_trace(parity, [parity.values[current]])
    assert parity_trace['outside_gates'] == distance-2
    return dict(distance_three=triple_trace, distance_four=pair_trace,
                single_parity_distance_seven=parity_trace,
                distances_proved_symbolically_not_searched=True)


def common_offset():
    r = m = 3
    n = 2*r+m*(2*r+1)
    prefix = coordinate_circuit(n)
    targets, translated = [], []
    for i in range(m):
        local = list(range(2*r+i*(2*r+1), 2*r+(i+1)*(2*r+1)))
        targets.append(xor_all(1 << j for j in local))
        pairs = [prefix.add(j, local[j]) for j in range(2*r)]
        current = pairs[0]
        for pair in pairs[1:]:
            current = prefix.add(current, pair)
        translated.append(prefix.add(current, local[-1]))
    assert len(prefix.gates) == 36
    suffix = Circuit(prefix.values, (1 << n)-1)
    anchor_pairs = [suffix.add(2*i, 2*i+1) for i in range(r)]
    h = anchor_pairs[0]
    for pair in anchor_pairs[1:]:
        h = suffix.add(h, pair)
    outputs = [suffix.add(u, h) for u in translated]
    assert [suffix.values[i] for i in outputs] == targets
    trace = check_trace(suffix, targets)
    assert trace['initial_collision_rank'] == m-1
    assert trace['missing_directions'] == 1
    assert trace['outside_gates'] == 2*r-1
    assert trace['gates'] == m+2*r-1 == 8

    # A specified quotient certifies escape length; no word search is used.
    columns = [1 << j for j in range(2*r)]
    for i in range(m):
        columns.extend([1 << j for j in range(2*r)]+[1 << (2*r+i)])
    def project(value):
        return xor_all(columns[i] for i in range(n) if value & (1 << i))
    assert all(project(value).bit_count() <= 1 for value in prefix.values)
    assert all(project(target).bit_count() == 2*r+1 for target in targets)
    # The symbolic proof covers every W\R0 value (an odd number of targets).
    trace.update(prefix_gates_charged_separately=36, escape_length_certificate=7,
                 all_quotient_input_weights_at_most_one=True)
    return trace


def affine_incidence():
    q = 3
    points = [(x, y) for x in range(q) for y in range(q)]
    lines = [(s, t) for s in range(q) for t in range(q)]
    edges = [(p, l) for p, (x, y) in enumerate(points)
             for l, (s, t) in enumerate(lines) if (s*x+t-y) % q == 0]
    assert len(edges) == q**3
    n = 5*q*q
    circ = coordinate_circuit(n)
    helpers = [circ.add(circ.add(3*p, 3*p+1), 3*p+2) for p in range(q*q)]
    suppliers = [circ.add(3*q*q+2*l, 3*q*q+2*l+1) for l in range(q*q)]
    outputs = [circ.add(helpers[p], suppliers[l]) for p, l in edges]
    targets = [circ.values[output] for output in outputs]
    assert len(set(targets)) == q**3
    assert all(target.bit_count() == 5 for target in targets)
    patterns = [sum(1 << j for j, target in enumerate(targets)
                    if target & (1 << i)) for i in range(n)]
    assert all(patterns) and len(set(patterns)) == 2*q*q
    stats = circ.stats(outputs)
    assert stats['gates'] == q**3+3*q*q == 54
    assert stats['extra_odd'] == q*q == 9
    assert stats['pairs'] == stats['effective_even_rank'] == 2*q*q == 18
    assert stats['even_plus_even'] == stats['odd_graph_cycles'] == 0
    return dict(prime=q, inputs=n, targets=len(targets),
                column_classes=len(set(patterns)),
                clone_overhead=n-len(set(patterns)),
                reduced_map_pair_outputs=len(targets),
                sidon_property_proved_symbolically_not_enumerated=True, **stats)


if __name__ == '__main__':
    print(json.dumps(dict(coordinate_examples=sharp_coordinate_examples(),
                         prepared_common_offset=common_offset(),
                         affine_incidence=affine_incidence(),
                         circuit_search=False, representation_search=False,
                         codeword_enumeration=False), indent=2))
