#!/usr/bin/env python3
"""Q1: per operator and per chain: CPU, jobs, admissions, front admissions, value.  Output: text tables."""
import sys
from collections import defaultdict
from l1_lib import Data, CAMPS, GENERATORS, fmt, table, tier

D = Data()

print('## spans');
for c in CAMPS:
    s = D.span[c]; print(c, round((s[1] - s[0]) / 3600, 2), 'h', 'runs', len(D.runs[c]), 'cpu_h', round(sum(r['cpu_s'] for r in D.runs[c]) / 3600, 2))

# ---- per operator, all campaigns and per campaign/phase --------------------------------------
def opstats(runs_iter):
    S = defaultdict(lambda: defaultdict(float))
    for c, r in runs_iter:
        o = r['operator']; s = S[o]
        s['jobs'] += 1; s['cpu'] += r['cpu_s']; s['adm'] += r['admitted']; s['hubgain'] += r['gain']
        if r['admitted'] == 0: s['cpu0'] += r['cpu_s']
        v = 0; nf = 0
        for oc in r['outcome']:
            if oc['status'] == 'admitted' and (c, oc['id']) in D.val:
                x = D.val[(c, oc['id'])]; v += x['V']; nf += 1
                s['n_' + x['kind']] += 1
                m = D.m[oc['id']]
                if m[0] <= 31: s['V_A<=31'] += x['V']; s['nf_A<=31'] += 1
        s['V'] += v; s['nf'] += nf
        if nf == 0: s['cpuNoFront'] += r['cpu_s']
    return S

def show(S, title):
    rows = []
    tot = sum(s['cpu'] for s in S.values())
    for o, s in sorted(S.items(), key=lambda kv: -kv[1]['cpu']):
        h = s['cpu'] / 3600
        rows.append([o, int(s['jobs']), '%.2f' % h, '%.0f%%' % (100 * s['cpu'] / tot), int(s['adm']), int(s['nf']),
                     '%d/%d/%d/%d/%d' % (s['n_A'], s['n_AD'], s['n_G'], s['n_GD'], s['n_new']),
                     int(s['nf_A<=31']), '%.0f' % s['V'], '%.0f' % s['V_A<=31'], '%.1f' % (s['V'] / h if h else 0),
                     '%.2f' % (s['nf'] / h if h else 0), '%.0f%%' % (100 * s['cpuNoFront'] / s['cpu'] if s['cpu'] else 0),
                     '%.1f' % (s['hubgain'] / h if h else 0)])
    print('\n### ' + title + '  (total %.2f CPU-h)' % (tot / 3600))
    print(table(rows, ['op', 'jobs', 'CPU-h', 'share', 'adm', 'front adm', 'kind A/AD/G/GD', 'front A<=31', 'V', 'V A<=31', 'V/CPU-h', 'front/CPU-h', 'CPU in jobs w/o front adm', 'hub gain/CPU-h']))

allruns = [(c, r) for c in CAMPS for r in D.runs[c]]
show(opstats(allruns), 'all hub campaigns')
for c in CAMPS:
    if c == 'long':
        for ph in ['long1', 'long2', 'long3', 'long4a', 'long4']:
            rr = [(c, r) for r in D.runs[c] if D.phase(c, r['ts_end'] - r['wall_s']) == ph]
            if rr: show(opstats(rr), ph)
    else:
        show(opstats([(c, r) for r in D.runs[c]]), c)

# ---- chains: operator x operator of the target (CPU-accounted), and lineage signatures of valued points ----
def tkind(c, r):
    t = r['target']
    if t not in D.recs: return '?'
    o = D.op(t)
    return o

S = defaultdict(lambda: defaultdict(float))
for c, r in allruns:
    key = (r['operator'], tkind(c, r)); s = S[key]
    s['jobs'] += 1; s['cpu'] += r['cpu_s']; s['adm'] += r['admitted']
    for oc in r['outcome']:
        if oc['status'] == 'admitted' and (c, oc['id']) in D.val:
            x = D.val[(c, oc['id'])]; s['V'] += x['V']; s['nf'] += 1
            if D.m[oc['id']][0] <= 31: s['nfA31'] += 1; s['VA31'] += x['V']
