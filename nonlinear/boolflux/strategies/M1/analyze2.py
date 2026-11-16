#!/usr/bin/env python3
"""M1: pulls with / without repair_keep, stage tables of lineages, repeats, conjugate screen vs outcome.
argv[1] = data dir (harvest.py output). Read-only."""
import json, os, sys, re, collections, statistics as st, glob

D = sys.argv[1]
ROOT = os.path.expanduser('~/xs-campaigns/2026-11-15-targets')
runs = [json.loads(l) for l in open(os.path.join(D, 'runs.jsonl'))]
kr = [r for r in runs if r['src'] != 'p1job']


def spearman(x, y):
    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i]); r = [0] * len(v); i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]: j += 1
            for t in range(i, j + 1): r[o[t]] = (i + j) / 2 + 1
            i = j + 1
        return r
    a, b = rk(x), rk(y); n = len(x)
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    den = (sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b)) ** .5
    return num / den if den else float('nan')


print('# 1. pulls (start GD above the cap): repair_keep off vs on')
print('agent rk | pulls | reached cap | share | median dG(final-start) when reached | median t to cap')
g = collections.defaultdict(list)
for r in kr:
    s = r.get('start')
    if not s or s[3] is None or r.get('cap_gd') is None: continue
    if s[3] <= r['cap_gd']: continue
    g[(r['agent'], bool(r.get('rk')))].append(r)
for k in sorted(g):
    rs = g[k]; ok = [r for r in rs if r.get('first_imp') is not None]
    dg = [r['final'][2] - r['start'][2] for r in ok]
    print(*k, '|', len(rs), '|', len(ok), '| %.0f%%' % (100 * len(ok) / len(rs)), '|',
          st.median(dg) if dg else None, '|', round(st.median([r['first_imp'] for r in ok])) if ok else None)

print('\n# 1b. same, by pull depth (start GD - cap): all agents')
g = collections.defaultdict(list)
for r in kr:
    s = r.get('start')
    if not s or s[3] is None or r.get('cap_gd') is None or s[3] <= r['cap_gd']: continue
    g[(min(s[3] - r['cap_gd'], 5), bool(r.get('rk')))].append(r)
for k in sorted(g):
    rs = g[k]; ok = [r for r in rs if r.get('first_imp') is not None]
    dg = [r['final'][2] - r['start'][2] for r in ok]
    print('depth', k[0], 'rk', k[1], '|', len(rs), 'reached', len(ok), '| median dG', st.median(dg) if dg else None)

print('\n# 2. P3 lineage stages (rk*, pipe-*, cj*, c11*): dir, mode cap, start -> final, first/last imp, wall')
for r in sorted([r for r in kr if r['agent'] == 'P3'], key=lambda r: r['t0']):
    print('P3', r['dir'], r['mode'], r['cap_gd'], r['start'], '->', r['final'], 'first', r['first_imp'], 'last', r['last_imp'],
          'wall', r['wall'], 'rk', r['rk'], 'pareto', sorted(set((p[0], p[1]) for p in r.get('pareto') or []))[:6])

print('\n# 3. P5 / P4 lineage stages')
for r in sorted([r for r in kr if r['agent'] in ('P5', 'P4')], key=lambda r: r['t0']):
    print(r['agent'], r['dir'], r['mode'], r['cap_gd'], r['start'], '->', r['final'], 'first', r['first_imp'], 'last', r['last_imp'],
          'wall', r['wall'], 'rk', r['rk'])

print('\n# 4. repeats: same start tuple + same start file/parent + same mode + cap, >= 2 runs')
g = collections.defaultdict(list)
for r in kr:
    key = (r['agent'], tuple(r['start'] or ()), r.get('start_file') or os.path.dirname(os.path.dirname(r['dir'])),
           r.get('mode'), r.get('cap_gd'))
    g[key].append(r)
for k, rs in sorted(g.items(), key=lambda kv: -len(kv[1])):
    if len(rs) < 2: continue
    fin = collections.Counter((r['final'][2], r['final'][3]) for r in rs)
    print(k[0], k[1], str(k[2])[-60:], k[3], k[4], '| n', len(rs), '| finals (G,GD):count', dict(fin))

print('\n# 5. conjugate screen score vs outcome (P6 c3-* pipelines; outcome = best G over both stages, and best G at GD <= 27)')
for d in sorted(glob.glob(ROOT + '/P6/runs/c3-*/log.txt')):
    rows = []
    for l in open(d):
        m = re.search(r'lam (\d+) k (\d+) score (\d+).*cap31 stage \d+ best \(35, 3, (\d+), (\d+)\).*cap27 stage \d+ best \(35, 3, (\d+), (\d+)\)', l)
        if m:
            lam, k, sc, g1, d1, g2, d2 = map(int, m.groups())
            best = min((g1, d1), (g2, d2))
            b27 = min([g for g, dd in ((g1, d1), (g2, d2)) if dd <= 27] or [999])
            rows.append((lam, k, sc, best, b27))
    if not rows: continue
    print(os.path.basename(os.path.dirname(d)), [(r[0], r[1], r[2], r[3], r[4]) for r in rows])
    print('  spearman(score, best G any GD) = %.2f; spearman(score, best G at GD<=27) = %.2f; n = %d' % (
        spearman([r[2] for r in rows], [r[3][0] for r in rows]), spearman([r[2] for r in rows], [r[4] for r in rows]), len(rows)))
