#!/usr/bin/env python3
"""Hub scheduler: one shared archive, operator jobs chosen by a bandit on frontier gain per CPU second.

    python3 nonlinear/boolflux/hub/scheduler.py --dir CAMPAIGN [--cpus 4,5,6,7] --hours H [--seed-list FILES]
        [--ops polish,pull,join,trb] [--seconds polish=90,pull=90,join=60,trb=30] [--eps 0.25] [--seed 1]
        [--cpu-allow 4-11]

Loop: for every free CPU choose an operator (epsilon-greedy on the recent gain / CPU-s of each
operator, epsilon = uniform floor) and a target (a Pareto-front circuit, fewest attempts by that
operator first, ties random), run op_<name>.py pinned to that CPU, then verify and admit its
candidates (archive.Archive.admit: two verifiers, cell rule).  Gain of an admission
(archive.Archive.gain): 8 if it lowers A at no worse other coordinates, 4 for AD, 2 for G, 1 for GD
(lexicographic research priorities), 0.01 for a better circuit of its (A, AD, GD) cell that is
dominated elsewhere.  Every job: DIR/runs/<run_id>.json (code version, seed, settings, parents,
timing, status, outcome); DIR/stats.jsonl one line per job; DIR/front.json every 5 minutes.

CPUs (review 5, H4).  One job per CPU.  --cpus defaults to the CPU affinity mask of the scheduler
process (the list given to xsrun), so the list is written once.  An explicit --cpus outside that
mask is refused unless --cpu-allow names it.  --cpu-allow (default: the start set) is the hard
limit: control.json "cpus" sets the active set exactly (it can shrink and grow), but never beyond
the allow list.  The active set is written to DIR/cpus.json on every change.

Run ids are '<campaign uid>.r<number>-<op>' (DIR/campaign.json holds the uid), unique across
campaigns, so an archive copied into another campaign keeps unambiguous lineage (review 5, H3).
"""
from __future__ import annotations

import argparse
import json
import os
import random
import signal
import subprocess
import sys
import time
from pathlib import Path

HUBDIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HUBDIR.parents[1]))
from boolflux import core   # noqa: E402
from boolflux.hub.common import load, code_version, metrics, cid, file_sha, atomic_write   # noqa: E402
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
KILL_FACTOR = 2.0; KILL_GRACE = 120.0    # a job is killed after seconds * KILL_FACTOR + KILL_GRACE wall seconds
MIN_JOB_S = 5.0                          # no job is started with less than this left before the end
FAIL_LIMIT = 5; SUSPEND_S = 600.0        # an operator failing FAIL_LIMIT times in a row is suspended
FB_SAVE_S = 60.0                         # function bank written at most this often


def acls(A):
    return 'A<=31' if A <= 31 else ('A32-35' if A <= 35 else 'A>=36')


def parse_cpus(s):
    """'0-3,7' or [0, 1, '2-3'] -> sorted list without repeats"""
    if isinstance(s, (list, tuple)): s = ','.join(str(x) for x in s)
    out = set()
    for part in str(s).split(','):
        part = part.strip()
        if not part: continue
        if '-' in part:
            a, b = part.split('-', 1); out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    if any(c < 0 for c in out): raise ValueError('negative CPU number')
    return sorted(out)


