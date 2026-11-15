"""Exact condition list for a 9 + 5 + k circuit with a GF(4)-norm last layer (agent H1).

Graph model: members are true functions of x (track C's model: m = (z, zeta), product
N_GF(4)(Tr(Ax) + Tr_K(s v)), v = n + gamma N, s^3 = zeta, A = z / (zeta s)); one gamma per layer.
Stage 1 is NOT fixed: it must be any l = 9 level-1 products covering U = V_N + x-junk.
A layer S (k members) yields 9 + 5 + k ANDs iff all of:
  R1 (n-block, gamma-free): the 16-bit vectors (Y_m, z_m), Y = z/zeta, span a space containing
     F x 0 (equivalently: per output, sum c Y = b_j and sum c z = 0 are solvable).
  R2 (feasibility): T inside span(1, x, N, n, Quad, S)   [Quad = all x-quadratic forms]
  R3 (N-junk): T inside span(1, x, N, n, Quad, S) needs no function of N beyond span(1, N, n)
     - implied by R2 here because R2 uses no V0. (With V0 free one gets C's/G's weaker test.)
     H2 [C, vjunk.py]: no nonzero N-junk lands in any of G's 30 classes of 5-AND middles, so R3
     is necessary for a 5-AND middle, and with R3 the middle is BMP (n only).
  R4 (x-junk): J = dim(A + S + T) - dim(A + S), A = span(1, x, N, n); U = V_N + q-parts,
     unique iff D = Quad cap (A + S) adds nothing mod V_N (reported).
  R5 (stage 1): U lies in the span of 9 level-1 products (exact: track C's cover_enum when
     9 - dim U <= 2, else track C's SAT model via G's cover_cli with a time limit).
Then the circuit is 9 + 5 + k: R5's products, BMP 5-AND inversion, S, XOR network (build with
strategies/C/build27.py or G/eval3.py, then aes_check.py).

usage: python3 cond27.py FILE GAMMA      (test the last layer of a circuit file)
       import cond27; cond27.evaluate(members, gamma)   (members = [(z, zeta), ...])
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'G'))
sys.path.insert(0, str(HERE.parent / 'C'))
sys.path.insert(0, str(HERE))
import gf                                    # noqa: E402
import qmc                                   # noqa: E402
import wsat                                  # noqa: E402
import xag                                   # noqa: E402
from fam_check import gp                     # noqa: E402
from kj_search import Model                  # noqa: E402
from zdfs import MU5, CUBE_ROOT              # noqa: E402

ONES = gf.ONES
QUAD = [gf.X[i] & gf.X[j] for i in range(8) for j in range(i + 1, 8)]
T = [gf.bit_table(gf.INV, k) for k in range(8)]
A_BASE = [ONES] + list(gf.X) + xag.NC + xag.nC
_models = {}


def model(gamma):
    if gamma not in _models:
        _models[gamma] = Model(gp(int(gamma)) if gamma != 'none' else None, 'hard')
    return _models[gamma]


def member_table_slow(z, zeta, gamma):
    s = CUBE_ROOT[zeta]; Y = gf.mul(gf.INV[zeta], z); A = gf.mul(Y, gf.INV[s])
    return wsat.member_table(model(gamma), A, s)


# fast version (same function; checked against member_table_slow in selftest())
_EXP = xag.EXP; _LOG = xag.LOG
_TRF = [0] * 256
for _p in range(256):
    _t = 0
    for _i in range(8): _t ^= gf.power(_p, 1 << _i)
    _TRF[_p] = _t & 1
_TRK = [0] * 256
for _p in gf.SUB16:
    _t = 0
    for _i in range(4): _t ^= gf.power(_p, 1 << _i)
    _TRK[_p] = _t & 1
_OM = gp(85); _OM2 = gf.mul(_OM, _OM)
_vcache = {}


def _fmul(a, b):
    return 0 if a == 0 or b == 0 else _EXP[_LOG[a] + _LOG[b]]


def _vtab(gamma):
    if gamma not in _vcache:
        _vcache[gamma] = model(gamma).w
    return _vcache[gamma]


def _tab(A, s, V, TRs):
    t = 0
    for p in range(256):
        if _TRF[_fmul(A, p)] ^ TRs[_fmul(s, V[p])]: t |= 1 << p
    return t


def member_table(z, zeta, gamma):
    s = CUBE_ROOT[zeta]; Y = gf.mul(gf.INV[zeta], z); A = gf.mul(Y, gf.INV[s])
    V = _vtab(gamma)
    return _tab(A, s, V, _TRK) & _tab(gf.mul(_OM, A), gf.mul(_OM2, s), V, _TRK)


def selftest(n=40):
    import random
    rnd = random.Random(1)
    for _ in range(n):
        z = rnd.randrange(1, 256); zt = rnd.choice(MU5)
        g = rnd.choice(['none'] + [str(17 * i) for i in range(15)])
        assert member_table(z, zt, g) == member_table_slow(z, zt, g), (z, zt, g)
    return True


def r1(members):
    """n-block test on (Y, z) in F^2 (16 bits)."""
    sp = gf.Span()
    for z, zeta in members:
        sp.add(gf.mul(z, gf.INV[zeta]) | (z << 8))
    return all(sp.contains(1 << i) for i in range(8))


def dim(*lists):
    return xag.span(*lists).dim()


def junk(members, gamma):
    """returns (feasible, J, q-parts, dimD) for one gamma"""
    S = [member_table(z, zt, gamma) for z, zt in members]
    if dim(A_BASE, QUAD, S, T) != dim(A_BASE, QUAD, S):
        return False, None, None, None
    J = dim(A_BASE, S, T) - dim(A_BASE, S)
    # q-parts: express each target over [A, S] (tag 0) then Quad (tagged)
    sp = gf.Span()
    for t in A_BASE + S: sp.add(t, 0)
    for i, t in enumerate(QUAD): sp.add(t, 1 << i)
    qs = []
    for t in T:
        r, tag = sp.reduce(t)
        assert r == 0
        q = 0
        for i in range(28):
            if tag >> i & 1: q ^= QUAD[i]
        qs.append(q)
    # D = Quad cap (A + S) modulo V_N (+ affine)
    dQ = dim([ONES], gf.X, QUAD); dAS = dim(A_BASE, S); dAll = dim(A_BASE, S, QUAD)
    capD = dQ + dAS - dAll                       # dim(Quad+aff  cap  A+S)
    capVN = dim([ONES], gf.X, xag.NC)            # = 13: aff + V_N, which lies in both
    return True, J, qs, capD - capVN


def cover(qs, limit=60):
    import eval3                                  # track G (imports track C's cover_enum)
    A = gf.Span([ONES] + list(gf.X))
    U = [t for t in xag.NC + qs if A.add(t)]
    ok, pairs = eval3.cover_sat(U, 9, limit)
    return len(U), ok


def evaluate(members, gamma, do_cover=True, limit=60):
    out = {'k': len(members), 'gamma': gamma, 'R1': r1(members)}
    if not out['R1']: return out
    feas, J, qs, dD = junk(members, gamma)
    out.update({'R2R3': feas})
    if not feas: return out
    out.update({'J': J, 'dimD_modVN': dD})
    if do_cover and J <= 5:
        dU, ok = cover(qs, limit)
        out.update({'dimU': dU, 'R5': ok})
    return out


def members_of_file(f, gamma):
    from exp_stage3 import tables_of
    l1, inv = tables_of(f)
    En = qmc.Normal([ONES] + list(gf.X) + l1 + inv)
    idx = {}
    for z in range(1, 256):
        for zeta in MU5:
            idx.setdefault(En.nf(member_table(z, zeta, gamma)), (z, zeta))
    c, ands, outs, ot = xag.parse(f)
    top = max(A['level'] for A in ands)
    return [idx[En.nf(A['tab'])] for A in ands if A['level'] == top]


if __name__ == '__main__':
    f, g = sys.argv[1], sys.argv[2]
    mem = members_of_file(f, g)
    print(Path(f).name, mem)
    print(evaluate(mem, g))
