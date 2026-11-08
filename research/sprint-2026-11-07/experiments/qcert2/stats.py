#!/usr/bin/env python3
"""qcert2: statistics of CERTIFICATES_CASES75.json and scan_cases75.json for REPORT.md (no LP, no checking)."""
import json, sys
from collections import Counter
from pathlib import Path
HERE = Path.home() / 'xs-campaigns/2026-11-07-sprint/qcert2'
sys.path.insert(0, str(HERE))
import check_cases75 as chk
import gen_certs2 as gen

data = json.load(open(HERE / 'CERTIFICATES_CASES75.json')); scan = json.load(open(HERE / 'scan_cases75.json'))
certs = data['certificates']; claims = data['claims']
killed = [tuple(k) for k in data['killed_keys']]; surv = [tuple(k) for k in data['surviving_keys']]
print('counts:', json.dumps(data['counts']))
# claims
print('claims by orientation:', dict(Counter(c['orientation'] for c in claims)))
how = Counter(); sf = Counter(); dk = Counter()
for c in claims:
    a, b, Y, V, ha, hb, la, lb, Sa, Sb, budget = c['state']; k, l = c['lower_even'], c['lower_odd']
    how['k > S_e' if k > Sa else ('l > S_o' if l > Sb else 'k + l > budget')] += 1
    sf[budget - (c['batch1_lower_even'] + c['batch1_lower_odd'])] += 1
    dk[(k - c['batch1_lower_even'], l - c['batch1_lower_odd'])] += 1
print('how the 317 claims are excluded:', dict(how)); print('their shortfall under batch-1:', dict(sorted(sf.items())))
print('increase of (k, l) over batch-1:', dict(sorted(dk.items())))
# surviving claims
full_surv = scan['full_survivors']; kl = {(tuple(c['state']), c['orientation']): c for c in scan['claims']}
sfs = Counter(); so = Counter()
for st, o in full_surv:
    c = kl[(tuple(st), o)]; k, l, dead = c['full']; sfs[st[10] - k - l] += 1; so[o] += 1
print('surviving claims:', len(full_surv), dict(so), 'shortfall histogram', dict(sorted(sfs.items())))
# keys
print('killed keys by q:', dict(sorted(Counter(k[4] for k in killed).items())), 'by ori:', dict(Counter(k[3] for k in killed)))
print('surviving keys by q:', dict(sorted(Counter(k[4] for k in surv).items())), 'by ori:', dict(Counter(k[3] for k in surv)))
by_key = {}
for e in certs: by_key.setdefault(tuple(e['key']), []).append(e)
def kinds_of(key):
    es = by_key[key]
    hub_only = sum(1 for e in es if e['hub'] is not None and e['dark'] is None)
    dark = sum(1 for e in es if e['dark'] is not None)
    return hub_only, dark
hk = Counter()
for k in killed:
    ho, dk_ = kinds_of(k)
    hk['hub cases only' if dk_ == 0 else ('dark cases only' if ho == 0 and all(e['hub'] is None for e in by_key[k]) else 'hub and dark cases')] += 1
print('killed keys by the cases their certificates use:', dict(hk))
print('certificates per killed key: min/max', min(len(by_key[k]) for k in killed), max(len(by_key[k]) for k in killed), 'total', sum(len(by_key[k]) for k in killed))
ref_only = [k for k in by_key if k not in set(killed)]
kind_ref = Counter(by_key[k][0]['kind'] for k in ref_only)
print('referenced-only keys:', len(ref_only), 'by kind', dict(kind_ref))
b1set = {tuple(k) for k in data['batch1_feasible_keys']}
case_keys = [k for k in by_key if by_key[k][0]['kind'] == 'case']
print('case keys:', len(case_keys), 'in the 681 list:', sum(1 for k in case_keys if k in b1set), 'outside:', sum(1 for k in case_keys if k not in b1set),
      'by q:', dict(sorted(Counter(k[4] for k in case_keys).items())))
# multipliers and row usage
nz = 0; tot = 0; mx = 0; rows_used = Counter(); rows_len = Counter(); rhs = Counter()
for e in certs:
    key = tuple(e['key']); hub = tuple(e['hub']) if e['hub'] else None; dark = e['dark']
    types, aux, A, B, names, n_pkg, n_b1 = gen.ext_system(key, hub, dark)
    w = e['weights']; tot += len(w); nz += sum(1 for v in w if v); mx = max(mx, max(w)); rows_len[len(w)] += 1
    rhs[sum(v * b for v, b in zip(w, B))] += 1
    for v, nme in zip(w, names):
        if v: rows_used[nme.split(' qD=')[0].split(' <=')[0].split(' >=')[0]] += 1
print('multipliers total', tot, 'nonzero', nz, 'largest', mx, 'rows per certificate', min(rows_len), '..', max(rows_len))
print('weighted rhs histogram (top):', sorted(rhs.items(), reverse=True)[:5])
print('rows with a nonzero multiplier (certificates using the row):')
for nme, c in sorted(rows_used.items(), key=lambda x: -x[1]): print(f'   {c:6d}  {nme}')
# new rows used by case certificates only
cu = Counter()
for e in certs:
    if e['kind'] != 'case': continue
    key = tuple(e['key']); hub = tuple(e['hub']) if e['hub'] else None; dark = e['dark']
    types, aux, A, B, names, n_pkg, n_b1 = gen.ext_system(key, hub, dark)
    for v, nme in zip(e['weights'][n_pkg + n_b1:], names[n_pkg + n_b1:]):
        if v: cu[nme.split(' qD=')[0].split(' <=')[0].split(' >=')[0]] += 1
print('case rows used by the 2,497 case certificates:', dict(sorted(cu.items(), key=lambda x: -x[1])))
print('json size MB', round((HERE / 'CERTIFICATES_CASES75.json').stat().st_size / 1e6, 2))
