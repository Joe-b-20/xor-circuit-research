#!/usr/bin/env python3
"""Every 20 min until the deadline: summarise the long run (both arms) into E/STATUS-live.md.
python3 status_live.py LONGDIR HOURS"""
import json, sys, time
from collections import Counter
from pathlib import Path

d = Path(sys.argv[1]); end = time.time() + float(sys.argv[2]) * 3600
pub_cache = None


def leq(u, m): return all(a <= b for a, b in zip(u, m))


while True:
    lines = ['# Track E long run, live summary', '', 'written %s UTC by status_live.py (%s)' % (time.strftime('%Y-%m-%d %H:%M', time.gmtime()), d), '']
    arms = {}
    for arm in (sys.argv[3].split(",") if len(sys.argv) > 3 else ("splice", "control")):
        lf = d / arm / 'log.jsonl'
        if not lf.exists(): continue
        ev = [json.loads(l) for l in lf.read_text().splitlines() if l.strip()]
        cnt = Counter(e['ev'] for e in ev)
        adm = [tuple(e['m']) for e in ev if e['ev'] == 'admit'] + [tuple(e['m']) for e in ev if e['ev'] == 'polished' and e['admitted']]
        nd = sorted({m for m in adm if not any(u != m and leq(u, m) for u in adm)})
        arms[arm] = set(nd)
        t0 = ev[0]['ts']
        lines.append('## %s arm: %d events, %d polishes (%d admitted), %d splice steps, %d splice admits, %.1f h' % (
            arm, len(ev), cnt['polished'], sum(1 for e in ev if e['ev'] == 'polished' and e['admitted']),
            cnt['spliced'], cnt['admit'], (ev[-1]['ts'] - t0) / 3600))
        lines.append('admitted tuples non-dominated among this arm\'s admissions (A AD G GD): ' + ', '.join('%d/%d/%d/%d' % m for m in nd))
        lines.append('')
    if 'splice' in arms and 'control' in arms:
        s, c = arms['splice'], arms['control']
        lines.append('splice-arm points not dominated by any control-arm point: %d; control-arm points not dominated by splice: %d' % (
            sum(1 for m in s if not any(leq(u, m) for u in c)), sum(1 for m in c if not any(leq(u, m) for u in s))))
    (d.parent / ("STATUS-live.md" if d.name == "long1" else "STATUS-live-%s.md" % d.name)).write_text('\n'.join(lines) + '\n')
    if time.time() > end: break
    time.sleep(1200)
