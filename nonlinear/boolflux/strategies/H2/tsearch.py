"""Exact last-layer search in the relaxed tower model (L, R early; v late, independent).

Free: affine(L, R, v), umizame's 9 early products (Karatsuba on LR), v-quadratic forms g with
g(Q + gamma D) in span(1, D, BMP products) (as functions of D), Q = D^-1.
Targets: coordinates of R (v + gamma D) and (v + gamma D) L.
Candidates: GF(4)-norm members (lam(L,R), mu(v)), set chosen by --cands:
  row   : umizame row-local members (lam in span_GF4{a_r, b_r}, mu = c_r)  (45)
  rows+ : lam in span_GF4{a_r, b_r} for any row r, mu any class            (3 x 15 x 15 / ...)
  all   : all members (1275 distinct)
Runs ./cover for K = kmin..kmax; prints solutions.
usage: tsearch.py CANDS GAMMA|all KMIN KMAX [MAXSOL]
"""
import sys, subprocess, itertools, os, json
from h2lib import Basis
import tower as TW
from tower import m4, tau, W, W2, MUL, INV16, norm, tab, VAR, ONE, g16, b16, sq

HERE = os.path.dirname(os.path.abspath(__file__))


def gf4_of(i, which):
    A1, A0 = g16(i); return A1 if which else A0


# GF(4)-valued linear functionals of (L, R): coefficients (c_L1, c_L0, c_R1, c_R0)
def lam_val(coef, L, R):
    cL1, cL0, cR1, cR0 = coef
    return m4(cL1, gf4_of(L, 1)) ^ m4(cL0, gf4_of(L, 0)) ^ m4(cR1, gf4_of(R, 1)) ^ m4(cR0, gf4_of(R, 0))


def mu_val(coef, v):
    c1, c0 = coef
    return m4(c1, gf4_of(v, 1)) ^ m4(c0, gf4_of(v, 0))


def member_table(lc, mc):
    def f(L, R, v):
        a = lam_val(lc, L, R); c = mu_val(mc, v)
        return (tau(a) ^ tau(m4(W, c))) & (tau(m4(W, a)) ^ tau(c))
    return tab(f)


# umizame rows: (a, b, c) = (L0, R0, Q0), (W L1, W R1, W Q1), (L0 + W L1, R0 + W R1, Q0 + W Q1)
ROWS = [((0, 1, 0, 0), (0, 0, 0, 1), (0, 1)),
        ((W, 0, 0, 0), (0, 0, W, 0), (W, 0)),
        ((W, 1, 0, 0), (0, 0, W, 1), (W, 1))]


def lin_comb(r, a, t, b):
    return tuple(m4(r, x) ^ m4(t, y) for x, y in zip(a, b))


def early_products():
    ps = []
    for a, b, c in ROWS:
        for r in (1, W, W2):
            ps.append(tab(lambda L, R, v, a=a, b=b, r=r: tau(m4(r, lam_val(a, L, R))) & tau(m4(r, lam_val(b, L, R)))))
    return ps


def d_bits(D):
    A1, A0 = g16(D)
    d0, d1 = TW.NB[A1]; d2, d3 = TW.NB[A0]
    return d0, d1, d2, d3


def middle_span16():
    """BMP products as 16-point tables over D (index = D's 4-bit code)."""
    out = []
    m = [[0] * 16 for _ in range(5)]
    for D in range(16):
        d0, d1, d2, d3 = d_bits(D)
        m1 = (d0 ^ d1) & (d2 ^ d3)
        m2 = d1 & (d2 ^ m1)
        m3 = (d0 ^ m1) & d3
        m4_ = d2 & (m1 ^ m3)
        m5 = (d0 ^ m2) & (d2 ^ m1 ^ m4_)
        q0 = d2 ^ d3 ^ m4_; q1 = d3 ^ m3 ^ m4_; q2 = d0 ^ d1 ^ m2 ^ m5; q3 = d1 ^ m5
        # check Q = D^-1: Q = (q0 W^2 + q1 W) Z^4 + (q2 W^2 + q3 W) Z
        Qb = b16((TW.nb(q0, q1), TW.nb(q2, q3)))
        assert Qb == INV16[D], (D, Qb, INV16[D])
        for i, val in enumerate((m1, m2, m3, m4_, m5)): m[i][D] = val
    tabs = [sum(1 << D for D in range(16) if m[i][D]) for i in range(5)]
    lin = [sum(1 << D for D in range(16) if D >> j & 1) for j in range(4)]
    return [0xFFFF] + lin + tabs


