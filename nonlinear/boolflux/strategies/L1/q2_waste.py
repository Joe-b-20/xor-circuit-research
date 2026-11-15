#!/usr/bin/env python3
"""Q2 + Q4: where CPU goes without paying; settings evidence.  Text tables."""
from collections import defaultdict, Counter
from l1_lib import Data, CAMPS, GENERATORS, fmt, table, tier, GOALS

D = Data()
allruns = [(c, r) for c in CAMPS for r in D.runs[c]]


def rv(c, r):
    """(front admissions, V, V at A<=31) of a run"""
    n = 0; v = 0.0; va = 0.0
    for oc in r['outcome']:
        if oc['status'] == 'admitted' and (c, oc['id']) in D.val:
            x = D.val[(c, oc['id'])]; n += 1; v += x['V']
            if D.m[oc['id']][0] <= 31: va += x['V']
    return n, v, va


def agg(keyf, runs=allruns, minjobs=1):
    S = defaultdict(lambda: defaultdict(float))
    for c, r in runs:
        k = keyf(c, r)
        if k is None: continue
        s = S[k]; n, v, va = rv(c, r)
        s['jobs'] += 1; s['cpu'] += r['cpu_s']; s['adm'] += r['admitted']; s['nf'] += n; s['V'] += v; s['VA'] += va
        s['jobs_adm'] += r['admitted'] > 0; s['jobs_nf'] += n > 0
    rows = []
    for k, s in sorted(S.items(), key=lambda kv: kv[0] if not isinstance(kv[0], tuple) else tuple(str(x) for x in kv[0])):
        if s['jobs'] < minjobs: continue
        h = s['cpu'] / 3600
        rows.append([k if not isinstance(k, tuple) else ' / '.join(str(x) for x in k), int(s['jobs']), '%.2f' % h, int(s['adm']), int(s['jobs_nf']), int(s['nf']),
                     '%.0f' % s['V'], '%.0f' % s['VA'], '%.1f' % (s['V'] / h if h else 0), '%.1f%%' % (100 * s['jobs_nf'] / s['jobs'])])
    return table(rows, ['key', 'jobs', 'CPU-h', 'adm', 'jobs with front adm', 'front adm', 'V', 'V A<=31', 'V/CPU-h', 'P(front adm per job)'])


# ---- (a) repeated jobs on the same target -----------------------------------------------------
seen = Counter(); idx = {}
for c in CAMPS:
    for r in sorted(D.runs[c], key=lambda r: r['run_id']):
        k = (c, r['operator'], r['target']); seen[k] += 1; idx[(c, r['run_id'])] = seen[k]
print('### (a) yield by attempt index of (campaign dir, operator, target)')
print(agg(lambda c, r: (r['operator'], min(idx[(c, r['run_id'])], 6) if idx[(c, r['run_id'])] < 6 else '6+') if r['operator'] in ('polish', 'pull', 'osc', 'trb', 'gen_skel', 'join') else None))
mx = Counter()
for (c, o, t), n in seen.items(): mx[(o, min(n, 10))] += 1
print('targets by number of jobs:', sorted(mx.items()))
top = sorted(seen.items(), key=lambda kv: -kv[1])[:12]
print('most repeated:', [(o, fmt(D.m[t]), n) for (c, o, t), n in top])

# ---- (a2) originals vs tie copies ---------------------------------------------------------------
first = {}
for i in sorted(D.recs, key=lambda i: D.recs[i]['t_admit']):
    first.setdefault(D.m[i], i)
print('\n### (a2) target is the first circuit with its (A,AD,G,GD) tuple (original) or a later equal-tuple copy')
print(agg(lambda c, r: (r['operator'], 'original' if first[D.m[r['target']]] == r['target'] else 'copy by ' + D.op(r['target'])) if r['operator'] in ('polish', 'pull', 'osc', 'trb', 'gen_skel') and r['target'] in D.recs else None))
ncopy = sum(1 for i in D.recs if first[D.m[i]] != i)
print('records that are equal-tuple copies: %d of %d; by maker %s' % (ncopy, len(D.recs), Counter(D.op(i) for i in D.recs if first[D.m[i]] != i)))

