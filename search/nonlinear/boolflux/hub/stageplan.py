"""stageplan: stage accounting of S-box circuits and planned joins (idea 03, from U6 #4/#7).

Stage split (U6work/feat.py): A = s1 + s2 + s3 with s3 = terminal ANDs (no AND among their successors),
s1 = level-1 non-terminal ANDs (first-level products), s2 = the rest (the middle).  Every AND class we made
by recombination so far is a sum of stage minima of two families (31/5 = 9+5+17).

Planned join (exact, by linear algebra on the 256-entry truth tables).  For a front circuit X and a back
circuit Y cut above AND level LY:
  * the cut of Y = Y's signals of AND level <= LY read by a gate above LY (or outputs of level <= LY);
  * every cut function must lie in the affine span of X's inputs and ANDs (ONE basis per circuit, all
    levels: the AND level of X's front is not a parameter, it follows from what Y's cut needs);
  * needed = the X ANDs in the supports of the cut functions, closed under X's DAG fan-in;
  * result A = |needed| + (Y's ANDs above LY); AND depth from X's levels of the supports pushed through
    Y's back.  The build (minimal-support join) reuses join.join with X's linear signals restricted to
    those whose AND fan-in lies inside `needed`, so unneeded X ANDs never become live (a blind join's
    greedy interface may route through an X signal containing an AND that cancels, and keeps it).
When X's ANDs are linearly independent modulo the affine input functions (checked: Tagged.indep), the
support of a cut function is unique, so |needed| is the minimum over joins that keep X's AND gates.

Pools: archives (DIR/archive/index.jsonl + <id>.bfx), circuit files (.circ.txt / .bfx) and directories
of them; forward and inverse circuits are told apart by their value table.  --transport adds the other
direction's circuits through ops/transport.py maps (same ANDs, the inputs/outputs re-mapped by
balanced XOR trees, transport.wrap): their G is inflated, the join result is polished afterwards.

CLI:
  stageplan.py tag  POOL... --out FILE.jsonl            tags (stage split, profiles) per circuit
  stageplan.py plan POOL... --function F --out DIR      target pairs (plan.jsonl) + a summary
  stageplan.py blind POOL... --function F --seconds T   blind joins (hub join_all on random pairs), for the A/B
No 27-AND work: targets are classes with A >= --min-a (default 28; values below 28 are refused).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import time
from pathlib import Path
from types import SimpleNamespace

from .common import core, aesfn, ONES, clean, metrics, structure_key, leq
from . import join as J

NL = core.NONLINEAR_OPS
MIN_A = 28


def canon(t):
    return min(t, t ^ ONES)


def _bits(m):
    while m:
        b = m & -m
        yield b.bit_length() - 1
        m ^= b


class Tagged:
    """One circuit: tables, AND levels, live ANDs, stage split, profiles, AND basis, cuts."""

    def __init__(self, c, ident=None, src=None, origin='native'):
        c = c.live()
        self.c = c; self.id = ident; self.src = src; self.origin = origin
        n = c.n; self.n = n
        self.t = c.tables(); self.l = J.levels(c)
        gd = [0] * n
        for op, a, b in c.gates: gd.append(max(gd[a], gd[b]) + 1)
        self.gdl = gd
        self.ands = [n + j for j, g in enumerate(c.gates) if g[0] in NL]
        self.aidx = {s: i for i, s in enumerate(self.ands)}
        self.A = len(self.ands); self.G = len(c.gates)
        self.AD = max(self.l[o] for o in c.outputs); self.GD = max(gd[o] for o in c.outputs)
        fin = [0] * n                                   # AND fan-in (DAG) of every signal, bitmask over self.ands
        for j, (op, a, b) in enumerate(c.gates):
            m = fin[a] | fin[b]
            if op in NL: m |= 1 << self.aidx[n + j]
            fin.append(m)
        self.fin = fin
        # basis: bit 0 ONE, bits 1..n inputs, bits n+1+i AND i (join.Front convention with every AND)
        self.piv = []; self.indep = True
        basis = [ONES] + [self.t[i] for i in range(n)] + [self.t[s] for s in self.ands]
        for i, t in enumerate(basis):
            f = 1 << i
            for p, rt, rf in self.piv:
                if (t >> p) & 1: t ^= rt; f ^= rf
            if t:
                self.piv.append((t.bit_length() - 1, t, f)); self.piv.sort(key=lambda r: -r[0])
            elif i > n:
                self.indep = False
        self._stages()
        self._cuts = {}

    # ---- tags -------------------------------------------------------------------------------
    def _stages(self):
        n = self.n; c = self.c
        below = [False] * (n + len(c.gates))           # an AND among the transitive successors
        for j in range(len(c.gates) - 1, -1, -1):
            op, a, b = c.gates[j]; s = n + j
            v = below[s] or op in NL
            for u in (a, b):
                if v: below[u] = True
        s3 = sum(1 for s in self.ands if not below[s])
        s1 = sum(1 for s in self.ands if self.l[s] == 1 and below[s])
        self.stages = (s1, self.A - s1 - s3, s3)
        self.and_prof = [sum(1 for s in self.ands if self.l[s] == k) for k in range(1, self.AD + 1)]
        self.lin_prof = [sum(1 for j, g in enumerate(c.gates) if g[0] not in NL and self.l[n + j] == k)
                         for k in range(self.AD + 1)]

    def tag(self):
        return {'id': self.id, 'src': self.src, 'origin': self.origin, 'A': self.A, 'AD': self.AD, 'G': self.G,
                'GD': self.GD, 'stages': list(self.stages), 'and_prof': self.and_prof, 'lin_prof': self.lin_prof,
                'indep': self.indep, 'fkey': self.front_key()}

    def front_key(self):
        """the AND functions with their levels and fan-in sets (canonical up to complement): circuits with the same
        key offer the same fronts to every back"""
        if not hasattr(self, '_fkey'):
            h = hashlib.blake2b(digest_size=10)
            rows = []
            for s in self.ands:
                fi = sorted(canon(self.t[self.ands[i]]) for i in _bits(self.fin[s]))
                rows.append((canon(self.t[s]), self.l[s], tuple(fi)))
            for r in sorted(rows): h.update(repr(r).encode())
            self._fkey = h.hexdigest()
        return self._fkey

    # ---- linear algebra -----------------------------------------------------------------------
    def form(self, t):
        f = 0
        for p, rt, rf in self.piv:
            if (t >> p) & 1: t ^= rt; f ^= rf
        return f if t == 0 else None

    def cut(self, LY):
        """(cut signals, back ANDs, back key) of the back above AND level LY"""
        if LY in self._cuts: return self._cuts[LY]
        n = self.n; c = self.c; need = set()
        for j, (op, a, b) in enumerate(c.gates):
            if self.l[n + j] > LY:
                for o in (a, b):
                    if o >= n and self.l[o] <= LY: need.add(o)
        for o in c.outputs:
            if o >= n and self.l[o] <= LY: need.add(o)
        cut = sorted(need)
        backA = sum(1 for s in self.ands if self.l[s] > LY)
        lab = {i: 'i%d' % i for i in range(n)}
        for s in cut: lab[s] = 'c%x' % canon(self.t[s])
        h = hashlib.blake2b(digest_size=10); h.update(b'%d|' % LY)
        for j, (op, a, b) in enumerate(c.gates):
            s = n + j
            if self.l[s] <= LY: continue
            lab[s] = 'g%d' % j
            h.update(('%d,%s,%s;' % (op, lab.get(a, '?'), lab.get(b, '?'))).encode())
        for o in c.outputs: h.update(lab.get(o, '?').encode() + b',')
        r = (cut, backA, h.hexdigest())
        self._cuts[LY] = r
        return r


def plan_pair(X, Y, LY):
    """exact prediction of the minimal-support join of X's front and Y's back above LY:
    None (Y's cut not in X's span) or dict(A, AD, need mask, cut forms)"""
    cut, backA, _ = Y.cut(LY)
    n = X.n; need = 0; forms = {}
    for s in cut:
        f = X.form(Y.t[s])
        if f is None: return None
        forms[s] = f; need |= f >> (n + 1)
    clo = need
    for i in _bits(need): clo |= X.fin[X.ands[i]]
    # AND depth: cut level = highest X level among the support's DAG closure, pushed through Y's back
    lev = {i: 0 for i in range(n)}
    for s, f in forms.items():
        m = f >> (n + 1); m2 = m
        for i in _bits(m): m2 |= X.fin[X.ands[i]]
        lev[s] = max((X.l[X.ands[i]] for i in _bits(m2)), default=0)
    for j, (op, a, b) in enumerate(Y.c.gates):
        s = n + j
        if Y.l[s] <= LY: continue
        lev[s] = max(lev[a], lev[b]) + (1 if op in NL else 0)
    AD = max(lev[o] for o in Y.c.outputs)
    return {'A': bin(clo).count('1') + backA, 'AD': AD, 'need': clo, 'xa': bin(clo).count('1'), 'ya': backA}


def build_pair(X, Y, LY, need=None):
    """minimal-support join: X's gates + interface XORs from X's linear signals whose AND fan-in lies in `need`
    + Y's back above LY; cleaned.  None if the build fails."""
    if need is None:
        p = plan_pair(X, Y, LY)
        if p is None: return None
        need = p['need']
    have = {}
    for s in range(X.n + len(X.c.gates)):
        if X.fin[s] & ~need: continue
        if s >= X.n and X.c.gates[s - X.n][0] in NL and not (need >> X.aidx[s]) & 1: continue
        f = X.form(X.t[s])
        if f is not None and f not in have: have[f] = s
    shim = SimpleNamespace(X=X.c, have=have, form=X.form)
    Yp = SimpleNamespace(c=Y.c, t=Y.t, l=Y.l)
    c, nint = J.join(shim, Yp, LY)
    if c is None: return None
    return clean(c)


