#!/usr/bin/env python3
"""Target starvation and the join partner list.
 1. replay of the long archive cells (K = 4 ties per cell): number of front ids over time vs join's partner limit 300
 2. for every front admission with A <= 31 or near a goal: kernel jobs it received after admission
 3. coverage of the final front by polish / pull
"""
import json
from collections import defaultdict, Counter
from l1_lib import Data, CAMPS, fmt, table, GOALS, goal_near, leq

D = Data()
K = 4
ids = sorted(D.inarch['long'], key=lambda i: D.recs[i]['t_admit'])
t0 = D.span['long'][0]
cells = {}
marks = [t0 + 3600 * h for h in (0, 0.1, 1, 2, 2.1, 3, 4, 5, 5.65, 6, 6.8)]
mi = 0


def front_ids():
    pts = {(k[0], k[1], D.m[v[0]][2], k[2]) for k, v in cells.items()}
    fr = {p for p in pts if not any(q != p and leq(q, p) for q in pts)}
    return [i for k, v in cells.items() for i in v if (k[0], k[1], D.m[i][2], k[2]) in fr], len(fr)


print('### 1. long: front tuples and front ids (targets; join partners are (front ids + shuffled other cell minima)[:300])')
rows = []
for i in ids + [None]:
    t = D.recs[i]['t_admit'] if i else 1e18
    while mi < len(marks) and marks[mi] <= t:
        f, n = front_ids(); others = sum(1 for k, v in cells.items() if v and v[0] not in set(f))
        rows.append(['%.1f' % ((marks[mi] - t0) / 3600), D.phase('long', marks[mi]), n, len(f), others, max(0, 300 - (len(f) - 1))])
        mi += 1
    if i is None: break
    m = D.m[i]; k = (m[0], m[1], m[3]); cur = cells.get(k)
    if not cur or m[2] < D.m[cur[0]][2]: cells[k] = [i]
    elif m[2] == D.m[cur[0]][2] and len(cur) < K: cur.append(i)
print(table(rows, ['hours since 18:41 UTC', 'phase', 'front tuples', 'front ids', 'non-front cell minima', 'partner slots left for non-front circuits']))
final_front, _ = front_ids()

# join jobs: how many had any non-front partner?  (not logged per job; partners count only)
pc = Counter(r['op_info'].get('partners') for r in D.runs['long'] if r['operator'] == 'join')
print('join partner counts in long:', sorted(pc.items(), key=lambda kv: -kv[1])[:6])

# ---- 2. kernel jobs received by valuable admissions after they were admitted -------------------------
jobs = defaultdict(list)
for r in D.runs['long']:
    jobs[r['target']].append(r)
tjobs = defaultdict(list)
for r in D.runs['long']:
    tjobs[tuple(r['target_metrics'])].append(r)
tend = D.span['long'][1]
rows = []
for (c, i), x in sorted(D.val.items(), key=lambda kv: D.recs[kv[0][1]]['t_admit']):
    if c != 'long': continue
    m = D.m[i]
    if not (m[0] <= 31 or any(goal_near(m, g) for g in GOALS)): continue
    ta = D.recs[i]['t_admit']
    oc = Counter(r['operator'] for r in jobs[i]); ot = Counter(r['operator'] for r in tjobs[m] if r['ts_end'] > ta)
    infront = i in final_front
    kern = [r for r in tjobs[m] if r['operator'] in ('polish', 'pull', 'osc', 'trb') and r['ts_end'] > ta]
    first = min((r['ts_end'] - r['wall_s'] - ta) / 60 for r in kern) if kern else None
    rows.append([fmt(m), i, '%.2f' % ((ta - t0) / 3600), '%.1f' % ((tend - ta) / 3600), 'yes' if infront else 'no',
                 ' '.join('%s %d' % kv for kv in sorted(ot.items())) or '-', ot['polish'], ot['pull'], '-' if first is None else '%.0f' % first])
print('\n### 2. long: jobs on each valuable front admission (A <= 31 or near a goal) after its admission, counted on its TUPLE (all equal-tuple copies)')
print(table(rows, ['A/AD/G/GD', 'id', 'admitted at h', 'hours until stop', 'on final front', 'jobs by op', 'polish', 'pull', 'min to first kernel job']))

# ---- 3. coverage of the final front in long3+long4 -------------------------------------------------------
st = sorted(e['ts'] for e in D.events['long'] if e['ev'] == 'start')
for name, a, b in (('long3', st[2], st[3]), ('long4', st[4], 1e18)):
    cnt = defaultdict(Counter)
    for r in D.runs['long']:
        t = r['ts_end'] - r['wall_s']
        if a <= t < b: cnt[r['operator']][r['target']] += 1
    alive = [i for i in final_front if D.recs[i]['t_admit'] < a]     # on the final front and present for the whole phase
    tup = {D.m[i] for i in alive}
    print('\n### 3. %s: final-front ids present for the whole phase: %d ids / %d tuples' % (name, len(alive), len(tup)))
    rows = []
    for o in ('polish', 'pull', 'trb', 'osc', 'gen_skel', 'join'):
        per = [cnt[o][i] for i in alive]
        pt = defaultdict(int)
        for i in alive: pt[D.m[i]] += cnt[o][i]
        rows.append([o, sum(cnt[o].values()), sum(1 for x in per if x == 0), '%.0f%%' % (100 * sum(1 for x in per if x == 0) / max(1, len(per))),
                     sum(1 for v in pt.values() if v == 0), '%.1f' % (sum(pt.values()) / max(1, len(pt))), max(pt.values()) if pt else 0])
    print(table(rows, ['op', 'jobs in phase', 'ids with 0 jobs', 'share', 'tuples with 0 jobs', 'mean jobs per tuple', 'max per tuple']))
