#!/usr/bin/env python3
"""Goal view: CPU by goal relevance of the target, effort already spent on the goal-near tuples,
essential vs incidental joins / gen_skel in lineages, AND spans by class."""
import json
from collections import defaultdict, Counter
from l1_lib import Data, CAMPS, GENERATORS, fmt, table, tier, GOALS, HOME, OUT

D = Data()
struct = json.loads((OUT / 'struct.json').read_text())
allruns = [(c, r) for c in CAMPS for r in D.runs[c]]


def rv(c, r):
    n = 0; v = 0.0
    for oc in r['outcome']:
        if oc['status'] == 'admitted' and (c, oc['id']) in D.val:
            n += 1; v += D.val[(c, oc['id'])]['V']
    return n, v


def goal_of(m, gw=12, dw=6):
    """goals whose class contains m and whose box is within gw gates / dw levels"""
    return [g[0] for g in GOALS if m[0] <= g[1] and m[1] <= g[2] and m[2] <= g[3] + gw and m[3] <= g[4] + dw]


# ---- CPU by goal relevance of the target -----------------------------------------------------------
S = defaultdict(lambda: defaultdict(float))
for c, r in allruns:
    m = r['target_metrics']; gs = goal_of(m)
    k = 'goal window ' + '+'.join(gs) if gs else ('no goal window, A<=31' if m[0] <= 31 else 'no goal window, A>=32')
    s = S[k]; n, v = rv(c, r); s['jobs'] += 1; s['cpu'] += r['cpu_s']; s['nf'] += n; s['V'] += v
    for oc in r['outcome']:
        if oc['status'] == 'admitted' and goal_of(oc['metrics'], 6, 4) and (c, oc['id']) in D.val: s['goalnear'] += 1
tot = sum(s['cpu'] for s in S.values())
print('### CPU by goal relevance of the target (window: inside the goal class, G <= cap+12, GD <= cap+6)')
print(table([[k, int(s['jobs']), '%.2f' % (s['cpu'] / 3600), '%.0f%%' % (100 * s['cpu'] / tot), int(s['nf']), int(s['goalnear']), '%.0f' % s['V'], '%.1f' % (s['V'] / (s['cpu'] / 3600))]
             for k, s in sorted(S.items(), key=lambda kv: -kv[1]['cpu'])], ['target', 'jobs', 'CPU-h', 'share', 'front adm', 'front adm within 6/4 of a goal box', 'V', 'V/CPU-h']))

# ---- effort on the goal-near tuples ----------------------------------------------------------------------
KEY = [(28, 4, 131, 23), (28, 4, 132, 22), (28, 4, 133, 20), (28, 4, 135, 18), (28, 5, 127, 22), (28, 5, 128, 20), (28, 5, 130, 19), (28, 5, 133, 18), (28, 5, 125, 25), (28, 5, 124, 27),
       (29, 4, 130, 22), (29, 4, 129, 23), (29, 4, 131, 20), (32, 4, 116, 20), (32, 4, 117, 19), (32, 4, 119, 18), (32, 4, 115, 22), (32, 4, 114, 26),
       (32, 5, 104, 29), (32, 5, 105, 26), (31, 5, 114, 28), (33, 4, 105, 25), (35, 3, 139, 27), (35, 3, 140, 25), (35, 3, 141, 24), (35, 3, 142, 21), (43, 4, 141, 12), (48, 4, 151, 11)]
rows = []
for m in KEY:
    ops = Counter(); cpu = 0.0; adm = 0; nf = 0; best = Counter()
    for c, r in allruns:
        if tuple(r['target_metrics']) != m: continue
        ops[r['operator']] += 1; cpu += r['cpu_s']; adm += r['admitted']; nf += rv(c, r)[0]
        if r['operator'] in ('polish', 'pull', 'osc') and r['outcome']:
            mm = r['outcome'][0]['metrics']
            if mm[0] <= m[0] and mm[1] <= m[1] and mm[3] <= m[3]: best[mm[2] - m[2]] += 1
    rows.append([fmt(m), '+'.join(goal_of(m, 6, 4)) or '-', '%.2f' % (cpu / 3600), ' '.join('%s %d' % kv for kv in sorted(ops.items())), adm, nf,
                 ' '.join('%+d:%d' % kv for kv in sorted(best.items()))])
print('\n### effort already spent on goal-near and key tuples (all campaigns); kernel results within the target caps: dG:count')
print(table(rows, ['target tuple', 'near goal', 'CPU-h', 'jobs by op', 'adm', 'front adm', 'kernel-job result G minus target G under the same A/AD/GD caps']))

