"""Exact large-neighbourhood test of last layers by SAT (track G): "can these r members of a
published last layer be replaced by r' new products (any l*m, l, m in O = span(x, N, N^-1))?"

For a layer S (from a published A28 file), a set D of dropped members and a set F of freed members,
the kept members S - D - F are folded into the free space E' = E + span(kept); then track C's exact
one-layer SAT model (qmc.encode, read-only import) asks for |F| products over O covering T mod E'.
|D| = 1, |F| = 3 with E = the file's own prefix: a hit is a 12-member layer = 27 ANDs.

usage:
  python3 lns_sat.py --l1 FILE --inv FILE --layer FILE --drop-max 1 --free 3 [--limit SECS]
        [--only-drop J] [--start N] [--stride S] [--log OUT.jsonl]
Enumerates every (D, F) with |D| = drop count (0 or 1) and |F| = free; one JSON line per case.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent / 'C'))
import gf                                            # noqa: E402
import qmc                                           # noqa: E402  (track C, read-only)
from aes_prob import load_circuit, sbox_tables, n_coords  # noqa: E402
from ll_prob import ninv_coords, prefix_pairs        # noqa: E402

ONES = (1 << 256) - 1


def layer_products(path):
    _, lev, ands = load_circuit(path)
    top = max(lev)
    return [(A['Ltab'], A['Rtab']) for A in ands if A['level'] == top]


def run_case(O, E, T, kept, nfree, limit):
    from pysat.solvers import Solver
    E2 = list(E) + [a & b for a, b in kept]
    f, LMC, meta = qmc.encode(O, E2, T, nfree)
    t0 = time.time()
    with Solver(name='cadical153', bootstrap_with=f.cl) as s:
        timer = threading.Timer(limit, s.interrupt) if limit else None
        if timer: timer.start()
        ok = s.solve_limited(expect_interrupt=True)
        if timer: timer.cancel()
        model = s.get_model() if ok else None
    dt = time.time() - t0
    res = {'sat': ok, 'secs': round(dt, 2), 'q': meta['q'], 'vars': meta['vars']}
    if ok:
        prods, cmat = qmc.decode(model, LMC, O)
        res['check'] = qmc.check(prods, cmat, O, E2, T)
        res['prods'] = [[''.join(map(str, lv)), ''.join(map(str, mv))] for lv, mv in prods]
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--l1', required=True); ap.add_argument('--inv', required=True)
    ap.add_argument('--layer', required=True)
    ap.add_argument('--drop', type=int, default=1); ap.add_argument('--free', type=int, default=3)
    ap.add_argument('--limit', type=float, default=600)
    ap.add_argument('--only-drop', type=int, default=None)
    ap.add_argument('--start', type=int, default=0); ap.add_argument('--stride', type=int, default=1)
    ap.add_argument('--log', default=None)
    ap.add_argument('--subsets', default=None, help='subsets.py JSON: run its keep-sets of --size')
    ap.add_argument('--size', type=int, default=None)
    a = ap.parse_args()
    pairs = prefix_pairs(a.l1, a.inv)
    E = [ONES] + list(gf.X) + [x & y for x, y in pairs]
    O = list(gf.X) + n_coords() + ninv_coords()
    T = sbox_tables()
    S = layer_products(a.layer)
    idx = list(range(len(S)))
    cases = []
    if a.subsets:
        sub = json.loads(Path(a.subsets).read_text())
        K = sub['K']
        for t in sub['top']:
            if t['size'] != a.size: continue
            keep = [i - 1 for i in t['keep']]
            cases.append((tuple(i for i in idx if i not in keep), ()))
        a.free = K - a.size
    for D in (itertools.combinations(idx, a.drop) if not a.subsets else []):
        if a.only_drop is not None and D != (a.only_drop - 1,): continue
        rest = [i for i in idx if i not in D]
        for F in itertools.combinations(rest, a.free):
            cases.append((D, F))
    log = open(a.log, 'a') if a.log else None
    for ci in range(a.start, len(cases), a.stride):
        D, F = cases[ci]
        kept = [S[i] for i in idx if i not in D and i not in F]
        res = run_case(O, E, T, kept, a.free, a.limit)
        rec = {'case': ci, 'of': len(cases), 'drop': [d + 1 for d in D], 'free': [x + 1 for x in F],
               'K': len(kept) + a.free, 'l1': Path(a.l1).name, 'inv': Path(a.inv).name,
               'layer': Path(a.layer).name, **res, 'utc': time.strftime('%H:%M:%S', time.gmtime())}
        print(json.dumps(rec), flush=True)
        if log: log.write(json.dumps(rec) + '\n'); log.flush()


if __name__ == '__main__':
    main()
