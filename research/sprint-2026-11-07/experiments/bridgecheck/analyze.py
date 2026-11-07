#!/usr/bin/env python3
"""Summaries of bridgecheck/recheck.json for REPORT.md."""
import json, statistics
from collections import Counter

OUT = '/home/joebachir20/xs-campaigns/2026-11-07-sprint/bridgecheck'
d = json.load(open(OUT + '/recheck.json'))
R = d['results']
print('circuits', len(R), 'seconds %.0f' % d['seconds'])


def dist(v):
    v = sorted(v)
    return '%d / %g / %d' % (v[0], statistics.median(v), v[-1])


def hist(v):
    c = Counter(v)
    return ', '.join('%s:%d' % (k, c[k]) for k in sorted(c, key=str))


print('\n## (a) reconstruction')
print('raw pairs per value (no levelling), values with >1 pair per circuit:', hist(r['n_amb_values'] for r in R))
print('acyclic reconstructions per circuit:', hist(r['n_acyclic_reconstructions'] for r in R))
print('levelled-ambiguous values (my count / bridge count):', hist('%d/%d' % (r['n_multi_levelled'], r['n_multi_bridge']) for r in R))
for r in R:
    if r['n_acyclic_reconstructions'] > 1:
        print('  ', r['tag'], 'recons', r['n_acyclic_reconstructions'], 'yx over recons', r['yx_over_reconstructions'],
              'alternatives:', [(a['x'], a['y'], a['q'], a['z'], a['F'], a['E_B'], a['raw_margin']) for a in r['alternatives']][:6],
              'base C:', (r['orbit'][0]['x'], r['orbit'][0]['y'], r['orbit'][0]['q'], r['orbit'][0]['z'], r['orbit'][0]['F'], r['orbit'][0]['E_B'], r['two_raw']['margin']))
for r in R:
    if 'true_eq_recon' in r:
        print('  ', r['tag'], 'true gate list == reconstruction (equation sets):', r['true_eq_recon'],
              '| true tail margin', r['true_two_tail']['margin'], 'EB', r['true_two_tail']['EB'], '| recon tail margin', r['two_tail']['margin'], 'EB', r['two_tail']['EB'])

print('\n## (b) package assertions / rows: all circuits ran through analyse without AssertionError (else the script would have died).')
viol = [(r['tag'], o['step'], k, v) for r in R for o in r['orbit'] for k, v in o['rows'].items() if v < 0]
print('row violations:', viol)

print('\n## comparison with bridge/profiles.json')
print('circuits with any difference in (ori,x,y,h,q,z,s,F,F_H,F_B,e1,xp,E_B,L_H,types,rows) over 6 steps:', sum(1 for r in R if r['diff_vs_profiles']))
for r in R:
    if r['diff_vs_profiles']:
        print('  ', r['tag'], r['diff_vs_profiles'][:8])
print('bridge two (raw) vs mine (raw) margin equal:', hist(r['bridge_two']['margin'] == r['two_raw']['margin'] for r in R))

print('\n## (c) periodicity (deterministic canonical choice, as the bridge used)')
for key in ('vals_0_2', 'eqs_0_2', 'vals_1_3', 'eqs_1_3', 'vals_2_4', 'eqs_2_4', 'vals_3_5', 'eqs_3_5'):
    print('  %-9s %s' % (key, hist(r['period'][key] for r in R)))
