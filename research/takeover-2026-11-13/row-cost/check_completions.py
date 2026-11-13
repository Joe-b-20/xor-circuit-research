#!/usr/bin/env python3
"""Directly check the fixed sheet-5 completion witness. No search."""

BLOCK_COUNT = 8
BLOCK_SIZE = 4
INPUT_COUNT = BLOCK_COUNT * BLOCK_SIZE
values = [1 << index for index in range(INPUT_COUNT)]
parents = [None] * INPUT_COUNT
by_value = {value: index for index, value in enumerate(values)}


def inputs(block):
    first = block * BLOCK_SIZE
    return tuple(range(first, first + BLOCK_SIZE))


def part(value, block):
    return (value >> (block * BLOCK_SIZE)) & 15


def gate(left, right):
    value = values[left] ^ values[right]
    assert value
    if value not in by_value:
        by_value[value] = len(values)
        values.append(value)
        parents.append((left, right))
    return by_value[value]


def extend(node, *terms):
    for term in terms:
        node = gate(node, term)
    return node


def pair(block, row):
    coordinates = inputs(block)
    return coordinates[row], coordinates[(row + 1) % BLOCK_SIZE]


def target(sheet, row):
    coordinates = [node for index, node in enumerate(inputs(sheet)) if index != row]
    coordinates.extend(pair((sheet - 1) % BLOCK_COUNT, row))
    if sheet in (1, 3, 4):
        coordinates.extend(pair(7, row))
    return sum(1 << node for node in coordinates)


u = inputs(4)
x = inputs(5)
v = inputs(6)
q = v[0]

beta_0 = gate(u[0], u[1])
beta_1 = gate(u[0], u[2])
beta_2 = gate(u[3], u[0])
p_0 = extend(q, x[1], x[3], x[2])
p_1 = extend(q, x[0], x[1])
p_2 = gate(q, x[3])
ell = gate(p_0, x[0])

a_0 = gate(beta_0, p_0)
a_1 = gate(beta_1, p_1)
a_2 = gate(beta_2, p_2)
hidden_operands = {a_0, a_1, a_2}
outputs = {
    (5, 0): gate(a_0, q),
    (5, 1): gate(a_0, a_1),
    (5, 2): gate(a_1, a_2),
    (5, 3): gate(a_2, ell),
    (6, 1): extend(ell, v[2], v[3], x[0], x[3]),
    (6, 2): extend(p_0, v[1], v[3], x[1]),
    (6, 0): extend(p_1, v[1], v[2], v[3], v[0]),
    (6, 3): extend(p_2, v[1], v[2], x[0]),
}
for node, missing_own, row in ((beta_0, u[2], 3), (beta_1, u[3], 1), (beta_2, u[1], 2)):
    outputs[4, row] = extend(node, missing_own, *pair(3, row), *pair(7, row))

for sheet in range(BLOCK_COUNT):
    for row in range(BLOCK_SIZE):
        if (sheet, row) not in outputs:
            mask = target(sheet, row)
            coordinates = [index for index in range(INPUT_COUNT) if mask & (1 << index)]
            outputs[sheet, row] = extend(*coordinates)


def event(node):
    if parents[node] is None:
        return False
    left, right = parents[node]
    return any(
        part(values[left], block) and part(values[left], block) == part(values[right], block)
        for block in range(BLOCK_COUNT)
    )


def reachable(start, stop_at_events):
    todo = list(start)
    seen = set()
    while todo:
        node = todo.pop()
        if node in seen:
            continue
        seen.add(node)
        if parents[node] is not None and (not stop_at_events or not event(node)):
            todo.extend(parents[node])
    return seen


assert len(outputs) == INPUT_COUNT
assert all(values[node] == target(*key) for key, node in outputs.items())
live = reachable(outputs.values(), stop_at_events=False)
visible = reachable(outputs.values(), stop_at_events=True)
live_gates = {node for node in live if node >= INPUT_COUNT}
sheet_5_events = {outputs[5, row] for row in range(BLOCK_SIZE)}
assert {node for node in live_gates if event(node)} == sheet_5_events
assert sheet_5_events <= visible
assert live_gates - visible == hidden_operands
assert parents[outputs[5, 0]] == (a_0, q)
assert parents[outputs[5, 1]] == (a_0, a_1)
assert parents[outputs[5, 2]] == (a_1, a_2)
assert parents[outputs[5, 3]] == (a_2, ell)
assert len({values[node] for node in live_gates}) == len(live_gates)
assert all(values[node] not in values[:INPUT_COUNT] for node in live_gates)
assert ell in reachable([outputs[6, 1]], stop_at_events=True)
assert part(values[ell], 6) and values[ell] ^ values[q] == 15 << (5 * BLOCK_SIZE)

print(f"{len(live_gates)} reduced live gates, all 32 MixColumns outputs correct.")
print("Exactly four events, all designated sheet-5 outputs, and exactly three hidden gates.")
print("The parity-shifted local partner is retained through sheet 6.")
