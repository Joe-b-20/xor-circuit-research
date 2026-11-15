#!/usr/bin/env python3
"""Kernel dynamics from the run records and the kernel logs of polish / pull jobs (all hub campaigns).
 1. polish: G reduction and time of last improvement by maker of the target and by kernel attempt on the id
 2. pull: feasibility at the end (kernel.log 'final ... feas'), by lowered cap and target AD; time feasibility was reached
 3. gap fill vs same-depth improvement for the 80 front admissions
 4. results of jobs on targets with A >= 33
"""
import re
import json
from collections import defaultdict, Counter
from pathlib import Path
from l1_lib import Data, CAMPS, GENERATORS, fmt, table, HOME, leq

HUB = HOME / 'xs-campaigns' / '2026-11-14-hub'
D = Data()
allruns = [(c, r) for c in CAMPS for r in D.runs[c]]


def rv(c, r):
    n = 0; v = 0.0
    for oc in r['outcome']:
        if oc['status'] == 'admitted' and (c, oc['id']) in D.val:
            n += 1; v += D.val[(c, oc['id'])]['V']
    return n, v


def q(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else None


# ---- 1. polish -------------------------------------------------------------------------------------
seen = Counter()
S = defaultdict(lambda: defaultdict(list))
for c in CAMPS:
    for r in sorted(D.runs[c], key=lambda r: r['run_id']):
        if r['operator'] not in ('polish', 'pull', 'osc'): continue
        seen[(c, r['target'])] += 1
        if r['operator'] != 'polish' or not r['outcome']: continue
        tm = r['target_metrics']; m = r['outcome'][0]['metrics']
        tg = r['target']
        mk = D.op(tg)
        k = (mk, 'first kernel job on the id' if seen[(c, tg)] == 1 else 'later')
        s = S[k]
        dg = tm[2] - m[2] if (m[0] <= tm[0] and m[1] <= tm[1] and m[3] <= tm[3]) else 0
        s['dg'].append(dg); s['t'].append(r['op_info'].get('t_last_improvement')); s['nf'].append(rv(c, r)[0]); s['cpu'].append(r['cpu_s'])
rows = []
for k, s in sorted(S.items()):
    n = len(s['dg']); imp = [d for d in s['dg'] if d > 0]; ts = [t for t, d in zip(s['t'], s['dg']) if d > 0 and t is not None]
    rows.append([' / '.join(k), n, len(imp), '%.0f%%' % (100 * len(imp) / n), '%.1f' % (sum(imp) / len(imp)) if imp else '-', max(imp) if imp else '-',
                 '%.0f' % q(ts, .5) if ts else '-', sum(1 for t in ts if t > 75), sum(s['nf'])])
print('### 1. polish (90 s, own caps): G reduction under the caps, by maker of the target and whether the id had a kernel job before')
print(table(rows, ['target made by / kernel history', 'jobs', 'G lowered', 'share', 'mean dG when lowered', 'max dG', 'median t of last improvement s', 'last improvement after 75 s', 'front adm']))

# G excess of the target over the front at job time is not logged; use nursery flag as a proxy
S = defaultdict(lambda: defaultdict(list))
for c, r in allruns:
    if r['operator'] not in ('polish', 'pull') or not r['outcome']: continue
    tg = r['target']; rec = D.recs.get(tg)
    if not rec: continue
    nur = D.op(tg) in GENERATORS or bool((rec.get('operator_settings') or {}).get('nursery'))
    tm = r['target_metrics']; m = r['outcome'][0]['metrics']
    t = r['op_info'].get('t_last_improvement')
    k = (r['operator'], 'nursery-flag target' if nur else 'regular target')
    S[k]['t'].append(t); S[k]['adm'].append(r['admitted'] > 0); S[k]['nf'].append(rv(c, r)[0] > 0)
rows = []
for k, s in sorted(S.items()):
    ta = [t for t, a in zip(s['t'], s['adm']) if a and t is not None]
    rows.append([' / '.join(k), len(s['t']), sum(s['adm']), sum(s['nf']), '%.0f' % q(ta, .5) if ta else '-', '%.0f%%' % (100 * sum(1 for t in ta if t > 75) / len(ta)) if ta else '-'])
print(table(rows, ['op / target', 'jobs', 'jobs with admission', 'jobs with front adm', 'median t last improvement of admitted s', 'admitted jobs still improving after 75 s']))

# ---- 2. pull feasibility from kernel logs -----------------------------------------------------------------
fin = re.compile(r'^final cost (\d+) G (\d+) A (\d+) GD (\d+) AD (\d+) obj ([\d.e+]+) feas (\d)')
bst = re.compile(r'^best t ([\d.]+) it \d+ mv \S+ cost \d+ G (\d+) A (\d+) GD (\d+) AD (\d+) obj ([\d.e+]+)')
S = defaultdict(Counter); tf = defaultdict(list)
for c, r in allruns:
    if r['operator'] != 'pull': continue
    f = HUB / c / 'jobs' / r['run_id'] / 'kernel.log'
    if not f.exists(): S['?']['no log'] += 1; continue
    txt = f.read_text().splitlines()
    low = r['op_info'].get('lowered'); tm = r['target_metrics']
    if low == 'GD': low = 'GD-%d' % (tm[3] - r['op_info']['caps']['GD'])
    k = (low, 'AD%d target' % tm[1])
    S[k]['jobs'] += 1; S[k]['cpu'] += r['cpu_s']
    feas = None; tfe = None
    for ln in txt:
        mm = fin.match(ln)
        if mm: feas = int(mm.group(7))
        mb = bst.match(ln)
        if mb and tfe is None and float(mb.group(6)) < 1000: tfe = float(mb.group(1))
    S[k]['feasible at end'] += feas == 1
    if feas == 1 and tfe is not None: tf[k].append(tfe)
    S[k]['admitted'] += r['admitted'] > 0; S[k]['front adm'] += rv(c, r)[0]
    if feas == 0:
        S[k]['infeasible: front adm'] += rv(c, r)[0]; S[k]['infeasible: admitted'] += r['admitted'] > 0
rows = []
for k, s in sorted(S.items(), key=lambda kv: str(kv[0])):
    if k == '?': print(dict(s)); continue
    t = tf[k]
    rows.append([' / '.join(k), s['jobs'], '%.2f' % (s['cpu'] / 3600), s['feasible at end'], '%.0f%%' % (100 * s['feasible at end'] / s['jobs']),
                 '%.0f / %.0f' % (q(t, .5), q(t, .9)) if t else '-', s['admitted'], s['front adm'], s['infeasible: admitted'], s['infeasible: front adm']])
print('\n### 2. pull: did the kernel end feasible under the lowered caps? (kernel.log)')
print(table(rows, ['lowered / target', 'jobs', 'CPU-h', 'feasible at end', 'share', 'time to first feasible s (median / 90%)', 'jobs admitted', 'front adm', 'infeasible but admitted', 'infeasible, front adm']))

# ---- 3. gap fill vs same-depth improvement --------------------------------------------------------------------
print('\n### 3. the front admissions: did the class (A<=, AD<=) already hold a circuit at exactly this gate depth?')
C = Counter(); V = Counter(); ex = defaultdict(list)
for c in CAMPS:
    ids = sorted(D.inarch[c], key=lambda i: D.recs[i]['t_admit'])
    pts = list(D.published)
    for i in ids:
        m = D.m[i]
        if (c, i) in D.val:
            same = [p[2] for p in pts if p[0] <= m[0] and p[1] <= m[1] and p[3] == m[3]]
            exact = [p[2] for p in pts if p[0] == m[0] and p[1] == m[1] and p[3] == m[3]]
            k = 'same A, AD and GD existed (true same-box improvement)' if exact else ('class had this GD only with lower A or AD' if same else 'gap fill: no circuit of the class at this GD')
            a = 'A<=31' if m[0] <= 31 else 'A>=32'
            C[(k, a)] += 1; V[(k, a)] += D.val[(c, i)]['V']
            if exact: ex[a].append('%s (was %d)' % (fmt(m), min(exact)))
        pts.append(m)
print(table([[k[0], k[1], n, '%.0f' % V[k]] for k, n in sorted(C.items())], ['kind', 'class', 'front adm', 'V']))
for a, l in ex.items(): print(' same-box improvements', a, ':', ', '.join(l))

# ---- 4. jobs on A >= 33 targets: A of admitted results ------------------------------------------------------------
C = Counter()
for c, r in allruns:
    if r['target_metrics'][0] < 33: continue
    for oc in r['outcome']:
        if oc['status'] == 'admitted' and (c, oc['id']) in D.val:
            C['A<=32' if oc['metrics'][0] <= 32 else 'A>=33'] += 1
print('\n### 4. front admissions from jobs on targets with A >= 33, by result A:', dict(C))
