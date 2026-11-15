#!/usr/bin/env python3
"""T4: build a GD-11-shaped AES S-box skeleton: a donor circuit's stage 1 (9 products, N = x^17),
an explicit depth-3 GF(16) inversion with 3 A2 + 4 A3 gates (inv6/invdesign model) giving 4 direct
Y-forms + a 5th Y-form = XOR of two A3 gates (equal residuals), and a bottom of rank-1 products
Tr(alpha Y) * Tr(beta R_k(x)) with the y5/y6 products shared.  Writes skeleton + synthesized circuit.
    python3 build47.py DONOR DESIGN_INDEX DESIGNS.jsonl OUTDIR [PICK]
"""
import sys, json, itertools
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import inv6 as I  # noqa
import invdesign as D  # noqa
from rank2 import load, analyse, ONES  # noqa
from chain import lin  # noqa
from coversearch import TSpan, bound  # noqa
from boolflux import core, skeleton, targets  # noqa

m, p = I.m256, I.p256
SUB, IDX, ONE16 = I.SUB, I.IDX, I.ONE


def build(donor, design, pick=0, bases_override=None):
    c = load(donor); n = c.n
    T, lg, la, fa, ba, V, X0 = analyse(c)
    sk0 = skeleton.extract(c)
    ands_sig = [n + j for j, g in enumerate(c.gates) if g[0] in core.NONLINEAR_OPS]
    lvl1 = [k for k, s in enumerate(ands_sig) if la[s] == 1]
    X = core.input_tables(8)
    st1 = [sk0['ands'][k] for k in lvl1]
    for L, R in st1:
        assert L >> (1 + n) == 0 and R >> (1 + n) == 0
    P = [T[ands_sig[k]] for k in lvl1]
    ts = TSpan()
    for i, v in enumerate([ONES] + X + P): ts.add(v, 1 << i)

    def pos_and(j): return 1 << (1 + n + j)

    def form_of_tag(tag):
        f = tag & 1
        for i in range(8):
            if (tag >> (1 + i)) & 1: f |= 1 << (1 + i)
        for j in range(9):
            if (tag >> (9 + j)) & 1: f |= pos_and(j)
        return f
    Nx = [p(x, 17) for x in range(256)]

    def lift(f16):
        return sum(((f16 >> IDX[Nx[x]]) & 1) << x for x in range(256))

    def aff_form(f16):
        tag = ts.express(lift(f16))
        assert tag is not None, 'affine function of N not in span'
        return form_of_tag(tag)
    qs = design['A2']
    from coversearch import huff
    st1lev = [1 + max(huff([0] * bin(L >> 1).count('1'), L & 1), huff([0] * bin(R >> 1).count('1'), R & 1)) for L, R in st1]
    def flev(f):
        """Huffman level of a form over (const, x, stage-1 products)"""
        terms = [0] * bin((f >> 1) & 0xff).count('1') + [st1lev[j] for j in range(9) if (f >> (1 + n + j)) & 1]
        return huff(terms, f & 1)
    def alev(f16):
        if f16 in (0, ONE16): return 0
        return flev(aff_form(f16))
    A2ops = []; a2lev = []
    for q in qs:
        cands = [(max(alev(a), alev(b)), a, b) for a in I.NONC for b in I.NONC if a < b and a & b == q]
        assert cands, 'no operands for A2'
        lv, a, b = min(cands)
        A2ops.append((a, b)); a2lev.append(1 + lv)
    def l6lev(f16):
        for i, q in enumerate(qs):
            if f16 == q: return a2lev[i]
            if f16 == q ^ ONE16: return a2lev[i] + 1        # NOT gate
        return alev(f16)
    def reslev(res):
        k = res[0]
        if k == 'aff': return [alev(res[1])] if res[1] not in (0, ONE16) else []
        if k == 'A2+aff': return [a2lev[res[1]]] + ([alev(res[2])] if res[2] not in (0, ONE16) else [])
        return [a2lev[res[1]], a2lev[res[2]]]
    def ylev(d):
        a3 = 1 + max(l6lev(d['p']), l6lev(d['r']))
        return (huff([a3] + reslev(d['res'])), a3)
    real = D.realise(qs)
    for al in real: real[al].sort(key=ylev)
    four = design['best7']['four']; fifth = design['best7']['fifth']
    fx = fy = None
    if fifth is not None:
        for x, y in itertools.combinations(four, 2):
            if x ^ y == fifth:
                best = None
                for dx in real[x]:
                    for dy in real[y]:
                        if dx['res'] == dy['res'] and dx['a3'] != dy['a3']:
                            sc = (max(ylev(dx)[0], ylev(dy)[0], 1 + max(ylev(dx)[1], ylev(dy)[1])), ylev(dx), ylev(dy))
                            if best is None or sc < best[0]: best = (sc, (x, dx), (y, dy))
                if best: fx, fy = best[1], best[2]
            if fx: break
        assert fx, 'fifth not realisable'
    chosen = {}
    for al in four:
        if fx and al == fx[0]: chosen[al] = fx[1]
        elif fx and al == fy[0]: chosen[al] = fy[1]
        else: chosen[al] = real[al][pick % len(real[al])]
    ands = [(L, R) for L, R in st1]
    a2pos = []
    for (a, b) in A2ops:
        ands.append((aff_form(a), aff_form(b))); a2pos.append(len(ands) - 1)

    def l6_form(f16):
        for i, q in enumerate(qs):
            if f16 == q: return pos_and(a2pos[i])
            if f16 == q ^ ONE16: return pos_and(a2pos[i]) | 1
        return aff_form(f16)
    a3pos = {}
    for al in four:
        d = chosen[al]
        ands.append((l6_form(d['p']), l6_form(d['r']))); a3pos[al] = len(ands) - 1

    def cform(f16):
        if f16 == 0: return 0
        if f16 == ONE16: return 1
        return aff_form(f16)

    def res_form(res):
        kind = res[0]
        if kind == 'aff': return cform(res[1])
        if kind == 'A2+aff': return pos_and(a2pos[res[1]]) ^ cform(res[2])
        if kind == 'A2+A2': return pos_and(a2pos[res[1]]) ^ pos_and(a2pos[res[2]]) ^ (1 if res[3] else 0)

    def trY(al):
        return I.tab(lambda z: I.tr16(m(al, D.inv(z))))
    Yform = {}
    for al in four:
        d = chosen[al]
        f = pos_and(a3pos[al]) ^ res_form(d['res'])
        if d['t'] != trY(al): f ^= 1
        Yform[al] = f
    if fifth is not None:
        val = Yform[fx[0]] ^ Yform[fy[0]]
        assert val & ~1 == pos_and(a3pos[fx[0]]) ^ pos_and(a3pos[fy[0]])
        Yform[fifth] = val
    sbox = targets.aes_sbox()
    outs_t = core.tables_from_values(8, 8, sbox)
    bases = {j: tuple(four) for j in range(8)}
    if design['best7'].get('A_y5'):
        bases[5] = tuple(design['best7']['A_y5']); bases[6] = tuple(design['best7']['A_y6'])
    if bases_override: bases.update(bases_override)
    prodidx = {}
    outforms = []
    for j in range(8):
        th = D.TH[7 - j]
        B = list(bases[j]); dB = D.dual(B)
        f = 0
        for al, be in zip(B, dB):
            wt = sum(I.tr16(m(be, m(th, p(x, 16)) ^ m(p(th, 16), x))) << x for x in range(256))
            assert wt & 1 == 0
            wl = lin(wt)
            key = (al, wl)
            if key not in prodidx:
                ands.append((Yform[al], wl << 1)); prodidx[key] = len(ands) - 1
            f ^= pos_and(prodidx[key])
        outforms.append(f)
    sk = {'n': 8, 'm': 8, 'ands': ands, 'outputs': outforms}
    tab, ft, ones = skeleton._form_tables(sk)
    for j in range(8):
        if ft(outforms[j]) ^ outs_t[j] == ones: outforms[j] ^= 1
    ok = all(ft(outforms[j]) == outs_t[j] for j in range(8))
    b, arr, ol = bound(sk, 8)
    return sk, ok, b, len(ands), len(prodidx)


