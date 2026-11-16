#!/usr/bin/env python3
"""M1: current (G, GD) frontier per target inside its hard limits (baseline archive + pinned NIST names +
campaign found/ sidecars), with one file per point. argv[1] = data dir. Read-only."""
import json, os, sys, glob, re

D = sys.argv[1]
ROOT = os.path.expanduser('~/xs-campaigns/2026-11-15-targets')
TG = {t['id']: t for t in json.load(open(os.path.join(ROOT, 'TARGETS.json')))['targets']}
pts = []
for r in json.load(open(os.path.join(ROOT, 'L0/baseline/baseline.json')))['rows']:
    if r.get('ok') and r.get('tuple'): pts.append((tuple(r['tuple']), r['path'], 'archive'))
for p in glob.glob(os.path.expanduser('~/xcr-boolflux/nonlinear/nist/aes-sbox/*.circ.txt')):
    m = re.search(r'-a(\d+)-ad(\d+)-g(\d+)-gd(\d+)', os.path.basename(p))
    if m: pts.append((tuple(map(int, m.groups())), p, 'NIST'))
for l in open(os.path.join(D, 'sidecars.jsonl')):
    s = json.loads(l)
    pts.append((tuple(s['tuple']), os.path.join(ROOT, s['agent'], 'found', s['file'] + '.circ.txt'), s['agent']))
for t, sp in TG.items():
    inn = [p for p in pts if p[0][0] <= sp['A'] and p[0][1] <= sp['AD']]
    front = {}
    for p in inn:
        G, GD = p[0][2], p[0][3]
        if any(q[0][2] <= G and q[0][3] <= GD and (q[0][2], q[0][3]) != (G, GD) for q in inn): continue
        k = (G, GD)
        # prefer fewer ANDs, then lower AD, then campaign file
        if k not in front or (p[0][0], p[0][1]) < (front[k][0][0], front[k][0][1]): front[k] = p
    print('==', t, 'ref %d/%d/%d/%d' % (sp['A'], sp['AD'], sp['G'], sp['GD']))
    for k in sorted(front, key=lambda k: k[1]):
        p = front[k]
        print('  %d/%d/%d/%d  %-8s %s' % (*p[0], p[2], p[1]))
