"""Run the copied BoolFlux gate kernel (strategies/D/bfx, built from kernel/bfx.c) on a circuit."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))  # nonlinear
from boolflux import core  # noqa: E402

KBIN = HERE / 'bfx'
DEFAULTS = {'T0': 0.6, 'Tperiod_it': 20000, 'stall_it': 60000, 'uphill': 1.0, 'max_excess': 8,
            'mv.resub1': 1, 'mv.resub2': 2, 'mv.resub3': 1, 'dmax': 220, 'pdiv': 90,
            'nl_samples': 12, 'cand_cap': 40, 'fraig': 1}


def kernel(c, workdir, tag, seconds, seed, cap_gd=None, cap_ad=None, cap_a=None,
           weights=(('w.cost', 1.0), ('w.a', 1e-4), ('w.gd', 1e-8)), extra=None):
    wd = Path(workdir)
    wd.mkdir(parents=True, exist_ok=True)
    sp = wd / ('%s.start.bfx' % tag)
    bp = wd / ('%s.best.bfx' % tag)
    cp = wd / ('%s.cfg' % tag)
    sp.write_text(core.to_kernel(c), encoding='utf-8')
    cfg = dict(DEFAULTS)
    for k in ('w.cost', 'w.g', 'w.a', 'w.gd', 'w.ad'):
        cfg[k] = 0.0
    cfg.update(dict(weights))
    for op in (8, 6, 9, 3):
        cfg['cost.%d' % op] = 1
    if cap_gd is not None:
        cfg['cap.gd'] = cap_gd
    if cap_ad is not None:
        cfg['cap.ad'] = cap_ad
    if cap_a is not None:
        cfg['cap.a'] = cap_a
    cfg['lex'] = 'cost,a,gd'
    cfg.update(extra or {})
    cfg.update({'in': str(sp), 'out': str(bp), 'seed': seed, 'seconds': seconds, 'iters': -1})
    cp.write_text(''.join('%s %s\n' % kv for kv in cfg.items()), encoding='utf-8')
    r = subprocess.run([str(KBIN), str(cp)], capture_output=True, text=True, timeout=seconds + 120)
    if r.returncode != 0:
        raise RuntimeError('bfx failed: %s' % r.stdout[-500:] + r.stderr[-500:])
    c2 = core.from_kernel(bp.read_text(), c.name)
    c2.in_names = list(c.in_names)
    c2.out_names = list(c.out_names)
    return c2, r.stdout
