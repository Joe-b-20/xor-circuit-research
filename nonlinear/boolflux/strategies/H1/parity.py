"""Row-parity space Pi(gamma) and the n-block counting bound (agent H1).

N-junk of a GF(4)-norm member depends only on its class zeta (H2 NOTES 3; checked here: the V0
part - univariate exponents divisible by 17 - of member_table(z, zeta, gamma) modulo span(1, N, n)
is the same for all z). Pi(gamma) = {pi in F_2^5 : sum pi_zeta g_zeta in span(1, N, n)}: the
parity vectors a target combination may have when the middle provides only n (R3).

Counting bound [P, NOTES 7]: a k-member layer using classes P (sizes n_P), d = dim(sum_P D_P)
(D_P = span of differences of the z's in row P), p = dim(Pi restricted to the used classes) needs
   8 - p <= sum_P min(n_P - 1, d) - d     and    d <= k - 8.
This prints, per gamma, the least k allowed by the bound over all class subsets and sizes.
usage: python3 parity.py"""
import itertools
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cond27, xag
from cond27 import gf, MU5

MULT17 = [0] + [17 * i for i in range(1, 15)] + [255]


def v0_part(t):
    """table of sum_{e = 0 mod 17} c_e x^e (a function of N)"""
    cs = {}
    f0 = t & 1
    for e in range(17, 255, 17):
        cs[e] = xag.coeff(t, e)
    d0 = 0
    for p in range(1, 256): d0 ^= (t >> p) & 1
    out = 0
    for p in range(256):
        if p == 0:
            v = f0
        else:
            v = 0
            for e, c in cs.items():
                if c: v ^= xag.EXP[(xag.LOG[c] + xag.LOG[p] * e) % 255]
            v ^= f0 ^ (d0 ^ f0)          # c_0 = f(0), c_255 = d0 + f(0), x^255 = 1 on F*
            assert v in (0, 1), v
        out |= v << p
    return out


def pi_space(gamma):
    base = xag.span([gf.ONES], xag.NC, xag.nC)
    gs = []
    for zt in MU5:
        reps = set()
        for z in (1, 7, 100, 201):
            r = v0_part(cond27.member_table(z, zt, gamma))
            reps.add(base.reduce(r)[0] if not base.contains(r) else 0)
        gs.append(v0_part(cond27.member_table(1, zt, gamma)))
    free = []
    for m in range(32):
        t = 0
        for i in range(5):
            if m >> i & 1: t ^= gs[i]
        if base.contains(t): free.append(m)
    # class-only check: V0 parts of different z in one class differ by span(1, N, n)?
    same = all(base.contains(v0_part(cond27.member_table(z, zt, gamma)) ^ gs[i])
               for i, zt in enumerate(MU5) for z in (3, 77, 250))
    return free, same


def bound(free):
    best = None
    for r in range(1, 6):
        for cls in itertools.combinations(range(5), r):
            p = len([m for m in free if all((m >> i & 1) == 0 for i in range(5) if i not in cls)])
            p = p.bit_length() - 1             # |subspace| = 2^p
            for d in range(0, 9):
                # best sizes: n_P - 1 >= d for as many rows as needed; minimal k = 8 + ... search
                for k in range(8, 19):
                    if d > k - 8: continue
                    # maximise sum min(n_P - 1, d) with sum n_P = k, n_P >= 1
                    cap = min(r * d, k - r)
                    if 8 - p <= cap - d:
                        if best is None or k < best[0]: best = (k, cls, d, p)
                        break
    return best


if __name__ == '__main__':
    for g in ['none'] + [str(17 * i) for i in range(15)]:
        free, same = pi_space(g)
        print('gamma %-4s  Pi = %s (dim %d)  class-only: %s  least k by bound: %s' % (
            g, [format(m, '05b')[::-1] for m in free], len(free).bit_length() - 1, same, bound(free)))
