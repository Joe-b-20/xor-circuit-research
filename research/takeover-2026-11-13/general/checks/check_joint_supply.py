#!/usr/bin/env python3
"""Verify specified constructions only; no circuit or parameter search."""

import json
from itertools import combinations


def rank(values):
    basis = {}
    for value in values:
        while value:
            pivot = value.bit_length() - 1
            if pivot in basis:
                value ^= basis[pivot]
            else:
                basis[pivot] = value
                break
    return len(basis)


class Circuit:
    def __init__(self, initial, parity_mask):
        self.values = list(initial)
        self.initial_count = len(initial)
        self.parity_mask = parity_mask
        self.gates = []

    def parity(self, value):
        return (value & self.parity_mask).bit_count() % 2

    def add(self, left, right):
        assert 0 <= left < len(self.values)
        assert 0 <= right < len(self.values)
        self.gates.append((left, right))
        self.values.append(self.values[left] ^ self.values[right])
        return len(self.values) - 1

    def stats(self, outputs):
        gate_values = self.values[self.initial_count:]
        odd = sum(self.parity(value) for value in gate_values)
        pairs = sum(self.parity(self.values[l]) and self.parity(self.values[r])
                    for l, r in self.gates)
        ee = sum(not self.parity(self.values[l]) and not self.parity(self.values[r])
                 for l, r in self.gates)
        initial_even = [v for v in self.values[:self.initial_count] if not self.parity(v)]
        even = [v for v in gate_values if not self.parity(v)]
        effective_rank = rank(initial_even + even) - rank(initial_even)
        return dict(gates=len(self.gates), odd=odd, pairs=pairs, even_plus_even=ee,
                    effective_even_rank=effective_rank, odd_graph_cycles=pairs-effective_rank,
                    extra_odd=odd-len(outputs), ternary_resource=odd+ee)


def coordinate_circuit(n):
    return Circuit([1 << i for i in range(n)], (1 << n) - 1)


def tagged_complete_graph():
    q = 5
    edges = list(combinations(range(q), 2))
    m = len(edges)
    n = q + m
    circ = coordinate_circuit(n)
    star = {i: circ.add(0, i) for i in range(1, q)}
    # One specified assignment, with two occurrences of each cost mechanism.
    choices = iter(['odd', 'even', 'pair', 'odd', 'even', 'pair'])
    outputs = []
    expected = []
    for index, (u, v) in enumerate(edges):
        tag = q + index
        expected.append((1 << u) ^ (1 << v) ^ (1 << tag))
        if u == 0:
            out = circ.add(tag, star[v])
        else:
            choice = next(choices)
            if choice == 'odd':
                out = circ.add(circ.add(tag, star[u]), star[v])
            elif choice == 'even':
                out = circ.add(circ.add(star[u], star[v]), tag)
            else:
                out = circ.add(circ.add(u, v), tag)
        outputs.append(out)
    assert [circ.values[i] for i in outputs] == expected
    result = circ.stats(outputs)
    assert result == dict(gates=20, odd=12, pairs=6, even_plus_even=2,
                          effective_even_rank=4, odd_graph_cycles=2,
                          extra_odd=2, ternary_resource=14)
    rows = [1 << i for i in range(q)] + expected
    assert rank(rows) == n
    for i, row in enumerate(rows):
        composed = 0
        for j in range(n):
            if row & (1 << j):
                composed ^= rows[j]
        assert composed == 1 << i
    return dict(vertices=q, edges=m, inputs=n, target_graph_cycle_rank=m-q+1,
                inverse_is_same_map=True, verified_noninput_outputs=m, **result)


def supplier_copies(even_aggregation_copies):
    b = 3
    circ = coordinate_circuit(10*b)
    outputs = []
    expected = []
    for index in range(b):
        offset = 10 * index
        a, bb, c, d = range(offset, offset+4)
        e = circ.add(a, bb)
        f = circ.add(c, d)
        if index in even_aggregation_copies:
            h = circ.add(e, f)
        else:
            h = circ.add(circ.add(a, f), bb)
        for pair, supplier in enumerate([e, f, h]):
            for copy in range(2):
                tag = offset + 4 + 2*pair + copy
                outputs.append(circ.add(supplier, tag))
                core = [(1 << a) ^ (1 << bb),
                        (1 << c) ^ (1 << d),
                        (1 << a) ^ (1 << bb) ^ (1 << c) ^ (1 << d)][pair]
                expected.append(core ^ (1 << tag))
    assert [circ.values[i] for i in outputs] == expected
    stats = circ.stats(outputs)
    d_count = len(even_aggregation_copies)
    assert stats['gates'] == 30-d_count
    assert stats['even_plus_even'] == d_count
    assert stats['effective_even_rank'] == 6
    assert stats['odd_graph_cycles'] == 3-d_count
    assert stats['extra_odd'] == 3-d_count
    assert stats['ternary_resource'] == 21
    return dict(copies=b, inputs=30, verified_outputs=len(outputs), **stats)


def connected_hierarchy():
    # One fixed tree: three pair leaves, node (0,1), root ((0,1),2).
    circ = coordinate_circuit(16)
    suppliers = [circ.add(0, 1), circ.add(2, 3), circ.add(4, 5)]
    suppliers.append(circ.add(suppliers[0], suppliers[1]))
    suppliers.append(circ.add(suppliers[3], suppliers[2]))
    expected_suppliers = [3, 12, 48, 15, 63]
    assert [circ.values[i] for i in suppliers] == expected_suppliers
    outputs = []
    for index, supplier in enumerate(suppliers):
        for copy in range(2):
            tag = 6 + 2*index + copy
            out = circ.add(supplier, tag)
            assert circ.values[out] == expected_suppliers[index] ^ (1 << tag)
            outputs.append(out)
    stats = circ.stats(outputs)
    assert stats == dict(gates=15, odd=10, pairs=3, even_plus_even=2,
                         effective_even_rank=3, odd_graph_cycles=0,
                         extra_odd=0, ternary_resource=12)
    return dict(inputs=16, leaf_pairs=3, verified_outputs=10, **stats)


def supplied_dictionary():
    # q=2: five independent odd and four independent even members, plus b.
    independent = [1 << i for i in range(9)]
    b = (1 << 9) - 1
    dictionary = independent + [b]
    target = (1 << 5) - 1
    assert len(dictionary)-rank(dictionary) == 1
    odd_tree = Circuit(dictionary, target)
    current = 0
    for left, right in [(1, 2), (3, 4)]:
        current = odd_tree.add(current, odd_tree.add(left, right))
    assert odd_tree.values[current] == target
    odd_stats = odd_tree.stats([current])
    assert (odd_stats['pairs'], odd_stats['ternary_resource']) == (2, 2)
    even_tree = Circuit(dictionary, target)
    current = 9
    for index in range(5, 9):
        current = even_tree.add(current, index)
    assert even_tree.values[current] == target
    even_stats = even_tree.stats([current])
    assert (even_stats['pairs'], even_stats['ternary_resource']) == (0, 4)
    return dict(dictionary_size=10, dictionary_rank=9,
                specified_resource_pairs=[[2, 2], [0, 4]],
                coordinate_prefix_claim=False)


if __name__ == '__main__':
    print(json.dumps(dict(
        complete_graph=tagged_complete_graph(),
        supplier_copies=[supplier_copies({0, 1, 2}),
                         supplier_copies({0}), supplier_copies(set())],
        connected_hierarchy=connected_hierarchy(),
        supplied_dictionary=supplied_dictionary(),
        circuit_search=False, representation_search=False,
    ), indent=2))
