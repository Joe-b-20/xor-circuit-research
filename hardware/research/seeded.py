#!/usr/bin/env python3
"""Statistics on the seeded repeats (results/table.csv base values + results/seeds.csv) -> results/seeded.json, SEEDED.md

    python3 hardware/research/seeded.py

Per (circuit, library, flow) the repeats are the base run plus every seeded variant run there:
placement seeds pnr1-3 on every flow, and for the free flows also synth1-2 (RTL statement order
plus placement).  Then:

  groups      the seeded same-metric groups: one-way ANOVA of each measure (between circuits vs
              within a circuit's repeats), F-test p, and the share of variance due to structure
              (intraclass correlation ICC(1)); best and worst member by mean
  inversions  the seeded dominance-inversion pairs: in every configuration, the mean relative gain
              of the logically worse circuit, Welch t-test p (one-sided, worse < better), and
              whether it holds there (p < 0.05)
  first pair  the benchmark's first pair with seed means and standard deviations
"""
from __future__ import annotations

import collections
import csv
import json
import pathlib

import numpy as np
from scipy import stats

HERE = pathlib.Path(__file__).resolve().parent
RES = HERE / 'results'
MEAS = ('area', 'delay', 'adp', 'power')
CONFIGS = [(p, f) for p in ('nangate45', 'sky130hd') for f in ('preserve', 'free', 'free-area')]


def short(c):
    return c.split('--', 1)[1]


