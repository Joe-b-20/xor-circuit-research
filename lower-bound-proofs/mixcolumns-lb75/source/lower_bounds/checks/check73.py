"""Integer scalar reduction and independent boundary-rank check for PROOF73.

No optimizer is used. The AES boundary is built directly from multiplication
by 1, 2, 3 modulo x^8+x^4+x^3+x+1. All triples are enumerated exhaustively.
"""
import itertools
import json
from math import comb
from pathlib import Path


def minimum_s(x, y, gates):
    target = 96 - 2 * gates + 2 * x + y
    return next(s for s in range(2 * gates + 1)
                if max(s, comb(s, 2)) >= target)


def parameter_check(gates=72):
    """Enumerate all steady reciprocal count levels, including h=0."""
    examined = 0
    with_fanout = 0
    survivors = []
    rejected_drift_minimum = None
    for a in range(24, gates - 44):
        for b in range(24, gates - 31):
            for Y in range(gates - 31 - a):
                for Z in range(min(Y, gates - 32 - b) + 1):
                    examined += 1
                    difference = Y - Z
                    if gates - 32 - b + difference < 13:
                        continue
                    sa = minimum_s(a, Y, gates)
                    sb = minimum_s(b, Z, gates)
                    if sa > 3 * gates - 128 - 3 * a - 2 * difference:
                        continue
                    if sb > 3 * gates - 128 - 3 * b + 2 * difference:
                        continue
                    with_fanout += 1
                    drift = sa + sb + 192 - 2 * gates - a - b
                    row = {"a": a, "b": b, "Y": Y, "Z": Z,
                           "minimum_s_a": sa, "minimum_s_b": sb,
                           "minimum_two_step_drift": drift}
                    if drift <= 0:
                        survivors.append(row)
                    else:
                        rejected_drift_minimum = min(
                            drift, rejected_drift_minimum or drift)
    if gates == 72:
        assert survivors == [{"a": 24, "b": 24, "Y": 0, "Z": 0,
                              "minimum_s_a": 0, "minimum_s_b": 0,
                              "minimum_two_step_drift": 0}]
    return {"gates": gates, "examined": examined,
            "surviving_fanout_conditions": with_fanout,
            "positive_drift_minimum": rejected_drift_minimum,
            "nonpositive_drift_cases": survivors}


def rank(vectors):
    pivots = {}
    for value in vectors:
        while value:
            leading = value.bit_length() - 1
            if leading in pivots:
                value ^= pivots[leading]
            else:
                pivots[leading] = value
                break
    return len(pivots)


def rank6_check():
    coefficients = ((2, 3, 1, 1), (1, 2, 3, 1),
                    (1, 1, 2, 3), (3, 1, 1, 2))
    columns = []
    for byte in range(4):
        for bit in range(8):
            value = 1 << bit
            twice = (value << 1) ^ (0x11B if value & 0x80 else 0)
            column = 0
            for output_byte in range(4):
                coefficient = coefficients[output_byte][byte]
                product = (value if coefficient == 1 else
                           twice if coefficient == 2 else twice ^ value)
                column |= product << (8 * output_byte)
            columns.append(column)
    # Rows of M^T are columns of M, giving the transpose circuit boundary.
    boundary = [1 << bit for bit in range(32)] + columns
    assert len(set(boundary)) == 64
    assert all(value.bit_count() % 2 == 1 for value in boundary)
    assert len({boundary[a] ^ boundary[b]
                for a, b in itertools.combinations(range(64), 2)}) == comb(64, 2)
    fibers = {}
    relation_vectors = []
    zero_words = set()
    for a, b, c in itertools.combinations(range(64), 3):
        actual = boundary[a] ^ boundary[b] ^ boundary[c]
        formal = (1 << a) | (1 << b) | (1 << c)
        if actual in fibers:
            for previous in fibers[actual]:
                relation = formal ^ previous
                assert relation.bit_count() == 6
                zero_words.add(relation)
            relation_vectors.append(formal ^ fibers[actual][0])
            fibers[actual].append(formal)
        else:
            fibers[actual] = [formal]
    rho6 = rank(relation_vectors)
    assert rho6 == 28
    assert len(zero_words) == 84
    return {"orientation": "M^T", "triples": comb(64, 3),
            "weight_six_relations": len(zero_words), "rank": rho6,
            "zero_missing_zero_helper_edges_implies_y_at_least": 32-rho6}


if __name__ == "__main__":
    report = {"scalar_reduction": parameter_check(),
              "boundary_rank": rank6_check()}
    Path(__file__).with_name("CHECK73.json").write_text(
        json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
