"""Exact search: can ONE extra product l*m (l, m in an operand space O) close the last missing
output dimension of a near-complete layer?

P = span(1, x, given AND outputs).  T = the 8 S-box output tables.  If dim(T + P) - dim(P) = 1,
with missing direction t*, we search all l in O (Gray code) and solve linearly for m.
Returns all (l, m) found (as tables).
"""
import sys, itertools
from h2lib import Basis
import a28parse as AP

ONE = AP.ONE


def missing(P_tabs, T=None):
    T = T or AP.Stabs
    B = Basis()
    for v in [ONE] + AP.BITS + list(P_tabs): B.add(v)
    miss = Basis(); reps = []
    for t in T:
        r = B.full_reduce(t)[0]
        if miss.add(r): reps.append(r)
    return B, reps


def search(P_tabs, O_basis, maxsol=20, verbose=True):
    B, reps = missing(P_tabs)
    if len(reps) != 1:
        if verbose: print('missing dims =', len(reps))
        return len(reps), []
    tstar = reps[0]
    red = lambda v: B.full_reduce(v)[0]
    O = list(O_basis)
    k = len(O)
    R = [[red(O[i] & O[j]) for j in range(k)] for i in range(k)]
    cur = [0] * k              # red(l * o_j) for current l
    l = 0; sols = []
    for g in range(1, 1 << k):
        i = (g & -g).bit_length() - 1        # gray: flip basis i
        l ^= 1 << i
        Ri = R[i]
        for j in range(k): cur[j] ^= Ri[j]
        # is tstar in span(cur)?
        Bl = Basis(track=True)
        for j in range(k):
            if cur[j]: Bl.add(cur[j], 1 << j)
        r, tag = Bl.full_reduce(tstar)
        if r == 0:
            lt = 0
            for a in range(k):
                if l >> a & 1: lt ^= O[a]
            mt = 0
            for a in range(k):
                if tag >> a & 1: mt ^= O[a]
            sols.append((l, tag, lt, mt))
            if len(sols) >= maxsol: break
    if verbose: print('missing dims = 1; solutions found:', len(sols))
    return 1, sols


def dedupe_O(vs):
    B = Basis(); out = []
    for v in vs:
        if B.add(v): out.append(v)
    return out


if __name__ == '__main__':
    import glob
    D = '../../../nist/aes-sbox/'
    ad4 = sorted(glob.glob(D + 'aes-sbox-a28-ad4-g131-gd31*'))[0]
    ad5 = sorted(glob.glob(D + 'aes-sbox-a28-ad5-g124*'))[0]
    _, A4 = AP.load(ad4); _, A5 = AP.load(ad5)
    L4 = [A['out'] for A in A4 if A['stage'] == 'L']
    M4 = [A['out'] for A in A4 if A['stage'] == 'M']
    F4 = [A['out'] for A in A4 if A['stage'] == 'F']
    L5 = [A['out'] for A in A5 if A['stage'] == 'L']
    M5 = [A['out'] for A in A5 if A['stage'] == 'M']
    F5 = [A['out'] for A in A5 if A['stage'] == 'F']
    Obase = dedupe_O([ONE] + AP.BITS + AP.Ntabs + AP.ntabs)
    print('O dims', len(Obase))
    for name, P in [('AD4L+AD5M+AD4F', L4 + M5 + F4), ('AD5L+AD4M+AD5F', L5 + M4 + F5),
                    ('AD4L+AD5M+AD5F', L4 + M5 + F5), ('AD5L(9 subsets)+AD5M+AD5F', None)]:
        if P is None: continue
        print(name)
        d, sols = search(P, Obase)
        for s in sols[:5]: print('  l-mask %x m-mask %x' % (s[0], s[1]))
    # O enlarged by middle products
    O2 = dedupe_O(Obase + M5)
    print('O2 dims', len(O2))
    d, sols = search(L4 + M5 + F4, O2)