# ---- (b) by target class ------------------------------------------------------------------------
def tcls(m):
    A, AD = m[0], m[1]
    a = '28' if A <= 28 else '29' if A == 29 else '30-31' if A <= 31 else '32' if A == 32 else '33-35' if A <= 35 else '36+'
    return 'A%s AD%s' % (a, '3' if AD <= 3 else '4' if AD == 4 else '5+')
print('\n### (b) CPU and value by class of the TARGET (all ops)')
print(agg(lambda c, r: tcls(r['target_metrics'])))
print('\n### (b2) by operator x target class (>= 10 jobs)')
print(agg(lambda c, r: (r['operator'], tcls(r['target_metrics'])), minjobs=10))

# ---- (c) pull by lowered cap --------------------------------------------------------------------
def pullkey(c, r):
    if r['operator'] != 'pull': return None
    oi = r['op_info']; low = oi.get('lowered')
    tm = r['target_metrics']
    if low == 'GD': low = 'GD-%d' % (tm[3] - oi['caps']['GD'])
    res = 'no candidate' if not r['outcome'] else ''
    return (low,)
print('\n### (c) pull by lowered cap')
print(agg(pullkey))
S = defaultdict(Counter)
for c, r in allruns:
    if r['operator'] != 'pull': continue
    oi = r['op_info']; low = oi.get('lowered'); caps = oi.get('caps') or {}
    if not r['outcome']: S[low]['no candidate'] += 1; continue
    m = r['outcome'][0]['metrics']
    ok = all(caps.get(k) is None or m[j] <= caps[k] for k, j in (('A', 0), ('AD', 1), ('GD', 3)))
    S[low]['caps met' if ok else 'caps NOT met'] += 1
    if ok: S[low]['met+' + r['outcome'][0]['status'].split(':')[0]] += 1
    tm = r['target_metrics']
    if ok and low in ('AD', 'GD') and m[0] != tm[0]: S[low]['met with A changed %+d' % (m[0] - tm[0])] += 1
for k, v in S.items(): print(' pull', k, dict(v))
print(agg(lambda c, r: ('pull', r['op_info'].get('lowered'), tcls(r['target_metrics'])) if r['operator'] == 'pull' else None, minjobs=8))

# ---- (d) kernel improvement times ---------------------------------------------------------------
print('\n### (d) time of last improvement inside the kernel budget (jobs that produced a front admission / any admission / all)')
for op in ('polish', 'pull'):
    for name, cond in (('front adm', lambda c, r: rv(c, r)[0] > 0), ('admitted', lambda c, r: r['admitted'] > 0), ('all', lambda c, r: True)):
        ts = sorted(r['op_info'].get('t_last_improvement') or 0 for c, r in allruns if r['operator'] == op and cond(c, r) and r['op_info'].get('t_last_improvement') is not None)
        nn = sum(1 for c, r in allruns if r['operator'] == op and cond(c, r))
        if ts:
            q = lambda p: ts[min(len(ts) - 1, int(p * len(ts)))]
            print(' %s %-9s n %4d with t %4d: quartiles %.0f / %.0f / %.0f s, max %.0f; share after 60 s %.0f%%, after 80 s %.0f%%' % (
                op, name, nn, len(ts), q(.25), q(.5), q(.75), ts[-1], 100 * sum(t > 60 for t in ts) / len(ts), 100 * sum(t > 80 for t in ts) / len(ts)))

# ---- (e) job overheads and time-outs --------------------------------------------------------------
print('\n### (e) per operator: budget, CPU and wall per job, return codes')
S = defaultdict(lambda: defaultdict(list))
for c, r in allruns:
    s = S[r['operator']]; s['cpu'].append(r['cpu_s']); s['wall'].append(r['wall_s']); s['sec'].append((r['settings'] or {}).get('seconds') or 0); s['rc'].append(r['returncode'])
    s['nocand'].append(r['candidates'] == 0)
