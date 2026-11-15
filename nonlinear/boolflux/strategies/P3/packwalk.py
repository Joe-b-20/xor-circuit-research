#!/usr/bin/env python3
"""Flip-graph walk over bilinear rank-18 decompositions of the bottom tensor, looking for 'packable'
pairs: two terms (s, A', w), (t, B', w) with the same w, s != t, and {A', B'} inside the operand plane of
one of FRONT's level-1 ANDs.  Each packable pair gives a 17-AND bottom (pack.py mechanism: one AND
(A'+t)(B'+s), the level-1 AND XORed into w, Y*Y cancelled by Y-forms added to other terms' X-operands).
Every such bottom is built on FRONT (build.py), checked on 256 inputs, logged, and the best are saved.

    packwalk.py REF FRONT --steps N --seed S --out DIR [--kmax 3] [--nb 2] [--plus 0.002] [--save-g 120]
"""
import json, random, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import bottom as BT, flip as FL, qflip as QF, build as BD, pack as PK  # noqa
from boolflux import core  # noqa


def arg(a, k, d, f=str):
    return f(a[a.index(k) + 1]) if k in a else d


def try_pack(D, i, j, fk, fixed0, lin0, goal, kmax):
    (u1, vA, w), (u2, vB, _) = D[i], D[j]
    rest = [t for k, t in enumerate(D) if k not in (i, j)]
    free = [(PK.Y(u), PK.X(v), ww) for (u, v, ww) in rest]
    P = (PK.X(vA) | PK.Y(u2), PK.X(vB) | PK.Y(u1), w)
    cp, dp = PK.cross(u2, u1)
    target = [cp if w >> o & 1 else 0 for o in range(8)]
    sol = PK.solve_cancel(target, [(u, ww) for (u, v, ww) in rest], kmax)
    if sol is None: return None
    for k, nu in sol:
        L, R, ww = free[k]; free[k] = (L, R ^ PK.Y(nu), ww)
    free.append(P)
    fixed = [tuple(t) for t in fixed0]; lin = list(lin0)
    cur = QF.total(free, fixed, [0] * 8)
    qf, lf = QF.prodfun(*fixed0[fk][:2])
    for o in range(8):
        rows_g, lg = goal[o]; rows_c, lc = cur[o]
        diffq = [x ^ y for x, y in zip(rows_g, rows_c)]
        if any(diffq):
            if list(qf) != diffq: return None
            L_, R_, w_ = fixed[fk]; fixed[fk] = (L_, R_, w_ ^ (1 << o)); lc ^= lf
        lin[o] = lg ^ lc
    assert QF.total(free, fixed, lin) == goal
    return free, fixed, lin, len(sol)


def main():
    a = sys.argv[1:]
    ref, front = a[0], a[1]
    steps = arg(a, '--steps', 100000, int); seed = arg(a, '--seed', 1, int)
    out = Path(arg(a, '--out', 'packwalk')); out.mkdir(parents=True, exist_ok=True)
    kmax = arg(a, '--kmax', 3, int); nb = arg(a, '--nb', 2, int); plus_p = arg(a, '--plus', 0.002, float)
    saveg = arg(a, '--save-g', 120, int); maxrank = arg(a, '--maxrank', 19, int)
    rc, Yt = FL.ref_basis(ref)
    fc = BT.load(front)
    D, ten, const = FL.extract(fc, Yt)
    free0, fixed0, lin0 = QF.decompose(fc, Yt)
    goal = QF.total(free0, fixed0, lin0)
    planes = []
    for k, (L, R, w) in enumerate(fixed0):
        if (L >> 9) or (R >> 9): continue
        A_, B_ = (L >> 1) & 0xFF, (R >> 1) & 0xFF
        planes.append((k, {A_, B_, A_ ^ B_}))
    rng = random.Random(seed)
    log = open(out / ('packwalk-s%d.jsonl' % seed), 'a')
    terms = FL.reduce_terms(list(D)); seen = set(); tried = 0; best = None; t0 = time.time()
    for st in range(steps):
        F = FL.flips(terms)
        if (rng.random() < plus_p and len(terms) < maxrank) or not F:
            terms = FL.reduce_terms(FL.plus(terms, rng))
        else:
            i, j, ax = rng.choice(F)
            terms = FL.reduce_terms(FL.do_flip(terms, i, j, ax))
        if len(terms) != 18: continue
        byw = {}
        for idx, t in enumerate(terms): byw.setdefault(t[2], []).append(idx)
        for w, ix in byw.items():
            if len(ix) < 2: continue
            for i in ix:
                for j in ix:
                    if i == j or terms[i][0] == terms[j][0] or terms[i][1] == terms[j][1]: continue
                    for fk, pi in planes:
                        if terms[i][1] in pi and terms[j][1] in pi:
                            key = (FL.canon(terms), i, j, fk)
                            sig = (tuple(sorted([terms[i], terms[j]])), fk, FL.canon(terms))
                            if sig in seen: continue
                            seen.add(sig); tried += 1
                            r = try_pack(terms, i, j, fk, fixed0, lin0, goal, kmax)
                            if r is None:
                                log.write(json.dumps({'st': st, 'pack': None}) + '\n'); continue
                            free, fixed, lin, K = r
                            bc = None
                            for s in range(nb):
                                c = BD.build(fc, Yt, free, fixed, lin, random.Random(s))
                                m = c.metrics(BD.MODEL)
                                if bc is None or (m['G'], m['GD']) < bc[0]: bc = ((m['G'], m['GD']), c, m)
                            (G, GD), c, m = bc
                            assert c.value_table() == BD.AES and m['A'] <= 32
                            log.write(json.dumps({'st': st, 'G': G, 'GD': GD, 'A': m['A'], 'K': K,
                                                  'free': free, 'fixed': fixed, 'lin': lin}) + '\n'); log.flush()
                            if best is None or (G, GD) < best:
                                best = (G, GD); print('st %d tried %d best G %d GD %d A %d K %d (%.0fs)' % (st, tried, G, GD, m['A'], K, time.time() - t0), flush=True)
                            if G <= saveg:
                                (out / ('pw-s%d-g%d-gd%d-%d.circ.txt' % (seed, G, GD, tried))).write_text(core.write_ncff(c, BD.MODEL))
        if st % 20000 == 0:
            print('st %d rank %d tried %d (%.0fs)' % (st, len(terms), tried, time.time() - t0), flush=True)
    print('end tried', tried, 'best', best)


if __name__ == '__main__':
    main()
