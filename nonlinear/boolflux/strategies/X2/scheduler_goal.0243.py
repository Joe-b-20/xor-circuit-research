#!/usr/bin/env python3
"""Goal-directed hub scheduler (agent X2, 2026-11-15): the hub scheduler (scheduler.Scheduler, subclassed, not
copied) with the user's ordered goal list (hub/goals.py) driving target choice, operator choice, caps and
objective.  Archive, operators, admission (two verifiers), run records and control.json are the hub's.

    python3 nonlinear/boolflux/hub/scheduler_goal.py --dir CAMPAIGN --cpus 4,5 --hours H
        [--ops polish,pull,join,trb,osc,gen_skel] [--goal-share A=0.1,B=0.2,...] [--generic-share 0.1]
        [--found DIR] [--nursery 0.3] [... every scheduler.py option]

Per free CPU:
 1. goal: stride scheduling on CPU seconds: the active goal (share > 0, not yet met unless keep_met) with the
    smallest used_cpu / share; 'generic' (share --generic-share) runs the original bandit choice unchanged.
 2. operator: eps 0.1 uniform, else chosen with probability proportional to (goal reward + PRIOR[op]) / (CPU s + 120)
    over the last 40 jobs of that
    (goal, operator) pair; reward = goals.step_gain of the archive's best key for that goal (x5) plus, per
    admitted candidate, step_gain from the target's key to the candidate's key, plus 0.05 per new stepping
    stone.  Learned online, separately per goal.
 3. target: every archive record with scalar distance <= best + W (W = 10) or a stepping stone, nearest 40;
    a tuple (A, AD, G, GD) gets at most TUPLE_CAP[op] jobs of op per front state (polish 2, pull 3, join 1, ...;
    counted over all copies of the tuple, reset when the front changes); with probability 0.7 the nearest tuple
    with no job yet is taken (new near-goal tuples get their first job at once); otherwise sampled with weight
    exp(-(scalar - best) / T) / (1 + attempts of this (goal, op, target)), T = 3.
    (2026-11-15 02:15 changes after L1's counts, relayed by the coordinator: tuple caps, fresh first, priors,
    pull uncapped, gjoin, shares A .12 B .22 C .18 D .14 E .10 F .08 G .08 generic .08.)
 4. caps (--caps A,AD,GD) and objective per job, from the goal:
      polish, osc, gen_inv3: the goal's caps (a target outside them is repaired by the kernel);
      pull: the hub's pull unchanged (no --caps: GD by 1-3 with the AD cap dropped, AD by 1 or A by 1, relative
            to the target; L1: this is what moved A <= 29);
      gjoin (strategies/X2/op_gjoin.py): join with partners from the goal pool (env X2_GOAL), not the front;
      jump (op_polish.py): caps (A + 1, AD - 1, max(GD, goal GD)) on its own pool (A <= goal A, AD = goal AD + 1,
            G <= goal G + 15, GD <= goal GD + 6): the class jump of L1 finding 5 made deliberate;
      polish is never run on seed / ingested circuits (L1 finding 3); osc and plain join are not goal ops;
      gpull (op_polish.py with these caps): one step toward the goal: the first violated coordinate in A, AD, GD order lowered by 1 (GD by 1-2,
            never below the goal), satisfied coordinates at the goal cap, other violated ones at the target's
            value; coordinates the goal leaves free: AD at the target's value, GD free; if only G is violated,
            GD capped 1-2 below the target's GD (a stepping stone that trades back under polish);
      trb, join, gen_skel, linres, gen_joinplus: unchanged (they take no caps).
    Objective always 'a,ad,cost,gd' (the user's lexicographic order: never trade an AND for gates).
Every admission (any goal, generic too) is scored against every goal; a circuit that MEETS a goal is written
to --found (NCFF + JSON sidecar), checked with campaigns/aes_check.py, logged as event GOAL-MET and appended to
DIR/GOALS-MET.txt.  Extra files: DIR/goal_stats.jsonl (one line per job), DIR/goals.json (state, every 5 min),
runs/<run_id>.json gets 'goal', 'goal_caps', 'goal_reward', 'goal_progress'.

control.json (re-read like the original; all original keys still work), additional keys:
  "goal_share": {"A": x, ...}, "generic_share": x, "goal_ops": {"B": [ops], ...}, "goal_T": x, "goal_W": x,
  "keep_met": bool, "goal_eps": x
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

HUBDIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HUBDIR.parents[1]))
from boolflux.hub import scheduler as S                       # noqa: E402
from boolflux.hub import goals as GL                          # noqa: E402
from boolflux.hub.common import core, MODEL, metrics, atomic_write   # noqa: E402

DEFAULT_SHARE = {'A': 0.12, 'B': 0.22, 'C': 0.18, 'D': 0.14, 'E': 0.10, 'F': 0.08, 'G': 0.08}
DEFAULT_GENERIC = 0.08
CAPPED = {'polish', 'osc', 'gen_inv3'}      # pull runs as the hub's pull (L1 fact 5: GD-1, AD cap off, on originals)
OPS_A = ['pull', 'gpull', 'polish', 'gjoin', 'gen_skel']
OPS_OTHER = ['pull', 'gpull', 'jump', 'polish', 'trb', 'gjoin', 'gen_skel']   # osc and plain join dropped (L1 6.2)
# bandit priors (pseudo-reward at 120 CPU s): L1 facts 4-5 (pull moved A <= 29; osc poor yield)
# = the CPU split among a goal's operators while no reward has come in (choice is proportional to the score):
# L1 WHAT-WORKS 6.1 suggests pull 45 %, gen_skel 20 %, polish 20 % (fresh only), trb 10 %, join 5 %
PRIOR = {'pull': 0.40, 'gen_skel': 0.18, 'polish': 0.15, 'gpull': 0.10, 'jump': 0.07, 'trb': 0.07, 'gjoin': 0.05,
         'join': 0.03, 'osc': 0.02}
# jump = the class jump made deliberate (L1 finding 5: every 29/4 and 30/4 front point came from pulls that ended
# one AND above the A cap with AD one lower): op_polish.py with caps (A + 1, AD - 1, max(GD, goal GD)) on targets
# one AND-depth level above the goal box (A <= goal A, AD = goal AD + 1, G <= goal G + 15, GD <= goal GD + 6)
S.SCRIPTS.setdefault('jump', HUBDIR / 'op_polish.py')
S.DEFAULT_SECONDS.setdefault('jump', 90)
NO_POLISH_ON = {'seed', 'ingest'}     # L1 finding 3: polish on seeds 0 of 138 with lower G
# max jobs of one operator on one tuple (A, AD, G, GD) per front state (L1 fact 3: polish yield 2.31/0.92/0 per
# CPU-h on attempts 1/2/3, pull 2.08/2.19/1.29/0; repeat joins on the same target are waste); fresh tuples first
TUPLE_CAP = {'polish': 2, 'gpull': 3, 'pull': 3, 'osc': 2, 'join': 1, 'gjoin': 1, 'trb': 1, 'gen_skel': 2, 'jump': 2}
FRESH_FIRST = 0.7
S.SCRIPTS.setdefault('gjoin', HUBDIR.parent / 'strategies' / 'X2' / 'op_gjoin.py')
WRAPPER = HUBDIR.parent / 'strategies' / 'X2' / 'op_goal.py'
S.DEFAULT_SECONDS.setdefault('gjoin', 60)
# gpull = the polish script run with goal-stepped caps (op_pull itself lowers a cap relative to the target and
# drops the AD cap, so it cannot take a goal step)
S.SCRIPTS.setdefault('gpull', HUBDIR / 'op_polish.py')
S.DEFAULT_SECONDS.setdefault('gpull', 90)
POOL_N = 40
AES_CHECK = HUBDIR.parent / 'campaigns' / 'aes_check.py'


def _cap(v):
    return '-' if v is None else str(int(v))


class GoalScheduler(S.Scheduler):
    def __init__(self, args):
        super().__init__(args)
        self.gshare = dict(DEFAULT_SHARE); self.gshare.update(GL.parse_shares(args.goal_share))
        self.generic_share = args.generic_share
        self.gops = {n: list(OPS_A if n == 'A' else OPS_OTHER) for n in GL.NAMES}
        self.gT = 3.0; self.gW = 10; self.keep_met = False; self.geps = args.eps
        self.gused = {n: 0.0 for n in list(GL.NAMES) + ['generic']}
        self.ghist = {}                 # (goal, op) -> [(cpu_s, reward)]
        self.gatt = {}                  # (goal, op, id) -> n
        self._goal_pick = None          # (op, why, target) while Scheduler.launch runs for a goal job
        self.tatt = {}                  # (op, tuple, goal or None, front version) -> n
        self.fver = 0; self._front_set = frozenset(self.ar.front())
        self.found = Path(args.found) if args.found else self.dir / 'found'
        self.gctl_mtime = None
        self._pool_cache = {}; self._pool_n = -1
        self.gbest = {}                 # goal -> (key, m, id)
        self.met = set()
        self._recompute_best()
        for o in OPS_OTHER + OPS_A: self.hist.setdefault(o, [])
        self.secs.setdefault('gpull', 90.0); self.secs.setdefault('gjoin', 60.0); self.secs.setdefault('jump', 90.0)
        self.geps = min(self.geps, 0.1)

    # ---- goal state ---------------------------------------------------------------------------
    def _recompute_best(self):
        self.gbest = {}
        for i, r in self.ar.rec.items():
            self._update_best(i, (r['A'], r['AD'], r['G'], r['GD']))
        self.met = {n for n in GL.NAMES if self.gbest.get(n) and self.gbest[n][0] == (0, 0, 0, 0)}
        self._pool_n = -1

    def seed(self, files):
        n = super().seed(files)
        self._recompute_best(); self._front_set = frozenset(self.ar.front())
        return n

    def _update_best(self, i, m):
        """returns the goals whose best key improved"""
        imp = []
        for g in GL.GOALS:
            k = GL.key(g, m); b = self.gbest.get(g.name)
            if b is None or (k, m) < (b[0], b[1]):
                if b is None or k < b[0]: imp.append(g.name)
                self.gbest[g.name] = (k, m, i)
        return imp

    def pool(self, gname):
        """records nearest to the goal: scalar <= best + W, or stepping stones; nearest POOL_N"""
        n = len(self.ar.rec)
        if self._pool_n != n: self._pool_cache = {}; self._pool_n = n
        if gname in self._pool_cache: return self._pool_cache[gname]
        g = GL.goal(gname); rows = []
        for i, r in self.ar.rec.items():
            m = (r['A'], r['AD'], r['G'], r['GD'])
            rows.append((GL.scalar(g, m), m, i, GL.stepping(g, m)))
        if not rows: return (0, [])
        smin = min(s for s, m, i, st in rows)
        sel = sorted([x for x in rows if x[0] <= smin + self.gW or x[3]], key=lambda x: (x[0], x[1], x[2]))
        out = (smin, [(s, i) for s, m, i, st in sel[:(400 if gname == 'A' else POOL_N)]])
        self._pool_cache[gname] = out
        return out

    # ---- control --------------------------------------------------------------------------------
    def control(self):
        f = self.dir / 'control.json'
        if f.exists() and f.stat().st_mtime != self.gctl_mtime:
            self.gctl_mtime = f.stat().st_mtime
            try:
                c = json.loads(f.read_text())
            except Exception as e:
                c = {}; self.log(ev='goal-control-error', error=repr(e))
            if 'goal_share' in c: self.gshare = {k: float(v) for k, v in c['goal_share'].items() if k in GL.BY_NAME}
            if 'generic_share' in c: self.generic_share = float(c['generic_share'])
            for k, v in (c.get('goal_ops') or {}).items():
                if k in GL.BY_NAME: self.gops[k] = list(v)
            self.gT = float(c.get('goal_T', self.gT)); self.gW = int(c.get('goal_W', self.gW))
            self.keep_met = bool(c.get('keep_met', self.keep_met)); self.geps = float(c.get('goal_eps', self.geps))
            self.log(ev='goal-control', goal_share=self.gshare, generic_share=self.generic_share, goal_ops=self.gops,
                     goal_T=self.gT, goal_W=self.gW, keep_met=self.keep_met, goal_eps=self.geps)
        super().control()
        for ops in self.gops.values():
            for o in ops: self.hist.setdefault(o, [])

    # ---- choice ---------------------------------------------------------------------------------
    def choose_goal(self):
        cand = {n: s for n, s in self.gshare.items() if s > 0 and (self.keep_met or n not in self.met)}
        if self.generic_share > 0: cand['generic'] = self.generic_share
        if not cand: return 'generic'
        return min(cand, key=lambda n: (self.gused[n] / cand[n], self.rng.random()))

    def gscore(self, gname, op):
        h = self.ghist.get((gname, op), [])[-S.WINDOW:]
        return (sum(r for c, r in h) + PRIOR.get(op, 0.5)) / (sum(c for c, r in h) + 120.0)

    def tkey(self, op, i, gname):
        r = self.ar.rec[i]
        return (op, (r['A'], r['AD'], r['G'], r['GD']), gname if op in CAPPED or op in ('gpull', 'jump') else None, self.fver)

    def jump_pool(self, gname):
        g = GL.goal(gname); key = 'jump:' + gname
        n = len(self.ar.rec)
        if self._pool_n != n: self._pool_cache = {}; self._pool_n = n
        if key in self._pool_cache: return self._pool_cache[key]
        rows = []
        if g.AD is not None and g.A is not None:
            for i, r in self.ar.rec.items():
                if (r['A'] <= g.A and r['AD'] == g.AD + 1 and (g.G is None or r['G'] <= g.G + 15)
                        and (g.GD is None or r['GD'] <= g.GD + 6)):
                    # rank by the goal distance of the circuit the jump aims at: (A + 1, AD - 1, G, GD)
                    rows.append((GL.scalar(g, (r['A'] + 1, r['AD'] - 1, r['G'], r['GD'])), r['G'] + r['GD'], i))
        rows.sort()
        out = (0, [(0, i) for a, x, i in rows[:POOL_N]])
        self._pool_cache[key] = out
        return out

    def open_rows(self, gname, op, busy):
        smin, rows = self.jump_pool(gname) if op == 'jump' else self.pool(gname)
        cap = TUPLE_CAP.get(op, 3)
        out = [(s, i) for s, i in rows if i not in busy and self.tatt.get(self.tkey(op, i, gname), 0) < cap]
        if op == 'polish': out = [(s, i) for s, i in out if self.ar.rec[i]['operator'] not in NO_POLISH_ON]
        return smin, out

    def choose_goal_op(self, gname, busy=()):
        ops = [o for o in self.gops[gname] if o in S.SCRIPTS]
        ok = [o for o in ops if self.open_rows(gname, o, busy)[1]]
        ops = ok or ops
        if self.rng.random() < self.geps: return self.rng.choice(ops), 'explore'
        w = [self.gscore(gname, o) for o in ops]          # proportional, not argmax: the prior is a CPU split
        x = self.rng.random() * sum(w)
        for o, wi in zip(ops, w):
            x -= wi
            if x <= 0: return o, 'exploit'
        return ops[-1], 'exploit'

    def choose_goal_target(self, gname, op, busy):
        smin, rows = self.open_rows(gname, op, busy)
        if not rows:
            smin, rows = self.jump_pool(gname) if op == 'jump' else self.pool(gname)
            rows = [(s, i) for s, i in rows if i not in busy]
        if not rows: return None
        fresh = [(s, i) for s, i in rows if self.tatt.get(self.tkey(op, i, gname), 0) == 0]
        if fresh and self.rng.random() < FRESH_FIRST:
            s0 = min(s for s, i in fresh)
            return self.rng.choice([i for s, i in fresh if s == s0])
        w = [math.exp(-(s - smin) / self.gT) / (1.0 + self.gatt.get((gname, op, i), 0)) for s, i in rows]
        x = self.rng.random() * sum(w)
        for wi, (s, i) in zip(w, rows):
            x -= wi
            if x <= 0: return i
        return rows[-1][1]

    def goal_caps(self, gname, op, tm):
        g = GL.goal(gname); A, AD, G, GD = tm
        if op in CAPPED:
            return (g.A, g.AD, g.GD)
        if op == 'jump':
            return (A + 1, AD - 1, GD if g.GD is None else max(GD, g.GD))
        if op != 'gpull':
            return None
        cur = {'A': A, 'AD': AD, 'GD': GD}; gc = {'A': g.A, 'AD': g.AD, 'GD': g.GD}
        caps = {}
        viol = [k for k in ('A', 'AD', 'GD') if gc[k] is not None and cur[k] > gc[k]]
        for k in ('A', 'AD', 'GD'):
            if gc[k] is None: caps[k] = AD if k == 'AD' else None
            elif cur[k] <= gc[k]: caps[k] = gc[k]
            else: caps[k] = cur[k]
        if viol:
            k = viol[0]; step = self.rng.choice([1, 1, 2]) if k == 'GD' else 1
            caps[k] = max(gc[k], cur[k] - step)
        else:
            caps['GD'] = GD - self.rng.choice([1, 1, 2])
        return (caps['A'], caps['AD'], caps['GD'])

    # ---- jobs -----------------------------------------------------------------------------------
    def choose_op(self):
        if self._goal_pick is not None: return self._goal_pick[0], self._goal_pick[1]
        return super().choose_op()

    def choose_target(self, op, busy):
        if self._goal_pick is not None: return self._goal_pick[2]
        return super().choose_target(op, busy)

    def launch(self, cpu, busy):
        """the hub's own Scheduler.launch (run ids, job dict, pinning), with choose_op / choose_target answered by
        the goal layer, and caps / objective handed to the job by the wrapper strategies/X2/op_goal.py"""
        gname = self.choose_goal()
        caps = None; objective = None; self._goal_pick = None; op = None
        if gname != 'generic':
            op, why = self.choose_goal_op(gname, busy)
            tid = self.choose_goal_target(gname, op, busy)
            if tid is None:
                self.gused[gname] += 30.0      # do not retry an empty goal forever
                return None
            r = self.ar.rec[tid]
            caps = self.goal_caps(gname, op, (r['A'], r['AD'], r['G'], r['GD']))
            objective = 'a,ad,cost,gd'
            self._goal_pick = (op, why, tid)
        env = {'X2_GOAL': gname}
        saved = None
        if op is not None:
            saved = S.SCRIPTS[op]
            env.update({'X2_REAL': str(saved), 'X2_CAPS': ','.join(_cap(v) for v in caps) if caps else '',
                        'X2_OBJECTIVE': objective or ''})
            S.SCRIPTS[op] = WRAPPER
        old = {k: os.environ.get(k) for k in env}
        os.environ.update(env)
        try:
            job = super().launch(cpu, busy)
        finally:
            for k, v in old.items():
                if v is None: os.environ.pop(k, None)
                else: os.environ[k] = v
            if op is not None: S.SCRIPTS[op] = saved
            pick = self._goal_pick; self._goal_pick = None
        if job is None: return None
        if pick is not None and (job.get('op') != pick[0] or job.get('target') != pick[2]):
            self.log(ev='goal-compat-warning', run_id=job.get('run_id'), want=pick, got=[job.get('op'), job.get('target')])
        if gname != 'generic':
            tid = job['target']
            self.gatt[(gname, op, tid)] = self.gatt.get((gname, op, tid), 0) + 1
            tk = self.tkey(op, tid, gname); self.tatt[tk] = self.tatt.get(tk, 0) + 1
        est = float(self.secs.get(job['op'], 60)); self.gused[gname] += est
        job.update({'goal': gname, 'goal_caps': caps, 'goal_objective': objective, 'est': est,
                    'goal_script': str(saved) if saved else None})
        return job

    def finish(self, job):
        before = set(self.ar.rec)
        best0 = {n: (self.gbest[n][0] if n in self.gbest else None) for n in GL.NAMES}
        tr = self.ar.rec[job['target']]; tm = (tr['A'], tr['AD'], tr['G'], tr['GD'])
        try:
            super().finish(job)
        finally:
            new = [i for i in self.ar.rec if i not in before]
            fs = frozenset(self.ar.front())
            if fs != self._front_set: self._front_set = fs; self.fver += 1      # new front state: tuple caps reset
            if job['op'] == 'gjoin' and new: self._fix_gjoin_parents(job)
            prog = {}
            for i in new:
                r = self.ar.rec[i]; m = (r['A'], r['AD'], r['G'], r['GD'])
                for n in self._update_best(i, m): prog[n] = [best0[n], list(self.gbest[n][0]), list(m), i]
                for n in GL.met_goals(m):
                    self.goal_met(n, i, m, job)
            gname = job['goal']; reward = 0.0
            if gname != 'generic':
                g = GL.goal(gname); kt = GL.key(g, tm)
                reward += 5.0 * GL.step_gain(best0[gname], self.gbest[gname][0])
                for i in new:
                    r = self.ar.rec[i]; m = (r['A'], r['AD'], r['G'], r['GD'])
                    reward += GL.step_gain(kt, GL.key(g, m)) + (0.05 if GL.stepping(g, m) else 0.0)
            rf = self.dir / 'runs' / (job['run_id'] + '.json')
            cpu = None
            if rf.exists():
                try:
                    run = json.loads(rf.read_text()); cpu = run.get('cpu_s')
                    run.update({'goal': gname, 'goal_caps': job['goal_caps'], 'goal_objective': job.get('goal_objective'),
                                'goal_script': job.get('goal_script'), 'goal_reward': reward, 'goal_progress': prog})
                    rf.write_text(json.dumps(run, indent=1, default=str))
                except Exception as e:
                    self.log(ev='goal-run-error', run_id=job['run_id'], error=repr(e))
            cpu = float(cpu or (time.time() - job['t0']))
            self.gused[gname] += cpu - job['est']
            if gname != 'generic': self.ghist.setdefault((gname, job['op']), []).append((cpu, reward))
            if prog: self.log(ev='goal-progress', run_id=job['run_id'], goal=gname, op=job['op'], progress=prog)
            with open(self.dir / 'goal_stats.jsonl', 'a') as f:
                f.write(json.dumps({'run_id': job['run_id'], 'goal': gname, 'op': job['op'], 'target': job['target'],
                                    'target_m': list(tm), 'caps': job['goal_caps'], 'cpu_s': cpu, 'admitted': len(new),
                                    'reward': reward, 'progress': prog, 'ts': round(time.time(), 1)}) + '\n')

    def _fix_gjoin_parents(self, job):
        """the hub's finish() records join parents only for op 'join': same for gjoin (record json rewritten)"""
        try:
            run = json.loads((self.dir / 'runs' / (job['run_id'] + '.json')).read_text())
            joins = ((run.get('op_info') or {}).get('joins')) or []
            for o in run.get('outcome') or []:
                if o.get('status') != 'admitted' or not o.get('id'): continue
                k = int(o['cand'].split('-')[1].split('.')[0])
                if k >= len(joins): continue
                r = self.ar.rec[o['id']]
                r['parents'] = [joins[k]['front'], joins[k]['back']]
                r['operator_settings'] = dict(r.get('operator_settings') or {}, **joins[k])
                atomic_write(self.ar.dir / (o['id'] + '.json'), json.dumps(r, indent=1))
        except Exception as e:
            self.log(ev='goal-run-error', run_id=job['run_id'], error='gjoin parents: %r' % e)

    def goal_met(self, gname, i, m, job):
        """a circuit meeting goal gname: NCFF + sidecar in found/, aes_check, event, GOALS-MET.txt"""
        if gname in self.met and not self.keep_met:
            pass                        # still recorded: every meeting circuit is evidence
        self.met.add(gname)
        self.found.mkdir(parents=True, exist_ok=True)
        base = 'goal%s-a%d-ad%d-g%d-gd%d-%s' % (gname, m[0], m[1], m[2], m[3], i)
        cf = self.found / (base + '.circ.txt')
        c = self.ar.circuit(i)
        cf.write_text(core.write_ncff(c, MODEL))
        jf = self.found / (base + '.aes_check.json')
        try:
            p = subprocess.run([sys.executable, str(AES_CHECK), str(cf), '--json', str(jf)], capture_output=True,
                               text=True, timeout=600)
            ok = p.returncode == 0; out = p.stdout[-3000:]
        except Exception as e:
            ok = False; out = repr(e)
        r = self.ar.rec[i]
        side = {'goal': gname, 'goal_caps': GL.goal(gname).caps(), 'id': i, 'metrics': list(m), 'aes_check_ok': ok,
                'aes_check_stdout': out, 'operator': r.get('operator'), 'parents': r.get('parents'), 'seed': r.get('seed'),
                'run_id': r.get('run_id'), 'code_version': r.get('code_version'), 'scheduler': 'hub/scheduler_goal.py',
                'scheduler_version': self.version, 'job_goal': job.get('goal'), 'job_caps': job.get('goal_caps'),
                'campaign': str(self.dir), 'time_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
        (self.found / (base + '.json')).write_text(json.dumps(side, indent=1, default=str))
        self.log(ev='GOAL-MET', goal=gname, id=i, m=list(m), aes_check_ok=ok, file=str(cf))
        with open(self.dir / 'GOALS-MET.txt', 'a') as f:
            f.write('%s goal %s %s id %s aes_check %s %s\n' % (side['time_utc'], gname, m, i, ok, cf))

    def write_front(self):
        super().write_front()
        st = {n: {'best_key': (self.gbest.get(n) or (None,) * 3)[0], 'best_m': (self.gbest.get(n) or (None,) * 3)[1],
                  'best_id': (self.gbest.get(n) or (None,) * 3)[2],
                  'met': n in self.met, 'share': self.gshare.get(n, 0), 'used_cpu': round(self.gused[n], 1),
                  'op_scores': {o: round(self.gscore(n, o), 5) for o in self.gops[n]},
                  'op_jobs': {o: len(self.ghist.get((n, o), [])) for o in self.gops[n]}} for n in GL.NAMES}
        st['generic'] = {'share': self.generic_share, 'used_cpu': round(self.gused['generic'], 1)}
        (self.dir / 'goals.json').write_text(json.dumps(st, indent=1, default=str))

    def run(self):
        self.control()
        self.log(ev='goal-start', goal_share=self.gshare, generic_share=self.generic_share, goal_ops=self.gops,
                 best={n: self.gbest.get(n) for n in GL.NAMES}, met=sorted(self.met))
        super().run()


class _Args(object):
    """argparse result that answers None for attributes this parser does not define, so a newer Scheduler that reads
    new options (e.g. after the review5 merge) does not fail on them; their defaults then come from that code"""
    def __init__(self, ns):
        self.__dict__.update(vars(ns))

    def __getattr__(self, k):
        if k.startswith('__'): raise AttributeError(k)
        return None


def _convert(v):
    for f in (int, float):
        try:
            return f(v)
        except ValueError:
            pass
    return v


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True)
    ap.add_argument('--cpus', help='default: the CPUs this process may run on')
    ap.add_argument('--hours', type=float, default=1.0); ap.add_argument('--seed-list')
    ap.add_argument('--ops', default='polish,pull,join,trb,osc,gen_skel'); ap.add_argument('--seconds')
    ap.add_argument('--eps', type=float, default=0.25); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--seed-only', action='store_true')
    ap.add_argument('--near', type=float, default=0.0); ap.add_argument('--near-gap', type=int, default=3)
    ap.add_argument('--nursery', type=float, default=0.0)
    ap.add_argument('--goal-share', default='', help="e.g. A=0.1,B=0.2 (others keep the defaults)")
    ap.add_argument('--generic-share', type=float, default=DEFAULT_GENERIC)
    ap.add_argument('--found', help='directory for goal-meeting circuits (default DIR/found)')
    ns, rest = ap.parse_known_args()
    if ns.cpus is None:
        ns.cpus = ','.join(str(c) for c in sorted(os.sched_getaffinity(0)))
    args = _Args(ns)
    # options of the base scheduler this parser does not know (--name value / --flag) are passed through
    i = 0
    while i < len(rest):
        k = rest[i]
        if not k.startswith('--'): sys.exit('unexpected argument %s' % k)
        if '=' in k:
            k, v = k.split('=', 1); setattr(args, k[2:].replace('-', '_'), _convert(v)); i += 1
        elif i + 1 < len(rest) and not rest[i + 1].startswith('--'):
            setattr(args, k[2:].replace('-', '_'), _convert(rest[i + 1])); i += 2
        else:
            setattr(args, k[2:].replace('-', '_'), True); i += 1
    s = GoalScheduler(args)
    if args.seed_list:
        s.seed(Path(args.seed_list).read_text().split())
    if not args.seed_only:
        s.run()


if __name__ == '__main__':
    main()
