#!/usr/bin/env python3
"""Linear algebra on two specified relation graphs and one specified producer."""

import json
from pathlib import Path


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


def kernel(columns):
    basis, dependencies = {}, []
    for index, value in enumerate(columns):
        coefficients = 1 << index
        while value:
            pivot = value.bit_length() - 1
            if pivot in basis:
                previous, previous_coefficients = basis[pivot]
                value ^= previous
                coefficients ^= previous_coefficients
            else:
                basis[pivot] = value, coefficients
                break
        if not value:
            dependencies.append(coefficients)
    return dependencies


def relation_plane(three_directions):
    odd_values = [1, 7, 13, 11]
    even_values = [6, 12, 10] if three_directions else [6, 12]
    # These are the explicitly described matchings, not generated configurations.
    edges = [(0, 1, 0), (2, 3, 0), (0, 2, 1), (1, 3, 1)]
    if three_directions:
        edges += [(0, 3, 2), (1, 2, 2)]
    incidence = [(1 << u) ^ (1 << v) for u, v, _ in edges]
    formal_rows = []
    for u, v, colour in edges:
        assert odd_values[u] ^ odd_values[v] == even_values[colour]
        formal_rows.append((1 << u) ^ (1 << v) ^ (1 << (4 + colour)))
    even_relations = [7] if three_directions else []
    formal_rows.extend(value << 4 for value in even_relations)
    cycle_colours = []
    for cycle in kernel(incidence):
        colour_sum = 0
        for index, (_, _, colour) in enumerate(edges):
            if cycle & (1 << index):
                colour_sum ^= 1 << colour
        cycle_colours.append(colour_sum)
    direct_rank = rank(formal_rows)
    graph_rank = rank(incidence) + rank(even_relations + cycle_colours)
    assert direct_rank == graph_rank == (4 if three_directions else 3)
    if not three_directions:
        assert formal_rows[0] ^ formal_rows[1] ^ formal_rows[2] ^ formal_rows[3] == 0
    return {"even_directions": len(even_values), "available_relations": len(formal_rows),
            "formal_relation_rank": direct_rank, "graph_formula_rank": graph_rank}


def supplier_profile():
    # The ten fixed masks verified independently by check_exports.py.
    gates = [3, 12, 13, 7, 3 ^ (3 << 4), 12 ^ (12 << 4),
             14 ^ (3 << 4), 11 ^ (12 << 4), 13 ^ (6 << 4), 7 ^ (9 << 4)]
    values = [1, 2, 4, 8] + gates
    assert len(set(values)) == len(values)
    groups = {}
    for value in values:
        own, free = value & 15, value >> 4
        assert free.bit_count() % 2 == 0
        key = own ^ free, own.bit_count() % 2
        groups.setdefault(key, []).append(value)
    # Add only the free representative of a coset that meets the fixed value set.
    # Every other free-only coset is a singleton and contributes no differences.
    for (residue, parity), group in groups.items():
        if parity == 0:
            group.append(residue << 4)
    clean = groups[0, 0]
    assert rank(clean) == 2
    records = []
    for (residue, parity), group in sorted(groups.items()):
        differences = [value ^ group[0] for value in group]
        joint_rank = rank(clean + differences)
        assert joint_rank == 2
        records.append({"residue": residue, "own_parity": parity,
                        "available_values": len(group), "clean_plus_difference_rank": joint_rank})
    return {"clean_rank": 2, "required_clean_rank": 3,
            "fixed_supplier_profile_deficient": True, "cosets_meeting_fixed_nodes": records}


if __name__ == "__main__":
    result = {"method": "Direct linear algebra on specified graphs and a specified producer; no circuit search.",
              "relation_graphs": [relation_plane(False), relation_plane(True)],
              "supplier_profile": supplier_profile()}
    Path(__file__).with_name("check-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
