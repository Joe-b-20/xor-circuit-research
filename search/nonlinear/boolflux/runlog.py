"""Run records: what an outsider needs to replay a BoolFlux search run, and the tools it measures with.

    log = RunLog(OUT, 'cli.flow', seeds={...}, config={...}, budget_s=120)
    log.add_start('start.circ.txt', metrics=...); log.add_kernel(bin_path)
    log.improvement({'G': 117, ...}, operator='gate kernel', t=12.3)
    log.finish('ok', best=...)

OUT/run.json (written at the start and at the end; schema 'boolflux-run/1'):
  kind              entry point: cli.run, cli.pipe, cli.flow, hub.scheduler, hub.op.<name>, ops.<name>
  argv, cwd, command  the exact command line (argv[0] as called), the directory it ran in, and a
                    shell-quoted line that replays it from there
  git               commit, branch, dirty (any tracked change, or untracked files under search/),
                    diff = file with `git diff HEAD --binary` plus every untracked file under search/
                    (as new-file patches), saved when dirty; replay: git checkout COMMIT, then
                    `zcat DIFF | git apply`
  sources_sha256    sha256 over every source file of search/nonlinear/boolflux (path and bytes)
  function          AES function of the AES tools (aesfn), when the run uses them
  seeds             every seed the run uses (entry point specific; derived seeds also in events)
  config            the resolved configuration, caps included
  starts            start circuits: path, sha256, metrics
  budget_s          wall-time budget (null: iteration budget)
  kernels           kernel binaries: path, sha256, source and its sha256, build command, compiler
  host              CPU count, CPU affinity, OS, Python
  tools             GNU time and taskset (path or null), how time/RSS are measured and how jobs are pinned
  env               BOOLFLUX_* variables
  t_start_utc, t_end_utc, wall_s, cpu_s (this process and its waited-for children), max_rss_kb
  (largest child), status ('running' until finish(); 'exited' if the process ended without it), result
OUT/events.jsonl.gz: one JSON object per line, {t (s since start), ev, ...}; ev 'improvement' carries
the metrics and the operator.  Each event is its own gzip member, written by one append, so a killed
run keeps every event written (and forked workers can share the file).

Tools: gnu_time(), taskset() find the programs on PATH; measured() runs a command under GNU time -v or,
without it, measures wall time and peak RSS with os.wait4; pin() pins with taskset or, without it,
os.sched_setaffinity (unpinned with one warning where neither exists).  report() is the startup line.
"""
from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
import os
import platform
import resource
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from functools import lru_cache
from pathlib import Path

PKG = Path(__file__).resolve().parent            # search/nonlinear/boolflux
REPO = PKG.parents[2]
SCHEMA = 'boolflux-run/1'
SOURCE_SUFFIXES = ('.py', '.c', '.json')
MAX_UNTRACKED = 2 << 20                          # untracked files above this size are listed, not saved
_WARNED = set()


def utc(ts=None):
    t = dt.datetime.now(dt.timezone.utc) if ts is None else dt.datetime.fromtimestamp(ts, dt.timezone.utc)
    return t.strftime('%Y-%m-%dT%H:%M:%SZ')


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def warn(key, text):
    """print `text` once per process on stderr"""
    if key not in _WARNED:
        _WARNED.add(key)
        print('boolflux: ' + text, file=sys.stderr, flush=True)


# ---- tools -------------------------------------------------------------------------------------

