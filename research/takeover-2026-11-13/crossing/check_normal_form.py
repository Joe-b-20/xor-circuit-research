#!/usr/bin/env python3
"""Evaluate the established producer graphs and one partial auxiliary control; no search."""

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("tree_checks", HERE.parent / "frontier/check_tree.py")
tree_checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tree_checks)
checks = tree_checks.checks


def partial_auxiliary_control():
    c = checks.Circuit([4, 4], (1,))
    b = c.units[0]
    p01 = c.add(b[0], b[1])
    e2 = c.add(p01, b[3])
    p02 = c.add(b[0], b[2])
    diagonal = c.add(p02, checks.free(c, 5))
    auxiliary = c.add(e2, checks.free(c, 6))
    row = c.add(auxiliary, diagonal)
    assert row == (14 | (3 << 4))
    assert len(c.gates) == 6
    assert all(not c.is_event(v) for v in c.gates)
    assert diagonal in c.ancestors([row])
    assert set(c.gates) <= c.ancestors([row])
    return {"gates": 6, "event_free": True, "noncycle_diagonal_feeds_row": True,
            "scope": "Partial circuit only; not an augmented solution."}


def main():
    c = checks.Circuit([4, 4], (1,))
    b = c.units[0]
    labels = [checks.free(c, (1 << i) ^ (1 << ((i + 1) % 4))) for i in range(4)]
    # Exactly the ten gates in tradeoff/EXPORTS.md.
    p, q = c.add(b[0], b[1]), c.add(b[2], b[3])
    e1, e3 = c.add(q, b[0]), c.add(p, b[2])
    d01, d23 = c.add(p, labels[0]), c.add(q, labels[2])
    u0, u2 = c.add(d01, e1), c.add(d23, e3)
    u1, u3 = c.add(e1, labels[1]), c.add(e3, labels[3])
    outputs = [u0, u1, u2, u3]
    summary, entry_labels = checks.inspect(c, outputs, labels, 10, "two_clean_diagonals")

    def odd(v):
        return (v & 15).bit_count() % 2 == 1

    def rho(v):
        return (v & 15) ^ (v >> 4)

    def own_class(v):
        return (v & 3).bit_count() % 2

    def in_residue_plane(v):
        return checks.rank([3, 12, v]) == 2

    named = [*b, *outputs]
    odd_nodes = set(b) | {v for v in c.gates if odd(v)}
    even_nodes = [v for v in c.gates if not odd(v)]
    nonentry_edges, odd_entry_edges = [], []
    even_labels, odd_labels = [], []
    for v in c.gates:
        left, right = c.parents[v]
        if not left & 15 or not right & 15:
            label, other = (left, right) if not left & 15 else (right, left)
            if odd(v):
                odd_labels.append(label >> 4)
                odd_entry_edges.append((v, other))
            else:
                even_labels.append(label >> 4)
        else:
            endpoints = [w for w in [left, right, v] if odd(w)]
            assert len(endpoints) == 2
            nonentry_edges.append(tuple(endpoints))

    assert checks.rank(even_nodes) == len(even_nodes) == 4
    assert checks.rank([rho(v) for v in even_nodes]) == 2
    assert len(even_labels) == checks.rank(even_labels) == 2
    assert all(in_residue_plane(v) for v in even_labels)
    assert len(odd_labels) == 2 and all(not in_residue_plane(v) for v in odd_labels)
    forest = tree_checks.graph_data(odd_nodes, nonentry_edges)
    assert forest == {"vertices": 10, "edges": 6, "components": 4,
                      "incidence_rank": 6, "forest": True}
    class_results = []
    for index in [0, 1]:
        vertices = {v for v in odd_nodes if own_class(v) == index}
        edges = [(u, v) for u, v in nonentry_edges + odd_entry_edges if own_class(u) == index]
        assert all(own_class(v) == index for _, v in edges)
        data = tree_checks.graph_data(vertices, edges)
        assert data == {"vertices": 5, "edges": 4, "components": 1,
                        "incidence_rank": 4, "forest": True}
        residue_sum = 0
        for v in named:
            if own_class(v) == index:
                residue_sum ^= rho(v)
        assert residue_sum == 5  # w+P w = 0011 XOR 0110.
        class_results.append({"own_class": index, "named_residue_sum": residue_sum, **data})

    result = {
        "method": "Direct evaluation of one producer and one partial auxiliary control; no search.",
        "construction": summary,
        "clean_diagonal_rank": checks.rank([d01, d23]),
        "physical_even_rank": checks.rank(even_nodes),
        "even_entry_labels": even_labels,
        "odd_entry_labels": odd_labels,
        "nonentry_forest": forest,
        "lifted_class_trees": class_results,
        "partial_auxiliary_control": partial_auxiliary_control(),
    }
    (HERE / "check-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
