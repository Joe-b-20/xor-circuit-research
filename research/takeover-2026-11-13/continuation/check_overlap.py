#!/usr/bin/env python3
"""Check the one specified MixColumns overlap witness; no circuit search."""

values = [1 << i for i in range(32)]
parents = [None] * 32


def coordinate(block, bit):
    return 4 * block + bit


def part(value, block):
    return (value >> (4 * block)) & 15


def gate(left, right):
    values.append(values[left] ^ values[right])
    parents.append((left, right))
    return len(values) - 1


def chain(nodes):
    current = nodes[0]
    for node in nodes[1:]:
        current = gate(current, node)
    return current


def target(sheet, row):
    own = sum(1 << coordinate(sheet, i) for i in range(4) if i != row)
    def pair(block):
        return ((1 << coordinate(block, row)) |
                (1 << coordinate(block, (row + 1) % 4)))
    return own ^ pair((sheet - 1) % 8) ^ (pair(7) if sheet in (1, 3, 4) else 0)


def advance(current, wanted):
    for block in range(8):
        old, new = part(values[current], block), part(wanted, block)
        for bit in range(4):
            if (new >> bit) & 1 and not (old >> bit) & 1:
                current = gate(current, coordinate(block, bit))
        for bit in range(4):
            if (old >> bit) & 1 and not (new >> bit) & 1:
                current = gate(current, coordinate(block, bit))
    assert values[current] == wanted
    return current


u = chain([coordinate(2, 0), coordinate(2, 1), coordinate(7, 0),
           coordinate(3, 1), coordinate(3, 2), coordinate(3, 3)])
v = chain([coordinate(3, 0), coordinate(3, 1), coordinate(7, 1),
           coordinate(4, 1), coordinate(4, 2), coordinate(4, 3)])
a = gate(u, v)
b = gate(v, coordinate(7, 1))
c = gate(u, coordinate(7, 0))
f = gate(a, b)
g = gate(a, c)
outputs = {(3, 0): f, (4, 0): g,
           (3, 1): advance(u, target(3, 1)),
           (3, 2): advance(c, target(3, 2)),
           (4, 1): advance(v, target(4, 1)),
           (4, 2): advance(b, target(4, 2))}
for sheet in range(8):
    for row in range(4):
        if (sheet, row) not in outputs:
            mask = target(sheet, row)
            outputs[sheet, row] = chain([i for i in range(32) if (mask >> i) & 1])

assert len(values) - 32 == 159
assert all(values[node] == target(*key) for key, node in outputs.items())

# Redirect equal values to their earliest input/gate, then prune unreachable gates.
lookup = {values[i]: i for i in range(32)}
mapped = list(range(32))
reduced_values = values[:32]
reduced_parents = [None] * 32
for node in range(32, len(values)):
    mask = values[node]
    if mask in lookup:
        mapped.append(lookup[mask])
        continue
    assert mask != 0
    lookup[mask] = len(reduced_values)
    mapped.append(len(reduced_values))
    reduced_values.append(mask)
    reduced_parents.append(tuple(mapped[operand] for operand in parents[node]))
outputs = {key: mapped[node] for key, node in outputs.items()}


def event(node):
    if reduced_parents[node] is None:
        return False
    left, right = reduced_parents[node]
    return any(part(reduced_values[left], d) != 0 and
               part(reduced_values[left], d) == part(reduced_values[right], d)
               for d in range(8))


def reachable(stop_at_events):
    seen, todo = set(), list(outputs.values())
    while todo:
        node = todo.pop()
        if node in seen:
            continue
        seen.add(node)
        if reduced_parents[node] and (not stop_at_events or not event(node)):
            todo.extend(reduced_parents[node])
    return seen


live = reachable(False)
visible = reachable(True)
physical_gates = {node for node in live if node >= 32}
hidden = physical_gates - visible
assert len(physical_gates) == 156
assert hidden == {mapped[a]}
assert event(outputs[3, 0]) and event(outputs[4, 0])
assert mapped[a] in reduced_parents[outputs[3, 0]]
assert mapped[a] in reduced_parents[outputs[4, 0]]
assert all(reduced_values[node] == target(*key) for key, node in outputs.items())
assert len({reduced_values[node] for node in physical_gates}) == len(physical_gates)
assert all(reduced_values[node] not in values[:32] for node in physical_gates)
print('All 32 masks correct; 156 distinct non-input live gates; one hidden gate,')
print('which is an operand of the sheet-3 and sheet-4 row-0 output events.')
