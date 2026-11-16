#!/usr/bin/env python3
"""P6: depth bound of an AD3 circuit under re-basing of each level-3 class (GF(4)-Karatsuba form).

Level-3 products are Q_w * R_c (w in 3 classes, 4 products per class).  Re-basing a class with an
invertible T (new R'_i = sum_j T_ij R_j) keeps span(class products), so the outputs stay in the span;
the bottom block M_w becomes M_w T^-1.  For every class and every unordered basis of span{R_c} (840)
we compute the Huffman arrival of each new product (min over the trivial operand variants
(Q, R), (Q, Q+R+1), (Q+R+1, R) with the circuit's own Q/R forms over the skeleton basis; lower levels
fixed at their Huffman-earliest arrivals) and the Kraft contribution to every output at cap D.
Then the best triple (min over triples of max_j Kraft_j) is found exactly (dominance-pruned).

    python3 botbasis.py FILE [--cap 12] [--json OUT]
Bound semantics: [C] for the case "level <= 2 skeleton fixed, products restricted to re-bases of the
existing classes, outputs = XOR trees of products"; Kraft <= 1 per output <=> depth <= cap.
"""
import sys, json, argparse, itertools
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[4]))
from boolflux import core, skeleton                     # noqa: E402
from boolflux.hub.common import _gpow, _gmul, ONES       # noqa: E402
from skelan import huff, bits, anatomy                  # noqa: E402


def trace(z):
    t = 0; y = z
    for _ in range(8):
        t ^= y; y = _gmul(y, y)
    return t


def table(f):
    v = 0
    for x in range(256):
        if f(x) & 1: v |= 1 << x
    return v


def load(path):
    p = str(path)
    if p.endswith('.bfx'):
        return core.from_kernel(open(p).read())
    return core.read_ncff(p)


def qtables():
    P170 = [_gpow(x, 170) for x in range(256)]
    return {table(lambda x, w=w: trace(_gmul(w, P170[x]))) for w in range(1, 256)}


def gf2_rank(vs):
    vs = list(vs); r = 0; piv = []
    basis = []
    for v in vs:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v); r += 1
    return r


def solve(rows_basis, target):
    """express target (int vector over products) in terms of rows_basis (list of int); return mask or None"""
    # Gaussian elimination with tracking
    B = []   # (vec, mask)
    for i, v in enumerate(rows_basis):
        m = 1 << i
        for (bv, bm) in B:
            if v ^ bv < v: v ^= bv; m ^= bm
        if v: B.append((v, m))
        B.sort(key=lambda t: -t[0])
    v = target; m = 0
    for (bv, bm) in B:
        if v ^ bv < v: v ^= bv; m ^= bm
    return None if v else m


