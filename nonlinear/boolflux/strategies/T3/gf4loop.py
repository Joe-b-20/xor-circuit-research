#!/usr/bin/env python3
"""T3: memetic loop with the GF(4)-coordinate move (gf4build) and the gate kernel, shared pool directory.

Each step picks a pool circuit (half the time among the lowest G, else uniform over the pool) and either
  move   : rebuild level 3 with another GF(4)-point quadruple (choice list from a gf4search/gf4rep JSON,
           or a random admissible quadruple), region 2 kept (keep2) or rebuilt (fresh), then kernel
           polish --move-seconds under caps (A, AD, --move-gd);
  polish : kernel polish --polish-seconds under caps (A, AD, --gd).
Every verified result with GD <= --pool-gd enters POOL/ if it is among the best --keep G at its GD.
Results meeting the target go to OUT/found/ with a JSON sidecar.
    gf4loop.py --pool DIR --out DIR --seeds-from F1 F2 ... --choices J.json --hours H --seed S
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core                                                    # noqa: E402
from boolflux.hub import ops as O                                            # noqa: E402
from boolflux.hub.common import load, metrics, verify, cid, code_version, _gmul   # noqa: E402
from gf4build import build                                                   # noqa: E402

MODEL = core.Model.load('nist')


def scan(pool):
    out = []
    for f in pool.glob('*.bfx'):
        try:
            p = f.stem.split('-')        # a35-ad3-g140-gd25-<id>
            out.append((int(p[2][1:]), int(p[3][2:]), p[4], f))
        except Exception:
            pass
    return out


def add_pool(pool, c, m, keep, pool_gd):
    if m[3] > pool_gd: return False
    k = cid(c)
    ent = [e for e in scan(pool) if e[1] == m[3]]
    if any(e[2] == k for e in ent): return False
    gs = sorted(e[0] for e in ent)
    if len(gs) >= keep and m[2] > gs[keep - 1]: return False
    (pool / ('a%d-ad%d-g%d-gd%d-%s.bfx' % (m + (k,)))).write_text(core.to_kernel(c))
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pool', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--seeds-from', nargs='*', default=[]); ap.add_argument('--choices')
    ap.add_argument('--hours', type=float, default=1); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--p-move', type=float, default=0.5); ap.add_argument('--p-join', type=float, default=0.0); ap.add_argument('--p-local', type=float, default=0.5); ap.add_argument('--local-top', type=int, default=6); ap.add_argument('--p-l1', type=float, default=0.0)
    ap.add_argument('--move-seconds', type=float, default=80); ap.add_argument('--polish-seconds', type=float, default=200)
    ap.add_argument('--move-gd', type=int, default=28); ap.add_argument('--gd', type=int, default=26)
    ap.add_argument('--pool-gd', type=int, default=30); ap.add_argument('--keep', type=int, default=3)
    ap.add_argument('--target', default='35,3,138,26')
    a = ap.parse_args()
    pool = Path(a.pool); pool.mkdir(parents=True, exist_ok=True)
    out = Path(a.out); (out / 'found').mkdir(parents=True, exist_ok=True)
    tA, tAD, tG, tGD = (int(x) for x in a.target.split(','))
    rng = random.Random(a.seed)
    for f in a.seeds_from:
        c = load(f); add_pool(pool, c, metrics(c), a.keep, a.pool_gd)
    choices = [r[4] for r in json.load(open(a.choices))['res']] if a.choices else []
    log = open(out / ('loop-s%d.jsonl' % a.seed), 'a'); ver = code_version()
    t_end = time.time() + 3600 * a.hours; it = 0
    while time.time() < t_end:
        it += 1
        P = scan(pool)
        if not P: break
        if rng.random() < 0.5:
            g0 = min(e[0] for e in P); cand = [e for e in P if e[0] <= g0 + 1]
        else:
            cand = P
        G0, GD0, id0, f0 = rng.choice(cand)
        c0 = load(f0)
        seed = rng.randrange(1 << 30)
        job = out / 'jobs' / ('s%d-%05d' % (a.seed, it)); job.mkdir(parents=True, exist_ok=True)
        rec = {'it': it, 'start': f0.name, 'seed': seed, 'code': ver}
        if a.p_join and rng.random() < a.p_join and len(P) > 1:
            from boolflux.hub import join as JN
            other = rng.choice([e for e in P if e[3] != f0])
            X = JN.Prepared(c0, f0.name); Y = JN.Prepared(load(other[3]), other[3].name)
            best = {}; tried = 0; t1 = time.time()
            for F, Bk in ((X, Y), (Y, X)):
                for jc, LX, LY, nint in JN.join_all(F, Bk):
                    tried += 1
                    m = metrics(jc)
                    if m[0] <= 35 and m[1] <= 3 and m[3] <= a.pool_gd:
                        key = (m[3], m[2])
                        if key not in best: best[key] = jc
            pooled = []
            for (gd, g), jc in sorted(best.items(), key=lambda x: x[0][1])[:6]:
                ok, _ = verify(jc)
                gmin = min(e[0] for e in P)
                if ok and g <= gmin + 3 and add_pool(pool, jc, metrics(jc), a.keep, a.pool_gd): pooled.append(metrics(jc))
            rec.update({'op': 'join', 'other': other[3].name, 'tried': tried, 'pooled': pooled,
                        'best': sorted(best)[:3] if best else None, 'wall': round(time.time() - t1, 1)})
            log.write(json.dumps(rec, default=str) + chr(10)); log.flush()
            continue
        nc = None
        if a.p_l1 and rng.random() < a.p_l1:
            # level-1 product exchange walk (l1move.py): 1-3 steps, each a random variant with dG <= 0
            # (else dG <= 1), then a kernel polish
            from l1move import l1_variants
            cur = c0; steps = rng.choice([1, 2, 3]); path = []
            for _ in range(steps):
                g0 = metrics(cur)[2]
                vs = l1_variants(cur)
                cand0 = [v for v in vs if v[0] <= g0] or [v for v in vs if v[0] <= g0 + 1]
                if not cand0: break
                v = rng.choice(cand0); cur = v[4]; path.append(('s%d' % v[2], v[0], v[1]))
            if cur is not c0:
                nc = cur
                rec.update({'op': 'l1', 'path': path, 'built': metrics(nc)})
                caps = {'A': 35, 'AD': 3, 'GD': a.gd if metrics(nc)[3] <= a.gd else a.move_gd}; secs = a.move_seconds
        if nc is not None:
            pass
        elif rng.random() < a.p_move:
            pts = None; kind = 'global'
            if rng.random() < a.p_local:
                from nbscan import current_points
                try:
                    from pairs import Basis as _B
                    p0 = list(current_points(c0)); i = rng.randrange(4); opts = []
                    G0b = None
                    for p in range(1, 256):
                        q = list(p0); q[i] = p
                        bb = _B([])
                        if not all(bb.add(_gmul(s_, x_)) for x_ in q for s_ in (1, 188)): continue
                        try:
                            tc = build(c0, q, keep2=True)
                        except Exception:
                            continue
                        opts.append((metrics(tc)[2], metrics(tc)[3], q))
                    opts.sort()
                    gcur = opts[0][0] if opts else 0
                    # skip the variants of the current R set (they build at the minimum, +1 over the source)
                    real = [o for o in opts if o[0] > gcur]
                    if real:
                        pick = rng.choice(real[:a.local_top]); pts = pick[2]; kind = 'local'
                except Exception:
                    pts = None
            if pts is None and choices and rng.random() < 0.8:
                pts = list(rng.choice(choices[:300]))
            if pts is None:
                # random quadruple; admissibility checked by build (assert) -> retry a few times
                pts = [rng.randrange(1, 256) for _ in range(4)]
            # random representative scalings of the points (same R functions, other Q pairing)
            rho = 188 if rng.random() < 0.5 else 189
            if kind == "global": pts = [pts[0]] + [p if rng.random() < 0.34 else _gmul(rho, p) for p in pts[1:]]
            mode = 'keep2' if (kind == 'local' or rng.random() < 0.7) else 'fresh'
            try:
                nc = build(c0, pts, keep2=(mode == 'keep2'))
            except Exception as e:
                rec.update({'op': 'move', 'points': pts, 'error': str(e)[:80]}); log.write(json.dumps(rec) + '\n'); log.flush()
                continue
            rec.update({'op': 'move', 'kind': kind, 'points': pts, 'mode': mode, 'built': metrics(nc)})
            caps = {'A': 35, 'AD': 3, 'GD': max(a.move_gd, metrics(nc)[3]) if False else a.move_gd}
            secs = a.move_seconds
        else:
            nc = c0; rec['op'] = 'polish'
            caps = {'A': 35, 'AD': 3, 'GD': a.gd}; secs = a.polish_seconds
        cands, info = O._kernel(nc, caps, 'cost,gd', seed, secs, job, out)
        rec['caps'] = caps
        if cands:
            r = cands[0]; m = metrics(r); ok, vi = verify(r); rec.update({'m': m, 'ok': ok})
            if ok and m[0] <= 35 and m[1] <= 3:
                rec['pooled'] = add_pool(pool, r, m, a.keep, a.pool_gd)
                if m[0] <= tA and m[1] <= tAD and m[2] <= tG and m[3] <= tGD:
                    k = cid(r); name = 'aes-sbox-a%d-ad%d-g%d-gd%d-%s' % (m + (k,))
                    (out / 'found' / (name + '.circ.txt')).write_text(core.write_ncff(r, MODEL))
                    try:
                        sys.path.insert(0, str(HERE.parents[1] / 'campaigns'))
                        import aes_check
                        ac = aes_check.check(str(out / 'found' / (name + '.circ.txt')))
                    except Exception as e:
                        ac = {'error': str(e)}
                    (out / 'found' / (name + '.json')).write_text(json.dumps({
                        'metrics': m, 'made_by': 'strategies/T3/gf4loop.py (GF(4)-coordinate move + gate kernel)',
                        'record': rec, 'start_file': str(f0), 'aes_check': ac,
                        'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=1, default=str))
                    rec['found'] = name
        try:
            (job / 'kernel.log').write_text('\n'.join((job / 'kernel.log').read_text().splitlines()[-10:]))
        except Exception:
            pass
        log.write(json.dumps(rec, default=str) + '\n'); log.flush()


if __name__ == '__main__':
    main()
