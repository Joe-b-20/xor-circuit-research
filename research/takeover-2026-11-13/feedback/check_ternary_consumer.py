"""Direct evaluation of one prescribed ten-bearing-gate consumer and its exit."""

import json


def rank(values):
    pivots = {}
    for value in values:
        while value:
            pivot = value.bit_length() - 1
            if pivot not in pivots:
                pivots[pivot] = value
                break
            value ^= pivots[pivot]
    return len(pivots)


values = {f"z{i}": 1 << i for i in range(4)}
values.update(a=1 << 4, b=1 << 5, c=1 << 6)
own_mask = 15
steps = [
    ("q", "z0", "z1"),
    ("r", "q", "z2"),
    ("t", "r", "z3"),
    ("u", "t", "a"),
    ("v", "u", "c"),
    ("w", "v", "b"),
    ("e", "t", "w"),
    ("ab", "e", "c"),
    ("Y0", "w", "z0"),
    ("Y1", "v", "z1"),
    ("Y2", "u", "z2"),
    ("Y3", "r", "ab"),
]
formal = {f"z{i}": 0 for i in range(4)}
entries = []
bearing = 0
source = 0
before_exit_source = None
for name, left, right in steps:
    if name == "e":
        before_exit_source = {
            key: value for key, value in values.items() if not value & own_mask
        }
    value = values[left] ^ values[right]
    assert value and value not in values.values()
    values[name] = value
    if value & own_mask:
        bearing += 1
        left_bearing = bool(values[left] & own_mask)
        right_bearing = bool(values[right] & own_mask)
        if left_bearing and right_bearing:
            formal[name] = formal[left] ^ formal[right]
        else:
            previous = left if left_bearing else right
            label = right if left_bearing else left
            formal[name] = formal[previous] ^ (1 << len(entries))
            entries.append(label)
    else:
        source += 1

a, b, c = values["a"], values["b"], values["c"]
labels = [a ^ b ^ c, a ^ c, a, a ^ b]
for i, label in enumerate(labels):
    assert values[f"Y{i}"] == (own_mask ^ (1 << i)) ^ label
assert rank(labels) == 3 and labels[0] ^ labels[1] ^ labels[2] ^ labels[3] == 0
assert values["e"] == a ^ b ^ c
assert before_exit_source == {"a": a, "b": b, "c": c}
assert (values["e"] >> 4).bit_count() == 3
assert entries == ["a", "c", "b", "ab"]
traces = [
    sum(((formal[f"Y{i}"] >> j) & 1) << i for i in range(4))
    for j in range(4)
]
assert traces == [0b0111, 0b0011, 0b0001, 0b1000]
assert rank(traces) == 4
assert bearing == 10 and source == 2

# One specified substitution into the three-dimensional even diagonal.
diag = lambda mask: mask | (mask << 4)
d0, d1, d2, d3 = map(diag, [0b0011, 0b0110, 0b1100, 0b1001])
ma, mb, mc = d2, d2 ^ d3, d1 ^ d2
assert rank([ma, mb, mc]) == 3
assert [ma ^ mb ^ mc, ma ^ mc, ma, ma ^ mb] == [d0, d1, d2, d3]

print(json.dumps({
    "consumer_bearing_gates": bearing,
    "source_side_gates": source,
    "entry_labels": entries,
    "entry_trace_masks": traces,
    "entry_trace_rank": rank(traces),
    "source_target_rank": rank(labels),
    "early_return_is_three_independent_labels": True,
    "fourth_label_supplied_after_return": True,
    "mixcolumns_label_substitution": True,
}, indent=2))
