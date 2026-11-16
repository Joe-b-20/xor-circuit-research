#!/usr/bin/env python3
"""Build an AD3 circuit with re-based level-3 classes and depth-aware XOR trees (cap D).

    python3 rebased_build.py FILE --cap 12 --out OUT.bfx [--seed S] [--pick best|random]

Keeps the parent's gates of AND level <= 2 (and their linear signals), replaces the 12 level-3 ANDs
by the re-based products of botbasis.py (one triple of class bases with max output Kraft <= 1), builds
each new R' operand and each output as a Kraft-feasible XOR tree of existing signals (largest-subset
pieces first, falling back to basis terms), then removes dead gates and verifies on all 256 inputs.
"""
import sys, random, argparse, json, heapq
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core, skeleton                     # noqa: E402
from boolflux.hub.common import verify, metrics, clean   # noqa: E402
import botbasis as BB                                    # noqa: E402
from skelan import anatomy as _anat                      # noqa: E402
BB.anatomy = _anat

XOR, XNOR, NOT, AND = core.OPS['XOR'], core.OPS['XNOR'], core.OPS['NOT'], core.OPS['AND']


def popc(x):
    return bin(x).count('1')


class Builder:
    def __init__(self, c):
        self.n = c.n; self.gates = list(c.gates)
        n = c.n
        # forms over the skeleton basis of c (constant bit 0)
        form = [1 << (1 + i) for i in range(n)]; lv = [0] * n; kind = ['x'] * n
        k = 0
        for op, a, b in c.gates:
            fa, fb = form[a], form[b]
            if op == XOR: f = fa ^ fb
            elif op == XNOR: f = fa ^ fb ^ 1
            elif op == NOT: f = fa ^ 1
            else:
                p, q, r = skeleton.nl_decompose(op)
                f = (1 << (1 + n + k)) ^ r; k += 1
            form.append(f); lv.append(1 + max(lv[a], lv[b]))
            kind.append('and' if op not in (XOR, XNOR, NOT) else 'lin')
        self.form, self.lv, self.kind = form, lv, kind
        self.by = {}
        for s, f in enumerate(form):
            key = f & ~1
            if key and (key not in self.by or lv[s] < lv[self.by[key]]): self.by[key] = s

    def new(self, op, a, b):
        s = self.n + len(self.gates); self.gates.append((op, a, b))
        fa, fb = self.form[a], self.form[b]
        f = fa ^ fb if op == XOR else (fa ^ fb ^ 1 if op == XNOR else (fa ^ 1 if op == NOT else None))
        self.form.append(f); self.lv.append(1 + max(self.lv[a], self.lv[b])); self.kind.append('lin')
        if f is None: return s
        key = f & ~1
        if key and (key not in self.by or self.lv[s] < self.lv[self.by[key]]): self.by[key] = s
        return s

    def term_sig(self, p):
        """signal carrying basis position p alone (inputs / AND outputs, constant ignored)"""
        return self.by[1 << p]

    def build(self, F, r, rng=None):
        """signal with form F (incl. constant) at level <= r if possible; returns signal"""
        f = F & ~1
        if f == 0:
            raise ValueError('constant form')
        s = self.by.get(f)
        if s is not None and self.lv[s] <= r and (self.form[s] & 1) == (F & 1):
            return s
        if s is not None and self.lv[s] <= r - 1 and (self.form[s] & 1) != (F & 1):
            return self.new(NOT, s, s)
        terms = [p for p in BB.bits(f) if p]
        cap = 2 ** r
        base_k = {p: 2 ** self.lv[self.term_sig(p)] for p in terms}
        # candidate pieces: existing signals with form subset of f, more than one term
        cands = [(popc(key), key, s) for key, s in self.by.items()
                 if key & ~f == 0 and popc(key) >= 2 and self.lv[s] <= r - 1]
        cands.sort(key=lambda t: (-t[0], self.lv[t[2]]))
        if rng is not None:
            # light shuffle among equal popcounts
            cands.sort(key=lambda t: (-t[0], self.lv[t[2]], rng.random()))
        rem = f; pieces = []; used = 0.0
        def rest_k(m):
            return sum(base_k[p] for p in BB.bits(m) if p)
        for pc, key, s in cands:
            if key & ~rem: continue
            k2 = used + 2 ** self.lv[s] + rest_k(rem ^ key)
            if k2 <= cap:
                pieces.append(s); used += 2 ** self.lv[s]; rem ^= key
                if rem == 0: break
        for p in BB.bits(rem):
            if p: pieces.append(self.term_sig(p))
        # constant parity
        par = (F & 1) ^ (sum(self.form[s] & 1 for s in pieces) & 1)
        if len(pieces) == 1:
            s = pieces[0]
            return self.new(NOT, s, s) if par else s
        h = [(self.lv[s], i, s) for i, s in enumerate(pieces)]; heapq.heapify(h); cnt = len(h)
        while len(h) > 1:
            l1, _, a = heapq.heappop(h); l2, _, b = heapq.heappop(h)
            key = (self.form[a] ^ self.form[b]) & ~1
            op = XOR
            if len(h) == 0 and par: op = XNOR
            ex = self.by.get(key)
            if op == XOR and ex is not None and self.lv[ex] <= max(l1, l2) + 1 and ((self.form[ex] ^ self.form[a] ^ self.form[b]) & 1) == 0:
                s = ex
            else:
                s = self.new(op, a, b)
            cnt += 1; heapq.heappush(h, (self.lv[s], cnt, s))
        return h[0][2]


