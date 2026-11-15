#!/usr/bin/env python3
"""P1 worker for targets T01 (A<=28, AD<=4, ref 132/22) and T03 (A<=28, AD<=5, ref 128/20).

    python3 p1run.py --target T01 --seed 1 --hours 4 --data DIR --name w10 --starts starts.json \
        [--ops deep,pullD,osc,trb,join,skel,polish,gfree] [--kbin PATH]

Derived from strategies/T1/t1run.py v3.3 with the campaign's hard limits enforced everywhere:
  * every kernel call has cap.a 28 and cap.ad = the target's AD (never switched off); the kernel never
    leaves a feasible state for an infeasible one, and every start is inside the limits, so every
    kernel state is inside them;
  * gen_skel kicks, trb rebuilds and joins are kept only if A <= 28 and AD <= cap before anything
    else is done with them (no repair of out-of-limit states);
  * the pool admits only A <= 28, AD <= cap.
One process = one loop on one CPU.  Pool = survey rows (starts.json, legal starts) + DATA/shared/
(all P1 workers' admitted circuits, with lineage).  Each job: pick a start (weight exp(-excess/2) /
(1 + tries)), an operator (bandit on improvements per CPU-min with a floor), run it, verify every
output (hub common.verify), admit.  Every admitted circuit that no archived or pinned-NIST circuit
dominates or equals is written to DATA/found/ (.circ.txt + .json sidecar per BRIEF) and checked with
campaigns/aes_check.py.  Lineage: root start file + sha256 and the chain of operator steps with
their kernel seeds, caps, seconds, T0, max_excess.
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
sys.path.insert(0, str(PKG / 'strategies' / 'T4')); sys.path.insert(0, str(PKG / 'strategies' / 'P1'))
import p1synth as P1S                                    # noqa: E402
import pswap as PSW                                      # noqa: E402
from boolflux import skeleton as SK, targets as TG       # noqa: E402
TAB = tuple(TG.aes_sbox())
# 18:15: repair_keep 1 in every kernel call (review5 S2): a GD repair may no longer raise the A or AD excess,
# so kernel-internal states stay inside the hard limits too (before: outputs were checked, states were not)
HO.KDEFAULTS['repair_keep'] = 1

TARGETS = {
    # ref tuple, main GD cap, goal points (G, GD) used for start weighting, alternative GD caps
    'T01': {'ref': (28, 4, 132, 22), 'gd': 22, 'goals': [(130, 22), (131, 21), (132, 19), (129, 24)], 'alt': [21, 23, 24]},
    'T03': {'ref': (28, 5, 128, 20), 'gd': 20, 'goals': [(127, 20), (128, 19)], 'alt': [19, 21]},
}
BASEW = {'pswap': 0.2, 'skres': 0.2, 'deep': 0.22, 'pullD': 0.3, 'osc': 0.12, 'skel': 0.12, 'trb': 0.08, 'join': 0.08, 'polish': 0.05, 'gfree': 0.05}
OBJ = 'a,cost,gd'
STUDY_REF_JSON = Path('/home/joebachir20/xs-campaigns/2026-11-15-targets/P1/reftuples.json')


def cid(c):
    return hashlib.sha1(core.to_kernel(c).encode()).hexdigest()[:12]


def sha256f(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def git_sha():
    r = subprocess.run(['git', '-C', str(PKG.parents[1]), 'rev-parse', 'HEAD'], capture_output=True, text=True)
    return r.stdout.strip()


class Worker:
    def __init__(self, a):
        self.a = a; self.T = TARGETS[a.target]
        self.A, self.AD = self.T['ref'][0], self.T['ref'][1]
        self.rng = random.Random(a.seed)
        self.data = Path(a.data).resolve(); self.shared = self.data / 'shared'; self.found = self.data / 'found'
        for d in (self.shared, self.found): d.mkdir(parents=True, exist_ok=True)
        self.job = self.data / 'scratch' / a.name; self.job.mkdir(parents=True, exist_ok=True)
        self.log = open(self.data / 'runs' / (a.name + '.jobs.jsonl'), 'a')
        self.pool = {}      # id -> (circuit, metrics, origin, lineage)
        self.seen_shared = set()
        self.ops = a.ops.split(',')
        self.st = {o: [0, 0.0, 0] for o in self.ops}
        self.ver = code_version(); self.git = git_sha()
        self.kbin = HO.kernel_bin(str(self.data)); self.kbin_sha = sha256f(self.kbin)
        self.self_sha = sha256f(__file__)
        self.t0 = time.time(); self.ks = []
        self.orig = set()
        self.tries = {}
        self.base = dict(BASEW)
        self.follow = None
        self.ref = set(tuple(x) for x in json.loads(Path(a.ref).read_text()))
        self.load_starts()
        self.scan_shared()
        self.harvest('startup')
        signal.signal(signal.SIGTERM, self.on_term)
        self.emit({'event': 'start', 'argv': sys.argv, 'pool': len(self.pool), 'front': sorted(self.front()),
                   'kbin': str(self.kbin), 'kbin_sha256': self.kbin_sha, 'git': self.git, 'code_version': self.ver})

    # ---- limits ------------------------------------------------------------------------------
    def legal(self, m):
        return m[0] <= self.A and m[1] <= self.AD

    def caps(self, gd):
        return {'A': self.A, 'AD': self.AD, 'GD': gd}

    def excess(self, m):
        return min(max(0, m[2] - g) + max(0, m[3] - d) for g, d in self.T['goals'])

    def in_scope(self, m):
        return self.legal(m) and m[2] <= self.T['ref'][2] + self.a.gslack and m[3] <= self.T['gd'] + self.a.gdslack

    # ---- harvest ---------------------------------------------------------------------------
    def harvest(self, why):
        got = []
        for d in sorted(self.job.iterdir()) if self.job.exists() else []:
            b = d / 'best.bfx'
            if not b.exists(): continue
            try: c = core.from_kernel(b.read_text(), 'h')
            except Exception: continue
            lin = getattr(self, 'cur_lineage', None)
            r = self.admit(c, 'harvest-%s:%s' % (why, d.name), lin)
            got.append((metrics(c), r))
        self.emit({'event': 'harvest', 'why': why, 'got': got})

    def on_term(self, signum, frame):
        try: self.harvest('sigterm')
        finally: os._exit(0)

    # ---- saving -----------------------------------------------------------------------------
    def classify(self, m):
        A, AD, G, GD = self.T['ref']
        if not self.legal(m): return None
        if m[2] <= G and m[3] <= GD and (m[2] < G or m[3] < GD): return 'strict'
        if self.a.target == 'T01' and GD < m[3] <= 24 and m[2] <= G - 3: return 'tradeoff'
        return 'other'

    def save_front(self, c, m, origin, lineage):
        """legal circuit not dominated by (or equal to) any archived / pinned NIST tuple -> found/ + aes_check"""
        if not self.legal(m): return
        lineage = lineage or {'root': 'unknown (harvested scratch output of an earlier run)', 'root_sha256': None, 'chain': []}
        if any(all(a <= b for a, b in zip(q, m)) for q in self.ref): return
        cls = self.classify(m)
        name = 'P1-%s-a%d-ad%d-g%d-gd%d-%s' % ((self.a.target,) + m + (cid(c),))
        p = self.found / (name + '.circ.txt')
        if p.exists(): return
        p.write_text(core.write_ncff(c, MODEL, comments=['P1 %s %s seed %d' % (self.a.target, self.a.name, self.a.seed)]))
        r = subprocess.run([sys.executable, str(PKG / 'campaigns' / 'aes_check.py'), str(p), '--json',
                            str(self.found / (name + '.check.json'))], capture_output=True, text=True)
        okline = [ln for ln in r.stdout.splitlines() if 'OK' in ln][:1]
        side = {'target': self.a.target, 'class_vs_ref': cls, 'A': m[0], 'AD': m[1], 'G': m[2], 'GD': m[3],
                'start': {'path': lineage['root'], 'sha256': lineage['root_sha256'], 'tuple': lineage.get('root_m')},
                'method': {'engine': 'strategies/P1/p1run.py (hub kernel + hub join/trb/gen_skel)',
                           'operator_chain': lineage['chain'], 'objective': OBJ,
                           'hard_caps': {'A': self.A, 'AD': self.AD}},
                'command': ' '.join([sys.executable] + [str(Path(sys.argv[0]).resolve())] + sys.argv[1:]),
                'seed': self.a.seed, 'worker': self.a.name, 'origin': origin,
                'elapsed_s': round(time.time() - self.t0, 1),
                'code': {'git': self.git, 'code_version': self.ver, 'p1run_sha256': self.self_sha,
                         'kernel_bin': str(self.kbin), 'kernel_sha256': self.kbin_sha},
                'aes_check': okline[0] if okline else None, 'aes_check_rc': r.returncode,
                'aes_check_out': r.stdout[-3000:],
                'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
        (self.found / (name + '.json')).write_text(json.dumps(side, indent=1, default=str))
        self.emit({'event': 'FRONT', 'm': m, 'class': cls, 'file': str(p), 'aes_check_rc': r.returncode})

    # ---- pool ------------------------------------------------------------------------------
    def front(self):
        pts = {v[1] for v in self.pool.values()}
        return [p for p in pts if not any(q != p and all(a <= b for a, b in zip(q, p)) for q in pts)]

    def admit(self, c, origin, lineage, verified=False):
        m = metrics(c)
        if not self.in_scope(m): return None
        i = cid(c)
        if i in self.pool: return None
        same = [k for k, v in self.pool.items() if v[1] == m]
        pts = {v[1] for v in self.pool.values()}
        dominated = any(all(a <= b for a, b in zip(q, m)) for q in pts)
        strict_dom = any(all(a <= b for a, b in zip(q, m)) and q != m for q in pts)
        if len(same) >= 8: return None
        if not verified:
            ok, info = verify(c)
            if not ok:
                self.emit({'event': 'verify_fail', 'origin': origin, 'm': m, 'info': info}); return None
        if not same: self.orig.add(i)
        self.pool[i] = (c, m, origin, lineage)
        p = self.shared / (i + '.bfx')
        if not p.exists():
            tmp = self.shared / ('.%s.%s.tmp' % (i, self.a.name)); tmp.write_text(core.to_kernel(c)); os.replace(tmp, p)
            (self.shared / (i + '.json')).write_text(json.dumps({'id': i, 'm': m, 'origin': origin, 'worker': self.a.name,
                                                                  'target': self.a.target, 'lineage': lineage, 't': time.time(),
                                                                  'code_version': self.ver}, default=str))
        self.seen_shared.add(i)
        self.save_front(c, m, origin, lineage)
        return 'new_front' if not dominated else ('pool' if not strict_dom else 'pool_dom')

    def load_starts(self):
        rows = json.loads(Path(self.a.starts).read_text())
        n = 0
        for r in rows:
            m = (r['A'], r['AD'], r['G'], r['GD'])
            if not self.in_scope(m): continue
            t = Path(r['path']).read_text()
            c = core.from_kernel(t) if r['path'].endswith('.bfx') else core.read_ncff(t)
            if metrics(c) != m: continue
            i = cid(c)
            lin = {'root': r['path'], 'root_sha256': r['sha256'], 'root_m': m, 'chain': []}
            self.pool[i] = (c, m, 'start:' + r['path'], lin); self.orig.add(i); n += 1
        self.emit({'event': 'load_starts', 'pool': n})

    def scan_shared(self):
        k = 0
        for p in self.shared.glob('*.bfx'):
            i = p.stem
            if i in self.seen_shared: continue
            self.seen_shared.add(i)
            try:
                c = core.from_kernel(p.read_text(), i)
                meta = json.loads((self.shared / (i + '.json')).read_text())
            except Exception: continue
            m = metrics(c)
            if self.in_scope(m) and i not in self.pool:
                self.pool[i] = (c, m, 'shared:' + i, meta.get('lineage')); k += 1
        return k

    def pick(self):
        tup = {}
        for k, v in self.pool.items(): tup.setdefault(v[1], []).append(k)
        ts = list(tup)
        w = [math.exp(-self.excess(t) / 2.0) / (1.0 + self.tries.get(t, 0)) for t in ts]
        t = self.rng.choices(ts, weights=w)[0]
        ks = tup[t]
        k = self.rng.choices(ks, weights=[3.0 if x in self.orig else 1.0 for x in ks])[0]
        self.tries[t] = self.tries.get(t, 0) + 1
        return k, self.pool[k]

    # ---- operators -------------------------------------------------------------------------
    def kernel(self, c, caps, sec, tag):
        assert caps['A'] == self.A and caps['AD'] is not None and caps['AD'] <= self.AD
        assert self.legal(metrics(c))
        d = self.job / tag; d.mkdir(exist_ok=True)
        HO.KDEFAULTS['T0'] = self.rng.choice([0.3, 0.6, 0.6, 1.0])
        HO.KDEFAULTS['max_excess'] = self.rng.choice([4, 8, 8, 12])
        seed = self.rng.randrange(1 << 30)
        self.ks.append({'step': tag, 'caps': dict(caps), 'seconds': sec, 'seed': seed, 'T0': HO.KDEFAULTS['T0'],
                        'max_excess': HO.KDEFAULTS['max_excess']})
        cs, info = HO._kernel(c, caps, OBJ, seed, sec, d, str(self.data))
        x = cs[0] if cs else None
        if x is not None:
            self.ks[-1]['out'] = metrics(x)
            if not self.legal(metrics(x)):
                self.emit({'event': 'ILLEGAL_KERNEL_OUTPUT', 'm': metrics(x)}); return None
        return x

    def gd_main(self):
        r = self.rng.random()
        if r < 0.6: return self.T['gd']
        return self.rng.choice(self.T['alt'])

    def op_polish(self, c):
        x = self.kernel(c, self.caps(max(self.gd_main(), 0)), self.rng.choice([60, 90, 120]), 'p')
        return [x] if x else []

    def op_deep(self, c):
        m = metrics(c)
        gd = self.gd_main()
        if m[3] > gd + 3 and self.rng.random() < 0.5: gd = m[3] - 1     # far starts: walk down the GD axis
        x = self.kernel(c, self.caps(gd), self.a.deep_sec or self.rng.choice([240, 360, 480, 600]), 'dp')
        return [x] if x else []

    def op_pullD(self, c):
        """GD cap = start GD - 1 (p .6) / - 2 / - 3, A and AD caps kept; then a polish at the result's GD"""
        m = metrics(c)
        gd = m[3] - self.rng.choice([1, 1, 1, 2, 2, 3])
        x = self.kernel(c, self.caps(gd), self.rng.choice([90, 120, 180, 240]), 'pd')
        out = [x] if x else []
        if x and metrics(x)[3] <= gd:
            x2 = self.kernel(x, self.caps(metrics(x)[3]), self.rng.choice([60, 120]), 'pd2')
            if x2: out.append(x2)
        return out

    def op_gfree(self, c):
        x = self.kernel(c, self.caps(None), 120, 'gf')
        out = [x] if x else []
        if x:
            x2 = self.kernel(x, self.caps(max(metrics(x)[3] - 1, self.T['gd'])), 90, 'gf2')
            if x2: out.append(x2)
        return out

    def op_osc(self, c):
        m = metrics(c)
        base = min(m[3], self.T['gd'] + 2)
        r = self.rng.choice([1, 1, 2, 3])
        x1 = self.kernel(c, self.caps(base + r), self.rng.choice([30, 60]), 'o1')
        out = [x1] if x1 else []
        tgt = self.rng.choice([base, base, self.T['gd']])
        x2 = self.kernel(x1 or c, self.caps(tgt), self.rng.choice([60, 120]), 'o2')
        if x2: out.append(x2)
        return out

    def op_trb(self, c):
        t0 = time.time(); best = []; cur = c; sec = self.rng.choice([10, 20])
        m0 = metrics(c)
        while time.time() - t0 < sec:
            D = min(m0[3], self.T['gd']) - self.rng.choice([0, 0, 0, 1])
            kind = self.rng.choice(['bottom', 'top', 'mid', 'random', 'random'])
            try: nc, info = trb_impl.rebuild(cur, D, kind, self.rng)
            except Exception: continue
            if nc is cur: continue
            if self.legal(metrics(nc)):
                best.append(nc)
                if self.rng.random() < 0.5: cur = nc
        best.sort(key=lambda x: (self.excess(metrics(x)), metrics(x)))
        out = best[:3]
        if out:
            self.ks.append({'step': 'trb', 'note': 'trb_impl.rebuild chain (rng from worker seed)'})
            x = self.kernel(out[0], self.caps(metrics(out[0])[3]), 60, 't')
            if x: out.append(x)
        return out

    def op_join(self, c):
        X = J.Prepared(c, 'x')
        partners = list(self.pool.values())
        self.rng.shuffle(partners)
        partners = partners[:self.rng.choice([40, 80])]
        res = []; t0 = time.time()
        for pc, pm, po, pl in partners:
            if time.time() - t0 > 40: break
            P = J.Prepared(pc, 'p')
            for F, B in ((X, P), (P, X)):
                for jc, LX, LY, nint in J.join_all(F, B):
                    m = metrics(jc)
                    if self.legal(m) and self.excess(m) <= 8:
                        res.append((self.excess(m), m, jc, po))
        res.sort(key=lambda r: (r[0], r[1]))
        out = []; seen = set()
        for e, m, jc, po in res:
            k = cid(jc)
            if k in seen: continue
            seen.add(k); out.append(jc)
            if len(out) >= 6: break
        if out:
            self.ks.append({'step': 'join', 'note': 'hub join_all with pool partners (best by excess)', 'partner_origin': res[0][3]})
            x = self.kernel(out[0], self.caps(max(metrics(out[0])[3], self.T['gd'])), 60, 'j')
            if x: out.append(x)
        return out

    def op_skel(self, c):
        d = self.job / 'sk'; d.mkdir(exist_ok=True)
        out = []
        for _ in range(2):
            ks = self.rng.randrange(1 << 30); nacc = self.rng.choice([1, 1, 2, 3])
            kc = GS.kick(c, d, ks, nacc, str(self.data))
            if kc is None or not self.legal(metrics(kc)): continue
            self.ks.append({'step': 'skel_kick', 'seed': ks, 'nacc': nacc, 'out': metrics(kc)})
            # L1: gen_skel products are far from locally optimal and still improve late -> longer polishes
            x = self.kernel(kc, self.caps(None), self.rng.choice([10, 30]), 'sk1')
            if x is None: continue
            x2 = self.kernel(x, self.caps(max(self.T['gd'], metrics(x)[3] - self.rng.choice([2, 4, 6]))),
                             self.rng.choice([120, 240]), 'sk2')
            out += [x] + ([x2] if x2 else [])
        return out

    def op_skres(self, c):
        """keep the AND skeleton (A, AD unchanged), rebuild all XOR layers depth-first (p1synth timing-driven
        Paar or T4 reqsynth) for a cap near the target GD, then two kernel runs under the hard caps"""
        m0 = metrics(c)
        D = self.rng.choice([self.T['gd'], self.T['gd'], self.T['gd'] - 1, self.T['gd'] - 2])
        how = self.rng.choice(['paar', 'paar', 'req'])
        ss = self.rng.randrange(1 << 30)
        if how == 'paar':
            r = P1S.rebuild(c, D, ss)
        else:
            import reqsynth
            sk = SK.extract(c)
            r = reqsynth.synth({'ands': sk['ands'], 'outputs': sk['outputs']}, cap=D)
        if r is None or tuple(r.value_table()) != TAB: return []
        mr = metrics(r)
        if not self.legal(mr): return []
        self.ks.append({'step': 'skres', 'synth': how, 'cap': D, 'seed': ss, 'out': mr})
        gd = max(self.T['gd'], mr[3]) if self.rng.random() < 0.7 else max(self.T['gd'] - 1, mr[3])
        x = self.kernel(r, self.caps(gd), self.rng.choice([120, 180]), 'sr1')
        if x is None: return []
        x2 = self.kernel(x, self.caps(gd), self.rng.choice([180, 300]), 'sr2')
        return [x] + ([x2] if x2 else [])

    def op_pswap(self, c):
        """last-layer basis swap of 1-3 final products (pswap.py: z -> AND(p, p^q) etc. with the linear correction
        folded into the bottom, bottom region re-synthesised by trb with p .5), then two kernel runs at the caps"""
        k = self.rng.choice([1, 1, 2, 3]); rb = self.rng.random() < 0.5
        ks = self.rng.randrange(1 << 30)
        x0, info = PSW.kick(c, k, random.Random(ks), self.T['gd'], rebuild=rb)
        if x0 is None or tuple(x0.value_table()) != TAB or not self.legal(metrics(x0)): return []
        self.ks.append({'step': 'pswap', 'seed': ks, 'k': k, 'rebuild': rb, 'info': info, 'out': metrics(x0)})
        gd = max(self.T['gd'], min(metrics(c)[3], self.T['gd'] + 2))
        x = self.kernel(x0, self.caps(gd), self.rng.choice([90, 150]), 'ps1')
        if x is None: return []
        x2 = self.kernel(x, self.caps(self.T['gd'] if self.rng.random() < 0.7 else min(gd, metrics(x)[3])),
                         self.rng.choice([120, 240]), 'ps2')
        return [x] + ([x2] if x2 else [])

    # ---- main loop ---------------------------------------------------------------------------
    def choose_op(self):
        w = []
        for o in self.ops:
            n, cpu, imp = self.st[o]
            w.append(self.base.get(o, 0.1) * max(0.3, (imp + 1.0) / (cpu / 600.0 + 1.0)))
        return self.rng.choices(self.ops, weights=w)[0]

    def emit(self, d):
        d['t'] = round(time.time(), 1); self.log.write(json.dumps(d, default=str) + '\n'); self.log.flush()

    def run(self):
        k = 0
        while time.time() - self.t0 < self.a.hours * 3600:
            k += 1
            if k % 5 == 0: self.scan_shared()
            op = self.choose_op()
            if self.follow and self.follow in self.pool and self.rng.random() < 0.6:
                # L1: pull / deep on a circuit that a job just made is the strongest chain step
                i = self.follow; c, m, o, lin = self.pool[i]; op = self.rng.choice(['pullD', 'pullD', 'deep', 'osc'])
                op = op if op in self.ops else self.choose_op()
            else:
                i, (c, m, o, lin) = self.pick()
            self.follow = None
            lin = lin or {'root': 'shared:' + i, 'root_sha256': None, 'chain': []}
            t0 = time.time(); c0 = os.times(); self.ks = []
            step = {'op': op, 'job': k, 'worker': self.a.name, 'parent': i, 'parent_m': m, 'steps': self.ks}
            nlin = dict(lin, chain=lin['chain'] + [step])
            self.cur_lineage = nlin
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
            self.cur_lineage = None
            for x in cands:
                if x is None: continue
                mx = metrics(x)
                newtup = mx not in {v[1] for v in self.pool.values()}
                r = self.admit(x, '%s(%s)' % (op, i), nlin)
                outs.append((mx, r))
                if r and (r == 'new_front' or (newtup and self.excess(mx) <= e0 + 2)) and                         (self.follow is None or self.excess(mx) < self.excess(self.pool[self.follow][1])):
                    self.follow = cid(x)
                if r == 'new_front' or (r and r != 'pool_dom' and self.excess(mx) < e0): imp += 1
                if r and mx not in self.tries: self.tries[mx] = 0
            for d in self.job.iterdir():      # scratch outputs are consumed; keep the dir small
                b = d / 'best.bfx'
                if b.exists(): b.unlink()
            self.st[op][0] += 1; self.st[op][1] += cpu; self.st[op][2] += imp
            self.emit({'job': k, 'op': op, 'parent': i, 'pm': m, 'cpu': round(cpu, 1), 'wall': round(time.time() - t0, 1),
                       'outs': outs, 'imp': imp, 'err': err, 'kernel': self.ks})
            if k % 10 == 0:
                self.emit({'event': 'status', 'front': sorted(self.front()), 'pool': len(self.pool), 'stats': self.st})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--target', required=True, choices=list(TARGETS))
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--hours', type=float, default=1.0)
    ap.add_argument('--data', required=True)
    ap.add_argument('--name', required=True)
    ap.add_argument('--starts', required=True)
    ap.add_argument('--ops', default='pswap,skres,deep,pullD,osc,trb,join,skel,polish,gfree')
    ap.add_argument('--gslack', type=int, default=12)
    ap.add_argument('--gdslack', type=int, default=8)
    ap.add_argument('--deep-sec', type=float, default=0)
    ap.add_argument('--ref', default=str(STUDY_REF_JSON))
    a = ap.parse_args()
    Worker(a).run()


if __name__ == '__main__':
    main()
