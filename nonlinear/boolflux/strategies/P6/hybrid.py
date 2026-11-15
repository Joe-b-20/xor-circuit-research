#!/usr/bin/env python3
"""P6: hybrid depth-feasible construction: keep the parent's gates wherever their levels allow cap D.

    python3 hybrid.py FILE --cap 12 --out DIR [--n K] [--seed S] [--paar]

1. Re-base the level-3 classes (botbasis feasible triples; max output Kraft <= 1 at the cap).
2. Walk the lower ANDs in order.  arr[p] = level of basis position p in the circuit being built.
   An AND is reused from the parent (its gate and all parent gates under it) if, with arr[p] = its
   actual parent level, the skeleton bound of the rest (Huffman for everything not yet decided) is
   still <= D; otherwise it is rebuilt with the latest deadline that keeps the bound <= D, its
   operands covered by existing signals (parent linear signals included) + Huffman / Paar trees.
3. The new level-3 products and the outputs likewise (latest feasible deadlines), then dead gates
   are removed and the circuit is verified on all 256 inputs.
"""
import sys, random, argparse, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core, skeleton                        # noqa: E402
from boolflux.hub.common import verify, metrics, clean      # noqa: E402
import botbasis as BB                                       # noqa: E402
from skelan import anatomy                                  # noqa: E402
BB.anatomy = anatomy
from rebase import Builder, new_skeleton, feasible_triples, XOR, XNOR, NOT, AND   # noqa: E402
import paarb as PB                                          # noqa: E402


SLACK3 = True   # level-3 products get the latest deadline that keeps the bound (sequentially)


def bound_from(sk, arr0, fixed, n):
    """skeleton bound with arr fixed for positions in `fixed`, Huffman for the rest; returns max output level"""
    arr = list(arr0)
    for k, (L, R) in enumerate(sk['ands']):
        p = 1 + n + k
        if p in fixed: continue
        arr[p] = 1 + max(BB.huff([arr[q] for q in BB.bits(L) if q], L & 1), BB.huff([arr[q] for q in BB.bits(R) if q], R & 1))
    return max(BB.huff([arr[q] for q in BB.bits(F) if q], F & 1) for F in sk['outputs']), arr


