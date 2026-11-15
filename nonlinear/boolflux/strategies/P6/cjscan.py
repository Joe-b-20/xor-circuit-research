#!/usr/bin/env python3
"""P6: GF(2^8) conjugates (P3 conj.py, read-only import) of an AD3 circuit screened by the depth bound.

    python3 cjscan.py FILE --cap 12 --out OUT.jsonl [--emit DIR --emit-max 10]

For each of the 2040 conjugates (x -> lam x^(2^k), outputs through the matching affine map; AND
functions up to the input change unchanged, top forms f -> f o G, output rows -> Mout rows): skeleton
arrivals of the level-1/2 ANDs (prefilter: no lower AND later than in FILE), then the best level-3
class re-basing max output Kraft at the cap (botbasis).  Emits the naive conjugate circuits that meet
max Kraft <= 1 (the hybrid builder then builds them depth-feasibly).
"""
import sys, json, time, argparse
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
sys.path.append(str(HERE.parent / 'P3')); sys.path.append(str(HERE.parent / 'F'))
import conj as CJ                                   # noqa: E402  (P3, read-only)
from boolflux import core                           # noqa: E402
from boolflux.hub.common import load, metrics       # noqa: E402
import botbasis as BB                               # noqa: E402
from skelan import anatomy                          # noqa: E402


def lowmax(c):
    sk, arr, alv = anatomy(c); n = c.n
    v = [arr[1 + n + k] for k in range(len(sk['ands'])) if alv[1 + n + k] <= 2]
    return (max(v), sum(v))


SLACK = 2


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('file'); ap.add_argument('--cap', type=int, default=12)
    ap.add_argument('--out', required=True); ap.add_argument('--emit'); ap.add_argument('--emit-max', type=int, default=10)
    a = ap.parse_args()
    c = load(a.file); base = lowmax(c)
    tmp = Path(a.out).with_suffix('.tmp.bfx'); f = open(a.out, 'w'); rows = []; t0 = time.time(); npre = 0
    for lam in range(1, 256):
        for k in range(8):
            cc = CJ.conj_circuit(c, lam, k)
            lm = lowmax(cc)
            if lm[0] > base[0] or lm[1] > base[1] + SLACK: continue
            npre += 1
            tmp.write_text(core.to_kernel(cc))
            try:
                res = BB.analyse(str(tmp), a.cap, verbose=False)
            except AssertionError:
                continue
            row = {'lam': lam, 'k': k, 'lowmax': lm, 'kraft': res['best'], 'G_naive': metrics(cc)[2]}
            f.write(json.dumps(row) + '\n'); f.flush(); rows.append((res['best'], lam, k, cc))
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    print('prefilter passed %d of 2040; %.0f s; best:' % (npre, time.time() - t0), [(round(r[0], 3), r[1], r[2]) for r in rows[:12]], flush=True)
    if a.emit:
        d = Path(a.emit); d.mkdir(parents=True, exist_ok=True)
        for kr, lam, k, cc in rows[:a.emit_max]:
            if kr <= 1 + 1e-9:
                (d / ('cj-%d-%d-k%03d.bfx' % (lam, k, int(kr * 100)))).write_text(core.to_kernel(cc))


if __name__ == '__main__':
    main()
