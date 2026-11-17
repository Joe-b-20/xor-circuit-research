#!/usr/bin/env python3
"""Hub scheduler: one shared archive, operator jobs chosen by a fixed priority on new work (default) or by a bandit.

    python3 search/nonlinear/boolflux/hub/scheduler.py --dir CAMPAIGN [--cpus 4,5,6,7] --hours H [--seed-list FILES]
        [--ops polish,pull,join,trb] [--seconds polish=90,pull=90,join=60,trb=30] [--policy priority|bandit]
        [--seed 1] [--cpu-allow 4-11] [--ingest-every 60] [--join-batch 8] [--join-cpus 1]

Loop: for every free CPU choose an operator and a target, run op_<name>.py pinned to that CPU, then verify
and admit its candidates (archive.Archive.admit: cell rule, structure check, two verifiers).  The loop
sleeps until a job exits (SIGCHLD) or 1 s passes.

--policy priority (default since 2026-11-16; FINDINGS-U2 sections 2, 5): the first level with a target wins
  1 join     front circuits with archive members they have not been joined with (incremental marks), A, AD
             ascending, newest first, up to --join-batch targets per job, at most --join-cpus join jobs at once
             and at most --join-share of the CPU time over the last 10 minutes (every admission reopens every
             target, so join would otherwise hold a CPU without pause)
  2 fresh    the first polish, then the first pull, of a front tuple (A, AD ascending, newest first)
  2b repeat  polish / pull on front tuples under the tuple caps (fewest jobs first; --variants-first: after level 5)
  3 variant  the first polish / pull of each structure (circuit) of a front tuple that has had its first jobs
  4 near     the first polish / pull of each member of a cell within --near-gap gates of a dominating front point
  5 other    the first job of every other operator on a front tuple (trb at most once per tuple), and the first
             polish / pull of generator-made cell minima
  6 repeat   polish / pull (and other operators except join and trb) on front tuples: fewest jobs on the tuple
             first, under the tuple caps before over them, A, AD ascending (no CPU idles while a front exists)
  The levels' sizes and the rule are in each job's decision record.
--policy bandit (until 2026-11-16): epsilon-greedy on the recent gain / CPU-s of each operator, fresh tuples
  first, fallback to the other operators and finally to any tuple over its caps.
Gain of an admission (archive.Archive.gain, value rule): 8 for a lower A at a known AD, 4 for a new AND depth,
1 + 0.5 (d - 1) for d fewer gates in the cap box (d <= 6), 0.5 for a new gate depth; 0 when dominated.
Kernel options (2026-11-17): --kopt 'polish,pull:KEY=VAL,...' passes kernel options (ops.KOPT_KEYS) to every job of
those operators, --kopt-first 'polish:KEY=VAL,...' only to jobs chosen at a first-job level (--kopt-first-levels,
default fresh, variant, near, other); none by default (the 08012e1 kernel settings).  Each job event records kopt.
Every job: DIR/runs/<run_id>.json (code version, seed, settings, parents, timing, status, outcome);
DIR/stats.jsonl one line per job; DIR/front.json every 5 minutes.

CPUs.  One job per CPU.  --cpus defaults to the CPU affinity mask of the scheduler process (e.g. set
with taskset), so the list is written once.  An explicit --cpus outside that
mask is refused unless --cpu-allow names it.  --cpu-allow (default: the start set) is the hard
limit: control.json "cpus" sets the active set exactly (it can shrink and grow), but never beyond
the allow list.  The active set is written to DIR/cpus.json on every change.

Run ids are '<campaign uid>.r<number>-<op>' (DIR/campaign.json holds the uid), unique across
campaigns, so an archive copied into another campaign keeps unambiguous lineage.

Function: --function aes-sbox (default) or aes-invsbox, kept in DIR/campaign.json (a restart with
another function is refused); the operators inherit it ($BOOLFLUX_FUNCTION).  Run records
(runlog.py): DIR/sessions/<UTC>-<pid>/run.json + events.jsonl.gz per scheduler start (command, git
state, seeds, settings, seed files, kernel, host; every job and admission), and JOBDIR/run.json per
job; git diffs of a dirty tree go once to DIR/runlog/.  Pinning: taskset, else os.sched_setaffinity.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import select
import signal
import subprocess
import sys
import time
from pathlib import Path

HUBDIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HUBDIR.parents[1]))
from boolflux import aesfn, core, runlog   # noqa: E402
from boolflux.hub.common import load, code_version, metrics, cid, file_sha, atomic_write   # noqa: E402
from boolflux.hub.archive import Archive, GEN_SLACK, GAIN_RULE   # noqa: E402
from boolflux.hub.funcbank import FuncBank   # noqa: E402
from boolflux.hub.ops import kernel_bin, kernel_record   # noqa: E402

DEFAULT_SECONDS = {'polish': 90, 'pull': 90, 'join': 60, 'trb': 30, 'osc': 90, 'gen_inv3': 60,
                   'gen_bottom': 60, 'gen_skel': 60, 'linres': 30, 'gen_joinplus': 90}
# operator name -> script (common CLI); the operators beyond the four basic ones live in hub/ops/
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
KERNEL_OPS = ('polish', 'pull')          # the operators of the fresh / variant / near levels (--policy priority)
WAIT_S = 1.0                             # longest sleep of the main loop (a job exit wakes it at once)
JOIN_WINDOW_S = 600.0                    # window of --join-share


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
        self.function = self._function()
        self.scripts = dict(SCRIPTS); self.generators = set(GENERATORS)
        self.ar = Archive(self.dir, gain_mode=args.gain); self.fb = FuncBank(self.dir)
        self.ops = args.ops.split(',')
        bad = [o for o in self.ops if o not in self.scripts]
        if bad: raise SystemExit('unknown operators %s (known: %s)' % (bad, sorted(self.scripts)))
        self.secs = dict(DEFAULT_SECONDS)
        for kv in (args.seconds or '').split(','):
            if kv: k, v = kv.split('='); self.secs[k] = float(v)
        self.kopt = parse_kopt_arg(args.kopt); self.kopt_first = parse_kopt_arg(args.kopt_first)   # op -> kernel options
        self.kopt_levels = {x.strip() for x in (args.kopt_first_levels or '').split(',') if x.strip()}
        self.hist = {o: [] for o in self.ops}            # recent (cpu_s, gain)
        self.attempts = {}                                 # (op, target key) -> n; key = (A, AD, G, GD), or the id with --target-mode id
        self.sattempts = {}                                # (op, structure key) -> n (--policy priority: first job per structure)
        self._recent = []; self._mono0 = time.monotonic()  # (monotonic end, op, CPU s) of the jobs of the last JOIN_WINDOW_S
        self._near_cache = (None, [])
        self.tuple_caps = parse_caps_arg(args.tuple_caps)  # op -> jobs per tuple before it stops being chosen
        self.cap_base = {}; self.renewals = {}             # (op, tuple) -> attempts at the last renewal / renewals so far
        self.join_mark = {}                                # target id -> t_admit through which it was joined with every partner
        self.fail = {}; self.suspended = {}                # op -> consecutive failures / suspended until
        self.version = code_version()
        self.uid = self._campaign_uid()
        self.nrun = self._last_run_number()
        self.rng = random.Random('%s/%d' % (args.seed, self.nrun))   # a restart does not replay the same jobs
        kb = kernel_bin(self.dir)
        os.environ['BOOLFLUX_RUNLOG_STORE'] = str((self.dir / 'runlog').resolve())   # one copy of a git diff per campaign
        sess = self.dir / 'sessions' / ('%s-%d' % (runlog.utc().replace(':', ''), os.getpid()))
        self.runlog = runlog.RunLog(sess, 'hub.scheduler', argv=getattr(args, 'argv', None),
                                    seeds={'seed': args.seed, 'rng': "random.Random('%s/%d' % (seed, last run number))",
                                           'last_run_number': self.nrun,
                                           'jobs': 'each job gets rng.randrange(1, 2^30); every job is an event'},
                                    config=dict({k: v for k, v in vars(args).items() if k != 'argv'}, seconds_resolved=self.secs,
                                                campaign=self.uid, code_version=self.version),
                                    budget_s=args.hours * 3600, function=self.function)
        if kb: self.runlog.add_kernel(kb, **kernel_record(kb))
        self.ctl_mtime = None; self.ctl_bad = None
        self.ad3_share = 0.0; self.ingest_globs = []; self.ingested = set(); self.last_ingest = 0
        self.cpus = []; self.free = []; self.running = []; self.allow = set(); self.stop = None
        self.end = time.time() + args.hours * 3600; self.pending_cpus = None
        self.last_admit = max((r['t_admit'] for r in self.ar.rec.values()), default=0.0)
        self.last_fb_save = time.time()
        # instrumentation: per-operator counters of the current summary window, idle CPU time, last idle state
        self.win = {}; self.idle_cpu_s = 0.0; self.free_since = {}; self._idle_state = None; self._idle_why = None
        self.t_summary = time.time(); self._dec = {}; self._tdec = {}; self._fdec = None; self._launch_dec = None
        for e in self.ar.load_errors: self.log(ev='archive-load-error', what=e)
        if self.ar.cells_repaired:
            self.log(ev='cells-repaired', cells=len(self.ar.cells)); self.ar._save_cells()
        if self.ar.index_missing: self.ar.write_index()
        n = self.ar.dedupe_legacy()
        if n: self.log(ev='cells-deduplicated', dropped_members=n, cells=len(self.ar.cells))
        self.reclean()
        self.restore()

    def reclean(self):
        """Records admitted before candidates were cleaned (before 2026-11-14): each record whose cleaned
        circuit has other metrics is logged (event legacy-clean) and the cleaned circuit is admitted
        as a new record, operator 'clean', parent = the old record.  No file is rewritten; done
        once per record (archive/cleaned.json)."""
        def one(i, m0, m1, st, nid, g):
            self.log(ev='legacy-clean', id=i, recorded=m0, cleaned=m1, status=st, new_id=nid, gain=g)
            if st == 'admitted':
                self.fb.add_circuit(self.ar.circuit(nid), nid); self.last_admit = max(self.last_admit, self.ar.rec[nid]['t_admit'])
        n = self.ar.reclean_legacy(self.version, log=one)
        if n:
            self.log(ev='legacy-cleaned', records=n); self.fb.save()

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
            atomic_write(f, json.dumps({'uid': uid, 'created': time.time(), 'dir': str(self.dir.resolve()),
                                        'function': self.function}, indent=1))
            return uid

    def _function(self):
        """--function, checked against DIR/campaign.json (a campaign written before 2026-11-16 is aes-sbox);
        made the process's function, so every operator it starts inherits it"""
        try:
            old = json.loads((self.dir / 'campaign.json').read_text()).get('function', 'aes-sbox')
        except Exception:
            old = None
        f = aesfn.name(getattr(self.args, 'function', None) or old or 'aes-sbox')
        if old is not None and f != old:
            raise SystemExit('%s is an %s campaign (campaign.json); --function %s refused' % (self.dir, old, f))
        return aesfn.use(f)

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
        """bandit history, attempt counts (per tuple and per structure), join marks (incl. batch join jobs) from
        stats.jsonl and cap renewals from events.jsonl, so a restart neither starts the bandit cold nor repeats work
        the previous run already did.  The bandit history keeps only jobs whose gain was computed by the current
        gain rule (stats 'gain_rule'; lines written before 2026-11-16 have none and count for attempts only)."""
        sf = self.dir / 'stats.jsonl'
        n = 0; rule = GAIN_RULE[self.ar.gain_mode]
        for ln in (sf.read_text().splitlines() if sf.exists() else []):
            try:
                x = json.loads(ln); op = x['op']
            except Exception:
                continue
            if x.get('gain_rule') == rule: self.hist.setdefault(op, []).append((x.get('cpu_s') or 0.0, x.get('gain') or 0.0))
            else: self.hist.setdefault(op, [])
            tid = x.get('target'); tm = x.get('tm')
            if tid is None or tm is None:                   # line written before 2026-11-14: target is in the run file
                try:
                    rf = json.loads((self.dir / 'runs' / (x['run_id'] + '.json')).read_text())
                    tid = rf['target']; tm = rf['target_metrics']
                except Exception:
                    continue
            key = tuple(tm) if self.args.target_mode == 'tuple' else tid
            self.attempts[(op, key)] = self.attempts.get((op, key), 0) + 1; n += 1
            sk = (self.ar.rec.get(tid) or {}).get('skey') or tid
            self.sattempts[(op, sk)] = self.sattempts.get((op, sk), 0) + 1
            if x.get('join_mark') is not None: self.join_mark[tid] = max(self.join_mark.get(tid, 0.0), x['join_mark'])
            for t, v in (x.get('join_marks') or {}).items():
                if isinstance(v, (int, float)): self.join_mark[t] = max(self.join_mark.get(t, 0.0), v)
        for o in self.hist: self.hist[o] = self.hist[o][-WINDOW:]
        nr = 0
        ef = self.dir / 'events.jsonl'
        if ef.exists() and self.args.cap_renew != 'never':   # cap renewals (logged with their keys since 2026-11-16)
            with open(ef) as f:
                for ln in f:
                    if '"cap-renew"' not in ln: continue
                    try:
                        e = json.loads(ln)
                    except ValueError:
                        continue
                    for op, t, base in e.get('keys') or []:
                        k = (op, tuple(t)); self.cap_base[k] = base; self.renewals[k] = self.renewals.get(k, 0) + 1; nr += 1
        if sf.exists() or nr: self.log(ev='restored', jobs=n, join_marks=len(self.join_mark), cap_renewals=nr)

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
        self.free_since = {c: time.time() for c in self.free}
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
        self.free_since = {c: self.free_since.get(c, time.time()) for c in self.free}
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
        self.maybe_ingest()

    def maybe_ingest(self):
        """ingest every --ingest-every seconds (control.json "ingest_every"; until 2026-11-16 a fixed 1800 s, so
        conjugation circuits waited 944 s on average, U2 section 5)"""
        if self.ingest_globs and time.time() - self.last_ingest > self.args.ingest_every:
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
            every = float(c['ingest_every']) if 'ingest_every' in c else None
            tcaps = {str(k): int(v) for k, v in c['tuple_caps'].items()} if 'tuple_caps' in c else None
            gap = int(c['near_gap']) if 'near_gap' in c else None
            cpus = parse_cpus(c['cpus']) if 'cpus' in c else None
        except (TypeError, ValueError) as e:
            return 'bad value: %r' % (e,)
        if any(v <= 0 for v in secs.values()): return 'seconds must be positive'
        if every is not None and every <= 0: return 'ingest_every must be positive'
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
        if every is not None: self.args.ingest_every = every
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
                    n += 1; self.fb.add_circuit(self.ar.circuit(r['id']), r['id']); self.last_admit = r['t_admit']
                    self.log(ev='ingest', file=f, id=r['id'], m=rec_metrics(r), gain=gn)
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
            self.runlog.add_start(f, metrics=list(metrics(c)), label='seed: %s' % st, write=False)
            if st == 'admitted':
                n += 1; self.fb.add_circuit(self.ar.circuit(r['id']), r['id']); self.last_admit = r['t_admit']
            elif not st.startswith(('duplicate', 'not-better')):
                bad += 1; self.log(ev='seed-reject', file=str(f), status=st)
        self.fb.save(); self.runlog.write()
        self.log(ev='seeded', admitted=n, rejected=bad, cells=len(self.ar.cells), front=len(self.ar.front()))
        return n

    # ---- choice -----------------------------------------------------------------------------
    # Instrumentation (2026-11-16): every choice leaves its inputs in self._dec (operator choice: bandit
    # state of every operator, the epsilon draw, the mode, ties) and self._tdec (target choice: which pool,
    # how many candidates survived each filter, attempts of the chosen tuple, ties).  start_job() puts them
    # in the 'job' event of the session run record and in runs/<run_id>.json ('decision').  Recording draws
    # no random number: the choices are the same as without it.
    def score(self, op):
        h = self.hist[op][-WINDOW:]
        return (sum(g for c, g in h) + 0.5) / (sum(c for c, g in h) + 120.0)

    def bandit_state(self):
        """op -> score and the window it comes from (jobs, gain, CPU s): the bandit's inputs"""
        out = {}
        for o in self.ops:
            h = self.hist.get(o, [])[-WINDOW:]
            out[o] = {'score': round(self.score(o), 6), 'n': len(h), 'gain': round(sum(g for c, g in h), 4),
                      'cpu_s': round(sum(c for c, g in h), 1)}
        return out

    def active_ops(self):
        now = time.time()
        return [o for o in self.ops if self.suspended.get(o, 0) <= now]

    def choose_op(self):
        ops = self.active_ops()
        self._dec = d = {'bandit': self.bandit_state(), 'eps': self.args.eps,
                         'suspended': sorted(o for o in self.ops if o not in ops)}
        if not ops:
            d['mode'] = 'none'; return None, 'none'
        u = self.rng.random(); d['u'] = round(u, 4)
        if u < self.args.eps:
            op = self.rng.choice(ops); d.update(mode='explore', op=op); return op, 'explore'
        op = max(ops, key=lambda o: (self.score(o), self.rng.random()))
        top = max(self.score(o) for o in ops)
        d.update(mode='exploit', op=op, tied=sum(1 for o in ops if self.score(o) == top))
        return op, 'exploit'

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
        circuits of a cell share one count) or the circuit id (--target-mode id, as before)"""
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
        n = 0; keys = []
        for t in self.ar.front():
            if t == q or not (q[0] <= t[0] and q[1] <= t[1] and q[3] <= t[3]): continue
            for op in self.tuple_caps:
                k = (op, t)
                if self.eff_attempts(op, t) > 0 and self.renewals.get(k, 0) < self.args.cap_renew_max:
                    self.cap_base[k] = self.attempts.get(k, 0); self.renewals[k] = self.renewals.get(k, 0) + 1; n += 1
                    keys.append([op, list(t), self.cap_base[k]])
        if n: self.log(ev='cap-renew', by=list(q), renewed=n, keys=keys)     # keys: restored on a restart
        return n

    def fresh_target(self, busy):
        """a front tuple that has not had its first polish / pull yet: (op, id) or None.  A <= 31 first,
        then the newest.  New tuples get their first jobs at once instead of waiting behind old ones."""
        ops = [o for o in self.active_ops() if o in self.tuple_caps and self.tuple_caps[o] > 0]
        self._fdec = None
        if not ops or self.args.target_mode == 'id': return None
        best = None; nfresh = 0
        for i in self.ar.front_ids():
            k = self.target_key(i)
            if k in busy: continue
            todo = [o for o in ops if self.attempts.get((o, k), 0) == 0]
            if not todo: continue
            nfresh += 1
            r = self.ar.rec[i]; rank = (0 if r['A'] <= 31 else 1, -r['t_admit'])
            if best is None or rank < best[0]: best = (rank, todo[0], i)
        if best:
            self._fdec = {'mode': 'fresh', 'op': best[1], 'fresh_targets': nfresh, 'rule': 'A<=31 first, then newest',
                          'bandit': self.bandit_state()}
        return (best[1], best[2]) if best else None

    def choose_target(self, op, busy, ignore_caps=False):
        pool = self.ar.front_ids()
        d = {'op': op, 'pool': 'front', 'front': len(pool)}
        if ignore_caps: d['ignore_caps'] = True
        self._tdec = d
        if op in ('polish', 'pull', 'trb') and self.args.nursery > 0 and self.rng.random() < self.args.nursery:
            nu = [i for i in self.nursery_ids(op) if self.target_key(i) not in busy]
            d['nursery_draw'] = len(nu)
            if nu:
                d.update(pool='nursery', attempts=self.attempts.get((op, self.target_key(nu[0])), 0), rule='newest generator cell minimum')
                return nu[0]
        ad3 = self.ad3_share > 0 and self.rng.random() < self.ad3_share
        if op in ('polish', 'pull', 'trb') and self.args.near > 0 and self.rng.random() < self.args.near:
            nids = self.near_ids(); d['near_draw'] = len(nids)
            if nids: d['pool'] = 'near'
            pool = nids or pool
        if ad3:                                            # after the near choice, so that the share holds for both pools
            p3 = [i for i in pool if self.ar.rec[i]['AD'] <= 3]
            d['ad3_draw'] = len(p3)
            if p3: pool = p3; d['pool'] += '+ad3'
        d['n_pool'] = len(pool)
        ids = [i for i in pool if self.target_key(i) not in busy]
        d['n_not_busy'] = len(ids)
        if not ignore_caps:
            ids = [i for i in ids if not self.capped(op, self.target_key(i))]; d['n_under_cap'] = len(ids)
        if op == 'join' and self.args.join_mode == 'incremental':
            # a join of X with partners it has already met is the same computation: one pass per (target, archive state)
            ids = [i for i in ids if self.join_mark.get(i, 0.0) < self.last_admit]; d['n_unjoined'] = len(ids)
        if not ids:
            d['empty'] = True; return None
        self.rng.shuffle(ids)                              # ties random (also which of a tuple's circuits is used)
        if self.args.target_mode == 'id':
            t = min(ids, key=lambda i: self.attempts.get((op, i), 0))
            a0 = self.attempts.get((op, t), 0)
            d.update(attempts=a0, tied=sum(1 for i in ids if self.attempts.get((op, i), 0) == a0), rule='fewest attempts (id)')
            return t
        kf = lambda i: (self.eff_attempts(op, self.target_key(i)), 0 if self.ar.rec[i]['A'] <= 31 else 1)
        t = min(ids, key=kf); k0 = kf(t)
        d.update(attempts=k0[0], tied=sum(1 for i in ids if kf(i) == k0), rule='fewest attempts on the tuple, A<=31 first, ties random')
        return t

    # ---- --policy priority (2026-11-16) ----------------------------------------------------------
    def skey(self, i):
        return (self.ar.rec.get(i) or {}).get('skey') or i

    def near_members(self):
        """(G above the dominating front point, id) of every member of a cell that is not on the front and lies
        within --near-gap gates of a dominating front point (cached per archive state)"""
        st = (len(self.ar.rec), self.last_admit, self.args.near_gap)
        if self._near_cache[0] == st: return self._near_cache[1]
        fr = self.ar.front(); frs = set(fr); out = []
        for k, ids in self.ar.cells.items():
            if not ids: continue
            m = (k[0], k[1], self.ar.rec[ids[0]]['G'], k[2])
            if m in frs: continue
            doms = [q[2] for q in fr if all(a <= b for a, b in zip(q, m))]
            if doms and m[2] - min(doms) <= self.args.near_gap: out += [(m[2] - min(doms), i) for i in ids]
        self._near_cache = (st, out)
        return out

    def busy_set(self):
        """tuple keys, ids (a subclass that overrides launch may test ids) and structure keys of the running jobs'
        targets.  --policy priority leaves join jobs out (priority_choice keeps its own set of join targets: a join
        does not keep a kernel job off its targets); --policy bandit counts them, as before."""
        pr = getattr(self.args, 'policy', 'priority') == 'priority'
        jobs = [x for x in self.running if not (pr and x.get('op') == 'join')]
        return ({x.get('key', x['target']) for x in jobs} | {x['target'] for x in jobs}
                | {b for x in jobs for b in (x.get('batch') or ())} | {x['skey'] for x in jobs if x.get('skey')})

    def join_share(self):
        """join's share of the CPU time of the last JOIN_WINDOW_S (finished jobs + elapsed time of running join jobs),
        over at least 120 s of all active CPUs"""
        now = time.monotonic()
        self._recent = [x for x in self._recent if x[0] >= now - JOIN_WINDOW_S]
        used = sum(c for t, o, c in self._recent if o == 'join') + sum(now - j['m0'] for j in self.running if j.get('op') == 'join' and j.get('m0'))
        span = max(120.0, min(JOIN_WINDOW_S, now - self._mono0))
        return used / (max(1, len(self.cpus)) * span)

    def priority_choice(self, busy):
        """(op, target id, level, batch ids) of the first level with work (module docstring), or None.  The
        decision (level sizes counted so far, rule, attempts) is left in self._dec."""
        ops = self.active_ops(); rec = self.ar.rec
        d = self._dec = {'policy': 'priority', 'levels': {}, 'suspended': sorted(o for o in self.ops if o not in ops)}
        if not ops:
            d['mode'] = 'none'; return None
        lv = d['levels']; fr = self.ar.front_ids(); sk = self.skey
        kops = [o for o in ops if o in KERNEL_OPS]
        vr = lambda i: (rec[i]['A'], rec[i]['AD'], -rec[i]['t_admit'], i)
        free_t = lambda i: i not in busy and self.target_key(i) not in busy and sk(i) not in busy   # tuple not running
        free_i = lambda i: i not in busy and sk(i) not in busy                                      # circuit not running

        def pick(level, op, i, rule, n, batch=()):
            d.update(mode='priority', level=level, op=op, rule=rule, n_level=n,
                     attempts=self.attempts.get((op, self.target_key(i)), 0), struct_attempts=self.sattempts.get((op, sk(i)), 0))
            return op, i, level, list(batch)
        # 1 join
        if 'join' in ops and self.args.join_mode == 'incremental':
            jbusy = {t for j in self.running if j['op'] == 'join' for t in [j['target']] + list(j.get('batch') or [])}
            todo = sorted((i for i in fr if self.join_mark.get(i, 0.0) < self.last_admit and i not in jbusy), key=vr)
            lv['join'] = len(todo)
            share = self.join_share(); d['join_share'] = round(share, 4)
            if todo and len([j for j in self.running if j['op'] == 'join']) < max(1, self.args.join_cpus) and share <= self.args.join_share:
                b = todo[:max(1, self.args.join_batch)]
                return pick('join', 'join', b[0], 'front circuits with unmet partners; A, AD ascending, newest first; batched', len(todo), b[1:])
        # 2 fresh
        best = None; n = 0
        for i in fr:
            if not free_t(i): continue
            k = self.target_key(i); todo = [o for o in kops if self.attempts.get((o, k), 0) == 0]
            if not todo: continue
            n += 1
            if best is None or vr(i) < best[0]: best = (vr(i), todo[0], i)
        lv['fresh'] = n
        if best: return pick('fresh', best[1], best[2], 'first polish / pull of a front tuple; A, AD ascending, newest first', n)
        def repeat(under_only):
            best = None; n = 0
            rops = [o for o in ops if o not in ('join', 'trb')]
            for i in fr:
                if not free_t(i): continue
                k = self.target_key(i)
                for o in rops:
                    e = self.eff_attempts(o, k); cap = self.tuple_caps.get(o)
                    over = cap is not None and e >= cap
                    if over and (under_only or (self.args.repeat_max is not None and self.attempts.get((o, k), 0) >= self.args.repeat_max)): continue
                    n += 1; r = (over, e, rec[i]['A'], rec[i]['AD'], self.sattempts.get((o, sk(i)), 0), -rec[i]['t_admit'], i, o)
                    if best is None or r < best[0]: best = (r, o, i)
            lv['repeat-under-cap' if under_only else 'repeat'] = n
            if best:
                lvl = 'repeat-over-cap' if best[0][0] else 'repeat'
                return pick(lvl, best[1], best[2], 'fewest jobs on the tuple (under the caps first); A, AD ascending', n)
            return None
        # 2b repeats under the tuple caps (second polish, second and third pull of a front tuple) before the
        # structure variants (2026-11-17: in the inverse late phase variants-first gave 6 front adds in 2.98 CPU-h,
        # the old scheduler's repeats 17 in 2.95)
        if not self.args.variants_first:
            ch = repeat(True)
            if ch: return ch
        # 3 variant, 4 near: first polish / pull per structure
        for level, pool, rule in (('variant', [(0, i) for i in fr], 'first polish / pull of each structure of a front tuple'),
                                  ('near', None, 'first polish / pull of each member of a near-front cell (within --near-gap)')):
            if pool is None: pool = self.near_members()
            best = None; n = 0
            for gap, i in pool:
                if not free_i(i): continue
                todo = [o for o in kops if self.sattempts.get((o, sk(i)), 0) == 0]
                if not todo: continue
                n += 1; r = (rec[i]['A'], rec[i]['AD'], gap, -rec[i]['t_admit'], i)
                if best is None or r < best[0]: best = (r, todo[0], i)
            lv[level] = n
            if best: return pick(level, best[1], best[2], rule + '; A, AD ascending, newest first', n)
        # 5 other: first job of the other operators per front tuple (trb once), first polish / pull of nursery minima
        best = None; n = 0
        oops = [o for o in ops if o not in KERNEL_OPS and o != 'join']
        for i in fr:
            if not free_t(i): continue
            k = self.target_key(i)
            for o in oops:
                if self.attempts.get((o, k), 0) == 0:
                    n += 1; r = vr(i) + (o,)
                    if best is None or r < best[0]: best = (r, o, i)
        if kops and (self.generators & set(ops) or self.args.nursery > 0):
            frs = set(fr)
            for k, ids in self.ar.cells.items():
                if not ids or ids[0] in frs or not free_i(ids[0]): continue
                r0 = rec[ids[0]]
                if r0['operator'] not in self.generators and not (r0.get('operator_settings') or {}).get('nursery'): continue
                todo = [o for o in kops if self.sattempts.get((o, sk(ids[0])), 0) == 0]
                if todo:
                    n += 1; r = vr(ids[0]) + (todo[0],)
                    if best is None or r < best[0]: best = (r, todo[0], ids[0])
        lv['other'] = n
        if best: return pick('other', best[1], best[2], 'first job of the other operators per front tuple; first polish / pull of nursery minima', n)
        # 6 repeat (over the caps; the repeats under the caps came after fresh unless --variants-first)
        ch = repeat(False)
        if ch: return ch
        d['mode'] = 'empty'
        return None

    # ---- jobs -------------------------------------------------------------------------------
    def launch(self, cpu, busy):
        self._idle_why = None
        if getattr(self.args, 'policy', 'priority') == 'priority':
            ch = self.priority_choice(busy); dec = dict(self._dec)
            if ch is None:
                self._idle_why = ('no active operator (suspended: %s)' % dec.get('suspended') if dec.get('mode') == 'none'
                                  else 'no target for any operator'); return None
            op, tid, why, batch = ch
            dec['why'] = why
            if op == 'join' and self.args.join_mode == 'incremental':
                dec['batch'] = len(batch)
                dec['join_partners'] = sum(1 for t in [tid] + batch for ids in self.ar.cells.values() for i in ids
                                           if i != t and self.ar.rec[i]['t_admit'] > self.join_mark.get(t, 0.0))
            self._launch_dec = dec
            j = self.start_job(cpu, op, why, tid, batch=batch)
            if j is None: self._idle_why = 'less than %.0f s left' % MIN_JOB_S
            return j
        fresh = self.fresh_target(busy)
        if fresh is not None:
            op, tid = fresh; why = 'fresh'; dec = dict(self._fdec or {})
        else:
            op, why = self.choose_op()
            dec = dict(self._dec)
            if op is None:
                self._idle_why = 'no active operator (suspended: %s)' % dec.get('suspended'); return None
            tid = self.choose_target(op, busy); tried = [self._tdec]
            if tid is None:                                # e.g. nothing new to join, or every tuple at its cap: try the other operators
                for o in sorted((o for o in self.active_ops() if o != op), key=lambda o: -self.score(o)):
                    tid = self.choose_target(o, busy); tried.append(self._tdec)
                    if tid is not None: op, why = o, why + '-fallback'; break
            if tid is None:                                # everything capped: a CPU must not idle, least-attempted tuple first
                for o in sorted(self.active_ops(), key=lambda o: -self.score(o)):
                    tid = self.choose_target(o, busy, ignore_caps=True); tried.append(self._tdec)
                    if tid is not None: op, why = o, 'over-cap'; break
            dec['target_choice'] = tried[-1]
            if len(tried) > 1: dec['targets_tried'] = [{k: t.get(k) for k in ('op', 'pool', 'n_pool', 'n_not_busy', 'n_under_cap', 'n_unjoined', 'ignore_caps')} for t in tried[:-1]]
            if tid is None:
                self._idle_why = 'no target for any operator'; return None
        dec['why'] = why
        if op == 'join' and self.args.join_mode == 'incremental':     # partners the job will get (ops.join_partners)
            mk = self.join_mark.get(tid, 0.0)
            dec['join_partners'] = sum(1 for ids in self.ar.cells.values() for i in ids if i != tid and self.ar.rec[i]['t_admit'] > mk)
        self._launch_dec = dec
        j = self.start_job(cpu, op, why, tid)
        if j is None: self._idle_why = 'less than %.0f s left' % MIN_JOB_S
        return j

    def job_kopt(self, op, why):
        """kernel options of a job of `op` chosen at level `why`: --kopt, then --kopt-first when why is a first-job
        level (--kopt-first-levels); {} for non-kernel operators and by default"""
        d = dict(self.kopt.get(op) or {})
        if why in self.kopt_levels: d.update(self.kopt_first.get(op) or {})
        return d

    def start_job(self, cpu, op, why, tid, extra=(), env=None, batch=()):
        """Start operator `op` on archive member `tid`, pinned to `cpu`; returns the job dict, or None when
        too little time is left.  Everything a job needs for its run record is set here (unique run id, fresh job
        directory, seconds cut to the end of the campaign, own process group, kill limit, script hash, join
        mark), so a subclass that chooses (op, target) its own way should call this instead of building the
        command itself.  extra: more command-line arguments (e.g. ['--caps', '28,4,22']); env: environment;
        batch: more join targets (--batch, each with its own join mark)."""
        end = self.end
        secs = min(self.secs[op], end - time.time())       # a job never runs past the end of the campaign
        if secs < MIN_JOB_S: return None
        key = self.target_key(tid); batch = [b for b in batch if b != tid and b in self.ar.rec]
        for t in [tid] + batch:
            k = self.target_key(t); self.attempts[(op, k)] = self.attempts.get((op, k), 0) + 1
            k = (op, self.skey(t)); self.sattempts[k] = self.sattempts.get(k, 0) + 1
        while True:                                        # a job directory is never reused
            self.nrun += 1
            run_id = '%s.r%05d-%s' % (self.uid, self.nrun, op)
            jd = self.dir / 'jobs' / run_id
            if not jd.exists() and not (self.dir / 'runs' / (run_id + '.json')).exists(): break
        seed = self.rng.randrange(1, 1 << 30)
        script = self.scripts[op]
        cmd = [sys.executable, str(script), '--archive', str(self.dir),
               '--in', tid, '--seed', str(seed), '--seconds', str(round(secs, 1)), '--out', str(jd)]
        since = None
        if op == 'join' and self.args.join_mode == 'incremental':
            since = self.join_mark.get(tid, 0.0); cmd += ['--since', repr(since)]
            if batch: cmd += ['--batch', ','.join('%s:%r' % (b, self.join_mark.get(b, 0.0)) for b in batch)]
        kopt = self.job_kopt(op, why)
        if kopt: cmd += ['--kopt', ','.join('%s=%s' % kv for kv in sorted(kopt.items()))]   # before extra: a subclass's own --kopt wins
        cmd += [str(x) for x in extra]
        cmd, pre = runlog.pin(cmd, cpu)                    # taskset -c CPU, else os.sched_setaffinity in the child
        if env is not None: env = dict(env, **{k: v for k, v in os.environ.items() if k in (aesfn.ENV, 'BOOLFLUX_RUNLOG_STORE')})
        lf = open(self.dir / 'jobs' / (run_id + '.log'), 'w')
        t_spawn = time.time()
        p = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT, start_new_session=True, env=env, preexec_fn=pre)
        dec = getattr(self, '_launch_dec', None); self._launch_dec = None      # None: a subclass chose (op, target) itself
        tr = self.ar.rec.get(tid) or {}
        self.runlog.event('job', run_id=run_id, op=op, why=why, target=tid, seed=seed, cpu=cpu, seconds=round(secs, 1),
                          pinning=runlog.pinning(), target_metrics=[tr.get('A'), tr.get('AD'), tr.get('G'), tr.get('GD')],
                          target_attempts=self.attempts.get((op, key)), spawn_s=round(time.time() - t_spawn, 4),
                          running=len(self.running), decision=dec, kopt=kopt or None)
        return {'p': p, 'lf': lf, 'op': op, 'why': why, 'target': tid, 'run_id': run_id, 'jd': jd, 'seed': seed,
                'cpu': cpu, 't0': time.time(), 'cmd': cmd, 'key': key, 'secs': secs, 'script': str(script), 'script_sha': file_sha(script),
                'limit': secs * KILL_FACTOR + KILL_GRACE, 'since': since, 'pinning': runlog.pinning(), 'decision': dec,
                'm0': time.monotonic(), 'spawn_s': round(time.time() - t_spawn, 4), 'batch': batch, 'skey': self.skey(tid)}

    @staticmethod
    def reap(job):
        """Popen.poll() with the child's resource use: os.wait4(WNOHANG) reaps the operator and keeps its
        rusage (CPU of the operator and every child it waited for, peak RSS) and the time the exit was
        seen (wall and monotonic) in the job dict; the return code is the same as poll()'s."""
        p = job['p']
        if p.returncode is not None: return p.returncode
        try:
            pid, status, ru = os.wait4(p.pid, os.WNOHANG)
        except ChildProcessError:                  # already reaped elsewhere
            return p.poll()
        if pid == 0: return None
        p.returncode = os.waitstatus_to_exitcode(status)
        job['t_exit'] = time.time(); job['mono_exit'] = time.monotonic()
        job['proc_cpu_s'] = round(ru.ru_utime + ru.ru_stime, 3); job['proc_maxrss_kb'] = ru.ru_maxrss
        return p.returncode

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
        t_fin0 = time.monotonic(); admit_s = 0.0
        job['lf'].close()
        jd = job['jd']; op = job['op']; tm = self.ar.rec[job['target']]; rc = job['p'].returncode
        # (a subclass may build its own job dict: everything beyond the 2026-11-14 keys has a default)
        job.setdefault('secs', self.secs.get(op)); job.setdefault('script', str(self.scripts.get(op, SCRIPTS.get(op))))
        job.setdefault('script_sha', file_sha(job['script']))
        # durations on the monotonic clock (time.time() stepped back up to 68 s on this host, U2 section 7)
        wall = round(time.monotonic() - job['m0'], 2) if job.get('m0') else round(time.time() - job['t0'], 2)
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
               'applicable': info.get('applicable'), 'na_reason': info.get('na_reason'),
               'candidates': 0, 'admitted': 0, 'gain': 0.0, 'outcome': outcome,
               'run_record': str(jd / 'run.json') if (jd / 'run.json').exists() else None,
               'function': self.function, 'pinning': job.get('pinning'), 'decision': job.get('decision')}
        try:
            joins = info.get('joins') if isinstance(info.get('joins'), list) else []
            cand_ids = rec.get('cand_ids') if isinstance(rec.get('cand_ids'), list) else None
            # nursery slack for one generation (2026-11-16): a generator's output and the jobs on it, not their
            # descendants (the flag was inherited without end: 516 records in the 11-14 long run, U2 section 6)
            nurs = op in self.generators or tm['operator'] in self.generators
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
                            'scheduler_version': self.version, 'run_record': run['run_record']}
                if status != 'ok': settings['job_status'] = status       # lineage completed from the launch, flagged
                if len(joins) == len(files) and isinstance(joins[k], dict) and 'front' in joins[k] and 'back' in joins[k]:
                    parents = [joins[k]['front'], joins[k]['back']]; settings.update(joins[k])
                for k2 in ('caps', 'lowered', 't_last_improvement', 'kernel_bin', 'relaxed_caps'):
                    if info.get(k2) is not None: settings[k2] = info[k2]
                ta = time.monotonic()
                st, r, g = self.ar.admit(c, parents=parents, operator=op, settings=settings, seed=job['seed'],
                                         run_id=job['run_id'], code_version=version, cpu_s=cpu,
                                         wall_s=rec.get('wall_s', wall), slack=GEN_SLACK if nurs else None)
                admit_s += time.monotonic() - ta
                o = {'cand': f.name, 'metrics': m, 'status': st, 'id': r['id'] if r else None, 'gain': g}
                if r is not None and rec_metrics(r) != m: o['cleaned_metrics'] = rec_metrics(r)   # stored cleaned (archive.admit)
                # instrumentation: why (archive.explain / gain_reason); never changes the decision
                if st == 'not-better': o['reason'] = self.ar.explain(self.ar.last_metrics or m, GEN_SLACK if nurs else None)
                elif st == 'duplicate': o['reason'] = 'same circuit text as %s' % (r['id'] if r else '?')
                elif st == 'duplicate-structure': o['reason'] = 'same structure as %s' % (r['id'] if r else '?')
                elif st == 'admitted': o['reason'] = self.ar.last_gain_reason
                outcome.append(o)
                if st == 'admitted':
                    gain += g; self.fb.add_circuit(self.ar.circuit(r['id']), r['id']); self.last_admit = r['t_admit']
                    if g > 0: self.renew_caps(rec_metrics(r))
                    self.log(ev='admit', run_id=job['run_id'], op=op, id=r['id'], m=rec_metrics(r), gain=g, parents=parents,
                             gain_reason=self.ar.last_gain_reason)
                    self.runlog.improvement(dict(zip(('A', 'AD', 'G', 'GD'), rec_metrics(r))), op, run_id=job['run_id'],
                                            id=r['id'], gain=g, pub_new=r.get('pub_new'), parents=parents,
                                            gain_reason=self.ar.last_gain_reason)
        except Exception as e:                              # the run file is written whatever happens
            run['finish_error'] = repr(e); self.log(ev='finish-error', run_id=job['run_id'], error=repr(e))
        if self.fb.dirty and time.time() - self.last_fb_save > FB_SAVE_S:
            self.fb.save(); self.last_fb_save = time.time()
        self._recent.append((time.monotonic(), op, float(job.get('proc_cpu_s') or cpu or 0.0)))
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
        mark = None; marks = {}
        if op == 'join' and status == 'ok':
            by = info.get('joined_through_by')
            if not isinstance(by, dict) or not by:
                by = {job['target']: info.get('joined_through')}
            for t, v in by.items():
                if t in self.ar.rec and isinstance(v, (int, float)):
                    marks[t] = max(self.join_mark.get(t, 0.0), float(v)); self.join_mark[t] = marks[t]
            mark = marks.get(job['target'])
        run.update({'candidates': len(outcome), 'admitted': sum(1 for o in outcome if o['status'] == 'admitted'), 'gain': gain})
        # instrumentation: admission outcome by status, time spent verifying/admitting, the whole finish()
        counts = {}
        for o in outcome:
            s = o['status'] if not str(o['status']).startswith('rejected') else 'rejected'
            counts[s] = counts.get(s, 0) + 1
        adm = {'counts': counts, 'admit_s': round(admit_s, 3), 'finish_s': round(time.monotonic() - t_fin0, 3),
               'job_wall_s': wall, 'op_wall_s': rec.get('wall_s'), 'killed': job.get('killed')}
        run['admission'] = adm
        # instrumentation: monotonic process timing (U2-2): scheduler spawn, process start -> operator main, operator
        # setup and run (record.json 'timing'), operator end -> exit seen by the scheduler, rusage from os.wait4
        ot = rec.get('timing') if isinstance(rec.get('timing'), dict) else {}
        m0 = job.get('m0'); mx = job.get('mono_exit')
        rnd = lambda x: round(x, 3) if isinstance(x, (int, float)) else None
        timing = {'spawn_s': job.get('spawn_s'), 'mono_wall_s': rnd(mx - m0) if m0 and mx else None,
                  'start_to_main_s': rnd(ot['mono_main'] - m0) if m0 and 'mono_main' in ot else None,
                  'setup_s': ot.get('setup_s'), 'op_s': ot.get('op_s'),
                  'end_to_exit_seen_s': rnd(mx - ot['mono_end']) if mx and 'mono_end' in ot else None,
                  'exit_seen_to_finish_s': rnd(t_fin0 - mx) if mx else None,
                  'proc_cpu_s': job.get('proc_cpu_s'), 'proc_maxrss_kb': job.get('proc_maxrss_kb'), 't_exit': job.get('t_exit')}
        run['timing'] = timing
        try:
            self.runlog.event('admission', run_id=job['run_id'], op=op, status=status, gain=gain, cpu_s=cpu, **adm)
        except Exception:
            pass
        w = self.win.setdefault(op, {})
        for k2, v in (('jobs', 1), ('cpu_s', cpu or 0.0), ('wall_s', wall), ('cands', len(outcome)), ('admitted', run['admitted']),
                      ('gain', gain), ('admit_s', admit_s), ('finish_s', adm['finish_s']), (status, 1)):
            w[k2] = w.get(k2, 0) + v
        atomic_write(self.dir / 'runs' / (job['run_id'] + '.json'), json.dumps(run, indent=1, default=str))
        with open(self.dir / 'stats.jsonl', 'a') as f:
            f.write(json.dumps({'run_id': job['run_id'], 'op': op, 'cls': acls(tm['A']), 'cpu_s': cpu, 'target': job['target'],
                                'tm': [tm['A'], tm['AD'], tm['G'], tm['GD']],
                                'seed': job['seed'], 'status': status, 'join_mark': mark,
                                'join_marks': marks if len(marks) > 1 else None, 'why': job['why'],
                                'gain_rule': GAIN_RULE[self.ar.gain_mode],
                                'admitted': run['admitted'], 'gain': gain, 'ts': round(time.time(), 1),
                                'proc_cpu_s': timing.get('proc_cpu_s'), 'mono_wall_s': timing.get('mono_wall_s'),
                                'finish_s': adm['finish_s'], 't_exit': timing.get('t_exit')}) + '\n')

    def host_sample(self):
        """Host occupancy sampler (instrumentation, every 60 s): DIR/host.jsonl {ts, busy fraction of every CPU
        since the last sample (/proc/stat), loadavg, MemAvailable kB, cur_khz per CPU if readable, our CPUs}.
        Linux only; silently off elsewhere."""
        try:
            now = time.time(); cur = {}
            with open('/proc/stat') as f:
                for ln in f:
                    if ln.startswith('cpu') and ln[3:4].isdigit():
                        t = ln.split(); v = [int(x) for x in t[1:]]
                        cur[int(t[0][3:])] = (sum(v), v[3] + (v[4] if len(v) > 4 else 0))   # total, idle + iowait
            prev = getattr(self, '_host_prev', None); self._host_prev = cur
            if prev is None: return
            busy = {c: round(1 - (cur[c][1] - prev[c][1]) / max(1, cur[c][0] - prev[c][0]), 3) for c in cur if c in prev}
            d = {'ts': round(now, 1), 'busy': busy, 'ours': sorted(self.cpus), 'running': len(self.running)}
            rd = lambda f: Path(f).read_text()
            try: d['loadavg'] = [float(x) for x in rd('/proc/loadavg').split()[:3]]
            except OSError: pass
            try:
                for ln in rd('/proc/meminfo').splitlines():
                    if ln.startswith('MemAvailable'): d['mem_available_kb'] = int(ln.split()[1]); break
            except OSError: pass
            fr = {}
            for c in cur:
                try: fr[c] = int(rd('/sys/devices/system/cpu/cpu%d/cpufreq/scaling_cur_freq' % c))
                except (OSError, ValueError): break
            if fr: d['cur_khz'] = fr
            with open(self.dir / 'host.jsonl', 'a') as f: f.write(json.dumps(d) + '\n')
        except Exception:
            pass

    def summary(self, final=False):
        """Periodic summary event (instrumentation; every 5 min with front.json, and at the end): per operator
        jobs, statuses, CPU and wall seconds, candidates, admissions, gain, admission and finish time in the
        window; idle CPU seconds (a CPU counted from the moment its job was seen to end until it gets the
        next job); the bandit state; archive, cell and front sizes.  Counters restart after each summary."""
        try:
            now = time.time()
            idle_open = sum(now - t for t in self.free_since.values())
            self.log(ev='summary', final=final, window_s=round(now - self.t_summary, 1), per_op=self.win,
                     idle_cpu_s=round(self.idle_cpu_s + idle_open, 1), cpus=len(self.cpus), running=len(self.running),
                     free=len(self.free), bandit=self.bandit_state(), archive=len(self.ar.rec), cells=len(self.ar.cells),
                     front=len(self.ar.front()), suspended=sorted(o for o, t in self.suspended.items() if t > now))
            self.win = {}; self.idle_cpu_s = 0.0; self.t_summary = now
            self.free_since = {c: now for c in self.free_since}
        except Exception as e:
            self.log(ev='summary-error', error=repr(e))

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
        wake = self._wake_setup()
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
                if self.reap(j) is None:
                    if self.stop: self.kill(j, 'stopped')
                    elif (time.monotonic() - j['m0'] if j.get('m0') else now - j['t0']) > j.get('limit', self.secs.get(j['op'], 90.0) * KILL_FACTOR + KILL_GRACE):
                        self.kill(j, 'timeout')
                        self.log(ev='job-kill', run_id=j['run_id'], op=j['op'], reason='timeout', elapsed_s=round(now - j['t0'], 1),
                                 limit_s=j.get('limit'))
                    continue
                running.remove(j)
                if j['cpu'] in self.cpus and j['cpu'] not in self.free:
                    self.free.append(j['cpu']); self.free_since[j['cpu']] = time.time()
                try:
                    self.finish(j)
                except Exception as e:     # never lose the loop; the job dir stays as evidence
                    self.log(ev='finish-error', run_id=j['run_id'], error=repr(e))
            while self.free and time.time() < end and not self.stop:
                j = self.launch(self.free[0], self.busy_set())
                if j is None:
                    st = (self._idle_why, len(self.free))
                    if st != self._idle_state:          # logged when the idle reason or the number of idle CPUs changes
                        self.log(ev='idle', reason=st[0], free=sorted(self.free), running=len(running),
                                 decision=dict(self._dec or {}, target_choice=self._tdec)); self._idle_state = st
                    break
                self._idle_state = None
                c0 = self.free.pop(0); running.append(j)
                t_free = self.free_since.pop(c0, None)
                if t_free is not None: self.idle_cpu_s += time.time() - t_free
            self.maybe_ingest()
            if time.time() - getattr(self, '_host_t', 0) >= 60:
                self._host_t = time.time(); self.host_sample()
            if time.time() - last_front > 300:
                try:
                    self.write_front()
                except Exception as e:
                    self.log(ev='front-error', error=repr(e))
                self.summary()
                last_front = time.time()
            self._wait(wake, WAIT_S if not self.stop else 0.1)
        self._wake_close(wake)
        self.summary(final=True)
        self.fb.save(); self.write_front()
        self.log(ev='end', reason=self.stop or 'time', archive=len(self.ar.rec), cells=len(self.ar.cells), front=len(self.ar.front()))
        self.runlog.finish(self.stop or 'time', archive=len(self.ar.rec), cells=len(self.ar.cells), front=len(self.ar.front()),
                           jobs=self.nrun)