def allowed_vquads(gamma):
    """v-quadratic forms (as 4096 tables) whose pullback g(Q + gamma D) lies in the middle span."""
    MS = Basis()
    for t in middle_span16(): MS.add(t)
    out = []
    pairs = list(itertools.combinations(range(4), 2))
    # enumerate all quadratic forms in v (2^6) and keep those allowed; return a basis
    B = Basis()
    for mask in range(1, 64):
        def gv(v):
            s = 0
            for k, (i, j) in enumerate(pairs):
                if mask >> k & 1: s ^= (v >> i) & (v >> j) & 1
            return s
        pull = sum(1 << D for D in range(16) if gv(INV16[D] ^ MUL[gamma][D]))
        if MS.contains(pull):
            t = tab(lambda L, R, v: gv(v))
            if B.add(t): out.append(t)
    return out


def targets(gamma):
    T = []
    for which in range(8):
        def f(L, R, v, which=which):
            Q = v ^ MUL[gamma][norm(L, R)]
            val = MUL[R][Q] if which < 4 else MUL[Q][L]
            return (val >> (which % 4)) & 1
        T.append(tab(f))
    return T


def all_lams():
    out = []
    for c in itertools.product(range(4), repeat=4):
        if any(c): out.append(c)
    return out


def all_mus():
    return [c for c in itertools.product(range(4), repeat=2) if any(c)]


def candidates(kind):
    C = []
    if kind == 'row':
        for a, b, c in ROWS:
            for r in range(4):
                for t in range(4):
                    if r == 0 and t == 0: continue
                    C.append((lin_comb(r, a, t, b), c))
    elif kind == 'rows+':
        for a, b, c in ROWS:
            for r in range(4):
                for t in range(4):
                    if r == 0 and t == 0: continue
                    for mu in all_mus():
                        C.append((lin_comb(r, a, t, b), mu))
    elif kind == 'all':
        for lc in all_lams():
            for mu in all_mus():
                C.append((lc, mu))
    return C


def setup(kind, gamma):
    free = [ONE] + VAR + early_products() + allowed_vquads(gamma)
    FB = Basis()
    for f in free: FB.add(f)
    # D coordinates must be free (check)
    for j in range(4):
        dt = tab(lambda L, R, v, j=j: norm(L, R) >> j & 1)
        assert FB.contains(dt), 'D not in early span'
    T = [FB.full_reduce(t)[0] for t in targets(gamma)]
    C = candidates(kind)
    ctabs = {}
    cl = []
    for lc, mc in C:
        t = FB.full_reduce(member_table(lc, mc))[0]
        if t == 0 or t in ctabs: continue
        ctabs[t] = len(cl); cl.append((t, lc, mc))
    # quotient coordinates
    QB = Basis(track=True); nb_ = 0
    for v in T + [c[0] for c in cl]:
        if QB.add(v, 1 << nb_): nb_ += 1
    def coord(v):
        r, tag = QB.full_reduce(v); assert r == 0; return tag
    return T, cl, coord, nb_, FB


def run_cover(Tc, Cc, K, maxsol=0):
    lines = ['%d %d %d %d' % (len(Cc), len(Tc), K, maxsol)]
    for v in Tc + Cc:
        lines.append('%x %x' % (v >> 64, v & ((1 << 64) - 1)))
    p = subprocess.run([os.path.join(HERE, 'cover')], input='\n'.join(lines) + '\n', capture_output=True, text=True)
    sols = [list(map(int, ln.split()[1:])) for ln in p.stdout.splitlines() if ln.startswith('SOL')]
    return sols, p.stderr.strip()


if __name__ == '__main__':
    kind = sys.argv[1]; gs = sys.argv[2]; kmin = int(sys.argv[3]); kmax = int(sys.argv[4])
    maxsol = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    gammas = range(16) if gs == 'all' else [int(gs)]
    for gamma in gammas:
        T, cl, coord, dim, FB = setup(kind, gamma)
        Tc = [coord(t) for t in T]; Cc = [coord(c[0]) for c in cl]
        TB = Basis()
        rk = sum(1 for t in Tc if TB.add(t))
        print('gamma', gamma, 'quotient dim', dim, 'target rank', rk, 'cands', len(cl), 'allowed vquads', len(allowed_vquads(gamma)), flush=True)
        if dim > 128: print('  quotient too big'); continue
        for K in range(kmin, kmax + 1):
            sols, err = run_cover(Tc, Cc, K, maxsol)
            print('  K', K, 'solutions', len(sols), err, flush=True)
            if sols:
                for s in sols[:3]:
                    print('   ', [(cl[i][1], cl[i][2]) for i in s])
                break