print('  profile sequences (y):', hist(tuple(o['y'] for o in r['orbit'][1:]) == tuple(o['y'] for o in r['orbit'][1:3]) * 2 + tuple(o['y'] for o in r['orbit'][1:2]) for r in R))
print('  e1 sequence period-2 from step 1 (e1[j+2]==e1[j], j>=1):', hist(all(r['orbit'][j + 2]['e1'] == r['orbit'][j]['e1'] for j in (1, 2, 3)) for r in R))
print('  s sequence period-2 from step 1:', hist(all(r['orbit'][j + 2]['s'] == r['orbit'][j]['s'] for j in (1, 2, 3)) for r in R))
print('  E_B sequence period-2 from step 1:', hist(all(r['orbit'][j + 2]['E_B'] == r['orbit'][j]['E_B'] for j in (1, 2, 3)) for r in R))
print('  (x,y,h,q,z,F,E_B,types) period-2 from step 1:', hist(all(all(r['orbit'][j + 2][k] == r['orbit'][j][k] for k in ('x', 'y', 'h', 'q', 'z', 'F', 'E_B', 'types')) for j in (1, 2, 3)) for r in R))
print('  drift e1[3]-e1[1]:', hist(r['orbit'][3]['e1'] - r['orbit'][1]['e1'] for r in R), ' e1[2]-e1[0] (raw):', hist(r['orbit'][2]['e1'] - r['orbit'][0]['e1'] for r in R))
print('  e1 along orbit, examples:', [[o['e1'] for o in r['orbit']] for r in R[:6]])
print('  which step-1 circuits are NOT period 2 as circuits but are as profiles:',
      sum(1 for r in R if not r['period']['eqs_1_3'] and all(r['orbit'][3][k] == r['orbit'][1][k] for k in ('x', 'y', 'h', 'q', 'z', 'F', 'E_B'))))

print('\n## (c\') random canonical tie-breaks (3 seeds per circuit, 5 steps)')
pers = Counter()
drift = Counter()
marg_eq = Counter()
for r in R:
    for x in r['random_canonical']:
        pers[(x['per']['eqs_1_3'], x['per']['eqs_2_4'])] += 1
        drift[x['e1'][3] - x['e1'][1]] += 1
        marg_eq[x['tail']['margin'] == -(x['tail']['EB'] + x['tail']['LH'])] += 1
print('  (eqs_1_3, eqs_2_4):', dict(pers))
print('  drift e1[3]-e1[1]:', dict(drift))
print('  tail margin == -(E_B+L_H):', dict(marg_eq))
print('  tail margins:', hist(x['tail']['margin'] for r in R for x in r['random_canonical']), ' E_B:', hist(x['tail']['EB'] for r in R for x in r['random_canonical']))
print('  y sequences differ from deterministic:', sum(1 for r in R for x in r['random_canonical'] if x['ys'] != [o['y'] for o in r['orbit'][:5]]))
print('  s sequences differ from deterministic:', sum(1 for r in R for x in r['random_canonical'] if x['ss'] != [o['s'] for o in r['orbit'][:5]]))
print('  E_B sequences differ from deterministic:', sum(1 for r in R for x in r['random_canonical'] if x['EB'] != [o['E_B'] for o in r['orbit'][:5]]))

print('\n## (d) two-phase identity, tail (steps 1,2), even = max-y phase as in the bridge')
rows = []
for r in R:
    o = r['orbit']
    s1, s2 = o[1], o[2]
    ev, od = (s1, s2) if s1['y'] >= s2['y'] else (s2, s1)
    G = r['G']
    budget = ev['x'] + od['x'] + 2 * G - 192
    ssum = ev['s'] + od['s']
    EB = s1['E_B'] + s2['E_B']
    LH = s1['L_H'] + s2['L_H']
    rows.append(dict(tag=r['tag'], G=G, a=ev['x'], b=od['x'], Y=ev['y'], V=od['y'], he=ev['h'], ho=od['h'], qe=ev['q'], ze=ev['z'], qo=od['q'], zo=od['z'],
                     se=ev['s'], so=od['s'], budget=budget, ssum=ssum, margin=ssum - budget, EB=EB, LH=LH, ori_even=ev['ori'],
                     ok=(ssum - budget == -(EB + LH)), drift=o[3]['e1'] - o[1]['e1'],
                     Se=3 * ev['h'] + 2 * od['y'] + ev['y'] - 32, So=3 * od['h'] + 2 * ev['y'] + od['y'] - 32,
                     Se2=2 * od['x'] - ev['x'] + G - 96 + od['y'], So2=2 * ev['x'] - od['x'] + G - 96 + ev['y']))
