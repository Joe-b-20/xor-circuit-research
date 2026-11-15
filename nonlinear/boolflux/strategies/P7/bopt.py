#!/usr/bin/env python3
"""P7: bottom optimiser for AD4 tower circuits at a gate-depth cap (rank-1 products, shared).

Model.  The front gives four base Y-forms Y_1..Y_4 (functions of N, gate level Lb).  Output j is
the bilinear tensor B_j (4 rows u_ij, 8-bit x-forms): y_j = c_j + sum_i Y_i u_ij(x).  A rank-1
product (alpha, w) = AND(Y_alpha, w), Y_alpha = sum_{i in alpha} Y_i (built by XORs: level
Lb + ceil(log2 |alpha|)), adds w to rows i in alpha.  Choose a product set P and per output a
subset S_j with sum = B_j, Kraft sum_{p in S_j} 2^(lev_p - D) <= 1 (product level = Y level + 1;
x-forms are early), |P| <= AMAX - front ANDs.  Cost (gates of the bottom):
  |P| + Y-sum XORs + new x-form XORs (>= 2 variables, not a front top-layer form) + sum_j (|S_j| - 1).

    bopt.py CIRCUIT --cap 12 --amax 45 [--iters 20000] [--seed 1] [--out plan.json] [--calib]
"""
import argparse, itertools, json, math, random, sys
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s1lib as L  # noqa: E402
import bsel  # noqa: E402
core = L.core


def base_front(c):
    T, lg, la = L.sim(c)
    n = c.n
    Ys = []
    for j, (op, a, b) in enumerate(c.gates):
        s = n + j
        if op in core.NONLINEAR_OPS and la[s] == 4:
            for o in (a, b):
                if L.deg(T[o]) > 1:
                    Ys.append((lg[o], T[o] ^ (L.ONES if T[o] & 1 else 0), o, T[o] & 1))
    Ys.sort()
    base = []
    for lv, t, s, pol in Ys:
        if all(t != b[1] for b in base) and bsel.gauss_solve([b[1] for b in base], t) is None:
            base.append((lv, t, s, pol))
        if len(base) == 4: break
    return T, lg, la, base


def mask_of(t):
    t = t ^ (L.ONES if t & 1 else 0)
    m = sum(1 << i for i in range(8) if (t >> (1 << i)) & 1)
    return m if L.lin_table(m) == t else None


def front_free_forms(c, T, la):
    """linear forms (masks) of top-layer gates that feed AND-level-1 gates (kept with the front)."""
    n = c.n; free = set()
    for j, (op, a, b) in enumerate(c.gates):
        if op in core.NONLINEAR_OPS and la[n + j] == 1:
            for o in (a, b):
                m = mask_of(T[o])
                if m is not None and bin(m).count('1') > 1: free.add(m)
    return free


def colspace(M):
    cols = set()
    for l in range(8):
        cols.add(sum(((M[i] >> l) & 1) << i for i in range(4)))
    # span
    sp = {0}
    for v in cols:
        sp |= {x ^ v for x in sp}
    return sp


def rank4(vs):
    piv = []
    for v in vs:
        for p in piv:
            v = min(v, v ^ p)
        if v: piv.append(v)
    return len(piv)


_BASES = {}
def bases_of(space):
    key = frozenset(space)
    if key in _BASES: return _BASES[key]
    nz = sorted(x for x in space if x)
    r = int(round(math.log2(len(space))))
    out = [S for S in itertools.combinations(nz, r) if rank4(S) == r]
    _BASES[key] = out
    return out


def decompose(M, A):
    """M (4 row masks) = sum_k alpha_k w_k^T with alphas A (basis of colspace(M))."""
    r = len(A)
    # express each column in basis A
    # build lookup: combination -> coefficients
    comb = {}
    for bits in range(1 << r):
        v = 0
        for k in range(r):
            if (bits >> k) & 1: v ^= A[k]
        comb[v] = bits
    w = [0] * r
    for l in range(8):
        col = sum(((M[i] >> l) & 1) << i for i in range(4))
        bits = comb[col]
        for k in range(r):
            if (bits >> k) & 1: w[k] |= 1 << l
    return [(A[k], w[k]) for k in range(r)]


def tensor(p):
    a, w = p
    return tuple(w if (a >> i) & 1 else 0 for i in range(4))


def tsub(M, p):
    a, w = p
    return tuple(M[i] ^ (w if (a >> i) & 1 else 0) for i in range(4))


