"""Helpers shared by ops/rebase.py and ops/bottom.py (both rebuild part of a circuit, then polish it with
the gate kernel), on top of ops/common.py: a Recorder adapter (per-candidate parent + method go into the
sidecar's `lineage` and `how`), one capped kernel stage, and --cpus K workers (K-1 extra processes with
their own seeds, merged at the end).
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as C                                           # noqa: E402  (operator contract, aes_check)
from boolflux import core                                    # noqa: E402
from boolflux.hub.common import verify, metrics, clean, load, cid   # noqa: E402
from boolflux.hub import ops as O                            # noqa: E402

MODEL = C.MODEL
KDIR = C.CACHE                                               # kernel binary at KDIR/bin/bfx-<sha1(bfx.c)[:10]>


def limits(tid):
    return C.target(tid)


def kernel_path():
    return C.kernel_bin(KDIR)


def kernel_stage(c, caps, seed, seconds, wd, objective='cost,gd', repair_keep=1, cfg=None):
    """one gate-kernel run (hub.ops._kernel) from c; returns (best verified circuit inside caps or None, info).
    caps: dict A/AD/GD (None = no cap).  The kernel may move outside the caps internally (repair mode)."""
    wd = Path(wd); wd.mkdir(parents=True, exist_ok=True)
    old = dict(O.KDEFAULTS)
    O.KDEFAULTS['repair_keep'] = repair_keep
    if cfg: O.KDEFAULTS.update(cfg)
    try:
        cands, info = O._kernel(c, caps, objective, seed, seconds, wd, KDIR)
    except Exception as e:      # a failed kernel job is not fatal for the operator
        return None, {'error': repr(e)[:300]}
    finally:
        O.KDEFAULTS.clear(); O.KDEFAULTS.update(old)
    best = None
    for k in cands:
        k = clean(k); ok, inf = verify(k)
        if not ok: continue
        m = metrics(k)
        if caps.get('A') is not None and m[0] > caps['A']: continue
        if caps.get('AD') is not None and m[1] > caps['AD']: continue
        if caps.get('GD') is not None and m[3] > caps['GD']: continue
        if best is None or (m[2], m[3]) < (best[1][2], best[1][3]): best = (k, m)
    info['kernel_bin_path'] = str(KDIR / 'bin' / info.get('kernel_bin', ''))
    return (best[0] if best else None), info


class Recorder:
    """adapter on common.Recorder: offer(c, parent, method) -> path or None"""

    def __init__(self, op, target, out, start, params, argv, seed, engine):
        self.op = op; self.tid = target; self.out = Path(out); self.t = limits(target)
        cmd = 'cd %s && python3 %s' % (os.getcwd(), ' '.join(argv))
        self.R = C.Recorder(out, op, target, start, seed, cmd, {'engine': engine, 'operator': op},
                            params, kernel=kernel_path())
        self.start_m = self.R.start_tuple
        self.notes = self.R.notes

    @property
    def front(self):
        pts = [(t[2], t[3]) for t in self.R.points]
        if self.start_m and C.in_limits(self.start_m, self.tid): pts.append((self.start_m[2], self.start_m[3]))
        return pts

    def dominated(self, m):
        return any(g <= m[2] and d <= m[3] for g, d in self.front)

    def offer(self, c, parent, method, extra=None, kernel_bin=None):
        c = clean(c)
        m = metrics(c)
        if not C.in_limits(m, self.tid): return None
        if self.start_m and all(a <= b for a, b in zip(self.start_m, m)): return None   # no worse-than-start points
        par = Path(parent) if parent else None
        lin = [{'parent': str(par.resolve()) if par else None,
                'parent_sha256': C.sha256(par) if par and par.exists() else None,
                'parent_tuple': list(metrics(load(par))) if par and par.exists() else None,
                'method': method}]
        how = '%s %s' % (method.get('stage', ''), json.dumps({k: v for k, v in method.items() if k in ('cap', 'kernel_seed', 'plan_seed', 'pw', 'build_G', 'parent_how', 'caps')}, default=str))
        p = self.R.offer(c, how=how, lineage=lin)
        if p:
            print('RECORDED', p.name, flush=True)
        return p

    def write(self, status=None):
        if status: self.R.finish(status)
        else: self.R.write_result()


def spawn_workers(argv, cpus, seed, out):
    """--cpus K > 1: run K-1 extra copies of this operator with --cpus 1 and seeds seed + 1000 i into out/w<i>;
    the caller is worker 0 and merges with merge_workers at the end."""
    procs = []
    for i in range(1, cpus):
        a = list(argv)

        def setf(flag, val):
            if flag in a: a[a.index(flag) + 1] = str(val)
            else: a.extend([flag, str(val)])
        setf('--cpus', 1); setf('--seed', seed + 1000 * i); setf('--out', str(Path(out) / ('w%d' % i)))
        setf('--shard', '%d/%d' % (i, cpus))
        lf = open(Path(out) / ('w%d.log' % i), 'w')
        procs.append(subprocess.Popen([sys.executable] + a, stdout=lf, stderr=subprocess.STDOUT))
    return procs


def merge_workers(rec, procs, deadline):
    for p in procs:
        try:
            p.wait(timeout=max(1, deadline - time.time()))
        except subprocess.TimeoutExpired:
            p.kill()
    for wd in sorted(rec.out.glob('w*')):
        if not wd.is_dir(): continue
        for f in sorted(wd.glob('%s-a*.circ.txt' % rec.op)):
            try:
                c = load(f); m = metrics(c)
            except Exception:
                continue
            if rec.dominated(m): continue
            sj = f.with_suffix('').with_suffix('.json')
            lin = json.load(open(sj)).get('lineage') if sj.exists() else None
            rec.R.offer(c, how='worker %s: %s' % (wd.name, f.name), lineage=lin)
