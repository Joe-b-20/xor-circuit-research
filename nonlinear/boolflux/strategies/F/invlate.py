#!/usr/bin/env python3
"""Inversion block with per-output depths (track F): the 'early' y-combos at depth 3 (from
the inversion inputs), the others at depth 4 as one XOR/XNOR of depth-3 signals (or present).

    python3 invlate.py OUTDIR --early y0,y1,y2,y3,y0^y1,y2^y3,y0123 --extras 0^2,1^3 --seeds 1-4 --iters 200000

Writes OUTDIR/<tag>-s<seed>.txt (invsplice format) and appends OUTDIR/results.jsonl.
fastset.py lists the early sets for which 116's bottom meets cap 14.
"""
import argparse
import contextlib
import io
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import invsyn as IS   # noqa: E402

y0, y1, y2, y3 = IS.Y
COMBO = {'y0': y0, 'y1': y1, 'y2': y2, 'y3': y3, 'y0^y2': y0 ^ y2, 'y1^y3': y1 ^ y3,
         'y0^y1': y0 ^ y1, 'y2^y3': y2 ^ y3, 'y0123': y0 ^ y1 ^ y2 ^ y3}


def val(e):
    v = 0
    for k in e.split('^'): v ^= IS.X[int(k)]
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--early', required=True); ap.add_argument('--extras', default='0^2,1^3')
    ap.add_argument('--seeds', default='1-4'); ap.add_argument('--iters', type=int, default=200000)
    ap.add_argument("--force3", default="")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    early = a.early.split(','); late = [k for k in COMBO if k not in early]
    ex = [e for e in a.extras.split(',') if e]
    base = list(IS.X) + [val(e) for e in ex]
    FAST = {'y0', 'y1', 'y2', 'y3', 'y0^y2', 'y1^y3'}
    dep = {k: (3 if k in early else 4) if k in FAST else (4 if k in early else 5) for k in COMBO}
    tg = [(COMBO[k], 3) for k in COMBO if dep[k] == 3]
    for h in [x for x in a.force3.split(",") if x]:
        v = 0
        for part in h.split("^"): v ^= IS.Y[int(part[1:])]
        if all(v != t for t, d in tg): tg.append((v, 3))
    lo, hi = map(int, a.seeds.split('-'))
    tag = ("E-" + "_".join(early) + "-X-" + "_".join(ex) + "-F-" + a.force3.replace(",", "_")).replace("^", "x")
    for seed in range(lo, hi + 1):
        syn = IS.Syn(tg, 2, base, random.Random(seed))
        syn.late = [(COMBO[k], dep[k]) for k in COMBO if dep[k] > 3]
        try:
            best = syn.anneal(a.iters)
        except ValueError as e:
            print('unreachable:', e); return
        s, cost, viol, ch = best
        syn._ch = ch
        extra_cost, gates = syn.complete(ch)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf): IS.show(best, base)
        txt = buf.getvalue()
        nm = {IS.X[k]: 'x%d' % k for k in range(4)}
        for v in base[4:]: nm[v] = 'e%04x' % v
        for f in ch: nm.setdefault(f, 'g%04x' % f)
        bad = False
        for op, t, a_, b_ in gates:
            if op is None: bad = True; continue
            txt += '  %-5s g%04x = %s %s\n' % ('XOR' if op == 6 else 'XNOR', t, nm[a_], nm[b_])
            nm.setdefault(t, 'g%04x' % t)
        used = sorted({e for e in ex if any(val(e) in (o[1], o[2]) for o in ch.values())})
        rec = {'early': early, 'extras': ex, 'used': used, 'seed': seed, 'gates': cost, 'core': len(ch),
               'late_xors': extra_cost, 'total_with_extras': cost + len(used), 'viol': viol, 'complete': not bad,
               'ands': sum(1 for o in ch.values() if o[0] == 8)}
        fn = out / ('%s-s%d.txt' % (tag, seed)); fn.write_text(txt); rec['file'] = str(fn)
        with open(out / 'results.jsonl', 'a') as f: f.write(json.dumps(rec) + '\n')
        print(json.dumps(rec), flush=True)


if __name__ == '__main__':
    main()
