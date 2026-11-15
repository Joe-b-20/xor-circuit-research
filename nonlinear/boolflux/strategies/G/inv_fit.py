"""Fit the middle (GF(16)) stage to a given stage 1 + last layer (track G).

Given level-1 products L1 (from --l1 FILE) and a last layer LL (from --layer FILE), everything the
middle stage contributes is a function of N.  Let V0 = functions of N (16-dim), Wx = span(1, x, L1,
LL).  The outputs need T in Wx + span(middle products); so the middle stage must provide the
V0-components r_i of the outputs (mod Wx & V0) and the coordinates of n = N^-1 (LL operands),
the latter mod span(1, x, L1) & V0.  This is a 4-bit problem on the 16 values of N.

usage: python3 inv_fit.py --l1 FILE --layer FILE --k K [--prob OUT.prob] [--sat]
  prints dimensions; writes an nlb problem (4 inputs = N coordinates, K products, two groups);
  --sat: exact SAT (CHM encoding extended with addends) for K products
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent / 'C'))
import gf                                           # noqa: E402
from nlbprob import Span, Problem                   # noqa: E402
from aes_prob import load_circuit, sbox_tables, n_coords   # noqa: E402
from ll_prob import ninv_coords                     # noqa: E402
from lns_sat import layer_products                  # noqa: E402

ONES = (1 << 256) - 1


def nvals():
    return [gf.power(p, 17) for p in range(256)]


def v0_basis():
    N = nvals()
    vals = sorted(set(N))
    out = []
    for v in vals:
        t = 0
        for p in range(256):
            if N[p] == v: t |= 1 << p
        out.append((v, t))
    return out


def coord_index():
    """N value -> 4-bit input index (coordinates w.r.t. the basis used by n_coords)"""
    sp = gf.Span(); basis = []
    for v in gf.SUB16:
        if v and sp.add(v): basis.append(v)
    idx = gf.coords_in_basis(basis)
    return idx, basis


def to16(t, idx):
    """256-point function of N -> 16-point table over the 4-bit coordinate input (msb = coord 0)"""
    N = nvals()
    out = 0
    for p in range(256):
        c = idx[N[p]]
        # input integer: coordinate i -> bit 3-i (input i = bit n-1-i, core.py convention)
        xin = sum(((c >> i) & 1) << (3 - i) for i in range(4))
        if (t >> p) & 1: out |= 1 << xin
    return out


def intersect_v0(W):
    """basis of span(W) & V0 (as 256-bit tables)"""
    V0 = [t for _, t in v0_basis()]
    S = Span()
    nw = 0
    for t in W:
        if S.add(t, 0): nw += 1
    inter = []
    S2 = Span()
    for j, t in enumerate(V0): S2.add(t, 1 << j)
    # vectors of V0 that lie in span W: solve via combined elimination with tags on V0 part
    C = Span()
    for t in W: C.add(t, 0)
    res = []
    for j, t in enumerate(V0):
        v, tag = C.reduce(t, 1 << j)
        if v == 0: res.append(t)
        else: C.rows[v.bit_length() - 1] = (v, tag)
    # also combinations: track reductions to zero with tags
    C = Span()
    for t in W: C.add(t, 0)
    zero = []
    for j, t in enumerate(V0):
        v, tag = C.reduce(t, 1 << j)
        if v == 0: zero.append(tag)
        else: C.rows[v.bit_length() - 1] = (v, tag)
    out = []
    for tag in zero:
        f = 0
        for j in range(16):
            if (tag >> j) & 1: f ^= V0[j]
        out.append(f)
    return out


def components(T, W):
    """V0-components of T modulo W (T must lie in W + V0)"""
    V0 = [t for _, t in v0_basis()]
    S = Span()
    for t in W: S.add(t, 0)
    for j, t in enumerate(V0): S.add(t, 1 << j)
    out = []
    for t in T:
        tag = S.express(t)
        if tag is None: return None
        f = 0
        for j in range(16):
            if (tag >> j) & 1: f ^= V0[j]
        out.append(f)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--l1', required=True); ap.add_argument('--layer', required=True)
    ap.add_argument('--k', type=int, default=5); ap.add_argument('--prob', default=None)
    a = ap.parse_args()
    _, lev, ands = load_circuit(a.l1)
    L1 = [A['tab'] for A in ands if A['level'] == 1]
    LL = [x & y for x, y in layer_products(a.layer)]
    T = sbox_tables()
    base1 = [ONES] + list(gf.X) + L1
    Wx = base1 + LL
    r = components(T, Wx)
    info = {'l1': Path(a.l1).name, 'layer': Path(a.layer).name, 'nL1': len(L1), 'nLL': len(LL)}
    if r is None:
        info['result'] = 'T not in Wx + V0: no middle stage can complete'
        print(json.dumps(info)); return
    A_res = intersect_v0(Wx)
    A_n = intersect_v0(base1)
    idx, basis = coord_index()
    r16 = [to16(t, idx) for t in r]
    n16 = [to16(t, idx) for t in ninv_coords()]
    Ar16 = [to16(t, idx) for t in A_res]
    An16 = [to16(t, idx) for t in A_n]
    # dimension of what the middle must add beyond the addends (and beyond affine in N)
    S = Span()
    for t in [0xFFFF] + [to16(c, idx) for c in n_coords()] + Ar16: S.add(t, 0)
    need_r = sum(1 for t in r16 if S.add(t, 0))
    S2 = Span()
    for t in [0xFFFF] + [to16(c, idx) for c in n_coords()] + An16: S2.add(t, 0)
    need_n = sum(1 for t in n16 if S2.add(t, 0))
    info.update({'dim_Wx_cap_V0': len(A_res), 'dim_L1_cap_V0': len(A_n),
                 'residue_dims_beyond_affine': need_r, 'n_dims_beyond_affine': need_n})
    print(json.dumps(info))
    if a.prob:
        P = Problem(4)
        for _ in range(a.k): P.add_slot()
        P.add_group(n16, An16)
        P.add_group(r16, Ar16)
        P.write(a.prob)
        print(json.dumps({'prob': a.prob, 'K': a.k}))


if __name__ == '__main__':
    main()
