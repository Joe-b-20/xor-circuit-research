#!/usr/bin/env python3
"""Shared helpers for the method scripts (ops/<name>.py).

Operator contract:

    python3 search/nonlinear/boolflux/ops/<name>.py --in START --target REF --seed S \
        --seconds T --out DIR [--cpus 1] [op-specific flags]

  * --target is a reference circuit (a path, or a file name in seeds/aes-sbox/) or an id in the JSON file
    $BOOLFLUX_TARGETS_JSON (see target()); A <= ref A, AD <= ref AD are the hard limits of a RECORDED
    result (search states may exceed every cap);
  * DIR receives only circuits that pass aes_check (two verifiers, all 256 inputs, NIST library) and are
    inside the target's hard limits, named <name>-a..-ad..-g..-gd..-<hash>.circ.txt, each with a full
    sidecar <same stem>.json (target, tuple, start and parent with sha256, op, params, method, command,
    seed, code version, aes_check output);
  * DIR/result.json: best per (G, GD), wall time, exit status; exit within T + 60 s.

What is here:
  limits(tid) / target(tid)          the target's reference tuple (a circuit file, or an entry of the targets
                                     file, re-read on every call)
  in_limits(tup, tid)                hard-limit filter on an (A, AD, G, GD) tuple
  classify(tup, tid)                 strict / tradeoff:<kind> / other / outside (informational label)
  check(path)                        aes_check.check wrapper -> (ok, tuple, OK-line, full text)
  Recorder(out, op, target, ...)     verify + filter + write circuit/sidecar for every new job-local Pareto
                                     point; result.json writer (atomic)
  pareto2 / pareto4                  (G, GD) and (A, AD, G, GD) Pareto filters
  kernel_bin()                       the gate-kernel build bfx-<sha1(kernel/bfx.c)[:10]> in $BOOLFLUX_CACHE/bin
  code_info(kernel)                  git commit of the repository, kernel path + sha256, ops/*.py sha256
"""
from __future__ import annotations

import datetime as dt
import hashlib
import io
import json
import os
import subprocess
import sys
import contextlib
from pathlib import Path

OPS = Path(__file__).resolve().parent            # search/nonlinear/boolflux/ops
PKG = OPS.parent                                  # search/nonlinear/boolflux
REPO = PKG.parents[2]                             # the repository root
# The targets file (ids, reference circuit, limits; format in target()) and the work directory for
# kernel builds and caches are set by the environment.
TARGETS_JSON = Path(os.environ.get('BOOLFLUX_TARGETS_JSON', 'TARGETS.json'))
CACHE = Path(os.environ.get('BOOLFLUX_CACHE', Path(os.environ.get('XDG_CACHE_HOME') or Path.home() / '.cache') / 'boolflux'))
NIST_DIR = PKG.parent / 'seeds' / 'aes-sbox'

sys.path.insert(0, str(PKG))
sys.path.insert(0, str(PKG.parent))
import aes_check                                   # noqa: E402  (sets sys.path for boolflux + verify)
from boolflux import core, targets as _targets     # noqa: E402

MODEL = core.Model.load('nist')
AES = _targets.aes_sbox()


def utc(ts=None):
    t = dt.datetime.now(dt.timezone.utc) if ts is None else dt.datetime.fromtimestamp(ts, dt.timezone.utc)
    return t.strftime('%Y-%m-%dT%H:%M:%SZ')


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def atomic_write(path, text):
    path = Path(path); tmp = path.with_name('.%s.tmp%d' % (path.name, os.getpid()))
    tmp.write_text(text); os.replace(tmp, path)


def write_json(path, obj):
    atomic_write(path, json.dumps(obj, indent=1, default=str) + '\n')


# ---- targets -----------------------------------------------------------------------------------

def spec():
    return json.loads(TARGETS_JSON.read_text())


def target(tid):
    """The target `tid`.  A circuit file (a path, or a file name in seeds/aes-sbox/) is the reference
    itself: limits A and AD are its own, G and GD its own point to beat.  Otherwise an entry of
    TARGETS_JSON: {"targets": [{"id", "ref" (file name in seeds/aes-sbox/ or a path), "A", "AD", "G",
    "GD", "tradeoffs" (optional)}], "definitions": {...} (optional, see classify)}."""
    for f in (Path(tid), NIST_DIR / tid):
        if f.is_file():
            A, AD, G, GD = metrics(load(f))
            return {'id': f.name.split('.')[0], 'ref': str(f.resolve()), 'A': A, 'AD': AD, 'G': G, 'GD': GD}
    if not TARGETS_JSON.is_file():
        raise KeyError('target %s: not a circuit file, and no targets file %s (set BOOLFLUX_TARGETS_JSON)' % (tid, TARGETS_JSON))
    for t in spec()['targets']:
        if t['id'] == tid:
            return t
    raise KeyError('target %s not in %s' % (tid, TARGETS_JSON))


def limits(tid):
    t = target(tid)
    return {'A': t['A'], 'AD': t['AD'], 'G': t['G'], 'GD': t['GD']}


