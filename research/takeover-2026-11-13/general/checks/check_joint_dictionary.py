#!/usr/bin/env python3
"""Check fixed joint-dictionary and coset constructions, without search."""

import json

from check_joint_supply import Circuit, coordinate_circuit, rank


def xor_values(values):
    result = 0
    for value in values:
        result ^= value
    return result


def resources(circ):
    pair_gates = sum(circ.parity(circ.values[a]) and circ.parity(circ.values[b])
                     for a, b in circ.gates)
    return dict(gates=len(circ.gates), odd_pair_gates=pair_gates,
                other_gates=len(circ.gates)-pair_gates)


def lift_counts(dictionary, representations, targets):
    assert [xor_values(dictionary[i] for i in row) for row in representations] == targets
    patterns = []
    for i in range(len(dictionary)):
        pattern = sum(1 << j for j, row in enumerate(representations) if i in row)
        if pattern:
            patterns.append(pattern)
    return dict(used_members=len(patterns), distinct_patterns=len(set(patterns)),
                disjoint_group_preparation=len(patterns)-len(set(patterns)))


def check_common_offset():
    r = m = 3
    n = 2*r + m*(2*r+1)
    anchors = list(range(2*r))
    local = [list(range(2*r+i*(2*r+1), 2*r+(i+1)*(2*r+1))) for i in range(m)]
    targets = [xor_values(1 << j for j in row) for row in local]
    before = coordinate_circuit(n)
    before_outputs = []
    for row in local:
        pairs = [before.add(row[2*j], row[2*j+1]) for j in range(r)]
        current = row[-1]
        for pair in pairs:
            current = before.add(current, pair)
        before_outputs.append(current)
    assert [before.values[i] for i in before_outputs] == targets
    assert resources(before) == dict(gates=18, odd_pair_gates=9, other_gates=9)

    prefix = coordinate_circuit(n)
    translated = []
    for row in local:
        pairs = [prefix.add(a, x) for a, x in zip(anchors, row[:-1])]
        current = pairs[0]
        for pair in pairs[1:]:
            current = prefix.add(current, pair)
        translated.append(prefix.add(current, row[-1]))
    assert len(prefix.gates) == 4*r*m == 36
    dictionary = prefix.values[:]
    assert all(target not in dictionary for target in targets)
    h_value = xor_values(1 << a for a in anchors)
    assert h_value not in dictionary
    assert [prefix.values[i] ^ h_value for i in translated] == targets

    # This quotient proves all single-target lower certificates simultaneously.
    quotient_columns = [1 << i for i in range(2*r)]
    for i in range(m):
        quotient_columns.extend([1 << j for j in range(2*r)] + [1 << (2*r+i)])

    def project(value):
        return xor_values(quotient_columns[i] for i in range(n) if value & (1 << i))

    for value in dictionary:
        expected_weight = 1 if prefix.parity(value) else 0
        assert project(value).bit_count() == expected_weight
    assert all(project(target).bit_count() == 2*r+1 for target in targets)
    assert project(h_value).bit_count() == 2*r
    difference = targets[0] ^ targets[1]
    assert difference not in dictionary
    assert prefix.values[translated[0]] ^ prefix.values[translated[1]] == difference

    suffix = Circuit(dictionary, (1 << n)-1)
    pairs = [suffix.add(anchors[2*j], anchors[2*j+1]) for j in range(r)]
    h = pairs[0]
    for pair in pairs[1:]:
        h = suffix.add(h, pair)
    assert suffix.values[h] == h_value
    suffix_outputs = [suffix.add(u, h) for u in translated]
    assert [suffix.values[i] for i in suffix_outputs] == targets
    assert resources(suffix) == dict(gates=8, odd_pair_gates=3, other_gates=5)

    # Fixed joint lifts; no optimization over representations is performed.
    initial = [1 << i for i in range(n)]
    initial_lift = lift_counts(initial, local, targets)
    translated_rows = [anchors + [u] for u in translated]
    supplied_lift = lift_counts(dictionary, translated_rows, targets)
    assert initial_lift == dict(used_members=21, distinct_patterns=3,
                               disjoint_group_preparation=18)
    assert supplied_lift == dict(used_members=9, distinct_patterns=4,
                                disjoint_group_preparation=5)
    # Residual initial lift is an identity; supplied lift adds the common group.
    assert initial_lift['disjoint_group_preparation'] == len(before.gates)
    assert supplied_lift['disjoint_group_preparation'] + m == len(suffix.gates)
    pair_shared_budget = (2*r) + 1 + 1 - 1
    assert pair_shared_budget == 7

    rows = initial[:]
    for i, row in enumerate(local):
        rows[row[-1]] = targets[i]
    assert rank(rows) == n
    assert all(row.bit_count() % 2 for row in rows)
    for i, row in enumerate(rows):
        assert xor_values(rows[j] for j in range(n) if row & (1 << j)) == 1 << i
    return dict(parameter_r=r, targets=m, coordinate_inputs=n, prefix_gates=36,
                initial_continuation=resources(before), supplied_continuation=resources(suffix),
                individual_frontier_certificate=[r, r], quotient_lower_certificates_verified=True,
                initial_lift=initial_lift, supplied_lift=supplied_lift,
                two_target_independent_cost=4*r, two_target_shared_cost=pair_shared_budget,
                square_map_rank=rank(rows), involution_verified=True,
                prefix_is_charged_separately=True)


def check_coset_saturation():
    circ = coordinate_circuit(5)
    blocks = [0b00011, 0b01100, 0b10000]
    pa, pb = circ.add(0, 1), circ.add(2, 3)
    outputs = list(range(5))
    outputs += [circ.add(0, pb), circ.add(1, pb), circ.add(2, pa), circ.add(3, pa)]
    left, right = circ.add(4, pa), circ.add(4, pb)
    outputs += [left, right, circ.add(left, pb)]
    masks = [circ.values[i] for i in outputs]
    assert len(set(masks)) == 12 == len(blocks) * 2**2
    assert all(sum((mask & block).bit_count() % 2 for block in blocks) == 1 for mask in masks)
    assert rank([circ.values[pa], circ.values[pb]]) == 2
    stats = circ.stats(outputs[5:])
    assert stats == dict(gates=9, odd=7, pairs=2, even_plus_even=0,
                         effective_even_rank=2, odd_graph_cycles=0,
                         extra_odd=0, ternary_resource=7)
    return dict(inputs=5, partition_sizes=[2, 2, 1], targets_verified=12,
                complete_cosets_by_cardinality=True, **stats)


if __name__ == '__main__':
    print(json.dumps(dict(common_offset=check_common_offset(),
                         coset_saturation=check_coset_saturation(),
                         circuit_search=False, representation_search=False,
                         target_set_enumeration=False), indent=2))