def _noop_handler(signum, frame):
    pass


def _wake_setup_fn():
    """a pipe that SIGCHLD (and every other handled signal) writes to (signal.set_wakeup_fd), so the loop sleeps
    until a job exits instead of polling every 0.5 s (U5 section 1).  None when not possible (not the main thread)."""
    try:
        r, w = os.pipe(); os.set_blocking(r, False); os.set_blocking(w, False)
        old = signal.set_wakeup_fd(w, warn_on_full_buffer=False)
        prev = signal.signal(signal.SIGCHLD, _noop_handler)
        return (r, w, old, prev)
    except (ValueError, OSError, AttributeError):
        return None


def _wait_fn(wake, timeout):
    if wake is None:
        time.sleep(timeout); return
    try:
        select.select([wake[0]], [], [], timeout)
    except (InterruptedError, OSError, ValueError):
        pass
    try:
        while os.read(wake[0], 4096): pass
    except (BlockingIOError, OSError):
        pass


def _wake_close_fn(wake):
    if wake is None: return
    try:
        signal.set_wakeup_fd(wake[2] if wake[2] is not None else -1)
        signal.signal(signal.SIGCHLD, wake[3] if wake[3] is not None else signal.SIG_DFL)
    except (ValueError, OSError, TypeError):
        pass
    for fd in wake[:2]:
        try: os.close(fd)
        except OSError: pass