def construct(c, res, triple, cap, rng=None):
    pcs = res['_pc']; info = res['_info']
    sk = skeleton.extract(c); n = c.n
    B = Builder(c)
    and_sig = {}
    k = 0
    for j, (op, a, b) in enumerate(c.gates):
        if op not in (XOR, XNOR, NOT):
            and_sig[k] = n + j; k += 1
    out_forms = sk['outputs']
    # new products: for each class, for each new basis vector
    prod_sig = []   # (class idx, t) -> signal
    outs_terms = [[] for _ in out_forms]
    def farr_sig(F):
        return B.lv[B.by[F & ~1]] if (F & ~1) in B.by else None
    for ci, pc in enumerate(pcs):
        ks = pc['ands']; d = len(ks)
        Bs = triple[ci]
        qforms = sorted({info[kk][0] for kk in ks}, key=lambda F: B.lv[B.by.get(F & ~1, 0)] if (F & ~1) in B.by else 99)
        rf = [info[kk][1] for kk in ks]
        new_sigs = []
        for v in Bs:
            R = 0
            for i in range(d):
                if (v >> i) & 1: R ^= rf[i]
            best = None
            for Qf in qforms:
                for (X, Y) in ((Qf, R), (Qf, Qf ^ R ^ 1), (Qf ^ R ^ 1, R)):
                    sx = B.build(X, cap - 3, rng); sy = B.build(Y, cap - 3, rng)
                    lvl = 1 + max(B.lv[sx], B.lv[sy])
                    if best is None or lvl < best[0]: best = (lvl, sx, sy)
            s = B.new(AND, best[1], best[2]); B.kind[-1] = 'and'
            B.form[s] = None
            new_sigs.append(s)
        # output membership
        for j, f in enumerate(out_forms):
            m = 0
            for i, kk in enumerate(ks):
                if (f >> (1 + n + kk)) & 1: m |= 1 << i
            sol = BB.solve(list(Bs), m)
            for t in range(d):
                if (sol >> t) & 1: outs_terms[j].append(new_sigs[t])
    # outputs: old forms contain only level-3 terms (+ const); check
    l3 = {1 + n + kk for pc in pcs for kk in pc['ands']}
    outs = []
    # give new products fresh basis ids in the form table for output building
    nb0 = 1 + n + len(sk['ands'])
    pid = {}
    for s in sorted({s for ts in outs_terms for s in ts}):
        pid[s] = nb0 + len(pid); B.form[s] = 1 << pid[s]; B.by[1 << pid[s]] = s
    for j, f in enumerate(out_forms):
        other = f & ~1
        for p in l3: other &= ~(1 << p)
        assert other == 0, 'output has non-level-3 terms'
        F = (f & 1)
        for s in outs_terms[j]: F ^= B.form[s]
        outs.append(B.build(F, cap, rng))
    nc = core.Circuit(n, c.m, B.gates, outs, 'rebase', c.in_names, c.out_names).live()
    return clean(nc)


