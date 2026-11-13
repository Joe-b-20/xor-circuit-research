#!/usr/bin/env python3
"""Directly evaluate the fixed ten-gate producer and its 22-gate completion."""

b = [1 << i for i in range(4)]
a = [1 << (4 + i) for i in range(4)]
z = [1 << (8 + i) for i in range(4)]
blocks = (15, 15 << 4, 15 << 8)
available = set(b + z)


def is_available(value):
    return value in available or value & ~(15 << 4) == 0
parents = {}
gates = []


def add(left, right):
    assert is_available(left) and is_available(right)
    assert not any((left & block) and (left & block) == (right & block)
                   for block in blocks)
    result = left ^ right
    assert result and not is_available(result)
    available.add(result)
    parents[result] = (left, right)
    gates.append(result)
    return result


def s(block, c):
    return block[c] ^ block[(c + 1) % 4]


def e(block, c):
    return sum(block[d] for d in range(4) if d != c)


p01 = add(b[0], b[1])
p23 = add(b[2], b[3])
e1 = add(p23, b[0])
e3 = add(p01, b[2])
d01 = add(p01, s(a, 0))
d23 = add(p23, s(a, 2))
t0 = add(d01, e1)
t2 = add(d23, e3)
t1 = add(e1, s(a, 1))
t3 = add(e3, s(a, 3))
assert len(gates) == 10
assert all(value == (e(b, c) ^ s(a, c))
           for c, value in enumerate((t0, t1, t2, t3)))
assert d01 == (b[0] ^ b[1] ^ a[0] ^ a[1])
assert d23 == (b[2] ^ b[3] ^ a[2] ^ a[3])

e2 = add(p01, b[3])
d12 = add(t1, e2)
assert d12 == (b[1] ^ b[2] ^ a[1] ^ a[2])

g = add(z[2], z[3])
h = add(g, z[1])
u = add(h, d01)
v = add(z[0], d12)
w = add(z[3], d23)
r0 = u
r1 = add(g, v)
r2 = add(add(w, z[0]), z[1])
r3 = add(add(u, v), w)
assert len(gates) == 22
assert all(value == (e(z, c) ^ s(b, c) ^ s(a, c))
           for c, value in enumerate((r0, r1, r2, r3)))

# Every non-input gate is used by a designated row in this fixed circuit.
todo = [t0, t1, t2, t3, r0, r1, r2, r3]
live = set()
while todo:
    node = todo.pop()
    if node in live:
        continue
    live.add(node)
    if node in parents:
        todo.extend(parents[node])
assert set(gates) <= live
print('Fixed producer: 10 event-free gates, four rows and two independent diagonals.')
print('Fixed joint completion: 22 distinct live event-free gates, all eight rows correct.')