Scheduler._wake_setup = staticmethod(_wake_setup_fn)
Scheduler._wait = staticmethod(_wait_fn)
Scheduler._wake_close = staticmethod(_wake_close_fn)


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
    # changes of behaviour of 2026-11-14, each with its old mode (earlier campaigns ran legacy / id / legacy / no caps)
    ap.add_argument('--gain', choices=('value', 'legacy'), default='value', help='archive.Archive.gain rule')
    ap.add_argument('--target-mode', choices=('tuple', 'id'), default='tuple', help='attempts counted per (A, AD, G, GD) tuple or per circuit id')
    ap.add_argument('--join-mode', choices=('incremental', 'legacy'), default='incremental',
                    help='incremental: one join pass per (target, archive state) over all cell members; legacy: front-first 300 partners every time')
    ap.add_argument('--tuple-caps', default='polish=2,pull=3',
                    help="jobs per tuple after which an operator stops choosing it (with --target-mode tuple); '' for none")
    ap.add_argument('--cap-renew', choices=('never', 'box'), default='never',
                    help='box: a new front tuple inside the cap box (A, AD, GD) of a front tuple renews that tuple\'s caps')
    ap.add_argument('--cap-renew-max', type=int, default=3, help='renewals per (operator, tuple) with --cap-renew box')
    ap.add_argument('--policy', choices=('priority', 'bandit'), default='priority',
                    help='priority (default, 2026-11-16): fixed levels join, fresh, variant, near, other, repeat; bandit: the earlier rule')
    ap.add_argument('--ingest-every', type=float, default=60.0, help='seconds between ingest passes of control.json "ingest" (was 1800)')
    ap.add_argument('--join-batch', type=int, default=8, help='--policy priority: join targets per join job')
    ap.add_argument('--join-cpus', type=int, default=1, help='--policy priority: join jobs running at once at most')
    ap.add_argument('--join-share', type=float, default=0.10, help='--policy priority: join CPU share over the last 10 min at most')
    ap.add_argument('--variants-first', action='store_true', help='--policy priority: structure variants and near members before the repeats under the tuple caps (order of 2026-11-16)')
    ap.add_argument('--repeat-max', type=int, default=None, help='--policy priority: jobs per (operator, tuple) beyond which no repeat is run')
    ap.add_argument('--function', choices=aesfn.NAMES, default=None,
                    help='aes-sbox or aes-invsbox (default: the campaign\'s, from campaign.json; aes-sbox for a new one)')
    ap.add_argument('--kopt', action='append', metavar='OPS:KEY=VAL,...',
                    help="kernel options passed to every job of the named kernel operators, e.g. 'polish,pull:pair_xor=1' "
                         "(repeatable; keys: ops.KOPT_KEYS; default none = the kernel defaults)")
    ap.add_argument('--kopt-first', action='append', metavar='OPS:KEY=VAL,...',
                    help="kernel options for the FIRST jobs only (choice level in --kopt-first-levels), over --kopt, "
                         "e.g. 'polish:tgt_w.mffc1=0.5,tgt_w.and=0.3'")
    ap.add_argument('--kopt-first-levels', default=','.join(FIRST_LEVELS),
                    help='choice levels (job why) that count as first jobs for --kopt-first (default %(default)s)')
    return ap


