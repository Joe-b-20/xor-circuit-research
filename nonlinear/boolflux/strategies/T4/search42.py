#!/usr/bin/env python3
"""T4: search for fewer ANDs on a GD-11 front by shared bottom junk, including 3-product designs
with free x-forms (chain.py graphs), using exact linear algebra on alternating-form residues.

G (extra junk ANDs) = x-junk constituents of a basis set of outputs using p2 PAIRING (default
(0,2)(1,3)) + d-junk AND(Y_a, Y_b) for the non-free pairs of that pairing.  Every other output takes
its best design whose x-junk lies in span(stage-1, G) and whose d-junk lies in V + G:
2-product designs (save 2), 3-product designs incl. free x-forms (save 1).
    python3 search42.py FRONT [PAIRING e.g. 02-13] [MAXB]"""
import sys, itertools, json
from pathlib import Path
from collections import Counter
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from rank2 import load, analyse, ONES, Span  # noqa
from xjunk import decompose  # noqa
from chain import lin, wedge, qform, Red, designs, WT  # noqa


def span_of(vecs):
    piv = {}
    for v in vecs:
        for h in sorted(piv, reverse=True):
            if (v >> h) & 1: v ^= piv[h]
        if v: piv[v.bit_length() - 1] = v
    return piv


def reduce_(piv, v):
    for h in sorted(piv, reverse=True):
        if (v >> h) & 1: v ^= piv[h]
    return v


def extend(piv, vecs):
    p = dict(piv)
    for v in vecs:
        v = reduce_(p, v)
        if v: p[v.bit_length() - 1] = v
    return p


