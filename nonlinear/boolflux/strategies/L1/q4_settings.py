#!/usr/bin/env python3
"""Q4 and follow-ups: transitions of value-producing jobs, originals vs copies by class, A/B arms in the
value model, ad3_share before/after, bandit behaviour, target-pool composition."""
import json
from collections import defaultdict, Counter
from l1_lib import Data, CAMPS, GENERATORS, fmt, table, tier, GOALS, HOME

D = Data()
allruns = [(c, r) for c in CAMPS for r in D.runs[c]]
first = {}
for i in sorted(D.recs, key=lambda i: D.recs[i]['t_admit']):
    first.setdefault(D.m[i], i)


def rv(c, r):
    n = 0; v = 0.0
    for oc in r['outcome']:
        if oc['status'] == 'admitted' and (c, oc['id']) in D.val:
            n += 1; v += D.val[(c, oc['id'])]['V']
    return n, v


def tcls(m):
    A, AD = m[0], m[1]
    a = '28' if A <= 28 else '29' if A == 29 else '30-31' if A <= 31 else '32' if A == 32 else '33-35' if A <= 35 else '36+'
    return 'A%s AD%s' % (a, '3' if AD <= 3 else '4' if AD == 4 else '5+')


# ---- 1. every value-producing job: target -> result ----------------------------------------------
rows = []
for c, r in allruns:
    for oc in r['outcome']:
        if oc['status'] == 'admitted' and (c, oc['id']) in D.val:
            x = D.val[(c, oc['id'])]; oi = r['op_info']
            what = oi.get('lowered') or ''
            if what == 'GD': what = 'GD-%d (AD cap off)' % (r['target_metrics'][3] - oi['caps']['GD'])
            t = oi.get('t_last_improvement')
            tg = r['target']
            rows.append((D.recs[oc['id']]['t_admit'], [D.phase(c, D.recs[oc['id']]['t_admit']), r['operator'], what, fmt(r['target_metrics']),
                         'original' if first[D.m[tg]] == tg else 'copy/' + D.op(tg), D.op(tg), fmt(oc['metrics']), x['delta'], '%.0f' % x['V'],
                         '' if t is None else '%.0f' % t, r['choice']]))
rows.sort()
print('### 1. every job that produced a front admission (time order)')
print(table([r for t, r in rows], ['phase', 'op', 'pull lowered', 'target', 'target is', 'target made by', 'result', 'dG in cap box', 'V', 't last impr s', 'choice']))
C = Counter()
for t, r in rows:
    a0, d0 = map(int, r[3].split('/')[:2]); a1, d1 = map(int, r[6].split('/')[:2])
    C[(r[1], 'A%+d AD%+d' % (a1 - a0, d1 - d0))] += 1
print('front admissions by op and (A, AD) change target->result:', sorted(C.items()))

# ---- 1b. A/AD change of all kernel-op candidates (not only admitted) --------------------------------
C = defaultdict(Counter)
for c, r in allruns:
    if r['operator'] not in ('polish', 'pull', 'osc') or not r['outcome']: continue
    m = r['outcome'][0]['metrics']; tm = r['target_metrics']; low = r['op_info'].get('lowered') or ''
    k = r['operator'] + (' ' + low if low else '')
    C[k]['jobs'] += 1
    C[k]['A%+d' % (m[0] - tm[0])] += 1
    C[k]['AD%+d' % (m[1] - tm[1])] += 1
    C[k]['same tuple'] += tuple(m) == tuple(tm)
    C[k]['G lower, GD<=, AD<=, A<='] += m[2] < tm[2] and m[3] <= tm[3] and m[1] <= tm[1] and m[0] <= tm[0]
    if tm[1] == 3: C[k]['AD3 target'] += 1; C[k]['AD3 target -> result AD>3'] += m[1] > 3
print('\n### 1b. first candidate of kernel jobs vs target')
for k, v in sorted(C.items()): print(' ', k, dict(sorted(v.items())))

