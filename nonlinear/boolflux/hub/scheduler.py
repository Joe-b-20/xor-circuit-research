#!/usr/bin/env python3
"""Hub scheduler: one shared archive, operator jobs chosen by a bandit on frontier gain per CPU second.

    python3 nonlinear/boolflux/hub/scheduler.py --dir CAMPAIGN --cpus 4,5,6,7 --hours H [--seed-list FILES]
        [--ops polish,pull,join,trb] [--seconds polish=90,pull=90,join=60,trb=30] [--eps 0.25] [--seed 1]

Loop: for every free CPU choose an operator (epsilon-greedy on the recent gain / CPU-s of each
operator, epsilon = uniform floor) and a target (a Pareto-front circuit, fewest attempts by that
operator first, ties random), run op_<name>.py pinned to that CPU, then verify and admit its
candidates (archive.Archive.admit: two verifiers, cell rule).  Gain of an admission
(archive.Archive.gain): 8 if it lowers A at no worse other coordinates, 4 for AD, 2 for G, 1 for GD
(lexicographic research priorities), 0.05 for a better circuit of its (A, AD, GD) cell that is
dominated elsewhere.  Every job: DIR/runs/<run_id>.json (code version, seed, settings, parents,
timing, outcome); DIR/stats.jsonl one line per job; DIR/front.json every 5 minutes.
"""
from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
import time
from pathlib import Path

HUBDIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HUBDIR.parents[1]))
from boolflux.hub.common import load, code_version, metrics   # noqa: E402
from boolflux.hub.archive import Archive, GEN_SLACK   # noqa: E402
from boolflux.hub.funcbank import FuncBank   # noqa: E402
from boolflux.hub.ops import kernel_bin   # noqa: E402

DEFAULT_SECONDS = {'polish': 90, 'pull': 90, 'join': 60, 'trb': 30, 'osc': 90, 'gen_inv3': 60,
                   'gen_bottom': 60, 'gen_skel': 60, 'linres': 30, 'gen_joinplus': 90}
# operator name -> script (common CLI); track F operators live in hub/ops/
SCRIPTS = {'polish': HUBDIR / 'op_polish.py', 'pull': HUBDIR / 'op_pull.py', 'join': HUBDIR / 'op_join.py',
           'trb': HUBDIR / 'op_trb.py', 'osc': HUBDIR / 'ops' / 'op_osc.py', 'gen_inv3': HUBDIR / 'ops' / 'gen_inv3.py',
           'gen_bottom': HUBDIR / 'ops' / 'gen_bottom.py', 'gen_skel': HUBDIR / 'ops' / 'gen_skel.py',
           'linres': HUBDIR / 'ops' / 'op_linres.py', 'gen_joinplus': HUBDIR / 'ops' / 'gen_joinplus.py'}
WINDOW = 40
GENERATORS = {'gen_skel', 'gen_joinplus', 'gen_inv3', 'gen_bottom'}   # admitted with the nursery slack


def acls(A):
    return 'A<=31' if A <= 31 else ('A32-35' if A <= 35 else 'A>=36')


