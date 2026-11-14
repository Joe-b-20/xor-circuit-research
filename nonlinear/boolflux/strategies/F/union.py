#!/usr/bin/env python3
"""Union-graph recombination of AES S-box circuits under a gate-depth cap (track F).

Every gate of every circuit in a pool is a hyperedge (op, f_a, f_b) -> f over complete truth
tables (256-bit ints).  Gates from different circuits combine whenever their operand functions
are available, so the union graph contains every "splice" of the pool (front of one circuit,
back of another, at any cut whose functions coincide).  We select a cover of the 8 outputs
with gate depth <= D and few gates, by depth-constrained technology mapping:

  1. min arrival of every function over the union (relaxation to a fixpoint);
  2. depth-optimal cover, then area recovery: forward passes choosing, for every function in the
     cover, the hyperedge with the least area flow / exact local area whose arrival meets the
     function's required level (from the current cover, cap D at the outputs);
  3. randomised tie-breaking and edge-cost noise for diversity (seed).

    python3 union.py --cap 14 --pool FILE_OR_GLOB ... --out OUT.circ.txt [--seeds 1-20]

The result is checked on all 256 inputs here; run aes_check.py on anything reported.
"""
import argparse
import glob
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core, targets   # noqa: E402

AESTAB = targets.aes_sbox()
NIST = core.Model.load(str(core.MODELS / "nist.json"))
ALLOWED = {8, 6, 9, 3}          # AND XOR XNOR NOT
INF = 10 ** 9


def load_pool(specs, verbose=True):
    files = []
    for s in specs:
        files += sorted(glob.glob(s, recursive=True)) if any(ch in s for ch in '*?[') else [s]
    circs = []; seen = set()
    for f in files:
        try:
            c = core.read_ncff(f)
        except Exception:
            continue
        if c.n != 8 or c.m != 8: continue
        if any(op not in ALLOWED for op, a, b in c.gates): continue
        if c.value_table() != AESTAB: continue
        key = tuple(c.gates), tuple(c.outputs)
        if key in seen: continue
        seen.add(key); circs.append((f, c))
    if verbose: print('pool: %d circuits from %d files' % (len(circs), len(files)), file=sys.stderr)
    return circs


