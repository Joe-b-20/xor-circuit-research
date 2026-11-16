#!/usr/bin/env python3
"""M1: stage-length tail, P7 polish groups, CPU-h of named run groups (argv[1] = data dir). Read-only."""
import json, os, sys, collections, calendar, re

D = sys.argv[1]
runs = [json.loads(l) for l in open(os.path.join(D, 'runs.jsonl'))]
kr = [r for r in runs if r['src'] != 'p1job']


def utc(h, m):
    return calendar.timegm((2026, 11, 15, h, m, 0))


print('# 1. when does the last improvement of a stage come? (runs with an improvement, by mode)')
for mode in ('gate', 'mix', 'trb', 'kern'):
    rs = [r for r in kr if r.get('mode') == mode and r.get('last_imp') is not None]
    if not rs: continue
    for lim in (120, 240, 360, 600):
        long_ = [r for r in rs if (r.get('wall') or 0) >= lim + 30]
        late = [r for r in long_ if r['last_imp'] > lim]
        print(mode, 'runs longer than %d s: %d, last improvement after %d s: %d (%.0f%%)' % (
            lim + 30, len(long_), lim, len(late), 100 * len(late) / max(1, len(long_))))

print('\n# 2. P7 polish groups (pol-*/polgate-*): start tuple -> final G distribution')
g = collections.defaultdict(list)
for r in kr:
    if r['agent'] == 'P7' and r['dir'].startswith(('pol', 'deep')):
        m = re.match(r'(pol(?:gate|mix)?-L[A-E]?-?)', r['dir'])
        key = (r['dir'].split('-s')[0][:40], tuple(r['start']))
        g[key].append((r['final'][0], r['final'][2]))
for k in sorted(g):
    print(k, len(g[k]), 'final (A,G):', dict(collections.Counter(g[k])))

print('\n# 3. CPU-h of named groups')
groups = {
    'P2 T02 polishing of the 174 (trb/mix after 16:21)': lambda r: r['agent'] == 'P2' and r.get('target') == 'T02' and r['t0'] and r['t0'] > utc(16, 21) and r['cat'] == 'kernel-plain',
    'P2 T02 conjugate pipelines': lambda r: r['agent'] == 'P2' and r.get('target') == 'T02' and r['cat'] == 'conj',
    'P2 T06 all kernel': lambda r: r['agent'] == 'P2' and r.get('target') == 'T06',
    'P3 after 20:16 (after 115@18)': lambda r: r['agent'] == 'P3' and r['t0'] and r['t0'] > utc(20, 16),
    'P3 before 17:52 (to 114@19)': lambda r: r['agent'] == 'P3' and r['t0'] and r['t0'] < utc(17, 52),
    'P3 rk re-derivations 18:15-19:37 (rkA/rkC/rkD/rkE)': lambda r: r['agent'] == 'P3' and r['dir'].startswith(('rkA', 'rkC', 'rkD', 'rkE')),
    'P5 after 19:33 (after last AD4 event)': lambda r: r['agent'] == 'P5' and r['t0'] and r['t0'] > utc(19, 33),
    'P5 AD5 work (ad5*, cp-ad5*, n104*)': lambda r: r['agent'] == 'P5' and ('ad5' in r['dir'] or 'n104' in r['dir']),
    'P4 conj lineages': lambda r: r['agent'] == 'P4',
    'P6 GD12 pulls after 16:41 (pull12d-i, seeds181, polish181)': lambda r: r['agent'] == 'P6' and r['dir'].startswith(('pull12d', 'pull12e', 'pull12f', 'pull12g', 'pull12h', 'pull12i', 'seeds181', 'polish181')),
    'P6 GD13 pulls/relax (pull13*, relax*)': lambda r: r['agent'] == 'P6' and r['dir'].startswith(('pull13', 'relax')),
    'P6 T07 fixed-lam conjugates (t07conj*, conj-t1*)': lambda r: r['agent'] == 'P6' and r['dir'].startswith(('conj-t', 't07conj')),
    'P6 T07 screened conjugates (c3-*)': lambda r: r['agent'] == 'P6' and r['dir'].startswith('c3-'),
    'P6 T07 polish139*': lambda r: r['agent'] == 'P6' and r['dir'].startswith('polish139'),
    'P7 T09 polish before 18:00': lambda r: r['agent'] == 'P7' and r.get('target') == 'T09' and r['t0'] and r['t0'] < utc(18, 0),
    'P7 T09 polish 18:00-21:19': lambda r: r['agent'] == 'P7' and r.get('target') == 'T09' and r['t0'] and utc(18, 0) <= r['t0'] < utc(21, 19),
    'P7 T09 polish after 21:19': lambda r: r['agent'] == 'P7' and r.get('target') == 'T09' and r['t0'] and r['t0'] >= utc(21, 19),
    'P1 all kernel': lambda r: r['agent'] == 'P1',
}
for name, f in groups.items():
    rs = [r for r in kr if f(r)]
    imp = sum(1 for r in rs if r.get('last_imp') is not None and (r['final'][2] < r['start'][2] if r.get('feas0') else True))
    print('%-70s runs %4d  CPU-h %.2f  improved-in-run %d' % (name, len(rs), sum(r.get('wall') or 0 for r in rs) / 3600, imp))
p1 = [r for r in runs if r['src'] == 'p1job']
print('%-70s jobs %4d  CPU-h %.2f  imp %d' % ('P1 p1run jobs (jobs.jsonl)', len(p1), sum(r.get('wall') or 0 for r in p1) / 3600,
                                             sum(1 for r in p1 if r.get('imp'))))
print('P1 p1run verdict counts', collections.Counter(v for r in p1 for v in r.get('verdicts') or []))

print('\n# 4. agent time spans of kernel runs (first start, last end, UTC) and total kernel CPU-h')
for a in sorted(set(r['agent'] for r in kr)):
    rs = [r for r in kr if r['agent'] == a and r['t0']]
    t0 = min(r['t0'] for r in rs); t1 = max(r['t0'] + (r.get('wall') or 0) for r in rs)
    print(a, '%s - %s' % (__import__('time').strftime('%H:%M', __import__('time').gmtime(t0)),
                          __import__('time').strftime('%H:%M', __import__('time').gmtime(t1))),
          'kernel CPU-h %.2f' % (sum(r.get('wall') or 0 for r in rs) / 3600))
