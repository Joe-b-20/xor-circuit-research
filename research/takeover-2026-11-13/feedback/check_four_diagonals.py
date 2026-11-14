#!/usr/bin/env python3
"""Evaluate two prescribed constructions; no circuit or diagonal-basis search."""

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("row_checks", HERE.parent / "row-cost/check_row_cost.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Circuit = module.Circuit


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


def source(include_d12):
    circuit = Circuit([4, 4, 4], (1,))
    b, a, z = circuit.units
    labels = [circuit.free(1, (i, (i + 1) % 4)) for i in range(4)]
    p01, p23 = circuit.add(b[0], b[1]), circuit.add(b[2], b[3])
    e1, e2, e3 = circuit.add(p23, b[0]), circuit.add(p01, b[3]), circuit.add(p01, b[2])
    u1, u2, u3 = circuit.add(e1, labels[1]), circuit.add(e2, labels[2]), circuit.add(e3, labels[3])
    d01, d23 = circuit.add(p01, labels[0]), circuit.add(p23, labels[2])
    d12 = circuit.add(u1, e2) if include_d12 else None
    u0 = circuit.add(d01, e1)
    rows = [u0, u1, u2, u3]
    for i, row in enumerate(rows):
        assert row == (sum(b) ^ b[i]) ^ labels[i]
    assert len(circuit.gates) == (12 if include_d12 else 11)
    return circuit, rows, d01, d23, d12, e2


def check_source():
    circuit, rows, d01, d23, d12, _ = source(True)
    d13 = circuit.add(d23, d12)
    diagonals = [d23, d12, d13, d01]
    assert diagonals == [mask | (mask << 4) for mask in (12, 6, 10, 3)]
    assert rank(diagonals) == 3
    assert d23 ^ d12 ^ d13 == 0
    assert rank([d23, d12, d01]) == 3
    assert len(circuit.gates) == 13
    assert set(circuit.gates) <= circuit.ancestors(rows + diagonals)
    assert all(not circuit.is_event(gate) for gate in circuit.gates)
    return {"gates": 13, "diagonal_masks": [12, 6, 10, 3],
            "clean_triangle_and_independent_fourth": True,
            "all_required_values_checked": True,
            "event_free": True, "all_gates_live_distinct": True}


def check_joint():
    circuit, rows, d01, d23, _, e2 = source(False)
    source_gates = list(circuit.gates)
    z = circuit.units[2]
    g = circuit.add(z[2], z[3])
    h = circuit.add(g, z[1])
    u = circuit.add(h, d01)
    v_first = circuit.add(z[0], rows[1])
    v = circuit.add(v_first, e2)
    w = circuit.add(z[3], d23)
    targets = [u, circuit.add(g, v), circuit.add(circuit.add(w, z[0]), z[1]),
               circuit.add(circuit.add(u, v), w)]
    d12 = rows[1] ^ e2
    desired_labels = [d01, d12, d23, d01 ^ d12 ^ d23]
    for i, target in enumerate(targets):
        assert target == (sum(z) ^ z[i]) ^ desired_labels[i]
    consumer_gates = circuit.gates[len(source_gates):]
    entries = [operand for gate in consumer_gates for operand in circuit.parents[gate]
               if not operand & circuit.blocks[2]]
    assert entries == [d01, rows[1], e2, d23]
    assert rank(entries) == 4
    assert rank([d01, d23, d12]) == 3
    is_clean = lambda value: (value & 15) == ((value >> 4) & 15) and (value & 15).bit_count() % 2 == 0
    assert [is_clean(label) for label in entries] == [True, False, False, True]
    assert len(source_gates) == 11 and len(consumer_gates) == 11 and len(circuit.gates) == 22
    assert all(value & circuit.blocks[2] for value in consumer_gates)
    assert set(circuit.gates) <= circuit.ancestors(rows + targets)
    assert all(not circuit.is_event(gate) for gate in circuit.gates)
    assert all(not value & circuit.blocks[2] for value in circuit.ancestors(rows))
    return {"gates": 22, "source_gates": 11, "consumer_gates": 11,
            "entry_count": len(entries), "entry_rank": rank(entries),
            "two_clean_two_nonclean_entries": True,
            "all_eight_output_values_checked": True,
            "event_free": True, "no_feedback_to_first_sheet": True,
            "all_gates_live_distinct": True}


if __name__ == "__main__":
    result = {"method": "Direct evaluation of two specified circuits; no search.",
              "four_diagonal_source": check_source(), "mixed_joint": check_joint()}
    (HERE / "four-diagonal-check.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