rows = []
for o, s in sorted(S.items()):
    n = len(s['cpu']); cs = sorted(s['cpu']); ws = sorted(s['wall'])
    rows.append([o, n, '%.0f' % (sum(s['sec']) / n), '%.1f' % (sum(cs) / n), '%.1f' % cs[n // 2], '%.1f' % cs[-1], '%.1f' % (sum(ws) / n), '%.1f' % ws[-1], dict(Counter(s['rc'])), sum(s['nocand'])])
print(table(rows, ['op', 'jobs', 'budget s', 'mean CPU s', 'median CPU s', 'max CPU s', 'mean wall s', 'max wall s', 'return codes', 'jobs without candidate']))

# utilisation per phase: sum of job wall time / (cpus x span)
print('\n### (e2) worker utilisation = sum(job wall) / (CPUs x elapsed)')
for c in CAMPS:
    st = sorted([e for e in D.events[c] if e['ev'] == 'start'], key=lambda e: e['ts'])
    ctl = sorted([e for e in D.events[c] if e['ev'] == 'control'], key=lambda e: e['ts'])
    for k, e in enumerate(st):
        t0 = e['ts']; t1 = st[k + 1]['ts'] if k + 1 < len(st) else D.span[c][1]
        rr = [r for r in D.runs[c] if r['ts_end'] and t0 <= r['ts_end'] - r['wall_s'] < t1]
        if not rr: continue
        t1 = max(r['ts_end'] for r in rr)
        # cpu-seconds available: piecewise by the cpu set (control events add cpus)
        cpus = set(e['cpus']); avail = 0; t = t0
        for ce in ctl:
            if t0 < ce['ts'] < t1 and 'cpus' in ce['control']:
                avail += len(cpus) * (ce['ts'] - t); t = ce['ts']; cpus |= set(ce['control']['cpus'])
        avail += len(cpus) * (t1 - t)
        used_cpus = len({r['cpu'] for r in rr})
        print(' %s start %d: %.2f h, cpus at start %d (used %d), jobs %d, job wall %.1f CPU-h, available %.1f CPU-h, utilisation %.0f%%' % (
            c, k, (t1 - t0) / 3600, len(e['cpus']), used_cpus, len(rr), sum(r['wall_s'] for r in rr) / 3600, avail / 3600, 100 * sum(r['wall_s'] for r in rr) / avail))

# ---- (f) nursery ----------------------------------------------------------------------------------
print('\n### (f) nursery: admissions with the nursery flag or made by a generator')
desc = defaultdict(set)
for i in D.recs:
    for a in D.ancestors(i): desc[a].add(i)
valued = {i for (c, i) in D.val}
tgt = Counter(); tcpu = Counter()
for c, r in allruns:
    tgt[r['target']] += 1; tcpu[r['target']] += r['cpu_s']
S = defaultdict(lambda: defaultdict(float))
for i, r in D.recs.items():
    o = D.op(i)
    nur = o in GENERATORS or bool((r.get('operator_settings') or {}).get('nursery'))
    if o == 'base': continue
    k = (o, 'nursery' if nur else 'regular'); s = S[k]
    s['n'] += 1; s['targeted'] += tgt[i] > 0; s['jobs'] += tgt[i]; s['cpu'] += tcpu[i]; s['withdesc'] += bool(desc[i]); s['valdesc'] += bool(desc[i] & valued) or i in valued
    s['self'] += i in valued
rows = [[' / '.join(k), int(s['n']), int(s['self']), int(s['targeted']), int(s['jobs']), '%.2f' % (s['cpu'] / 3600), int(s['withdesc']), int(s['valdesc'])] for k, s in sorted(S.items())]
print(table(rows, ['maker / flag', 'admissions', 'front adm themselves', 'ever used as a target', 'jobs on them', 'CPU-h on them', 'with any descendant', 'self or a descendant is a front admission']))
print(agg(lambda c, r: ('target nursery-flag' if (r['target'] in D.recs and (D.op(r['target']) in GENERATORS or bool((D.recs[r['target']].get('operator_settings') or {}).get('nursery')))) else 'target regular', r['operator'])))
# nursery admissions: how far above the front were they (G excess over the best prior G in their cap box)?

# ---- (g) explore vs exploit ------------------------------------------------------------------------
print('\n### (g) bandit choice')
print(agg(lambda c, r: (r['choice'], r['operator'])))
print(agg(lambda c, r: (r['choice'],)))

# ---- (h) osc ---------------------------------------------------------------------------------------
print('\n### (h) osc outcomes')
S = Counter()
for c, r in allruns:
    if r['operator'] != 'osc': continue
    oi = r['op_info']; tm = tuple(r['target_metrics'])
    rm = tuple(oi.get('relaxed_metrics') or ()); pm = tuple(oi.get('repaired_metrics') or ())
    S['jobs'] += 1
    S['relaxed stage changed the circuit metrics'] += rm != tm
    S['relaxed stage lowered G'] += bool(rm) and rm[2] < tm[2]
    S['repair back within GD cap'] += bool(pm) and pm[3] <= tm[3]
    S['repaired G < target G at GD <= target GD, AD <= target AD'] += bool(pm) and pm[3] <= tm[3] and pm[2] < tm[2] and pm[1] <= tm[1]
    S['... of which A raised'] += bool(pm) and pm[3] <= tm[3] and pm[2] < tm[2] and pm[1] <= tm[1] and pm[0] > tm[0]
    S['A raised in result'] += bool(pm) and pm[0] > tm[0]
print(dict(S))

# ---- (i) join -----------------------------------------------------------------------------------------
print('\n### (i) join admissions: equal-tuple copies vs new tuples; gain classes')
S = Counter()
for i, r in D.recs.items():
    if D.op(i) != 'join': continue
    ps = [p for p in r['parents'] if p in D.m]
    S['admitted'] += 1
    S['same tuple as a parent'] += any(D.m[p] == D.m[i] for p in ps)
    S['equal-tuple copy of an earlier record'] += first[D.m[i]] != i
    S['hub gain >= 1'] += (r.get('gain') or 0) >= 1
    S['front admission (L1 replay)'] += i in valued
    S['has descendants'] += bool(desc[i]); S['self or descendant front admission'] += bool(desc[i] & valued) or i in valued
print(dict(S))
jr = [(c, r) for c, r in allruns if r['operator'] == 'join']
print('join jobs %d, with 0 admissions %d (%.0f%%), CPU-h %.2f; mean partners %.0f, mean tried %.0f' % (
    len(jr), sum(r['admitted'] == 0 for c, r in jr), 100 * sum(r['admitted'] == 0 for c, r in jr) / len(jr), sum(r['cpu_s'] for c, r in jr) / 3600,
    sum(r['op_info'].get('partners') or 0 for c, r in jr) / len(jr), sum(r['op_info'].get('n_tried') or r['op_info'].get('tried') or 0 for c, r in jr) / len(jr)))
# join admissions over time in long (per hour)
byh = Counter(); byhj = Counter(); byhf = Counter()
t0 = D.span['long'][0]
for r in D.runs['long']:
    if r['operator'] != 'join': continue
    h = int((r['ts_end'] - t0) / 3600); byhj[h] += 1; byh[h] += r['admitted']; byhf[h] += rv('long', r)[0]
print('long, join per hour since 18:41 UTC: jobs', sorted(byhj.items()), 'admissions', sorted(byh.items()), 'front adm', sorted(byhf.items()))

# ---- (j) front admissions per hour in long, by op -----------------------------------------------------
print('\n### (j) long: front admissions and V per hour (all ops)')
byh = defaultdict(lambda: defaultdict(float))
for r in D.runs['long']:
    h = int((r['ts_end'] - t0) / 3600); n, v, va = rv('long', r)
    byh[h]['cpu'] += r['cpu_s']; byh[h]['n'] += n; byh[h]['V'] += v; byh[h]['nA'] += sum(1 for oc in r['outcome'] if oc['status'] == 'admitted' and ('long', oc['id']) in D.val and D.m[oc['id']][0] <= 31)
print(table([[h, '%.1f' % (s['cpu'] / 3600), int(s['n']), int(s['nA']), '%.0f' % s['V'], '%.1f' % (s['V'] / (s['cpu'] / 3600))] for h, s in sorted(byh.items())], ['hour', 'CPU-h', 'front adm', 'A<=31', 'V', 'V/CPU-h']))