def main():
    rows = list(csv.DictReader(open(RES / 'table.csv')))
    seeds = list(csv.DictReader(open(RES / 'seeds.csv')))
    vals = collections.defaultdict(list)
    info = {}
    for r in rows:
        if r.get('dup_of'):
            continue
        info[r['circuit']] = r
        vals[(r['circuit'], r['platform'], r['flow'])].append({m: float(r[m]) for m in MEAS})
    for s in seeds:
        k = (s['circuit'], s['platform'], s['flow'])
        if k in vals:
            vals[k].append({m: float(s[m]) for m in MEAS})
    why = {}
    for line in open(HERE / 'lists' / 'seeds.txt'):
        f, _, w = line.partition('#')
        why[pathlib.Path(f.strip()).name[:-len('.circ.txt')]] = w.strip()
    seeded = {c for (c, p, f), v in vals.items() if len(v) >= 3}

    def series(c, p, f, m):
        return np.array([x[m] for x in vals.get((c, p, f), [])])

    # groups
    iso_keys = {(w.split()[1], w.split()[2]) for w in why.values() if w.startswith('iso')}
    groups = collections.defaultdict(set)
    for c in seeded:
        r = info[c]
        if (r['function'], r['key']) in iso_keys:
            groups[(r['function'], r['key'])].add(c)
    gout = []
    for (fn, k), cs in sorted(groups.items()):
        cs = sorted(cs)
        if len(cs) < 3:
            continue
        for p, f in CONFIGS:
            for m in ('delay', 'power', 'adp', 'area'):
                ss = [series(c, p, f, m) for c in cs]
                ss = [s for s in ss if len(s) >= 3]
                if len(ss) < 3:
                    continue
                grand = np.concatenate(ss)
                if np.ptp(grand) == 0:
                    continue
                with np.errstate(all='ignore'):
                    F, pv = stats.f_oneway(*ss)
                n0 = np.mean([len(s) for s in ss])
                msb = sum(len(s) * (s.mean() - grand.mean()) ** 2 for s in ss) / (len(ss) - 1)
                msw = sum(((s - s.mean()) ** 2).sum() for s in ss) / (len(grand) - len(ss))
                icc = (msb - msw) / (msb + (n0 - 1) * msw) if msb + (n0 - 1) * msw > 0 else 1.0
                means = sorted((s.mean(), c) for s, c in zip(ss, cs))
                gout.append({'function': fn, 'key': k, 'platform': p, 'flow': f, 'measure': m,
                             'circuits': len(ss), 'repeats': int(n0), 'F': float(F) if np.isfinite(F) else None,
                             'p': float(pv) if np.isfinite(pv) else 0.0, 'icc': float(icc),
                             'best': means[0][1], 'best_mean': float(means[0][0]),
                             'worst': means[-1][1], 'worst_mean': float(means[-1][0]),
                             'spread': float(means[-1][0] / means[0][0] - 1),
                             'noise_cv': float(np.median([s.std(ddof=1) / s.mean() for s in ss]))})
    # inversions
    iout = []
    a = json.loads((RES / 'analysis.json').read_text())
    best = {}
    for t in a['inversions_top']:
        if t['measure'] == 'area' and t['flow'] == 'preserve':
            continue
        k = (t['function'], t['platform'], t['flow'], t['measure'])
        if k not in best or t['gain'] > best[k]['gain']:
            best[k] = t
    for k, t in sorted(best.items()):
        b, g = t['worse_logically'], t['better_logically']
        if b not in seeded or g not in seeded:
            continue
        res = {'found_in': '%s %s %s %s' % k, 'worse_logically': b, 'key_worse': t['key_worse'],
               'better_logically': g, 'key_better': t['key_better'], 'base_gain': t['gain'], 'configs': {}}
        for p, f in CONFIGS:
            xb, xg = series(b, p, f, k[3]), series(g, p, f, k[3])
            if len(xb) < 3 or len(xg) < 3:
                continue
            gain = 1 - xb.mean() / xg.mean()
            if np.ptp(np.concatenate([xb, xg])) == 0:
                pv = 0.0 if gain > 0 else 1.0
            else:
                pv = float(stats.ttest_ind(xb, xg, equal_var=False, alternative='less').pvalue)
            res['configs']['%s/%s' % (p, f)] = {'gain': float(gain), 'p': pv, 'holds': bool(pv < 0.05 and gain > 0),
                                                'n': [len(xb), len(xg)]}
        iout.append(res)
    # first pair
    fp = {}
    for c in ('ours--aes-invsbox-a40-ad4-g134-gd12-xx94-41', 'nist--aes-invsbox-a45-ad4-g141-gd12-xx96-25'):
        for p, f in CONFIGS:
            for m in MEAS:
                s = series(c, p, f, m)
                if len(s):
                    fp['%s|%s|%s|%s' % (c, p, f, m)] = {'mean': float(s.mean()), 'sd': float(s.std(ddof=1)) if len(s) > 1 else 0.0, 'n': len(s)}
    out = {'groups': gout, 'inversions': iout, 'first_pair': fp}
    (RES / 'seeded.json').write_text(json.dumps(out, indent=1) + '\n')
    # markdown
    md = ['# Seeded repeats (generated by seeded.py)', '',
          '## Same-metric groups: structure vs noise (one-way ANOVA over each circuit\'s repeats)', '',
          'ICC: share of the variance due to the circuit (structure); spread: worst mean / best mean - 1.', '',
          '| Function | key | Library | Flow | measure | circuits | repeats | spread | noise CV | ICC | p |',
          '|---|---|---|---|---|---:|---:|---:|---:|---:|---:|']
    for g in gout:
        if g['measure'] not in ('delay', 'power'):
            continue
        md.append('| %s | %s | %s | %s | %s | %d | %d | %.1f%% | %.2f%% | %.2f | %.2g |' % (
            g['function'], g['key'], g['platform'], g['flow'], g['measure'], g['circuits'], g['repeats'],
            100 * g['spread'], 100 * g['noise_cv'], g['icc'], g['p']))
    md += ['', '## Apparent dominance inversions under repeats', '',
           'The logically worse circuit (first) against the one dominating it; gain = 1 - mean(worse)/mean(better) '
           'of the measure the inversion was found on; holds = Welch p < 0.05 and gain > 0.', '',
           '| found in | worse (key) | better (key) | base gain | ' + ' | '.join('%s/%s' % c for c in CONFIGS) + ' |',
           '|---|---|---|---:|' + '---|' * 6]
    for r in iout:
        cells = []
        for p, f in CONFIGS:
            v = r['configs'].get('%s/%s' % (p, f))
            cells.append('—' if not v else '%+.1f%%%s' % (100 * v['gain'], ' ✓' if v['holds'] else ''))
        md.append('| %s | %s (%s) | %s (%s) | %.1f%% | %s |' % (
            r['found_in'], short(r['worse_logically'])[:46], r['key_worse'], short(r['better_logically'])[:46],
            r['key_better'], 100 * r['base_gain'], ' | '.join(cells)))
    (RES / 'SEEDED.md').write_text('\n'.join(md) + '\n')
    print('wrote', RES / 'SEEDED.md', len(gout), 'group rows', len(iout), 'pairs')


if __name__ == '__main__':
    main()