# ---- pools --------------------------------------------------------------------------------------

def _load_any(p):
    p = Path(p)
    if p.suffix == '.bfx': return core.from_kernel(p.read_text(), name=p.stem)
    return core.read_ncff(str(p))


def iter_pool(spec):
    """yield (circuit, id, src) for an archive dir (DIR/archive/index.jsonl), a directory of circuit files
    (recursive *.circ.txt, *.bfx) or one file"""
    p = Path(os.path.expanduser(spec))
    ix = p / 'archive' / 'index.jsonl'
    if ix.exists():
        for ln in ix.read_text().splitlines():
            try: r = json.loads(ln)
            except Exception: continue
            f = p / 'archive' / (r['id'] + '.bfx')
            if f.exists(): yield _load_any(f), r['id'], str(p)
        return
    files = [p] if p.is_file() else sorted(list(p.rglob('*.circ.txt')) + list(p.rglob('*.bfx')))
    for f in files:
        if f.name.startswith('start') or f.name.startswith('best'): continue
        try: c = _load_any(f)
        except Exception: continue
        yield c, f.name.split('.')[0][:60], str(f)


def which_function(c):
    try:
        v = tuple(c.value_table())
    except Exception:
        return None
    for fn in ('aes-sbox', 'aes-invsbox'):
        if v == aesfn.table(fn): return fn
    return None


