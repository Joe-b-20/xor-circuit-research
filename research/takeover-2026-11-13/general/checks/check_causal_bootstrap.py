"""Check one specified odd-arm construction: r=5, k=3.

Verifies its matrix, forward circuit, inverse circuit, and cyclic equations.
There is no circuit search, optimization, or enumeration of alternatives.
Universal lower bounds are the hand proofs in CAUSAL_BOOTSTRAP_GAP.md.
"""

import json


R = 5
K = 3
N = R * K


def rank(rows):
    pivots = {}
    for value in rows:
        while value:
            pivot = value.bit_length() - 1
            if pivot not in pivots:
                pivots[pivot] = value
                break
            value ^= pivots[pivot]
    return len(pivots)


def xor_values(values):
    total = 0
    for value in values:
        total ^= value
    return total


class Circuit:
    def __init__(self):
        self.values = [1 << i for i in range(N)]
        self.operations = []

    def add(self, left, right):
        assert 0 <= left < len(self.values)
        assert 0 <= right < len(self.values)
        self.operations.append((left, right))
        self.values.append(self.values[left] ^ self.values[right])
        return len(self.values) - 1


def main():
    full = (1 << N) - 1
    prefix = {(arm, 0): 0 for arm in range(R)}
    for arm in range(R):
        for step in range(1, K + 1):
            prefix[arm, step] = prefix[arm, step - 1] ^ (1 << (arm * K + step - 1))

    labels = [(0, 0)] + [
        (arm, step)
        for arm in range(R)
        for step in range(1, K + 1)
        if (arm, step) != (R - 1, K)
    ]
    matrix = [full ^ prefix[label] for label in labels]
    assert len(matrix) == N
    assert rank(matrix) == N
    assert len(set(matrix)) == N
    assert min(value.bit_count() for value in matrix) == (R - 1) * K

    # Compute the first endpoint using only its input coordinates.
    forward = Circuit()
    initial_inputs = list(range(K, N))
    current = initial_inputs[0]
    for coordinate in initial_inputs[1:]:
        current = forward.add(current, coordinate)
    q_forward = {(0, K): current}
    for step in range(K - 1, -1, -1):
        current = forward.add(current, step)
        q_forward[0, step] = current
    center = current
    for arm in range(1, R):
        current = center
        last = K - 1 if arm == R - 1 else K
        for step in range(1, last + 1):
            current = forward.add(current, arm * K + step - 1)
            q_forward[arm, step] = current
    assert [forward.values[q_forward[label]] for label in labels] == matrix
    assert len(forward.operations) == (2 * R - 1) * K - 2
    assert len(set(forward.values)) == len(forward.values)

    # The inverse inputs are the retained tree vertices in the matrix row order.
    inverse = Circuit()
    q_inverse = {label: index for index, label in enumerate(labels)}
    for arm in range(R):
        q_inverse[arm, 0] = q_inverse[0, 0]
    endpoint_indices = [q_inverse[arm, K] for arm in range(R - 1)]
    current = endpoint_indices[0]
    for endpoint in endpoint_indices[1:]:
        current = inverse.add(current, endpoint)
    q_inverse[R - 1, K] = current
    inverse_rows = []
    for arm in range(R):
        for step in range(1, K + 1):
            output = inverse.add(q_inverse[arm, step - 1], q_inverse[arm, step])
            inverse_rows.append(inverse.values[output])
    assert len(inverse.operations) == N + R - 2
    assert len(set(inverse.values)) == len(inverse.values)
    for coordinate, inverse_row in enumerate(inverse_rows):
        composed = xor_values(matrix[i] for i in range(N) if inverse_row >> i & 1)
        assert composed == 1 << coordinate

    selected = {labels.index((arm, K)) for arm in range(R - 1)}
    selected.add(labels.index((R - 1, K - 1)))
    exceptional = xor_values(1 << i for i in selected)
    assert inverse_rows[-1] == exceptional
    assert exceptional.bit_count() == R
    assert all((row & exceptional).bit_count() <= 1 for row in inverse_rows[:-1])

    # Full target tree plus the prescribed partial endpoint sums.
    unknown_values = [full]
    q_unknown = {(arm, 0): 0 for arm in range(R)}
    for arm in range(R):
        for step in range(1, K + 1):
            q_unknown[arm, step] = len(unknown_values)
            unknown_values.append(full ^ prefix[arm, step])
    z_unknown = {}
    for count in range(2, R - 1):
        z_unknown[count] = len(unknown_values)
        unknown_values.append(xor_values(full ^ prefix[arm, K] for arm in range(count)))

    coefficient_rows = []

    def equation(unknowns, coordinate=None):
        row = xor_values(1 << i for i in unknowns)
        value = xor_values(unknown_values[i] for i in unknowns)
        if coordinate is not None:
            value ^= 1 << coordinate
        assert value == 0
        assert len(unknowns) + (coordinate is not None) == 3
        coefficient_rows.append(row)

    for arm in range(R):
        for step in range(1, K + 1):
            equation([q_unknown[arm, step - 1], q_unknown[arm, step]], arm * K + step - 1)
    equation([z_unknown[2], q_unknown[0, K], q_unknown[1, K]])
    for count in range(3, R - 1):
        equation([z_unknown[count], z_unknown[count - 1], q_unknown[count - 1, K]])
    equation([z_unknown[R - 2], q_unknown[R - 2, K], q_unknown[R - 1, K]])
    assert len(unknown_values) == N + R - 2
    assert len(set(unknown_values)) == len(unknown_values)
    assert len(coefficient_rows) == N + R - 2
    assert rank(coefficient_rows) == N + R - 2

    print(json.dumps({
        "specified_arms": R,
        "specified_arm_length": K,
        "matrix_dimension_and_rank": N,
        "minimum_target_weight": min(value.bit_count() for value in matrix),
        "forward_gates_verified": len(forward.operations),
        "inverse_gates_verified": len(inverse.operations),
        "inverse_composition_verified": True,
        "cyclic_unknowns_and_rank": len(unknown_values),
        "cyclic_equations_evaluate_to_zero": True,
        "independent_selected_tree_vertices": len(selected),
        "all_other_inverse_rows_project_to_zero_or_unit": True,
        "circuit_search": False,
        "optimization": False,
    }, indent=2))


if __name__ == "__main__":
    main()
