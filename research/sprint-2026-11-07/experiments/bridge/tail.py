#!/usr/bin/env python3
"""Tail profile (orbit steps 1,2: both canonical transposes, orbit is period 2) and the exact margin identity.
Also prints a few neutral remove1 moves of real circuits (what they exchange)."""
import json, statistics, sys
from collections import Counter
OUT = '/home/joebachir20/xs-campaigns/2026-11-07-sprint/bridge'
d = json.load(open(OUT + '/profiles.json'))
R = [r for r in d['results'] if 'error' not in r]


def dist(v):
    v = sorted(v)
    return '%d / %g / %d' % (v[0], statistics.median(v), v[-1])


def hist(v):
    c = Counter(v)
    return ', '.join('%s:%d' % (k, c[k]) for k in sorted(c))


rows = []
for r in R:
    o = r['orbit']
    s1, s2 = o[1], o[2]
    G = r['G']
    # even phase = larger y (tie: step 1)
    ev, od = (s1, s2) if s1['y'] >= s2['y'] else (s2, s1)
    a, b = ev['x'], od['x']
    budget = a + b + 2 * G - 192
    ssum = ev['s'] + od['s']
    EB = s1['E_B'] + s2['E_B']
    LH = s1['L_H'] + s2['L_H']
    rows.append(dict(tag=r['tag'], G=G, ori_even=ev['ori'], a=a, b=b, Y=ev['y'], V=od['y'], he=ev['h'], ho=od['h'],
                     Fe=ev['F'], Fo=od['F'], qe=ev['q'], ze=ev['z'], qo=od['q'], zo=od['z'], se=ev['s'], so=od['s'],
                     budget=budget, ssum=ssum, margin=ssum - budget, EB=EB, LH=LH, ident=(ssum - budget == -(EB + LH)),
                     Se=3 * ev['h'] + 2 * od['y'] + ev['y'] - 32, So=3 * od['h'] + 2 * ev['y'] + od['y'] - 32,
                     drift2=o[3]['e1'] - o[1]['e1']))
for name, sel in (('sampled 88', [x for x in rows if x['tag'].startswith('sample:')]),
                  ('kste 88', [x for x in rows if x['tag'].startswith('kste:')]),
                  ('repo', [x for x in rows if x['tag'].startswith('repo:')])):
    print('## tail profile,', name, 'N=%d' % len(sel))
    print('identity margin == -(E_B+L_H) on the tail holds:', hist(x['ident'] for x in sel), '; two-step drift on tail:', hist(x['drift2'] for x in sel))
    print('orientation of the even (max-y) phase:', hist(x['ori_even'] for x in sel))
    for k in ('a', 'b', 'Y', 'V', 'he', 'ho', 'Fe', 'Fo', 'qe', 'ze', 'qo', 'zo', 'se', 'so', 'budget', 'ssum', 'margin', 'EB', 'LH', 'Se', 'So'):
        print('  %-7s %-16s %s' % (k, dist(x[k] for x in sel), hist(x[k] for x in sel)))
    print('  (a,b):', hist((x['a'], x['b']) for x in sel))
    print('  (Y,V):', hist((x['Y'], x['V']) for x in sel))
    print('  (he,ho):', hist((x['he'], x['ho']) for x in sel))
    print('  (se,so):', hist((x['se'], x['so']) for x in sel))
    print('  Y+V:', dist(x['Y'] + x['V'] for x in sel), ' he+ho:', dist(x['he'] + x['ho'] for x in sel), ' a+b:', dist(x['a'] + x['b'] for x in sel))
    print('  s_e <= S_e slack:', dist(x['Se'] - x['se'] for x in sel), ' s_o <= S_o slack:', dist(x['So'] - x['so'] for x in sel))
    for x in sel if name == 'repo' else []:
        print('  ', x)
json.dump(rows, open(OUT + '/tail.json', 'w'))

# neutral moves of a few circuits
sys.path.insert(0, '/home/joebachir20/xs-campaigns/2026-11-05-exit/pes')
from pes_lib import make_space, fan  # noqa: E402
sp = make_space('mc', None)
pc = lambda v: bin(v).count('1')
agg = Counter()
for r in [x for x in R if x['tag'].startswith('sample:')][:40]:
    S = frozenset(v for v in r['values'] if v not in sp.tset)
    g, dep, neutral, downs, binds = fan(sp, S)
    for Rm, A, hk, dd in neutral:
        agg[(tuple(sorted(pc(v) for v in Rm)), tuple(sorted(pc(v) for v in A)))] += 1
print('## neutral move shapes over 40 circuits: (weights removed) -> (weights added): count')
for k, c in agg.most_common(25):
    print('  ', k, c)
r = [x for x in R if x['tag'].startswith('sample:')][0]
S = frozenset(v for v in r['values'] if v not in sp.tset)
g, dep, neutral, downs, binds = fan(sp, S)
print('## example', r['tag'], 'gates', g, 'neutral', len(neutral))
for Rm, A, hk, dd in neutral[:12]:
    print('   remove', ['%08x(w%d)' % (v, pc(v)) for v in sorted(Rm)], 'add', ['%08x(w%d)' % (v, pc(v)) for v in sorted(A)])