def load_pools(specs, function, transport=False, maps=('1:0',), log=print):
    """Tagged circuits computing `function` (deduplicated by structure; --transport also the other direction's,
    re-mapped).  Returns list of Tagged."""
    own, other = [], []
    seen = set()
    for spec in specs:
        k0 = len(own) + len(other)
        for c, ident, src in iter_pool(spec):
            if (c.n, c.m) != (8, 8): continue
            fn = which_function(c)
            if fn is None: continue
            cc = clean(c.live()); sk = structure_key(cc)
            if sk in seen: continue
            seen.add(sk)
            (own if fn == function else other).append((cc, ident, src))
        log('pool %s: %d circuits' % (spec, len(own) + len(other) - k0))
    out = [Tagged(c, i, s) for c, i, s in own]
    if transport and other:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ops'))
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ops' / 'conj_lib'))
        import transport as TR
        src_fn = 'aes-invsbox' if function == 'aes-sbox' else 'aes-sbox'
        # one transported copy per distinct AND structure (front key), fewest G first
        byk = {}
        for c, i, s in other:
            T = Tagged(c, i, s)
            k = T.front_key()
            if k not in byk or T.G < byk[k][0].G: byk[k] = (T, c, i, s)
        for spec in maps:
            lam, k = (int(x) for x in spec.split(':'))
            In, cin, Out, cout = TR.maps(src_fn, lam, k)
            for T, c, i, s in byk.values():
                w = clean(TR.wrap(c, In, cin, Out, cout))
                out.append(Tagged(w, '%s@T%s' % (i, spec), s, origin='transport %s' % spec))
        log('transported %d circuits (%d distinct AND structures x %d maps)' % (len(byk) * len(maps), len(byk), len(maps)))
    return out


# ---- targets ------------------------------------------------------------------------------------

def known_points(pool, extra=()):
    pts = set((T.A, T.AD, T.G, T.GD) for T in pool if T.origin == 'native')
    pts |= set(extra)
    return pts


def classify(A, AD, pts, min_a=MIN_A):
    """'reach' (no known circuit with A' <= A and AD' <= AD), 'new-class' (no known (A, AD)), None"""
    if A < min_a: return None
    if not any(p[0] <= A and p[1] <= AD for p in pts): return 'reach'
    if not any(p[0] == A and p[1] == AD for p in pts): return 'new-class'
    return None


def class_room(A, AD, pts):
    """the fewest G among known circuits dominating the class's (A, AD) box (A' <= A, AD' <= AD) at each GD:
    a new-class circuit must beat these to be on the front"""
    box = [p for p in pts if p[0] <= A and p[1] <= AD]
    return min((p[2] for p in box), default=None)


def rref(vecs):
    """fully reduced row echelon basis (tuple of (pivot, row), pivots descending): a canonical key of the span"""
    rows = []
    for t in vecs:
        for p, r in rows:
            if (t >> p) & 1: t ^= r
        if t:
            p = t.bit_length() - 1
            rows = [(q, r ^ t if (r >> p) & 1 else r) for q, r in rows]
            rows.append((p, t)); rows.sort(key=lambda x: -x[0])
    return tuple(rows)


