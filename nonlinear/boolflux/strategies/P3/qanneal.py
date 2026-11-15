#!/usr/bin/env python3
"""Annealing over quadratic bottom decompositions (qflip moves) with the built circuit as the cost.

State: a decomposition of rank <= R (free terms), fixed terms = FRONT's level-1 ANDs.  Every --every
steps at rank <= R the decomposition is built on FRONT (build.py, --nb seeds) and scored
    cost = G + pen * max(0, GD - cap)     (A <= 32 holds since rank <= 17 and the front has 15 ANDs)
Metropolis on cost at temperature T (T = 0: only non-worse; T = inf: random walk).  Every built circuit
with cost <= --keep is written to OUT/cands/ (verified on all 256 inputs by build) with its decomposition.

    qanneal.py REF FRONT START --steps N --seed S --out DIR [--rank 17] [--cap 19] [--T 1.0] [--every 5]
"""
import json, math, random, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import bottom as BT, flip as FL, qflip as QF, build as BD  # noqa
from boolflux import core  # noqa


def arg(a, k, d, f=str):
    return f(a[a.index(k) + 1]) if k in a else d


def main():
    a = sys.argv[1:]
    ref, front, start = a[0], a[1], a[2]
    steps = arg(a, '--steps', 10000, int); seed = arg(a, '--seed', 1, int)
    out = Path(arg(a, '--out', 'qa')); (out / 'cands').mkdir(parents=True, exist_ok=True)
    R = arg(a, '--rank', 17, int); cap = arg(a, '--cap', 19, int); T = arg(a, '--T', 1.0, float)
    every = arg(a, '--every', 5, int); nb = arg(a, '--nb', 2, int); pen = arg(a, '--pen', 3.0, float)
    keep = arg(a, '--keep', 118, int); maxrank = arg(a, '--maxrank', R + 1, int)
    plus_p = arg(a, '--plus', 0.01, float); seconds = arg(a, '--seconds', 1e9, float)
    rc, Yt = FL.ref_basis(ref)
    fc = BT.load(front); sc = BT.load(start)
    free, fixed, lin = QF.decompose(sc, Yt)
    if front != start:
        # fixed terms must be FRONT's level-1 ANDs: only allowed when START has no fixed w
        ffree, ffixed, flin = QF.decompose(fc, Yt)
        assert all(w == 0 for _, _, w in fixed), 'START uses its own level-1 ANDs'
        fixed = [(L, R_, 0) for L, R_, _ in ffixed]
    goal = QF.total(free, fixed, lin)
    st = QF.State(free, fixed, lin); st.reduce()
    rng = random.Random(seed)
    log = open(out / ('anneal-s%d.jsonl' % seed), 'a')

    def evaluate(s):
        best = None
        for k in range(nb):
            c = BD.build(fc, Yt, s.free, s.fixed, s.lin, random.Random(rng.randrange(1 << 30)))
            m = c.metrics(BD.MODEL)
            cost = m['G'] + pen * max(0, m['GD'] - cap)
            if best is None or cost < best[0]: best = (cost, m, c)
        return best

    cur = evaluate(st) if st.rank() <= R else (1e9, None, None)
    print('start rank', st.rank(), 'cost', cur[0], cur[1] and (cur[1]['G'], cur[1]['GD']), flush=True)
    bestc = cur[0]; t0 = time.time(); seen = set()
    snap = (list(st.free), list(st.fixed), list(st.lin))
    nev = 0
    for it in range(steps):
        if time.time() - t0 > seconds: break
        prev = (list(st.free), list(st.fixed), list(st.lin))
        QF.step(st, rng, maxrank, plus_p); st.reduce()
        if st.rank() == 0 or st.rank() > maxrank:
            st.free, st.fixed, st.lin = prev; continue
        if st.rank() > R or it % every: continue
        ev = evaluate(st); nev += 1
        cost, m, c = ev
        dec = (list(st.free), list(st.fixed), list(st.lin))
        acc = cost <= cur[0] or (T > 0 and rng.random() < math.exp(-(cost - cur[0]) / T))
        if acc:
            cur = ev; snap = (list(st.free), list(st.fixed), list(st.lin))
        else:
            st.free, st.fixed, st.lin = [list(x) for x in snap]
        if cost < bestc:
            bestc = cost
            print('it %d ev %d cost %.1f G %d GD %d rank %d (%.0fs)' % (it, nev, cost, m['G'], m['GD'], st.rank() if acc else -1, time.time() - t0), flush=True)
        if m['G'] <= keep and m['GD'] <= cap + 2:
            key = core.to_kernel(c)
            if key not in seen:
                seen.add(key)
                assert c.value_table() == BD.AES
                assert QF.total(*dec) == goal
                name = 'g%d-gd%d-%d' % (m['G'], m['GD'], len(seen))
                (out / 'cands' / (name + '.circ.txt')).write_text(core.write_ncff(c, BD.MODEL))
                log.write(json.dumps({'it': it, 'name': name, 'G': m['G'], 'GD': m['GD'], 'A': m['A'], 'AD': m['AD'],
                                      'free': dec[0], 'fixed': dec[1], 'lin': dec[2]}) + '\n'); log.flush()
        if nev % 500 == 0 and acc:
            assert QF.total(st.free, st.fixed, st.lin) == goal
    print('end it %d evals %d best %.1f' % (it, nev, bestc), flush=True)


if __name__ == '__main__':
    main()
