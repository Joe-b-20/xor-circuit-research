#!/usr/bin/env python3
"""P6: harvest kernel job results (DIR/jobs/*/best.bfx) that are new (G, GD) Pareto points among
A<=35 AD<=3 circuits (vs found/ and the archive baseline), and save them with save.py sidecars.

    python3 harvest.py RUNDIR --target T08 --command "the run's exact command"
"""
import sys, json, re, subprocess, argparse
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux.hub.common import load, metrics, verify   # noqa: E402

FOUND = Path.home() / 'xs-campaigns/2026-11-15-targets/P6/found'
BASE = [(140, 25), (141, 19), (143, 18), (144, 17), (147, 16), (155, 15), (162, 14), (177, 13), (139, 27)]


def known():
    pts = list(BASE)
    for f in FOUND.glob('*.json'):
        d = json.loads(f.read_text())
        if d.get('A', 99) <= 35 and d.get('AD', 9) <= 3: pts.append((d['G'], d['GD']))
    return pts


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('rundir'); ap.add_argument('--target', default='T08')
    ap.add_argument('--command', default=''); ap.add_argument('--method', default='')
    a = ap.parse_args()
    R = Path(a.rundir)
    kb = sorted((Path.home() / 'xs-campaigns/2026-11-15-targets/P6/kbin/bin').glob('bfx-*'))
    for jd in sorted((R / 'jobs').glob('*')):
        bp = jd / 'best.bfx'
        if not bp.exists(): continue
        c = load(bp); m = metrics(c)
        if m[0] > 35 or m[1] > 3: continue
        pts = known()
        if any(g <= m[2] and d <= m[3] for g, d in pts): continue
        ok, inf = verify(c)
        if not ok: print('verify fail', bp, inf); continue
        cfg = dict(l.split(' ', 1) for l in (jd / 'kernel.cfg').read_text().splitlines() if ' ' in l)
        meth = a.method or ('P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel '
                            'hub.ops._kernel caps A%s AD%s GD%s objective %s, %s s stage' %
                            (cfg.get('cap.a'), cfg.get('cap.ad'), cfg.get('cap.gd'), cfg.get('lex'), cfg.get('seconds')))
        r = subprocess.run(['python3', str(HERE / 'save.py'), str(bp), '--target', a.target, '--start', str(jd / 'start.bfx'),
                            '--method', meth, '--command', a.command, '--seed', cfg.get('seed', '').strip(),
                            '--elapsed', cfg.get('seconds', '0').strip(), '--kernel-bin', str(kb[-1]) if kb else '',
                            '--note', 'job dir %s (start.bfx = stage start; stage 0 start = hybrid build of the parent in pull.jsonl)' % jd],
                           capture_output=True, text=True)
        print(m, r.stdout.splitlines()[1] if r.stdout else r.stderr[-300:])


if __name__ == '__main__':
    main()
