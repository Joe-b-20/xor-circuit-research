"""Exhaustive test of a subspace cover by rank-2 alternating forms on F_2^8.

Fact [P]: if U (dim d) lies in span(P_1..P_l) with P_i rank-2, then the images of the P_i in
Lambda^2 / U span a space of dim <= l - d (dim span P = dim(span P mod U) + dim(U & span P)).
So all l forms lie in the preimage of an (l-d)-dim subspace Y of the quotient that is spanned by
images of rank-2 forms. We bucket all 10795 rank-2 forms by their image mod U and, for
e = l - d <= 2, enumerate Y exactly; a Y works iff the rank-2 forms in its preimage span a space
containing U of dim <= l.

usage: python3 cover_enum.py --l 9 --a28-junk | --forms FILE
"""
from __future__ import annotations

import argparse
import itertools
import json
import time

import gf
import qmc

PAIRS = list(itertools.combinations(range(8), 2))


_R2 = None


def rank2_forms():
    global _R2
    if _R2 is not None: return _R2
    vecs = list(range(1, 256))
    seen = set(); out = []
    for a in vecs:
        for b in vecs:
            if b <= a: continue
            la = [(a >> (7 - i)) & 1 for i in range(8)]; lb = [(b >> (7 - i)) & 1 for i in range(8)]
            w = 0
            for k, (i, j) in enumerate(PAIRS):
                if (la[i] & lb[j]) ^ (la[j] & lb[i]): w |= 1 << k
            if w not in seen:
                seen.add(w); out.append(w)
    _R2 = out
    return out


def run(U, l):
    d = gf.Span(U).dim()
    e = l - d
    R = rank2_forms()
    assert len(R) == 10795
    Nu = qmc.Normal(U)
    buckets = {}
    for w in R:
        buckets.setdefault(Nu.nf(w), []).append(w)
    c0 = len(buckets.get(0, []))
    sizes = sorted((len(v) for k, v in buckets.items() if k), reverse=True)
    info = {'d': d, 'l': l, 'e': e, 'in_U': c0, 'points': len(buckets) - (1 if c0 else 0),
            'max_bucket': sizes[:8]}
    found = []

    # U-coordinates (d bits) of elements of U, for a fast exact plane test:
    # span(preimage forms) & U = span(forms in U, within-bucket differences, one triple sum)
    # and dim span(preimage) = dim(that) + dim(image span); so the plane works iff that span = U.
    Ub = []
    spU = gf.Span()
    for u in U:
        if spU.add(u, 1 << len(Ub)): Ub.append(u)

    def ucoord(v):
        r, t = spU.reduce(v, 0)
        assert r == 0
        return t

    inner = {}

    def bucket_inner(y):
        if y not in inner:
            fs = buckets[y]
            inner[y] = [ucoord(f ^ fs[0]) for f in fs[1:]]
        return inner[y]

    base0 = [ucoord(f) for f in buckets.get(0, [])]

    def rank_small(vs):
        piv = {}
        for v in vs:
            while v:
                h = v.bit_length() - 1
                if h not in piv: piv[h] = v; break
                v ^= piv[h]
        return len(piv)

    def test(Y):
        ys = [y for y in Y if y]
        vs = list(base0)
        for y in ys: vs += bucket_inner(y)
        if len(ys) == 3:
            vs.append(ucoord(buckets[ys[0]][0] ^ buckets[ys[1]][0] ^ buckets[ys[2]][0]))
        if rank_small(vs) == d and d + len(ys) - (1 if len(ys) == 3 else 0) <= l:
            forms = []
            for y in Y: forms += buckets.get(y, [])
            S = gf.Span(forms)
            assert all(S.contains(u) for u in U)
            return S.dim(), forms
        return None

    if e < 0:
        info['result'] = 'impossible (l < d)'
        return info, found
    if e == 0:
        r = test([0])
        if r: found.append([0])
    pts = [k for k in buckets if k]
    if e >= 1:
        for y in pts:
            if c0 + len(buckets[y]) < l: continue      # need l forms in the preimage
            r = test([0, y])
            if r: found.append([y])
    if e >= 2:
        # complete enumeration of planes {y1, y2, y1^y2}: the point of the plane with most forms
        # has >= ceil(need/3) of them (need = l - c0), take it as y1; y2 ranges over all points
        # with enough forms that the plane can still reach `need`.
        need = l - c0
        size = {y: len(buckets[y]) for y in pts}
        mx = max(size.values(), default=0)
        y1s = [y for y in pts if 3 * size[y] >= need]
        info['y1_candidates'] = len(y1s)
        work = 0
        bymin = {}
        for y1 in y1s:
            s1 = size[y1]
            lo = max(1, -(-(need - s1) // 2))      # y2 = larger of the other two points
            if lo not in bymin:
                bymin[lo] = [y for y in pts if size[y] >= lo]
            for y2 in bymin[lo]:
                s2 = size[y2]
                if s2 < lo or y2 == y1 or s2 > s1: continue
                y3 = y1 ^ y2
                s3 = size.get(y3, 0)
                if s3 == 0 or s3 > s2 or s1 + s2 + s3 < need: continue
                work += 1
                r = test([0, y1, y2, y3])
                if r: found.append([y1, y2, y3]); break
            if found: break
        info['plane_tests'] = work
    if e >= 3:
        info['note'] = 'e >= 3 not enumerated'
    info['found'] = len(found)
    return info, found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--l', type=int, default=9)
    ap.add_argument('--a28-junk', action='store_true')
    ap.add_argument('--forms', default=None)
    a = ap.parse_args()
    if a.a28_junk:
        import cover
        U = cover.a28_junk_space()
    else:
        U = json.load(open(a.forms))
    t0 = time.time()
    info, found = run(U, a.l)
    info['secs'] = round(time.time() - t0, 1)
    print(json.dumps(info))


if __name__ == '__main__':
    main()