def hybrid(c, res, tri, cap, rng=None, use_paar=False):
    n = c.n
    sk = new_skeleton(c, res, tri)
    # parent AND gate index per parent skeleton position; parent level-3 positions
    psk = skeleton.extract(c)
    pal = anatomy(c)[2]
    l3 = {1 + n + kk for pc in res['_pc'] for kk in pc['ands']}
    keep = [k for k in range(len(psk['ands'])) if 1 + n + k not in l3]
    remap = {1 + n + k: 1 + n + i for i, k in enumerate(keep)}
    B = Builder(c)
    # remap parent forms; drop signals that depend on parent level-3 ANDs
    newform = []
    for s, f in enumerate(B.form):
        if f is None: newform.append(None); continue
        if any(p in l3 for p in BB.bits(f)):
            newform.append(None); continue
        g = f & 1
        for p in BB.bits(f):
            if p: g |= 1 << (remap.get(p, p))
        newform.append(g)
    # AND gates: their own form is the basis position (constant r)
    B.form = newform
    # structural AND cone of every parent signal (new positions; bit 0 = some parent level-3 AND)
    cone = [0] * n; kq = 0
    for j, (op, a, b) in enumerate(c.gates):
        cc = cone[a] | cone[b]
        if op not in (XOR, XNOR, NOT):
            pp = 1 + n + kq; kq += 1
            cc |= 1 if pp in l3 else (1 << remap[pp])
        cone.append(cc)
    npar = len(B.form)
    def refresh(reused_mask):
        B.by = {}
        for s, f in enumerate(B.form):
            if f is None: continue
            if s < npar and (cone[s] & ~reused_mask): continue
            key = f & ~1
            if key and (key not in B.by or B.lv[s] < B.lv[B.by[key]]): B.by[key] = s
    reused_mask = 0
    refresh(reused_mask)
    # parent AND signal per new position
    pand = {}
    k = 0
    for j, (op, a, b) in enumerate(c.gates):
        if op not in (XOR, XNOR, NOT):
            p = 1 + n + k; k += 1
            if p in remap: pand[remap[p]] = n + j
    nb = 1 + n + len(sk['ands'])
    arr = [0] * nb; fixed = set(); stats = {'reused': 0, 'rebuilt': 0}
    nlow = len(keep)
    for kk, (L, R) in enumerate(sk['ands']):
        p = 1 + n + kk
        if use_paar and kk >= nlow:
            break
        refresh(reused_mask)
        if p in pand and (cone[pand[p]] & ~(reused_mask | (1 << p))) == 0:
            s = pand[p]; arr[p] = B.lv[s]
            bd, _ = bound_from(sk, arr, fixed | {p}, n)
            if bd <= cap:
                fixed.add(p); stats['reused'] += 1
                reused_mask |= 1 << p
                continue
        # rebuild with the latest feasible deadline
        hl = BB.huff([arr[q] for q in BB.bits(L) if q], L & 1)
        hr = BB.huff([arr[q] for q in BB.bits(R) if q], R & 1)
        d0 = max(hl, hr)
        d = d0
        for dd in range(d0 + 3, d0, -1):
            arr[p] = dd + 1
            bd, _ = bound_from(sk, arr, fixed | {p}, n)
            if bd <= cap: d = dd; break
        if use_paar:
            sl, sr = PB.layer_build(B, [(L, d), (R, d)], rng)
        else:
            sl = B.build(L, d, rng); sr = B.build(R, d, rng)
        s = B.new(AND, sl, sr); B.kind[-1] = 'and'
        B.form[s] = 1 << p; B.by[1 << p] = s; arr[p] = B.lv[s]; fixed.add(p)
        stats['rebuilt'] += 1
    refresh(reused_mask)
    if use_paar:
        # the re-based level-3 products: all operands in one shared layer, Huffman-earliest deadlines
        tg = []; ps3 = []
        for kk in range(nlow, len(sk['ands'])):
            L, R = sk['ands'][kk]; p = 1 + n + kk
            d = max(BB.huff([arr[q] for q in BB.bits(L) if q], L & 1), BB.huff([arr[q] for q in BB.bits(R) if q], R & 1))
            if SLACK3:
                for dd in range(d + 2, d, -1):
                    arr[p] = dd + 1
                    bd, _ = bound_from(sk, arr, fixed | {p}, n)
                    if bd <= cap: d = dd; break
                arr[p] = d + 1; fixed.add(p)
            tg += [(L, d), (R, d)]; ps3.append(p)
        sigs = PB.layer_build(B, tg, rng)
        for i, p in enumerate(ps3):
            s = B.new(AND, sigs[2 * i], sigs[2 * i + 1]); B.kind[-1] = 'and'
            B.form[s] = 1 << p; B.by[1 << p] = s; arr[p] = B.lv[s]; fixed.add(p); stats['rebuilt'] += 1
        outs = PB.layer_build(B, [(F, cap) for F in sk['outputs']], rng)
    else:
        outs = [B.build(F, cap, rng) for F in sk['outputs']]
    nc = core.Circuit(n, c.m, B.gates, outs, 'hybrid', c.in_names, c.out_names).live()
    return clean(nc), stats


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('file'); ap.add_argument('--cap', type=int, default=12)
    ap.add_argument('--out', required=True); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--n', type=int, default=1); ap.add_argument('--paar', action='store_true')
    a = ap.parse_args()
    c = BB.load(a.file)
    res = BB.analyse(a.file, a.cap, verbose=False)
    T = feasible_triples(res)
    print('feasible triples (Pareto reps):', len(T), 'best max Kraft', res['best'], flush=True)
    rng = random.Random(a.seed)
    outdir = Path(a.out); outdir.mkdir(parents=True, exist_ok=True)
    rows = []; bestg = None
    for it in range(a.n):
        tri = T[it] if it < len(T) else rng.choice(T)
        nc, st = hybrid(c, res, tri, a.cap, rng if it >= len(T) else None, a.paar)
        ok, inf = verify(nc); m = metrics(nc)
        rows.append({'it': it, 'ok': ok, 'm': m, 'triple': tri, 'stats': st})
        if ok and m[3] <= a.cap and (bestg is None or m[2] < bestg):
            bestg = m[2]
            p = outdir / ('hy-a%d-ad%d-g%d-gd%d-s%d-%d.bfx' % (m[0], m[1], m[2], m[3], a.seed, it))
            p.write_text(core.to_kernel(nc)); rows[-1]['file'] = str(p)
            print(it, ok, m, tri, st, p.name, flush=True)
    json.dump({'parent': str(Path(a.file).resolve()), 'seed': a.seed, 'paar': a.paar, 'rows': rows},
              open(outdir / ('hybrid-s%d.json' % a.seed), 'w'), indent=1)
    gs = sorted(r['m'][2] for r in rows if r['ok'] and r['m'][3] <= a.cap)
    print('GD<=cap builds %d/%d' % (len(gs), len(rows)), 'G min/median', gs[0] if gs else None, gs[len(gs) // 2] if gs else None)


if __name__ == '__main__':
    main()
