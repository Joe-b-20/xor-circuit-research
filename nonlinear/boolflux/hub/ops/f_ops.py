"""Track-F operators and generators for the hub (registered into hub/ops.py's OPS table, same CLI).

    python3 hub/ops/op_osc.py      --archive DIR --in ID --seed S --seconds T --out JOBDIR [--caps A,AD,GD]
    python3 hub/ops/gen_inv3.py    --archive DIR --in ID --seed S --seconds T --out JOBDIR [--caps ...]
    python3 hub/ops/gen_bottom.py  --archive DIR --in ID [--in2 ID] --seed S --seconds T --out JOBDIR

  osc        depth oscillation: kernel under GD cap + 1 (input's AD/A caps), then the kernel's repair
             back to the input's caps (or --caps), then a polish under those caps.  Measured on
             122@GD14 (track F A/B, NOTES.md 4): repairs feasible 50/65, relaxed stage reaches
             118@GD15 in seconds; no gain below 122 in 2.9 CPU-h.
  gen_inv3   generator: replaces the GF(2^4) inversion block of a tower-field (BP-style) input by
             depth-3 blocks (library hub/ops/inv_designs/, 22-27 gates + pair sums, extra inputs
             x0^x2/x1^x3 etc. built at the inversion-input level by table lookup), optionally new
             blocks synthesised on the fly (invsyn annealing, extras chosen at random); every
             candidate is a complete circuit (AD unchanged class, GD typically -1).  On NIST
             116@GD15 it gives 122@GD14 A37 directly.
  gen_bottom generator: keeps the input's front and inversion, takes the AND-level-4 products and
             output XORs of a donor (--in2, else random archive members with AD4); missing
             y-combinations / top forms rebuilt from the input's signals by table lookup.
All candidates are checked here on all 256 inputs before they are written; the hub admits.
"""
from __future__ import annotations

import random
import sys
import time
from pathlib import Path

OPS_DIR = Path(__file__).resolve().parent
HUBDIR = OPS_DIR.parent
sys.path.insert(0, str(HUBDIR.parents[1]))          # nonlinear/ (for `boolflux`)
sys.path.insert(0, str(OPS_DIR / 'f_lib'))

from boolflux.hub import ops as HO                 # noqa: E402  (E's hub/ops.py)
from boolflux.hub.common import core, metrics, sbox   # noqa: E402


def _ok(c):
    return tuple(c.value_table()) == sbox()


def op_osc(ar, args, rng, out):
    c = ar.circuit(args.inp); A, AD, G, GD = metrics(c)
    # A cap = the input's own (review 5 H8; until 2026-11-14 osc ran without an A cap and could trade
    # ANDs for gates; `--caps=-,AD,GD` gives the old behaviour)
    caps = dict(args.caps or {'A': A, 'AD': AD, 'GD': GD})
    relaxed = dict(caps); relaxed['GD'] = (caps['GD'] or GD) + 1
    t = args.seconds
    s1 = out / 'relax'; s1.mkdir(exist_ok=True)
    c1, i1 = HO._kernel(c, relaxed, args.objective, args.seed, t * 0.3, s1, args.archive)
    c1 = c1[0] if c1 else c
    s2 = out / 'repair'; s2.mkdir(exist_ok=True)
    c2, i2 = HO._kernel(c1, caps, args.objective, args.seed + 7, t * 0.4, s2, args.archive)
    c2 = c2[0] if c2 else c1
    s3 = out / 'polish'; s3.mkdir(exist_ok=True)
    c3, i3 = HO._kernel(c2, caps, args.objective, args.seed + 13, t * 0.3, s3, args.archive)
    cands = [x for x in [c3[0] if c3 else None, c2] if x is not None and _ok(x)]
    return cands, {'caps': caps, 'relaxed_caps': relaxed, 'relaxed_metrics': metrics(c1), 'repaired_metrics': metrics(c2)}


def op_gen_inv3(ar, args, rng, out):
    import invsplice
    c = ar.circuit(args.inp)
    designs = sorted((OPS_DIR / 'inv_designs').glob('*.txt'))
    rng.shuffle(designs)
    t0 = time.time(); cands = {}; tried = []
    for d in designs:
        if time.time() - t0 > args.seconds: break
        try:
            nc = invsplice.splice(c, invsplice.parse_inv(d.read_text()))
        except Exception as e:
            tried.append((d.name, 'error: %s' % str(e)[:80])); continue
        if not _ok(nc): tried.append((d.name, 'wrong function')); continue
        tried.append((d.name, metrics(nc))); cands[core.to_kernel(nc)] = nc
    # optional on-the-fly synthesis of new blocks (different extras / seeds)
    while time.time() - t0 < args.seconds and getattr(args, 'synth', True):
        import invsyn as IS, io, contextlib
        ex = rng.choice([['0^2', '1^3'], ['2^3'], ['1^3', '2^3'], ['0^2', '2^3'], ['0^1', '2^3'], ['2^3', '0^1^2^3']])
        base = list(IS.X)
        for e in ex:
            v = 0
            for k in e.split('^'): v ^= IS.X[int(k)]
            base.append(v)
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                syn = IS.Syn(IS.targets(3, 4), 2, base, random.Random(rng.randrange(10 ** 9)))
                best = syn.anneal(30000)
        except Exception:
            continue
        if best[2]: continue
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf): IS.show(best, base)
        txt = buf.getvalue()
        y0, y1, y2, y3 = IS.Y; have = set(best[3])
        nm = {f: 'g%04x' % f for f in have}
        for (u, v) in ((y0, y1), (y2, y3), (y0 ^ y2, y1 ^ y3)):
            if (u ^ v) not in have: txt += '  XOR   g%04x = %s %s\n' % (u ^ v, nm[u], nm[v])
        try:
            nc = invsplice.splice(c, invsplice.parse_inv(txt))
        except Exception:
            continue
        if _ok(nc):
            cands[core.to_kernel(nc)] = nc; tried.append(('synth %s' % ex, metrics(nc)))
    cl = sorted(cands.values(), key=lambda x: (metrics(x)[3], metrics(x)[2]))
    return cl[:args.max_cands], {'tried': tried[:60]}


def op_gen_bottom(ar, args, rng, out):
    import botsplice
    base = ar.circuit(args.inp)
    donors = [args.in2] if args.in2 else [i for i, r in ar.rec.items() if r['AD'] == 4 and i != args.inp]
    rng.shuffle(donors)
    t0 = time.time(); cands = {}; tried = []
    for did in donors:
        if time.time() - t0 > args.seconds: break
        try:
            nc = botsplice.build(base, ar.circuit(did))
        except Exception as e:
            tried.append((did, 'error %s' % str(e)[:60])); continue
        if not _ok(nc): continue
        m = metrics(nc); tried.append((did, m))
        if ar.would_place(m): cands[core.to_kernel(nc)] = nc
    cl = sorted(cands.values(), key=lambda x: (metrics(x)[3], metrics(x)[2]))
    return cl[:args.max_cands], {'tried': tried[:60]}


HO.OPS.update({'osc': op_osc, 'gen_inv3': op_gen_inv3, 'gen_bottom': op_gen_bottom})


def run(name):
    sys.exit(HO.main(name))
