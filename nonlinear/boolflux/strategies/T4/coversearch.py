#!/usr/bin/env python3
"""T4: replace the stage-1 cover of an AD4 circuit (which uses stage 1 only through N, see swap.py)
by any image g(C) of a known 9-cover C under G = {x -> a x^(2^i)} and compute the AND-skeleton
depth bound (F's Huffman bound) of the resulting skeleton.  Writes the best skeletons found.
    python3 coversearch.py CIRCUIT OUTDIR COVER_SOURCE_DIR...
"""
import sys, glob, os, json, heapq, itertools, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from rank2 import load, analyse, ONES  # noqa
from covers import covers_of, canon, GROUP, act_key, L_OF, A_OF  # noqa
from absorb import N_tables  # noqa
from boolflux import core, skeleton  # noqa

def huff(levels, const=False):
    if not levels: return 0
    if len(levels) == 1: return levels[0] + (1 if const else 0)
    h = list(levels); heapq.heapify(h)
    while len(h) > 1:
        a = heapq.heappop(h); b = heapq.heappop(h); heapq.heappush(h, max(a, b) + 1)
    return h[0]

def bound(sk, n):
    ands = sk['ands']; nb = 1 + n + len(ands); arr = [0] * nb
    for k, (L, R) in enumerate(ands):
        tl = [arr[p] for p in range(1, nb) if (L >> p) & 1]; tr_ = [arr[p] for p in range(1, nb) if (R >> p) & 1]
        arr[1 + n + k] = 1 + max(huff(tl, L & 1), huff(tr_, R & 1))
    ol = [huff([arr[p] for p in range(1, nb) if (F >> p) & 1], F & 1) for F in sk['outputs']]
    return max(ol), arr, ol

class TSpan:
    """span with tags (which generators combine to give the vector)"""
    def __init__(self): self.piv = {}
    def add(self, v, tag):
        for h in sorted(self.piv, reverse=True):
            if (v >> h) & 1: pv, pt = self.piv[h]; v ^= pv; tag ^= pt
        if v: self.piv[v.bit_length() - 1] = (v, tag); return True
        return False
    def express(self, v):
        tag = 0
        for h in sorted(self.piv, reverse=True):
            if (v >> h) & 1: pv, pt = self.piv[h]; v ^= pv; tag ^= pt
        return tag if v == 0 else None

def wt(l): return bin(l).count('1')
def lev(l): return 0 if wt(l) <= 1 else (wt(l) - 1).bit_length()

def lin_tab(l, X):
    t = 0
    for i in range(8):
        if (l >> i) & 1: t ^= X[i]
    return t

def options(key):
    """operand choices for a rank-2 form: 2 of the 3 nonzero vectors, each optionally complemented;
    returns list of (Lform, Rform) with bit 0 = constant, bit 1+i = x_i"""
    vs = sorted(key)
    out = []
    for u, v in ((vs[0], vs[1]), (vs[0], vs[2]), (vs[1], vs[2])):
        for c1 in (0, 1):
            for c2 in (0, 1):
                out.append(((u << 1) | c1, (v << 1) | c2))
    return out

def default_choice(key):
    vs = sorted(key, key=lambda l: (lev(l), wt(l)))
    return ((vs[0] << 1), (vs[1] << 1))

def ftab(F, X):
    t = ONES if F & 1 else 0
    for i in range(8):
        if (F >> (1 + i)) & 1: t ^= X[i]
    return t

def rebuild(sk, n, lvl1, oldA1tab, cover_keys, X, choice=None):
    """new skeleton with stage-1 products from cover_keys (list of 9 subspaces); choice = list of
    (Lform, Rform) per product (default: least-weight operands); returns skeleton or None"""
    prods = choice if choice is not None else [default_choice(k) for k in cover_keys]
    ts = TSpan()
    gens = [ONES] + X + [ftab(L, X) & ftab(R, X) for L, R in prods]
    for i, v in enumerate(gens): ts.add(v, 1 << i)
    # tag bit 0 = const, 1..8 = x_i, 9+j = product j  -> basis positions: 0, 1+i, 1+n+lvl1[j]
    def remap(tag):
        f = tag & 1
        for i in range(8):
            if (tag >> (1 + i)) & 1: f ^= 1 << (1 + i)
        for j in range(9):
            if (tag >> (9 + j)) & 1: f ^= 1 << (1 + n + lvl1[j])
        return f
    mask = 0
    for k in lvl1: mask |= 1 << (1 + n + k)
    def rewrite(F):
        part = F & mask
        if not part: return F
        t = 0
        for j, k in enumerate(lvl1):
            if (part >> (1 + n + k)) & 1: t ^= oldA1tab[j]
        tag = ts.express(t)
        if tag is None: return None
        return (F & ~mask) ^ remap(tag)
    # reorder: stage-1 products first (positions 0..8), then the other ANDs in original order
    others = [k for k in range(len(sk['ands'])) if k not in lvl1]
    order = list(lvl1) + others
    newpos = {k: i for i, k in enumerate(order)}
    def perm(F):
        G = F & ((1 << (1 + n)) - 1)
        for k in range(len(sk['ands'])):
            if (F >> (1 + n + k)) & 1: G |= 1 << (1 + n + newpos[k])
        return G
    ands = []
    for j, k in enumerate(lvl1):
        ands.append(prods[j])
    for k in others:
        L, R = sk['ands'][k]; L2, R2 = rewrite(L), rewrite(R)
        if L2 is None or R2 is None: return None
        ands.append((perm(L2), perm(R2)))
    outs = []
    for F in sk['outputs']:
        F2 = rewrite(F)
        if F2 is None: return None
        outs.append(perm(F2))
    return {'n': n, 'm': sk['m'], 'ands': ands, 'outputs': outs}

