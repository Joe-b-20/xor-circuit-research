#!/usr/bin/env python3
"""T1 targeted descent worker for goals B (28/4/<=130/<=22) and C (28/5/<=127/<=19).

    python3 t1run.py --goal B --seed 1 --hours 4.5 --data DIR --name w0 [--ops polish,osc,trb,join,skel,pullA]

One process = one loop on one CPU.  A local pool (circuits with A <= 28 and AD <= goal AD, near the
goal) is seeded from the hub archive (A28 records, plus A29 records for the A-pull) and from the
shared directory DATA/shared/ where all T1 workers write admitted circuits.  Each job picks a start
(weight exp(-excess/2), excess = (G-Gt)^+ + (GD-GDt)^+) and an operator (bandit on improvements per
CPU-minute with a floor):
  polish  gate kernel (hub ops._kernel) under caps (28, ADt, GDt), objective a,cost,gd
  osc     kernel under GD cap GDt+1..3, then repair/polish at GDt
  trb     chained timing-aware XOR-region rebuilds at D = GDt (hub trb_impl), then a short polish
  join    front/back joins (hub join.py) of the start with pool + hub partners, best kept, short polish
  skel    gen_skel kick (skeleton move + seeded rebuild + 8 s polish), then polish at the goal caps
  pullA   start from an A29 circuit, kernel under caps (28, ADt, GDt+2) then polish at goal caps
Every candidate is verified (hub common.verify: core + independent verifier) before it enters the
pool.  A circuit meeting goal B or C is checked with campaigns/aes_check.py and saved to DATA/found/
with a JSON sidecar.  Every job is one line in DATA/<name>.jobs.jsonl.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import signal
import subprocess
import sys
import time
from pathlib import Path

PKG = Path('/home/joebachir20/xcr-boolflux/nonlinear/boolflux')
sys.path.insert(0, str(PKG.parent))
sys.path.insert(0, str(PKG / 'hub' / 'ops'))
sys.path.insert(0, str(PKG / 'hub' / 'ops' / 'e_lib'))
from boolflux.hub import ops as HO                       # noqa: E402
from boolflux.hub import join as J                       # noqa: E402
from boolflux.hub import trb_impl                        # noqa: E402
from boolflux.hub.common import core, metrics, verify, code_version, MODEL   # noqa: E402
import gen_skel as GS                                    # noqa: E402

HUBAR = Path('/home/joebachir20/xs-campaigns/2026-11-14-hub/long/archive')
GOALS = {'B': (28, 4, 130, 22), 'C': (28, 5, 127, 19)}
# v3 base operator weights (L1: same-caps polish at the goal-near tuples: 0 improvements in 9-24 jobs each;
# pull with GD - 1 and the AD cap off on originals moved A <= 29)
BASEW = {'gfree': 0.3, 'pullD': 0.45, 'polish': 0.06, 'deep': 0.06, 'osc': 0.1, 'trb': 0.1, 'skel': 0.12, 'join': 0.05, 'pullA': 0.06}
OBJ = 'a,cost,gd'


def cid(c):
    return hashlib.sha1(core.to_kernel(c).encode()).hexdigest()[:12]


def meets(m, g):
    return m[0] <= g[0] and m[1] <= g[1] and m[2] <= g[2] and m[3] <= g[3]


class Worker:
    def __init__(self, a):
        self.a = a; self.goal = GOALS[a.goal]
        self.rng = random.Random(a.seed)
        self.data = Path(a.data); self.shared = self.data / a.shared; self.found = self.data / 'found'
        for d in (self.shared, self.found): d.mkdir(parents=True, exist_ok=True)
        self.job = self.data / 'scratch' / a.name; self.job.mkdir(parents=True, exist_ok=True)
        self.log = open(self.data / (a.name + '.jobs.jsonl'), 'a')
        self.pool = {}      # id -> (circuit, metrics, origin)
        self.a29 = {}
        self.seen_shared = set()
        self.ops = a.ops.split(',')
        self.st = {o: [0, 0.0, 0] for o in self.ops}
        self.extra_scan = [Path(x) for x in (a.extra or [])]   # jobs, cpu_s, improvements
        self.ver = code_version()
        self.t0 = time.time(); self.ks = []
        self.orig = set()          # seed/ingest originals and circuits with a tuple first reached by this run
        self.tries = {}            # (AD, G, GD) -> jobs started from it in this worker
        self.base = dict(BASEW)
        if not self.a.no_hub: self.load_hub()
        self.scan_shared()
        self.ref = self.load_ref()
        self.harvest('startup')          # v3.3: outputs of a job killed by an earlier stop of this worker
        signal.signal(signal.SIGTERM, self.on_term)

    # ---- v3.3: harvest of killed jobs, frontier saving ---------------------------------------
    def load_ref(self):
        ref = set()
        try:
            from boolflux.hub.common import published
            ref = set(published())
        except Exception: pass
        for f in HUBAR.glob('*.json'):
            if f.name == 'cells.json': continue
            try: r = json.loads(f.read_text()); ref.add((r['A'], r['AD'], r['G'], r['GD']))
            except Exception: pass
        return ref

    def harvest(self, why):
        got = []
        for d in sorted(self.job.iterdir()) if self.job.exists() else []:
            b = d / 'best.bfx'
            if not b.exists(): continue
            try: c = core.from_kernel(b.read_text(), 'h')
            except Exception: continue
            r = self.admit(c, 'harvest-%s:%s' % (why, d.name))
            got.append((metrics(c), r))
        self.emit({'event': 'harvest', 'why': why, 'got': got})

    def on_term(self, signum, frame):
        try: self.harvest('sigterm')
        finally: os._exit(0)

    def save_front(self, c, m, origin):
        """v3.3: a circuit not dominated by (or equal to) any hub archive / pinned NIST tuple -> found/front/ + aes_check"""
        if any(all(a <= b for a, b in zip(q, m)) for q in self.ref): return
        d = self.found / 'front'; d.mkdir(exist_ok=True)
        name = 'aes-sbox-a%d-ad%d-g%d-gd%d-%s' % (m + (cid(c),))
        if (d / (name + '.bfx')).exists(): return
        (d / (name + '.bfx')).write_text(core.to_kernel(c))
        r = subprocess.run([sys.executable, str(PKG / 'campaigns' / 'aes_check.py'), str(d / (name + '.bfx')), '--json',
                            str(d / (name + '.check.json'))], capture_output=True, text=True)
        (d / (name + '.json')).write_text(json.dumps({'tuple': m, 'origin': origin, 'worker': self.a.name, 'seed': self.a.seed,
                                                       'driver': 'strategies/T1/t1run.py v3.3', 'code_version': self.ver,
                                                       'time_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'aes_check_rc': r.returncode}, indent=1))
        self.emit({'event': 'FRONT', 'm': m, 'file': str(d / (name + '.bfx')), 'aes_check_rc': r.returncode})

    # ---- pool ------------------------------------------------------------------------------
    def excess(self, m):
        # v3: AD above the goal's AD counts 4 (repairable by an AD-capped kernel run, but far)
        return max(0, m[2] - self.goal[2]) + max(0, m[3] - self.goal[3]) + 4 * max(0, m[1] - self.goal[1])

    def in_scope(self, m):
        # v3: AD <= 5 kept for both goals (pullD with the AD cap off makes AD5 circuits; they serve C and are AD-repair starts for B)
        return m[0] <= 28 and m[1] <= self.a.admax and m[2] <= self.goal[2] + self.a.gslack and m[3] <= self.goal[3] + self.a.gdslack

    def front(self):
        pts = {v[1][2:] for v in self.pool.values()}
        return [p for p in pts if not any(q != p and q[0] <= p[0] and q[1] <= p[1] for q in pts)]

    def admit(self, c, origin, verified=False):
        """returns 'new_front', 'pool' or None"""
        m = metrics(c)
        if not self.in_scope(m): return None
        i = cid(c)
        if i in self.pool: return None
        same = [k for k, v in self.pool.items() if v[1][2:] == m[2:]]
        # v3.1: dominance on the full (A, AD, G, GD) tuple (v3 compared (G, GD) across AD classes)
        pts = {v[1] for v in self.pool.values()}
        dominated = any(all(a <= b for a, b in zip(q, m)) for q in pts)
        strict_dom = any(all(a <= b for a, b in zip(q, m)) and q != m for q in pts)
        if len(same) >= 6: return None
        if not verified:
            ok, info = verify(c)
            if not ok:
                self.emit({'event': 'verify_fail', 'origin': origin, 'm': m, 'info': info}); return None
        if not same: self.orig.add(i)
        self.pool[i] = (c, m, origin)
        p = self.shared / (i + '.bfx')
        if not p.exists():
            tmp = self.shared / ('.%s.%s.tmp' % (i, self.a.name)); tmp.write_text(core.to_kernel(c)); os.replace(tmp, p)
            (self.shared / (i + '.json')).write_text(json.dumps({'id': i, 'm': m, 'origin': origin, 'worker': self.a.name,
                                                                  'goal': self.a.goal, 't': time.time(), 'code_version': self.ver}))
        self.seen_shared.add(i)
        for gname, g in GOALS.items():
            if meets(m, g): self.save_found(c, m, gname, origin)
        if hasattr(self, 'ref'): self.save_front(c, m, origin)
        return 'new_front' if not dominated else ('pool' if not strict_dom else 'pool_dom')

    def load_hub(self):
        n = 0
        for f in HUBAR.glob('*.json'):
            if f.name == 'cells.json': continue
            try: r = json.loads(f.read_text())
            except Exception: continue
            m = (r['A'], r['AD'], r['G'], r['GD'])
            if m[0] == 28 and self.in_scope(m):
                c = core.from_kernel((HUBAR / (r['id'] + '.bfx')).read_text(), r['id'])
                if metrics(c) != m: continue
                self.pool[r['id']] = (c, m, 'hub:' + r['id']); n += 1
                if r.get('operator') in ('seed', 'ingest'): self.orig.add(r['id'])
            elif m[0] == 29 and m[1] <= self.goal[1] and m[2] <= self.goal[2] + 3 and m[3] <= self.goal[3] + 4:
                c = core.from_kernel((HUBAR / (r['id'] + '.bfx')).read_text(), r['id'])
                self.a29[r['id']] = (c, m, 'hub:' + r['id'])
        self.emit({'event': 'load_hub', 'pool': n, 'a29': len(self.a29), 'front': sorted(self.front())})

    def scan_shared(self):
        k = 0
        for p in [q for d in [self.shared] + self.extra_scan for q in d.glob('*.bfx')]:
            i = p.stem.split('-')[-1]
            if i in self.seen_shared: continue
            self.seen_shared.add(i)
            try: c = core.from_kernel(p.read_text(), i)
            except Exception: continue
            m = metrics(c)
            if self.in_scope(m) and i not in self.pool:
                self.pool[i] = (c, m, 'shared:' + i); k += 1
        return k

    def pick(self, src=None):
        """v3: choose a tuple (weight exp(-excess/2) / (1 + tries)), then a structure in it (originals x3)"""
        src = src or self.pool
        tup = {}
        for k, v in src.items(): tup.setdefault(v[1], []).append(k)
        ts = list(tup)
        w = [math.exp(-self.excess(t) / 2.0) / (1.0 + self.tries.get(t, 0)) for t in ts]
        t = self.rng.choices(ts, weights=w)[0]
        ks = tup[t]
        k = self.rng.choices(ks, weights=[3.0 if x in self.orig else 1.0 for x in ks])[0]
        self.tries[t] = self.tries.get(t, 0) + 1
        return k, src[k]

    # ---- operators -------------------------------------------------------------------------
    def kernel(self, c, caps, sec, tag):
        d = self.job / tag; d.mkdir(exist_ok=True)
        if self.a.vary:      # per-call kernel diversity (annealing temperature, uphill excess)
            HO.KDEFAULTS['T0'] = self.rng.choice([0.3, 0.6, 0.6, 1.0])
            HO.KDEFAULTS['max_excess'] = self.rng.choice([4, 8, 8, 12])
        self.ks.append((tag, caps.get('GD'), sec, HO.KDEFAULTS['T0'], HO.KDEFAULTS['max_excess']))
        cs, info = HO._kernel(c, caps, OBJ, self.rng.randrange(1 << 30), sec, d, str(self.data))
        return cs[0] if cs else None

    def caps(self, gd=None):
        return {'A': 28, 'AD': self.goal[1], 'GD': self.goal[3] if gd is None else gd}

    def op_polish(self, c):
        x = self.kernel(c, self.caps(), self.rng.choice([30, 60, 60, 120]), 'p')
        return [x] if x else []

    def op_pullD(self, c):
        """v3 (L1: what moved A <= 29): kernel with GD cap = start GD - 1 (p 0.75) or - 2, AD cap off
        (p 0.5 for C, 0.3 for B; else the goal AD), A cap 28; then, if that met GD <= goal GD, a polish at the goal caps"""
        m = metrics(c)
        gd = m[3] - self.rng.choice([1, 1, 1, 2])
        adoff = self.rng.random() < (0.5 if self.a.goal == 'C' else 0.3)
        caps = {'A': 28, 'AD': None if adoff else self.goal[1], 'GD': gd}
        x = self.kernel(c, caps, self.rng.choice([60, 90, 90]), 'pd')
        out = [x] if x else []
        if x and metrics(x)[3] <= self.goal[3] and metrics(x)[1] <= self.goal[1] and metrics(x)[2] > self.goal[2]:
            x2 = self.kernel(x, self.caps(), 45, 'pd2')
            if x2: out.append(x2)
        return out

    def op_gfree(self, c):
        """v3.2: G first, GD free (caps A 28, AD <= admax), 120 s - for raw new-space circuits"""
        x = self.kernel(c, {'A': 28, 'AD': self.a.admax, 'GD': None}, 120, 'gf')
        return [x] if x else []

    def op_deep(self, c):
        x = self.kernel(c, self.caps(), self.a.deep_sec or self.rng.choice([240, 360, 480]), 'dp')
        return [x] if x else []

    def op_osc(self, c):
        r = self.rng.choice([1, 1, 2, 3])
        x1 = self.kernel(c, self.caps(self.goal[3] + r), self.rng.choice([20, 40]), 'o1')
        out = [x1] if x1 else []
        x2 = self.kernel(x1 or c, self.caps(), self.rng.choice([30, 60]), 'o2')
        if x2: out.append(x2)
        return out

    def op_trb(self, c):
        t0 = time.time(); best = []; cur = c; sec = self.rng.choice([10, 20])
        while time.time() - t0 < sec:
            D = self.goal[3] - self.rng.choice([0, 0, 0, 1])
            kind = self.rng.choice(['bottom', 'top', 'mid', 'random', 'random'])
            try: nc, info = trb_impl.rebuild(cur, D, kind, self.rng)
            except Exception: continue
            if nc is cur: continue
            m = metrics(nc)
            if m[0] <= 28 and m[1] <= self.goal[1]:
                best.append(nc)
                if self.rng.random() < 0.5: cur = nc
        best.sort(key=lambda x: (self.excess(metrics(x)), metrics(x)))
        out = best[:3]
        if out:
            x = self.kernel(out[0], self.caps(), 30, 't')
            if x: out.append(x)
        return out

    def op_join(self, c):
        X = J.Prepared(c, 'x')
        partners = list(self.pool.values())
        self.rng.shuffle(partners)
        partners = partners[:self.rng.choice([40, 80])]
        res = []; t0 = time.time()
        for pc, pm, po in partners:
            if time.time() - t0 > 40: break
            P = J.Prepared(pc, 'p')
            for F, B in ((X, P), (P, X)):
                for jc, LX, LY, nint in J.join_all(F, B):
                    m = metrics(jc)
                    if m[0] <= 28 and m[1] <= self.goal[1] and self.excess(m) <= 8:
                        res.append((self.excess(m), m, jc))
        res.sort(key=lambda r: (r[0], r[1]))
        out = []; seen = set()
        for e, m, jc in res:
            k = cid(jc)
            if k in seen: continue
            seen.add(k); out.append(jc)
            if len(out) >= 6: break
        if out:
            x = self.kernel(out[0], self.caps(), 30, 'j')
            if x: out.append(x)
        return out

    def op_skel(self, c):
        m0 = metrics(c)
        d = self.job / 'sk'; d.mkdir(exist_ok=True)
        out = []
        for _ in range(2):
            kc = GS.kick(c, d, self.rng.randrange(1 << 30), self.rng.choice([1, 1, 2, 3]), str(self.data))
            if kc is None: continue
            x = self.kernel(kc, {'A': 28, 'AD': self.goal[1], 'GD': None}, 8, 'sk1')
            if x is None: continue
            x2 = self.kernel(x, self.caps(), 40, 'sk2')
            out += [x] + ([x2] if x2 else [])
        return out

    def op_pullA(self, c):
        x1 = self.kernel(c, self.caps(self.goal[3] + 2), 60, 'a1')
        if not x1 or metrics(x1)[0] > 28: return [x1] if x1 else []
        x2 = self.kernel(x1, self.caps(), 60, 'a2')
        return [x1] + ([x2] if x2 else [])

    # ---- main loop ---------------------------------------------------------------------------
    def choose_op(self):
        w = []
        for o in self.ops:
            n, cpu, imp = self.st[o]
            b = self.base.get(o, 0.1)
            w.append(b * max(0.3, (imp + 1.0) / (cpu / 600.0 + 1.0)))
        return self.rng.choices(self.ops, weights=w)[0]

    def emit(self, d):
        d['t'] = round(time.time(), 1); self.log.write(json.dumps(d, default=str) + '\n'); self.log.flush()

    def run(self):
        k = 0
        while time.time() - self.t0 < self.a.hours * 3600:
            k += 1
            if k % 10 == 0: self.scan_shared()
            op = self.choose_op()
            if op == 'pullA':
                if not self.a29: continue
                i, (c, m, o) = self.pick(self.a29)
            else:
                i, (c, m, o) = self.pick()
            t0 = time.time(); c0 = os.times(); self.ks = []
            try:
                cands = getattr(self, 'op_' + op)(c)
                err = None
            except Exception as ex:
                cands = []; err = repr(ex)[:300]
            c1 = os.times()
            cpu = (c1.user + c1.system + c1.children_user + c1.children_system) - \
                  (c0.user + c0.system + c0.children_user + c0.children_system)
            outs = []; imp = 0
            e0 = self.excess(m)
            for x in cands:
                if x is None: continue
                mx = metrics(x)
                r = self.admit(x, '%s(%s)' % (op, i))
                outs.append((mx, r))
                if r == 'new_front' or (r and r != 'pool_dom' and self.excess(mx) < e0): imp += 1
                if r and mx not in self.tries: self.tries[mx] = 0
            self.st[op][0] += 1; self.st[op][1] += cpu; self.st[op][2] += imp
            self.emit({'job': k, 'op': op, 'parent': i, 'pm': m, 'cpu': round(cpu, 1), 'wall': round(time.time() - t0, 1),
                       'outs': outs, 'imp': imp, 'err': err, 'kernel': self.ks})
            if k % 20 == 0:
                self.emit({'event': 'status', 'front': sorted(self.front()), 'pool': len(self.pool), 'stats': self.st})

    def save_found(self, c, m, gname, origin):
        name = 'aes-sbox-a%d-ad%d-g%d-gd%d-%s' % (m[0], m[1], m[2], m[3], cid(c))
        p = self.found / (name + '.bfx')
        if p.exists(): return
        p.write_text(core.to_kernel(c))
        (self.found / (name + '.circ.txt')).write_text(core.write_ncff(c, MODEL))
        r = subprocess.run([sys.executable, str(PKG / 'campaigns' / 'aes_check.py'), str(p), '--json',
                            str(self.found / (name + '.check.json'))], capture_output=True, text=True)
        side = {'goal': gname, 'metrics': m, 'origin': origin, 'worker': self.a.name, 'seed': self.a.seed,
                'driver': 'strategies/T1/t1run.py', 'code_version': self.ver, 'time_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'aes_check_rc': r.returncode, 'aes_check_out': r.stdout[-2000:]}
        (self.found / (name + '.json')).write_text(json.dumps(side, indent=1, default=str))
        self.emit({'event': 'FOUND', 'goal': gname, 'm': m, 'file': str(p), 'aes_check_rc': r.returncode})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--goal', required=True, choices=list(GOALS))
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--hours', type=float, default=1.0)
    ap.add_argument('--data', required=True)
    ap.add_argument('--name', required=True)
    ap.add_argument('--ops', default='pullD,polish,deep,osc,trb,join,skel,pullA')
    ap.add_argument('--vary', type=int, default=1)
    ap.add_argument('--no-hub', action='store_true', help='v3.2: no hub archive starts (pool = --extra dirs + shared)')
    ap.add_argument('--admax', type=int, default=5); ap.add_argument('--gslack', type=int, default=12)
    ap.add_argument('--gdslack', type=int, default=10)
    ap.add_argument('--deep-sec', type=float, default=0, help='v3.3: fixed seconds for op deep (0: 240/360/480)')
    ap.add_argument('--shared', default='shared', help='v3.2: name of the shared dir under DATA')
    ap.add_argument('--extra', action='append', help='extra start dirs (.bfx), scanned like shared/')
    a = ap.parse_args()
    Worker(a).run()


if __name__ == '__main__':
    main()