rows = []
for k, s in sorted(S.items(), key=lambda kv: -kv[1]['cpu']):
    h = s['cpu'] / 3600
    rows.append(['%s on %s' % k, int(s['jobs']), '%.2f' % h, int(s['adm']), int(s['nf']), int(s['nfA31']), '%.0f' % s['V'], '%.0f' % s['VA31'], '%.1f' % (s['V'] / h if h else 0)])
print('\n### operator x maker of its target (all campaigns)')
print(table(rows, ['op on target-made-by', 'jobs', 'CPU-h', 'adm', 'front adm', 'front A<=31', 'V', 'V A<=31', 'V/CPU-h']))

# lineage signature (depth 2) of valued points
S = defaultdict(lambda: defaultdict(float))
for (c, i), x in D.val.items():
    if D.op(i) == 'base': key = 'ingest'
    else: key = D.chain(i, 2)
    s = S[key]; s['n'] += 1; s['V'] += x['V']
    if D.m[i][0] <= 31: s['nA31'] += 1; s['VA31'] += x['V']
rows = [[k, int(s['n']), int(s['nA31']), '%.0f' % s['V'], '%.0f' % s['VA31']] for k, s in sorted(S.items(), key=lambda kv: -kv[1]['V'])]
print('\n### depth-2 lineage signature of front admissions (all campaigns)')
print(table(rows, ['chain', 'front adm', 'of which A<=31', 'V', 'V A<=31']))

# ops present anywhere in the lineage (enabled value)
S = defaultdict(lambda: defaultdict(float))
totV = 0
for (c, i), x in D.val.items():
    ops = {D.op(a) for a in D.ancestors(i)} | {D.op(i)}
    ops.discard('base'); totV += x['V']
    for o in ops:
        S[o]['n'] += 1; S[o]['V'] += x['V']
        if D.m[i][0] <= 31: S[o]['nA31'] += 1; S[o]['VA31'] += x['V']
rows = [[k, int(s['n']), int(s['nA31']), '%.0f' % s['V'], '%.0f' % s['VA31']] for k, s in sorted(S.items(), key=lambda kv: -kv[1]['V'])]
print('\n### operator present anywhere in the lineage of a front admission (enabled value; total V %.0f, n %d)' % (totV, len(D.val)))
print(table(rows, ['op in lineage', 'front adm', 'of which A<=31', 'V', 'V A<=31']))

# ---- the valuable points: every front admission with A <= 31, and goal events ----------------
rows = []
for (c, i), x in sorted(D.val.items(), key=lambda kv: D.recs[kv[0][1]]['t_admit']):
    m = D.m[i]
    if m[0] > 31: continue
    r = D.recs[i]
    rows.append([fmt(m), D.phase(c, r['t_admit']), x['kind'], x['delta'], '%.0f' % x['V'], i, D.chain(i, 99)])
print('\n### every front admission with A <= 31 (time order)')
print(table(rows, ['A/AD/G/GD', 'campaign', 'type', 'delta', 'V', 'id', 'full lineage']))

rows = []
for e in D.goalev:
    rows.append([e['goal'], D.phase(e['camp'], D.recs[e['id']]['t_admit']), fmt(e['m']), e['dist'], e['id'], D.chain(e['id'], 99)])
print('\n### goal-near admissions: non-dominated in (G, GD) inside the goal class (A, AD caps) and within 6 gates / 4 levels of the goal box')
print(table(rows, ['goal', 'campaign', 'A/AD/G/GD', 'G excess + GD excess', 'id', 'full lineage']))
S = defaultdict(lambda: defaultdict(int))
for e in D.goalev:
    S[D.op(e['id'])][e['goal']] += 1
    for o in {D.op(a) for a in D.ancestors(e['id'])} - {'base'}: S['lineage:' + o][e['goal']] += 1
print(table([[o] + [s[g] for g in 'BCDEFG'] + [sum(s.values())] for o, s in sorted(S.items())], ['made by / lineage contains', 'B', 'C', 'D', 'E', 'F', 'G', 'all']))
from collections import Counter
print('\nhub gain kind of the %d front admissions:' % len(D.val), Counter(x['hub_kind'] for x in D.val.values()), ' cap-box kind:', Counter(x['kind'] for x in D.val.values()))
