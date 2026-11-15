#!/usr/bin/env python3
"""T4: rebuild the bottom of a GD-11 AD-4 circuit (4 rank-1 products per output) with rank-2
products whose junk is shared between outputs (pair56.py findings), keeping the front.

Plan language (per output k, NIST order):
  r1          keep the 4 rank-1 products Y_i * w_ik
  p3 a b      3 products: (Y_a + w_bk)(Y_b + w_ak) + the 2 other rank-1 products;
              junk Y_a Y_b (front span or extra AND) + w_ak w_bk (extra AND or front span + another
              output's extra AND)
  p2 a b c d  2 products (Y_a + w_b)(Y_b + w_a), (Y_c + w_d)(Y_d + w_c); junk Y_aY_b + Y_cY_d +
              w_a w_b + w_c w_d
Junk is solved generically: the junk function must lie in span(front signals, extra ANDs); extra
ANDs (x-junk AND(w, w'), d-junk AND(Y, Y')) are created on demand and shared by function.
    python3 build46.py FILE OUTDIR 'k:plan;k:plan;...'
"""
import sys, json, itertools, os
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from rank2 import load, analyse, ONES  # noqa
from xjunk import decompose  # noqa
from coversearch import TSpan, bound  # noqa
from boolflux import core, skeleton, targets  # noqa


XOPTS = [(pa, c1, c2) for pa in range(3) for c1 in (0, 1) for c2 in (0, 1)]


def front_first(c):
    """stable topological reorder: gates not depending on a last-AND-level AND first"""
    n = c.n; la = [0] * n
    for op, a, b in c.gates: la.append((op in core.NONLINEAR_OPS) + max(la[a], la[b]))
    AD = max(la[o] for o in c.outputs)
    dep = [False] * (n + len(c.gates))
    for j, (op, a, b) in enumerate(c.gates):
        s = n + j
        dep[s] = dep[a] or dep[b] or (op in core.NONLINEAR_OPS and la[s] == AD)
    order = [j for j in range(len(c.gates)) if not dep[n + j]] + [j for j in range(len(c.gates)) if dep[n + j]]
    new = list(range(n)) + [None] * len(c.gates)
    gates = []
    for j in order:
        op, a, b = c.gates[j]
        new[n + j] = n + len(gates); gates.append((op, new[a], new[b]))
    return core.Circuit(n, c.m, gates, [new[o] for o in c.outputs], c.name)


