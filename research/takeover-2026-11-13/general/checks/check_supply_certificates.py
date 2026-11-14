"""Check specified witnesses, not candidate circuits or target subsets.

Checks one recorded 88-gate MixColumns circuit and its deterministic ternary
translation, one fixed target order certifying the total-parity profile ceiling,
and one displayed common-core/private-input construction.
"""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def rank(vectors):
    basis = {}
    for value in vectors:
        while value:
            pivot = value.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = value
                break
            value ^= basis[pivot]
    return len(basis)


def check_mixcolumns():
    reader = ROOT / 'research/structure-2026-11-11/review-record/lib.py'
    spec = importlib.util.spec_from_file_location('specified_reader', reader)
    lib = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lib)
    n, gates, outs, values, rows = lib.load(
        ROOT / 'circuits/aes-mixcolumns/aes-mixcolumns-xor88-depth5.circ.txt',
        ROOT / 'circuits/aes-mixcolumns/aes-mixcolumns.mat.txt',
    )
    parity = lambda value: value.bit_count() % 2
    odd_values = [1 << i for i in range(n)]
    known = {value: i for i, value in enumerate(odd_values)}
    odd = {f'x{i}': i for i in range(n)}
    pairs = {}
    ternary_operations = []

    def add_three(a, b, c):
        value = odd_values[a] ^ odd_values[b] ^ odd_values[c]
        if value in known:
            return known[value]
        index = len(odd_values)
        ternary_operations.append((a, b, c))
        odd_values.append(value)
        known[value] = index
        return index

    for name, a, b in gates:
        pa, pb = parity(values[a]), parity(values[b])
        if pa and pb:
            pairs[name] = (odd[a], odd[b])
        elif pa or pb:
            u, e = (a, b) if pa else (b, a)
            odd[name] = add_three(odd[u], *pairs[e])
            assert odd_values[odd[name]] == values[name]
        else:
            a1, a2 = pairs[a]
            b1, b2 = pairs[b]
            pairs[name] = (add_three(a1, a2, b1), b2)
        if name in pairs:
            i, j = pairs[name]
            assert odd_values[i] ^ odd_values[j] == values[name]

    assert [odd_values[odd[name]] for name in outs] == rows
    even = [values[name] for name, _, _ in gates if not parity(values[name])]
    odd_count = len(gates) - len(even)
    ee_count = sum(not parity(values[a]) and not parity(values[b]) for _, a, b in gates)
    even_rank = rank(even)
    assert (len(gates), odd_count, len(even), even_rank, ee_count) == (88, 48, 40, 24, 16)
    assert len(ternary_operations) == odd_count + ee_count == 64

    # This is one fixed nested sequence, not a minimization over subsets.
    ordered = [rows[8 * byte + sheet] for sheet in range(8) for byte in range(4)]
    union = 0
    prefix_bounds = []
    for k, row in enumerate(ordered, 1):
        if k > 1:
            assert row & union  # the support-overlap graph stays connected
        union |= row
        numerator = union.bit_count() - 1 - 2 * k
        prefix_bounds.append((numerator + 1) // 2)
    assert min(row.bit_count() for row in rows) == 5
    assert max(0, *prefix_bounds) == 1

    # The eight bit-position blocks give a compatible target partition.
    blocks = [sum(1 << (8 * byte + sheet) for byte in range(4)) for sheet in range(8)]
    for row in rows:
        assert sum(parity(row & block) for block in blocks) == 1
    return {
        'specified_binary_gates': len(gates),
        'odd_gates': odd_count,
        'even_gates': len(even),
        'even_rank': even_rank,
        'even_plus_even_gates': ee_count,
        'odd_graph_cycles': len(even) - even_rank - ee_count,
        'deterministic_ternary_gates': len(ternary_operations),
        'ternary_outputs_verified': len(outs),
        'fixed_nested_order_profile_upper_bound': max(0, *prefix_bounds),
        'first_target_profile_lower_bound': 1,
        'compatible_bit_position_parts': len(blocks),
        'standalone_total_parity_bound_ceiling': 32 + (32 - len(blocks)) + 1,
    }


def check_common_core():
    a = 2
    private_pair_counts = [1, 2, 3]
    core_size = 2 * a + 1
    n = core_size + 2 * sum(private_pair_counts)
    values = [1 << i for i in range(n)]
    gates = []

    def add(left, right):
        gates.append((left, right))
        values.append(values[left] ^ values[right])
        return len(values) - 1

    current = 0
    for i in range(a):
        pair = add(1 + 2 * i, 2 + 2 * i)
        current = add(current, pair)
    core = current
    outputs = []
    expected = []
    coordinate = core_size
    for b in private_pair_counts:
        current = core
        mask = (1 << core_size) - 1
        for _ in range(b):
            pair = add(coordinate, coordinate + 1)
            mask ^= (1 << coordinate) ^ (1 << (coordinate + 1))
            current = add(current, pair)
            coordinate += 2
        outputs.append(current)
        expected.append(mask)
    assert [values[i] for i in outputs] == expected
    even = [value for value in values[n:] if value.bit_count() % 2 == 0]
    odd_count = len(gates) - len(even)
    ee_count = sum(values[l].bit_count() % 2 == 0 and values[r].bit_count() % 2 == 0 for l, r in gates)
    helpers = odd_count - len(outputs)
    assert len(gates) == n - 1 == 16
    assert rank(even) == len(even) == 8
    assert ee_count == 0
    assert helpers == a + sum(b - 1 for b in private_pair_counts) == 5
    return {
        'core_parameter': a,
        'private_pair_counts': private_pair_counts,
        'inputs': n,
        'gates_verified': len(gates),
        'outputs_verified': len(outputs),
        'even_rank': rank(even),
        'extra_odd_gates': helpers,
        'even_plus_even_gates': ee_count,
        'combined_resource_matches_proved_bound': True,
    }


if __name__ == '__main__':
    print(json.dumps({
        'mixcolumns': check_mixcolumns(),
        'common_core': check_common_core(),
        'circuit_search': False,
        'target_subset_optimization': False,
    }, indent=2))
