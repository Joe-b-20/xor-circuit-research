"""Directly verify the two specified JOINT01 constructions; no search."""

import json


def rank(vectors):
    pivots = {}
    for value in vectors:
        while value:
            bit = value.bit_length() - 1
            if bit in pivots:
                value ^= pivots[bit]
            else:
                pivots[bit] = value
                break
    return len(pivots)


def verify(name, free, gates, outputs, expected):
    values = {f"x{i}": 1 << i for i in range(4)} | free
    formal = {node: 0 for node in values}
    operands = {}
    labels = []
    gate_values = []
    for node, left, right in gates:
        assert node not in values
        assert left in values and right in values
        value = values[left] ^ values[right]
        assert value & 15, "Every counted gate must carry own-block content"
        assert value not in values.values(), "A gate duplicates an available value"
        values[node] = value
        operands[node] = (left, right)
        gate_values.append(value)
        left_free = not (values[left] & 15)
        right_free = not (values[right] & 15)
        if left_free or right_free:
            assert left_free != right_free
            label_node, own_node = (left, right) if left_free else (right, left)
            formal[node] = formal[own_node] ^ (1 << len(labels))
            labels.append(values[label_node] >> 4)
        else:
            formal[node] = formal[left] ^ formal[right]
    assert [values[node] for node in outputs] == expected
    live = set()
    stack = list(outputs)
    while stack:
        node = stack.pop()
        if node not in operands or node in live:
            continue
        live.add(node)
        stack.extend(operands[node])
    assert live == set(operands), "An unneeded gate remains"
    traces = [
        sum(((formal[node] >> j) & 1) << c for c, node in enumerate(outputs))
        for j in range(len(labels))
    ]
    return values, labels, traces, {
        "name": name,
        "gates": len(gates),
        "outputs": len(outputs),
        "entries": len(labels),
        "all_gates_live_and_distinct": True,
        "label_rank": rank(labels),
        "trace_rank": rank(traces),
    }


def main():
    s = [(1 << i) ^ (1 << ((i + 1) % 4)) for i in range(4)]
    expected = [(15 ^ (1 << i)) ^ (s[i] << 4) for i in range(4)]
    first = [
        ("p", "x0", "x1"),
        ("q", "x0", "x3"),
        ("u", "q", "s1"),
        ("v", "p", "s2"),
        ("w", "x2", "s3"),
        ("d", "u", "v"),
        ("U0", "d", "w"),
        ("U1", "u", "x2"),
        ("U2", "v", "x3"),
        ("U3", "w", "p"),
    ]
    values, _, _, first_result = verify(
        "ten_gate_sheet_with_diagonal",
        {f"s{i}": s[i] << 4 for i in (1, 2, 3)},
        first,
        [f"U{i}" for i in range(4)],
        expected,
    )
    assert values["d"] == 10 ^ (10 << 4)
    assert len(first) == 10
    first_result["clean_diagonal_mask"] = values["d"]

    h = 1
    q = [h ^ value for value in s]
    second = [
        ("g1", "x0", "x1"),
        ("g2", "g1", "h"),
        ("g3", "g2", "x2"),
        ("g4", "g3", "x3"),
        ("g5", "g4", "x0"),
        ("O0", "g5", "q0"),
        ("g7", "g4", "x1"),
        ("O1", "g7", "q1"),
        ("g9", "g2", "x3"),
        ("O2", "g9", "q2"),
        ("O3", "g3", "q3"),
    ]
    _, labels, traces, second_result = verify(
        "eleven_gate_sheet_avoiding_clean_labels",
        {"h": h << 4} | {f"q{i}": q[i] << 4 for i in range(4)},
        second,
        [f"O{i}" for i in range(4)],
        expected,
    )
    assert len(second) == 11 and len(labels) == 5
    assert all(label.bit_count() % 2 == 1 for label in labels)
    assert rank(labels) == rank(traces) == 4
    assert len(set(traces)) == 5 and 0 not in traces
    assert sum(trace.bit_count() % 2 for trace in traces) == 4
    trace_sum = 0
    odd_label_sum = 0
    for label, trace in zip(labels, traces):
        trace_sum ^= trace
        if trace.bit_count() % 2:
            odd_label_sum ^= label
    assert trace_sum == odd_label_sum == 0
    even_index = next(i for i, trace in enumerate(traces) if not trace.bit_count() % 2)
    assert rank([label for i, label in enumerate(labels) if i != even_index]) == 3
    second_result["trace_masks"] = traces
    second_result["all_entry_labels_outside_even_subspace"] = True
    print(json.dumps([first_result, second_result], indent=2))


if __name__ == "__main__":
    main()
