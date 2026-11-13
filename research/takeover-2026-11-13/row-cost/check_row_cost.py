#!/usr/bin/env python3
"""Evaluate specified constructions in PORTS and FOUR_ROWS; never search circuits."""

import json
from functools import reduce
from operator import xor
from pathlib import Path


class Circuit:
    def __init__(self, sizes, free_blocks=()):
        self.blocks = []
        self.units = []
        offset = 0
        for size in sizes:
            units = [1 << (offset + j) for j in range(size)]
            self.units.append(units)
            self.blocks.append(sum(units))
            offset += size
        self.inputs = {v for block in self.units for v in block}
        self.available = set(self.inputs)
        self.free_blocks = set(free_blocks)
        self.gates = []
        self.parents = {}

    def free(self, block, indices):
        assert block in self.free_blocks
        value = reduce(xor, (self.units[block][i] for i in indices), 0)
        self.available.add(value)
        return value

    def add(self, left, right):
        assert left in self.available and right in self.available
        value = left ^ right
        assert value and value not in self.available, "Specified construction must be reduced"
        self.available.add(value)
        self.gates.append(value)
        self.parents[value] = (left, right)
        return value

    def chain(self, terms):
        terms = list(terms)
        value = terms[0]
        for term in terms[1:]:
            value = self.add(value, term)
        return value

    def is_event(self, value):
        if value not in self.parents:
            return False
        left, right = self.parents[value]
        return any(left & block and left & block == right & block for block in self.blocks)

    def ancestors(self, outputs, stop=False):
        seen, todo = set(), list(outputs)
        while todo:
            value = todo.pop()
            if value in seen:
                continue
            seen.add(value)
            if value in self.parents and not (stop and self.is_event(value)):
                todo.extend(self.parents[value])
        return seen


def check_ports(p, f):
    circuit = Circuit([4] * (1 + p + f), range(1 + p, 1 + p + f))
    b = circuit.units[0]
    paid = circuit.units[1:1 + p]
    alpha, beta, gamma = [], [], []
    for block in range(1 + p, 1 + p + f):
        alpha.append(circuit.free(block, (0, 1)))
        beta.append(circuit.free(block, (0, 2)))
        gamma.append(circuit.free(block, (0, 3)))
    if p:
        u0 = circuit.chain([b[3]] + [a[1] for a in paid] + alpha)
        u1 = circuit.chain([b[0]] + [a[2] for a in paid] + beta)
        u2 = circuit.chain([b[1]] + [a[3] for a in paid] + gamma)
        u3 = circuit.chain([b[2]] + [a[0] for a in paid])
        outputs = [circuit.chain(terms) for terms in (
            (u0, u3, b[1]), (u0, u1, b[2]),
            (u1, u2, b[3]), (u2, u3, b[0]),
        )]
        expected = 4 * p + 3 * f + 8
    elif f:
        u = circuit.chain([b[2], b[3]] + alpha)
        v = circuit.chain([b[0]] + beta)
        w = circuit.chain([b[1]] + gamma)
        outputs = [circuit.chain(terms) for terms in (
            (u, b[1]), (u, v), (v, w, b[3]), (b[0], b[2], w),
        )]
        expected = 3 * f + 7
    else:
        p01, p23 = circuit.add(b[0], b[1]), circuit.add(b[2], b[3])
        outputs = [circuit.add(p23, b[1]), circuit.add(p23, b[0]),
                   circuit.add(p01, b[3]), circuit.add(p01, b[2])]
        expected = 6
    for c, output in enumerate(outputs):
        target = sum(v for j, v in enumerate(b) if j != c)
        for block in circuit.units[1:]:
            target ^= block[c] ^ block[(c + 1) % 4]
        assert output == target
    assert len(circuit.gates) == expected
    assert not any(circuit.is_event(gate) for gate in circuit.gates)
    assert set(circuit.gates) <= circuit.ancestors(outputs)
    return {"ordinary_neighbors": p, "free_neighbors": f, "gates": expected,
            "outputs_correct": True, "event_free": True}


def check_four_rows(r, translations):
    circuit = Circuit([4, 4] + [4] * r + [2] * (4 * r))
    pairs = [[circuit.add(block[c], block[(c + 1) % 4]) for c in range(4)]
             for block in circuit.units[:2]]
    shifts = [circuit.add(pairs[0][c], pairs[1][c]) for c in range(4)] if translations else []
    outputs, targets = [], []
    for i in range(r):
        z = circuit.units[2 + i]
        p01, p23 = circuit.add(z[0], z[1]), circuit.add(z[2], z[3])
        triples = [circuit.add(p23, z[1]), circuit.add(p23, z[0]),
                   circuit.add(p01, z[3]), circuit.add(p01, z[2])]
        for c in range(4):
            partner = circuit.add(triples[c], pairs[1][c])
            target = circuit.add(partner, shifts[c]) if translations else circuit.add(triples[c], pairs[0][c])
            tag = circuit.units[2 + r + 4 * i + c]
            tagged = circuit.chain([partner] + tag)
            expected_own = sum(v for j, v in enumerate(z) if j != c)
            assert target == expected_own ^ pairs[0][c]
            assert tagged == expected_own ^ pairs[1][c] ^ sum(tag)
            outputs.extend((target, tagged))
            targets.append(target)
    gates = set(circuit.gates)
    events = {g for g in gates if circuit.is_event(g)}
    hidden = gates - circuit.ancestors(outputs, stop=True)
    assert gates <= circuit.ancestors(outputs)
    assert len(gates) == 22 * r + (12 if translations else 8)
    assert events == (set(targets) if translations else set())
    assert hidden == (set(shifts + pairs[0]) if translations else set())
    return {"sheets": r, "translations": translations, "gates": len(gates),
            "outputs": len(outputs), "events": len(events), "hidden": len(hidden),
            "outputs_correct": True, "reduced_live": True}


if __name__ == "__main__":
    result = {
        "method": "Direct evaluation of specified constructions; no search or lower-bound enumeration.",
        "ports": [check_ports(p, f) for p, f in
                  ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (2, 0), (2, 2))],
        "four_rows": [check_four_rows(8, True), check_four_rows(8, False)],
    }
    path = Path(__file__).with_name("check-results.json")
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
