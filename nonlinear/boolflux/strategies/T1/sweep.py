#!/usr/bin/env python3
"""Sweep T1 scratch/job dirs for kernel outputs (best.bfx, also start.bfx) that were never harvested (a job killed
by a worker stop).  Every A <= 28 circuit not dominated by (or equal to) a hub archive record or a pinned NIST
circuit is verified and copied to FOUND/front/ (goal hits to FOUND/) with a sidecar naming its scratch path and
kernel.cfg; with --pool DIR every A <= 28 output is also copied to DIR (<cid>.bfx) as a start.

    python3 sweep.py FOUND_DIR [--pool DIR] ROOT...
"""
import hashlib, json, subprocess, sys, time
from pathlib import Path
PKG = Path('/home/joebachir20/xcr-boolflux/nonlinear/boolflux')
sys.path.insert(0, str(PKG.parent))
from boolflux.hub.common import core, metrics, verify, published   # noqa: E402
HUBAR = Path('/home/joebachir20/xs-campaigns/2026-11-14-hub/long/archive')
GOALS = {'B': (28, 4, 130, 22), 'C': (28, 5, 127, 19)}
found = Path(sys.argv[1]); args = sys.argv[2:]; pool = None
if args and args[0] == '--pool': pool = Path(args[1]); pool.mkdir(parents=True, exist_ok=True); args = args[2:]
leq = lambda q, m: all(a <= b for a, b in zip(q, m))
ref = set(published())
for f in HUBAR.glob('*.json'):
    if f.name == 'cells.json': continue
    r = json.loads(f.read_text()); ref.add((r['A'], r['AD'], r['G'], r['GD']))
n = 0; hits = []
for root in args:
    for p in list(Path(root).rglob('best.bfx')) + list(Path(root).rglob('start.bfx')):
        try: c = core.from_kernel(p.read_text(), 'x')
        except Exception: continue
        n += 1; m = metrics(c)
        if m[0] > 28: continue
        h = hashlib.sha1(core.to_kernel(c).encode()).hexdigest()[:12]
        if pool is not None and not (pool / (h + '.bfx')).exists(): (pool / (h + '.bfx')).write_text(core.to_kernel(c))
        goal = [g for g, gm in GOALS.items() if leq(m, gm)]
        if any(leq(q, m) for q in ref) and not goal: continue
        if not verify(c)[0]: print('VERIFY FAIL', p); continue
        d = found if goal else found / 'front'; d.mkdir(parents=True, exist_ok=True)
        name = 'aes-sbox-a%d-ad%d-g%d-gd%d-%s' % (m + (h,))
        if (d / (name + '.bfx')).exists(): continue
        (d / (name + '.bfx')).write_text(core.to_kernel(c))
        r = subprocess.run([sys.executable, str(PKG / 'campaigns' / 'aes_check.py'), str(d / (name + '.bfx')), '--json', str(d / (name + '.check.json'))],
                           capture_output=True, text=True)
        cfg = p.parent / 'kernel.cfg'
        json.dump({'tuple': m, 'goal': goal, 'source': str(p), 'harvested_by': 'strategies/T1/sweep.py (unharvested kernel output of a stopped job)',
                   'kernel_cfg': cfg.read_text() if cfg.exists() else None, 'time_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                   'aes_check_rc': r.returncode}, open(d / (name + '.json'), 'w'), indent=1)
        hits.append((m, str(p), r.returncode)); print('NEW', m, p, 'aes_check rc', r.returncode, flush=True)
print('scanned', n, 'new', len(hits))
