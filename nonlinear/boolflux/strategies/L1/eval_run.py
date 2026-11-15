#!/usr/bin/env python3
"""Judge hub directories with the L1 measures (front admissions against the directory's own archive at
admission time + the pinned published set; cap-box value; goal-near admissions; goal hits).

    L1_OUT=/tmp/x python3 l1_load.py armA=/abs/hubdirA armB=/abs/hubdirB
    L1_OUT=/tmp/x python3 eval_run.py

Per directory and per operator: jobs, CPU-h, front admissions (all / A <= 31 / near a goal B-G / meeting
a goal), value V.  Reference rates of the 2026-11-14 hub era (65.9 CPU-h): 1.14 hub-made front admissions per
CPU-h, 0.52 with A <= 31, 0.29 near a goal box (6 gates / 4 levels), 0 goal hits.
"""
from collections import defaultdict
from l1_lib import Data, CAMPS, fmt, table, GOALS, goal_near, goal_dist

D = Data()
near = defaultdict(list)
for e in D.goalev: near[(e['camp'], e['id'])].append((e['goal'], e['dist']))
for c in CAMPS:
    S = defaultdict(lambda: defaultdict(float))
    for r in D.runs[c]:
        s = S[r['operator']]; s['jobs'] += 1; s['cpu'] += r['cpu_s']; s['adm'] += r['admitted']
        for oc in r['outcome']:
            if oc['status'] != 'admitted' or (c, oc['id']) not in D.val: continue
            x = D.val[(c, oc['id'])]; m = D.m[oc['id']]
            s['nf'] += 1; s['V'] += x['V']; s['nfA'] += m[0] <= 31
            s['near'] += bool(near.get((c, oc['id'])))
            s['hit'] += any(d == 0 for g, d in near.get((c, oc['id']), []))
    tot = defaultdict(float)
    for s in S.values():
        for k, v in s.items(): tot[k] += v
    S['ALL'] = tot
    print('\n## %s' % c)
    print(table([[o, int(s['jobs']), '%.2f' % (s['cpu'] / 3600), int(s['adm']), int(s['nf']), int(s['nfA']), int(s['near']), int(s['hit']), '%.0f' % s['V'],
                  '%.2f' % (s['nf'] / (s['cpu'] / 3600)) if s['cpu'] else '-', '%.1f' % (s['V'] / (s['cpu'] / 3600)) if s['cpu'] else '-']
                 for o, s in sorted(S.items(), key=lambda kv: -kv[1]['cpu'])],
                ['op', 'jobs', 'CPU-h', 'admitted', 'front adm', 'A<=31', 'near a goal', 'goal met', 'V', 'front adm/CPU-h', 'V/CPU-h']))
    pts = sorted((D.m[i], i) for (cc, i) in D.val if cc == c)
    for m, i in pts:
        tag = ' '.join('%s%s' % (g, '(MET)' if d == 0 else '(+%d)' % d) for g, d in near.get((c, i), []))
        if m[0] <= 31 or tag: print('  %-14s %s  %s  %s' % (fmt(m), i, tag, D.chain(i, 4)))
