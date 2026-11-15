"""Exact level-1 cover test for l - dim U <= 2 (cover lemma, as track C's cover_enum.py, own
implementation): can l products of x-forms (rank-2 alternating forms on F_2^8) span a space
containing U?  Their span P has dim <= l and P contains U, so the images of the chosen forms in
Lambda^2 / U span <= s = l - dim U dimensions; conversely if the forms whose image lies in an
s-dim space S span a space containing U, a subset of size <= dim U + s = l does.  [P]

cover(U_wedges, l) -> list of l (a, b) operand pairs (bit masks over the 8 x bits) or None.
"""
from __future__ import annotations

import itertools

import cover1

PAIRS = list(itertools.combinations(range(8), 2))
WI = {p: i for i, p in enumerate(PAIRS)}


def wedge(l, m):
    v = 0
    for i, (a, b) in enumerate(PAIRS):
        if ((l >> a) & (m >> b) & 1) ^ ((l >> b) & (m >> a) & 1): v |= 1 << i
    return v


def all_rank2():
    seen = {}
    for l in range(1, 256):
        for m in range(l + 1, 256):
            w = wedge(l, m)
            if w and w not in seen: seen[w] = (l, m)
    return seen


R2 = None


FREE = {}


def pick(vecs_with_ops, Urows, need):
    """greedy: choose forms from the list that are independent mod the free space, return ops
    if their span + free contains U (need = U basis)"""
    rows = dict(FREE); chosen = []
    for w, ops in vecs_with_ops:
        v = cover1.reduce(w, rows)
        if v:
            rows[v.bit_length() - 1] = v; chosen.append(ops)
    span = rows
    if all(cover1.reduce(u, span) == 0 for u in need):
        return chosen
    return None


def cover(U, l, free=()):
    """products P (l of them) with span(P) + span(free) >= U.  Exact for l - dim(U mod free) <= 2:
    the lemma is applied in Lambda^2 / span(free)."""
    global R2
    if R2 is None: R2 = all_rank2()
    global FREE
    Frows = cover1.rowspace(list(free))
    FREE = dict(Frows)
    U = [cover1.reduce(u, Frows) for u in U]
    Urows = cover1.rowspace([u for u in U if u])
    d = len(Urows); s = l - d
    if s < 0: return None
    Ub = list(Urows.values())
    img = {}
    UF = cover1.rowspace(list(Urows.values()) + list(Frows.values()))
    for w, ops in R2.items():
        w = cover1.reduce(w, Frows)
        if not w: continue
        r = cover1.reduce(w, UF)
        img.setdefault(r, []).append((w, ops))
    inside = img.get(0, [])
    if s >= 0:
        c = pick(inside, Urows, Ub)
        if c is not None and len(c) <= l: return c
    if s >= 1:
        for v, lst in img.items():
            if v == 0: continue
            c = pick(inside + lst, Urows, Ub)
            if c is not None and len(c) <= l: return c
    if s >= 2:
        keys = [v for v in img if v]
        # planes {0, v1, v2, v1^v2}
        done = set()
        for i, v1 in enumerate(keys):
            for v2 in keys[i + 1:]:
                v3 = v1 ^ v2
                key = frozenset((v1, v2, v3))
                if key in done: continue
                done.add(key)
                lst = inside + img[v1] + img[v2] + img.get(v3, [])
                if len(lst) < d: continue
                c = pick(lst, Urows, Ub)
                if c is not None and len(c) <= l: return c
    if s > 2: raise ValueError('s > 2 not supported')
    return None