class Scheduler:
    def __init__(self, args):
        self.args = args; self.dir = Path(args.dir); self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / 'runs').mkdir(exist_ok=True); (self.dir / 'jobs').mkdir(exist_ok=True)
        self.ar = Archive(self.dir); self.fb = FuncBank(self.dir)
        self.rng = random.Random(args.seed)
        self.ops = args.ops.split(',')
        self.secs = dict(DEFAULT_SECONDS)
        for kv in (args.seconds or '').split(','):
            if kv: k, v = kv.split('='); self.secs[k] = float(v)
        self.hist = {o: [] for o in self.ops}            # recent (cpu_s, gain)
        self.attempts = {}                                 # (op, id) -> n
        self.version = code_version()
        self.nrun = len(list((self.dir / 'runs').glob('*.json')))
        kernel_bin(self.dir)
        self.ctl_mtime = None; self.ad3_share = 0.0; self.ingest_globs = []; self.ingested = set(); self.last_ingest = 0

    # ---- hot control: DIR/control.json  {"ops": [...], "seconds": {...}, "eps": x, "near": x, "ad3_share": x,
    #      "ingest": [glob, ...], "scripts": {name: path}, "generators": [name, ...]}; every change is logged as an event ---------------------------------------
    def control(self):
        f = self.dir / 'control.json'
        if f.exists() and f.stat().st_mtime != self.ctl_mtime:
            self.ctl_mtime = f.stat().st_mtime
            try:
                c = json.loads(f.read_text())
            except Exception as e:
                self.log(ev='control-error', error=repr(e)); return
            # new operators can join a running campaign: {"scripts": {"name": "/path/op.py"}, "generators": [...]}
            for name, path in c.get('scripts', {}).items():
                sp = Path(path).expanduser()
                if sp.exists():
                    SCRIPTS[name] = sp; self.secs.setdefault(name, 60.0)
                else:
                    self.log(ev='control-error', error='script missing %s' % sp)
            for g in c.get('generators', []):
                GENERATORS.add(g)
            if 'ops' in c:
                bad = [o for o in c['ops'] if o not in SCRIPTS]
                if bad: self.log(ev='control-error', error='unknown ops %s' % bad); return
                self.ops = list(c['ops'])
                for o in self.ops: self.hist.setdefault(o, [])
            self.secs.update({k: float(v) for k, v in c.get('seconds', {}).items()})
            if 'eps' in c: self.args.eps = float(c['eps'])
            if 'near' in c: self.args.near = float(c['near'])
            if 'nursery' in c: self.args.nursery = float(c['nursery'])
            self.ad3_share = float(c.get('ad3_share', self.ad3_share))
            if 'cpus' in c and hasattr(self, 'free'):          # add CPUs (never removes running ones)
                add = [int(x) for x in c['cpus'] if int(x) not in self.cpus]
                self.cpus += add; self.free += add
            self.ingest_globs = c.get('ingest', self.ingest_globs)
            self.log(ev='control', control=c, ops=self.ops, secs=self.secs, eps=self.args.eps, near=self.args.near,
                     ad3_share=self.ad3_share)
            self.last_ingest = 0
        if self.ingest_globs and time.time() - self.last_ingest > 1800:
            self.last_ingest = time.time(); self.ingest()

    def ingest(self):
        import glob
        n = 0; seen = 0
        for g in self.ingest_globs:
            for f in sorted(glob.glob(str(Path(g).expanduser()))):
                key = (f, Path(f).stat().st_mtime)
                if key in self.ingested: continue
                self.ingested.add(key); seen += 1
                try:
                    c = load(f)
                except Exception:
                    continue
                st, r, gn = self.ar.admit(c, operator='ingest', settings={'file': f}, code_version=self.version, force_keep=True)
                if st == 'admitted':
                    n += 1; self.fb.add_circuit(c, r['id'])
                    self.log(ev='ingest', file=f, id=r['id'], m=metrics(c), gain=gn)
        self.log(ev='ingested', files=seen, admitted=n)

    def log(self, **kw):
        kw['ts'] = round(time.time(), 2)
        with open(self.dir / 'events.jsonl', 'a') as f: f.write(json.dumps(kw, default=str) + '\n')

    # ---- seeding ----------------------------------------------------------------------------
    def seed(self, files):
        n = 0; bad = 0
        for f in files:
            try:
                c = load(f)
            except Exception:
                bad += 1; continue
            st, r, g = self.ar.admit(c, operator='seed', settings={'file': str(f)}, code_version=self.version, force_keep=True)
            if st == 'admitted':
                n += 1; self.fb.add_circuit(c, r['id'])
            elif not st.startswith(('duplicate', 'not-better')):
                bad += 1; self.log(ev='seed-reject', file=str(f), status=st)
        self.fb.save()
        self.log(ev='seeded', admitted=n, rejected=bad, cells=len(self.ar.cells), front=len(self.ar.front()))
        return n

    # ---- choice -----------------------------------------------------------------------------
    def score(self, op):
        h = self.hist[op][-WINDOW:]
        return (sum(g for c, g in h) + 0.5) / (sum(c for c, g in h) + 120.0)

    def choose_op(self):
        if self.rng.random() < self.args.eps: return self.rng.choice(self.ops), 'explore'
        return max(self.ops, key=lambda o: (self.score(o), self.rng.random())), 'exploit'

    def near_ids(self):
        """cell minima that are not on the front but within NEAR_GAP gates of a dominating front point"""
        fr = self.ar.front(); out = []
        for k, ids in self.ar.cells.items():
            if not ids: continue
            m = (k[0], k[1], self.ar.rec[ids[0]]['G'], k[2])
            doms = [q[2] for q in fr if q != m and all(a <= b for a, b in zip(q, m))]
            if doms and m[2] - min(doms) <= self.args.near_gap: out.append(ids[0])
        return out

    def nursery_ids(self, op):
        """cell minima admitted by a generator, not on the front, polished < 3 times by op (newest first)"""
        fr = set(self.ar.front_ids()); out = []
        for k, ids in self.ar.cells.items():
            if not ids: continue
            r = self.ar.rec[ids[0]]
            if (r['operator'] in GENERATORS or (r.get('operator_settings') or {}).get('nursery')) and ids[0] not in fr and self.attempts.get((op, ids[0]), 0) < 3:
                out.append((r['t_admit'], ids[0]))
        return [i for t, i in sorted(out, reverse=True)]

    def choose_target(self, op, busy):
        pool = self.ar.front_ids()
        if op in ('polish', 'pull', 'trb') and self.args.nursery > 0 and self.rng.random() < self.args.nursery:
            nu = [i for i in self.nursery_ids(op) if i not in busy]
            if nu: return nu[0]
        if self.ad3_share > 0 and self.rng.random() < self.ad3_share:
            p3 = [i for i in pool if self.ar.rec[i]['AD'] <= 3]
            if p3: pool = p3
        if op in ('polish', 'pull', 'trb') and self.args.near > 0 and self.rng.random() < self.args.near:
            pool = self.near_ids() or pool
        ids = [i for i in pool if i not in busy]
        if not ids: return None
        self.rng.shuffle(ids)
        return min(ids, key=lambda i: self.attempts.get((op, i), 0))

    # ---- jobs -------------------------------------------------------------------------------
    def launch(self, cpu, busy):
        op, why = self.choose_op()
        tid = self.choose_target(op, busy)
        if tid is None: return None
        self.attempts[(op, tid)] = self.attempts.get((op, tid), 0) + 1
        self.nrun += 1
        run_id = 'r%05d-%s' % (self.nrun, op)
        jd = self.dir / 'jobs' / run_id
        seed = self.rng.randrange(1, 1 << 30)
        cmd = ['taskset', '-c', str(cpu), sys.executable, str(SCRIPTS[op]), '--archive', str(self.dir),
               '--in', tid, '--seed', str(seed), '--seconds', str(self.secs[op]), '--out', str(jd)]
        lf = open(self.dir / 'jobs' / (run_id + '.log'), 'w')
        p = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT)
        return {'p': p, 'lf': lf, 'op': op, 'why': why, 'target': tid, 'run_id': run_id, 'jd': jd, 'seed': seed,
                'cpu': cpu, 't0': time.time(), 'cmd': cmd}

    def finish(self, job):
        job['lf'].close()
        jd = job['jd']; tm = self.ar.rec[job['target']]
        rec = json.loads((jd / 'record.json').read_text()) if (jd / 'record.json').exists() else {}
        outcome = []; gain = 0.0
        joins = (rec.get('info') or {}).get('joins') or []
        nurs = job['op'] in GENERATORS or tm['operator'] in GENERATORS or bool((tm.get('operator_settings') or {}).get('nursery'))
        for k, f in enumerate(sorted(jd.glob('cand-*.bfx'))):
            from boolflux import core
            c = core.from_kernel(f.read_text(), f.stem)
            parents = [job['target']]
            settings = {'nursery': nurs, 'caps': rec.get('caps'), 'objective': rec.get('objective'), 'seconds': rec.get('seconds')}
            if job['op'] in ('join', 'gen_joinplus') and k < len(joins):
                parents = [joins[k]['front'], joins[k]['back']]; settings.update(joins[k])
            elif job['op'] in ('polish', 'pull'):
                settings.update({k2: (rec.get('info') or {}).get(k2) for k2 in ('caps', 'lowered', 't_last_improvement')})
            st, r, g = self.ar.admit(c, parents=parents, operator=job['op'], settings=settings, seed=job['seed'],
                                     run_id=job['run_id'], code_version=rec.get('code_version'), cpu_s=rec.get('cpu_s'),
                                     wall_s=rec.get('wall_s'), slack=GEN_SLACK if nurs else None)
            outcome.append({'cand': f.name, 'metrics': metrics(c), 'status': st, 'id': r['id'] if r else None, 'gain': g})
            if st == 'admitted':
                gain += g; self.fb.add_circuit(c, r['id'])
                self.log(ev='admit', run_id=job['run_id'], op=job['op'], id=r['id'], m=metrics(c), gain=g, parents=parents)
        if self.fb.dirty >= 10: self.fb.save()
        cpu = rec.get('cpu_s') or (time.time() - job['t0'])
        self.hist[job['op']].append((cpu, gain))
        run = {'run_id': job['run_id'], 'operator': job['op'], 'choice': job['why'], 'target': job['target'],
               'target_metrics': [tm['A'], tm['AD'], tm['G'], tm['GD']], 'target_class': acls(tm['A']),
               'seed': job['seed'], 'cpu': job['cpu'], 'command': job['cmd'], 'returncode': job['p'].returncode,
               'code_version': rec.get('code_version', self.version), 'scheduler_version': self.version,
               'settings': {k: rec.get(k) for k in ('caps', 'objective', 'seconds')}, 'op_info': rec.get('info'),
               'parents': [job['target']], 'wall_s': round(time.time() - job['t0'], 2), 'cpu_s': cpu,
               'candidates': len(outcome), 'admitted': sum(1 for o in outcome if o['status'] == 'admitted'),
               'gain': gain, 'outcome': outcome}
        (self.dir / 'runs' / (job['run_id'] + '.json')).write_text(json.dumps(run, indent=1, default=str))
        with open(self.dir / 'stats.jsonl', 'a') as f:
            f.write(json.dumps({'run_id': job['run_id'], 'op': job['op'], 'cls': acls(tm['A']), 'cpu_s': cpu,
                                'admitted': run['admitted'], 'gain': gain, 'ts': round(time.time(), 1)}) + '\n')

    def write_front(self):
        fr = []
        for i in self.ar.front_ids():
            r = self.ar.rec[i]
            fr.append({'id': i, 'm': [r['A'], r['AD'], r['G'], r['GD']], 'operator': r['operator'], 'parents': r['parents'],
                       'pub_new': r.get('pub_new'), 'run_id': r.get('run_id')})
        fr.sort(key=lambda d: d['m'])
        (self.dir / 'front.json').write_text(json.dumps(fr, indent=0))

    def run(self):
        end = time.time() + self.args.hours * 3600
        cpus = [int(x) for x in self.args.cpus.split(',')]
        self.cpus = list(cpus); self.free = free = list(cpus); running = []; last_front = 0; last_ctl = 0
        self.log(ev='start', cpus=cpus, ops=self.ops, seconds=self.secs, eps=self.args.eps, version=self.version,
                 archive=len(self.ar.rec), cells=len(self.ar.cells), front=len(self.ar.front()))
        while running or time.time() < end:
            for j in list(running):
                if j['p'].poll() is None: continue
                running.remove(j); free.append(j['cpu'])
                try:
                    self.finish(j)
                except Exception as e:     # never lose the loop; the job dir stays as evidence
                    self.log(ev='finish-error', run_id=j['run_id'], error=repr(e))
            while free and time.time() < end:
                j = self.launch(free[0], {x['target'] for x in running})
                if j is None: break
                free.pop(0); running.append(j)
            if time.time() - last_ctl > 30:
                self.control(); last_ctl = time.time()
            if time.time() - last_front > 300:
                self.write_front(); last_front = time.time()
            time.sleep(0.5)
        self.fb.save(); self.write_front()
        self.log(ev='end', archive=len(self.ar.rec), cells=len(self.ar.cells), front=len(self.ar.front()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True); ap.add_argument('--cpus', required=True)
    ap.add_argument('--hours', type=float, default=1.0); ap.add_argument('--seed-list')
    ap.add_argument('--ops', default='polish,pull,join,trb'); ap.add_argument('--seconds')
    ap.add_argument('--eps', type=float, default=0.25); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--seed-only', action='store_true')
    ap.add_argument('--near', type=float, default=0.0,
                    help='probability that polish/pull/trb target a near-front cell minimum instead of a front circuit')
    ap.add_argument('--near-gap', type=int, default=3)
    ap.add_argument('--nursery', type=float, default=0.0, help='probability that polish/pull/trb target a generator-made cell minimum')
    args = ap.parse_args()
    s = Scheduler(args)
    if args.seed_list:
        s.seed(Path(args.seed_list).read_text().split())
    if not args.seed_only:
        s.run()


if __name__ == '__main__':
    main()