# ---- essential vs incidental ops in lineages ---------------------------------------------------------------
def essential(i):
    """ancestors (and self) that changed the tuple relative to all parents / changed the AND span"""
    out = Counter()
    for a in D.ancestors(i) | {i}:
        o = D.op(a)
        if o == 'base': continue
        ps = [p for p in D.recs[a]['parents'] if p in D.recs]
        same_tuple = any(D.m[p] == D.m[a] for p in ps)
        same_span = any(struct[p]['span'] == struct[a]['span'] for p in ps)
        out[(o, 'copy' if same_tuple else 'moved')] += 1
        if not same_span: out[(o, 'new span')] += 1
    return out

S = defaultdict(lambda: defaultdict(float))
for (c, i), x in D.val.items():
    e = essential(i)
    for o in ('join', 'gen_skel', 'trb', 'osc', 'pull', 'polish'):
        if e[(o, 'moved')]: S[o]['moved'] += 1; S[o]['Vmoved'] += x['V']
        elif e[(o, 'copy')]: S[o]['copyonly'] += 1; S[o]['Vcopy'] += x['V']
        if e[(o, 'new span')]: S[o]['newspan'] += 1; S[o]['Vspan'] += x['V']
print('\n### operator in the lineage of the %d front admissions: as a step that changed the tuple, only as equal-tuple copies, as a step that changed the AND span' % len(D.val))
print(table([[o, int(s['moved']), '%.0f' % s['Vmoved'], int(s['copyonly']), '%.0f' % s['Vcopy'], int(s['newspan']), '%.0f' % s['Vspan']] for o, s in S.items()],
            ['op', 'front adm with a tuple-changing step by op', 'V', 'only equal-tuple copies by op', 'V', 'with an AND-span-changing step by op', 'V']))

# what did the tuple-changing joins in valued lineages do (A change)?
C = Counter()
for (c, i), x in D.val.items():
    for a in D.ancestors(i) | {i}:
        if D.op(a) != 'join': continue
        ps = [p for p in D.recs[a]['parents'] if p in D.recs]
        if any(D.m[p] == D.m[a] for p in ps): continue
        C[(fmt(D.m[a]), ' x '.join(sorted(fmt(D.m[p]) for p in ps)), struct[a]['span'] in {struct[p]['span'] for p in ps})] += 1
print('tuple-changing joins inside valued lineages (result, parents, same span as a parent): count of front admissions below')
for k, v in sorted(C.items(), key=lambda kv: -kv[1])[:25]: print('  ', k, v)

# ---- AND spans by class ---------------------------------------------------------------------------------------
S = defaultdict(lambda: defaultdict(set))
for i in D.recs:
    m = D.m[i]; k = (min(m[0], 36), m[1]) if m[0] <= 36 else (36, m[1])
    S[k]['spans'].add(struct[i]['span']); S[k]['profiles'].add(struct[i]['profile']); S[k]['ids'].add(i)
    if D.op(i) == 'base': S[k]['basespans'].add(struct[i]['span'])
print('\n### distinct AND spans in all hub archives by (A, AD)   (A 36 = 36 and above)')
print(table([[k[0], k[1], len(s['ids']), len(s['spans']), len(s['basespans']), len(s['spans'] - s['basespans']), ' '.join(sorted(s['profiles'])[:8])] for k, s in sorted(S.items())],
            ['A', 'AD', 'records', 'distinct AND spans', 'of which among base circuits', 'new in the hub', 'AND level profiles']))
# new spans at A <= 29 made in the hub
rows = []
seen = set()
for i in sorted(D.recs, key=lambda i: D.recs[i]['t_admit']):
    sp = struct[i]['span']
    if sp in seen: continue
    seen.add(sp)
    if D.m[i][0] <= 30 and D.op(i) != 'base':
        ps = [p for p in D.recs[i]['parents'] if p in D.recs]
        low = (D.recs[i].get('operator_settings') or {}).get('lowered') or ''
        nfa = sum(1 for (c, j) in D.val if struct[j]['span'] == sp)
        rows.append([sp, fmt(D.m[i]), struct[i]['profile'], D.op(i) + (' ' + low if low else ''), ' x '.join('%s [%s]' % (fmt(D.m[p]), struct[p]['profile']) for p in ps), nfa])
print('\n### new AND spans with A <= 30 first made in the hub')
print(table(rows, ['span', 'first tuple', 'profile', 'made by', 'parents', 'front adm with this span']))