def reference_file(tid):
    return NIST_DIR / target(tid)['ref']


def in_limits(tup, tid, lim=None):
    lim = lim or limits(tid)
    return tup[0] <= lim['A'] and tup[1] <= lim['AD']


def classify(tup, tid, t=None, defs=None):
    """Informational label of a result against its target: strict (no worse in G and GD, better in one),
    tradeoff:<kind> (a trade the target's "tradeoffs" list allows), other, outside (beyond A or AD)."""
    if t is None:
        t = target(tid)
    if defs is None:
        defs = spec().get('definitions', {}) if TARGETS_JSON.is_file() else {}
    A, AD, G, GD = tup
    if A > t['A'] or AD > t['AD']:
        return 'outside'
    if G <= t['G'] and GD <= t['GD'] and (G < t['G'] or GD < t['GD']):
        return 'strict'
    gain = defs.get('min_gate_gain_for_depth_cost', 3); cost = defs.get('max_gate_cost_for_depth_gain', 8)
    for tr in t.get('tradeoffs', []):
        k = tr['kind']
        if k == 'gates_for_depth' and t['GD'] < GD <= tr['GD_max'] and G <= t['G'] - gain:
            return 'tradeoff:' + k
        if k == 'depth_for_gates' and GD <= tr['GD_max'] < t['GD'] and t['G'] < G <= t['G'] + cost:
            return 'tradeoff:' + k
        if k == 'and_depth_for_gates' and AD < t['AD'] and AD <= max(tr['AD_targets']) and (G > t['G'] or GD > t['GD']):
            return 'tradeoff:' + k
    return 'other'


# ---- Pareto ------------------------------------------------------------------------------------

def dominates(u, v):
    return all(a <= b for a, b in zip(u, v)) and tuple(u) != tuple(v)


def pareto2(tuples):
    """(G, GD)-minimal tuples (A, AD, G, GD) (one per (G, GD), first kept)."""
    pts = {}
    for t in tuples:
        pts.setdefault((t[2], t[3]), t)
    keys = [k for k in pts if not any(dominates(o, k) for o in pts)]
    return sorted((pts[k] for k in keys), key=lambda t: (t[2], t[3]))


def pareto4(tuples):
    s = set(tuple(t) for t in tuples)
    return sorted(t for t in s if not any(dominates(o, t) for o in s))


# ---- verification ------------------------------------------------------------------------------

def check(path):
    """aes_check.check (core + independent verifier, all 256 inputs, NIST library, metrics agreement).
    Returns (ok, tuple, ok_line, full_text) with aes_check.py's own printed lines."""
    r = aes_check.check(str(path))
    if not r['ok']:
        return False, r.get('tuple'), 'FAIL %s: %s' % (r['file'], r.get('errors')), str(r.get('errors'))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            aes_check.main([str(path)])
        except SystemExit:
            pass
    full = buf.getvalue()
    line = next((l for l in full.splitlines() if l.startswith('OK')), 'OK   %s  A AD G GD = %s' % (path, ' '.join(map(str, r['tuple']))))
    return True, tuple(r['tuple']), line.strip(), full


def load(path):
    p = Path(path)
    if p.suffix == '.bfx':
        return core.from_kernel(p.read_text(), name=p.stem)
    return core.read_ncff(str(p))


def metrics(c):
    m = c.metrics(MODEL)
    return (m['A'], m['AD'], m['G'], m['GD'])


def body(text):
    return '\n'.join(l for l in text.splitlines() if l.strip() and not l.strip().startswith('%'))


def structure_key(c):
    from boolflux.hub.common import structure_key as sk
    return sk(c)


# ---- code / kernel -----------------------------------------------------------------------------

def kernel_bin(bindir=None):
    """Gate-kernel build bfx-<sha1(kernel/bfx.c)[:10]> in CACHE/bin (hub.ops.kernel_bin, atomic build)."""
    from boolflux.hub.ops import kernel_bin as kb
    return kb(bindir or CACHE)


_GIT = None


def git_head():
    global _GIT
    if _GIT is None:
        try:
            _GIT = subprocess.run(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], capture_output=True, text=True,
                                  timeout=20).stdout.strip()
        except Exception:
            _GIT = 'unknown'
    return _GIT


def code_info(kernel=None, extra_files=()):
    info = {'git': git_head(), 'tree': 'working tree (uncommitted changes included)',
            'ops_sha256': {p.name: sha256(p) for p in sorted(OPS.glob('*.py'))}}
    for f in extra_files:
        try: info.setdefault('used_sha256', {})[str(f)] = sha256(f)
        except OSError: pass
    if kernel:
        info['kernel'] = str(kernel); info['kernel_sha256'] = sha256(kernel)
        info['kernel_src_sha256'] = sha256(PKG / 'kernel' / 'bfx.c')
    return info


# ---- recorder ----------------------------------------------------------------------------------