# ---- 2. originals vs join copies, by class (polish + pull) -----------------------------------------
S = defaultdict(lambda: defaultdict(float))
for c, r in allruns:
    if r['operator'] not in ('polish', 'pull'): continue
    tg = r['target']
    kind = 'original' if first[D.m[tg]] == tg else ('join copy' if D.op(tg) == 'join' else 'other copy')
    a = r['target_metrics'][0]
    k = ('A<=29' if a <= 29 else 'A30-32' if a <= 32 else 'A33+', kind); s = S[k]; n, v = rv(c, r)
    s['jobs'] += 1; s['cpu'] += r['cpu_s']; s['nf'] += n; s['V'] += v; s['adm'] += r['admitted']
print('\n### 2. polish + pull: target original vs equal-tuple copy, by class')
print(table([[' / '.join(k), int(s['jobs']), '%.2f' % (s['cpu'] / 3600), int(s['adm']), int(s['nf']), '%.0f' % s['V'], '%.1f' % (s['V'] / (s['cpu'] / 3600)), '%.2f' % (s['nf'] / (s['cpu'] / 3600))]
             for k, s in sorted(S.items())], ['class / target kind', 'jobs', 'CPU-h', 'adm', 'front adm', 'V', 'V/CPU-h', 'front adm/CPU-h']))

# was the copy's original also a target of the same op (i.e. duplicated effort)?
dup = Counter()
for c in CAMPS:
    tg = defaultdict(set)
    for r in D.runs[c]:
        if r['operator'] in ('polish', 'pull', 'osc'): tg[(r['operator'], tuple(r['target_metrics']))].add(r['target'])
    for (o, m), ids in tg.items():
        dup[(o, min(len(ids), 5))] += 1
print('distinct target ids per (campaign, op, tuple):', sorted(dup.items()))
S = defaultdict(lambda: defaultdict(float))
for c in CAMPS:
    order = defaultdict(list)
    for r in sorted(D.runs[c], key=lambda r: r['run_id']):
        if r['operator'] not in ('polish', 'pull'): continue
        k = (r['operator'], tuple(r['target_metrics'])); order[k].append(r)
    for k, rr in order.items():
        for j, r in enumerate(rr):
            s = S[(k[0], min(j + 1, 5))]; n, v = rv(c, r); s['jobs'] += 1; s['cpu'] += r['cpu_s']; s['nf'] += n; s['V'] += v
print('\n### 2b. yield by attempt index on the same TUPLE (any circuit with that A/AD/G/GD) and operator')
print(table([[k[0], k[1] if k[1] < 5 else '5+', int(s['jobs']), '%.2f' % (s['cpu'] / 3600), int(s['nf']), '%.0f' % s['V'], '%.1f' % (s['V'] / (s['cpu'] / 3600)), '%.2f' % (s['nf'] / (s['cpu'] / 3600))]
             for k, s in sorted(S.items())], ['op', 'attempt on tuple', 'jobs', 'CPU-h', 'front adm', 'V', 'V/CPU-h', 'front adm/CPU-h']))

# ---- 3. A/B arms in the value model ------------------------------------------------------------------
print('\n### 3. one-hour arms: count and value of front admissions (per arm, replayed against its own archive + pin)')
rows = []
for c in ['abhub', 'ab2base', 'ab2gen', 'ab3gen', 'ab3lin', 'ab4base', 'ab4ad3']:
    pts = [(i, x) for (cc, i), x in D.val.items() if cc == c]
    cpu = sum(r['cpu_s'] for r in D.runs[c]) / 3600
    rows.append([c, '%.2f' % cpu, len(pts), sum(1 for i, x in pts if D.m[i][0] <= 31), '%.0f' % sum(x['V'] for i, x in pts),
                 ', '.join('%s %s V%.0f' % (fmt(D.m[i]), D.op(i), x['V']) for i, x in sorted(pts, key=lambda p: D.m[p[0]]))])
