#!/usr/bin/env python3
"""Evaluate the two specified ONE_EXIT circuits; no circuit search."""

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("checks", HERE.parent / "row-cost/check_row_cost.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Circuit = module.Circuit


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


def evaluate(feedback):
    c = Circuit([3, 1] + [2] * 4 + [3, 2, 1, 2])
    y = c.units[0]
    z = c.units[1][0]
    first_tags = c.units[2:6]
    consumer_tags = c.units[6:10]
    if feedback:
        g1 = c.add(z, y[0])
        g2 = c.add(g1, y[1])
        g3 = c.add(g2, y[2])
        g4 = c.add(g1, y[2])
        common = c.add(g3, z)
    else:
        common = c.add(c.add(y[0], y[1]), y[2])
        g1 = c.add(z, y[0])
        g2 = c.add(g1, y[1])
        g3 = c.add(g2, y[2])
        g4 = c.add(g1, y[2])
    first = [c.chain([common] + tag) for tag in first_tags]
    consumer = [c.chain([base] + tag) for base, tag in
                zip((g1, g2, g3, g4), consumer_tags)]
    outputs = first + consumer
    expected_first = [sum(y + tag) for tag in first_tags]
    expected_consumer = [z ^ y[0] ^ sum(consumer_tags[0]),
                         z ^ y[0] ^ y[1] ^ sum(consumer_tags[1]),
                         z ^ sum(y) ^ sum(consumer_tags[2]),
                         z ^ y[0] ^ y[2] ^ sum(consumer_tags[3])]
    assert first == expected_first and consumer == expected_consumer
    assert all(value.bit_count() == 5 for value in outputs)
    assert rank(outputs) == 8
    assert len(c.gates) == (21 if feedback else 22)
    assert set(c.gates) <= c.ancestors(outputs)
    events = {value for value in c.gates if c.is_event(value)}
    assert events == ({common} if feedback else set())
    if not feedback:
        assert all(not value & z for value in c.ancestors(first) if value in c.parents)
    return len(c.gates), len(events)


if __name__ == "__main__":
    print("Specified feedback circuit: %d gates, %d event." % evaluate(True))
    print("Specified no-feedback circuit: %d gates, %d events." % evaluate(False))
    print("Both have the required eight independent weight-five outputs and all gates live.")
