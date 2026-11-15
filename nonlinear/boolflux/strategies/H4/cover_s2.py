"""Exact cover test for s = l - dim U = 2 with bucket-size pruning [P]:
forms with images in a plane S = {0, v1, v2, v1+v2} contribute at most
(|B1| - 1) + (|B2| - 1) + (|B3| - 1) + 1 dimensions to U beyond the r0 of the forms inside U
(differences within a bucket and one cross combination), so a plane can only work if
r0 + |B1| + |B2| + |B3| - 2 >= dim U.
usage: cover_s2.cover2(U, free) -> ops or None (l = dim U + 2)"""
import itertools
VERBOSE = False

import cover1
import cover_exact as CE


def cover2(U, free=()):
    if CE.R2 is None: CE.R2 = CE.all_rank2()
    Frows = cover1.rowspace(list(free)); CE.FREE = dict(Frows)
    Ur = cover1.rowspace([cover1.reduce(u, Frows) for u in U if cover1.reduce(u, Frows)])
    d = len(Ur); Ub = list(Ur.values())
    UF = cover1.rowspace(list(Ur.values()) + list(Frows.values()))
    img = {}
    for w, ops in CE.R2.items():
        w = cover1.reduce(w, Frows)
        if not w: continue
        img.setdefault(cover1.reduce(w, UF), []).append((w, ops))
    inside = img.pop(0, [])
    r0 = len(cover1.rowspace([w for w, _ in inside]))
    need = d - r0
    sizes = {v: len(l) for v, l in img.items()}
    big = [v for v in img if sizes[v] >= 1]
    hist = {}
    for v in img: hist[sizes[v]] = hist.get(sizes[v], 0) + 1
    if VERBOSE: print('d', d, 'r0', r0, 'buckets', len(img), 'size hist', dict(sorted(hist.items())), flush=True)
    # plane needs |B1|+|B2|+|B3| >= need + 2
    keys = sorted(img, key=lambda v: -sizes[v])
    smax = sizes[keys[0]] if keys else 0
    tested = 0
    for i, v1 in enumerate(keys):
        if sizes[v1] * 3 < need + 2: break
        for v2 in keys[i + 1:]:
            if sizes[v1] + 2 * sizes[v2] < need + 2 and sizes[v1] + sizes[v2] + smax < need + 2: break
            v3 = v1 ^ v2
            tot = sizes[v1] + sizes[v2] + sizes.get(v3, 0)
            if tot < need + 2: continue
            if v3 in sizes and sizes[v3] > sizes[v1]: continue   # plane seen with v3 first
            tested += 1
            c = CE.pick(inside + img[v1] + img[v2] + img.get(v3, []), Ur, Ub)
            if c is not None and len(c) <= d + 2: return c, tested
    return None, tested