class Union:
    def __init__(self, circs):
        n = 8
        self.ones = (1 << 256) - 1
        ins = core.input_tables(n)
        self.fid = {}; self.ftab = []
        for t in ins: self._id(t)
        self.edges = {}            # (op, ia, ib) -> out id
        self.outs = None
        for f, c in circs:
            tabs = c.tables()
            ids = [self._id(t) for t in tabs]
            for j, (op, a, b) in enumerate(c.gates):
                ia, ib = ids[a], ids[b]
                if op in (8, 6, 9) and ia > ib: ia, ib = ib, ia
                if op == 3: ib = ia
                self.edges[(op, ia, ib)] = ids[n + j]
            outs = [ids[s] for s in c.outputs]
            assert self.outs is None or self.outs == outs
            self.outs = outs
        self.n = n; self.F = len(self.ftab)
        self.by_out = [[] for _ in range(self.F)]
        for (op, a, b), o in self.edges.items():
            if o in (a, b): continue
            self.by_out[o].append((op, a, b))
        print('union: %d functions, %d gates (hyperedges)' % (self.F, len(self.edges)), file=sys.stderr)

    def _id(self, t):
        i = self.fid.get(t)
        if i is None:
            i = len(self.ftab); self.fid[t] = i; self.ftab.append(t)
        return i

    def topo(self, rng):
        """Topological order of functions in which every edge's operands precede its output;
        edges that would close a cycle are dropped (counted in self.dropped)."""
        if getattr(self, '_topo', None) is not None:
            return self._topo
        n = self.n; F = self.F
        deps = [set() for _ in range(F)]
        for f in range(n, F):
            for op, a, b in self.by_out[f]:
                deps[f].add(a); deps[f].add(b)
        state = [0] * F; order = []; dropped = 0
        for root in range(F):
            if state[root]: continue
            stack = [(root, iter(sorted(deps[root])))]; state[root] = 1
            while stack:
                f, it = stack[-1]
                nxt = None
                for g in it:
                    if state[g] == 0: nxt = g; break
                    if state[g] == 1:   # cycle: drop edges of f that use g
                        before = len(self.by_out[f])
                        self.by_out[f] = [e for e in self.by_out[f] if g not in (e[1], e[2])]
                        dropped += before - len(self.by_out[f])
                if nxt is None:
                    state[f] = 2; order.append(f); stack.pop()
                else:
                    state[nxt] = 1; stack.append((nxt, iter(sorted(deps[nxt]))))
        self.dropped = dropped
        self._topo = [f for f in order if f >= n]
        print('topological order: %d functions, %d edges dropped for cycles' % (len(self._topo), dropped), file=sys.stderr)
        return self._topo

    def min_arrival(self):
        arr = [INF] * self.F
        for i in range(self.n): arr[i] = 0
        changed = True
        while changed:
            changed = False
            for (op, a, b), o in self.edges.items():
                v = 1 + max(arr[a], arr[b])
                if v < arr[o]: arr[o] = v; changed = True
        return arr

    # ---- mapping -------------------------------------------------------------------------
    def map(self, D, seed=0, passes=8, noise=0.3, exact_passes=0):
        rng = random.Random(seed)
        arr0 = self.min_arrival()
        if max(arr0[o] for o in self.outs) > D:
            return None
        F = self.F; n = self.n
        jit = [1.0 + noise * rng.random() for _ in range(F)] if noise else [1.0] * F
        order = self.topo(rng)
        choice = [None] * F
        af = [0.0] * F
        refs = [1.0] * F
        req = {}
        for it in range(passes + 1):
            arr = [INF] * F
            for i in range(n): arr[i] = 0
            done = [False] * F
            for i in range(n): done[i] = True
            for f in order:
                r = req.get(f, INF)
                best = None; bv = None; bt = None
                for e in self.by_out[f]:
                    op, a, b = e
                    if not (done[a] and done[b]): continue
                    t = 1 + max(arr[a], arr[b])
                    if r < INF:
                        if t > r: continue
                        v = jit[f] + af[a] / refs[a] + (af[b] / refs[b] if b != a else 0.0)
                        key = (v, t)
                    else:
                        v = jit[f] + af[a] / refs[a] + (af[b] / refs[b] if b != a else 0.0)
                        key = (t, v)
                    if bv is None or key < bv or (key == bv and rng.random() < 0.5):
                        bv = key; best = e; bt = t
                if best is None:
                    if r < INF: return None   # cannot happen: the previous cover met r
                    continue
                choice[f] = best; arr[f] = bt; done[f] = True
                af[f] = bv[0] if r < INF else bv[1]
            cover = self._cover(choice)
            if max(arr[o] for o in self.outs) > D: return None
            req = self._required(choice, cover, D, arr)
            refs = self._refs(choice, cover)
        return self._build(choice)

    def _cover(self, choice):
        cov = set(); stack = [o for o in self.outs if o >= self.n]
        while stack:
            f = stack.pop()
            if f in cov or f < self.n: continue
            cov.add(f); e = choice[f]
            stack += [e[1], e[2]]
        self._choice_ref = choice
        return cov

    def _refs(self, choice, cover):
        refs = {}
        for f in cover:
            e = choice[f]
            for x in {e[1], e[2]}: refs[x] = refs.get(x, 0) + 1
        for o in self.outs: refs[o] = refs.get(o, 0) + 1
        out = [1.0] * self.F
        for k, v in refs.items(): out[k] = float(v)
        return out

    def _levels(self, choice, cover):
        lv = {i: 0 for i in range(self.n)}
        def L(f):
            if f in lv: return lv[f]
            stack = [f]
            while stack:
                x = stack[-1]
                if x in lv: stack.pop(); continue
                e = choice[x]; pend = [y for y in (e[1], e[2]) if y not in lv]
                if pend: stack += pend; continue
                lv[x] = 1 + max(lv[e[1]], lv[e[2]]); stack.pop()
            return lv[f]
        for f in cover: L(f)
        return lv

    def _required(self, choice, cover, D, arr):
        lv = self._levels(choice, cover)
        req = {}
        for o in self.outs: req[o] = min(req.get(o, INF), D)
        for f in sorted(cover, key=lambda f: -lv[f]):
            r = req.get(f, INF); e = choice[f]
            for x in {e[1], e[2]}:
                req[x] = min(req.get(x, INF), r - 1)
        return req

    def _depth_ok(self, choice, cover, D):
        lv = self._levels(choice, cover)
        return max(lv[o] for o in self.outs) <= D

    def _build(self, choice):
        cover = self._cover(choice)
        lv = self._levels(choice, cover)
        sig = {i: i for i in range(self.n)}; gates = []
        for f in sorted(cover, key=lambda f: lv[f]):
            op, a, b = choice[f]
            sig[f] = self.n + len(gates); gates.append((op, sig[a], sig[b]))
        c = core.Circuit(self.n, 8, gates, [sig[o] for o in self.outs], 'union',
                         ['U%d' % i for i in range(8)], ['S%d' % i for i in range(8)])
        return c.live()


def exact_area_map(U, D, seed, passes=6, noise=0.3):
    return U.map(D, seed=seed, passes=passes, noise=noise, exact_passes=0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cap', type=int, required=True)
    ap.add_argument('--pool', nargs='+', required=True)
    ap.add_argument('--seeds', default='1-10')
    ap.add_argument('--noise', type=float, default=0.3)
    ap.add_argument('--passes', type=int, default=8)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    circs = load_pool(a.pool)
    U = Union(circs)
    arr = U.min_arrival()
    print('min arrival of outputs over the union:', [arr[o] for o in U.outs], file=sys.stderr)
    lo, hi = (int(x) for x in a.seeds.split('-')) if '-' in a.seeds else (int(a.seeds), int(a.seeds))
    best = None
    for s in range(lo, hi + 1):
        c = U.map(a.cap, seed=s, passes=a.passes, noise=a.noise if s > lo else 0.0, exact_passes=0)
        if c is None:
            print('seed %d: infeasible' % s, file=sys.stderr); continue
        m = c.metrics(NIST); ok = c.value_table() == AESTAB
        print('seed %d: G=%d A=%d GD=%d AD=%d ok=%s' % (s, m['G'], m['A'], m['GD'], m['AD'], ok), file=sys.stderr)
        if ok and m['GD'] <= a.cap and (best is None or m['G'] < best[0]['G']):
            best = (m, c, s)
    if best:
        m, c, s = best
        Path(a.out).write_text(core.write_ncff(c, NIST, comments=['union-graph cover, cap GD %d, seed %d' % (a.cap, s)]), encoding='utf-8')
        print('best: G=%d A=%d GD=%d AD=%d seed %d -> %s' % (m['G'], m['A'], m['GD'], m['AD'], s, a.out))


if __name__ == '__main__':
    main()
