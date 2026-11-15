#!/usr/bin/env python3
"""Robustness test: the window pipeline (no polish) on N random archive cell minima, T s each.
    python3 robust_test.py ARCHIVE N T SEED"""
import random, sys, time, traceback
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(next(q for q in HERE.parents if (q / 'boolflux' / 'core.py').exists())))
from boolflux.hub.archive import Archive          # noqa: E402
from boolflux.hub.common import metrics, sbox     # noqa: E402
import aslack as AS                               # noqa: E402

ar = Archive(sys.argv[1]); N, T, seed = int(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
rng = random.Random(seed)
ids = [v[0] for v in ar.cells.values() if v]; rng.shuffle(ids)
tot = {'win': 0, 'ok': 0, 'bad': 0, 'err': 0, 'better_or_equal_G': 0}
for i in ids[:N]:
    c = ar.circuit(i); m0 = metrics(c); I = AS.Info(c); t0 = time.time()
    while time.time() - t0 < T:
        try:
            S = AS.choose_S(I, rng)
            if S is None: break
            W = AS.Window(I, S, rng.choice(['wide', 'local']), rng, ddepth=rng.choice([None, 0, 1, 2, 3]))
            tot['win'] += 1
            pr = W.products(rng, exhaustive_dim=10)
            ch = W.pick(pr, rng) if pr else None
            if ch is None: continue
            rows = W.target_rows(ch, rng)
            nc = AS.rebuild(W, ch, rows, rng) if rows else None
            if nc is None: continue
            if tuple(nc.value_table()) == sbox():
                tot['ok'] += 1; m = metrics(nc)
                tot['better_or_equal_G'] += (m[0] <= m0[0] and m[1] <= m0[1] and m[2] <= m0[2])
            else:
                tot['bad'] += 1
        except Exception:
            tot['err'] += 1; traceback.print_exc(limit=2)
    print(i, m0, dict(tot), flush=True)