@lru_cache(None)
def gnu_time():
    """path of GNU time on PATH (a `time` that understands -v), or None"""
    p = shutil.which('time')
    if not p:
        return None
    try:
        r = subprocess.run([p, '-v', 'true'], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return p if 'Maximum resident set size' in r.stderr else None


@lru_cache(None)
def taskset():
    return shutil.which('taskset')


def can_setaffinity():
    return hasattr(os, 'sched_setaffinity')


def pinning():
    return 'taskset' if taskset() else ('sched_setaffinity' if can_setaffinity() else 'none')


def timing():
    return 'gnu-time' if gnu_time() else 'python-resource (wall clock, os.wait4 ru_maxrss)'


def pin(cmd, cpu):
    """(command, preexec_fn) that run `cmd` on CPU `cpu` (None = unpinned): taskset -c, else
    os.sched_setaffinity in the child, else unpinned with one warning."""
    if cpu is None:
        return list(cmd), None
    if taskset():
        return ['taskset', '-c', str(cpu)] + list(cmd), None
    if can_setaffinity():
        warn('taskset', 'taskset not found: CPUs pinned with os.sched_setaffinity instead')
        cpus = {int(x) for x in str(cpu).split(',')}
        return list(cmd), lambda: os.sched_setaffinity(0, cpus)
    warn('taskset', 'taskset not found and no os.sched_setaffinity: jobs run UNPINNED')
    return list(cmd), None


def measured(cmd, cpu=None):
    """Run `cmd` (pinned to `cpu` if given); (stdout, stderr, peak RSS kB, wall s, returncode).
    GNU time -v when it is on PATH (its report is appended to stderr, as before); otherwise wall
    clock and the child's ru_maxrss from os.wait4, with one warning."""
    t0 = time.time()
    gt = gnu_time()
    if gt:
        full, pre = pin([gt, '-v'] + list(cmd), cpu)
        r = subprocess.run(full, capture_output=True, text=True, preexec_fn=pre)
        import re
        m = re.search(r'Maximum resident set size \(kbytes\): (\d+)', r.stderr)
        return r.stdout, r.stderr, int(m.group(1)) if m else None, time.time() - t0, r.returncode
    warn('time', 'GNU time not found: wall time and peak RSS measured by Python (os.wait4)')
    full, pre = pin(cmd, cpu)
    with tempfile.TemporaryFile() as fo, tempfile.TemporaryFile() as fe:
        p = subprocess.Popen(full, stdout=fo, stderr=fe, preexec_fn=pre)
        _, status, ru = os.wait4(p.pid, 0)
        p.returncode = os.waitstatus_to_exitcode(status)
        fo.seek(0); fe.seek(0)
        out = fo.read().decode(errors='replace'); err = fe.read().decode(errors='replace')
    return out, err, int(ru.ru_maxrss), time.time() - t0, p.returncode


@lru_cache(None)
def compiler(cc='gcc'):
    try:
        r = subprocess.run([cc, '--version'], capture_output=True, text=True, timeout=20)
        return r.stdout.splitlines()[0].strip() if r.returncode == 0 and r.stdout else None
    except (OSError, subprocess.SubprocessError, IndexError):
        return None


def module_version(name):
    try:
        import importlib.metadata as md
        return md.version({'pysat': 'python-sat'}.get(name, name))
    except Exception:
        try:
            __import__(name)
            return 'installed'
        except Exception:
            return None


def tools():
    return {'gnu_time': gnu_time(), 'taskset': taskset(), 'timing': timing(), 'pinning': pinning(),
            'gcc': compiler(), 'numpy': module_version('numpy'), 'python_sat': module_version('pysat')}


def report(file=None):
    """the startup line: what is there and what replaces what is not"""
    t = tools()
    parts = ['python %s' % platform.python_version(),
             'gcc: %s' % (t['gcc'] or 'MISSING (needed to build the kernels)'),
             'GNU time: %s' % (t['gnu_time'] or 'missing, Python measures time and RSS'),
             'taskset: %s' % (t['taskset'] or ('missing, os.sched_setaffinity pins' if can_setaffinity() else 'missing, unpinned')),
             'numpy: %s' % (t['numpy'] or 'missing'), 'python-sat: %s' % (t['python_sat'] or 'missing')]
    print('boolflux: ' + '; '.join(parts), file=file or sys.stderr, flush=True)
    return t


def kernel_info(path, source=None, command=None):
    """binary path and sha256, its source and sha256, the build command, and the compiler on PATH
    when the record is made (the binaries are built by that gcc on first use)"""
    p = Path(path)
    d = {'path': str(p.resolve()), 'sha256': sha256_file(p) if p.is_file() else None}
    if source is not None:
        s = Path(source); d['source'] = str(s.resolve()); d['source_sha256'] = sha256_file(s) if s.is_file() else None
    d['command'] = [str(x) for x in command] if command else None
    d['compiler'] = compiler()
    return d


# ---- code version -------------------------------------------------------------------------------

def _git(args, repo):
    return subprocess.run(['git', '-C', str(repo)] + args, capture_output=True, timeout=60)


@lru_cache(None)
def git_state(repo=str(REPO)):
    """(info dict, diff bytes or None).  Cached per process."""
    info = {'commit': None, 'branch': None, 'dirty': None}
    try:
        r = _git(['rev-parse', 'HEAD'], repo)
    except (OSError, subprocess.SubprocessError):
        r = None
    if r is None or r.returncode != 0:
        info['note'] = 'not a git checkout (or git missing): see sources_sha256'
        return info, None
    info['commit'] = r.stdout.decode().strip()
    b = _git(['rev-parse', '--abbrev-ref', 'HEAD'], repo)
    info['branch'] = b.stdout.decode().strip() if b.returncode == 0 else None
    diff = _git(['diff', 'HEAD', '--binary'], repo).stdout
    unt = _git(['ls-files', '--others', '--exclude-standard', '-z', '--', 'search'], repo).stdout.decode()
    parts = [diff]; skipped = []; untracked = []
    for f in sorted(x for x in unt.split('\0') if x):
        try:
            if (Path(repo) / f).stat().st_size > MAX_UNTRACKED:
                skipped.append(f); continue
        except OSError:
            continue
        untracked.append(f)
        parts.append(_git(['diff', '--no-index', '--binary', '--', '/dev/null', f], repo).stdout)
    info['dirty'] = bool(diff.strip() or untracked or skipped)
    if untracked: info['untracked'] = untracked
    if skipped: info['untracked_not_saved'] = skipped
    blob = b''.join(parts)
    if not info['dirty']:
        return info, None
    info['diff_sha256'] = hashlib.sha256(blob).hexdigest()
    info['diff_bytes'] = len(blob)
    return info, blob


@lru_cache(None)
def sources_sha256(pkg=str(PKG)):
    h = hashlib.sha256()
    for f in sorted(Path(pkg).rglob('*')):
        if f.suffix in SOURCE_SUFFIXES and f.is_file() and '__pycache__' not in f.parts:
            h.update(str(f.relative_to(pkg)).encode()); h.update(b'\0'); h.update(f.read_bytes()); h.update(b'\0')
    return h.hexdigest()


def host():
    try:
        aff = sorted(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        aff = None
    u = platform.uname()
    return {'cpu_count': os.cpu_count(), 'affinity': aff, 'os': '%s %s %s' % (u.system, u.release, u.machine),
            'python': '%s %s' % (platform.python_implementation(), platform.python_version()),
            'python_executable': sys.executable}


def _cpu():
    s = resource.getrusage(resource.RUSAGE_SELF); c = resource.getrusage(resource.RUSAGE_CHILDREN)
    return s.ru_utime + s.ru_stime + c.ru_utime + c.ru_stime, c.ru_maxrss


# ---- the record ---------------------------------------------------------------------------------

class RunLog:
    """run.json + events.jsonl.gz in `out` (module docstring).  `store`: folder for the git diff,
    shared by many runs (content-addressed, git-<sha256[:16]>.diff.gz); default $BOOLFLUX_RUNLOG_STORE,
    else `out` itself."""

    def __init__(self, out, kind, argv=None, seeds=None, config=None, budget_s=None, function=None,
                 store=None, name='run', t0=None):
        self.out = Path(out); self.out.mkdir(parents=True, exist_ok=True)
        self.path = self.out / (name + '.json')
        self.events_path = self.out / ('events.jsonl.gz' if name == 'run' else name + '.events.jsonl.gz')
        self.t0 = t0 or time.time(); self.cpu0 = _cpu()[0]
        argv = list(sys.argv if argv is None else argv)
        gi, diff = git_state()
        gi = dict(gi)
        if diff is not None:
            st = Path(store or os.environ.get('BOOLFLUX_RUNLOG_STORE') or self.out)
            st.mkdir(parents=True, exist_ok=True)
            df = st / ('git-%s.diff.gz' % gi['diff_sha256'][:16])
            if not df.exists():
                tmp = df.with_name(df.name + '.%d.tmp' % os.getpid())
                tmp.write_bytes(gzip.compress(diff)); os.replace(tmp, df)
            gi['diff'] = str(df.resolve())
        self.rec = {
            'schema': SCHEMA, 'kind': kind, 'status': 'running',
            'argv': [sys.executable] + argv, 'cwd': os.getcwd(),
            'command': ' '.join(shlex.quote(a) for a in ['python3'] + argv),
            'git': gi, 'sources_sha256': sources_sha256(), 'repo': str(REPO),
            'function': function, 'seeds': seeds or {}, 'config': config or {}, 'starts': [],
            'budget_s': budget_s, 'kernels': [], 'host': host(), 'tools': tools(),
            'env': {k: v for k, v in sorted(os.environ.items()) if k.startswith('BOOLFLUX_')},
            't_start_utc': utc(self.t0), 'events': self.events_path.name, 'result': None}
        self.done = False
        self.write()
        import atexit
        atexit.register(self._atexit, os.getpid())

    # -- fields ------------------------------------------------------------------------------
    def write(self):
        tmp = self.path.with_name('.%s.%d.tmp' % (self.path.name, os.getpid()))
        tmp.write_text(json.dumps(self.rec, indent=1, default=str) + '\n')
        os.replace(tmp, self.path)

    def set(self, write=True, **kw):
        self.rec.update(kw)
        if write: self.write()

    def add_start(self, path=None, metrics=None, label=None, circuit_text=None, write=True):
        d = {'label': label}
        if path is not None:
            p = Path(path); d['path'] = str(p.resolve()) if p.exists() else str(path)
            d['sha256'] = sha256_file(p) if p.is_file() else None
        if circuit_text is not None:
            d['text_sha256'] = hashlib.sha256(circuit_text.encode()).hexdigest()
        if metrics is not None: d['metrics'] = metrics
        self.rec['starts'].append(d)
        if write: self.write()
        return d

    def add_kernel(self, path, source=None, command=None, write=True):
        if path is None:
            return None
        k = kernel_info(path, source, command)
        if all(x.get('path') != k['path'] for x in self.rec['kernels']):
            self.rec['kernels'].append(k)
            if write: self.write()
        return k

    # -- events ------------------------------------------------------------------------------
    def event(self, ev, t=None, **kw):
        d = {'t': round(time.time() - self.t0 if t is None else t, 3), 'ev': ev}
        d.update(kw)
        data = gzip.compress((json.dumps(d, default=str) + '\n').encode(), mtime=0)
        fd = os.open(str(self.events_path), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
        try:
            os.write(fd, data)
        finally:
            os.close(fd)

    def improvement(self, metrics, operator, t=None, **kw):
        self.event('improvement', t=t, metrics=metrics, operator=operator, **kw)

    # -- end ---------------------------------------------------------------------------------
    def finish(self, status='ok', **result):
        cpu, rss = _cpu()
        t1 = time.time()
        self.rec.update({'status': status, 't_end_utc': utc(t1), 'wall_s': round(t1 - self.t0, 3),
                         'cpu_s': round(cpu - self.cpu0, 3), 'max_rss_kb': rss,
                         'result': result or self.rec.get('result')})
        self.done = True
        self.write()

    def _atexit(self, pid):
        if not self.done and os.getpid() == pid:        # not in forked workers
            try:
                self.finish('exited')
            except Exception:
                pass

    def summary(self):
        """the fields a circuit sidecar carries (the full record is run.json)"""
        r = self.rec
        return {'run_record': str(self.path.resolve()), 'kind': r['kind'], 'command': r['command'],
                'argv': r['argv'], 'cwd': r['cwd'], 'git': {k: r['git'].get(k) for k in ('commit', 'dirty', 'diff', 'diff_sha256')},
                'sources_sha256': r['sources_sha256'], 'seeds': r['seeds'], 'function': r['function'],
                'kernels': [{k: x.get(k) for k in ('path', 'sha256', 'compiler')} for x in r['kernels']],
                'host': {k: r['host'][k] for k in ('cpu_count', 'os', 'python')}}


def read_events(path):
    """the events of an events.jsonl.gz file (a list of dicts)"""
    with gzip.open(path, 'rt') as f:
        return [json.loads(ln) for ln in f if ln.strip()]


if __name__ == '__main__':
    t = report(sys.stdout)
    sys.exit(0 if t['gcc'] and sys.version_info >= (3, 11) else 1)