for name, sel in (('88s (hunt+kste+repo88)', [x for x in rows if x['G'] == 88]), ('repo 89, 97', [x for x in rows if x['G'] != 88])):
    print(' ', name, 'N=%d' % len(sel))
    print('   margin == -(E_B+L_H):', hist(x['ok'] for x in sel), ' drift:', hist(x['drift'] for x in sel))
    for k in ('a', 'b', 'Y', 'V', 'he', 'ho', 'qe', 'ze', 'qo', 'zo', 'se', 'so', 'budget', 'ssum', 'margin', 'EB', 'LH'):
        print('   %-7s %-16s %s' % (k, dist(x[k] for x in sel), hist(x[k] for x in sel)))
    print('   even phase orientation:', hist(x['ori_even'] for x in sel))
    print('   Lemma 8.2 upper bounds: S_e - s_e', dist(x['Se'] - x['se'] for x in sel), '; (2b-a+G-96+V) - s_e', dist(x['Se2'] - x['se'] for x in sel),
          '; S_o - s_o', dist(x['So'] - x['so'] for x in sel), '; (2a-b+G-96+Y) - s_o', dist(x['So2'] - x['so'] for x in sel))
    for x in sel if name.startswith('repo') else []:
        print('   ', x)
# per-phase one-step identity residual: s = e(T) - e(C) - 96 + G - x + 2x' - E_B - L_H  (always 0 by (E)); report E_B per phase and L_H raw
print('  per-phase E_B, canonical phases 1-5:', hist(o['E_B'] for r in R for o in r['orbit'][1:]), ' raw phase 0:', hist(r['orbit'][0]['E_B'] for r in R))
print('  L_H raw phase 0:', hist(r['orbit'][0]['L_H'] for r in R), ' canonical:', hist(o['L_H'] for r in R for o in r['orbit'][1:]))
print('  raw two-phase (steps 0,1) margin:', hist(r['two_raw']['margin'] for r in R), ' = -(EB+LH)?', hist(r['two_raw']['margin'] == -(r['two_raw']['EB'] + r['two_raw']['LH']) for r in R),
      ' drift e1[2]-e1[0]:', hist(r['two_raw']['drift'] for r in R))

print('\n## (e)/(g) profiles and helpers')
can = [o for r in R if r['G'] == 88 for o in r['orbit'][1:]]
raw = [r['orbit'][0] for r in R if r['G'] == 88]
for k in ('x', 'y', 'h', 'q', 'z', 's', 'F', 'E_B'):
    print('   %-4s canonical phases %-16s  raw C %s' % (k, dist(o[k] for o in can), dist(o[k] for o in raw)))
print('   h (odd non-output helpers) raw C of 88s:', hist(o['h'] for o in raw), ' canonical:', hist(o['h'] for o in can))
print('   weight-2 even values all represented (canonical + raw):', hist(o['w2'] == o['w2_rep'] for r in R for o in r['orbit']), ' w2 per raw C:', dist(o['w2'] for o in raw))
print('   helper min odd-degree, canonical:', hist(o['hdeg_min'] for o in can), ' raw:', hist(o['hdeg_min'] for o in raw))
print('   helper fan-out hist, canonical 88 phases:', sum((Counter({int(k): v for k, v in o['helper_fanout'].items()}) for o in can), Counter()))

print('\n## (f) row slacks, canonical phases 1-5 of all 40 (min / median), by orientation')
names = sorted({k for o in can for k in o['rows']})
allcan = [o for r in R for o in r['orbit'][1:]]
for nm in names:
    vals_M = [o['rows'][nm] for o in allcan if nm in o['rows'] and o['ori'] == 'M']
    vals_T = [o['rows'][nm] for o in allcan if nm in o['rows'] and o['ori'] == 'Mt']
    print('   %-36s M: %-16s Mt: %s' % (nm, dist(vals_M) if vals_M else '-', dist(vals_T) if vals_T else '-'))
m = min((o['rows'][nm], nm, r['tag'], o['step']) for r in R if r['G'] == 88 for o in r['orbit'][1:] for nm in o['rows'] if nm != 'helper degree >= 2 (any circuit)')
print('   min slack over canonical 88 phases excluding the degree row:', m)
m2 = min((o['rows'][nm], nm, r['tag'], o['step']) for r in R for o in r['orbit'][1:] for nm in o['rows'] if nm != 'helper degree >= 2 (any circuit)')
print('   min slack over all 40 canonical phases excluding the degree row:', m2)
print('   raw phase 0 min slack (excl. degree row):', min((o['rows'][nm], nm, r['tag']) for r in R for o in r['orbit'][:1] for nm in o['rows'] if nm != 'helper degree >= 2 (any circuit)'))
