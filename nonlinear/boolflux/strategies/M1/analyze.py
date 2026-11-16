#!/usr/bin/env python3
"""M1: per-method tables from harvest.py output (argv[1] = data dir). Read-only."""
import json, os, sys, statistics as st, collections, calendar

D = sys.argv[1]
runs = [json.loads(l) for l in open(os.path.join(D, 'runs.jsonl'))]
ev = [json.loads(l) for l in open(os.path.join(D, 'events.jsonl'))]
ev4 = [json.loads(l) for l in open(os.path.join(D, 'events4.jsonl'))]
side = [json.loads(l) for l in open(os.path.join(D, 'sidecars.jsonl'))]
ROOT = os.path.expanduser('~/xs-campaigns/2026-11-15-targets')


def med(x):
    x = [v for v in x if v is not None]
    return round(st.median(x)) if x else None


def pct(x, q):
    x = sorted(v for v in x if v is not None)
    if not x: return None
    return round(x[min(len(x) - 1, int(q * len(x)))])


def improved(r):
    s, f = r.get('start'), r.get('final')
    if r['src'] == 'p1job':
        return bool(r.get('imp'))
    if not s or not f: return False
    if not r.get('feas0'):
        return r.get('first_imp') is not None      # pull: reached the cap
    return f[2] < s[2]


# link events to runs: the run dir that occurs in the sidecar command / aes_check / method text
own = [e for e in ev if e['ev_target'] == e['target']]
own4 = [e for e in ev4 if e['ev_target'] == e['target']]
for e in own + own4:
    txt = (e.get('command') or '') + ' ' + (e.get('aes') or '') + ' ' + (e.get('method') or '')
    best = None
    for r in runs:
        if r['agent'] != e['agent'] or r['src'] == 'p1job': continue
        key = '/runs/' + r['dir']
        if key in txt and (best is None or len(r['dir']) > len(best['dir'])): best = r
    e['run'] = best['dir'] if best else None
    e['run_cat'] = best['cat'] if best else None
    e['run_mode'] = best['mode'] if best else None

print('# A. kernel runs by agent / target / category / mode')
print('agent target cat mode | runs CPU-h | improved-in-run (share) | first-imp s med/p90 | last-imp s med/p90 | wall med | rk share')
g = collections.defaultdict(list)
for r in runs:
    g[(r['agent'], r.get('target'), r['cat'], r.get('mode'))].append(r)
for k in sorted(g, key=lambda k: tuple(str(x) for x in k)):
    rs = g[k]
    cpu = sum(r.get('wall') or 0 for r in rs) / 3600
    imp = [r for r in rs if improved(r)]
    print(*k, '|', len(rs), '%.2f' % cpu, '|', len(imp), '(%.0f%%)' % (100 * len(imp) / len(rs)), '|',
          med([r.get('first_imp') for r in imp]), pct([r.get('first_imp') for r in imp], .9), '|',
          med([r.get('last_imp') for r in imp]), pct([r.get('last_imp') for r in imp], .9), '|',
          med([r.get('wall') for r in rs]), '|', '%.0f%%' % (100 * sum(1 for r in rs if r.get('rk')) / len(rs)))

print('\n# B. CPU-h by agent / target / category (kernel runs only)')
g2 = collections.defaultdict(float)
for r in runs:
    g2[(r['agent'], r.get('target'), r['cat'])] += (r.get('wall') or 0) / 3600
for k in sorted(g2): print(*k, '%.2f' % g2[k])

print('\n# C. own-target (G,GD) frontier events with the run that made them')
for e in own:
    print(e['target'], e['utc'][11:16], e['agent'], e['tuple'], e['cls'], 'run=%s cat=%s mode=%s' % (e['run'], e['run_cat'], e['run_mode']))
print('\n# C4. own-target (A,AD,G,GD) Pareto events')
for e in own4:
    print(e['target'], e['utc'][11:16], e['agent'], e['tuple'], 'run=%s cat=%s' % (e['run'], e['run_cat']), e['file'][:60])

print('\n# D. the runs whose result became an event: start, cap, time of first / last improvement, wall')
seen = set()
for e in own + own4:
    if not e.get('run') or (e['agent'], e['run']) in seen: continue
    seen.add((e['agent'], e['run']))
    r = next(r for r in runs if r['agent'] == e['agent'] and r['dir'] == e['run'])
    print(e['target'], r['agent'], r['dir'], r.get('mode'), 'cap', r.get('cap_gd'), 'start', r.get('start'), 'final', r.get('final'),
          'first', r.get('first_imp'), 'last', r.get('last_imp'), 'wall', r.get('wall'), 'rk', r.get('rk'))

json.dump({'own': own, 'own4': own4}, open(os.path.join(D, 'linked.json'), 'w'))