def build(f, plans, xvar=None):
    xvar = xvar or {}
    xcount = [0]
    c = front_first(load(f)); n = c.n
    T, lg, la, fa, ba, V, X = analyse(c)
    AD = max(la[o] for o in c.outputs)
    sk0 = skeleton.extract(c)
    ands_sig = [n + j for j, g in enumerate(c.gates) if g[0] in core.NONLINEAR_OPS]
    front = [k for k, s in enumerate(ands_sig) if la[s] < AD]
    assert front == list(range(len(front))), 'front ANDs must come first'
    nf = len(front)
    # forms of Y-sides and x-sides from the skeleton's bottom ANDs
    tab, ft, ones = skeleton._form_tables(sk0)
    yform = {}; xform = {}           # function -> form
    for k, s in enumerate(ands_sig):
        if la[s] != AD: continue
        L, R = sk0['ands'][k]
        for A_, B_ in ((L, R), (R, L)):
            if A_ >> (1 + n) and not (B_ >> (1 + n)):
                yform.setdefault(ft(A_), A_); xform.setdefault(ft(B_), B_)
    outs = decompose(c, T, la, ba, AD)
    ys = sorted({y for d in outs for y in d})
    # span of front signals with forms (tags = basis positions 0..1+n+nf-1)
    ts = TSpan()
    basis_t = [ONES] + [T[i] for i in range(n)] + [T[ands_sig[k]] for k in front]
    for i, v in enumerate(basis_t): ts.add(v, 1 << i)
    ands = [sk0['ands'][k] for k in front]
    extra = {}                        # function -> AND index (extra junk ANDs, rank-1 products)

    def P(j): return 1 << (1 + n + j)

    def new_and(L, R):
        tl, tr_ = ftab(L), ftab(R)
        key = tl & tr_
        if key in extra: return extra[key]
        ands.append((L, R)); extra[key] = len(ands) - 1
        ts.add(key, P(len(ands) - 1))   # tag = its own position bit
        return extra[key]

    def ftab(F):
        t = ONES if F & 1 else 0
        for p in range(1, 1 + n + len(ands)):
            if (F >> p) & 1: t ^= (basis_t[p] if p < len(basis_t) else tabs_extra[p])
        return t
    tabs_extra = {}

    def reg(j):
        L, R = ands[j]
        tabs_extra[1 + n + j] = ftab(L) & ftab(R)

    _affN = []

    def dj_low(F):
        """AND of two affine functions of N equal to F modulo the current span (lowest level)"""
        if not _affN:
            import inv6 as _I
            Nx = [_I.p256(x, 17) for x in range(256)]
            for f16 in _I.NONC:
                t = sum(((f16 >> _I.IDX[Nx[x]]) & 1) << x for x in range(256))
                tag = ts.express(t)
                if tag is None: continue
                form = 0
                for p_ in range(tag.bit_length()):
                    if (tag >> p_) & 1: form |= 1 << p_
                _affN.append((t, form))
        best = None
        for (t1, f1), (t2, f2) in itertools.combinations(_affN, 2):
            if ts.express(F ^ (t1 & t2)) is None: continue
            cost = max(bin(f1).count('1'), bin(f2).count('1'))
            if best is None or cost < best[0]: best = (cost, f1, f2)
        return None if best is None else (best[1], best[2])

    def junk_form(fun, xparts=(), yparts=()):
        """form of fun using front span + extra ANDs; creates the listed x-junk / d-junk ANDs if needed"""
        tag = ts.express(fun)
        if tag is not None: return tag
        for idx, (La, Lb) in enumerate(list(xparts) + list(yparts)):
            if idx < len(xparts):
                o = XOPTS[xvar.get(xcount[0], 0)]; xcount[0] += 1
                u, v = [(La, Lb), (La, La ^ Lb), (Lb, La ^ Lb)][o[0]]
                La, Lb = u ^ o[1], v ^ o[2]
            elif os.environ.get('T4_DJLOW') == '1':
                low = dj_low(ftab(La) & ftab(Lb))
                if low is not None: La, Lb = low
            j = new_and(La, Lb); reg(j)
            tag = ts.express(fun)
            if tag is not None: return tag
        return None
    outforms = [None] * 8
    sbox_t = core.tables_from_values(8, 8, targets.aes_sbox())
    import os
    order = [int(x) for x in os.environ.get('T4_ORDER', '').split(',') if x != '']
    order += [k for k in range(8) if k not in order]
    for k in order:
        w = [outs[k].get(y, 0) for y in ys]
        Yf = [yform[y] for y in ys]; Wf = [xform[x] for x in w]
        plan = plans.get(k, 'r1').split()
        F = 0
        prods = []
        if plan[0] == 'r1':
            for i in range(4): prods.append((Yf[i], Wf[i]))
            junk = 0; xp = []; yp = []
        elif plan[0] == 'p3':
            a, b = int(plan[1]), int(plan[2])
            prods.append((Yf[a] ^ Wf[b], Yf[b] ^ Wf[a]))
            for i in range(4):
                if i not in (a, b): prods.append((Yf[i], Wf[i]))
            junk = (ys[a] & ys[b]) ^ (w[a] & w[b])
            xp = [(Wf[a], Wf[b])]; yp = [(Yf[a], Yf[b])]
        elif plan[0] == 'p2':
            a, b, cc, d = map(int, plan[1:5])
            prods.append((Yf[a] ^ Wf[b], Yf[b] ^ Wf[a])); prods.append((Yf[cc] ^ Wf[d], Yf[d] ^ Wf[cc]))
            junk = (ys[a] & ys[b]) ^ (ys[cc] & ys[d]) ^ (w[a] & w[b]) ^ (w[cc] & w[d])
            xp = [(Wf[a], Wf[b]), (Wf[cc], Wf[d])]; yp = [(Yf[a], Yf[b]), (Yf[cc], Yf[d])]
        if plan[0] == 'cx':
            # explicit products: groups "a b u v" (edge: AND(Y_a ^ u, Y_b ^ v), u, v x-linear hex)
            # or "a - z" (vertex: AND(Y_a, z)); junk = S_k ^ sum of the products (generic)
            groups = ' '.join(plan[1:]).split('|')
            prods = []; xp = []; yp = []
            for gtxt in groups:
                t = gtxt.split()
                if t[1] == '-':
                    a = int(t[0]); z = int(t[2], 16)
                    prods.append((Yf[a], z << 1))
                else:
                    a, b = int(t[0]), int(t[1]); u, v = int(t[2], 16), int(t[3], 16)
                    prods.append((Yf[a] ^ (u << 1), Yf[b] ^ (v << 1)))
                    xp.append((u << 1, v << 1)); yp.append((Yf[a], Yf[b]))
            ptab = 0
            for L, R in prods: ptab ^= ftab(L) & ftab(R)
            junk = sbox_t[k] ^ ptab
            if junk in (0, ONES): junk = 0
        for L, R in prods:
            j = new_and(L, R); reg(j); F ^= P(j)
        if junk:
            # the junk is the XOR of the (constant-free) junk terms; constants handled at the end
            tag = junk_form(junk, xp, yp)
            if tag is None:
                tag = junk_form(junk ^ ONES, xp, yp)
                if tag is None: raise ValueError('junk of output %d not expressible' % k)
                tag ^= 1
            F ^= tag
        outforms[k] = F
    sk = {'n': n, 'm': 8, 'ands': ands, 'outputs': outforms}
    tb, ftt, on = skeleton._form_tables(sk)
    for k in range(8):
        if ftt(outforms[k]) ^ sbox_t[k] == on: outforms[k] ^= 1
    ok = all(ftt(outforms[k]) == sbox_t[k] for k in range(8))
    return sk, ok


