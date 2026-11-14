#!/usr/bin/env python3
"""Form-level stage transplant (Track E, M3c).

Back of Y = Y's ANDs of level > LY, as products of affine forms over (1, x, Y's ANDs).  Each operand
form and each output form is split into its back part (back ANDs) and its front part (a Boolean
function of x computed by Y's front).  The front parts only need to lie in the affine span of X's
front (inputs + X's ANDs of level <= LX); individual Y front signals need not exist in X.  The new
skeleton = X's front ANDs (forms copied) + Y's back ANDs (re-expressed) is synthesised with X as the
seeding parent (X's front gates kept) and checked on all 256 inputs.

    python3 splice3.py OUTDIR FILE...        (or one FILE.list)  [--maxA K]
"""
import json, sys, time, hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import core, load, metrics, correct, ONES, MODEL, SBOX   # noqa: E402
import skeleton_e as skeleton   # noqa: E402


def and_levels(sk, n):
    lv = []
    for k, (L, R) in enumerate(sk['ands']):
        deps = [j for j in range(k) if ((L | R) >> (1 + n + j)) & 1]
        lv.append(1 + max([lv[j] for j in deps], default=0))
    return lv


def form_tables(sk, n):
    it = core.input_tables(n)
    tab = [ONES] + it
    def ft(f):
        t = 0; i = 0
        while f:
            if f & 1: t ^= tab[i]
            f >>= 1; i += 1
        return t
    for L, R in sk['ands']: tab.append(ft(L) & ft(R))
    return tab, ft


class Info:
    def __init__(self, name, c):
        self.name = name; self.c = c; self.n = c.n
        self.sk = skeleton.extract(c)
        self.lv = and_levels(self.sk, c.n)
        self.tab, self.ft = form_tables(self.sk, c.n)
        self.m = tuple(metrics(c))


def front_basis(X, LX):
    """positions kept (const, inputs, front ANDs), elimination rows over their tables -> new-position forms"""
    n = X.n
    keep = [k for k in range(len(X.sk['ands'])) if X.lv[k] <= LX]
    newpos = {1 + n + k: 1 + n + i for i, k in enumerate(keep)}
    for i in range(1 + n): newpos[i] = i
    piv = []
    for p_old, p_new in sorted(newpos.items()):
        t = X.tab[p_old]; f = 1 << p_new
        for pb, rt, rf in piv:
            if (t >> pb) & 1: t ^= rt; f ^= rf
        if t: piv.append((t.bit_length() - 1, t, f)); piv.sort(key=lambda r: -r[0])
    return keep, newpos, piv


def express(piv, t):
    f = 0
    for pb, rt, rf in piv:
        if (t >> pb) & 1: t ^= rt; f ^= rf
    return f if t == 0 else None


def remap(f, newpos):
    g = 0; i = 0
    while f:
        if f & 1: g |= 1 << newpos[i]
        f >>= 1; i += 1
    return g


def splice3(X, LX, fb, Y, LY):
    keep, newpos, piv = fb
    n = X.n; nf = len(keep)
    ands = [(remap(L, newpos), remap(R, newpos)) for k, (L, R) in enumerate(X.sk['ands']) if k in set(keep)]
    back = [k for k in range(len(Y.sk['ands'])) if Y.lv[k] > LY]
    if not back: return None
    bpos = {1 + n + k: 1 + n + nf + i for i, k in enumerate(back)}
    backmask = 0
    for p in bpos: backmask |= 1 << p

    def tr(f):
        fb_ = f & backmask; ff = f & ~backmask
        e = express(piv, Y.ft(ff))
        if e is None: return None
        g = e; i = 0; x = fb_
        while x:
            if x & 1: g |= 1 << bpos[i]
            x >>= 1; i += 1
        return g
    for k in back:
        L, R = Y.sk['ands'][k]
        a, b = tr(L), tr(R)
        if a is None or b is None: return None
        ands.append((a, b))
    outs = []
    for o in Y.sk['outputs']:
        g = tr(o)
        if g is None: return None
        outs.append(g)
    sk = {'n': n, 'm': Y.c.m, 'ands': ands, 'outputs': outs}
    best = None
    for kw in ({'parent': X.c}, {'use_paar': True, 'paar_outputs': True}):
        try:
            c = skeleton.synthesize(sk, MODEL.ops(), name='s3', **kw)
        except Exception:
            continue
        if c.value_table() != SBOX: continue
        if best is None or len(c.gates) < len(best.gates): best = c
    return best


def main():
    out = Path(sys.argv[1]); (out / 'cands').mkdir(parents=True, exist_ok=True)
    args = sys.argv[2:]; maxA = 99
    if '--maxA' in args:
        i = args.index('--maxA'); maxA = int(args[i + 1]); del args[i:i + 2]
    if len(args) == 1 and args[0].endswith('.list'): args = Path(args[0]).read_text().split()
    infos = []; seen_k = set()
    for f in args:
        c = load(f)
        if not correct(c): continue
        k = core.to_kernel(c)
        if k in seen_k: continue
        seen_k.add(k); infos.append(Info(Path(f).name, c))
    print('circuits', len(infos), flush=True)
    sys.path.insert(0, str(HERE.parents[1] / 'campaigns'))
    import aes_check
    pub = [u for (u, nm) in aes_check.published()]
    rows = []; seen = set(); t0 = time.time(); tried = 0; feas = 0
    for X in infos:
        fbs = {LX: front_basis(X, LX) for LX in range(1, X.m[1])}
        for Y in infos:
            if X is Y: continue
            for LY in range(1, Y.m[1]):
                nb = sum(1 for k in range(len(Y.sk['ands'])) if Y.lv[k] > LY)
                for LX in range(1, X.m[1]):
                    nfr = len(fbs[LX][0])
                    if nfr + nb > maxA: continue
                    tried += 1
                    c = splice3(X, LX, fbs[LX], Y, LY)
                    if c is None: continue
                    feas += 1
                    m = tuple(metrics(c))
                    h = hashlib.sha1(core.to_kernel(c).encode()).hexdigest()[:16]
                    if h in seen: continue
                    seen.add(h)
                    gs = [u[2] for u in pub if u[0] <= m[0] and u[1] <= m[1] and u[3] <= m[3]]
                    need = max(0, m[2] - min(gs) + 1) if gs else 0
                    (out / 'cands' / (h + '.bfx')).write_text(core.to_kernel(c))
                    rows.append({'X': X.name, 'Y': Y.name, 'LX': LX, 'LY': LY, 'metrics': m, 'need': need, 'h': h})
        print('X %s tried %d feasible %d distinct %d %.0f s' % (X.name[:40], tried, feas, len(seen), time.time() - t0), flush=True)
    rows.sort(key=lambda r: (r['metrics'][0], r['need'], r['metrics'][2]))
    (out / 'splices.json').write_text(json.dumps(rows))
    for r in rows[:60]:
        print(r['need'], r['metrics'], r['X'][:36], '<-', r['Y'][:36], 'LX', r['LX'], 'LY', r['LY'])


if __name__ == '__main__':
    main()
