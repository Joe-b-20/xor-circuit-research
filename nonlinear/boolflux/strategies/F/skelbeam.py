#!/usr/bin/env python3
"""Beam search over sets of AND distributions (skelxf) to lower the skeleton depth bound.
Score: (bound, total Kraft excess at cap D over all forms, ANDs added).

    python3 skelbeam.py FILE --cap D [--width 12] [--depth 8]
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2])); sys.path.insert(0, str(HERE))
from boolflux import core   # noqa: E402
from skelxf import Skel, gate_forms, splits, bits, N   # noqa: E402


def kraft_excess(sk, D):
    arr = sk.arrivals()
    tot = 0.0
    for f in sk.outs:
        k = sum(2.0 ** (arr[p] - D) for p in bits(f) if p > 0)
        tot += max(0.0, k - 1.0) + 0.01 * k
    return tot


def moves(sk, c, form):
    """Distribute moves: splits from the parent circuit forms and, for ANDs created by earlier
    moves, all 2-way splits into existing parent forms."""
    out = []
    pf = set(form)
    for k, a in enumerate(sk.ands):
        if a is None: continue
        L, R = a
        sl = [(L,)] + splits(c, form, L); sr = [(R,)] + splits(c, form, R)
        for Ls in sl:
            for Rs in sr:
                if len(Ls) == 1 and len(Rs) == 1: continue
                out.append((k, Ls, Rs))
    return out


def main():
    f = sys.argv[1]; D = int(sys.argv[sys.argv.index('--cap') + 1])
    W = int(sys.argv[sys.argv.index('--width') + 1]) if '--width' in sys.argv else 12
    depth = int(sys.argv[sys.argv.index('--depth') + 1]) if '--depth' in sys.argv else 8
    c = core.read_ncff(f); form = gate_forms(c)
    sk0 = Skel.from_circuit(c)
    b0 = sk0.bound()[0]
    beam = [(b0, kraft_excess(sk0, D), 0, sk0, [])]
    seen = set()
    for step in range(depth):
        cand = []
        for b, ke, added, sk, hist in beam:
            for k, Ls, Rs in moves(sk, c, form):
                s2 = sk.copy()
                try:
                    ad = s2.distribute(k, list(Ls), list(Rs))
                    bb, ol, _ = s2.bound()
                except ValueError:
                    continue
                key = (tuple(sorted(x for x in s2.ands if x is not None)), tuple(s2.outs))
                if key in seen: continue
                seen.add(key)
                cand.append((bb, kraft_excess(s2, D), added + ad, s2, hist + [(k + 1, len(Ls), len(Rs))]))
        cand.sort(key=lambda t: (t[0], t[1] + 0.05 * t[2]))
        beam = cand[:W]
        if not beam: break
        b, ke, added, sk, hist = beam[0]
        print('step %d: best bound %d kraft-excess %.3f +%d AND  %s' % (step + 1, b, ke, added, hist), flush=True)
        if b <= D:
            print('reached cap', D); break


if __name__ == '__main__':
    main()
