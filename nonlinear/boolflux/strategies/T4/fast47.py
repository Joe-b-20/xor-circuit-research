#!/usr/bin/env python3
"""T4: joint search over stage-1 covers (images g(C) of the known 9-cover classes) and 7-AND
inversion options (designs180.jsonl, all7 with share5 >= 1) for a 47-AND GD-11 skeleton:
all Y-forms (incl. the 5th = A3_x + A3_y) at gate level <= 8.
Level model: affine function of N = Huffman over its unique (1, x, stage-1) representation;
A2 = 1 + max(operand levels) (best operand pair); complemented A2 operand +1 (NOT);
A3 = 1 + max(operand levels); Y-form = Huffman(A3, residual terms).
    python3 fast47.py DESIGNS.jsonl OUT.jsonl COVER_SOURCE_DIR...
"""
import sys, json, glob, os, itertools
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import inv6 as I  # noqa
import invdesign as D  # noqa
from rank2 import load, ONES  # noqa
from covers import covers_of, canon, GROUP, act_key  # noqa
from coversearch import TSpan, huff, lev, wt, ftab, default_choice  # noqa
from boolflux import core  # noqa

ONE16 = I.ONE
X = core.input_tables(8)
Nx = [I.p256(x, 17) for x in range(256)]
def lift(f16): return sum(((f16 >> I.IDX[Nx[x]]) & 1) << x for x in range(256))
AFFN = [f for f in I.AFF if f not in (0, ONE16)]
LIFT = {f: lift(f) for f in AFFN}


def cover_levels(keys, prods=None):
    prods = prods or [default_choice(k) for k in keys]
    plev = [1 + max(huff([0] * bin(L >> 1).count('1'), L & 1), huff([0] * bin(R >> 1).count('1'), R & 1)) for L, R in prods]
    ts = TSpan()
    for i, v in enumerate([ONES] + X + [ftab(L, X) & ftab(R, X) for L, R in prods]): ts.add(v, 1 << i)
    al = {0: 0, ONE16: 0}
    for f in AFFN:
        tag = ts.express(LIFT[f])
        if tag is None: return None, None, None
        terms = [0] * bin((tag >> 1) & 0xff).count('1') + [plev[j] for j in range(9) if (tag >> (9 + j)) & 1]
        al[f] = huff(terms, tag & 1)
    return al, plev, prods


def opt_variants(keys, passes=2):
    """greedy choice of operand pair / polarity per product maximising (#affine at <= 5, #at <= 6)"""
    from coversearch import options
    prods = [default_choice(k) for k in keys]
    def score(pr):
        al, plev, _ = cover_levels(keys, pr)
        if al is None: return (-1, -1), None, None
        return (sum(1 for f in AFFN if al[f] <= 5), sum(1 for f in AFFN if al[f] <= 6)), al, plev
    best, bal, bpl = score(prods)
    for _ in range(passes):
        imp = False
        for j, k in enumerate(keys):
            for o in options(k):
                if o == prods[j]: continue
                pr = list(prods); pr[j] = o
                sc, al, pl = score(pr)
                if sc > best: best, bal, bpl, prods, imp = sc, al, pl, pr, True
        if not imp: break
    return bal, bpl, prods


def prep_option(d, r):
    qs = d['A2']
    real = D.realise(qs)
    A2ops = {}
    for i, q in enumerate(qs):
        A2ops[i] = [(a, b) for a in I.NONC for b in I.NONC if a < b and a & b == q]
    return {'qs': qs, 'real': {al: real[al] for al in set(r['four'])}, 'A2ops': A2ops, 'four': r['four'], 'fifth': r['fifth'], 'opt': r}


def eval_option(po, al):
    qs = po['qs']
    a2lev = [1 + min(max(al[a], al[b]) for a, b in po['A2ops'][i]) for i in range(len(qs))]
    def l6(f):
        for i, q in enumerate(qs):
            if f == q: return a2lev[i]
            if f == q ^ ONE16: return a2lev[i] + 1
        return al[f]
    def rl(res):
        k = res[0]
        if k == 'aff': return [al[res[1]]] if res[1] not in (0, ONE16) else []
        if k == 'A2+aff': return [a2lev[res[1]]] + ([al[res[2]]] if res[2] not in (0, ONE16) else [])
        return [a2lev[res[1]], a2lev[res[2]]]
    def yl(dd):
        a3 = 1 + max(l6(dd['p']), l6(dd['r']))
        return huff([a3] + rl(dd['res'])), a3
    best = {a: min(yl(dd)[0] for dd in po['real'][a]) for a in po['four']}
    worst = max(best.values())
    if po['fifth'] is not None:
        x, y = [(x, y) for x, y in itertools.combinations(po['four'], 2) if x ^ y == po['fifth']][0]
        bp = None
        for dx in po['real'][x]:
            yx = yl(dx)
            for dy in po['real'][y]:
                if dx['res'] != dy['res'] or dx['a3'] == dy['a3']: continue
                yy = yl(dy)
                sc = max(yx[0], yy[0], 1 + max(yx[1], yy[1]))
                if bp is None or sc < bp: bp = sc
        if bp is None: return 99, a2lev
        others = [best[a] for a in po['four'] if a not in (x, y)]
        worst = max(others + [bp])
    return worst, a2lev


if __name__ == '__main__':
    dfile, outf = sys.argv[1], sys.argv[2]
    designs = [json.loads(l) for l in open(dfile) if l.startswith('{')]
    opts = []
    for i, d in enumerate(designs):
        for oi, r in enumerate(d.get('all7') or []):
            if r['share5'] >= 1: opts.append((i, oi, prep_option(d, r)))
    print('options', len(opts), flush=True)
    files = []
    for dd in sys.argv[3:]:
        files += sorted(glob.glob(os.path.join(dd, '*.bfx'))) + sorted(glob.glob(os.path.join(dd, '*.circ.txt')))
    raw = set()
    for f in files:
        try: cc = load(f)
        except Exception: continue
        for cov in covers_of(cc): raw.add(cov)
    classes = {}
    for cov in raw: classes.setdefault(canon(cov), cov)
    print('cover classes', len(classes), flush=True)
    out = open(outf, 'w')
    nbest = 99; cnt = 0
    for ci, cov in enumerate(classes.values()):
        for g in GROUP:
            keys = [act_key(x, g) for x in cov]
            pl0 = [1 + max(lev(sorted(k, key=lambda l: (lev(l), wt(l)))[0]), lev(sorted(k, key=lambda l: (lev(l), wt(l)))[1])) for k in keys]
            if max(pl0) > 3: continue
            al, plev, prods = opt_variants(keys)
            if al is None: continue
            n5 = sum(1 for f in AFFN if al[f] <= 5)
            if n5 < 6: continue
            cnt += 1
            for (i, oi, po) in opts:
                w, a2lev = eval_option(po, al)
                if w <= 8:
                    rec = {'class': ci, 'g': g, 'design': i, 'opt': oi, 'ymax': w, 'a2lev': a2lev, 'plev': plev, 'n5': n5,
                           'keys': [sorted(k) for k in keys], 'prods': prods}
                    out.write(json.dumps(rec) + '\n'); out.flush()
                nbest = min(nbest, w)
        print('class', ci, 'covers evaluated', cnt, 'best ymax', nbest, flush=True)
    print('done', flush=True)
