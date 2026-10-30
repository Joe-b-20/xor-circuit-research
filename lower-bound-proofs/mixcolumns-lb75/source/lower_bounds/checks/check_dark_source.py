#!/usr/bin/env python3
"""Independently prove completeness of the dark-label audit's word source.

Rebuild every transpose-boundary dependency word of weight <=12 from both
halves of weight <=6, then compare the complete nonzero R10 quotient list
with the inherited source used by the two dark-label implementations.
"""
from collections import Counter
from itertools import combinations
from pathlib import Path
import json
from check73_drift import boundaries
from check_short_boundary import inverse, apply


def insert(vector, basis):
    while vector:
        p = vector & -vector
        if p not in basis:
            basis[p] = vector
            return
        vector ^= basis[p]


def reduce(vector, basis):
    for p in sorted(basis):
        if vector & p:
            vector ^= basis[p]
    return vector


def main():
    B = boundaries()['Mt']
    columns = B[32:]
    inv = inverse(columns)
    words = set()
    for size in range(1,7):
        for indices in combinations(range(32),size):
            mask = sum(1 << i for i in indices)
            a = b = 0
            for i in indices:
                a ^= columns[i]
                b ^= inv[i]
            if size+a.bit_count() <= 12:
                words.add(a | (mask << 32))
            if size+b.bit_count() <= 12:
                words.add(mask | (b << 32))
    assert all(apply(B,w) == 0 for w in words)
    basis = {}
    for w in words:
        if w.bit_count() <= 10:
            insert(w,basis)
    assert len(basis) == 29
    nonzero = {w for w in words if reduce(w,basis)}
    assert len(nonzero) == 736
    assert all(w.bit_count() == 12 for w in nonzero)
    source = Path(__file__).with_name('short_code.json')   # flat layout of lower_bounds/checks (original: ../../research_push/global/)
    inherited = json.loads(source.read_text())
    assert nonzero == set(inherited['new_words'])
    counts = dict(sorted(Counter(w.bit_count() for w in words).items()))
    assert counts == {6:84,8:276,10:1300,12:8112}
    result = dict(orientation='Mt',complete_through_weight=12,
                  word_counts=counts,rank_R10=29,
                  complete_nonzero_quotient_word_count=len(nonzero),
                  inherited_source_exactly_matches=True,
                  all_checks_passed=True)
    Path(__file__).with_name('DARK_SOURCE_VERIFIED.json').write_text(
        json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
