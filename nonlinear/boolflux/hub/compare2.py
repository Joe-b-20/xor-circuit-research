#!/usr/bin/env python3
"""Compare hub campaigns that started from the same archive state.

    python3 compare2.py BASELINE_CAMPAIGN NAME=CAMPAIGN:CPUS ... [--check] [--json OUT]
Per arm: records admitted after the arm's (last) start event; new frontier points = not dominated by
the pinned NIST set nor by the baseline's cell minima, nor strictly inside the arm; per CPU-hour; by
operator; lineage (operator chain back to records of the baseline); cross-dominance between arms."""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from boolflux.hub.archive import Archive                 # noqa: E402
from boolflux.hub.common import leq, published           # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
check = '--check' in sys.argv
jout = sys.argv[sys.argv.index('--json') + 1] if '--json' in sys.argv else None
if jout in args: args.remove(jout)
base = Archive(args[0]); pub = list(published())
basepts = base.points() + pub
res = {}; fronts = {}
for spec in args[1:]:
    # NAME=CAMPAIGN:CPUS, or NAME=CAMPAIGN:auto:START_TS:END_TS (time window; CPU-h = sum of the jobs' CPU s)
    name, rest = spec.split('=', 1); parts = rest.split(':'); d = Path(parts[0])
    ev = [json.loads(l) for l in (d / 'events.jsonl').read_text().splitlines() if l.strip()]
    if len(parts) >= 4:
        ncpu = parts[1]; st = float(parts[2]); en = float(parts[3])
    else:
        ncpu = int(parts[1]); st = [e for e in ev if e.get('ev') == 'start'][-1]['ts']; en = ev[-1]['ts']
    hours = (en - st) / 3600
    ar = Archive(d)
    items = [(tuple(r[k] for k in ('A', 'AD', 'G', 'GD')), i, r) for i, r in ar.rec.items() if st < r['t_admit'] <= en]
    allm = [m for m, i, r in items]
    fr = {}
    for m, i, r in sorted(items, key=lambda x: x[2]['t_admit']):
        if any(leq(u, m) for u in basepts): continue
        if any(u != m and leq(u, m) for u in allm): continue
        fr.setdefault(m, (i, r))

    def lin(i, depth=0):
        r = ar.rec.get(i)
        if r is None or r['t_admit'] <= st or depth > 6: return 'base'
        return '%s(%s)' % (r['operator'], ','.join(lin(p, depth + 1) for p in r['parents']))
    stats = {}
    sf = d / 'stats.jsonl'
    for l in sf.read_text().splitlines():
        x = json.loads(l)
        if x['ts'] < st or x['ts'] > en: continue
        v = stats.setdefault(x['op'], [0, 0, 0.0, 0.0]); v[0] += 1; v[1] += x['admitted']; v[2] += x['cpu_s']; v[3] += x['gain']
    pts = []
    for m, (i, r) in sorted(fr.items()):
        row = {'m': m, 'id': i, 'operator': r['operator'], 'lineage': lin(i), 'run_id': r.get('run_id'),
               'min_after_start': round((r['t_admit'] - st) / 60, 1)}
        if check:
            sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'campaigns'))
            import aes_check
            cr = aes_check.check(str(d / 'archive' / (i + '.bfx')))
            row['aes_check_ok_new'] = bool(cr['ok'] and cr['new_point'])
        pts.append(row)
    fronts[name] = list(fr)
    op_cpu_h = sum(v[2] for v in stats.values()) / 3600
    cpu_h = op_cpu_h if ncpu == 'auto' else hours * ncpu
    res[name] = {'hours': round(hours, 2), 'cpus': ncpu, 'cpu_h': round(cpu_h, 2), 'op_cpu_h': round(op_cpu_h, 2),
                 'admissions': len(items),
                 'new_frontier_points': len(fr), 'per_cpu_h': round(len(fr) / cpu_h, 2) if cpu_h else None,
                 'operators': {k: {'jobs': v[0], 'admitted': v[1], 'cpu_s': round(v[2]), 'gain': round(v[3], 2),
                                   'gain_per_cpu_h': round(v[3] / (v[2] / 3600), 2) if v[2] else 0} for k, v in stats.items()},
                 'points': pts}
for a in res:
    res[a]['not_dominated_by'] = {b: sum(1 for m in fronts[a] if not any(leq(u, m) for u in fronts[b])) for b in res if b != a}
out = json.dumps(res, indent=1, default=str)
if jout: Path(jout).write_text(out + '\n')
for a, r in res.items():
    print('== %s: %.2f CPU-h, admissions %d, new frontier points %d (%.2f/CPU-h), not dominated by %s' % (
        a, r['cpu_h'], r['admissions'], r['new_frontier_points'], r['per_cpu_h'] or 0, r['not_dominated_by']))
    for k, v in sorted(r['operators'].items()):
        print('   op %-12s jobs %3d adm %4d cpu %6ds gain %6.2f  (%.2f / CPU-h)' % (k, v['jobs'], v['admitted'], v['cpu_s'], v['gain'], v['gain_per_cpu_h']))
    for p in r['points']:
        print('   %-14s %5.1f min  %s%s' % ('/'.join(map(str, p['m'])), p['min_after_start'], p['lineage'],
                                         '' if 'aes_check_ok_new' not in p else ('  check OK-new' if p['aes_check_ok_new'] else '  CHECK FAIL')))