if __name__ == '__main__':
    f, outdir = sys.argv[1], Path(sys.argv[2]); outdir.mkdir(parents=True, exist_ok=True)
    plans = {}
    for part in sys.argv[3].split(';'):
        if part.strip():
            k, pl = part.split(':'); plans[int(k)] = pl.strip()
    best = None
    nx = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    import itertools as _it
    for combo in _it.product(range(len(XOPTS)), repeat=nx):
        xv = dict(enumerate(combo))
        try:
            sk_, ok_ = build(f, plans, xv)
        except ValueError:
            continue
        b_, arr_, ol_ = bound(sk_, 8)
        key = (not ok_, b_, sum(ol_))
        if best is None or key < best[0]: best = (key, sk_, ok_, xv)
        if b_ <= 11 and ok_: break
    _, sk, ok, xv = best
    print(json.dumps({'xvar': xv}))
    b, arr, ol = bound(sk, 8)
    print(json.dumps({'plans': plans, 'ok': ok, 'ANDs': len(sk['ands']), 'bound': b, 'outs': ol}), flush=True)
    if ok:
        model = core.Model.load('nist')
        cc = skeleton.synthesize(sk, {8, 6, 9, 3}, name='t4-b46')
        assert tuple(cc.value_table()) == tuple(targets.aes_sbox())
        mt = cc.metrics(model)
        print(json.dumps({'synth': {k: mt[k] for k in ('A', 'AD', 'G', 'GD')}}), flush=True)
        tag = '-'.join('%d%s' % (k, plans[k].replace(' ', '')) for k in sorted(plans))
        (outdir / ('syn-%s.circ.txt' % tag)).write_text(core.write_ncff(cc, model, comments=['T4 build46 plans %s' % plans]))
        (outdir / ('skel-%s.json' % tag)).write_text(json.dumps({'plans': plans, 'ands': [[hex(L), hex(R)] for L, R in sk['ands']], 'outputs': [hex(F) for F in sk['outputs']]}))