class Scheduler:
    def __init__(self, args):
        for k, v in vars(parser().parse_args(['--dir', '.'])).items():     # a subclass with its own argument parser
            if getattr(args, k, None) is None: setattr(args, k, v)          # gets the defaults of the options it lacks
        self.args = args; self.dir = Path(args.dir); self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / 'runs').mkdir(exist_ok=True); (self.dir / 'jobs').mkdir(exist_ok=True)
        self._lock()
        self.scripts = dict(SCRIPTS); self.generators = set(GENERATORS)
        self.ar = Archive(self.dir, gain_mode=args.gain); self.fb = FuncBank(self.dir)
        self.ops = args.ops.split(',')
        bad = [o for o in self.ops if o not in self.scripts]
        if bad: raise SystemExit('unknown operators %s (known: %s)' % (bad, sorted(self.scripts)))
        self.secs = dict(DEFAULT_SECONDS)
        for kv in (args.seconds or '').split(','):
            if kv: k, v = kv.split('='); self.secs[k] = float(v)
        self.hist = {o: [] for o in self.ops}            # recent (cpu_s, gain)
        self.attempts = {}                                 # (op, target key) -> n; key = (A, AD, G, GD), or the id with --target-mode id
        self.tuple_caps = parse_caps_arg(args.tuple_caps)  # op -> jobs per tuple before it stops being chosen
        self.cap_base = {}; self.renewals = {}             # (op, tuple) -> attempts at the last renewal / renewals so far
        self.join_mark = {}                                # target id -> t_admit through which it was joined with every partner
        self.fail = {}; self.suspended = {}                # op -> consecutive failures / suspended until
        self.version = code_version()
        self.uid = self._campaign_uid()
        self.nrun = self._last_run_number()
        self.rng = random.Random('%s/%d' % (args.seed, self.nrun))   # a restart does not replay the same jobs
        kernel_bin(self.dir)
        self.ctl_mtime = None; self.ctl_bad = None
        self.ad3_share = 0.0; self.ingest_globs = []; self.ingested = set(); self.last_ingest = 0
        self.cpus = []; self.free = []; self.running = []; self.allow = set(); self.stop = None
        self.end = time.time() + args.hours * 3600; self.pending_cpus = None
        self.last_admit = max((r['t_admit'] for r in self.ar.rec.values()), default=0.0)
        self.last_fb_save = time.time()
        for e in self.ar.load_errors: self.log(ev='archive-load-error', what=e)
        if self.ar.cells_repaired:
            self.log(ev='cells-repaired', cells=len(self.ar.cells)); self.ar._save_cells()
        if self.ar.index_missing: self.ar.write_index()
        n = self.ar.dedupe_legacy()
        if n: self.log(ev='cells-deduplicated', dropped_members=n, cells=len(self.ar.cells))
        self.restore()

    # ---- campaign identity, lock, state carried across restarts ---------------------------------
    def _lock(self):
        """one scheduler per campaign directory (two would race on admissions, cells.json and run ids)"""
        import fcntl
        self._lockf = open(self.dir / 'scheduler.lock', 'a+')
        try:
            fcntl.flock(self._lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise SystemExit('another scheduler is running on %s (scheduler.lock is held)' % self.dir)
        self._lockf.seek(0); self._lockf.truncate(); self._lockf.write('%d\n' % os.getpid()); self._lockf.flush()

    def _campaign_uid(self):
        f = self.dir / 'campaign.json'
        try:
            return json.loads(f.read_text())['uid']
        except Exception:
            uid = '%s-%s' % (self.dir.resolve().name.replace('.', '_'), os.urandom(3).hex())
            atomic_write(f, json.dumps({'uid': uid, 'created': time.time(), 'dir': str(self.dir.resolve())}, indent=1))
            return uid

    def _last_run_number(self):
        """highest run number used in runs/ or jobs/ (a count of run files repeats numbers when a
        stopped scheduler left jobs without a run file)"""
        import re
        n = 0
        for d in ('runs', 'jobs'):
            for p in (self.dir / d).iterdir():
                m = re.search(r'(?:^|\.)r(\d+)-', p.name)
                if m: n = max(n, int(m.group(1)))
        return n

    def restore(self):
        """bandit history, attempt counts and join marks from stats.jsonl, so a restart neither
        starts the bandit cold nor repeats work the previous run already did"""
        sf = self.dir / 'stats.jsonl'
        if not sf.exists(): return
        n = 0
        for ln in sf.read_text().splitlines():
            try:
                x = json.loads(ln); op = x['op']
            except Exception:
                continue
            self.hist.setdefault(op, []).append((x.get('cpu_s') or 0.0, x.get('gain') or 0.0))
            tid = x.get('target'); tm = x.get('tm')
            if tid is None or tm is None:                   # line written before review 5: target is in the run file
                try:
                    rf = json.loads((self.dir / 'runs' / (x['run_id'] + '.json')).read_text())
                    tid = rf['target']; tm = rf['target_metrics']
                except Exception:
                    continue
            key = tuple(tm) if self.args.target_mode == 'tuple' else tid
            self.attempts[(op, key)] = self.attempts.get((op, key), 0) + 1; n += 1
            if x.get('join_mark') is not None: self.join_mark[tid] = max(self.join_mark.get(tid, 0.0), x['join_mark'])
        for o in self.hist: self.hist[o] = self.hist[o][-WINDOW:]
        self.log(ev='restored', jobs=n, join_marks=len(self.join_mark))

    # ---- CPUs ----------------------------------------------------------------------------------
    def init_cpus(self):
        mask = set(os.sched_getaffinity(0)); online = os.cpu_count() or 1
        if self.args.cpus in (None, '', 'auto'):
            cpus = sorted(mask)
        else:
            cpus = parse_cpus(self.args.cpus)
        allow = set(parse_cpus(self.args.cpu_allow)) if self.args.cpu_allow else set(cpus)
        bad = [c for c in cpus if c >= online or c not in allow]
        if bad: raise SystemExit('--cpus %s: not online or outside --cpu-allow' % bad)
        outside = [c for c in cpus if c not in mask]
        if outside and not self.args.cpu_allow:
            raise SystemExit('--cpus %s lie outside the CPU affinity of this process (%s): the launch pinning and '
                             '--cpus disagree; fix one of them, or pass --cpu-allow to confirm' % (outside, sorted(mask)))
        self.allow = {c for c in allow if c < online}
        self.cpus = list(cpus); self.free = list(cpus)
        self.save_cpus('start')
        if self.pending_cpus is not None:                  # control.json was read before the CPUs were set up
            self.set_cpus(self.pending_cpus); self.pending_cpus = None

    def set_cpus(self, want, why='control'):
        """make `want` (within the allow list) the active set; jobs running on dropped CPUs finish, then the CPU is released"""
        want = parse_cpus(want)
        refused = [c for c in want if c not in self.allow]
        new = [c for c in want if c in self.allow]
        if refused: self.log(ev='control-error', error='cpus %s are outside the allow list %s: ignored' % (refused, sorted(self.allow)))
        if not new:
            self.log(ev='control-error', error='cpus %s would leave no CPU: ignored' % (want,)); return
        if new == sorted(self.cpus): return
        busy = {j['cpu'] for j in self.running}
        dropped = [c for c in self.cpus if c not in new]
        self.free = [c for c in self.free if c in new] + [c for c in new if c not in self.cpus and c not in busy]
        self.cpus = new
        self.save_cpus(why, dropped=dropped)

    def save_cpus(self, why, dropped=()):
        atomic_write(self.dir / 'cpus.json', json.dumps({'active': sorted(self.cpus), 'allow': sorted(self.allow),
                                                         'ts': time.time(), 'pid': os.getpid()}))
        self.log(ev='cpus', why=why, active=sorted(self.cpus), allow=sorted(self.allow), dropped=list(dropped))

    # ---- hot control: DIR/control.json  {"ops": [...], "seconds": {...}, "eps": x, "near": x, "near_gap": n,
    #      "nursery": x, "ad3_share": x, "cpus": [...], "ingest": [glob, ...], "scripts": {name: path},
    #      "generators": [name, ...]}.  A file is validated as a whole and applied only if valid; every
    #      change and every refusal is logged as an event. ------------------------------------------------
    def control(self):
        f = self.dir / 'control.json'
        try:
            mt = f.stat().st_mtime if f.exists() else None
        except OSError:
            mt = None
        if mt is not None and mt != self.ctl_mtime:
            try:
                c = json.loads(f.read_text())
                if not isinstance(c, dict): raise ValueError('control.json is not an object')
                err = self.apply_control(c)
            except Exception as e:                       # e.g. read while being written: retried at the next change of mtime,
                err = repr(e); c = None                  # or 30 s later if the file was only half written
            if err:
                if self.ctl_bad != (mt, err): self.log(ev='control-error', error=err)
                # a parse error may be a half-written file: look again next time; a content error waits for an edit
                if c is not None: self.ctl_mtime = mt
                self.ctl_bad = (mt, err)
            else:
                self.ctl_mtime = mt; self.ctl_bad = None; self.last_ingest = 0
        if self.ingest_globs and time.time() - self.last_ingest > 1800:
            self.last_ingest = time.time(); self.ingest()

    def apply_control(self, c):
        """returns an error string (nothing applied) or None (everything applied)"""
        scripts = {}
        for name, path in (c.get('scripts') or {}).items():
            sp = Path(path).expanduser()
            if not sp.is_file(): return 'script missing %s' % sp
            scripts[name] = sp
        known = set(self.scripts) | set(scripts)
        ops = c.get('ops')
        if ops is not None:
            if not ops or not isinstance(ops, list): return 'ops must be a non-empty list'
            bad = [o for o in ops if o not in known]
            if bad: return 'unknown ops %s' % bad
        gens = c.get('generators') or []
        bad = [g for g in gens if g not in known]
        if bad: return 'unknown generators %s' % bad
        try:
            secs = {k: float(v) for k, v in (c.get('seconds') or {}).items()}
            num = {k: float(c[k]) for k in ('eps', 'near', 'nursery', 'ad3_share') if k in c}
            tcaps = {str(k): int(v) for k, v in c['tuple_caps'].items()} if 'tuple_caps' in c else None
            gap = int(c['near_gap']) if 'near_gap' in c else None
            cpus = parse_cpus(c['cpus']) if 'cpus' in c else None
        except (TypeError, ValueError) as e:
            return 'bad value: %r' % (e,)
        if any(v <= 0 for v in secs.values()): return 'seconds must be positive'
        if any(not (0.0 <= v <= 1.0) for v in num.values()): return 'eps, near, nursery, ad3_share must be in [0, 1]'
        ing = c.get('ingest', self.ingest_globs)
        if not isinstance(ing, list): return 'ingest must be a list of globs'
        # ---- valid: apply ----
        self.scripts.update(scripts)
        for name in scripts: self.secs.setdefault(name, 60.0)
        self.generators.update(gens)
        if ops is not None: self.ops = list(ops)
        for o in self.ops: self.hist.setdefault(o, [])
        self.secs.update(secs)
        if 'eps' in num: self.args.eps = num['eps']
        if 'near' in num: self.args.near = num['near']
        if 'nursery' in num: self.args.nursery = num['nursery']
        if 'ad3_share' in num: self.ad3_share = num['ad3_share']
        if gap is not None: self.args.near_gap = gap
        if tcaps is not None: self.tuple_caps = tcaps
        if cpus is not None:
            if self.allow: self.set_cpus(cpus)
            else: self.pending_cpus = cpus
        self.ingest_globs = list(ing)
        self.log(ev='control', control=c, ops=self.ops, secs=self.secs, eps=self.args.eps, near=self.args.near,
                 nursery=self.args.nursery, ad3_share=self.ad3_share, cpus=sorted(self.cpus), tuple_caps=self.tuple_caps,
                 scripts={k: str(v) for k, v in self.scripts.items() if k not in SCRIPTS}, generators=sorted(self.generators))
        return None

    @staticmethod
    def source_info(f):
        """lineage of a circuit that enters from a file: content hash and, when present, its JSON sidecar"""
        p = Path(f); s = {'file': str(f), 'file_sha': file_sha(p)}
        for sc in (p.with_suffix('.json'), Path(str(p) + '.json'), Path(str(p).replace('.circ.txt', '.json'))):
            if sc != p and sc.is_file() and sc.stat().st_size < 200000:
                try:
                    s['sidecar'] = json.loads(sc.read_text()); s['sidecar_file'] = str(sc)
                except Exception:
                    s['sidecar_file'] = str(sc)
                break
        return s

    def ingest(self):
        import glob
        n = 0; seen = 0; bad = 0
        for g in self.ingest_globs:
            for f in sorted(glob.glob(str(Path(g).expanduser()))):
                try:
                    key = (f, Path(f).stat().st_mtime)
                    if key in self.ingested: continue
                    self.ingested.add(key); seen += 1
                    c = load(f)
                    st, r, gn = self.ar.admit(c, operator='ingest', settings=self.source_info(f), code_version=self.version,
                                              force_keep=True)
                except Exception as e:                    # vanished file, unreadable text: logged, never fatal
                    bad += 1; self.log(ev='ingest-error', file=f, error=repr(e)); continue
                if st == 'admitted':
                    n += 1; self.fb.add_circuit(c, r['id']); self.last_admit = r['t_admit']
                    self.log(ev='ingest', file=f, id=r['id'], m=metrics(c), gain=gn)
                elif st.startswith('rejected'):
                    bad += 1; self.log(ev='ingest-reject', file=f, status=st)
        self.log(ev='ingested', files=seen, admitted=n, bad=bad)

    def log(self, **kw):
        kw['ts'] = round(time.time(), 2)
        with open(self.dir / 'events.jsonl', 'a') as f: f.write(json.dumps(kw, default=str) + '\n')

    # ---- seeding ----------------------------------------------------------------------------
    def seed(self, files):
        n = 0; bad = 0
        for f in files:
            try:
                c = load(f)
            except Exception as e:
                bad += 1; self.log(ev='seed-reject', file=str(f), status='unreadable: %r' % (e,)); continue
            st, r, g = self.ar.admit(c, operator='seed', settings=self.source_info(f), code_version=self.version, force_keep=True)
            if st == 'admitted':
                n += 1; self.fb.add_circuit(c, r['id']); self.last_admit = r['t_admit']
            elif not st.startswith(('duplicate', 'not-better')):
                bad += 1; self.log(ev='seed-reject', file=str(f), status=st)
        self.fb.save()
        self.log(ev='seeded', admitted=n, rejected=bad, cells=len(self.ar.cells), front=len(self.ar.front()))
        return n

    # ---- choice -----------------------------------------------------------------------------
    def score(self, op):
        h = self.hist[op][-WINDOW:]
        return (sum(g for c, g in h) + 0.5) / (sum(c for c, g in h) + 120.0)

    def active_ops(self):
        now = time.time()
        return [o for o in self.ops if self.suspended.get(o, 0) <= now]

    def choose_op(self):
        ops = self.active_ops()
        if not ops: return None, 'none'
        if self.rng.random() < self.args.eps: return self.rng.choice(ops), 'explore'
        return max(ops, key=lambda o: (self.score(o), self.rng.random())), 'exploit'

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
            if (r['operator'] in self.generators or (r.get('operator_settings') or {}).get('nursery')) and ids[0] not in fr and self.attempts.get((op, self.target_key(ids[0])), 0) < 3:
                out.append((r['t_admit'], ids[0]))
        return [i for t, i in sorted(out, reverse=True)]

    def target_key(self, i):
        """what attempts are counted against: the (A, AD, G, GD) tuple (default; the up to K equal-tuple
        circuits of a cell share one count, review 5 H7) or the circuit id (--target-mode id, as before)"""
        if self.args.target_mode == 'id': return i
        r = self.ar.rec[i]
        return (r['A'], r['AD'], r['G'], r['GD'])

    def eff_attempts(self, op, key):
        """jobs of op on the tuple since its cap was last renewed"""
        return self.attempts.get((op, key), 0) - self.cap_base.get((op, key), 0)

    def capped(self, op, key):
        cap = self.tuple_caps.get(op)
        return cap is not None and self.eff_attempts(op, key) >= cap

    def renew_caps(self, q):
        """--cap-renew box: a new front tuple q renews the caps of every front tuple t whose cap box contains it
        (q.A <= t.A, q.AD <= t.AD, q.GD <= t.GD; q then has more gates than t): something moved under t's caps,
        so t gets its jobs again.  At most --cap-renew-max renewals per (operator, tuple)."""
        if self.args.cap_renew != 'box' or self.args.target_mode != 'tuple': return 0
        n = 0
        for t in self.ar.front():
            if t == q or not (q[0] <= t[0] and q[1] <= t[1] and q[3] <= t[3]): continue
            for op in self.tuple_caps:
                k = (op, t)
                if self.eff_attempts(op, t) > 0 and self.renewals.get(k, 0) < self.args.cap_renew_max:
                    self.cap_base[k] = self.attempts.get(k, 0); self.renewals[k] = self.renewals.get(k, 0) + 1; n += 1
        if n: self.log(ev='cap-renew', by=list(q), renewed=n)
        return n

    def fresh_target(self, busy):
        """a front tuple that has not had its first polish / pull yet: (op, id) or None.  A <= 31 first,
        then the newest.  New tuples get their first jobs at once instead of waiting behind old ones."""
        ops = [o for o in self.active_ops() if o in self.tuple_caps and self.tuple_caps[o] > 0]
        if not ops or self.args.target_mode == 'id': return None
        best = None
        for i in self.ar.front_ids():
            k = self.target_key(i)
            if k in busy: continue
            todo = [o for o in ops if self.attempts.get((o, k), 0) == 0]
            if not todo: continue
            r = self.ar.rec[i]; rank = (0 if r['A'] <= 31 else 1, -r['t_admit'])
            if best is None or rank < best[0]: best = (rank, todo[0], i)
        return (best[1], best[2]) if best else None

    def choose_target(self, op, busy, ignore_caps=False):
        pool = self.ar.front_ids()
        if op in ('polish', 'pull', 'trb') and self.args.nursery > 0 and self.rng.random() < self.args.nursery:
            nu = [i for i in self.nursery_ids(op) if self.target_key(i) not in busy]
            if nu: return nu[0]
        ad3 = self.ad3_share > 0 and self.rng.random() < self.ad3_share
        if op in ('polish', 'pull', 'trb') and self.args.near > 0 and self.rng.random() < self.args.near:
            pool = self.near_ids() or pool
        if ad3:                                            # after the near choice, so that the share holds for both pools
            p3 = [i for i in pool if self.ar.rec[i]['AD'] <= 3]
            if p3: pool = p3
        ids = [i for i in pool if self.target_key(i) not in busy]
        if not ignore_caps: ids = [i for i in ids if not self.capped(op, self.target_key(i))]
        if op == 'join' and self.args.join_mode == 'incremental':
            # a join of X with partners it has already met is the same computation: one pass per (target, archive state)
            ids = [i for i in ids if self.join_mark.get(i, 0.0) < self.last_admit]
        if not ids: return None
        self.rng.shuffle(ids)                              # ties random (also which of a tuple's circuits is used)
        if self.args.target_mode == 'id':
            return min(ids, key=lambda i: self.attempts.get((op, i), 0))
        return min(ids, key=lambda i: (self.eff_attempts(op, self.target_key(i)), 0 if self.ar.rec[i]['A'] <= 31 else 1))

    # ---- jobs -------------------------------------------------------------------------------
    def launch(self, cpu, busy):
        fresh = self.fresh_target(busy)
        if fresh is not None:
            op, tid = fresh; why = 'fresh'
        else:
            op, why = self.choose_op()
            if op is None: return None
            tid = self.choose_target(op, busy)
            if tid is None:                                # e.g. nothing new to join, or every tuple at its cap: try the other operators
                for o in sorted((o for o in self.active_ops() if o != op), key=lambda o: -self.score(o)):
                    tid = self.choose_target(o, busy)
                    if tid is not None: op, why = o, why + '-fallback'; break
            if tid is None:                                # everything capped: a CPU must not idle, least-attempted tuple first
                for o in sorted(self.active_ops(), key=lambda o: -self.score(o)):
                    tid = self.choose_target(o, busy, ignore_caps=True)
                    if tid is not None: op, why = o, 'over-cap'; break
            if tid is None: return None
        return self.start_job(cpu, op, why, tid)

    def start_job(self, cpu, op, why, tid, extra=(), env=None):
        """Start operator `op` on archive member `tid`, pinned to `cpu`; returns the job dict, or None when
        too little time is left.  Everything a job needs for its run record is set here (unique run id, fresh job
        directory, seconds cut to the end of the campaign, own process group, kill limit, script hash, join
        mark), so a subclass that chooses (op, target) its own way should call this instead of building the
        command itself.  extra: more command-line arguments (e.g. ['--caps', '28,4,22']); env: environment."""
        end = self.end
        secs = min(self.secs[op], end - time.time())       # a job never runs past the end of the campaign
        if secs < MIN_JOB_S: return None
        key = self.target_key(tid); self.attempts[(op, key)] = self.attempts.get((op, key), 0) + 1
        while True:                                        # a job directory is never reused
            self.nrun += 1
            run_id = '%s.r%05d-%s' % (self.uid, self.nrun, op)
            jd = self.dir / 'jobs' / run_id
            if not jd.exists() and not (self.dir / 'runs' / (run_id + '.json')).exists(): break
        seed = self.rng.randrange(1, 1 << 30)
        script = self.scripts[op]
        cmd = ['taskset', '-c', str(cpu), sys.executable, str(script), '--archive', str(self.dir),
               '--in', tid, '--seed', str(seed), '--seconds', str(round(secs, 1)), '--out', str(jd)]
        since = None
        if op == 'join' and self.args.join_mode == 'incremental':
            since = self.join_mark.get(tid, 0.0); cmd += ['--since', repr(since)]
        cmd += [str(x) for x in extra]
        lf = open(self.dir / 'jobs' / (run_id + '.log'), 'w')
        p = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT, start_new_session=True, env=env)
        return {'p': p, 'lf': lf, 'op': op, 'why': why, 'target': tid, 'run_id': run_id, 'jd': jd, 'seed': seed,
                'cpu': cpu, 't0': time.time(), 'cmd': cmd, 'key': key, 'secs': secs, 'script': str(script), 'script_sha': file_sha(script),
                'limit': secs * KILL_FACTOR + KILL_GRACE, 'since': since}

    @staticmethod
    def kill(job, why):
        if job.get('killed'): return
        job['killed'] = why
        p = job['p']
        try:
            if os.getpgid(p.pid) == p.pid: os.killpg(p.pid, signal.SIGKILL)    # the operator and its kernel child
            else: p.kill()                                                     # started without its own process group
        except OSError:
            pass

    def finish(self, job):
        job['lf'].close()
        jd = job['jd']; op = job['op']; tm = self.ar.rec[job['target']]; rc = job['p'].returncode
        # (a subclass may build its own job dict: everything beyond the 2026-11-14 keys has a default)
        job.setdefault('secs', self.secs.get(op)); job.setdefault('script', str(self.scripts.get(op, SCRIPTS.get(op))))
        job.setdefault('script_sha', file_sha(job['script']))
        wall = round(time.time() - job['t0'], 2)
        rec = {}; rec_error = None
        try:
            if (jd / 'record.json').exists():
                rec = json.loads((jd / 'record.json').read_text())
                if not isinstance(rec, dict): rec, rec_error = {}, 'record.json is not an object'
            else:
                rec_error = 'no record.json'
        except Exception as e:
            rec_error = 'record.json unreadable: %r' % (e,)
        if job.get('killed'): status = job['killed']                       # 'timeout' or 'stopped'
        elif self.stop and rc is not None and rc < 0: status = 'stopped'   # the stop signal reached the job first
        elif rc != 0 or rec_error or rec.get('error'): status = 'failed'
        else: status = 'ok'
        info = rec.get('info') if isinstance(rec.get('info'), dict) else {}
        version = rec.get('code_version') or self.version
        cpu = rec.get('cpu_s') or wall
        outcome = []; gain = 0.0
        run = {'run_id': job['run_id'], 'campaign': self.uid, 'operator': op, 'choice': job['why'], 'target': job['target'],
               'target_metrics': [tm['A'], tm['AD'], tm['G'], tm['GD']], 'target_class': acls(tm['A']),
               'seed': job['seed'], 'cpu': job['cpu'], 'command': job['cmd'], 'returncode': rc, 'status': status,
               'record_error': rec_error or rec.get('error'), 'script': job['script'], 'script_sha': job['script_sha'],
               'code_version': version, 'scheduler_version': self.version, 't_start': round(job['t0'], 2),
               'settings': {'caps': rec.get('caps'), 'objective': rec.get('objective'), 'seconds': rec.get('seconds', job['secs'])},
               'op_info': rec.get('info'), 'parents': [job['target']], 'wall_s': wall, 'cpu_s': cpu,
               'candidates': 0, 'admitted': 0, 'gain': 0.0, 'outcome': outcome}
        try:
            joins = info.get('joins') if isinstance(info.get('joins'), list) else []
            cand_ids = rec.get('cand_ids') if isinstance(rec.get('cand_ids'), list) else None
            nurs = op in self.generators or tm['operator'] in self.generators or bool((tm.get('operator_settings') or {}).get('nursery'))
            files = sorted(jd.glob('cand-*.bfx')) if jd.is_dir() else []
            for k, f in enumerate(files):
                try:
                    c = core.from_kernel(f.read_text(), f.stem); ident = cid(c); m = metrics(c)
                except Exception as e:
                    outcome.append({'cand': f.name, 'metrics': None, 'status': 'rejected: unreadable candidate: %r' % (e,), 'id': None, 'gain': 0.0})
                    continue
                if cand_ids is not None and (k >= len(cand_ids) or cand_ids[k] != ident):
                    outcome.append({'cand': f.name, 'metrics': m, 'status': 'rejected: not the candidate listed in record.json', 'id': None, 'gain': 0.0})
                    continue
                parents = [job['target']]
                settings = {'nursery': nurs, 'caps': rec.get('caps'), 'objective': rec.get('objective'),
                            'seconds': rec.get('seconds', job['secs']), 'script': job['script'], 'script_sha': job['script_sha'],
                            'scheduler_version': self.version}
                if status != 'ok': settings['job_status'] = status       # lineage completed from the launch, flagged
                if len(joins) == len(files) and isinstance(joins[k], dict) and 'front' in joins[k] and 'back' in joins[k]:
                    parents = [joins[k]['front'], joins[k]['back']]; settings.update(joins[k])
                for k2 in ('caps', 'lowered', 't_last_improvement', 'kernel_bin', 'relaxed_caps'):
                    if info.get(k2) is not None: settings[k2] = info[k2]
                st, r, g = self.ar.admit(c, parents=parents, operator=op, settings=settings, seed=job['seed'],
                                         run_id=job['run_id'], code_version=version, cpu_s=cpu,
                                         wall_s=rec.get('wall_s', wall), slack=GEN_SLACK if nurs else None)
                outcome.append({'cand': f.name, 'metrics': m, 'status': st, 'id': r['id'] if r else None, 'gain': g})
                if st == 'admitted':
                    gain += g; self.fb.add_circuit(c, r['id']); self.last_admit = r['t_admit']
                    if g > 0: self.renew_caps(tuple(m))
                    self.log(ev='admit', run_id=job['run_id'], op=op, id=r['id'], m=m, gain=g, parents=parents)
        except Exception as e:                              # the run file is written whatever happens
            run['finish_error'] = repr(e); self.log(ev='finish-error', run_id=job['run_id'], error=repr(e))
        if self.fb.dirty and time.time() - self.last_fb_save > FB_SAVE_S:
            self.fb.save(); self.last_fb_save = time.time()
        # ---- bandit and failure accounting ----
        h = self.hist.setdefault(op, []); h.append((cpu, gain)); del h[:-WINDOW]
        if status in ('failed', 'timeout'):
            self.fail[op] = self.fail.get(op, 0) + 1
            self.log(ev='job-' + status, run_id=job['run_id'], op=op, returncode=rc, error=rec_error or rec.get('error'))
            if self.fail[op] >= FAIL_LIMIT:
                self.suspended[op] = time.time() + SUSPEND_S; self.fail[op] = 0
                self.log(ev='op-suspended', op=op, seconds=SUSPEND_S, reason='%d failures in a row' % FAIL_LIMIT)
        elif status == 'ok':
            self.fail[op] = 0
        mark = None
        if op == 'join' and status == 'ok' and isinstance(info.get('joined_through'), (int, float)):
            mark = max(self.join_mark.get(job['target'], 0.0), float(info['joined_through'])); self.join_mark[job['target']] = mark
        run.update({'candidates': len(outcome), 'admitted': sum(1 for o in outcome if o['status'] == 'admitted'), 'gain': gain})
        atomic_write(self.dir / 'runs' / (job['run_id'] + '.json'), json.dumps(run, indent=1, default=str))
        with open(self.dir / 'stats.jsonl', 'a') as f:
            f.write(json.dumps({'run_id': job['run_id'], 'op': op, 'cls': acls(tm['A']), 'cpu_s': cpu, 'target': job['target'],
                                'tm': [tm['A'], tm['AD'], tm['G'], tm['GD']],
                                'seed': job['seed'], 'status': status, 'join_mark': mark,
                                'admitted': run['admitted'], 'gain': gain, 'ts': round(time.time(), 1)}) + '\n')

    def write_front(self):
        fr = []
        for i in self.ar.front_ids():
            r = self.ar.rec[i]
            fr.append({'id': i, 'm': [r['A'], r['AD'], r['G'], r['GD']], 'operator': r['operator'], 'parents': r['parents'],
                       'pub_new': r.get('pub_new'), 'run_id': r.get('run_id')})
        fr.sort(key=lambda d: d['m'])
        atomic_write(self.dir / 'front.json', json.dumps(fr, indent=0))

    def run(self):
        end = self.end = time.time() + self.args.hours * 3600
        self.init_cpus()
        running = self.running; last_front = 0; last_ctl = 0
        signal.signal(signal.SIGTERM, lambda s, f: setattr(self, 'stop', 'SIGTERM'))
        signal.signal(signal.SIGINT, lambda s, f: setattr(self, 'stop', 'SIGINT'))
        self.log(ev='start', gain=self.args.gain, target_mode=self.args.target_mode, join_mode=self.args.join_mode,
                 tuple_caps=self.tuple_caps, campaign=self.uid, cpus=self.cpus, ops=self.ops, seconds=self.secs, eps=self.args.eps, version=self.version,
                 archive=len(self.ar.rec), cells=len(self.ar.cells), front=len(self.ar.front()), last_run=self.nrun)
        while running or (time.time() < end and not self.stop):
            now = time.time()
            if now - last_ctl > 30:                         # before the first launch: control.json may change the CPU set
                last_ctl = now
                try:
                    self.control()
                except Exception as e:
                    self.log(ev='control-error', error='control(): %r' % (e,))
            for j in list(running):
                if j['p'].poll() is None:
                    if self.stop: self.kill(j, 'stopped')
                    elif now - j['t0'] > j.get('limit', self.secs.get(j['op'], 90.0) * KILL_FACTOR + KILL_GRACE): self.kill(j, 'timeout')
                    continue
                running.remove(j)
                if j['cpu'] in self.cpus and j['cpu'] not in self.free: self.free.append(j['cpu'])
                try:
                    self.finish(j)
                except Exception as e:     # never lose the loop; the job dir stays as evidence
                    self.log(ev='finish-error', run_id=j['run_id'], error=repr(e))
            while self.free and time.time() < end and not self.stop:
                # busy: tuple keys and ids (a subclass that overrides launch may test ids)
                busy = {x.get('key', x['target']) for x in running} | {x['target'] for x in running}
                j = self.launch(self.free[0], busy)
                if j is None: break
                self.free.pop(0); running.append(j)
            if time.time() - last_front > 300:
                try:
                    self.write_front()
                except Exception as e:
                    self.log(ev='front-error', error=repr(e))
                last_front = time.time()
            time.sleep(0.5 if not self.stop else 0.1)
        self.fb.save(); self.write_front()
        self.log(ev='end', reason=self.stop or 'time', archive=len(self.ar.rec), cells=len(self.ar.cells), front=len(self.ar.front()))


