"""Verify the specified 60-atom decomposition in QUADRATIC_LIFT_LIMIT.md.

This constructs the displayed atoms and checks their sum. It does not search,
optimize, enumerate circuits, or test alternative configurations.
"""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
MATRIX = Path("circuits/aes-mixcolumns/aes-mixcolumns.mat.txt")
PAIRS = [(i, j) for i in range(32) for j in range(i + 1, 32)]


def quadratic(mask):
    """Coordinate quadratic lift, represented by a 496-bit integer."""
    return sum(
        (((mask >> i) & 1) & ((mask >> j) & 1)) << k
        for k, (i, j) in enumerate(PAIRS)
    )


def wedge(left, right):
    return quadratic(left ^ right) ^ quadratic(left) ^ quadratic(right)


def main():
    lines = (ROOT / MATRIX).read_text().splitlines()
    assert lines[:2] == ["1", "32 32"]
    entries = [[int(x) for x in line.split()] for line in lines[2:34]]
    assert len(entries) == 32
    assert all(len(row) == 32 and set(row) <= {0, 1} for row in entries)
    rows = [sum(x << i for i, x in enumerate(row)) for row in entries]

    atoms = []
    weights = []
    common_triples = 0
    for sheet in range(8):
        weight = rows[sheet].bit_count()
        assert all(rows[8 * byte + sheet].bit_count() == weight for byte in range(4))
        weights.append(weight)
        near = (sheet - 1) % 8
        for first in (0, 2):
            second = (first + 1) % 4
            indices = [
                8 * ((first + 2) % 4) + sheet,
                8 * ((first + 3) % 4) + sheet,
                8 * ((first + 1) % 4) + near,
            ]
            units = [1 << i for i in indices]
            common = units[0] ^ units[1] ^ units[2]
            assert common.bit_count() == 3
            common_triples += 1
            left, right = units[0] ^ units[1], units[1] ^ units[2]
            influence = (1 << (8 * first + sheet)) ^ (1 << (8 * second + sheet))
            assert wedge(left, right) == quadratic(common)
            atoms.append((influence, left, right))

            for byte in (first, second):
                output = 8 * byte + sheet
                row = rows[output]
                assert row & common == common
                remainder = row ^ common
                vectors = [common] + [1 << i for i in range(32) if remainder >> i & 1]
                assert len(vectors) % 2 == 1
                prefix = vectors[0]
                for k in range(1, len(vectors), 2):
                    atoms.append((1 << output, prefix ^ vectors[k], vectors[k] ^ vectors[k + 1]))
                    prefix ^= vectors[k] ^ vectors[k + 1]

    reconstructed = [0] * 32
    for influence, left, right in atoms:
        atom_value = wedge(left, right)
        assert atom_value
        for output in range(32):
            if influence >> output & 1:
                reconstructed[output] ^= atom_value

    assert weights == [5, 7, 5, 7, 7, 5, 5, 5]
    assert common_triples == 16
    assert len(atoms) == 60
    assert reconstructed == [quadratic(row) for row in rows]
    print(json.dumps({
        "matrix": str(MATRIX),
        "sheet_row_weights": weights,
        "prescribed_common_triples": common_triples,
        "specified_atoms": len(atoms),
        "all_32_quadratic_rows_verified": True,
        "circuit_search": False,
        "optimization": False,
    }, indent=2))


if __name__ == "__main__":
    main()
