#!/usr/bin/env python3
"""Independent complete R8/R10 check for the transpose boundary.

Uses only this audit's polynomial-arithmetic matrix builder, then computes
a fresh inverse and enumerates both codeword halves of weight at most five.
Every total-weight-at-most-ten word has such a half, proving completeness.
"""
from collections import Counter
from itertools import combinations
from pathlib import Path
import json
from check73_drift import boundaries, rank


def apply(columns, v):
    out = 0
    while v:
        b = v & -v
        out ^= columns[b.bit_length()-1]
        v ^= b
    return out


def inverse(columns):
    basis = {}
    for i, vector in enumerate(columns):
        source = 1 << i
        while vector:
            pivot = vector.bit_length()-1
            if pivot not in basis:
                basis[pivot] = vector, source
                break
            row, record = basis[pivot]
            vector ^= row
            source ^= record
        assert vector
    result = []
    for i in range(32):
        vector, source = 1 << i, 0
        while vector:
            row, record = basis[vector.bit_length()-1]
            vector ^= row
            source ^= record
        result.append(source)
    assert all(apply(columns, v) == 1 << i for i, v in enumerate(result))
    return result


def main():
    B = boundaries()['Mt']
    columns = B[32:]
    inv = inverse(columns)
    words = set()
    for size in range(1, 6):
        for indices in combinations(range(32), size):
            small = sum(1 << i for i in indices)
            out = 0
            back = 0
            for i in indices:
                out ^= columns[i]
                back ^= inv[i]
            if size+out.bit_count() <= 10:
                words.add(out | (small << 32))
            if size+back.bit_count() <= 10:
                words.add(small | (back << 32))
    assert all(apply(B, w) == 0 for w in words)
    counts = dict(sorted(Counter(w.bit_count() for w in words).items()))
    ranks = {weight: rank(w for w in words if w.bit_count() <= weight)
             for weight in (6,8,10)}
    assert counts == {6:84, 8:276, 10:1300}
    assert ranks == {6:28, 8:29, 10:29}
    result = dict(orientation='Mt', complete_through_weight=10,
                  dependency_word_counts=counts, ranks=ranks,
                  all_checks_passed=True)
    Path(__file__).with_name('SHORT_BOUNDARY_VERIFIED.json').write_text(
        json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
