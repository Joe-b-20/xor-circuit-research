"""Alternative inversion routes, built as verified circuits (AND counts are exact for the
construction).  usage: d_routes.py OUTPREFIX

 q_tower : GF(4)-norm route, x^-1 = x^84 * N4^2, x^84 = x^16 * N^4, N = x^17, N4 = N^5
 q_pure  : GF(4)-norm route without the GF(16) norm of x: u = x^5 = x*s(x) (s = x->x^4) from
           Q-coordinates, N4 = N_{F/K}(u) = u^17 = x^85, adj = s(x)*s^2(u) = x^84, x^-1 = adj*N4^2
 q_pure2 : as q_pure, but N4 = x * adj taken from a full product (only the GF(4) part kept)
 itoh    : Itoh-Tsujii x^254 = (x^127)^2, 127 = 2^7-1 by the chain 1,2,3,6,7 (x^3, x^7, x^63, x^127)
 hybrid  : one K-coordinate of x^-1 through x^16*n (n = kinv5(N)), the other through
           (x^16*N^4)*N4^2
"""
import sys

import blocks
from h4lib import (Circ, Tower, norm, finv, smul, fmul, check_inverse, save, mul, pw, Q, K,
                   W)


def qcoords(C, T, b):
    """Q-coordinates of an F-valued bundle w.r.t. the Q-basis {f_i * g_j} of the tower"""
    LF, LK = T.levels[2], T.levels[1]
    b0, b1 = LF.coords(b)
    out = []; basis = []
    for bi, fi in ((b0, LF.e[0]), (b1, LF.e[1])):
        c0, c1 = LK.coords(bi)
        out += [c0, c1]; basis += [mul(fi, LK.e[0]), mul(fi, LK.e[1])]
    return out, basis


def design(name, T):
    C = Circ(); x = C.x
    if name == 'q_tower':
        N = norm(C, T, x, 3)
        N4 = norm(C, T, N, 2)
        adj = smul(C, T, C.frob(x, 4), C.frob(N, 2), 3, 2)
        y = smul(C, T, adj, C.frob(N4, 1), 3, 1)
    elif name in ('q_pure', 'q_pure2'):
        a, beta = qcoords(C, T, x)
        sbeta = [pw(b, 4) for b in beta]
        u = {}
        for i in range(4):
            u = C.add(u, C.scale(C.frob(a[i], 1), mul(beta[i], sbeta[i])))   # a_i^2 b_i s(b_i)
            for j in range(i + 1, 4):
                p = fmul(C, T, a[i], a[j], 1)
                u = C.add(u, C.scale(p, mul(beta[i], sbeta[j]) ^ mul(beta[j], sbeta[i])))
        adj = fmul(C, T, C.frob(x, 2), C.frob(u, 4), 3)
        if name == 'q_pure':
            N4 = C.project(norm(C, T, u, 3), Q)
        else:
            N4 = C.project(fmul(C, T, x, adj, 3), Q)
        y = smul(C, T, adj, C.frob(N4, 1), 3, 1)
    elif name == 'itoh':
        x3 = fmul(C, T, x, C.frob(x, 1), 3)
        x7 = fmul(C, T, C.frob(x3, 1), x, 3)
        x63 = fmul(C, T, C.frob(x7, 3), x7, 3)
        x127 = fmul(C, T, C.frob(x63, 1), x, 3)
        y = C.frob(x127, 1)
    elif name == 'hybrid':
        N = norm(C, T, x, 3)
        n = blocks.kinv_plug(C, N)
        N4 = norm(C, T, N, 2)
        LF = T.levels[2]
        x16 = C.frob(x, 4)
        c0, c1 = LF.coords(x16)
        y0 = fmul(C, T, c0, n, 2)
        z1 = fmul(C, T, c1, C.frob(N, 2), 2)
        y1 = smul(C, T, z1, C.frob(N4, 1), 2, 1)
        y = C.add(C.scale(y0, LF.e[0]), C.scale(y1, LF.e[1]))
    else:
        raise SystemExit(name)
    return C, y


if __name__ == '__main__':
    out = sys.argv[1]
    for name in ('q_tower', 'q_pure', 'q_pure2', 'itoh', 'hybrid'):
        best = None
        for kinds in (('normal',) * 3, ('poly',) * 3):
            T = Tower(kinds)
            C, y = design(name, T)
            ok = check_inverse(C, y)
            print(name, kinds, 'ANDs', C.ands, 'inverse ok', ok, flush=True)
            if ok and (best is None or C.ands < best[0]): best = (C.ands, C, y, kinds)
        if best:
            m = save(best[1], best[2], '%s-%s.circ.txt' % (out, name), ['H4 %s %s' % (name, best[3])])
            print(name, m['A'], m['AD'], m['G'], m['GD'], flush=True)