if __name__ == '__main__':
    c = load(sys.argv[1]); T, lg, la, fa, ba, V, X = analyse(c)
    pr = sys.argv[2] if len(sys.argv) > 2 else '02-13'
    PAIR = tuple(tuple(int(ch) for ch in p) for p in pr.split('-'))
    maxb = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    outs = decompose(c, T, la, ba, 4)
    ys = sorted({y for d in outs for y in d})
    S1 = Red([qform(T[s]) for s in fa if la[s] == 1])
    R = lambda q: S1.red(q)
    W = [[lin(outs[k].get(y, 0)) for y in ys] for k in range(8)]
    # d-junk: V plus the d-junk ANDs of the basis pairing
    dj_pairs = [p for p in PAIR if (ys[p[0]] & ys[p[1]]) not in V]
    import os as _os
    extra_pairs = [tuple(int(ch) for ch in p) for p in _os.environ.get('T4_EXTRA_DJ', '').split(',') if p]
    dj_pairs = dj_pairs + [p for p in extra_pairs if p not in dj_pairs and (ys[p[0]] & ys[p[1]]) not in V]
    Vd = Span(list(V.piv.values()) + [ys[a] & ys[b] for a, b in dj_pairs])
    # design families per output: (n_products, q0, M1 cols, M2 cols, Bmat) residues
    fam = {k: [] for k in range(8)}
    for k in range(8):
        w = W[k]
        for combo in designs(4):
            edges = [s for kind, s in combo if kind == 'e']
            cnt = Counter(edges)
            es = [e for e, m_ in cnt.items() if m_ % 2]
            s = 0
            for a, b in es: s ^= ys[a] & ys[b]
            if s not in Vd: continue
            # GD-11 Kraft: a 3-product output has room 1/4 for junk; a level-9 d-junk AND alone fills it
            import os as _os
            if len(combo) >= 3 and _os.environ.get('T4_LIGHT3', '1') == '1' and s not in V: continue
            slots = []
            for t, (kind, sv) in enumerate(combo):
                for v in sv: slots.append((v, t))
            byv = {}
            for idx, (v, t) in enumerate(slots): byv.setdefault(v, []).append(idx)
            free = [i for v, L in byv.items() for i in L[:-1]]
            if len(free) > 2: continue
            def q_of(vals):
                x = [None] * len(slots)
                for i, val in zip(free, vals): x[i] = val
                for v, L in byv.items():
                    acc = w[v]
                    for i in L[:-1]: acc ^= x[i]
                    x[L[-1]] = acc
                j = 0
                for t, (kind, sv) in enumerate(combo):
                    if kind == 'e':
                        ia = [i for i, (v, tt) in enumerate(slots) if tt == t]
                        j ^= WT[x[ia[0]]][x[ia[1]]]
                return R(j)
            nf = len(free)
            z = [0] * nf
            q0 = q_of(z)
            M = []
            for f in range(nf):
                cols = []
                for bit in range(8):
                    v = list(z); v[f] = 1 << bit
                    cols.append(q_of(v) ^ q0)
                M.append(cols)
            Bm = None
            if nf == 2:
                Bm = [[q_of([1 << i, 1 << jb]) ^ q0 ^ M[0][i] ^ M[1][jb] for jb in range(8)] for i in range(8)]
                if not any(any(r) for r in Bm): Bm = None
            fam[k].append((len(combo), q0, M, Bm, combo, free))

    def best_design(k, piv):
        best = 0; ex = None
        for npr, q0, M, Bm, combo, free in fam[k]:
            sav = 4 - npr
            if sav <= best: continue
            if not M:
                ok = reduce_(piv, q0) == 0
            elif Bm is None:
                p2 = extend(piv, [x for cols in M for x in cols])
                ok = reduce_(p2, q0) == 0
            else:
                ok = False
                for u1 in range(256):
                    qq = q0
                    cols = list(M[1])
                    for i in range(8):
                        if (u1 >> i) & 1:
                            qq ^= M[0][i]
                            cols = [cv ^ Bm[i][jb] for jb, cv in enumerate(cols)]
                    p2 = extend(piv, cols)
                    if reduce_(p2, qq) == 0: ok = True; break
            if ok: best = sav; ex = str(combo)
        return best, ex

    cons = {k: [R(wedge(W[k][a], W[k][b])) for a, b in PAIR] for k in range(8)}
    MIXED = _os.environ.get('T4_MIXED') == '1'
    PAIRS3 = [((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2))]
    consP = {(k, pi): [R(wedge(W[k][a], W[k][b])) for a, b in PAIRS3[pi]] for k in range(8) for pi in range(3)}
    base_piv = {}
    results = []
    def basis_sets():
        for nb in range(1, maxb + 1):
            for B in itertools.combinations(range(8), nb):
                if _os.environ.get('T4_MIXED') == '2':
                    # basis items: any p2 pairing or any single pair (p3) per output
                    opts = [('p2', pi) for pi in range(3)] + [('p3', pr_) for pr_ in itertools.combinations(range(4), 2)]
                    for ch in itertools.product(opts, repeat=nb):
                        vecs = []; prs = []
                        for k, (kind, o) in zip(B, ch):
                            if kind == 'p2':
                                vecs += consP[(k, o)]; prs.append(PAIRS3[o])
                            else:
                                vecs.append(R(wedge(W[k][o[0]], W[k][o[1]]))); prs.append((o,))
                        yield B, vecs, tuple(prs), tuple(ch)
                    continue
                if not MIXED:
                    yield B, [x for k in B for x in cons[k]], PAIR
                else:
                    for pis in itertools.product(range(3), repeat=nb):
                        yield B, [x for k, pi in zip(B, pis) for x in consP[(k, pi)]], tuple(PAIRS3[pi] for pi in pis)
    for item in basis_sets():
        B, cvecs, bpairs = item[0], item[1], item[2]
        bkinds = item[3] if len(item) > 3 else None
        if True:
            piv = span_of(cvecs)
            if MIXED or bkinds is not None:
                need = set()
                for prs in bpairs:
                    for pr_ in prs:
                        if (ys[pr_[0]] & ys[pr_[1]]) not in V: need.add(pr_)
                if not need.issubset(set(dj_pairs)): continue
            cost = len(piv) + len(dj_pairs)
            if bkinds is None:
                sav = 2 * len(B)
                detail = {k: (2, 'basis p2') for k in B}
            else:
                sav = sum(2 if kd[0] == 'p2' else 1 for kd in bkinds)
                detail = {k: (2 if kd[0] == 'p2' else 1, 'basis %s %s' % kd) for k, kd in zip(B, bkinds)}
            for k in range(8):
                if k in B: continue
                s_, ex = best_design(k, piv)
                sav += s_; detail[k] = (s_, ex)
            net = sav - cost
            results.append((net, B, cost, detail))
            print(json.dumps({'net': net, 'A': 48 - net, 'B': B, 'bpairs': bpairs if MIXED else None, 'cost': cost, 'detail': detail}), flush=True)
    results.sort(key=lambda r: -r[0])
    print('BEST', json.dumps({'net': results[0][0], 'B': results[0][1], 'detail': results[0][3]}))
