#!/usr/bin/env python3
"""Check specified circuits and flag ranks; no order or circuit search."""

import json
from pathlib import Path

from check_joint_supply import Circuit, rank
from check_subspace_and_sidon import collision_space, echelon, remainder


def coordinate_circuit(n):
    return Circuit([1 << i for i in range(n)], (1 << n) - 1)


def prefix_flag(initial, targets):
    return ([echelon([])]
            + [echelon(targets[:i]) for i in range(1, len(targets) + 1)]
            + [echelon(initial)])


def profile(dictionary, flag):
    ranks = [collision_space(dictionary, space)[0] for space in flag]
    deficits = [len(space) - value for space, value in zip(flag, ranks)]
    layers = [ranks[i] - ranks[i - 1] for i in range(1, len(flag))]
    phi = sum(max(0, deficits[i] - deficits[i - 1])
              for i in range(1, len(flag)))
    assert deficits[0] == deficits[-1] == 0
    assert all(value >= 0 for value in deficits + layers)
    return ranks, deficits, layers, phi


def check_transition(previous, current, flag, gate_value):
    old_ranks, _, old_layers, old_phi = previous
    new_ranks, _, new_layers, new_phi = current
    gains = [new - old for new, old in zip(new_ranks, old_ranks)]
    assert all(gain in (0, 1) for gain in gains)
    changed = [i for i, gain in enumerate(gains) if gain]
    if changed:
        first, after = changed[0], changed[-1] + 1
        assert changed == list(range(first, after))
        layer_changes = [new - old for new, old in zip(new_layers, old_layers)]
        expected = [0] * len(layer_changes)
        expected[first - 1], expected[after - 1] = 1, -1
        assert layer_changes == expected
        level = next(i for i, space in enumerate(flag)
                     if not remainder(gate_value, space))
        assert after <= level
    # Each strict target-prefix layer has dimension jump one. The final
    # appended V layer is allowed a larger jump and is never deficient.
    for i in range(1, len(flag) - 1):
        jump = len(flag[i]) - len(flag[i - 1])
        assert jump in (0, 1)
        if old_layers[i - 1] > 0:
            assert new_layers[i - 1] > 0
    assert old_phi - new_phi in (0, 1)
    return gains, old_phi - new_phi


def check_actual_output_flag(circ, targets):
    initial = circ.values[:circ.initial_count]
    target_set = set(targets)
    assert len(target_set) == len(targets)
    assert target_set.isdisjoint(initial)
    seen = set(initial)
    chronological_targets, first_productions = [], set()
    for index, value in enumerate(circ.values[circ.initial_count:], circ.initial_count):
        if value in target_set and value not in seen:
            chronological_targets.append(value)
            first_productions.add(index)
        seen.add(value)
    assert set(chronological_targets) == target_set
    flag = prefix_flag(initial, chronological_targets)
    previous = profile(initial, flag)
    initial_deficits, initial_phi = previous[1], previous[3]
    activations = neutral_auxiliary = 0
    for index, value in enumerate(circ.values[circ.initial_count:], circ.initial_count):
        current = profile(circ.values[:index + 1], flag)
        gains, drop = check_transition(previous, current, flag, value)
        if index in first_productions:
            assert not any(gains) and drop == 0
        else:
            activations += drop
            neutral_auxiliary += 1 - drop
        previous = current
    assert previous[3] == 0
    assert previous[0] == [len(space) for space in flag]
    assert activations == initial_phi
    assert len(circ.gates) == len(targets) + initial_phi + neutral_auxiliary
    return dict(gates=len(circ.gates), selected_targets=len(targets),
                initial_deficiency_profile=initial_deficits,
                initial_phi=initial_phi, activating_auxiliary=activations,
                neutral_auxiliary=neutral_auxiliary,
                every_gate_interval_verified=True,
                persistent_layer_occupation_verified=True,
                phi_monotone_verified=True,
                first_target_gates_have_zero_rank_credit=True,
                exact_auxiliary_ledger_verified=True)


def interleaved_blocks():
    blocks = 3
    circ = coordinate_circuit(4 * blocks)
    helpers = [circ.add(4 * block, 4 * block + 1) for block in range(blocks)]
    outputs = [[] for _ in range(blocks)]
    # One fixed interleaving: all first outputs, then all second outputs, etc.
    for stage in range(4):
        for block in range(blocks):
            a, _, c, d = range(4 * block, 4 * block + 4)
            if stage == 0:
                output = circ.add(helpers[block], c)
            elif stage == 1:
                output = circ.add(helpers[block], d)
            elif stage == 2:
                output = circ.add(outputs[block][0], d)
            else:
                output = circ.add(outputs[block][2], a)
            outputs[block].append(output)
    targets = []
    for block in range(blocks):
        a, b, c, d = [1 << j for j in range(4 * block, 4 * block + 4)]
        expected = [a ^ b ^ c, a ^ b ^ d, a ^ b ^ c ^ d, b ^ c ^ d]
        assert [circ.values[i] for i in outputs[block]] == expected
        targets.extend(expected)
    trace = check_actual_output_flag(circ, targets)
    assert (trace['gates'], trace['selected_targets'], trace['initial_phi']) == (15, 12, 3)
    assert trace['neutral_auxiliary'] == 0
    assert rank(targets) == 12
    return dict(blocks=blocks, full_map_rank=12,
                output_interleaving='by local output stage across three blocks', **trace)


