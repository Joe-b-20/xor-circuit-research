#!/usr/bin/env python3
"""Batch of depth-3 GF(2^4) inversion syntheses over extra-input sets and seeds (track F).

    python3 invbatch.py OUTDIR --sizes 1,2,3 --seeds 1-5 --iters 300000 [--sums4]

Extra level-0 inputs are chosen from the XOR combinations of inversion inputs that the 116
circuit can provide at level 6 (extradepth.py: all except x1^x2, x0^x1^x2, x0^x1^x3, x1^x2^x3).
Total = gates + (pair-sum XORs unless --sums4 synthesises them) + number of extras used.
Writes OUTDIR/inv-<extras>-s<seed>.txt (the gate list, invsplice format) and results.jsonl.
"""
import argparse
import itertools
import json
import random
import sys
import io
import contextlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import invsyn as IS   # noqa: E402

FEAS = ['0^1', '0^2', '0^3', '1^3', '2^3', '0^2^3', '0^1^2^3']


def val(e):
    v = 0
    for k in e.split('^'): v ^= IS.X[int(k)]
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--sizes', default='1,2,3'); ap.add_argument('--seeds', default='1-5')
    ap.add_argument('--iters', type=int, default=300000); ap.add_argument('--sums4', action='store_true')
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    lo, hi = map(int, a.seeds.split('-'))
    tg = IS.targets(3, 4, a.sums4)
    maxd = max(d for f, d in tg) - 1
    res = open(out / 'results.jsonl', 'a')
    best_tot = None
    for k in map(int, a.sizes.split(',')):
        for ex in ([tuple(a.only.split(","))] if a.only else itertools.combinations(FEAS, k)):
            base = list(IS.X) + [val(e) for e in ex]
            for seed in range(lo, hi + 1):
                syn = IS.Syn(tg, maxd, base, random.Random(seed))
                try:
                    best = syn.anneal(a.iters)
                except ValueError:
                    break          # a target is unreachable with these extras
                s, cost, viol, ch = best
                if viol: continue
                have = set(ch)
                y0, y1, y2, y3 = IS.Y
                sums = 0 if a.sums4 else len([x for x in (y0 ^ y1, y2 ^ y3, y0 ^ y1 ^ y2 ^ y3) if x not in have])
                used = sorted({e for e in ex if any(val(e) in (op[1], op[2]) for op in ch.values())})
                tot = cost + sums + len(used)
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf): IS.show(best, base)
                txt = buf.getvalue()
                if not a.sums4:
                    # append the pair-sum XORs in invsplice format
                    nm = {}
                    for ln in txt.splitlines():
                        p = ln.split(); nm[int(p[1][1:], 16) if p[1][0] == 'g' else None] = p[1]
                    def name(f):
                        return nm.get(f)
                    for (u, v) in ((y0, y1), (y2, y3), (y0 ^ y2, y1 ^ y3)):
                        if (u ^ v) not in have:
                            txt += '  XOR   g%04x = %s %s\n' % (u ^ v, name(u), name(v))
                fn = out / ('inv-%s-s%d.txt' % ('_'.join(ex).replace('^', 'x'), seed))
                fn.write_text(txt)
                rec = {'extras': list(ex), 'used': used, 'seed': seed, 'gates': cost, 'sums': sums, 'total': tot,
                       'ands': sum(1 for op in ch.values() if op[0] == 8), 'file': str(fn)}
                res.write(json.dumps(rec) + '\n'); res.flush()
                if best_tot is None or tot < best_tot:
                    best_tot = tot
                    print('best so far: total %d (%d gates + %d sums + %d extras %s) seed %d' % (tot, cost, sums, len(used), used, seed), flush=True)


if __name__ == '__main__':
    main()