def feasible_triples(res, limit=1.0 + 1e-9):
    pcs = res['_pc']; outT = []
    A, B_, C = [pc['pareto'] for pc in pcs]
    for a, ba in A:
        for b, bb in B_:
            ab = [x + y for x, y in zip(a, b)]
            if max(ab) > limit: continue
            for cc, bc in C:
                if max(x + y for x, y in zip(ab, cc)) <= limit:
                    outT.append((ba, bb, bc))
    return outT


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('file'); ap.add_argument('--cap', type=int, default=12)
    ap.add_argument('--out', required=True); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--n', type=int, default=1)
    a = ap.parse_args()
    c = BB.load(a.file)
    res = BB.analyse(a.file, a.cap, verbose=False)
    T = feasible_triples(res)
    print('feasible triples (Pareto reps):', len(T), 'best max Kraft', res['best'])
    rng = random.Random(a.seed)
    outdir = Path(a.out); outdir.mkdir(parents=True, exist_ok=True)
    seen = set(); rows = []
    for it in range(a.n):
        tri = T[0] if it == 0 else rng.choice(T)
        nc = construct(c, res, tri, a.cap, rng if it else None)
        ok, inf = verify(nc)
        m = metrics(nc)
        key = core.to_kernel(nc)
        if key in seen: continue
        seen.add(key)
        p = outdir / ('rb-a%d-ad%d-g%d-gd%d-%d.bfx' % (m[0], m[1], m[2], m[3], it))
        p.write_text(key)
        rows.append({'it': it, 'ok': ok, 'm': m, 'triple': tri, 'file': str(p)})
        print(it, ok, m, tri, p.name, inf.get('error', ''))
    json.dump(rows, open(outdir / 'rebase.json', 'w'), indent=1)




# ---------------------------------------------------------------------------------------------
# fresh depth-tight synthesis of a whole skeleton

def new_skeleton(c, res, triple):
    """skeleton (ands, outputs) with the level-3 classes re-based per triple"""
    pcs = res['_pc']; info = res['_info']
    sk = BB.anatomy(c)[0]; n = c.n
    _, arr, alv = BB.anatomy(c) if hasattr(BB, 'anatomy') else (None, None, None)
    def farr(f):
        return BB.huff([arr[p] for p in BB.bits(f) if p], f & 1)
    l3 = sorted(kk for pc in pcs for kk in pc['ands'])
    keep = [k for k in range(len(sk['ands'])) if k not in set(l3)]
    # keep lower ANDs at their positions; they never reference level-3 ANDs
    ands = [sk['ands'][k] for k in keep]
    remap = {}
    for i, k in enumerate(keep): remap[1 + n + k] = 1 + n + i
    def rm(f):
        g = f & 1
        for p in BB.bits(f):
            if p == 0: continue
            g |= 1 << (remap.get(p, p) if p > n else p)
        return g
    ands = [(rm(L), rm(R)) for L, R in ands]
    outs = [f & 1 for f in sk['outputs']]
    for ci, pc in enumerate(pcs):
        ks = pc['ands']; d = len(ks); Bs = triple[ci]
        qforms = sorted({info[kk][0] for kk in ks}, key=farr)
        rf = [info[kk][1] for kk in ks]
        newpos = []
        for v in Bs:
            R = 0
            for i in range(d):
                if (v >> i) & 1: R ^= rf[i]
            best = None
            for Qf in qforms:
                for (X, Y) in ((Qf, R), (Qf, Qf ^ R ^ 1), (Qf ^ R ^ 1, R)):
                    lvl = 1 + max(farr(X), farr(Y))
                    if best is None or lvl < best[0]: best = (lvl, X, Y)
            ands.append((rm(best[1]), rm(best[2]))); newpos.append(1 + n + len(ands) - 1)
        for j, f in enumerate(sk['outputs']):
            m = 0
            for i, kk in enumerate(ks):
                if (f >> (1 + n + kk)) & 1: m |= 1 << i
            sol = BB.solve(list(Bs), m)
            for t in range(d):
                if (sol >> t) & 1: outs[j] ^= 1 << newpos[t]
    return {'n': n, 'm': c.m, 'ands': ands, 'outputs': outs}


