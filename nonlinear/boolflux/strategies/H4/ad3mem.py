"""Level 2 of the AD3 GF(4)-norm route in the 'member' family (the structure of the published
A35, see NOTES.md section 4):
  members  m_lam = z0 * z1,  z = Tr_{F/Q}(lam x) + gamma(N)  (z0, z1 its GF(2) components in
           the basis {1, w} of Q), gamma = (g0, g1) a fixed pair of N-forms;  lam in F*
  N-products  products of two N-forms
Requirement (mod E0 = span(1, x, N)):  T in M + U,  M = span(members, N-products),
U = x-quadratic junk to be produced by level 1 (l1 = cover(V_N + U)).
Minimal junk dim J = dim((T + M)/M) when T + M is inside M + X2 (X2 = x-quadratics).

Search: simulated annealing over the k member parameters and the p N-product slots,
score = 100 * infeasibility + J.  Prints the best states; --cover runs the exact level-1 cover
(cover1.py SAT) of V_N + U for promising states.

usage: ad3mem.py --k K --p P --seconds S --seed S [--gamma g0,g1] [--cover]
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import random
import time

import cover1
from ad3sat import XT, NT, ADJ, N4T, basis_of
from h4lib import ONES, mul, pw, W

Nb = basis_of([t for t in NT if t])
E0 = cover1.rowspace([ONES] + XT + Nb)


def red(v, rows=E0):
    return cover1.reduce(v, rows)


def lin(bits, basis):
    t = 0
    for i, b in enumerate(basis):
        if (bits >> i) & 1: t ^= b
    return t


# Tr_{F/Q} components
def trFQ(z):
    return z ^ pw(z, 4) ^ pw(z, 16) ^ pw(z, 64)


W2 = mul(W, W)
QC = {0: (0, 0), 1: (1, 0), W: (0, 1), W2: (1, 1)}       # q = q0 + q1 w


def comp_tables(lam):
    t0 = t1 = 0
    for p in range(256):
        q0, q1 = QC[trFQ(mul(lam, p))]
        if q0: t0 |= 1 << p
        if q1: t1 |= 1 << p
    return t0, t1


COMP = {lam: comp_tables(lam) for lam in range(1, 256)}
X2 = basis_of([red(XT[a] & XT[b]) for a in range(8) for b in range(a + 1, 8)])
X2rows = cover1.rowspace(X2)
T = basis_of([red(t) for t in ADJ + [t for t in N4T if t]])
NFORMS = list(range(1, 16))


def member(lam, gamma):
    g0, g1 = gamma
    a0, a1 = COMP[lam]
    return red((a0 ^ lin(g0, Nb)) & (a1 ^ lin(g1, Nb)))


def nprod(a, b):
    return red(lin(a, Nb) & lin(b, Nb))


def junk(Mvecs):
    """returns (infeasibility, J): T + M must lie in M + X2"""
    M = cover1.rowspace(Mvecs)
    dM = len(M)
    TM = cover1.rowspace(Mvecs + T)
    J = len(TM) - dM
    MX = cover1.rowspace(Mvecs + X2)
    inf = len(cover1.rowspace(Mvecs + X2 + T)) - len(MX)
    return inf, J


def junk_space(Mvecs):
    """a valid U (subspace of X2) with T in M + U: for each target, an X2 part (canonical)"""
    # solve t = m + u: build combined basis of M and X2 with tags
    rows = {}
    def add(v, tag):
        for h in sorted(rows, reverse=True):
            if (v >> h) & 1: v ^= rows[h][0]; tag ^= rows[h][1]
        if v: rows[v.bit_length() - 1] = (v, tag)
    for i, m in enumerate(Mvecs): add(m, 0)
    for i, x in enumerate(X2): add(x, 1 << i)
    U = []
    for t in T:
        v = t; tag = 0
        for h in sorted(rows, reverse=True):
            if (v >> h) & 1: v ^= rows[h][0]; tag ^= rows[h][1]
        assert v == 0
        U.append(lin(tag, X2))
    return U


def m_cap_x2(Mvecs):
    """basis of span(M) & span(X2) (functions mod E0)"""
    rows = {}
    out = []
    def add(v, tag):
        for h in sorted(rows, reverse=True):
            if (v >> h) & 1: v ^= rows[h][0]; tag ^= rows[h][1]
        if v: rows[v.bit_length() - 1] = (v, tag); return None
        return tag
    for m in Mvecs: add(m, 0)
    for j, x in enumerate(X2):
        t = add(x, 1 << j)
        if t: out.append(lin(t, X2))
    return out


def to_wedge(f):
    """x-quadratic function (mod E0) -> its wedge vector on Lambda^2(8) (ANF), mod V_N handled by
    adding V_N to the cover targets"""
    return cover1.form_from_anf(8, cover1.anf_quadratic_part(f, 8))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--k', type=int, default=9); ap.add_argument('--p', type=int, default=3)
    ap.add_argument('--seconds', type=float, default=60); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--gamma', default=None)
    ap.add_argument('--cover', action='store_true')
    ap.add_argument('--T0', type=float, default=0.6)
    ap.add_argument('--out', default=None)
    ap.add_argument('--mix', action='store_true', help='each member has its own gamma (of the 15 good ones)')
    ap.add_argument('--restarts', type=int, default=1)
    ap.add_argument('--maxl1', type=int, default=10)
    a = ap.parse_args()
    rnd = random.Random(a.seed)
    if a.gamma:
        gamma = tuple(int(s, 0) for s in a.gamma.split(','))
    elif not a.mix:
        gamma = (10, 14)
    else:
        while True:
            gamma = (rnd.randrange(1, 16), rnd.randrange(1, 16))
            if gamma[0] != gamma[1]: break
    k, p = a.k, a.p
    GOOD = [(1, 8), (2, 7), (3, 15), (4, 10), (5, 2), (6, 13), (7, 5), (8, 9), (9, 1), (10, 14),
            (11, 6), (12, 3), (13, 11), (14, 4), (15, 12)]
    mix = a.mix
    def rmem():
        return (rnd.randrange(1, 256), rnd.choice(GOOD) if mix else gamma)
    lams = [rmem() for _ in range(k)]
    npairs = [tuple(rnd.sample(NFORMS, 2)) for _ in range(p)]
    mcache = {}
    def mv(l):
        if l not in mcache: mcache[l] = member(l[0], l[1])
        return mcache[l]
    def score(lams, npairs):
        vec = [mv(l) for l in lams] + [nprod(x, y) for x, y in npairs]
        inf, J = junk(vec)
        return 100 * inf + J, inf, J
    for rep in range(a.restarts):
      lams = [rmem() for _ in range(k)]
      npairs = [tuple(rnd.sample(NFORMS, 2)) for _ in range(p)]
      cur, ci, cj = score(lams, npairs)
      best = (cur, list(lams), list(npairs), ci, cj)
      t0 = time.time(); steps = 0
      while time.time() - t0 < a.seconds:
          steps += 1
          nl, nn = list(lams), list(npairs)
          if p and rnd.random() < p / (k + p):
              nn[rnd.randrange(p)] = tuple(rnd.sample(NFORMS, 2))
          else:
              j = rnd.randrange(k)
              if mix and rnd.random() < 0.3: nl[j] = (nl[j][0], rnd.choice(GOOD))
              elif rnd.random() < 0.5: nl[j] = (nl[j][0] ^ (1 << rnd.randrange(8)) or 1, nl[j][1])
              else: nl[j] = rmem()
          s, si, sj = score(nl, nn)
          temp = a.T0 * (1 - (time.time() - t0) / a.seconds) + 0.05
          if s <= cur or rnd.random() < math.exp((cur - s) / temp):
              lams, npairs, cur = nl, nn, s
              if s < best[0]:
                  best = (s, list(nl), list(nn), si, sj)
      s, bl, bn, bi, bj = best
      res = {'k': k, 'p': p, 'gamma': gamma, 'seed': a.seed, 'rep': rep, 'steps': steps, 'score': s, 'inf': bi,
             'J': bj, 'lams': bl, 'npairs': bn}
      if a.cover and bi == 0:
          vec = [mv(l) for l in bl] + [nprod(x, y) for x, y in bn]
          U = junk_space(vec)
          VN = [to_wedge(t) for t in NT if t]
          Uw = [to_wedge(u) for u in U]
          Fw = [to_wedge(f) for f in m_cap_x2(vec)]
          import cover_exact
          Fr = cover1.rowspace(Fw)
          tg = list(cover1.rowspace([cover1.reduce(v, Fr) for v in VN + Uw]).values())
          res['dimVNU'] = len(cover1.rowspace(VN + Uw)); res['dimfree'] = len(Fr); res['d'] = len(tg)
          import cover_s2
          for k1 in range(max(9, len(tg)), min(len(tg) + 2, a.maxl1) + 1):
              if k1 - len(tg) == 2: c, _ = cover_s2.cover2(VN + Uw, free=Fw)
              else: c = cover_exact.cover(VN + Uw, k1, free=Fw)
              res['cover%d' % k1] = c is not None
              if c is not None:
                  res['L1'] = c; res['total'] = k + p + k1 + 12; break
      if a.out:
          with open(a.out, 'a') as fh: fh.write(json.dumps(res) + chr(10))
      print(json.dumps(res), flush=True)


if __name__ == '__main__':
    main()
