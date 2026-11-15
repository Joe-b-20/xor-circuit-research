#!/usr/bin/env python3
"""Quadratic flip-graph walk on the bottom (last AND level) of an AD4 BP-family AES circuit.

Variables: bit 0 = constant 1, bits 1..8 = input bits x0..x7, bits 9..12 = Y basis y0..y3 (the Y basis of
REF; the Y function space is the same in every BP-family circuit).  A term is (L, R, w): an AND of the
affine forms L, R (13-bit masks) feeding the outputs in w (8-bit mask).  Free terms = last-level ANDs
(counted); fixed terms = the start circuit's level-1 ANDs (they exist in the front; a nonzero w only
means an extra XOR in the output layer).  Invariant: sum over all terms of w (x) L*R == the outputs
minus constants (exact as functions: the 1 + 12 + 66 monomials are independent on the 256 inputs).

Moves (each preserves the sum exactly):
  share flip    terms i, j with a common operand F:  F*Ri.wi + F*Rj.wj = F*(Ri+Rj).wi + F*Rj.(wi+wj)
                (j may be a fixed term: its operands stay, only its w changes)
  w flip        terms i, j (free) with wi == wj: Li*Ri + Lj*Rj = (Li+Lj)*Ri + Lj*(Ri+Rj)
  self          L*R = L*(L+R+1)
  plus          F*R.w = F*R'.w + F*(R+R').w   (rank + 1, only below --maxrank)
  reductions    w == 0 or an operand 0 -> drop; operand == 1 -> linear term (no AND, moved to `lin`);
                equal product functions -> merge w.
    qflip.py walk REF START --steps N --seed S --target R --out DIR [--plus-every K] [--maxrank M]
"""
import json, random, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import bottom as BT  # noqa
import flip as FL   # noqa

NV = 13


def prodfun(L, R):
    """Function of L*R as (quad rows tuple, linear mask incl const bit 0)."""
    lin = 0
    if L & 1 and R & 1: lin |= 1
    for a in range(1, NV):
        la = L >> a & 1; ra = R >> a & 1
        if (L & 1 and ra) ^ (la and R & 1) ^ (la and ra): lin |= 1 << a
    rows = []
    for a in range(1, NV):
        r = 0
        if L >> a & 1: r ^= R
        if R >> a & 1: r ^= L
        rows.append((r >> (a + 1)) << (a + 1))
    return tuple(rows), lin


def decompose(c, Yt):
    """All last-level ANDs as free terms, level-1 ANDs as fixed terms, w from the output layer."""
    T = c.tables()
    B = FL.basis_for(Yt, c.n)
    la, lg = BT.and_levels(c)
    AD = max(la[s] for s in c.outputs)
    free, fixed = [], []
    sig = []
    for j, (op, a, b) in enumerate(c.gates):
        if op not in BT.NL: continue
        if la[c.n + j] == AD or la[c.n + j] == 1:
            fa = B.coords(T[a]); fb = B.coords(T[b])
            assert fa is not None and fb is not None, 'operand outside span(1, X, Y)'
            (free if la[c.n + j] == AD else fixed).append([fa, fb, 0])
            sig.append((la[c.n + j] == AD, len(free if la[c.n + j] == AD else fixed) - 1, c.n + j))
    # output w: solve outputs over span(products, 1, x, y): build basis of product tables + linear
    PB = BT.Basis()
    names = []
    for isfree, k, s in sig:
        if PB.add(T[s], ('F' if isfree else 'X', k)): names.append(('F' if isfree else 'X', k))
    lin_names = []
    from boolflux import core  # noqa
    xs = core.input_tables(c.n)
    lin_tabs = [BT.ONES] + xs + list(Yt)
    for b, t in enumerate(lin_tabs):
        PB.add(t, ('L', b))
    lin = [0] * 8
    for o, s in enumerate(c.outputs):
        cb = PB.coords(T[s]); assert cb is not None, 'output outside span'
        for k, nm in enumerate(PB.names):
            if cb >> k & 1:
                if nm[0] == 'F': free[nm[1]][2] |= 1 << o
                elif nm[0] == 'X': fixed[nm[1]][2] |= 1 << o
                else: lin[o] |= 1 << nm[1]
    return [tuple(t) for t in free], [tuple(t) for t in fixed], lin


def total(free, fixed, lin):
    """Per output: (quad rows, lin) of the sum."""
    out = []
    for o in range(8):
        rows = [0] * (NV - 1); l = lin[o]
        for L, R, w in list(free) + list(fixed):
            if w >> o & 1:
                q, li = prodfun(L, R)
                rows = [x ^ y for x, y in zip(rows, q)]; l ^= li
        out.append((tuple(rows), l))
    return out


class State:
    def __init__(self, free, fixed, lin):
        self.free = list(free); self.fixed = list(fixed); self.lin = list(lin)

    def add_lin(self, f, w):
        for o in range(8):
            if w >> o & 1: self.lin[o] ^= f

    def reduce(self):
        changed = True
        while changed:
            changed = False
            keep = []
            for L, R, w in self.free:
                if w == 0 or L == 0 or R == 0: changed = True; continue
                if L == 1: self.add_lin(R, w); changed = True; continue
                if R == 1: self.add_lin(L, w); changed = True; continue
                keep.append((L, R, w))
            self.free = keep
            # merge equal product functions (free-free, and free into fixed)
            seen = {}
            for k, (L, R, w) in enumerate(self.fixed):
                seen[prodfun(L, R)] = ('X', k)
            new = []
            for L, R, w in self.free:
                f = prodfun(L, R)
                if f in seen:
                    kind, k = seen[f]
                    if kind == 'X':
                        L2, R2, w2 = self.fixed[k]; self.fixed[k] = (L2, R2, w2 ^ w)
                    else:
                        L2, R2, w2 = new[k]; new[k] = (L2, R2, w2 ^ w)
                    changed = True
                else:
                    seen[f] = ('F', len(new)); new.append((L, R, w))
            self.free = new

    def rank(self):
        return len(self.free)


