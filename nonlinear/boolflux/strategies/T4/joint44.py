#!/usr/bin/env python3
"""T4: joint search  stage-1 cover image  x  depth-3 inversion design (3 A2 + 4 A3, four direct
Y-forms)  x  rank-2 bottom with shared junk, for an AD-4 GD-11 S-box with fewer ANDs.

  depth   (fast47 level model) all four Y-forms at gate level <= 8 with the cover's affine-N levels
  savings (coinscore logic) x-junk classes modulo S1 = span(cover products) (alternating forms),
          d-junk free if sum Y_a Y_b in span(affine N, A2, A3) (functions of N)
Prints candidates with 16 + 32 - net ANDs, best first.
    python3 joint44.py DESIGNS.jsonl OUT.jsonl FRONT48 COVER_SOURCE_DIR...
"""
import sys, json, glob, os, itertools, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import inv6 as I  # noqa
import invdesign as D  # noqa
import fast47 as F  # noqa
from rank2 import load, analyse, ONES  # noqa
from covers import covers_of, canon, GROUP, act_key  # noqa
from chain import lin, wedge, qform, Red  # noqa
from absorb import N_tables  # noqa
from rank2 import ONES  # noqa
from coversearch import huff  # noqa

m, p = I.m256, I.p256
ONE16 = I.ONE
DES = [('p3', ((a, b),)) for a, b in itertools.combinations(range(4), 2)] + \
      [('p2', ((0, 1), (2, 3))), ('p2', ((0, 2), (1, 3))), ('p2', ((0, 3), (1, 2)))]
VN = [qform(t) for t in N_tables()]
_WC = {}


def wforms(basis):
    """per output k (NIST order): the x-linear forms w_ik with S_k = sum_i Tr(alpha_i Y) w_ik + const,
    solved exactly on truth tables (the decomposition is unique)"""
    key = tuple(basis)
    if key in _WC: return _WC[key]
    from coversearch import TSpan
    from boolflux import core, targets
    Nx = [p(x, 17) for x in range(256)]
    Xt = core.input_tables(8)
    Yt = [sum(((trY(a) >> I.IDX[Nx[x]]) & 1) << x for x in range(256)) for a in basis]
    ts = TSpan(); cols = []
    for i in range(4):
        for j in range(8): cols.append(Yt[i] & Xt[j])
        cols.append(Yt[i])
    cols.append(ONES)
    for t, v in enumerate(cols): ts.add(v, 1 << t)
    St = core.tables_from_values(8, 8, targets.aes_sbox())
    res = []
    for k in range(8):
        tag = ts.express(St[k])
        assert tag is not None, 'output not in Y (x) x span'
        ws = []
        for i in range(4):
            ws.append(sum(((tag >> (9 * i + j)) & 1) << j for j in range(8)))
        res.append(ws)
    _WC[key] = res
    return res


def trY(al): return I.tab(lambda z: I.tr16(m(al, D.inv(z))))


def rank16(vs):
    piv = {}
    for v in vs:
        while v:
            h = v.bit_length() - 1
            if h in piv: v ^= piv[h]
            else: piv[h] = v; break
    return piv


def in_span16(piv, v):
    while v:
        h = v.bit_length() - 1
        if h in piv: v ^= piv[h]
        else: return False
    return True


def score(hits_by_res, dfree, pfree=None):
    pfree = pfree or {}
    """best net saving: choose per output at most one design; classes need >= 2 outputs"""
    # nodes (k, di) with residue r; class = residue
    byres = collections.defaultdict(list)
    for r, L in hits_by_res.items():
        ks = {k for k, di in L}
        if len(ks) >= 2: byres[r] = L
    nodes = [v for L in byres.values() for v in L]
    res_of = {}
    for r, L in byres.items():
        for v in L: res_of[v] = r
    opts = collections.defaultdict(list)
    for v in nodes: opts[v[0]].append(v)
    outs = sorted(opts)
    best = (0, None)
    if sum(len(opts[o]) for o in outs) > 30:
        # too many: keep the 3 best options per output by design saving
        for o in outs: opts[o] = sorted(opts[o], key=lambda v: -(1 if DES[v[1]][0] == 'p3' else 2))[:3]

    def rec(i, chosen):
        nonlocal best
        if i == len(outs):
            if len(chosen) < 2: return
            sav = 0; cls = collections.defaultdict(list); dp = []
            for (k, di) in chosen:
                d = DES[di]; sav += 1 if d[0] == 'p3' else 2
                cls[res_of[(k, di)]].append((k, di))
                if not dfree[di]: dp.append(di)
            cost = 0
            for c, L in cls.items():
                if len({k for k, _ in L}) < 2: cost += 99
                else: cost += min(len(DES[di][1]) for k, di in L)
            # d-junk: one AND per non-free Y-pair among the chosen non-free designs
            pairs = set()
            for di in set(dp):
                for pr in DES[di][1]:
                    if not pfree.get(pr, False): pairs.add(pr)
            cost += len(pairs)
            if sav - cost > best[0]: best = (sav - cost, list(chosen))
            return
        rec(i + 1, chosen)
        for v in opts[outs[i]]:
            rec(i + 1, chosen + [v])
    rec(0, [])
    return best


