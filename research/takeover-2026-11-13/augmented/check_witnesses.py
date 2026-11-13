#!/usr/bin/env python3
"""Directly evaluate the specified 12-gate source and its 22-gate joint completion."""

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("row_checks", HERE.parent / "row-cost/check_row_cost.py")
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


def main():
    c = Circuit([4, 4, 4], (1,))
    b, a, z = c.units
    labels = [c.free(1, (i, (i + 1) % 4)) for i in range(4)]
    # The twelve-gate source in compatibility/DIAGONALS.md.
    p01, p23 = c.add(b[0], b[1]), c.add(b[2], b[3])
    e1, e2, e3 = c.add(p23, b[0]), c.add(p01, b[3]), c.add(p01, b[2])
    t1, t2, t3 = c.add(e1, labels[1]), c.add(e2, labels[2]), c.add(e3, labels[3])
    d01, d23 = c.add(p01, labels[0]), c.add(p23, labels[2])
    d12, t0 = c.add(t1, e2), c.add(d01, e1)
    rows = [t0, t1, t2, t3]
    diagonals = [d01, d12, d23]
    source_gates = list(c.gates)
    assert len(source_gates) == 12
    for i, row in enumerate(rows):
        assert row == (sum(b) ^ b[i]) ^ labels[i]
    assert diagonals == [mask | (mask << 4) for mask in (3, 6, 12)]
    assert rank(diagonals) == 3
    assert set(source_gates) <= c.ancestors(rows + diagonals)
    source_entries = [v for v in source_gates
                      if any(not operand & 15 for operand in c.parents[v])]
    assert len(source_entries) == 5
    assert all(not c.is_event(v) for v in source_gates)

    # The fixed ten-gate consumer, using the three supplied diagonals.
    d0, d1, d2 = diagonals
    g = c.add(z[2], z[3])
    h = c.add(g, z[1])
    u, v, w = c.add(h, d0), c.add(z[0], d1), c.add(z[3], d2)
    y0 = u
    y1 = c.add(g, v)
    y2 = c.add(c.add(w, z[0]), z[1])
    y3 = c.add(c.add(u, v), w)
    consumer_rows = [y0, y1, y2, y3]
    desired_labels = [d0, d1, d2, d0 ^ d1 ^ d2]
    for i, row in enumerate(consumer_rows):
        assert row == (sum(z) ^ z[i]) ^ desired_labels[i]
    assert len(c.gates) == 22
    assert all(not c.is_event(v) for v in c.gates)
    assert set(c.gates) <= c.ancestors(rows + consumer_rows)
    assert all(not value & c.blocks[2] for value in c.ancestors(rows))
    row_cone_gates = set(source_gates) & c.ancestors(rows)
    assert len(row_cone_gates) == 10

    result = {
        "method": "Direct evaluation of specified constructions; no circuit or basis search.",
        "augmented_source": {
            "gates": len(source_gates), "entries": len(source_entries),
            "diagonal_masks": [3, 6, 12], "diagonal_rank": rank(diagonals),
            "all_seven_required_values_checked": True,
            "event_free": True, "all_gates_live_distinct": True,
        },
        "joint_completion": {
            "gates": len(c.gates), "consumer_gates": 10,
            "first_sheet_ancestor_gates": len(row_cone_gates),
            "all_eight_output_values_checked": True,
            "no_feedback_to_first_sheet": True, "event_free": True,
            "all_gates_live_distinct": True,
        },
    }
    (HERE / "check-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
