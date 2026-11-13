#!/usr/bin/env python3
"""Direct evaluation of the displayed compatibility constructions. No search."""

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


def free(circuit, mask):
    return circuit.free(1, (j for j in range(len(circuit.units[1])) if mask & (1 << j)))


def inspect(circuit, outputs, labels, expected, name):
    b = circuit.units[0]
    for row, value in enumerate(outputs[:4]):
        assert value == sum(v for i, v in enumerate(b) if i != row) ^ labels[row]
    assert len(circuit.gates) == expected
    assert all(value & 15 for value in circuit.gates)
    assert set(circuit.gates) <= circuit.ancestors(outputs)
    formal = {v: 0 for v in circuit.inputs if v & 15}
    entries = []
    for value in circuit.gates:
        left, right = circuit.parents[value]
        if not left & 15 or not right & 15:
            label, other = (left, right) if not left & 15 else (right, left)
            formal[value] = formal[other] ^ (1 << len(entries))
            entries.append(label)
        else:
            formal[value] = formal[left] ^ formal[right]
    traces = [sum(1 << row for row, value in enumerate(outputs[:4])
                  if formal[value] & (1 << index)) for index in range(len(entries))]
    return {"name": name, "gates": expected, "targets": len(outputs),
            "entries": len(entries), "label_rank": rank(entries),
            "trace_rank_for_four_rows": rank(traces), "trace_masks": traces,
            "entry_labels": entries, "all_gates_live_distinct": True}, entries


def projected_gate_count(circuit, projection):
    available = {projection(v) for v in circuit.inputs if v & 15}
    retained = 0
    for value in circuit.gates:
        left, right = circuit.parents[value]
        a, b = projection(left), projection(right)
        assert not a & 15 or a in available
        assert not b & 15 or b in available
        image = projection(value)
        assert image == a ^ b
        if image & 15 and image not in available:
            available.add(image)
            retained += 1
    return retained


def rank_two_split():
    c = Circuit([4, 5], (1,))
    x = c.units[0]
    d = [free(c, v) for v in (1, 2, 4, 7)]
    u = c.chain([x[2], x[3], free(c, 8), free(c, 16), free(c, 1 ^ 8 ^ 16)])
    v = c.add(x[0], free(c, 3))
    w = c.add(x[1], d[3])
    outputs = [c.add(u, x[1]), c.add(u, v), c.chain([v, w, x[3]]),
               c.chain([x[0], x[2], w])]
    result, entries = inspect(c, outputs, d, 12, "two_unused_label_dimensions")
    assert rank(entries + d) == rank(entries) == rank(d) + 2
    count = projected_gate_count(c, lambda value: value & ((1 << 7) - 1))
    assert count == 10
    result["after_projecting_unused_dimensions"] = count
    return result


def mixed_interface():
    c = Circuit([4, 4], (1,))
    x = c.units[0]
    d = [free(c, (1 << j) ^ (1 << ((j + 1) % 4))) for j in range(4)]
    h, lam = free(c, 1), free(c, 5)
    a = c.chain([x[2], x[3], h, free(c, 1 ^ 6)])
    b = c.chain([x[0], x[1], d[3]])
    outputs = [c.chain([a, x[1], lam]), c.add(a, x[0]),
               c.chain([b, x[3], lam]), c.add(b, x[2])]
    result, entries = inspect(c, outputs, d, 11, "mixed_interface_with_repeated_clean_label")
    assert entries.count(lam) == 2
    assert sum((label >> 4).bit_count() % 2 for label in entries) == 2
    assert rank(entries) == 4 and rank(d) == 3
    count = projected_gate_count(c, lambda value: value ^ (h if (value >> 4).bit_count() % 2 else 0))
    assert count == 10
    result["after_killing_outside_label"] = count
    return result


def diagonals(full_clean_interface):
    c = Circuit([4, 4], (1,))
    b = c.units[0]
    s = [free(c, (1 << j) ^ (1 << ((j + 1) % 4))) for j in range(4)]
    p01, p23 = c.add(b[0], b[1]), c.add(b[2], b[3])
    e1, e2, e3 = c.add(p23, b[0]), c.add(p01, b[3]), c.add(p01, b[2])
    e0 = c.add(p23, b[1]) if full_clean_interface else None
    t1, t2, t3 = c.add(e1, s[1]), c.add(e2, s[2]), c.add(e3, s[3])
    d01, d23 = c.add(p01, s[0]), c.add(p23, s[2])
    d12 = c.add(t1, e2)
    t0 = c.add(e0, s[0]) if full_clean_interface else c.add(d01, e1)
    exports = [d01, d23, d12]
    assert exports == [mask ^ (mask << 4) for mask in (3, 12, 6)]
    assert rank(exports) == 3
    expected = 13 if full_clean_interface else 12
    result, _ = inspect(c, [t0, t1, t2, t3] + exports, s, expected,
                        "all_clean_triples_and_diagonals" if full_clean_interface else "mixed_diagonal_supply")
    assert not any(c.is_event(value) for value in c.gates)
    result["event_free"] = True
    result["diagonal_rank"] = 3
    return result


def overlapping_even_helpers():
    c = Circuit([4])
    b = c.units[0]
    p, q = c.add(b[0], b[1]), c.add(b[0], b[2])
    e3, e2, e1 = c.add(b[1], q), c.add(b[3], p), c.add(b[3], q)
    e0 = c.add(e2, q)
    result, _ = inspect(c, [e0, e1, e2, e3], [0] * 4, 6, "overlapping_even_helpers")
    assert rank([p, q, 15]) == 3
    result["all_ones_outside_even_helper_span"] = True
    return result


def pure_even_basis():
    c = Circuit([4, 4], (1,))
    b = c.units[0]
    labels = [free(c, (1 << j) ^ (1 << ((j + 1) % 4))) for j in range(4)]
    p, r, s = c.add(b[0], b[1]), c.add(b[0], b[2]), c.add(b[1], b[3])
    h, v = c.add(b[3], labels[1]), c.add(p, free(c, 10))
    u1, u2 = c.add(r, h), c.add(h, v)
    shifted = c.add(u1, free(c, 15))
    u3, u0 = c.add(s, shifted), c.add(v, shifted)
    result, _ = inspect(c, [u0, u1, u2, u3], labels, 10, "three_pure_even_suppliers")
    assert rank([p, r, s]) == 3
    result["pure_even_supplier_rank"] = 3
    return result


if __name__ == "__main__":
    result = {"method": "Evaluate six specified constructions and stated projections; no circuit search.",
              "cases": [rank_two_split(), mixed_interface(), diagonals(False), diagonals(True),
                        overlapping_even_helpers(), pure_even_basis()]}
    (HERE / "check-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