class Model:
    def __init__(self, B, Lb, D, free, amax_bottom, ycost=None):
        self.B = B; self.Lb = Lb; self.D = D; self.free = free; self.amax = amax_bottom; self.pairs = True; self.pw = 0

    def ylev(self, a):
        k = bin(a).count('1')
        return max(self.Lb[i] for i in range(4) if (a >> i) & 1) + (0 if k == 1 else 1 if k == 2 else 2)

    def plev(self, p):
        return self.ylev(p[0]) + 1

    def kraft(self, S):
        return sum(2.0 ** (self.plev(p) - self.D) for p in S) <= 1 + 1e-9

    def cost(self, choice):
        P = set();
        for S in choice: P.update(S)
        al = {a for a, w in P if bin(a).count('1') >= 2}
        yc = 0
        for a in al:
            k = bin(a).count('1')
            if k == 2: yc += 1
            else:
                yc += 1 if any((a ^ (1 << i)) in al for i in range(4) if (a >> i) & 1) else 2
        xf0 = {w for a, w in P if bin(w).count('1') >= 2 and w not in self.free}
        av = set(self.free) | {1 << i for i in range(8)}
        rem = set(xf0); xc = 0
        while rem:
            got = [w for w in rem if any((w ^ a) in av for a in av)]
            if not got:
                w = min(rem); xc += 2; av.add(w); rem.discard(w); continue
            for w in got: av.add(w); rem.discard(w); xc += 1
        xf = range(xc)
        out = sum(len(S) - 1 for S in choice)
        if self.pairs:
            terms = [list(S) for S in choice]
            while True:
                cnt = Counter()
                for tl in terms:
                    for i1 in range(len(tl)):
                        for i2 in range(i1 + 1, len(tl)):
                            cnt[(tl[i1], tl[i2]) if str(tl[i1]) < str(tl[i2]) else (tl[i2], tl[i1])] += 1
                k, v = max(cnt.items(), key=lambda kv: kv[1], default=(None, 0))
                if v < 2: break
                out -= v - 1
                nk = ('pair', k)
                for tl in terms:
                    if k[0] in tl and k[1] in tl:
                        tl.remove(k[0]); tl.remove(k[1]); tl.append(nk)
        g = len(P) + yc + len(xf) + out
        over = max(0, len(P) - self.amax)
        return g + self.pw * len(P) + 1000 * over, len(P), yc, len(xf), out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circuit'); ap.add_argument('--cap', type=int, default=12)
    ap.add_argument('--amax', type=int, default=45); ap.add_argument('--iters', type=int, default=20000)
    ap.add_argument('--seed', type=int, default=1); ap.add_argument('--out', default=None)
    ap.add_argument('--T0', type=float, default=2.0); ap.add_argument('--init', default=None); ap.add_argument('--refine', action='store_true'); ap.add_argument('--refine2', action='store_true'); ap.add_argument('--top', type=int, default=40); ap.add_argument('--pw', type=float, default=0); ap.add_argument('--calib', action='store_true')
    a = ap.parse_args()
    c = L.load(a.circuit); n = c.n
    T, lg, la, base = base_front(c)
    Ys = [b[1] for b in base]; Lb = [b[0] for b in base]
    U, C = bsel.decompose_outputs(c, T, Ys)
    for j, (cst, v, yt) in enumerate(C):
        if v or yt: print('note: output %d has junk v=%02x yt=%x in the base decomposition' % (j, v, yt))
    B = [tuple(U[j][i] for i in range(4)) for j in range(8)]
    nfront = sum(1 for j, g in enumerate(c.gates) if g[0] in core.NONLINEAR_OPS and la[n + j] <= 3)
    free = front_free_forms(c, T, la)
    print('front ANDs %d, base Y levels %s, free top forms %d' % (nfront, Lb, len(free)))
    M = Model(B, Lb, a.cap, free, a.amax - nfront); M.pw = a.pw
    rng = random.Random(a.seed)

    if a.calib:
        # the circuit's own bottom in this model
        andsig = [n + j for j, g in enumerate(c.gates) if g[0] in core.NONLINEAR_OPS]
        import botclass
        os_ = botclass.outsets(c)
        prod = {}
        for s, js in os_.items():
            op, x, y = c.gates[s - n]
            ty = T[x] if L.deg(T[x]) > 1 else T[y]; tx = T[y] if ty is T[x] else T[x]
            ty0 = ty ^ (L.ONES if ty & 1 else 0)
            sol = bsel.gauss_solve(Ys, ty0)
            al = sum(1 << i for i in sol) if sol is not None else None
            prod[s] = (al, mask_of(tx))
        choice = [[prod[s] for s, js in os_.items() if j in js] for j in range(8)]
        ok = all(sum_t(S) == B[j] for j, S in enumerate(choice))
        print('calibration: own bottom tensors match:', ok, ' cost', M.cost(choice),
              ' kraft', [M.kraft(S) for S in choice])

    # initial: best single-output bases
    opts = []
    for j in range(8):
        oj = []
        for A in bases_of(colspace(B[j])):
            S = decompose(B[j], A)
            if M.kraft(S): oj.append(S)
        opts.append(oj)
    choice = [rng.choice(o) for o in opts]
    if a.init:
        choice = [[tuple(p) for p in S] for S in json.load(open(a.init))['choice']]
    cur = M.cost(choice); best = (cur, [list(S) for S in choice])
    T0 = a.T0
    for it in range(a.iters):
        Tt = T0 * (1 - it / a.iters) + 0.05
        j = rng.randrange(8)
        others = Counter(p for k, S in enumerate(choice) if k != j for p in S)
        pool = list(others)
        cand = []
        r = rng.random()
        if r < 0.3 or not pool:
            cand.append(rng.choice(opts[j]))
        else:
            ksz = rng.choice([1, 1, 2, 2, 3])
            R = rng.sample(pool, min(ksz, len(pool)))
            Mx = B[j]
            for p in R: Mx = tsub(Mx, p)
            if not any(Mx):
                cand.append(list(R))
            else:
                sp = colspace(Mx)
                bs = bases_of(sp)
                if len(bs) > 60: bs = rng.sample(bs, 60)
                for A in bs:
                    S = list(R) + decompose(Mx, A)
                    if len(set(S)) == len(S) and M.kraft(S): cand.append(S)
        if not cand: continue
        old = choice[j]
        bestc = None
        for S in cand:
            choice[j] = S
            cc = M.cost(choice)
            if bestc is None or cc < bestc[0]: bestc = (cc, S)
        cc, S = bestc
        if cc[0] <= cur[0] or rng.random() < math.exp(-(cc[0] - cur[0]) / Tt):
            choice[j] = S; cur = cc
            if cc < best[0]:
                best = (cc, [list(x) for x in choice])
                print('it %d: cost %d (P %d, ysum %d, xf %d, out %d)' % ((it,) + cc), flush=True)
        else:
            choice[j] = old
    cc, ch = best
    if a.refine:
        ch = [list(S) for S in ch]
        cur = M.cost(ch)
        improved = True; rnd = 0
        while improved:
            improved = False; rnd += 1
            for j in range(8):
                others = sorted({p for k, S in enumerate(ch) if k != j for p in S})
                subsets = [()] + [(p,) for p in others] + list(itertools.combinations(others, 2))
                old = ch[j]; bestj = (cur, old)
                for R in subsets:
                    Mx = B[j]
                    for p in R: Mx = tsub(Mx, p)
                    if not any(Mx):
                        cands = [list(R)]
                    else:
                        cands = []
                        for A in bases_of(colspace(Mx)):
                            S = list(R) + decompose(Mx, A)
                            if len(set(S)) == len(S): cands.append(S)
                    for S in cands:
                        if not M.kraft(S): continue
                        ch[j] = S
                        c2 = M.cost(ch)
                        if c2 < bestj[0]: bestj = (c2, S)
                ch[j] = bestj[1]
                if bestj[0] < cur:
                    cur = bestj[0]; improved = True
                    print('refine round %d output %d: cost %s' % (rnd, j, cur), flush=True)
        cc = cur
    if a.refine2:
        ch = [list(S) for S in ch]
        cur = M.cost(ch)

        def cands_for(j, top):
            others = sorted({p for k, S in enumerate(ch) if k != j for p in S})
            subsets = [()] + [(p,) for p in others]
            out = []
            old = ch[j]
            for R in subsets:
                Mx = B[j]
                for p in R: Mx = tsub(Mx, p)
                cs = [list(R)] if not any(Mx) else [list(R) + decompose(Mx, A) for A in bases_of(colspace(Mx))]
                for S in cs:
                    if len(set(S)) != len(S) or not M.kraft(S): continue
                    ch[j] = S; out.append((M.cost(ch), S))
            ch[j] = old
            out.sort(key=lambda t: t[0])
            uniq = []; seen = set()
            for c2, S in out:
                key = tuple(sorted(S))
                if key in seen: continue
                seen.add(key); uniq.append(S)
                if len(uniq) >= top: break
            return uniq
        improved = True; rnd = 0
        while improved and rnd < 4:
            improved = False; rnd += 1
            for j in range(8):
                for k in range(j + 1, 8):
                    cj = cands_for(j, a.top); ck = cands_for(k, a.top)
                    # candidates of k that use products of cj are only found if k's pool contains them:
                    # also add k-candidates computed with j set to each of its top-5
                    oj, ok = ch[j], ch[k]
                    for Sj in cj[:5]:
                        ch[j] = Sj; ck += cands_for(k, 20)
                    ch[j] = oj
                    best = (cur, oj, ok)
                    for Sj in cj:
                        ch[j] = Sj
                        for Sk in ck:
                            ch[k] = Sk
                            c2 = M.cost(ch)
                            if c2 < best[0]: best = (c2, Sj, Sk)
                    ch[j], ch[k] = best[1], best[2]
                    if best[0] < cur:
                        cur = best[0]; improved = True
                        print('refine2 round %d pair (%d,%d): cost %s' % (rnd, j, k, cur), flush=True)
        cc = cur
    print('BEST', cc, '-> bottom ANDs %d, A = %d' % (cc[1], cc[1] + nfront))
    for j, S in enumerate(ch):
        print(' y%d:' % j, ' '.join('(%x,%02x)L%d' % (p[0], p[1], M.plev(p)) for p in S))
    if a.out:
        json.dump({'circuit': a.circuit, 'cap': a.cap, 'amax': a.amax, 'Lb': Lb, 'cost': cc,
                   'choice': [[list(p) for p in S] for S in ch], 'C': C}, open(a.out, 'w'))


def sum_t(S):
    M = (0, 0, 0, 0)
    for p in S: M = tsub(M, p)
    return M


if __name__ == '__main__':
    main()
