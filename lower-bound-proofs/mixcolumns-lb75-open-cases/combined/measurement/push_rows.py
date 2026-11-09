#!/usr/bin/env python3
"""Transcription of the push5 + push6 rows (model_full_cuts.py of both pushes) as a function of an ARBITRARY helper-type
list, so that the rows can be evaluated on real circuits whose phases contain types outside the package list
(raw circuits may have helpers of odd-graph degree 2).  The transcription is checked against the archive generator
(lb76/push6_copy, which imports the package certify75.py) on every key it is asked about: see selfcheck().

Read-only: nothing outside recon/ is written (sys.dont_write_bytecode).
"""
import sys
sys.dont_write_bytecode = True
import importlib.util
from fractions import Fraction
from math import gcd, comb
from pathlib import Path

G = 75
EXCEPTIONAL_Q_MAX = 6
PUSH6_COPY = Path.home() / 'xs-campaigns/2026-11-07-sprint/lb76/push6_copy'
PKG = Path.home() / 'xs-campaigns/2026-11-07-sprint/lb76/pkg_copy/source/lower_bounds/checks'


def load_archive_model():
    """the archive's push6 generator (which loads push5's, which loads the package certify75 copy)."""
    spec = importlib.util.spec_from_file_location('push6_model_full_cuts', PUSH6_COPY / 'push6/global_chronology/model_full_cuts.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def push5_rows(key, types, G=G, f1free=False):
    """push5/global_chronology/model_full_cuts.py, rows appended after the package rows: [(name, coef, bound)].
    G is the gate count (the archive model hard-codes 75; a real circuit must be evaluated with its own G).
    f1free=True keeps only the rows whose proofs rest on package lemmas and on finite facts recomputed here
    (finite_facts_recon.py): P5.1-P5.4; the exceptional-label rows (F1-F3 of the archive) are dropped."""
    h, y, F, ori, q, z = key
    out = []
    out.append(('new HH degree realizability <=', [int(v > z) for r, u, v in types], 0))
    x = G - 32 - h - y
    classes = 5 if ori == 'M' else 7
    cap = min(2 * classes, (x + 4 * classes) // 5)
    out.append(('new full helper chronological cap <=', [int(r == 3) for r, u, v in types], cap))
    out.append(('new full helper distinct represented labels <=', [int(r == 3) for r, u, v in types], (G - 32 - h - q) // 3))
    out.append(('new repeated helper joint birth ownership <=', [int(r == 2) + 5 * int(r == 3) for r, u, v in types], x + 4 * classes))
    if f1free: return out
    if ori == 'Mt':
        out.append(('new transpose full missing unanchored coupling <=', [(u if r == 3 else 0) - int(r == 0) for r, u, v in types], q - 1))
        out.append(('new transpose weighted excess unanchored coupling <=',
                    [max(0, r - 1) * u + (max(0, u - 2) if r == 3 else 0) - 3 * int(r == 0) for r, u, v in types], 3 * (q - 1)))
    if ori == 'Mt' and z == 0:
        exc = 2 if q <= EXCEPTIONAL_Q_MAX else 1
        out.append(('new transpose full missing exceptional colors <=', [u if r == 3 else 0 for r, u, v in types], q - exc))
        out.append(('new transpose weighted excess exceptional colors <=',
                    [max(0, r - 1) * u + (max(0, u - 2) if r == 3 else 0) for r, u, v in types], 3 * (q - exc)))
    return out


def overload_breakpoints(q):
    largest = max(4, q + 2)
    return tuple(sorted({Fraction(a, d) for d in range(1, largest + 1) for a in range(1, d + 1)}))


def push6_rows(key, types, dedup=True, G=G, f1free=False):
    """push6/global_chronology/model_full_cuts.py, the rows it appends after push5's: [(name, coef, bound)].
    dedup=True reproduces the generator (gcd-normalisation, identical coefficient vectors keep the smallest bound);
    dedup=False keeps every (resource, budget) product and every divisor row separately (for per-family reporting).
    f1free=True: q_eff = q and only the trivial budget p <= q (the Mt budgets B2-B6 and the exceptional-label constants,
    which rest on the archive's finite facts F1-F3, F5, are dropped); resources R1-R6 and the divisor rows are kept."""
    h, y, F_T, orientation, q, z = key
    C = 20 if orientation == 'M' else 28
    t = C // 4
    x = G - 32 - h - y
    q_eff = q
    if not f1free:
        if orientation == 'Mt' and z <= 2: q_eff = q - 1
        if orientation == 'Mt' and z == 0 and q <= EXCEPTIONAL_Q_MAX: q_eff = q - 2
    new = {}; flat = []
    def add(name, row, bound):
        common = gcd(abs(bound), *(abs(c) for c in row))
        if common > 1:
            row = [c // common for c in row]; bound //= common
        if not any(row) and bound >= 0: return
        signature = tuple(row)
        flat.append(('push6 ' + name + ' <=', list(row), bound))
        if signature not in new or bound < new[signature][0]:
            new[signature] = (bound, 'push6 ' + name + ' <=')
    def vector(fn): return [fn(r, u, v) for r, u, v in types]
    U = vector(lambda r, u, v: u if r >= 2 else 0)
    Erep = vector(lambda r, u, v: max(0, r - 1))
    Cost = vector(lambda r, u, v: int(r == 2) + 5 * int(r == 3))
    A = vector(lambda r, u, v: u if r == 3 else 0)
    Q = vector(lambda r, u, v: max(0, r - 1) * u + (max(0, u - 2) if r == 3 else 0))
    budgets = [('fixed repeated-color capacity', 1, [0] * len(types), q_eff)]
    if orientation == 'Mt' and not f1free:
        h0 = vector(lambda r, u, v: int(r == 0))
        h00 = vector(lambda r, u, v: int(r == 0 and u == 0))
        V0_minus_h00 = vector(lambda r, u, v: v - int(u == 0) if r == 0 else 0)
        D2 = vector(lambda r, u, v: (2 * v - 2 if u == 0 else v + min(v, q - u)) if r == 0 else 0)
        budgets += [('unanchored helper capacity', 1, h0, q - 1),
                    ('HH unanchored incidence deficiency', 3, V0_minus_h00, 3 * (q - 1)),
                    ('HH edge deficiency', 3, [-c for c in h00], 3 * (q - 1) + z),
                    ('HH label matching deficiency', 6, D2, 6 * (q - 1))]
        if q <= 6 or y <= 3:
            twice_h0_plus_W = vector(lambda r, u, v: 2 * int(r == 0) + (v if r in (1, 2) else 0))
            budgets.append(('small palette anchored full HH', 1, twice_h0_plus_W, q - 2))
    resources = [('repeated contact core ownership', [a + b for a, b in zip(Erep, U)], C, 1),
                 ('repeated contact OO three halves', [2 * a + 3 * b for a, b in zip(Cost, U)], 2 * x + 2 * C, 3),
                 ('repeated contact OO full colors', [a + 2 * b + c for a, b, c in zip(Cost, U, A)], x + C, 3)]
    if orientation == 'Mt':
        resources += [('full contacts', A, 0, 1), ('weighted excess', Q, 0, 3)]
    for ratio in overload_breakpoints(q):
        a, d = ratio.numerator, ratio.denominator
        coeff = vector(lambda r, u, v, a=a, d=d: (a * (r - 1 + u)) // d if r >= 2 else 0)
        resources.append(('class overload ratio ' + str(a) + '/' + str(d), coeff, t * ((4 * a) // d), 1))
    for resource, K, base, c in resources:
        for budget, s, g, b in budgets:
            add(resource + ' / ' + budget, [s * k - c * gg for k, gg in zip(K, g)], s * base + c * b)
    for d in range(2, q + 3):
        cap = min((t * ((4 * k + q_eff) // d)) // k for k in range(1, t + 1))
        coeff = vector(lambda r, u, v, d=d: (r - 1 + u) // d if r >= 2 else 0)
        add('rounded class core divisor ' + str(d), coeff, cap)
    if not dedup: return flat
    return [(name, list(sig), bound) for sig, (bound, name) in new.items()]


def push_rows(key, types, dedup=True, G=G, f1free=False):
    return push5_rows(key, types, G, f1free) + push6_rows(key, types, dedup, G, f1free)


def package_types(key):
    h, y, F, ori, q, z = key
    return [(r, u, v) for r in range(4) for u in range(q + 1) for v in range(min(2 * z, max(0, h - 1)) + 1) if r + u + v >= 3]


def selfcheck(keys, model=None):
    """my rows == the archive generator's appended rows, row by row (names, coefficients, bounds), on the package types."""
    sys.path.insert(0, str(PKG))
    import certify75
    model = model or load_archive_model()
    n = 0
    for key in keys:
        types, rows, bounds, names = model.system(key)
        t0, A0, B0, N0 = certify75.system(key)
        assert types == t0 == package_types(key), key
        assert rows[:len(A0)] == A0 and bounds[:len(B0)] == B0 and names[:len(N0)] == N0, ('package prefix differs', key)
        mine = push_rows(key, types)
        theirs = list(zip(names[len(N0):], rows[len(A0):], bounds[len(B0):]))
        assert len(mine) == len(theirs), (key, len(mine), len(theirs))
        for (na, ca, ba), (nb, cb, bb) in zip(mine, theirs):
            assert na == nb and ca == cb and ba == bb, (key, na, nb, ba, bb)
        n += len(mine)
    return n


if __name__ == '__main__':
    import itertools, random
    keys = []
    rng = random.Random(1)
    for ori in ('M', 'Mt'):
        for q in range(0, 11):
            for z in range(0, 9):
                for h, y, F in [(12, 5, 1), (14, 4, 3), (16, 3, 4), (10, 7, 2), (18, 0, 5), (13, 2, 2), (9, 6, 0)]:
                    keys.append((h, y, F, ori, q, z))
    n = selfcheck(keys)
    print(f'selfcheck PASSED on {len(keys)} keys, {n} appended rows identical to the archive generator (lb76/push6_copy)')
    # row inventory for two typical keys
    for key in [(14, 4, 3, 'M', 4, 0), (16, 3, 4, 'Mt', 2, 1), (15, 2, 2, 'Mt', 4, 0)]:
        rows = push_rows(key, package_types(key))
        print(key, 'push rows', len(rows), 'push5', len(push5_rows(key, package_types(key))), 'push6 (dedup)', len(push6_rows(key, package_types(key))),
              'push6 (all products)', len(push6_rows(key, package_types(key), dedup=False)))
