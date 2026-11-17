"""planexec: one arm of the planned-join A/B on one CPU (2026-11-17).

    python3 -m boolflux.hub.planexec --function F --pool POOL.pkl --out DIR --seed S --budget SECONDS
        (--plan PLAN.jsonl | --blind --join-seconds T)  [--polish S] [--pull S] [--per-class N]

planned: the rows of a stage plan (stageplan.py) in target classes are built as minimal-support joins, then
         polished and pulled in round-robin order over the target classes (reach first, then new classes with
         the most room: fewest G of a dominating known circuit minus the built G).
blind:   the hub's join on random pool pairs (join.join_all, both roles) for --join-seconds (= the planned arm's
         planning CPU), kept as the hub keeps them (cell rule + NEAR_SLACK against the known points), then the
         same polish + pull on the kept candidates, highest value gain first; another join phase when they run out.
Each candidate: kernel polish at its own (A, AD, GD) caps for --polish s, then a pull from the polish best
(GD - 1, same A and AD caps) for --pull s; the kernel's final and intermediate bests are cleaned and verified
(core evaluation + independent verifier on all 256 inputs, hub common.verify).  DIR/events.jsonl: every
candidate, kernel call and verified circuit; DIR/circuits/<id>.bfx: every verified circuit.
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import random
import time
from pathlib import Path

from .common import core, clean, metrics, verify, cid, structure_key, leq
from . import join as J
from . import stageplan as SP
from . import ops as OPS
from .archive import NEAR_SLACK, VALUE_W


def value_gain(m, pts):
    """Archive.gain ('value' rule) of tuple m against the point set pts (pareto not needed: same answer)"""
    if any(leq(q, m) for q in pts): return 0.0
    A, AD, G, GD = m
    if not any(q[0] <= A and q[1] <= AD for q in pts):
        return VALUE_W['A'] if any(q[1] <= AD for q in pts) else VALUE_W['AD']
    box = [q[2] for q in pts if q[0] <= A and q[1] <= AD and q[3] <= GD]
    if not box: return VALUE_W['GD']
    d = min(min(box) - G, VALUE_W['Gmax'])
    return VALUE_W['G1'] + VALUE_W['Gstep'] * (d - 1)


def hub_placeable(m, cells, front):
    """Archive.would_place with the default slack, against static cells {(A,AD,GD): minG} and front points"""
    k = (m[0], m[1], m[3]); g = cells.get(k)
    if not (g is None or m[2] < g): return False
    doms = [q[2] for q in front if leq(q, m)]
    return not doms or m[2] <= min(doms) + NEAR_SLACK


class Arm:
    def __init__(self, a):
        self.a = a; self.out = Path(a.out); self.out.mkdir(parents=True, exist_ok=True)
        (self.out / 'circuits').mkdir(exist_ok=True)
        self.ev = open(self.out / 'events.jsonl', 'a')
        self.t0 = time.time(); self.c0 = time.process_time()
        self.seen = set(); self.found = {}
        self.rng = random.Random(a.seed)

    def log(self, **kw):
        kw['t'] = round(time.time() - self.t0, 2)
        self.ev.write(json.dumps(kw) + '\n'); self.ev.flush()

    def record(self, c, how, src):
        cc = clean(c); k = structure_key(cc)
        if k in self.seen: return None
        self.seen.add(k)
        ok, info = verify(cc)
        m = metrics(cc)
        if not ok:
            self.log(ev='reject', m=m, why=info.get('error'), how=how, src=src); return None
        i = cid(cc)
        (self.out / 'circuits' / (i + '.bfx')).write_text(core.to_kernel(cc))
        self.found[i] = m
        self.log(ev='circuit', id=i, m=m, how=how, src=src)
        return cc

    def kernel(self, c, caps, seconds, tag, src):
        jd = self.out / 'k' / ('%04d-%s' % (len(list((self.out / 'k').glob('*'))) if (self.out / 'k').exists() else 0, tag))
        jd.mkdir(parents=True, exist_ok=True)
        seed = self.rng.randrange(1 << 30)
        cands, info = OPS._kernel(c, caps, OPS.DEFAULT_OBJECTIVE, seed, seconds, jd, str(self.out.parent / 'bin'))
        kept = sorted(Path(info['bests_dir']).glob('best-*.bfx'), key=lambda p: int(p.stem.split('-')[1]))
        outs = []
        for p in kept:
            try: outs.append(core.from_kernel(p.read_text(), p.stem))
            except Exception: pass
        outs += cands
        for x in outs: self.record(x, tag, src)
        best = clean(cands[0]) if cands else None
        self.log(ev='kernel', tag=tag, caps=caps, seconds=seconds, seed=seed, n_bests=len(kept),
                 best=metrics(best) if best else None, src=src, t_imp=info.get('t_last_improvement'))
        return best

    def polish_pull(self, c, src):
        A, AD, G, GD = metrics(c)
        b = self.kernel(c, {'A': A, 'AD': AD, 'GD': GD}, self.a.polish, 'polish', src) or c
        A2, AD2, G2, GD2 = metrics(b)
        if self.a.pull > 0 and self.left() > 5:
            self.kernel(b, {'A': A2, 'AD': AD2, 'GD': max(1, GD2 - 1)}, min(self.a.pull, max(5, self.left())), 'pull', src)

    def left(self):
        return self.a.budget - (time.time() - self.t0)


def planned(arm, pool, pts, a):
    rows = [json.loads(l) for l in open(a.plan)]
    rows = [r for r in rows if r.get('kind') and SP.MIN_A <= r['A'] <= a.max_a and r['AD'] <= a.max_ad]
    # a few rows per (class, recipe): recipe = (front stages, back stages, LY)
    seen = {}; pick = []
    for r in rows:
        k = (r['A'], r['AD'], tuple(r['Xst']), tuple(r['Yst']), r['LY'])
        if seen.get(k, 0) >= a.per_recipe: continue
        seen[k] = seen.get(k, 0) + 1; pick.append(r)
    byid = {T.id: T for T in pool}
    built = {}; nmis = [0]
    tb = time.time()
    for r in pick:
        X, Y = byid.get(r['X']), byid.get(r['Y'])
        if X is None or Y is None: continue
        c = SP.build_pair(X, Y, r['LY'])
        if c is None: arm.log(ev='build-fail', row=r); continue
        m = metrics(c)
        if (m[0], m[1]) != (r['A'], r['AD']):
            nmis[0] += 1                                   # clean() merged an X AND with a Y AND (A lower) or AD moved
            r = dict(r, kind=SP.classify(m[0], m[1], pts), planned=[r['A'], r['AD']])
            if r['kind'] is None or m[0] > a.max_a or m[1] > a.max_ad: continue
        k = (m[0], m[1])
        room = SP.class_room(m[0], m[1], pts)
        built.setdefault(k, []).append((m, c, r, room))
    arm.log(ev='built', rows=len(rows), picked=len(pick), mismatched=nmis[0], classes={'%d/%d' % k: len(v) for k, v in built.items()},
            seconds=round(time.time() - tb, 2))
    # classes in value order (A, then AD), reach first; a class whose best build is more than --max-excess gates above
    # its room (fewest G of a dominating known circuit) is left out
    def best_g(k): return min(x[0][2] for x in built[k])
    order = [k for k in sorted(built, key=lambda k: (0 if built[k][0][2]['kind'] == 'reach' else 1, k))
             if built[k][0][3] is None or best_g(k) - built[k][0][3] <= a.max_excess]
    queues = []
    for k in order:
        v = sorted(built[k], key=lambda x: (x[0][2], x[0][3]))
        dedup = []; sk = set(); rec = {}
        for x in v:
            s = structure_key(x[1]); rk = (tuple(x[2]['Xst']), tuple(x[2]['Yst']), x[2]['LY'])
            if s in sk: continue
            sk.add(s)
            if rec.get(rk, 0) >= 1 and len(v) > a.per_class: continue      # prefer distinct recipes
            rec[rk] = rec.get(rk, 0) + 1; dedup.append(x)
        queues.append(dedup[:a.per_class])
    sched = []
    for i in range(max((len(q) for q in queues), default=0)):
        for q in queues:
            if i < len(q): sched.append(q[i])
    arm.log(ev='schedule', n=len(sched), order=['%d/%d room %s best %d' % (k + (built[k][0][3], best_g(k))) for k in order])
    for m, c, r, room in sched:
        if arm.left() < 10: break
        src = {'arm': 'planned', 'X': r['X'], 'Y': r['Y'], 'LY': r['LY'], 'kind': r['kind'], 'raw': m, 'room': room,
               'Xst': r['Xst'], 'Yst': r['Yst'], 'Xorigin': r['Xorigin'], 'Yorigin': r['Yorigin']}
        arm.record(c, 'join', src)
        arm.polish_pull(c, src)


def blind(arm, pool, pts, a):
    """join phases of --join-seconds on random pairs, each followed by polish + pull of its kept candidates (highest
    value gain first); a new join phase starts when the kept candidates are used up and time is left"""
    cells = {}
    for p in pts:
        k = (p[0], p[1], p[3]); cells[k] = min(cells.get(k, 999), p[2])
    front = [p for p in pts if not any(q != p and leq(q, p) for q in pts)]
    kept = {}; done = set(); phase = 0
    while arm.left() > 10:
        tried = 0; pairs = 0; tj = time.time(); new = 0
        while time.time() - tj < a.join_seconds and arm.left() > 10:
            X, Y = arm.rng.sample(pool, 2); pairs += 1
            PX, PY = J.Prepared(X.c, X.id), J.Prepared(Y.c, Y.id)
            for F, B in ((PX, PY), (PY, PX)):
                for c, LX, LY, nint in J.join_all(F, B):
                    tried += 1
                    cc = clean(c); m = metrics(cc)
                    if m[0] < SP.MIN_A: continue
                    if not hub_placeable(m, cells, front): continue
                    s = structure_key(cc)
                    if s in kept or s in done: continue
                    new += 1
                    kept[s] = (value_gain(m, pts), m, cc, {'arm': 'blind', 'X': F.id, 'Y': B.id, 'LX': LX, 'LY': LY, 'raw': m})
        arm.log(ev='blind-joins', phase=phase, pairs=pairs, tried=tried, kept=new, seconds=round(time.time() - tj, 2),
                classes={'%d/%d' % k: n for k, n in _count((v[1][0], v[1][1]) for v in kept.values()).items()})
        phase += 1
        sched = sorted(kept.items(), key=lambda x: (-x[1][0], x[1][1][2]))
        for s, (g, m, c, src) in sched:
            if arm.left() < 10: break
            done.add(s); kept.pop(s)
            arm.record(c, 'join', src)
            arm.polish_pull(c, src)


def _count(it):
    d = {}
    for k in it: d[k] = d.get(k, 0) + 1
    return d


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--function', required=True, choices=('aes-sbox', 'aes-invsbox'))
    ap.add_argument('--pool', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--budget', type=float, required=True, help='wall seconds of the whole arm (after loading)')
    ap.add_argument('--plan')
    ap.add_argument('--blind', action='store_true')
    ap.add_argument('--join-seconds', type=float, default=300)
    ap.add_argument('--polish', type=float, default=60)
    ap.add_argument('--pull', type=float, default=45)
    ap.add_argument('--per-class', type=int, default=2)
    ap.add_argument('--per-recipe', type=int, default=3)
    ap.add_argument('--max-a', type=int, default=40)
    ap.add_argument('--max-ad', type=int, default=7)
    ap.add_argument('--max-excess', type=int, default=30, help='planned: skip a class whose best raw join is this far above its room')
    a = ap.parse_args(argv)
    os.environ['BOOLFLUX_FUNCTION'] = a.function
    pool = pickle.load(open(a.pool, 'rb'))
    pts = SP.known_points(pool)
    arm = Arm(a)
    arm.log(ev='start', args=vars(a), pool=len(pool), known=len(pts))
    if a.blind: blind(arm, pool, pts, a)
    else: planned(arm, pool, pts, a)
    arm.log(ev='end', found=len(arm.found), cpu=round(time.process_time() - arm.c0, 1))


if __name__ == '__main__':
    main()