def parse_caps_arg(text):
    out = {}
    for kv in (text or '').split(','):
        if kv.strip():
            k, v = kv.split('='); out[k.strip()] = int(v)
    return out


def parser():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True)
    ap.add_argument('--cpus', default='auto', help="CPU list such as 4,5,8-11; default: the CPU affinity of this process")
    ap.add_argument('--cpu-allow', help='hard limit for --cpus and for control.json "cpus" (default: the start set)')
    ap.add_argument('--hours', type=float, default=1.0); ap.add_argument('--seed-list')
    ap.add_argument('--ops', default='polish,pull,join,trb'); ap.add_argument('--seconds')
    ap.add_argument('--eps', type=float, default=0.25); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--seed-only', action='store_true')
    ap.add_argument('--near', type=float, default=0.0,
                    help='probability that polish/pull/trb target a near-front cell minimum instead of a front circuit')
    ap.add_argument('--near-gap', type=int, default=3)
    ap.add_argument('--nursery', type=float, default=0.0, help='probability that polish/pull/trb target a generator-made cell minimum')
    # review 5 changes of behaviour, each with its old mode (the 2026-11-14 campaigns ran legacy / id / legacy / no caps)
    ap.add_argument('--gain', choices=('value', 'legacy'), default='value', help='archive.Archive.gain rule')
    ap.add_argument('--target-mode', choices=('tuple', 'id'), default='tuple', help='attempts counted per (A, AD, G, GD) tuple or per circuit id')
    ap.add_argument('--join-mode', choices=('incremental', 'legacy'), default='incremental',
                    help='incremental: one join pass per (target, archive state) over all cell members; legacy: front-first 300 partners every time')
    ap.add_argument('--tuple-caps', default='polish=2,pull=3',
                    help="jobs per tuple after which an operator stops choosing it (with --target-mode tuple); '' for none")
    ap.add_argument('--cap-renew', choices=('never', 'box'), default='never',
                    help='box: a new front tuple inside the cap box (A, AD, GD) of a front tuple renews that tuple\'s caps')
    ap.add_argument('--cap-renew-max', type=int, default=3, help='renewals per (operator, tuple) with --cap-renew box')
    return ap


def main(argv=None):
    args = parser().parse_args(argv)
    s = Scheduler(args)
    if args.seed_list:
        s.seed(Path(args.seed_list).read_text().split())
    if not args.seed_only:
        s.run()


if __name__ == '__main__':
    main()
