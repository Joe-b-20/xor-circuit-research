#!/usr/bin/env python3
"""P6 oscillation through re-basing for AD3 circuits (T08 GD12 gate count).

    python3 oscloop.py --pool DIR --cap 12 --hours H --seed S [--seeds-from F ...] [--relax-seconds 40]
                       [--seconds 240] [--builds 30] [--top 2] [--p-fresh 0.15]

Pool = verified circuits with A<=35, AD<=3, GD<=cap (file names a35-ad3-gG-gdD-<id>.bfx).  One step:
  pick a pool member (rank-biased to low G); with p-fresh pick a seed file instead;
  RELAX: gate kernel under caps (A35, AD3, GD cap+1) for --relax-seconds (G falls, the depth slack
         moves) - skipped for seed files at GD > cap;
  PULL:  botbasis re-basing at the cap on the relaxed circuit; if max Kraft <= 1, --builds hybrid
         builds (random feasible triples) and the --top lowest-G builds get a kernel stage of
         --seconds under (A35, AD3, GD cap); every result is verified and pooled.
The relaxed circuits (GD cap+1) are kept in POOL/relaxed/ (they are T08 GD13 candidates).
Every hard cap (A<=35, AD<=3) is enforced by the kernel caps and re-checked on every pooled circuit.
Log: POOL/../oscloop-s<seed>.jsonl.
"""
import sys, json, time, random, argparse, hashlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core                                        # noqa: E402
from boolflux.hub.common import verify, metrics, clean, load      # noqa: E402
from boolflux.hub import ops as O                                 # noqa: E402
O.KDEFAULTS['repair_keep'] = 1   # compliance 18:20: no move may raise any single cap excess (A/AD stay hard)
import botbasis as BB                                             # noqa: E402
from rebase import feasible_triples                               # noqa: E402
from hybrid import hybrid                                         # noqa: E402

BIN = Path.home() / 'xs-campaigns/2026-11-15-targets/P6/kbin'


def cid(c):
    return hashlib.sha1(core.to_kernel(c).encode()).hexdigest()[:12]


def put(d, c):
    m = metrics(c); p = d / ('a%d-ad%d-g%d-gd%d-%s.bfx' % (m[0], m[1], m[2], m[3], cid(c)))
    if not p.exists(): p.write_text(core.to_kernel(c))
    return p


def best_of(cands, caps):
    out = None
    for k in cands:
        k = clean(k); ok, _ = verify(k)
        if not ok: continue
        m = metrics(k)
        if m[0] <= caps['A'] and m[1] <= caps['AD'] and m[3] <= caps['GD']:
            if out is None or (m[2], m[3]) < (out[1][2], out[1][3]): out = (k, m)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pool', required=True); ap.add_argument('--cap', type=int, default=12)
    ap.add_argument('--hours', type=float, default=1); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--seeds-from', nargs='*', default=[]); ap.add_argument('--relax-seconds', type=float, default=40)
    ap.add_argument('--seconds', type=float, default=240); ap.add_argument('--builds', type=int, default=30)
    ap.add_argument('--top', type=int, default=2); ap.add_argument('--p-fresh', type=float, default=0.15)
    ap.add_argument('--keep', type=int, default=40)
    a = ap.parse_args()
    pool = Path(a.pool); pool.mkdir(parents=True, exist_ok=True); (pool / 'relaxed').mkdir(exist_ok=True)
    jobs = pool.parent / 'jobs'; jobs.mkdir(exist_ok=True)
    log = open(pool.parent / ('oscloop-s%d.jsonl' % a.seed), 'a')
    rng = random.Random(a.seed); t0 = time.time(); it = 0
    capA, capAD = 35, 3
    for f in a.seeds_from:
        c = load(f); m = metrics(c)
        if m[0] <= capA and m[1] <= capAD and m[3] <= a.cap and verify(c)[0]: put(pool, c)
    while time.time() - t0 < a.hours * 3600:
        it += 1; rec = {'it': it, 'utc': time.strftime('%H:%M:%S', time.gmtime())}
        members = sorted(pool.glob('a*-ad*-g*-gd*-*.bfx'), key=lambda p: (int(p.stem.split('-')[2][1:]), p.name))
        members = members[:a.keep]
        if a.seeds_from and (not members or rng.random() < a.p_fresh):
            src = Path(rng.choice(a.seeds_from)); rec['src_kind'] = 'seed'
        else:
            i = min(int(rng.expovariate(1 / 3.0)), len(members) - 1)
            src = members[i]; rec['src_kind'] = 'pool'
        rec['src'] = str(src)
        c = load(src); m0 = metrics(c); rec['src_m'] = m0
        tj = time.time()
        # RELAX
        if m0[3] <= a.cap:
            sd = rng.randrange(1, 10 ** 6); jd = jobs / ('it%d-relax' % it); jd.mkdir(exist_ok=True)
            caps = {'A': capA, 'AD': capAD, 'GD': a.cap + 1}
            cands, info = O._kernel(c, caps, 'cost,gd', sd, a.relax_seconds, jd, BIN)
            r = best_of(cands, caps)
            if r is None:
                rec['fail'] = 'relax'; log.write(json.dumps(rec) + '\n'); log.flush(); continue
            c, mr = r; rec['relax_seed'] = sd; rec['relaxed'] = mr
            if mr[3] > a.cap: put(pool / 'relaxed', c)
        # PULL
        tmp = jobs / ('it%d-src.bfx' % it); tmp.write_text(core.to_kernel(c))
        res = BB.analyse(str(tmp), a.cap, verbose=False)
        rec['kraft'] = res['best']
        if res['best'] > 1.0 + 1e-9:
            rec['fail'] = 'bound'; log.write(json.dumps(rec) + '\n'); log.flush(); continue
        T = feasible_triples(res)
        builds = []
        order = list(T); rng.shuffle(order)
        for b in range(min(a.builds, len(order))):
            tri = order[b]
            nc, st = hybrid(c, res, tri, a.cap, None, True)
            ok, _ = verify(nc); m = metrics(nc)
            if ok and m[0] <= capA and m[1] <= capAD and m[3] <= a.cap:
                builds.append((m[2], cid(nc), nc, tri))
        builds.sort(key=lambda t: t[0]); seen = set(); pick = []
        for b in builds:
            if b[1] not in seen:
                seen.add(b[1]); pick.append(b)
            if len(pick) >= a.top: break
        rec['builds'] = [p[0] for p in pick]; rec['results'] = []
        for g0, h, nc, tri in pick:
            sd = rng.randrange(1, 10 ** 6); jd = jobs / ('it%d-%s' % (it, h)); jd.mkdir(exist_ok=True)
            caps = {'A': capA, 'AD': capAD, 'GD': a.cap}
            cands, info = O._kernel(nc, caps, 'cost,gd', sd, a.seconds, jd, BIN)
            r = best_of(cands, caps)
            if r is None: continue
            k, mk = r; p = put(pool, k)
            rec['results'].append({'build_G': g0, 'triple': tri, 'seed': sd, 'm': mk, 'file': str(p)})
        rec['elapsed_s'] = round(time.time() - tj, 1)
        log.write(json.dumps(rec) + '\n'); log.flush()
        print(it, rec.get('src_m'), '->', rec.get('relaxed'), 'K%.2f' % rec['kraft'], rec['builds'],
              [x['m'][2] for x in rec['results']], flush=True)


if __name__ == '__main__':
    main()
