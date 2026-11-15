#!/usr/bin/env python3
"""P6 / T07: gate price of level-3 class re-basings (non-aligned bases included) on a low-G AD3 circuit.

    python3 t07rb.py FILE --cap 31 --n 200 --out DIR [--seed S]

Random class-basis triples (identity first = control), hybrid build (lower ANDs reused, level 3 and
outputs rebuilt with the shared Paar layer), verified; prints the G distribution and writes the
lowest-G builds to DIR.
"""
import sys, random, argparse, json, itertools
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core                                   # noqa: E402
from boolflux.hub.common import verify, metrics              # noqa: E402
import botbasis as BB                                        # noqa: E402
from hybrid import hybrid                                    # noqa: E402


def bases(d=4):
    vecs = list(range(1, 1 << d))
    return [B for B in itertools.combinations(vecs, d) if BB.gf2_rank(B) == d]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('file'); ap.add_argument('--cap', type=int, default=31)
    ap.add_argument('--n', type=int, default=100); ap.add_argument('--out', required=True); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--keep', type=int, default=6)
    a = ap.parse_args()
    c = BB.load(a.file); res = BB.analyse(a.file, a.cap, verbose=False)
    allb = bases(); rng = random.Random(a.seed)
    ident = (1, 2, 4, 8)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    rows = []
    for it in range(a.n):
        if it == 0: tri = (ident, ident, ident)
        elif it <= 3 * 30:
            # one class changed
            tri = [ident, ident, ident]; tri[(it - 1) % 3] = rng.choice(allb); tri = tuple(tri)
        else:
            tri = tuple(rng.choice(allb) for _ in range(3))
        nc, st = hybrid(c, res, tri, a.cap, None, True)
        ok, _ = verify(nc); m = metrics(nc)
        rows.append((m[2], m[3], ok, tri))
    rows.sort()
    for r in rows[:a.keep]:
        print(r)
    print('control (identity):', [r for r in rows if r[3] == ((1, 2, 4, 8),) * 3])
    gs = [r[0] for r in rows]
    print('G min %d median %d max %d' % (min(gs), sorted(gs)[len(gs) // 2], max(gs)))
    json.dump(rows, open(out / ('t07rb-s%d.json' % a.seed), 'w'))
    for r in rows[:a.keep]:
        nc, st = hybrid(c, res, r[3], a.cap, None, True)
        m = metrics(nc)
        (out / ('rb-g%d-gd%d-%s.bfx' % (m[2], m[3], '-'.join(''.join('%x' % v for v in b) for b in r[3])))).write_text(core.to_kernel(nc))


if __name__ == '__main__':
    main()