def fresh_build(sk, cap, rng=None, slack=0):
    n = sk['n']
    class FB(Builder):
        def __init__(s):
            s.n = n; s.gates = []; s.form = [1 << (1 + i) for i in range(n)]; s.lv = [0] * n
            s.kind = ['x'] * n; s.by = {s.form[i]: i for i in range(n)}
    B = FB()
    arr = [0] * (1 + n + len(sk['ands']))
    for k, (L, R) in enumerate(sk['ands']):
        hl = BB.huff([arr[p] for p in BB.bits(L) if p], L & 1)
        hr = BB.huff([arr[p] for p in BB.bits(R) if p], R & 1)
        dl = max(hl, hr) + slack
        sl = B.build(L, dl, rng); sr = B.build(R, dl, rng)
        s = B.new(AND, sl, sr); B.kind[-1] = 'and'
        p = 1 + n + k; B.form[s] = 1 << p; B.by[1 << p] = s
        arr[p] = B.lv[s]
    outs = [B.build(F, cap, rng) for F in sk['outputs']]
    nc = core.Circuit(n, sk['m'], B.gates, outs, 'fresh')
    return clean(nc.live())


def main2():
    ap = argparse.ArgumentParser(); ap.add_argument('file'); ap.add_argument('--cap', type=int, default=12)
    ap.add_argument('--out', required=True); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--n', type=int, default=1); ap.add_argument('--slack', type=int, default=0)
    a = ap.parse_args()
    c = BB.load(a.file)
    res = BB.analyse(a.file, a.cap, verbose=False)
    T = feasible_triples(res)
    print('feasible triples (Pareto reps):', len(T), 'best max Kraft', res['best'])
    rng = random.Random(a.seed)
    outdir = Path(a.out); outdir.mkdir(parents=True, exist_ok=True)
    seen = set(); rows = []
    for it in range(a.n):
        tri = T[0] if it == 0 else rng.choice(T)
        sk = new_skeleton(c, res, tri)
        nc = fresh_build(sk, a.cap, rng if it else None, a.slack)
        ok, inf = verify(nc); m = metrics(nc); key = core.to_kernel(nc)
        if key in seen: continue
        seen.add(key)
        p = outdir / ('fb-a%d-ad%d-g%d-gd%d-%d.bfx' % (m[0], m[1], m[2], m[3], it))
        p.write_text(key)
        rows.append({'it': it, 'ok': ok, 'm': m, 'triple': tri, 'file': str(p), 'parent': str(Path(a.file).resolve())})
        print(it, ok, m, tri, p.name, inf.get('error', ''), flush=True)
    json.dump(rows, open(outdir / 'fresh.json', 'w'), indent=1)


if __name__ == '__main__':
    if '--fresh' in sys.argv:
        sys.argv.remove('--fresh'); main2()
    else:
        main()
