#!/usr/bin/env python3
"""Goal-directed aslack run (agent R2): repeated aslack (window redesign + kernel polish) under a goal's
caps, starting from the archive circuits closest to the goal, with a small pool per goal.

    python3 goal_run.py ARCHIVE_CAMPAIGN OUTDIR HOURS SEED SECONDS GOALS(e.g. B,C,D,E)

A goal hit (A, AD, GD within caps and G <= cap) is checked with campaigns/aes_check.check and saved to
OUTDIR/found/ (.bfx + .json sidecar: goal, parents, seed, code md5, time).  log.jsonl: one line per op call."""
import argparse, hashlib, json, random, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
PKG_PARENT = next(q for q in HERE.parents if (q / 'boolflux' / 'core.py').exists())
sys.path.insert(0, str(PKG_PARENT)); sys.path.insert(0, str(PKG_PARENT / 'boolflux' / 'campaigns'))
from boolflux import core                         # noqa: E402
from boolflux.hub.archive import Archive          # noqa: E402
from boolflux.hub.common import metrics           # noqa: E402
import op_aslack as OP                            # noqa: E402
import aes_check                                  # noqa: E402

# goal: (A cap, AD cap (exact AD for B/C/D/F), G cap, GD cap)
GOALS = {'B': (28, 4, 130, 22), 'C': (28, 5, 127, 19), 'D': (32, 4, 116, 19), 'E': (32, 6, 102, 31),
         'F': (35, 3, 138, 26), 'G': (44, 4, 140, 11)}

camp, outd, hours, seed, secs, goals = sys.argv[1], Path(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5]), sys.argv[6].split(',')
outd.mkdir(parents=True, exist_ok=True); (outd / 'found').mkdir(exist_ok=True); (outd / 'jobs').mkdir(exist_ok=True)
rng = random.Random(seed)
md5 = {f: hashlib.md5((HERE / f).read_bytes()).hexdigest() for f in ('aslack.py', 'op_aslack.py', 'goal_run.py')}
ar = Archive(camp)


def dist(m, g):
    return (max(0, m[0] - g[0]) * 4 + max(0, m[1] - g[1]) * 50 + max(0, m[2] - g[2]) + max(0, m[3] - g[3]) * 2)


def lk(m, g):
    return (dist(m, g),) + tuple(m)


pool = {}
for gname in sorted(set(goals)):
    g = GOALS[gname]
    cand = [(lk((r['A'], r['AD'], r['G'], r['GD']), g), i) for i, r in ar.rec.items() if r['A'] <= g[0] + 8 and r['AD'] <= g[1]]
    cand.sort()
    pool[gname] = [(k, ar.circuit(i), i) for k, i in cand[:12]]


class FakeAr:
    def __init__(self, c): self.c = c
    def circuit(self, i): return self.c
    def would_place(self, m): return True
    def gain(self, m): return 0.0


end = time.time() + hours * 3600; it = 0; hits = set()
log = open(outd / 'log.jsonl', 'a')
while time.time() < end:
    gname = goals[it % len(goals)]; g = GOALS[gname]; it += 1
    P = pool[gname]
    k, c, pid = P[min(int(rng.expovariate(0.6)), len(P) - 1)] if rng.random() < 0.8 else rng.choice(P)
    jd = outd / 'jobs' / ('j%05d-%s' % (it, gname)); jd.mkdir(exist_ok=True)
    a = argparse.Namespace(inp=pid, caps={'A': g[0], 'AD': g[1], 'GD': g[3]}, objective='a,ad,cost,gd', seed=rng.randrange(1, 1 << 30),
                           seconds=secs, archive=str(outd), max_cands=40, npolish=3, hunt=0.1, ztries=4, partners=0, in2=None)
    t0 = time.time()
    try:
        cands, info = OP.op_aslack(FakeAr(c), a, random.Random(a.seed), jd)
    except Exception as e:
        log.write(json.dumps({'it': it, 'goal': gname, 'error': repr(e)[:200]}) + '\n'); log.flush(); continue
    best = None; new = 0
    for nc in cands:
        m = metrics(nc); kk = lk(m, g)
        if best is None or kk < best: best = kk
        kt = core.to_kernel(nc)
        if all(core.to_kernel(x[1]) != kt for x in P) and kk < P[-1][0]:
            P.append((kk, nc, '%s/j%05d' % (gname, it))); new += 1
        if kk[0] == 0 and kt not in hits:
            hits.add(kt)
            name = 'R2-goal%s-a%d-ad%d-g%d-gd%d-%s' % (gname, *m, hashlib.sha1(kt.encode()).hexdigest()[:8])
            p = outd / 'found' / (name + '.bfx'); p.write_text(kt)
            r = aes_check.check(str(p))
            (outd / 'found' / (name + '.json')).write_text(json.dumps({
                'goal': gname, 'metrics': m, 'parent': pid, 'seed': a.seed, 'op': 'aslack goal_run', 'code_md5': md5,
                'time_utc': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()), 'aes_check_ok': r.get('ok'),
                'new_point': r.get('new_point')}, indent=1, default=str))
            log.write(json.dumps({'ev': 'HIT', 'goal': gname, 'm': m, 'file': str(p), 'aes_check_ok': r.get('ok')}) + '\n')
    P.sort(key=lambda x: x[0]); del P[12:]
    log.write(json.dumps({'it': it, 'goal': gname, 'start': pid, 'start_key': k, 'best_key': best, 'new_in_pool': new,
                          'pool_best': P[0][0], 'stats': info.get('stats', {}).get('func_ok'), 'secs': round(time.time() - t0, 1)}) + '\n')
    log.flush()