if __name__ == '__main__':
    dfile, outf, front = sys.argv[1], sys.argv[2], sys.argv[3]
    designs = [json.loads(l) for l in open(dfile) if l.startswith('{')]
    # design options: (design index, four alphas)
    dopts = []
    for i, d in enumerate(designs):
        qs = d['A2']; real = D.realise(qs)
        A2ops = {j: [(a, b) for a in I.NONC for b in I.NONC if a < b and a & b == q] for j, q in enumerate(qs)}
        for four in itertools.combinations(sorted(real), 4):
            if not D.indep(four): continue
            dopts.append({'i': i, 'qs': qs, 'four': four, 'real': {a: real[a] for a in four}, 'A2ops': A2ops})
    print('design options', len(dopts), flush=True)
    raw = set()
    for dd in sys.argv[4:]:
        for ff in sorted(glob.glob(os.path.join(dd, '*.bfx'))) + sorted(glob.glob(os.path.join(dd, '*.circ.txt'))):
            try: cc = load(ff)
            except Exception: continue
            for cov in covers_of(cc): raw.add(cov)
    classes = {}
    for cov in raw: classes.setdefault(canon(cov), cov)
    covers = []
    # the front's own cover with its own operand variants first
    c48 = load(front); T, lg, la, fa, ba, V, X = analyse(c48)
    from boolflux import skeleton
    sk = skeleton.extract(c48)
    own = [sk['ands'][k] for k, s in enumerate([8 + j for j, g in enumerate(c48.gates) if g[0] in (8,)]) if la[s] == 1]
    own_keys = [frozenset({L >> 1, R >> 1, (L ^ R) >> 1}) for L, R in own]
    covers.append(('own', own_keys, own))
    for ci, cov in enumerate(classes.values()):
        for g in GROUP:
            covers.append(((ci, g), [act_key(x, g) for x in cov], None))
    print('covers', len(covers), flush=True)
    out = open(outf, 'w')
    best_total = 99; nc = 0
    for tag, keys, prods in covers:
        if prods is None:
            pl0 = [1 + max(F.lev(sorted(k, key=lambda l: (F.lev(l), F.wt(l)))[0]), F.lev(sorted(k, key=lambda l: (F.lev(l), F.wt(l)))[1])) for k in keys]
            if max(pl0) > 3: continue
            al, plev, prods = F.opt_variants(keys)
        else:
            al, plev, _ = F.cover_levels(keys, prods)
        if al is None: continue
        nc += 1
        S1 = Red(VN + [wedge(*sorted(k)[:2]) for k in keys])
        for o in dopts:
            po = {'qs': o['qs'], 'real': o['real'], 'A2ops': o['A2ops'], 'four': o['four'], 'fifth': None}
            w, a2lev = F.eval_option(po, al)
            if w > 8: continue
            # d-free designs: span of affine N, A2 and the A3 gates of the best realisations
            basis = list(o['four'])
            span = list(I.AFF) + list(o['qs']) + [x['a3'] for a in basis for x in o['real'][a]]
            piv = rank16(span)
            Ys = [trY(a) for a in basis]
            dfree = {}
            for di, d in enumerate(DES):
                s = 0
                for a, b in d[1]: s ^= Ys[a] & Ys[b]
                dfree[di] = in_span16(piv, s)
            ws = wforms(basis)
            byres = collections.defaultdict(list)
            for k in range(8):
                for di, d in enumerate(DES):
                    q = 0
                    for a, b in d[1]: q ^= wedge(ws[k][a], ws[k][b])
                    byres[S1.red(q)].append((k, di))
            pfree = {}
            for a, b in itertools.combinations(range(4), 2):
                pfree[(a, b)] = in_span16(piv, Ys[a] & Ys[b])
            net, ch = score(byres, dfree, pfree)
            tot = 48 - net
            if net >= 1:
                rec = {'cover': tag, 'design': o['i'], 'four': o['four'], 'net': net, 'A_est': tot,
                       'choice': [(k, DES[di][0], DES[di][1]) for k, di in ch], 'a2lev': a2lev,
                       'keys': [sorted(k) for k in keys], 'prods': prods}
                out.write(json.dumps(rec) + '\n'); out.flush()
                if tot < best_total:
                    best_total = tot
                    print(json.dumps({'new_best': tot, 'cover': tag, 'design': o['i'], 'four': o['four'], 'choice': rec['choice']}), flush=True)
        if nc % 20 == 0: print('covers evaluated', nc, 'best', best_total, flush=True)
    print('done; covers evaluated', nc, 'best', best_total, flush=True)
