"""Reusable blocks: GF(2)-coordinates of subfield bundles, plugging small SAT circuits in."""
from __future__ import annotations

import json
from pathlib import Path

import chm
from h4lib import Circ, mul, inv, Q, K, F

DATA = Path.home() / 'xs-campaigns' / '2026-11-15-study' / 'H4'


def gf2_basis(field):
    """a GF(2)-basis of the subfield (greedy)"""
    B = []; span = {0}
    for e in sorted(field):
        if e not in span:
            B.append(e); span = span | {s ^ e for s in span}
    return B


def coord_map(B):
    d = {}
    for c in range(1 << len(B)):
        v = 0
        for i in range(len(B)):
            if (c >> i) & 1: v ^= B[i]
        d[v] = c
    return d


def gf2_coords(C, b, B):
    cm = coord_map(B)
    out = [{} for _ in B]
    for w, c in b.items():
        cc = cm[c]
        for i in range(len(B)):
            if (cc >> i) & 1: out[i][w] = 1
    return out


def apply_small(C, circ, ins, Bout):
    """circ from chm.solve; ins: list of GF(2) bundles; returns sum_o out_o * Bout[o]"""
    ands, outs = circ
    n = len(ins)
    ts = []

    def comb(co):
        b = {0: 1} if co[0] else {}
        for j in range(n):
            if co[1 + j]: b = C.add(b, ins[j])
        for r in range(len(ts)):
            if co[1 + n + r]: b = C.add(b, ts[r])
        return b
    for a0, a1 in ands:
        ts.append(C.AND(comb(a0), comb(a1)))
    y = {}
    for o, co in enumerate(outs):
        y = C.add(y, C.scale(comb(co), Bout[o]))
    return y


def small_circuit(key, func, field_in, field_out, k):
    """MC circuit with k ANDs for func: field_in -> field_out (cached in DATA/blocks.json)."""
    Bi, Bo = gf2_basis(field_in), gf2_basis(field_out)
    ci, co = coord_map(Bi), coord_map(Bo)
    n, m = len(Bi), len(Bo)
    table = [0] * (1 << n)
    for a, c in ci.items():
        table[c] = co[func(a)]
    cache = DATA / 'blocks.json'
    db = json.loads(cache.read_text()) if cache.exists() else {}
    ck = '%s|k%d|%s|%s' % (key, k, Bi, Bo)
    if ck in db:
        circ = db[ck]
    else:
        circ, dt, _ = chm.solve(table, n, m, k)
        if circ is None: return None
        db[ck] = circ
        cache.write_text(json.dumps(db))
    for p in range(1 << n):
        assert chm.evaluate(circ, n, p) == table[p]
    return circ, Bi, Bo


def kinv5():
    return small_circuit('kinv', inv, K, K, 5)


def kinv_plug(C, a):
    circ, Bi, Bo = kinv5()
    return apply_small(C, circ, gf2_coords(C, a, Bi), Bo)