print(table(rows, ['arm', 'CPU-h', 'front adm', 'A<=31', 'V', 'points']))
# long by hour blocks of 1 CPU-h equivalents: dispersion of V per CPU-h in the same configuration (long2: 6 CPUs, 2 h)
for ph in ('long2', 'long3', 'long4'):
    blocks = defaultdict(lambda: [0.0, 0, 0.0])
    for r in D.runs['long']:
        if D.phase('long', r['ts_end'] - r['wall_s']) != ph: continue
        b = (r['cpu'], int((r['ts_end'] - D.span['long'][0]) / 3600))
        n, v = rv('long', r); blocks[b][0] += r['cpu_s']; blocks[b][1] += n; blocks[b][2] += v
    full = [x for x in blocks.values() if x[0] > 3000]
    ns = sorted(x[1] for x in full); vs = sorted(round(x[2]) for x in full)
    print(' %s: %d one-CPU one-hour blocks (same configuration, shared archive): front adm per block %s; V per block %s' % (ph, len(full), dict(sorted(Counter(ns).items())), vs))

# ---- 4. ad3_share before / after 21:52 UTC within long3 ----------------------------------------------
ctl = [e for e in D.events['long'] if e['ev'] == 'control' and e.get('ad3_share', 0) > 0]
t_ad3 = min(e['ts'] for e in ctl)
st = sorted(e['ts'] for e in D.events['long'] if e['ev'] == 'start')
print('\n### 4. long3 before / after ad3_share 0.3 (set at ts %.0f)' % t_ad3)
S = defaultdict(lambda: defaultdict(float))
for r in D.runs['long']:
    t = r['ts_end'] - r['wall_s']
    if D.phase('long', t) not in ('long3', 'long4'): continue
    k = ('before' if t < t_ad3 else 'after', 'AD3 target' if r['target_metrics'][1] <= 3 else 'AD>=4 target'); s = S[k]; n, v = rv('long', r)
    s['jobs'] += 1; s['cpu'] += r['cpu_s']; s['nf'] += n; s['V'] += v
tot = defaultdict(float)
for k, s in S.items(): tot[k[0]] += s['cpu']
print(table([[' / '.join(k), int(s['jobs']), '%.2f' % (s['cpu'] / 3600), '%.0f%%' % (100 * s['cpu'] / tot[k[0]]), int(s['nf']), '%.0f' % s['V'], '%.1f' % (s['V'] / (s['cpu'] / 3600)), '%.2f' % (s['nf'] / (s['cpu'] / 3600))]
             for k, s in sorted(S.items())], ['period / target', 'jobs', 'CPU-h', 'CPU share', 'front adm', 'V', 'V/CPU-h', 'front adm/CPU-h']))

# ---- 5. bandit: share of jobs / CPU per op per phase, exploit picks -----------------------------------
print('\n### 5. exploit picks per phase (which op the bandit favoured)')
for ph in ('abhub', 'long2', 'long3', 'long4'):
    C = Counter(); CC = Counter()
    for c, r in allruns:
        if D.phase(c, (r['ts_end'] or 0) - r['wall_s']) != ph: continue
        if r['choice'] == 'exploit': C[r['operator']] += 1; CC[r['operator']] += r['cpu_s']
    print(' ', ph, 'exploit jobs', dict(C), 'exploit CPU-h', {k: round(v / 3600, 2) for k, v in CC.items()})

# ---- 6. target pool at the end of long ------------------------------------------------------------------
fr = json.loads((HOME / 'xs-campaigns' / '2026-11-14-hub' / 'long' / 'front.json').read_text())
tup = Counter(tuple(d['m']) for d in fr)
print('\n### 6. long front at stop: %d ids for %d tuples; by class:' % (len(fr), len(tup)))
C = Counter(); CI = Counter()
for m, n in tup.items(): C[tcls(m)] += 1; CI[tcls(m)] += n
print(table([[k, C[k], CI[k], '%.0f%%' % (100 * CI[k] / len(fr))] for k in sorted(C)], ['class', 'front tuples', 'front ids (targets)', 'share of target pool']))
