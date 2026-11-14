"""Admissions of a memetic run with A <= AMAX: tuple, mechanism, parents, time to result.
python3 lowsum.py RUNDIR [AMAX]"""
import json, sys
from pathlib import Path

d = Path(sys.argv[1]); amax = int(sys.argv[2]) if len(sys.argv) > 2 else 31
ev = [json.loads(l) for l in (d / 'log.jsonl').read_text().splitlines()]
t0 = ev[0]['ts']
adm = {}
for f in (d / 'admitted').glob('*.json'):
    j = json.loads(f.read_text()); adm[f.stem] = j
rows = []
for e in ev:
    if e['ev'] == 'admit': rows.append((tuple(e['m']), 'splice', e['ts'] - t0, e['h']))
    if e['ev'] == 'polished' and e['admitted']: rows.append((tuple(e['m']), 'polish', e['ts'] - t0, e.get("new")))
lo = [r for r in rows if r[0][0] <= amax]
def leq(u, m): return all(a <= b for a, b in zip(u, m))
nd = [r for r in lo if not any(o[0] != r[0] and leq(o[0], r[0]) for o in rows)]
print('admissions %d, with A<=%d: %d, non-dominated: %d' % (len(rows), amax, len(lo), len(nd)))
for m, kind, t, h in sorted(nd):
    o = adm.get(h, {}).get('origin', {})
    if kind == 'polish':
        desc = 'polish of %s %s caps %s, t_last_imp %s s' % (o.get('from'), o.get('from_m'), o.get('caps'), o.get('time_to_result_s'))
    else:
        desc = 'splice front %s LX%s + back %s LY%s (%s interface gates)' % (o.get('front'), o.get('LX'), o.get('back'), o.get('LY'), o.get('interface'))
    print('%-16s %s at %.0f min: %s' % ('/'.join(map(str, m)), h, t / 60, desc))
