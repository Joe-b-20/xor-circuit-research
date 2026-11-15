"""X3b x3b_junk.py REF FILE ...: per-level junk structure of A28-type circuits compared with REF.

For each file (H1 xag roles: S1, MID, LAST/LASTV0/OTHER):
  * dims of V_L = span(1, x, ANDs of level <= L) and dim(V_L cap V_L(REF)) - 9 per level;
  * U = V_N + S1-parts of the outputs (H1 decomp), dim(U cap U_REF) - 9;
  * junk coordinates (c3, c5, c9) (univariate coefficients of x^3, x^5, x^9; class 17 = V_N is free):
    rank over GF(2) of these 24-bit vectors on V_1 (stage 1) and on U, and of c5 alone;
  * the part of the outputs on each level that is NOT the same as REF's (dim of
    span(level-L parts) and its intersection with REF's), level parts from the unique
    decomposition y = sum c_k a_k + affine (ANDs independent);
  * exact 9-cover test of U (G eval3.cover_sat, as H1 cond27 R5), if --cover.
"""
import sys
from pathlib import Path
S = Path.home() / 'xcr-boolflux/nonlinear/boolflux/strategies'
for d in ('G', 'C', 'H1'):
    sys.path.insert(0, str(S / d))
import xag
from xag import ONES, AFFX, NC, coeff, deps

def ech(vs):
    b = {}
    for v in vs:
        while v:
            h = v.bit_length() - 1
            if h in b: v ^= b[h]
            else: b[h] = v; break
    return b
def dim(vs): return len(ech(vs))
def capdim(a, b): return dim(a) + dim(b) - dim(list(a) + list(b))

def jc(t):
    return coeff(t, 3) | (coeff(t, 5) << 8) | (coeff(t, 9) << 16)

def info(f):
    c, ands, outs, otabs = xag.parse(f)
    roles = [xag.role(A) for A in ands]
    top = max(A['level'] for A in ands)
    V = {L: list(AFFX) + [A['tab'] for A in ands if A['level'] <= L] for L in range(1, top + 1)}
    def part(o, pred):
        t = 0
        for k in deps(o):
            if pred(k): t ^= ands[k]['tab']
        return t
    s1 = [part(o, lambda k: roles[k] == 'S1') for o in outs]
    U = list(AFFX) + list(NC) + s1
    lvparts = {L: [part(o, lambda k, L=L: ands[k]['level'] == L) for o in outs] for L in range(1, top + 1)}
    st1 = [A['tab'] for A in ands if A['level'] == 1]
    return dict(f=Path(f).name, V=V, U=U, s1=s1, st1=st1, lv=lvparts, top=top,
                prof='|'.join(str(sum(1 for A in ands if A['level'] == L)) for L in range(1, top + 1)),
                roles={r: roles.count(r) for r in set(roles)})

ref = info(sys.argv[1])
cov = '--cover' in sys.argv
files = [a for a in sys.argv[1:] if not a.startswith('--')]
for f in files:
    r = info(f)
    lvl = ' '.join('L%d:%d/%d' % (L, capdim(r['V'][L], ref['V'][L]) - 9, dim(r['V'][L]) - 9)
                   for L in r['V'] if L in ref['V'])
    dU = dim(r['U']) - 9
    capU = capdim(r['U'], ref['U']) - 9
    # junk coordinates
    j1 = dim([jc(t) for t in r['st1']]); j1c5 = dim([coeff(t, 5) for t in r['st1']])
    jU = dim([jc(t) for t in r['s1']]); jUc5 = dim([coeff(t, 5) for t in r['s1']])
    # output parts per level, same as REF's? (span of the 8 parts, mod affine)
    lp = ' '.join('P%d:%d/%d' % (L, capdim(list(AFFX) + r['lv'][L], list(AFFX) + ref['lv'][L]) - 9,
                                 dim(list(AFFX) + r['lv'][L]) - 9) for L in r['lv'] if L in ref['lv'])
    s = '%-58s %s %s | %s | dimU %d capU_ref %d | jc(stage1) %d c5 %d | jc(U) %d c5 %d | %s' % (
        r['f'][:58], r['prof'], r['roles'], lvl, dU, capU, j1, j1c5, jU, jUc5, lp)
    if cov:
        import eval3
        A = ech(list(AFFX))
        Ub = []
        b = dict(A)
        for t in list(NC) + r['s1']:
            v = t
            while v:
                h = v.bit_length() - 1
                if h in b: v ^= b[h]
                else: b[h] = v; Ub.append(t); break
        ok, pairs = eval3.cover_sat(Ub, 9, 60)
        s += ' | 9-cover(U): %s' % ok
    print(s, flush=True)