class Recorder:
    """Collects candidate circuits of one operator job.  Every candidate inside the target's hard limits
    that is a new job-local (G, GD) Pareto point (or a new (A, AD, G, GD) Pareto point) is written at
    once (so a killed job keeps its results), checked with aes_check and given a sidecar; a file that
    fails aes_check is removed.  result.json is rewritten on every new point and by finish()."""

    def __init__(self, out, op, tid, start, seed, command, method, params, kernel=None, t0=None):
        import time
        self.out = Path(out); self.out.mkdir(parents=True, exist_ok=True)
        self.op, self.tid, self.seed, self.command, self.method = op, tid, seed, command, method
        self.params = params; self.kernel = kernel
        self.t0 = t0 or time.time()
        self.lim = limits(tid); self.tgt = target(tid)
        self.defs = spec().get('definitions', {}) if TARGETS_JSON.is_file() else {}
        self.start = Path(start).resolve(); self.start_sha = sha256(self.start)
        self.points = {}          # (A, AD, G, GD) -> record
        self.bodies = set()
        self.rejected = {'outside': 0, 'dominated': 0, 'aes_check_fail': 0, 'duplicate': 0}
        self.status = 'running'; self.notes = []
        self.skip_start_tuple = True      # a result weakly dominated by the start's own tuple is not recorded
        self._code = None
        try:
            self.start_tuple = metrics(load(self.start))
        except Exception:
            self.start_tuple = None

    def code(self):
        if self._code is None: self._code = code_info(self.kernel)
        return self._code

    def offer(self, c, how='', lineage=None, path_certified='unknown'):
        """c: core circuit (already checked to compute the S-box by the caller or not; checked here)."""
        import time
        t = metrics(c)
        if not in_limits(t, self.tid, self.lim):
            self.rejected['outside'] += 1; return None
        known = list(self.points) + ([tuple(self.start_tuple)] if self.start_tuple and self.skip_start_tuple else [])
        if any(all(a <= b for a, b in zip(p, t)) for p in known):
            # weakly dominated in (A, AD, G, GD) (hence also in (G, GD)) by a point already written or the start
            self.rejected['dominated'] += 1; return None
        if c.value_table() != AES:
            self.rejected['aes_check_fail'] += 1; return None
        text = core.write_ncff(c, MODEL, comments=['%s job target %s seed %s: %s t=%.1f s' % (
            self.op, self.tid, self.seed, how, time.time() - self.t0)])
        b = body(text)
        if b in self.bodies:
            self.rejected['duplicate'] += 1; return None
        h = hashlib.sha256(text.encode()).hexdigest()
        name = '%s-a%d-ad%d-g%d-gd%d-%s' % (self.op, t[0], t[1], t[2], t[3], h[:10])
        p = self.out / (name + '.circ.txt')
        p.write_text(text)
        ok, vt, line, full = check(p)
        if not ok or tuple(vt) != tuple(t):
            self.rejected['aes_check_fail'] += 1; self.notes.append('aes_check failed: %s' % line)
            p.unlink(); return None
        self.bodies.add(b)
        side = {'target': self.tid, 'A': t[0], 'AD': t[1], 'G': t[2], 'GD': t[3],
                'class': classify(t, self.tid, self.tgt, self.defs),
                'reference': self.tgt['ref'],
                'start': {'path': str(self.start), 'sha256': self.start_sha, 'tuple': list(self.start_tuple) if self.start_tuple else None},
                'parent': {'path': str(self.start), 'sha256': self.start_sha},
                'op': self.op, 'params': self.params, 'how': how, 'lineage': lineage,
                'method': self.method, 'command': self.command, 'seed': self.seed,
                'elapsed_s': round(time.time() - self.t0, 1), 'code': self.code(),
                'aes_check': line, 'aes_check_full': full, 'circuit_sha256': sha256(p),
                'path_certified': path_certified,
                'path_note': 'informational; search states may exceed the caps, recorded circuits never exceed A and AD',
                'utc': utc()}
        write_json(self.out / (name + '.json'), side)
        self.points[t] = {'tuple': list(t), 'file': str(p), 'how': how, 't': side['elapsed_s'], 'class': side['class']}
        self.write_result()
        return p

    def best_points(self):
        pts = list(self.points)
        return {'pareto_G_GD': [self.points[t] for t in pareto2(pts)],
                'pareto_A_AD_G_GD': [self.points[t] for t in pareto4(pts)]}

    def write_result(self, extra=None):
        import time
        r = {'op': self.op, 'target': self.tid, 'seed': self.seed, 'status': self.status,
             'start': str(self.start), 'start_tuple': self.start_tuple, 'params': self.params,
             'wall_s': round(time.time() - self.t0, 1), 'n_written': len(self.points),
             'rejected': self.rejected, 'notes': self.notes[-20:], 'utc': utc()}
        r.update(self.best_points())
        if extra: r.update(extra)
        write_json(self.out / 'result.json', r)

    def finish(self, status='ok', extra=None):
        self.status = status
        self.write_result(extra)


def contract_args(ap):
    """Add the common operator flags to an argparse parser."""
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--target', required=True)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--seconds', type=float, required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--cpus', type=int, default=1)
    return ap
