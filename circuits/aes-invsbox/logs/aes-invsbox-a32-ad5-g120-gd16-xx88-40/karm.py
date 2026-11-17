#!/usr/bin/env python3
"""Kernel arm of the idea-09 A/B: hub op_polish settings (hub/ops.py KDEFAULTS, caps = own A, AD, GD,
objective a,ad,cost,gd, keep_bests) on one start for T seconds; every kernel best that is inside
A <= A0, AD <= AD0 and not weakly dominated by the start goes through ops/common.Recorder (aes_check).

    karm.py --in START --seconds T --seed S --out DIR
"""
import argparse, json, resource, subprocess, sys, time
from pathlib import Path
WT = Path.home() / 'xcr-idea-09' / 'search' / 'nonlinear' / 'boolflux'
sys.path.insert(0, str(WT / 'ops'))
import common as OC                       # noqa: E402
from boolflux import core, objective as OBJ   # noqa: E402
from boolflux.hub.ops import KDEFAULTS, kernel_bin   # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument('--in', dest='inp'); ap.add_argument('--seconds', type=float)
ap.add_argument('--seed', type=int); ap.add_argument('--out'); ap.add_argument('--gd', type=int)
a = ap.parse_args()
OC.init_function(argparse.Namespace(inp=a.inp, function='auto'))
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
t0 = time.time()
c = OC.load(a.inp); A, AD, G, GD = OC.metrics(c)
rec = OC.Recorder(out, 'kpolish', a.inp, a.inp, a.seed, ' '.join(sys.argv), 'kernel polish (hub op_polish settings)',
                  {'seconds': a.seconds, 'gd_cap': a.gd or GD}, t0=t0, budget_s=a.seconds)
sp = out / 'start.bfx'; sp.write_text(core.to_kernel(c)); bp = out / 'best.bfx'
cfg = dict(KDEFAULTS); cfg.update(OBJ.weights('a,ad,cost,gd'))
for op in (8, 6, 9, 3): cfg['cost.%d' % op] = 1
cfg.update({'cap.a': A, 'cap.ad': AD, 'cap.gd': a.gd or GD, 'in': sp, 'out': bp, 'seed': a.seed, 'seconds': a.seconds,
            'clock': 'cpu'})
kd = out / 'bests'; kd.mkdir(exist_ok=True); cfg['keep_bests'] = kd
(out / 'kernel.cfg').write_text(''.join('%s %s\n' % kv for kv in cfg.items()))
kb = kernel_bin(OC.CACHE)
r0 = resource.getrusage(resource.RUSAGE_CHILDREN)
with open(out / 'kernel.log', 'w') as lf:
    rc = subprocess.run([str(kb), str(out / 'kernel.cfg')], stdout=lf, stderr=subprocess.STDOUT).returncode
r1 = resource.getrusage(resource.RUSAGE_CHILDREN)
kcpu = r1.ru_utime + r1.ru_stime - r0.ru_utime - r0.ru_stime
cands = sorted(kd.glob('best-*.bfx'), key=lambda p: int(p.stem.split('-')[1])) + ([bp] if bp.exists() else [])
for p in cands:
    cc = core.from_kernel(p.read_text(), 'best')
    rec.offer(cc.live(), how='kernel best %s' % p.name)
rec.finish('ok', {'kernel': {'rc': rc, 'cpu_s': round(kcpu, 2), 'bests': len(cands)}})
