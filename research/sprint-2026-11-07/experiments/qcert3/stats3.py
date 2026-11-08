#!/usr/bin/env python3
"""qcert3: statistics for REPORT.md (no LP): kill counts by q / orientation, how the 207 claims fail, row usage of the
certificates, multipliers, survivor shortfalls.  Imports gen_certs3 only for the row names (ext_system; no LP is run)."""
import json, sys
from collections import Counter
from pathlib import Path
SPRINT = Path.home() / 'xs-campaigns/2026-11-07-sprint'
HERE = SPRINT / 'qcert3'
sys.path.insert(0, str(HERE))
import gen_certs3 as gen   # noqa: E402

d = json.load(open(HERE / 'CERTIFICATES_CASES75_B3.json'))
scan = json.load(open(HERE / 'scan_cases3.json'))
kf = json.load(open(HERE / 'keysfull3.json'))
killed = [tuple(k) for k in d['killed_keys']]; bkilled = [tuple(k) for k in d['baseline_killed_keys']]; bsurv = [tuple(k) for k in d['baseline_surviving_keys']]
surv = [tuple(k) for k in d['surviving_keys']]
byq = lambda ks: sorted(Counter(k[4] for k in ks).items()); byo = lambda ks: dict(Counter(k[3] for k in ks))
print('killed keys (all)      ', len(killed), 'by q', byq(killed), 'by ori', byo(killed))
print('killed keys (baseline) ', len(bkilled), 'by q', byq(bkilled), 'by ori', byo(bkilled))
print('surviving (baseline)   ', len(bsurv), 'by q', byq(bsurv), 'by ori', byo(bsurv))
print('surviving (union)      ', len(surv), 'by q', byq(surv))
feas = [tuple(k) for k in kf['feasible']]; lb = [tuple(k) for k in kf['load_bearing']]
print('scan: touched', kf['touched'], 'LP-feasible', len(feas), 'by q', byq(feas), 'by ori', byo(feas), '; load-bearing', len(lb), 'by q', byq(lb), 'by ori', byo(lb), '; load-bearing in baseline', len(set(lb) & set(d['baseline_keys'] and {tuple(k) for k in d['baseline_keys']})))
# claims
fail = Counter(); short2 = Counter(); byori = Counter(); side = Counter()
for c in d['claims']:
    st = c['state']; a, b, Y, V, he, ho, le_, lo_, Se, So, budget = st
    k, l, k2, l2 = c['lower_even'], c['lower_odd'], c['batch2_lower_even'], c['batch2_lower_odd']
    fail['k>Se' if k > Se else ('l>So' if l > So else 'k+l>budget')] += 1
    short2[budget - (k2 + l2)] += 1; byori[c['orientation']] += 1
    side['even rose' if k > k2 else ('odd rose' if l > l2 else 'neither')] += 1
print('claims', len(d['claims']), 'by ori', dict(byori), 'fail', dict(fail), 'batch-2 shortfall', sorted(short2.items()), 'which side rose', dict(side))
sf = Counter(); sfo = Counter()
for st, o, k, l in scan['full_survivor_bounds']:
    sf[st[10] - (k + l)] += 1; sfo[o] += 1
print('789 survivors: by ori', dict(sfo), 'shortfall', sorted(sf.items()))
# certificates
certs = d['certificates']
kinds = Counter(c['kind'] for c in certs); print('certificates', len(certs), dict(kinds))
per_key = Counter(tuple(c['key']) for c in certs)
kc = [per_key[k] for k in killed]; print('certificates per killed key: min', min(kc), 'max', max(kc), 'total', sum(kc), '; per baseline killed key total', sum(per_key[k] for k in bkilled))
kind_of = {}
for c in certs: kind_of.setdefault(tuple(c['key']), c['kind'])
print('killed keys by kind', dict(Counter(kind_of[k] for k in killed)), '; baseline', dict(Counter(kind_of[k] for k in bkilled)))
hubonly = darkonly = both = 0
for k in killed:
    cs = [c for c in certs if tuple(c['key']) == k and c['kind'] == 'case']
    if not cs: continue
    h = any(c['hub'] is not None for c in cs); dd = any(c['dark'] is not None for c in cs)
    if h and dd: both += 1
    elif h: hubonly += 1
    else: darkonly += 1
print('killed case keys using hub cases only / dark only / both:', hubonly, darkonly, both)
nm = 0; nz = 0; mx = 0; rows = []; use = Counter(); rhs = []
for c in certs:
    w = c['weights']; nm += len(w); nz += sum(1 for x in w if x); mx = max(mx, max(w)); rows.append(len(w))
    key = tuple(c['key']); hub = tuple(c['hub']) if c['hub'] else None
    types, aux, A, B, names, n_pkg, n_b1, n_flat = gen.ext_system(key, hub, c['dark'])
    rhs.append(sum(x * b for x, b in zip(w, B)))
    if c['kind'] in ('case', 'flat'):
        for x, n in zip(w, names):
            if x:
                n2 = n.split(' qD=')[0].split(' chord')[0].split(':')[0]
                if n2.startswith('HUB2 A = '): n2 = 'HUB2 A = a'
                use[n2] += 1
print('multipliers total', nm, 'nonzero', nz, 'largest', mx, '; rows per certificate', min(rows), '-', max(rows), '; largest weighted rhs', max(rhs))
print('row usage by the case + flat certificates (nonzero multiplier):')
for n, cnt in sorted(use.items(), key=lambda x: -x[1]): print(f'   {cnt:5d}  {n}')
hubs = Counter(str(tuple(c['hub'])) for c in certs if c['hub']); darks = Counter(c['dark'] for c in certs if c['dark'] is not None)
print('hub cases', dict(sorted(hubs.items())), 'dark cases', dict(sorted(darks.items())))
# referenced keys: kinds
needed = set()
for c in d['claims']:
    st = c['state']; a, b, Y, V, he, ho, le_, lo_, Se, So, budget = st; ori = c['orientation']; other = 'Mt' if ori == 'M' else 'M'
    for h, y, F, o, low, cap, bound in ((he, Y, V, ori, le_, Se, c['lower_even']), (ho, V, Y, other, lo_, So, c['lower_odd'])):
        for total in range(low, min(cap, bound - 1) + 1):
            for z in range(total + 1):
                q = total - z
                if 2 * h + y + z + q * (q - 1) // 2 < 32: continue
                kk = (h, y, F, o, q, z)
                if q == 0 and (z == 0 or (o == 'Mt' and z <= 7)): continue
                needed.add(kk)
print('referenced keys', len(needed), 'by kind', dict(Counter(kind_of[k] for k in needed)), '; among the killed', len(needed & set(killed)), '; among baseline killed', len(needed & set(bkilled)))