def in_span(rows, t):
    for p, r in rows:
        if (t >> p) & 1: t ^= r
    return t == 0


def make_plan(pool, pts, min_a=MIN_A, log=print, reps=2):
    """Every (front, back) pair whose minimal-support join lands in a target class.  Fronts are grouped by the
    span V of (ONE, inputs, ANDs), backs by (LY, span W of their cut, back AND count); feasibility (W inside V)
    is tested once per (V, W) group pair, then plan_pair runs on up to `reps` representatives of each side
    (fewest G; lowest GD)."""
    if min_a < MIN_A: raise SystemExit('refused: no 27-AND work (min_a %d < %d)' % (min_a, MIN_A))
    if not pool: return [], {}, {}
    aff = [ONES] + [pool[0].t[i] for i in range(pool[0].n)]
    t0 = time.time()
    fronts = {}
    for T in pool:
        fronts.setdefault(rref(aff + [T.t[s] for s in T.ands]), []).append(T)
    backs = {}
    for T in pool:
        for LY in range(1, T.AD):
            cut, backA, bk = T.cut(LY)
            w = rref(aff + [T.t[s] for s in cut])
            backs.setdefault((LY, w), {}).setdefault(backA, []).append(T)
    def pick(Ts):
        a = min(Ts, key=lambda T: (T.G, T.GD)); b = min(Ts, key=lambda T: (T.GD, T.G))
        return [a] if (reps < 2 or a is b) else [a, b]
    log('front spans %d, cut spans %d (pool %d), %.1f s' % (len(fronts), len(backs), len(pool), time.time() - t0))
    rows = []; tested = 0; feasible = 0; evals = 0
    affrows = rref(aff)
    wvec = {k: [r for p, r in k[1] if not in_span(affrows, r)] for k in backs}     # the cut rows outside the affine span
    for V, Xs in fronts.items():
        xr = pick(Xs)
        for (LY, W), byA in backs.items():
            tested += 1
            if not all(in_span(V, r) for r in wvec[(LY, W)]): continue
            feasible += 1
            for backA, Ys in byA.items():
                for X in xr:
                    for Y in pick(Ys):
                        evals += 1
                        p = plan_pair(X, Y, LY)
                        if p is None: continue
                        kind = classify(p['A'], p['AD'], pts, min_a)
                        if kind is None: continue
                        rows.append({'A': p['A'], 'AD': p['AD'], 'kind': kind, 'xa': p['xa'], 'ya': p['ya'], 'LY': LY,
                                     'X': X.id, 'Y': Y.id, 'Xorigin': X.origin, 'Yorigin': Y.origin,
                                     'Xtup': [X.A, X.AD, X.G, X.GD], 'Ytup': [Y.A, Y.AD, Y.G, Y.GD],
                                     'Xst': list(X.stages), 'Yst': list(Y.stages),
                                     'room': class_room(p['A'], p['AD'], pts)})
    log('span pairs tested %d, feasible %d, plan_pair evaluations %d, target rows %d, %.1f s'
        % (tested, feasible, evals, len(rows), time.time() - t0))
    return rows, fronts, backs


# ---- CLI ----------------------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('cmd', choices=('tag', 'plan'))
    ap.add_argument('pools', nargs='+')
    ap.add_argument('--function', default='aes-sbox', choices=('aes-sbox', 'aes-invsbox'))
    ap.add_argument('--transport', action='store_true')
    ap.add_argument('--maps', default='1:0')
    ap.add_argument('--min-a', type=int, default=MIN_A)
    ap.add_argument('--out', required=True)
    ap.add_argument('--pkl', help='load the pool from this pickle if it exists, else build it and save it here')
    a = ap.parse_args(argv)
    if a.pkl and os.path.exists(a.pkl):
        import pickle
        pool = pickle.load(open(a.pkl, 'rb'))
    else:
        pool = load_pools(a.pools, a.function, a.transport, a.maps.split(','))
        if a.pkl:
            import pickle
            pickle.dump(pool, open(a.pkl, 'wb'))
    if a.cmd == 'tag':
        with open(a.out, 'w') as f:
            for T in pool: f.write(json.dumps(T.tag()) + '\n')
        return
    pts = known_points(pool)
    rows, fronts, backs = make_plan(pool, pts, a.min_a)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    with open(out / 'plan.jsonl', 'w') as f:
        for r in rows: f.write(json.dumps(r) + '\n')
    with open(out / 'tags.jsonl', 'w') as f:
        for T in pool: f.write(json.dumps(T.tag()) + '\n')
    summ = {}
    for r in rows:
        k = '%d/%d %s' % (r['A'], r['AD'], r['kind'])
        summ[k] = summ.get(k, 0) + 1
    print(json.dumps(dict(sorted(summ.items())), indent=0))


if __name__ == '__main__':
    main()
