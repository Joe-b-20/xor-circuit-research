#!/usr/bin/env python3
"""Calibration of the affine-slack window move on archive circuits.

    python3 calib.py ARCHIVE_CAMPAIGN N_CIRCUITS WINDOWS_PER_CIRCUIT SEED OUT.jsonl
Per window: k, level, mode, |C|, |O|, dimV, r (residual dim), dimP, #product candidates, whether a
spanning set was found, rebuild ok, function ok, metrics before/after (raw, no polish), time."""
import json, random, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux.hub.archive import Archive          # noqa: E402
from boolflux.hub.common import metrics, sbox     # noqa: E402
import aslack as AS                               # noqa: E402

camp, ncirc, nwin, seed, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
rng = random.Random(seed)
ar = Archive(camp)
ids = ar.front_ids(); rng.shuffle(ids)
# prefer distinct (A, AD, GD)
seen = set(); pick = []
for i in ids:
    r = ar.rec[i]; k = (r['A'], r['AD'], r['GD'])
    if k in seen: continue
    seen.add(k); pick.append(i)
pick = pick[:ncirc]
with open(out, 'w') as f:
    for cid in pick:
        c = ar.circuit(cid); m0 = metrics(c); I = AS.Info(c)
        for w in range(nwin):
            t0 = time.time()
            S = AS.choose_S(I, rng)
            if S is None: continue
            mode = rng.choice(['wide', 'local'])
            dd = rng.choice([None, None, 0, 1, 2, 3])
            W = AS.Window(I, S, mode, rng, ddepth=dd)
            row = {'dd': dd, 'id': cid, 'm0': m0, 'k': len(S), 'L': W.L, 'mode': mode, 'C': len(W.C), 'O': len(W.O),
                   'dimV': W.dimV, 'r': W.r, 'dimP': W.dimP, 'targets': len(W.targets), 'D': len(W.D)}
            ta = time.time()
            prods = W.products(rng)
            row['nprods'] = len(prods); row['t_prod'] = round(time.time() - ta, 3)
            ch = W.pick(prods, rng) if prods else None
            row['spanned'] = ch is not None
            if ch is not None:
                row['m_new'] = len(ch)
                row['same_products'] = sum(1 for p in ch if any(p[4] == I.tabs[s] for s in S))
                row['prod_cost'] = sum(p[0] for p in ch)
                rows = W.target_rows(ch, rng)
                row['rows'] = rows is not None
                if rows is not None:
                    try:
                        nc = AS.rebuild(W, ch, rows, rng)
                    except Exception as e:
                        nc = None; row['err'] = repr(e)[:80]
                    row['rebuilt'] = nc is not None
                    if nc is not None:
                        row['func_ok'] = tuple(nc.value_table()) == sbox()
                        row['m1'] = metrics(nc)
            row['t'] = round(time.time() - t0, 3)
            f.write(json.dumps(row) + '\n'); f.flush()
