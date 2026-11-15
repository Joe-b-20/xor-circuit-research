"""Assumption-free XAG analysis of an AES S-box circuit (agent H1).

Every AND is written as L * R with L, R affine forms over [1, x0..x7, a1..a_{k-1}] (symbolic) and
as truth tables.  For each AND we report: AND level, algebraic degree of the product and of the
operands, the cyclotomic-coset support of the univariate polynomial of each operand and of the
product (basis-free description w.r.t. the AES field GF(2^8) = GF(2)[t]/0x11B), membership of
the operands in named subfield objects, fan-out, and the three-stage role it would have.

Span measurements per AND level: dims of E_L = span(1, x, ANDs of level <= L), its degree
filtration, how much of the output span and of N, N^-1, x^-1 lies in E_L.

usage: python3 xag.py FILE [--json OUT]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))          # nonlinear/boolflux
sys.path.insert(0, str(HERE.parent / 'C'))        # gf helpers (read-only use)

from core import read_ncff, NONLINEAR_OPS        # noqa: E402
import gf                                         # noqa: E402

ONES = gf.ONES
# ---------------------------------------------------------------- field tables
EXP = [0] * 510
LOG = [0] * 256
v = 1
for i in range(255):
    EXP[i] = v; EXP[i + 255] = v; LOG[v] = i; v = gf.mul(v, 3)

# cyclotomic cosets mod 255
COSETS = []
seen = set()
for e in range(255):
    if e in seen: continue
    cs = []; f = e
    while f not in cs:
        cs.append(f); f = (2 * f) % 255
    seen.update(cs); COSETS.append(min(cs))
COSETS.sort()
WT = {e: bin(e).count('1') for e in range(256)}


def tab_of(fun):
    t = 0
    for p in range(256):
        if fun(p): t |= 1 << p
    return t


def coeff(tab, e):
    """coefficient c_e of the univariate polynomial f(x) = sum_e c_e x^e, 1 <= e <= 254:
    c_e = sum_{x != 0} f(x) x^(255-e)"""
    s = 0
    k = (255 - e) % 255
    for p in range(1, 256):
        if (tab >> p) & 1:
            s ^= EXP[(LOG[p] * k) % 255]
    return s


def coset_support(tab):
    """list of coset leaders e (0 <= e <= 255; 255 means x^255) with c_e != 0"""
    sup = []
    f0 = tab & 1
    d0 = 0
    for p in range(1, 256):
        if (tab >> p) & 1: d0 ^= 1
    if f0: sup.append(0)
    for e in COSETS:
        if e == 0: continue
        if coeff(tab, e): sup.append(e)
    if d0 ^ f0: sup.append(255)
    return sup


def fun_of(tab, key):
    """is tab constant on the fibres of key (list of 256 values)?"""
    val = {}
    for p in range(256):
        b = (tab >> p) & 1
        if val.setdefault(key[p], b) != b: return False
    return True


# ---------------------------------------------------------------- named objects
Nv = [gf.power(p, 17) for p in range(256)]
nv = [gf.INV[q] for q in Nv]
Iv = gf.INV
X85 = [gf.power(p, 85) for p in range(256)]
X15 = [gf.power(p, 15) for p in range(256)]
X51 = [gf.power(p, 51) for p in range(256)]


def coords(vals):
    return [gf.bit_table(vals, k) for k in range(8)]


AFFX = gf.affine_x()
NC = coords(Nv); nC = coords(nv); IC = coords(Iv); X85C = coords(X85)
V0 = [tab_of(lambda p, s=s: Nv[p] == s) for s in gf.SUB16]          # indicator basis, dim 16


def span(*lists):
    S = gf.Span()
    for L in lists:
        for t in L: S.add(t)
    return S


NAMED = {
    'X': span(AFFX),
    'N': span([ONES], NC),
    'n': span([ONES], nC),
    'Nn': span([ONES], NC, nC),
    'V0': span(V0),
    'XN': span(AFFX, NC),
    'Xn': span(AFFX, nC),
    'XNn': span(AFFX, NC, nC),
    'XV0': span(AFFX, V0),
    'G4': span([ONES], X85C),
    'XG4': span(AFFX, X85C),
    'inv': span([ONES], IC),
}


def named_min(tab):
    hits = [k for k, S in NAMED.items() if S.contains(tab)]
    return hits


def anf_degree(t):
    a = [(t >> p) & 1 for p in range(256)]
    for i in range(8):
        s = 1 << i
        for p in range(256):
            if p & s: a[p] ^= a[p ^ s]
    return max((bin(p).count('1') for p in range(256) if a[p]), default=-1)


def op_as_product(op):
    for al in (0, 1):
        for be in (0, 1):
            for ga in (0, 1):
                if all(((op >> ((a << 1) | b)) & 1) == (((a ^ al) & (b ^ be)) ^ ga)
                       for a in (0, 1) for b in (0, 1)):
                    return al, be, ga
    raise ValueError(op)


def parse(path):
    c = read_ncff(path)
    n = c.n
    sym = [1 << (1 + i) for i in range(n)]
    tabs = list(gf.X)
    alev = [0] * n
    ands = []
    for op, a, b in c.gates:
        if op in (6, 9):
            s = sym[a] ^ sym[b] ^ (1 if op == 9 else 0)
            t = tabs[a] ^ tabs[b] ^ (ONES if op == 9 else 0)
            lv = max(alev[a], alev[b])
        elif op == 3:
            s = sym[a] ^ 1; t = tabs[a] ^ ONES; lv = alev[a]
        elif op in NONLINEAR_OPS:
            al, be, ga = op_as_product(op)
            L = sym[a] ^ al; R = sym[b] ^ be
            ta = tabs[a] ^ (ONES if al else 0); tb = tabs[b] ^ (ONES if be else 0)
            k = len(ands)
            lv = 1 + max(alev[a], alev[b])
            ands.append({'L': L, 'R': R, 'tab': ta & tb, 'Lt': ta, 'Rt': tb, 'level': lv})
            s = (1 << (1 + n + k)) ^ (1 if ga else 0)
            t = (ta & tb) ^ (ONES if ga else 0)
        else:
            raise ValueError(op)
        sym.append(s); tabs.append(t); alev.append(lv)
    outs = [sym[o] for o in c.outputs]
    otabs = [tabs[o] for o in c.outputs]
    return c, ands, outs, otabs


def deps(s, n=8):
    out = []; s >>= 1 + n; k = 0
    while s:
        if s & 1: out.append(k)
        s >>= 1; k += 1
    return out


def fmt(s, n=8):
    parts = []
    if s & 1: parts.append('1')
    xs = [i for i in range(n) if (s >> (1 + i)) & 1]
    if xs: parts.append('x[' + ''.join(str(i) for i in xs) + ']')
    parts += ['a%d' % (k + 1) for k in deps(s, n)]
    return '+'.join(parts) or '0'


def role(A):
    hl = named_min(A['Lt']); hr = named_min(A['Rt'])
    A['Lnamed'] = hl; A['Rnamed'] = hr
    if 'X' in hl and 'X' in hr: return 'S1'
    if 'V0' in hl and 'V0' in hr: return 'MID'
    if 'XNn' in hl and 'XNn' in hr: return 'LAST'
    if 'XV0' in hl and 'XV0' in hr: return 'LASTV0'
    return 'OTHER'


def analyse(path, quiet=False):
    c, ands, outs, otabs = parse(path)
    K = len(ands)
    out = {'file': str(path), 'K': K}
    levels = sorted({A['level'] for A in ands})
    out['profile'] = [sum(1 for A in ands if A['level'] == l) for l in levels]
    # fan-out
    for k, A in enumerate(ands):
        A['users'] = [j for j in range(K) if k in deps(ands[j]['L']) or k in deps(ands[j]['R'])]
        A['opuses'] = sum((k in deps(ands[j]['L'])) + (k in deps(ands[j]['R'])) for j in range(K))
        A['outuse'] = sum(1 for o in outs if k in deps(o))
        A['deg'] = anf_degree(A['tab'])
        A['degL'] = anf_degree(A['Lt']); A['degR'] = anf_degree(A['Rt'])
        A['role'] = role(A)
        A['supL'] = coset_support(A['Lt']); A['supR'] = coset_support(A['Rt'])
        A['sup'] = coset_support(A['tab'])
        A['mod17'] = sorted({e % 17 for e in A['sup'] if e not in (0, 255)})
    out['ands'] = [{k2: A[k2] for k2 in ('level', 'deg', 'degL', 'degR', 'role', 'Lnamed', 'Rnamed',
                                          'supL', 'supR', 'sup', 'mod17', 'users', 'opuses', 'outuse')}
                   | {'L': fmt(A['L']), 'R': fmt(A['R'])} for A in ands]
    # ---- span measurements per level
    rows = []
    for l in levels:
        E = span(AFFX, [A['tab'] for A in ands if A['level'] <= l])
        dims = {}
        # degree filtration of E: dim of E cap deg<=d computed via ANF: E is spanned by tables;
        # we compute ranks of E restricted to deg <= d by Gaussian elimination on ANF high parts.
        rows.append({'level': l, 'dimE': E.dim(),
                     'N_in': sum(E.contains(t) for t in NC),
                     'rankN': rank_in(E, NC), 'rankn': rank_in(E, nC), 'rankInv': rank_in(E, IC),
                     'rankOut': rank_in(E, otabs),
                     'rankX85': rank_in(E, X85C)})
    out['levels'] = rows
    P = span(AFFX, [A['tab'] for A in ands])
    out['P_dim'] = P.dim()
    out['P_cap'] = {k2: cap_dim(P, S) for k2, S in NAMED.items()}
    out['deg_hist'] = {}
    for A in ands:
        out['deg_hist'][A['deg']] = out['deg_hist'].get(A['deg'], 0) + 1
    out['roles'] = {}
    for A in ands:
        out['roles'][A['role']] = out['roles'].get(A['role'], 0) + 1
    if not quiet:
        report(out)
    return out


def rank_in(E, tabs):
    """dim of span(tabs) cap E  (as subspace count)"""
    S = gf.Span(tabs)
    return cap_dim(E, S)


def cap_dim(E, S):
    # dim(E cap S) = dim E + dim S - dim(E + S)
    ES = gf.Span()
    for p, (vv, _) in E.piv.items(): ES.add(vv)
    for p, (vv, _) in S.piv.items(): ES.add(vv)
    return E.dim() + S.dim() - ES.dim()


def report(o):
    print(o['file'])
    print('K=%d profile %s  P_dim=%d  roles %s  deg hist %s' % (
        o['K'], o['profile'], o['P_dim'], o['roles'], dict(sorted(o['deg_hist'].items()))))
    print('P cap named:', o['P_cap'])
    for r in o['levels']:
        print('  level<=%d dimE=%d rank N %d n %d inv %d out %d x85 %d' % (
            r['level'], r['dimE'], r['rankN'], r['rankn'], r['rankInv'], r['rankOut'], r['rankX85']))
    for k, A in enumerate(o['ands']):
        print('a%-2d L%d deg %d (%d,%d) %-6s fan %2d/%d out %d | L=%s [%s] | R=%s [%s]' % (
            k + 1, A['level'], A['deg'], A['degL'], A['degR'], A['role'], A['opuses'],
            len(A['users']), A['outuse'], A['L'], ','.join(A['Lnamed'][:3]), A['R'],
            ','.join(A['Rnamed'][:3])))
        print('      supL %s supR %s | prod sup %s mod17 %s' % (A['supL'], A['supR'], A['sup'],
                                                                 A['mod17']))


if __name__ == '__main__':
    o = analyse(sys.argv[1])
    if '--json' in sys.argv:
        Path(sys.argv[sys.argv.index('--json') + 1]).write_text(json.dumps(o, indent=1))