def ops_of(t):
    return (t[0], t[1])


def share_moves(st):
    """(i, j, Fi_is_L, Fj_is_L, j_fixed) where free term i and term j share an operand."""
    out = []
    idx = {}
    for i, (L, R, w) in enumerate(st.free):
        idx.setdefault(L, []).append(('F', i, 0)); idx.setdefault(R, []).append(('F', i, 1))
    for k, (L, R, w) in enumerate(st.fixed):
        idx.setdefault(L, []).append(('X', k, 0)); idx.setdefault(R, []).append(('X', k, 1))
    for F_, lst in idx.items():
        if len(lst) < 2: continue
        for a in lst:
            if a[0] != 'F': continue
            for b in lst:
                if b == a or (b[0] == 'F' and b[1] == a[1]): continue
                out.append((a, b))
    return out


def apply_share(st, a, b):
    """a = ('F', i, side) changes operand; b keeps operands and changes w."""
    _, i, sa = a
    L, R, w = st.free[i]
    Fop = L if sa == 0 else R
    Ri = R if sa == 0 else L
    if b[0] == 'F':
        L2, R2, w2 = st.free[b[1]]
    else:
        L2, R2, w2 = st.fixed[b[1]]
    Rj = R2 if b[2] == 0 else L2
    st.free[i] = (Fop, Ri ^ Rj, w)
    nb = (L2, R2, w2 ^ w)
    if b[0] == 'F': st.free[b[1]] = nb
    else: st.fixed[b[1]] = nb


def step(st, rng, maxrank, plus_p):
    n = len(st.free)
    r = rng.random()
    if r < plus_p and n < maxrank:
        i = rng.randrange(n); L, R, w = st.free[i]
        Rp = rng.randrange(2, 1 << NV)
        if rng.random() < 0.5: st.free[i] = (L, Rp, w); st.free.append((L, R ^ Rp, w))
        else: st.free[i] = (Rp, R, w); st.free.append((L ^ Rp, R, w))
        return 'plus'
    if r < plus_p + 0.05:
        i = rng.randrange(n); L, R, w = st.free[i]
        st.free[i] = (L, L ^ R ^ 1, w) if rng.random() < 0.5 else (R ^ L ^ 1, R, w)
        return 'self'
    if r < plus_p + 0.15:
        byw = {}
        for i, t in enumerate(st.free): byw.setdefault(t[2], []).append(i)
        cands = [v for v in byw.values() if len(v) > 1]
        if cands:
            v = rng.choice(cands); i, j = rng.sample(v, 2)
            Li, Ri, w = st.free[i]; Lj, Rj, _ = st.free[j]
            if rng.random() < 0.5: Li, Ri = Ri, Li
            if rng.random() < 0.5: Lj, Rj = Rj, Lj
            st.free[i] = (Li ^ Lj, Ri, w); st.free[j] = (Lj, Ri ^ Rj, w)
            return 'wflip'
    M = share_moves(st)
    if not M: return None
    a, b = rng.choice(M)
    apply_share(st, a, b)
    return 'share'


def canon(st):
    return tuple(sorted((min(L, R), max(L, R), w) for L, R, w in st.free)), tuple(w for _, _, w in st.fixed)


def main():
    a = sys.argv[1:]
    ref, f = a[1], a[2]
    steps = int(a[a.index('--steps') + 1]); seed = int(a[a.index('--seed') + 1])
    target = int(a[a.index('--target') + 1]); out = Path(a[a.index('--out') + 1]); out.mkdir(parents=True, exist_ok=True)
    plus_p = float(a[a.index('--plus') + 1]) if '--plus' in a else 0.002
    maxrank = int(a[a.index('--maxrank') + 1]) if '--maxrank' in a else 19
    rc, Yt = FL.ref_basis(ref)
    c = BT.load(f)
    free, fixed, lin = decompose(c, Yt)
    goal = total(free, fixed, lin)
    st = State(free, fixed, lin); st.reduce()
    assert total(st.free, st.fixed, st.lin) == goal
    print('start rank', st.rank(), 'fixed', len(st.fixed), flush=True)
    rng = random.Random(seed)
    log = open(out / ('qwalk-s%d.jsonl' % seed), 'a')
    found = set(); best = st.rank(); t0 = time.time()
    for it in range(steps):
        prev = (list(st.free), list(st.fixed), list(st.lin))
        mv = step(st, rng, maxrank, plus_p)
        st.reduce()
        if st.rank() == 0:
            st.free, st.fixed, st.lin = prev; continue
        r = st.rank()
        if r <= target:
            k = canon(st)
            if k not in found:
                assert total(st.free, st.fixed, st.lin) == goal
                found.add(k)
                log.write(json.dumps({'it': it, 't': round(time.time() - t0, 1), 'rank': r, 'free': st.free,
                                      'fixed': st.fixed, 'lin': st.lin}) + '\n'); log.flush()
        if r < best:
            best = r; print('it %d rank %d (%.1fs)' % (it, r, time.time() - t0), flush=True)
        if it % 200000 == 0 and it:
            assert total(st.free, st.fixed, st.lin) == goal
            print('it %d rank %d found %d (%.1fs)' % (it, r, len(found), time.time() - t0), flush=True)
    print('end best', best, 'found', len(found))


if __name__ == '__main__':
    main()