if __name__ == '__main__':
    donor, idx, dfile, outdir = sys.argv[1], int(sys.argv[2]), sys.argv[3], Path(sys.argv[4])
    pick = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    outdir.mkdir(parents=True, exist_ok=True)
    designs = [json.loads(l) for l in open(dfile) if l.startswith('{')]
    design = designs[idx]
    sk, ok, b, nA, nb = build(donor, design, pick)
    print(json.dumps({'design': idx, 'skeleton_ok': ok, 'bound': b, 'ANDs': nA, 'bottom': nb}), flush=True)
    if ok:
        model = core.Model.load('nist')
        c = skeleton.synthesize(sk, {8, 6, 9, 3}, name='t4-b47')
        assert tuple(c.value_table()) == tuple(targets.aes_sbox())
        mt = c.metrics(model)
        print(json.dumps({'synth': {k: mt[k] for k in ('A', 'AD', 'G', 'GD')}}), flush=True)
        tag = 'd%d-p%d' % (idx, pick)
        (outdir / ('syn-%s.circ.txt' % tag)).write_text(core.write_ncff(c, model, comments=['T4 build47 design %d pick %d' % (idx, pick)]))
        (outdir / ('skel-%s.json' % tag)).write_text(json.dumps({'ands': [[hex(L), hex(R)] for L, R in sk['ands']], 'outputs': [hex(F) for F in sk['outputs']]}))