def analyse(path, cap=12, verbose=True):
    c = load(path)
    sk, arr, alv = anatomy(c)
    n = c.n; ands = sk['ands']
    tab, ft, ones = skeleton._form_tables(sk)
    Qs = qtables()
    def farr(f):
        return huff([arr[p] for p in bits(f) if p], f & 1)
    l3 = [k for k in range(len(ands)) if alv[1 + n + k] == 3]
    # classes
    cls = {}
    info = {}
    for k in l3:
        L, R = ands[k]; tL, tR = ft(L), ft(R); P = tL & tR
        q = None
        for Q in Qs:
            if P & ~Q & ones == 0 and P != 0:
                q = Q; break
        assert q is not None, 'product not under a Q'
        # Q form and R form
        cand = [(L, R), (R, L)]
        qf = rf = None
        for X, Y in cand:
            if ft(X) == q: qf, rf = X, Y
        if qf is None:
            for X, Y in cand:
                if ft(X ^ Y ^ 1) == q: qf, rf = X ^ Y ^ 1, Y
        assert qf is not None and (q & ft(rf)) == P
        cls.setdefault(q, []).append(k); info[k] = (qf, rf, P)
    out_forms = sk['outputs']
    # outputs as vectors over level-3 ANDs (must contain only level-3 terms + maybe lower)
    res = {'file': str(path), 'cap': cap, 'classes': []}
    per_class = []
    for q, ks in cls.items():
        qforms = sorted({info[k][0] for k in ks}, key=farr)
        rf = [info[k][1] for k in ks]; Ps = [info[k][2] for k in ks]
        d = len(ks)
        # output block: for output j, mask over ks of the terms
        blk = []
        for f in out_forms:
            m = 0
            for i, k in enumerate(ks):
                if (f >> (1 + n + k)) & 1: m |= 1 << i
            blk.append(m)
        vecs = list(range(1, 1 << d))
        def vform(v):
            f = 0
            for i in range(d):
                if (v >> i) & 1: f ^= rf[i]
            return f
        def varr(v):
            R = vform(v); best = 99
            for Qf in qforms:
                a1 = 1 + max(farr(Qf), farr(R))
                a2 = 1 + max(farr(Qf), farr(Qf ^ R ^ 1))
                a3 = 1 + max(farr(Qf ^ R ^ 1), farr(R))
                best = min(best, a1, a2, a3)
            return best
        va = {v: varr(v) for v in vecs}
        opts = {}
        for B in itertools.combinations(vecs, d):
            if gf2_rank(B) < d: continue
            # each output block m (in old basis coords, i.e. sum of old products i) -> new coords:
            # old product i = e_i ; new products are B[t] = sum_i B[t]_i e_i ; solve m = sum_t s_t B[t]
            kr = []
            for m in blk:
                s = solve(list(B), m)
                kr.append(sum(2.0 ** (va[B[t]] - cap) for t in range(d) if (s >> t) & 1))
            key = tuple(kr)
            if key not in opts: opts[key] = B
        # dominance prune
        keys = sorted(opts)
        pareto = []
        for kk in keys:
            if not any(all(a <= b for a, b in zip(p, kk)) for p in pareto):
                pareto.append(kk)
        cur = []
        for m in blk:
            cur.append(sum(2.0 ** (va[1 << i] - cap) for i in range(d) if (m >> i) & 1))
        per_class.append({'Q': q, 'ands': ks, 'arr': {str(v): va[v] for v in vecs}, 'pareto': [(p, opts[p]) for p in pareto], 'current': cur})
        if verbose:
            print('class', ks, 'single-R arrivals', [va[1 << i] for i in range(d)], 'min arr any combo', min(va.values()),
                  'bases', len(opts), 'pareto', len(pareto))
    # best triple
    cur_tot = [sum(pc['current'][j] for pc in per_class) for j in range(len(out_forms))]
    best = None
    A, B_, C = [pc['pareto'] for pc in per_class]
    for a, ba in A:
        for b, bb in B_:
            ab = [x + y for x, y in zip(a, b)]
            if best is not None and max(ab) >= best[0]: continue
            for cc, bc in C:
                t = max(x + y for x, y in zip(ab, cc))
                if best is None or t < best[0]:
                    best = (t, [ba, bb, bc], [x + y for x, y in zip(ab, cc)])
    res['current_kraft'] = cur_tot; res['best'] = best[0]; res['best_kraft'] = best[2]; res['best_bases'] = best[1]
    res['classes'] = [{'ands': pc['ands'], 'arr': pc['arr']} for pc in per_class]
    res['_pc'] = per_class; res['_info'] = info
    if verbose:
        print('current Kraft per output', [round(x, 3) for x in cur_tot], 'max', max(cur_tot))
        print('best rebasing: max Kraft %.3f' % best[0], [round(x, 3) for x in best[2]], 'bases', best[1])
    return res


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('files', nargs='+'); ap.add_argument('--cap', type=int, default=12)
    ap.add_argument('--json'); ap.add_argument('--variants', action='store_true')
    a = ap.parse_args()
    import skelan; skelan.VARIANTS = a.variants
    allr = []
    for f in a.files:
        print('==', f)
        allr.append(analyse(f, a.cap))
    if a.json:
        [r.pop('_pc') and r.pop('_info') for r in allr]
        json.dump(allr, open(a.json, 'w'), indent=1, default=str)
