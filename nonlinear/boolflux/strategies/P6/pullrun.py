#!/usr/bin/env python3
"""P6 depth pull for AD3 circuits: re-base level 3 + hybrid depth-feasible build at cap D + kernel polish.

    python3 pullrun.py --parents F1 [F2 ...] --cap D --out DIR [--builds 60] [--top 4] [--seconds 240]
                       [--stages 2] [--seed 1] [--hours H] [--capa 35] [--capad 3]

For each parent: hybrid builds over the feasible class-basis triples (+ random-tie variants), keep the
--top lowest-G distinct builds meeting the cap, polish each with the gate kernel (hub.ops._kernel)
under the hard caps (A <= capa, AD <= capad, GD <= D; objective cost,gd), --stages restarts from the
stage best.  Every kernel result is verified (core + independent verifier); circuits are written to
DIR/pool/ (a<A>-ad<AD>-g<G>-gd<GD>-<id>.bfx) with DIR/pull.jsonl lines (parent, triple, build G,
kernel seeds, elapsed).  Loops over parents with new seeds until --hours.
"""
import sys, json, time, random, argparse, hashlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core                                       # noqa: E402
from boolflux.hub.common import verify, metrics, clean           # noqa: E402
from boolflux.hub import ops as O                                # noqa: E402
O.KDEFAULTS['repair_keep'] = 1   # compliance 18:20: no move may raise any single cap excess (A/AD stay hard)
import botbasis as BB                                            # noqa: E402
from rebase import feasible_triples                              # noqa: E402
from hybrid import hybrid                                        # noqa: E402

BIN = Path.home() / 'xs-campaigns/2026-11-15-targets/P6/kbin'


def cid(c):
    return hashlib.sha1(core.to_kernel(c).encode()).hexdigest()[:12]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--parents', nargs='+', required=True); ap.add_argument('--cap', type=int, required=True)
    ap.add_argument('--out', required=True); ap.add_argument('--builds', type=int, default=60)
    ap.add_argument('--top', type=int, default=4); ap.add_argument('--seconds', type=float, default=240)
    ap.add_argument('--stages', type=int, default=2); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--hours', type=float, default=1.0); ap.add_argument('--capa', type=int, default=35)
    ap.add_argument('--capad', type=int, default=3); ap.add_argument('--paar', action='store_true'); ap.add_argument('--max-build', type=int, default=9999, help='skip builds above this G')
    ap.add_argument('--evolve', type=int, default=0, help='each round also use the N lowest-G pool circuits as parents')
    a = ap.parse_args()
    out = Path(a.out); (out / 'pool').mkdir(parents=True, exist_ok=True); (out / 'jobs').mkdir(exist_ok=True)
    caps = {'A': a.capa, 'AD': a.capad, 'GD': a.cap}
    t0 = time.time(); rng = random.Random(a.seed); rnd = 0
    log = open(out / 'pull.jsonl', 'a')
    while time.time() - t0 < a.hours * 3600:
        parents = list(a.parents)
        if a.evolve:
            pool = sorted((int(f.stem.split('-')[2][1:]), int(f.stem.split('-')[3][2:]), str(f)) for f in (out / 'pool').glob('a*-ad*-g*-gd*-*.bfx'))
            pool = [x for x in pool if x[1] <= a.cap]
            if rnd > 0 or pool:
                parents = [x[2] for x in pool[:a.evolve]] + (parents if rnd % 2 == 0 else [])
        for par in parents:
            if time.time() - t0 >= a.hours * 3600: break
            c = BB.load(par)
            res = BB.analyse(par, a.cap, verbose=False)
            if res['best'] > 1.0 + 1e-9:
                print('parent', par, 'rebase bound > cap (max Kraft %.3f); skipped' % res['best'], flush=True)
                continue
            T = feasible_triples(res)
            builds = []
            for it in range(a.builds):
                tri = T[it] if (rnd == 0 and it < len(T)) else rng.choice(T)
                nc, st = hybrid(c, res, tri, a.cap, None if (rnd == 0 and it < len(T)) else rng, a.paar)
                ok, inf = verify(nc); m = metrics(nc)
                if ok and m[0] <= a.capa and m[1] <= a.capad and m[3] <= a.cap:
                    builds.append((m[2], cid(nc), nc, tri))
            builds = [b for b in builds if b[0] <= a.max_build]
            builds.sort(key=lambda t: t[0])
            seen = set(); pick = []
            for b in builds:
                if b[1] in seen: continue
                seen.add(b[1]); pick.append(b)
                if len(pick) >= a.top: break
            print('round %d parent %s: %d builds, picked G %s' % (rnd, Path(par).name, len(builds), [p[0] for p in pick]), flush=True)
            for g0, h, nc, tri in pick:
                if time.time() - t0 >= a.hours * 3600: break
                cur, cm = nc, metrics(nc); seeds = []
                tj = time.time()
                for st in range(a.stages):
                    sd = rng.randrange(1, 10 ** 6); seeds.append(sd)
                    jd = out / 'jobs' / ('%s-r%d-s%d' % (h, rnd, st)); jd.mkdir(parents=True, exist_ok=True)
                    cands, info = O._kernel(cur, caps, 'cost,gd', sd, a.seconds, jd, BIN)
                    for k in cands:
                        k = clean(k); ok, inf = verify(k)
                        if not ok: continue
                        m = metrics(k)
                        if m[0] <= a.capa and m[1] <= a.capad and m[3] <= a.cap and (m[2], m[3]) < (cm[2], cm[3]):
                            cur, cm = k, m
                    print('   build %s G%d stage %d -> %s' % (h, g0, st, cm), flush=True)
                kid = cid(cur)
                p = out / 'pool' / ('a%d-ad%d-g%d-gd%d-%s.bfx' % (cm[0], cm[1], cm[2], cm[3], kid))
                p.write_text(core.to_kernel(cur))
                (out / 'pool' / ('build-%s.bfx' % h)).write_text(core.to_kernel(nc))
                log.write(json.dumps({'parent': str(Path(par).resolve()), 'round': rnd, 'triple': tri, 'build_G': g0,
                                      'build_id': h, 'result': cm, 'file': str(p), 'kernel_seeds': seeds,
                                      'stage_seconds': a.seconds, 'caps': caps, 'elapsed_s': round(time.time() - tj, 1),
                                      'kernel_bin': info.get('kernel_bin'), 'utc': time.strftime('%H:%M:%S', time.gmtime())}) + '\n')
                log.flush()
        rnd += 1


if __name__ == '__main__':
    main()
