#!/usr/bin/env python3
"""Check the tree normal form on one specified ten-gate construction; no search."""

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "compatibility_checks", HERE.parent / "compatibility/check_compatibility.py"
)
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


def graph_data(vertices, edges):
    """Incidence rank via components, retaining the given edge multiplicities."""
    parent = {v: v for v in vertices}

    def root(v):
        while parent[v] != v:
            v = parent[v]
        return v

    for u, v in edges:
        assert u != v and u in parent and v in parent
        parent[root(u)] = root(v)
    components = len({root(v) for v in vertices})
    incidence_rank = len(vertices) - components
    return {
        "vertices": len(vertices), "edges": len(edges), "components": components,
        "incidence_rank": incidence_rank, "forest": len(edges) == incidence_rank,
    }


def main():
    c = checks.Circuit([4, 4], (1,))
    b = c.units[0]
    labels = [checks.free(c, (1 << j) ^ (1 << ((j + 1) % 4))) for j in range(4)]
    # The fixed construction in compatibility/CONTROLS.md.
    p, r, s = c.add(b[0], b[1]), c.add(b[0], b[2]), c.add(b[1], b[3])
    h, v = c.add(b[3], labels[1]), c.add(p, checks.free(c, 10))
    u1, u2 = c.add(r, h), c.add(h, v)
    shifted = c.add(u1, checks.free(c, 15))
    u3, u0 = c.add(s, shifted), c.add(v, shifted)
    outputs = [u0, u1, u2, u3]
    summary, entry_labels = checks.inspect(c, outputs, labels, 10, "three_even_directions")

    def odd(value):
        return (value & 15).bit_count() % 2 == 1

    odd_nodes = set(b) | {value for value in c.gates if odd(value)}
    even_nodes = [value for value in c.gates if not odd(value)]
    nonentry_edges, odd_entry_edges, formal_relations = [], [], []
    coordinates = {value: 1 << i for i, value in enumerate([*b, *c.gates])}
    for value in c.gates:
        left, right = c.parents[value]
        if not left & 15 or not right & 15:
            other = right if not left & 15 else left
            if odd(value):
                odd_entry_edges.append((value, other))
        else:
            triple = [left, right, value]
            endpoints = [node for node in triple if odd(node)]
            assert len(endpoints) == 2
            nonentry_edges.append(tuple(endpoints))
            formal_relations.append(coordinates[left] ^ coordinates[right] ^ coordinates[value])

    projected_vertices = {value & 15 for value in odd_nodes}
    projected_edges = [(u & 15, v & 15) for u, v in nonentry_edges]
    projected = graph_data(projected_vertices, projected_edges)
    physical = graph_data(odd_nodes, nonentry_edges)
    lifted = graph_data(odd_nodes, nonentry_edges + odd_entry_edges)
    assert len(entry_labels) == checks.rank(entry_labels) == 3
    assert len(even_nodes) == checks.rank(even_nodes) == 4
    assert checks.rank([value & 15 for value in even_nodes]) == 3
    assert checks.rank(formal_relations) == 7
    assert len(odd_entry_edges) == 2
    assert projected == {"vertices": 8, "edges": 7, "components": 1,
                         "incidence_rank": 7, "forest": True}
    assert physical == {"vertices": 10, "edges": 7, "components": 3,
                        "incidence_rank": 7, "forest": True}
    assert lifted == {"vertices": 10, "edges": 9, "components": 1,
                      "incidence_rank": 9, "forest": True}
    result = {
        "method": "Direct evaluation and linear algebra on one specified circuit; no search.",
        "construction": summary,
        "physical_even_value_rank": checks.rank(even_nodes),
        "even_own_projection_rank": checks.rank([value & 15 for value in even_nodes]),
        "independent_nonentry_relations": checks.rank(formal_relations),
        "projected_cube_tree": projected,
        "physical_nonentry_forest": physical,
        "tree_after_odd_entries": lifted,
    }
    (HERE / "check-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