def optimise(sk, n, lvl1, oldA1tab, keys, X, passes=2):
    choice = [default_choice(k) for k in keys]
    def score(ch):
        nsk = rebuild(sk, n, lvl1, oldA1tab, keys, X, ch)
        if nsk is None: return (99,), None
        b, arr, ol = bound(nsk, n)
        return (b, sum(ol), sum(arr)), nsk
    best, bsk = score(choice)
    for _ in range(passes):
        improved = False
        for j, key in enumerate(keys):
            for opt in options(key):
                if opt == choice[j]: continue
                ch = list(choice); ch[j] = opt
                sc, nsk = score(ch)
                if sc < best: best, bsk, choice, improved = sc, nsk, ch, True
        if not improved: break
    return best, bsk, choice

def skel_check(sk):
    tab, ft, ones = skeleton._form_tables(sk)
    from boolflux import targets
    outs = [ft(F) for F in sk['outputs']]
    c = core.Circuit(8, 8, [], [])
    return outs == core.tables_from_values(8, 8, targets.aes_sbox())

if __name__ == '__main__':
    circ, outdir = sys.argv[1], Path(sys.argv[2]); outdir.mkdir(parents=True, exist_ok=True)
    c = load(circ); n = c.n
    T, lg, la, fa, ba, V, X0 = analyse(c)
    sk = skeleton.extract(c)
    ands_sig = [n + j for j, g in enumerate(c.gates) if g[0] in core.NONLINEAR_OPS]
    lvl1 = [k for k, s in enumerate(ands_sig) if la[s] == 1]
    assert len(lvl1) == 9
    oldA1tab = [T[ands_sig[k]] for k in lvl1]
    X = core.input_tables(8)
    b0, _, _ = bound(sk, n)
    own = covers_of(c)[0]
    idk = rebuild(sk, n, lvl1, oldA1tab, [frozenset(k) for k in own], X)
    sc, osk, och = optimise(sk, n, lvl1, oldA1tab, [frozenset(k) for k in own], X)
    print('start bound', b0, 'own cover rebuilt bound', bound(idk, n)[0], 'ok', skel_check(idk), 'optimised', sc, skel_check(osk), flush=True)
    if '--idonly' in sys.argv: sys.exit(0)
    files = []
    for d in [a for a in sys.argv[3:] if not a.startswith('--')]:
        files += sorted(glob.glob(os.path.join(d, '*.bfx'))) + sorted(glob.glob(os.path.join(d, '*.circ.txt')))
    raw = set()
    t0 = time.time()
    for f in files:
        try: cc = load(f)
        except Exception: continue
        for cov in covers_of(cc): raw.add(cov)
    classes = {}
    for cov in raw: classes.setdefault(canon(cov), cov)
    print('files', len(files), 'raw covers', len(raw), 'classes', len(classes), 'secs', round(time.time() - t0), flush=True)
    res = []
    hist = {}
    for ci, (ck, cov) in enumerate(classes.items()):
        for g in GROUP:
            keys = [act_key(x, g) for x in cov]
            # quick filter: stage-1 product levels
            pl = []
            for key in keys:
                vs = sorted(key, key=lambda l: (lev(l), wt(l)))
                pl.append(1 + max(lev(vs[0]), lev(vs[1])))
            nsk = rebuild(sk, n, lvl1, oldA1tab, keys, X)
            if nsk is None: continue
            b, arr, ol = bound(nsk, n)
            hist[b] = hist.get(b, 0) + 1
            res.append((b, sum(ol), max(pl), ci, g, nsk))
        print('class', ci, 'hist', hist, flush=True)
    res.sort(key=lambda r: (r[0], r[1]))
    for r in res[:10]:
        print(json.dumps({'bound': r[0], 'sum_out_levels': r[1], 'max_A1_level': r[2], 'class': r[3], 'g': r[4]}), flush=True)
    for i, r in enumerate(res[:20]):
        ok = skel_check(r[5])
        (outdir / ('skel-%02d-b%d.json' % (i, r[0]))).write_text(json.dumps({'bound': r[0], 'class': r[3], 'g': r[4], 'ok': ok, 'skel': {
            'n': r[5]['n'], 'm': r[5]['m'], 'ands': [[hex(L), hex(R)] for L, R in r[5]['ands']], 'outputs': [hex(F) for F in r[5]['outputs']]}}))
    print('done', flush=True)
