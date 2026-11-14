#!/usr/bin/env python3
"""Paired summary of a batch directory: per (case, arm) final G (and GD), times to reach thresholds."""
import json, sys, statistics
from collections import defaultdict
from pathlib import Path

d = Path(sys.argv[1])
recs = [json.loads(p.read_text()) for p in sorted(d.glob('*.json')) if p.name != "plan.json"]
by = defaultdict(dict)
for r in recs:
    case, armname, _ = r['tag'].rsplit('-', 2)       # tag = CASE-ARM-sSEED
    by[case].setdefault(armname, []).append(r)
for case, arms in sorted(by.items()):
    print('==', case, 'start', arms[next(iter(arms))][0]['start_metrics'])
    for arm, rs in sorted(arms.items()):
        rs.sort(key=lambda r: r['seed'])
        gs = [r['metrics'][2] for r in rs]
        st = rs[0]['start_metrics'][2]
        line = ' '.join('%d/%d' % (r['metrics'][2], r['metrics'][3]) for r in rs)
        # time to reach start-1, start-2, ..., best overall
        ttr = []
        for r in rs:
            imps = r['improvements']
            ttr.append(imps[-1]['t'] if imps else None)
        ch = rs[0]['stats'].get('chain', {})
        chs = [r['stats'].get('chain', {}) for r in rs]
        cimp = sum(c.get('imp', 0) for c in chs); cnd = sum(c.get('imp', 0) - c.get('direct', 0) for c in chs)
        cia = sum(c.get('imp_and', 0) for c in chs)
        bmv = defaultdict(int)
        for r in rs:
            for i in r['improvements']: bmv[i['mv']] += 1
        print('  %-8s n=%d median G %s mean %.2f  min %d  G/GD: %s  t_last_imp %s  chain imp %d (via repair %d, AND-kick %d) best-moves %s' % (
            arm, len(rs), statistics.median(gs), statistics.mean(gs), min(gs), line,
            [round(t) if t is not None else None for t in ttr], cimp, cnd, cia, dict(bmv)))