FIRST_LEVELS = ('fresh', 'variant', 'near', 'other')      # --policy priority levels of a first job on a tuple / structure ('fresh' also bandit)


def parse_kopt_arg(items):
    """['polish,pull:pair_xor=1', ...] -> {op: {key: value}} (later items win per key)"""
    from boolflux.hub.ops import parse_kopt
    out = {}
    for it in items or ():
        if ':' not in it: raise SystemExit('--kopt wants OPS:KEY=VAL,..., got %r' % it)
        ops, kv = it.split(':', 1)
        try:
            d = parse_kopt(kv)
        except ValueError as e:
            raise SystemExit('--kopt %r: %s' % (it, e))
        for o in ops.split(','):
            o = o.strip()
            if o not in KERNEL_OPS: raise SystemExit('--kopt %r: %r is not a kernel operator (%s)' % (it, o, ', '.join(KERNEL_OPS)))
            out.setdefault(o, {}).update(d)
    return out


def rec_metrics(r):
    return (r['A'], r['AD'], r['G'], r['GD'])


def main(argv=None):
    args = parser().parse_args(argv)
    args.argv = list(sys.argv if argv is None else [sys.argv[0]] + list(argv))
    runlog.report()
    s = Scheduler(args)
    if args.seed_list:
        s.seed(Path(args.seed_list).read_text().split())
    if not args.seed_only:
        s.run()
    else:
        s.runlog.finish('seed-only', archive=len(s.ar.rec), front=len(s.ar.front()))


if __name__ == '__main__':
    main()
