"""Output decomposition and last-layer operand anatomy (agent H1).

For a circuit whose ANDs are linearly independent (dim span(1, x, ANDs) = 9 + K), each output has
a unique expression  y_j = sum_k c_jk a_k + affine(x).  Group the ANDs by role (xag.role: S1 =
operands affine in x, MID = operands functions of N, LAST = operands in span(1, x, N, n), other)
and measure:
  * Jx  = dim(V_N + span{S1-part of y_j}) - 4      (x-quadratic junk the outputs take from stage 1)
  * U   = V_N + S1-parts, dim U = 4 + Jx; slack = l - dim U
  * J0  = dim(span(1, N, n) + span{MID-part of y_j}) - 9  (N-function junk beyond n and N)
  * each S1 product: needed for N (not removable from a minimal N cover)? used by outputs? by
    MID operands? by LAST operands?
  * each LAST operand split as  c + Tr(A x) + Tr_K(t N) + Tr_K(s n)  (A in F, t, s in K)
    and the pair type (x|n, x+n|x+n, ...); GF(4)-norm test A'/A in {w, w^2}.
usage: python3 decomp.py FILE [FILE ...]
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import xag                                      # noqa: E402
from xag import gf, ONES, AFFX, NC, nC, deps, span, LOG   # noqa: E402

# trace forms
TR = [0] * 256
for p in range(256):
    t = 0
    for i in range(8): t ^= gf.power(p, 1 << i)
    TR[p] = t & 1
TRX = {}                                         # table of Tr(A x) -> A
for A in range(256):
    TRX[xag.tab_of(lambda p, A=A: TR[gf.mul(A, p)])] = A
K = [v for v in gf.SUB16]
TRK = [0] * 256                                  # Tr_K(v) = v + v^2 + v^4 + v^8 for v in K
for v in K:
    t = 0
    for i in range(4): t ^= gf.power(v, 1 << i)
    TRK[v] = t & 1
Nv = xag.Nv; nv = xag.nv
TRN = {}; TRn = {}
for s in K:
    TRN[xag.tab_of(lambda p, s=s: TRK[gf.mul(s, Nv[p])])] = s
    TRn[xag.tab_of(lambda p, s=s: TRK[gf.mul(s, nv[p])])] = s
w = gf.power(3, 85)


def name(v):
    return '0' if v == 0 else 'g%d' % LOG[v]


def split_operand(t):
    """t = c + Tr(Ax) + Tr_K(tN) + Tr_K(s n) ?  -> (c, A, tN, s) or None"""
    cand = [(ONES, ('c', 0))] + [(AFFX[1 + i], ('x', i)) for i in range(8)] + \
           [(NC[i], ('N', i)) for i in range(8)] + [(nC[i], ('n', i)) for i in range(8)]
    S = gf.Span(); basis = []
    for tb, lab in cand:
        if S.add(tb, 1 << len(basis)): basis.append((tb, lab))
    r, tag = S.reduce(t)
    if r: return None
    parts = {'c': 0, 'x': 0, 'N': 0, 'n': 0}
    for k, (tb, (kind, i)) in enumerate(basis):
        if (tag >> k) & 1: parts[kind] ^= tb
    A = TRX.get(parts['x']); tN = TRN.get(parts['N']); s = TRn.get(parts['n'])
    c = 1 if (tag & 1) else 0
    return c, A, tN, s


def kind(sp):
    c, A, tN, s = sp
    k = ''.join(ch for ch, v in (('x', A), ('N', tN), ('n', s)) if v)
    return k or 'const'


def analyse(path):
    c, ands, outs, otabs = xag.parse(path)
    Kn = len(ands)
    roles = [xag.role(A) for A in ands]
    P = span(AFFX, [A['tab'] for A in ands])
    res = {'file': Path(path).name, 'K': Kn, 'independent': P.dim() == 9 + Kn}
    idx = {r: [k for k in range(Kn) if roles[k] == r] for r in set(roles)}
    res['counts'] = {r: len(v) for r, v in idx.items()}

    def part(o, r):
        t = 0
        for k in deps(o):
            if roles[k] == r: t ^= ands[k]['tab']
        return t
    s1parts = [part(o, 'S1') for o in outs]
    midparts = [part(o, 'MID') for o in outs]
    lastparts = [part(o, 'LAST') ^ part(o, 'LASTV0') ^ part(o, 'OTHER') for o in outs]
    U = span(AFFX, NC, s1parts)
    res['Jx'] = U.dim() - 13
    res['dimU'] = U.dim() - 9
    res['l'] = len(idx.get('S1', []))
    res['rank_S1parts'] = span(AFFX, s1parts).dim() - 9
    res['V_N_in_S1parts'] = xag.cap_dim(span(AFFX, s1parts), span(AFFX, NC)) - 9
    res['J0'] = span([ONES], NC, nC, midparts).dim() - 9
    res['rank_midparts'] = span([ONES], midparts).dim() - 1
    res['rank_lastparts'] = span(lastparts).dim()
    # S1 product roles
    s1 = idx.get('S1', [])
    need_for_N = []
    for k in s1:
        S = span(AFFX, [ands[j]['tab'] for j in s1 if j != k])
        need_for_N.append(not all(S.contains(t) for t in NC))
    # least subset spanning V_N
    least = None
    for r in range(4, len(s1) + 1):
        for sub in itertools.combinations(s1, r):
            S = span(AFFX, [ands[j]['tab'] for j in sub])
            if all(S.contains(t) for t in NC): least = r; break
        if least: break
    res['least_N_cover'] = least
    # least subset spanning U
    leastU = None
    for r in range(res['dimU'], len(s1) + 1):
        ok = False
        for sub in itertools.combinations(s1, r):
            S = span(AFFX, [ands[j]['tab'] for j in sub])
            if all(S.contains(t) for t in NC + s1parts): ok = True; break
        if ok: leastU = r; break
    res['least_U_cover_within_file'] = leastU
    s1info = []
    for i, k in enumerate(s1):
        users = [j for j in range(Kn) if k in deps(ands[j]['L']) or k in deps(ands[j]['R'])]
        s1info.append({'and': k + 1, 'needN': need_for_N[i],
                       'out': sum(1 for o in outs if k in deps(o)),
                       'mid_users': sum(1 for j in users if roles[j] == 'MID'),
                       'last_users': sum(1 for j in users if roles[j] != 'MID' and roles[j] != 'S1')})
    res['s1'] = s1info
    # last-layer anatomy
    pairs = []
    for k in range(Kn):
        if roles[k] in ('S1', 'MID'): continue
        A = ands[k]
        L = split_operand(A['Lt']); R = split_operand(A['Rt'])
        if L is None or R is None:
            pairs.append({'and': k + 1, 'type': 'outside XNn'}); continue
        kl, kr = kind(L), kind(R)
        d = {'and': k + 1, 'type': '|'.join(sorted([kl, kr])),
             'L': [L[0], name(L[1] or 0), name(L[2] or 0), name(L[3] or 0)],
             'R': [R[0], name(R[1] or 0), name(R[2] or 0), name(R[3] or 0)]}
        if L[1] and R[1]:
            rat = gf.mul(R[1], gf.INV[L[1]])
            d['A_ratio'] = name(rat)
            d['gf4norm'] = rat in (w, gf.mul(w, w))
        if L[3] and R[3]:
            d['s_ratio'] = name(gf.mul(R[3], gf.INV[L[3]]))
        if L[2] and R[2]:
            d['t_ratio'] = name(gf.mul(R[2], gf.INV[L[2]]))
        if L[3] and L[2]:
            d['gammaL'] = name(gf.mul(L[2], gf.INV[L[3]]))
        if R[3] and R[2]:
            d['gammaR'] = name(gf.mul(R[2], gf.INV[R[3]]))
        pairs.append(d)
    res['last'] = pairs
    tc = {}
    for d in pairs: tc[d['type']] = tc.get(d['type'], 0) + 1
    res['last_types'] = tc
    res['gf4norm_count'] = sum(1 for d in pairs if d.get('gf4norm'))
    # middle: what the MID products span inside V0, beyond span(1, N, n)
    mids = [ands[k]['tab'] for k in idx.get('MID', [])]
    res['mid_extra_in_V0'] = span([ONES], NC, nC, mids).dim() - 9
    # does any last operand use a MID function outside span(N, n)?
    return res


if __name__ == '__main__':
    allres = []
    for f in sys.argv[1:]:
        if f.startswith('--'): break
        r = analyse(f); allres.append(r)
        print('%s K=%d %s l=%d Jx=%d dimU=%d slack=%d leastNcover=%d leastUcover=%s J0=%d '
              'mid_extra=%d gf4norm=%d last=%s' % (
                  r['file'], r['K'], r['counts'], r['l'], r['Jx'], r['dimU'], r['l'] - r['dimU'],
                  r['least_N_cover'], r['least_U_cover_within_file'], r['J0'], r['mid_extra_in_V0'],
                  r['gf4norm_count'], r['last_types']))
    if '--json' in sys.argv:
        Path(sys.argv[sys.argv.index('--json') + 1]).write_text(json.dumps(allres, indent=1))