def path_cover():
    edges = 7
    circ = coordinate_circuit(edges + 2)
    cover = [2, 4, 6, 8]
    helpers = {vertex: circ.add(0, vertex) for vertex in cover}
    outputs, targets = [], []
    for left in range(1, edges + 1):
        right = left + 1
        chosen = left if left in helpers else right
        other = right if chosen == left else left
        outputs.append(circ.add(helpers[chosen], other))
        targets.append(1 ^ (1 << left) ^ (1 << right))
    assert [circ.values[i] for i in outputs] == targets
    # This fixed four-edge matching certifies the displayed cover's minimum
    # size. No vertex-cover optimization or subset enumeration is performed.
    matching = [(1, 2), (3, 4), (5, 6), (7, 8)]
    endpoints = [vertex for edge in matching for vertex in edge]
    assert len(set(endpoints)) == len(endpoints)
    assert all(left in cover or left + 1 in cover for left in range(1, edges + 1))
    assert len(matching) == len(cover) == 4
    trace = check_actual_output_flag(circ, targets)
    stats = circ.stats(outputs)
    assert (trace['gates'], trace['selected_targets'], trace['initial_phi']) == (11, 7, 1)
    assert trace['neutral_auxiliary'] == 3
    assert stats['effective_even_rank'] == stats['pairs'] == 4
    assert stats['even_plus_even'] == stats['odd_graph_cycles'] == 0
    square_rows = [1, 1 << 1] + targets
    assert rank(square_rows) == 9
    assert all(row.bit_count() % 2 for row in square_rows)
    return dict(path_edges=edges, supplied_inputs=9,
                specified_cover=cover, disjoint_matching=matching,
                certified_minimum_cover_size=4, effective_even_rank=4,
                square_map_rank=9, all_square_rows_odd=True, **trace)


def cancelling_triangle():
    circ = coordinate_circuit(4)
    pair12 = circ.add(1, 2)
    target12 = circ.add(0, pair12)
    pair23 = circ.add(2, 3)
    target23 = circ.add(0, pair23)
    target13 = circ.add(target12, pair23)
    outputs = [target12, target23, target13]
    targets = [1 ^ (1 << u) ^ (1 << v) for u, v in [(1, 2), (2, 3), (1, 3)]]
    assert [circ.values[i] for i in outputs] == targets
    cancelled = 1 << 2
    assert circ.values[target12] & circ.values[pair23] == cancelled
    assert not circ.values[target13] & cancelled
    trace = check_actual_output_flag(circ, targets)
    stats = circ.stats(outputs)
    assert (trace['gates'], trace['selected_targets'], trace['initial_phi']) == (5, 3, 1)
    assert trace['neutral_auxiliary'] == 1
    assert stats['effective_even_rank'] == stats['pairs'] == 2
    assert stats['extra_odd'] == stats['even_plus_even'] == stats['odd_graph_cycles'] == 0
    return dict(effective_even_rank=2, cancelled_coordinate='x_2',
                cancellation_checked_in_both_parents_and_result=True,
                even_helpers_are_anchor_pairs=False, **trace)


def wrong_and_actual_order():
    circ = coordinate_circuit(3)
    pair = circ.add(0, 1)
    triple = circ.add(pair, 2)
    initial = circ.values[:circ.initial_count]
    u, t = circ.values[pair], circ.values[triple]
    wrong_flag = prefix_flag(initial, [t, u])
    actual_flag = prefix_flag(initial, [u, t])
    wrong_before = profile(initial, wrong_flag)
    wrong_after = profile(circ.values[:pair + 1], wrong_flag)
    actual_before = profile(initial, actual_flag)
    assert wrong_before[3] == 1 and actual_before[3] == 0
    assert wrong_after[0][1] - wrong_before[0][1] == 1
    trace = check_actual_output_flag(circ, [t, u])
    assert trace['gates'] == trace['selected_targets'] == 2
    assert trace['neutral_auxiliary'] == trace['initial_phi'] == 0
    return dict(wrong_order_phi=1, actual_order_phi=0,
                wrong_flag_first_output_increases_rank=True, **trace)


def overlapping_cuts():
    cuts = 6
    circ = coordinate_circuit(cuts + 2)
    initial = circ.values[:circ.initial_count]
    target = (1 << 0) ^ (1 << 1) ^ (1 << 2)
    extras = initial[3:]
    flag = ([echelon([])]
            + [echelon([target] + extras[:i]) for i in range(cuts)]
            + [echelon(initial)])
    before = profile(initial, flag)
    pair = circ.add(0, 1)
    after = profile(circ.values, flag)
    gains, drop = check_transition(before, after, flag, circ.values[pair])
    assert gains == [0] + [1] * cuts + [0]
    assert before[3] == drop == 1 and after[3] == 0
    return dict(nested_cuts=cuts, physical_gates=1,
                simultaneous_rank_increases=cuts, potential_drop=1)


if __name__ == '__main__':
    result = dict(interleaved_block_family=interleaved_blocks(),
                  path=path_cover(), cancelling_triangle=cancelling_triangle(),
                  order_counterexample=wrong_and_actual_order(),
                  overlapping_cuts=overlapping_cuts(),
                  circuit_search=False, output_order_enumeration=False,
                  target_subset_enumeration=False, representation_search=False)
    serialized = json.dumps(result, indent=2) + '\n'
    Path(__file__).with_name('flag-anchor-result.json').write_text(serialized)
    print(serialized, end='')
