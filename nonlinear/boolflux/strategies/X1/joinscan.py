#!/usr/bin/env python3
"""X1 join scan with the rank objective.

For a circuit, A_eff = dim span{1, inputs, products} - 9 (tables on the 256 inputs).  A circuit with A
ANDs can always be rewritten with A_eff ANDs (x1patch dep: the last product of a dependency is an XOR of
the others).  The hub's join operator keeps a transplant only if (A, AD, G, GD) places; here every
transplant between distinct AND skeletons of the pool is scored by A_eff instead.

    python3 joinscan.py CAMPAIGN_DIR OUT_DIR [--amax 30] [--target 27] [--seconds S] [--extra FILES...]
Pool: archive members with A <= amax, one per skeleton (set of product tables).  Output: OUT_DIR/scan.jsonl
(one line per ordered pair: best A_eff over the cuts), OUT_DIR/hist.json, and every reduced circuit with
A_eff <= target as OUT_DIR/cand-*.bfx (checked on all 256 inputs).
"""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import x1lib as X, x1patch as XP
from boolflux.hub.common import metrics, sbox, load
from boolflux.hub.archive import Archive
from boolflux.hub import join as J
from boolflux import core

ONES = (1 << 256) - 1


def prod_tables(c):
    t = c.tables(); n = c.n
    return [t[n + j] for j, g in enumerate(c.gates) if g[0] == 8]


def a_eff(c):
    t = c.tables(); n = c.n
    piv = []; r = 0
    for v in [ONES] + t[:n] + [t[n + j] for j, g in enumerate(c.gates) if g[0] == 8]:
        for p, pv in piv:
            if (v >> p) & 1: v ^= pv
        if v: piv.append((v.bit_length() - 1, v)); r += 1
    return r - 9


def reduce_full(c):
    """apply dep reductions until none is left; returns the circuit with the best (A, AD, GD, G)"""
    cur = c
    while True:
        cs = [nc for nc, d in XP.dep_candidates(XP.Info(cur)) if tuple(nc.value_table()) == sbox()]
        if not cs: return cur
        cur = min(cs, key=lambda x: (metrics(x)[0], metrics(x)[1], metrics(x)[3], metrics(x)[2]))


def main():
    args = sys.argv[1:]
    camp = args[0]; out = Path(args[1]); out.mkdir(parents=True, exist_ok=True)
    def opt(name, d):
        return type(d)(args[args.index(name) + 1]) if name in args else d
    amax = opt('--amax', 30); target = opt('--target', 27); seconds = opt('--seconds', 3000.0)
    extra = args[args.index('--extra') + 1:] if '--extra' in args else []
    ar = Archive(camp)
    pool = {}
    items = [(i, ar.circuit(i)) for i, r in ar.rec.items() if r['A'] <= amax]
    items += [(Path(f).name, load(f)) for f in extra]
    for i, c in items:
        if tuple(c.value_table()) != sbox(): continue
        key = frozenset(prod_tables(c))
        m = metrics(c)
        if key not in pool or m < pool[key][2]: pool[key] = (i, c, m)
    P = [J.Prepared(c, i) for i, c, m in sorted(pool.values(), key=lambda x: x[2])]
    print('pool: %d circuits, %d skeletons' % (len(items), len(P)), flush=True)
    t0 = time.time(); hist = {}; nj = 0; best = 99; found = 0; seen_red = set()
    lf = open(out / 'scan.jsonl', 'a')
    done = False
    for xi, F in enumerate(P):
        for yi, B in enumerate(P):
            if xi == yi: continue
            if time.time() - t0 > seconds: done = True; break
            pb = None
            for c, LX, LY, nint in J.join_all(F, B):
                nj += 1
                A = sum(1 for g in c.gates if g[0] == 8); ae = a_eff(c)
                hist[(A, ae)] = hist.get((A, ae), 0) + 1
                if pb is None or ae < pb[0]: pb = (ae, A, LX, LY)
                if ae <= target:
                    key = frozenset(prod_tables(c))
                    if key in seen_red: continue
                    seen_red.add(key)
                    rc = reduce_full(c)
                    if tuple(rc.value_table()) != sbox(): continue
                    m = metrics(rc); found += 1
                    name = 'cand-a%d-ad%d-g%d-gd%d-%04d' % (m[0], m[1], m[2], m[3], found)
                    (out / (name + '.bfx')).write_text(core.to_kernel(rc))
                    (out / (name + '.json')).write_text(json.dumps({'front': F.id, 'back': B.id, 'LX': LX, 'LY': LY,
                        'join_A': A, 'A_eff': ae, 'metrics': m, 'method': 'joinscan: hub join + x1patch dep reductions',
                        'time': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}))
                    print('FOUND', name, 'front', F.id, 'back', B.id, LX, LY, flush=True)
            if pb is not None:
                lf.write(json.dumps({'front': F.id, 'back': B.id, 'best': pb}) + '\n')
                if pb[0] < best: best = pb[0]; print('best A_eff %d (A %d) front %s back %s cut %d/%d  t %.0f' % (pb[0], pb[1], F.id, B.id, pb[2], pb[3], time.time() - t0), flush=True)
        if done: break
        if xi % 10 == 0: print('front %d/%d joins %d best %d t %.0f' % (xi, len(P), nj, best, time.time() - t0), flush=True)
    lf.close()
    (out / 'hist.json').write_text(json.dumps({'complete': not done, 'skeletons': len(P), 'joins': nj, 'best_A_eff': best,
                                               'hist_A_Aeff': sorted([list(k) + [v] for k, v in hist.items()])}, indent=0))
    print('done complete=%s joins %d best A_eff %d found %d  t %.0f' % (not done, nj, best, found, time.time() - t0))


if __name__ == '__main__':
    main()
