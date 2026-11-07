#!/usr/bin/env python3
"""Observed ranges of simple combinations of the proof's coordinates over every canonical phase (orbit steps >= 1)
of the 303 real circuits and of the package's 13 control circuits (C, T, TT); and how many LP-feasible G=75 keys
each observed inequality would exclude.  Nothing here is proved."""
import json, glob, sys, statistics
from collections import Counter
from math import comb
SPRINT = '/home/joebachir20/xs-campaigns/2026-11-07-sprint'
OUT = SPRINT + '/bridge'
sys.path.insert(0, SPRINT + '/lb76/pkg_copy/source/lower_bounds/checks')
sys.path.insert(0, OUT)
from profile_real import orbit  # noqa: E402

d = json.load(open(OUT + '/profiles.json'))
R = [r for r in d['results'] if 'error' not in r]
phases = []   # (source, ori, dict)
for r in R:
    for st in r['orbit'][1:]:
        phases.append((r['tag'].split(':')[0], st))
ctrl = []
for fn in sorted(glob.glob(SPRINT + '/lb76/pkg_copy/source/circuits/*.json')):
    dd = json.load(open(fn))
    recs = orbit(dd['gates'], steps=4)
    for st in recs[1:]:
        ctrl.append(('ctrl:' + fn.split('/')[-1], st))
    ctrl.append(('ctrl0:' + fn.split('/')[-1], recs[0]))
print('phases: real canonical', len(phases), 'control canonical+raw', len(ctrl))

CANDS = {
    'q - y': lambda s: s['q'] - s['y'],
    'q - h': lambda s: s['q'] - s['h'],
    's - h': lambda s: s['s'] - s['h'],
    's - y': lambda s: s['s'] - s['y'],
    'y - F': lambda s: s['y'] - s['F'],
    'h - F': lambda s: s['h'] - s['F'],
    'q': lambda s: s['q'],
    'z': lambda s: s['z'],
    'BB edges (= represented labels)': lambda s: s['bb_edges'],
    'n_even - q': lambda s: s['n_even'] - s['q'],
    'weight-2 labels': lambda s: s['w2'],
    'E_B': lambda s: s['E_B'],
    'n_r0': lambda s: s['n_r'][0],
    'n_r3': lambda s: s['n_r'][3],
    'n_r2 - n_r1': lambda s: s['n_r'][2] - s['n_r'][1],
    '2h + y + z + C(q,2) - 32': lambda s: 2 * s['h'] + s['y'] + s['z'] + comb(s['q'], 2) - 32,
    '3h + 2F + y - 32 - s': lambda s: 3 * s['h'] + 2 * s['F'] + s['y'] - 32 - s['s'],
    'x': lambda s: s['x'],
    'x + y + h (= G - 32)': lambda s: s['x'] + s['y'] + s['h'],
}
print('\n| combination | real canonical phases min / median / max (M ; Mt) | controls min / max (M ; Mt) |')
print('|---|---|---|')
for name, f in CANDS.items():
    def rng(sel):
        v = sorted(f(s) for _, s in sel)
        return '%d / %g / %d' % (v[0], statistics.median(v), v[-1]) if v else '-'
    def rng2(sel):
        v = sorted(f(s) for _, s in sel)
        return '%d / %d' % (v[0], v[-1]) if v else '-'
    print('| %s | %s ; %s | %s ; %s |' % (name, rng([p for p in phases if p[1]['ori'] == 'M']), rng([p for p in phases if p[1]['ori'] == 'Mt']),
                                       rng2([p for p in ctrl if p[1]['ori'] == 'M']), rng2([p for p in ctrl if p[1]['ori'] == 'Mt'])))

# how many LP-feasible keys (h,y,F,q,z,ori) at G=75 violate the observed real-circuit ranges
kk = json.load(open(SPRINT + '/lb76/g75_keys.json'))['feasible']
sv = json.load(open(SPRINT + '/lb76/g75_survivors.json'))['survivor_list']
print('\nLP-feasible keys at 75:', len(kk), '; survivors:', len(sv))
KC = {
    'q - y >= min observed': lambda k: k[3] - k[1],
    's - h >= min observed': lambda k: k[3] + k[4] - k[0],
    'q - h >= min observed': lambda k: k[3] - k[0],
    'y - F >= min observed': lambda k: k[1] - k[2],
    'h - F >= min observed': lambda k: k[0] - k[2],
    'q >= min observed': lambda k: k[3],
}
KR = {'q - y >= min observed': 'q - y', 's - h >= min observed': 's - h', 'q - h >= min observed': 'q - h',
      'y - F >= min observed': 'y - F', 'h - F >= min observed': 'h - F', 'q >= min observed': 'q'}
print('\n| observed inequality (real + controls, canonical phases) | bound | feasible keys violating (M ; Mt) |')
print('|---|---|---|')
for name, g in KC.items():
    f = CANDS[KR[name]]
    lo = min(f(s) for _, s in phases + ctrl)
    viol = Counter(k[5] for k in kk if g(k) < lo)
    print('| %s | >= %d | %d ; %d |' % (name, lo, viol['M'], viol['Mt']))
# survivors' scalar coordinates against observed tail ranges
tails = json.load(open(OUT + '/tail.json'))
real = [t for t in tails if t['G'] == 88]
print('\nsurvivor scalar states violating real-88 observed ranges (not universal, G differs): ')
for k in ('a', 'b', 'Y', 'V', 'he', 'ho'):
    lo, hi = min(t[k] for t in real), max(t[k] for t in real)
    print('  %s in [%d,%d]: survivors outside %d of %d' % (k, lo, hi, sum(1 for s in sv if not lo <= s[k] <= hi), len(sv)))
