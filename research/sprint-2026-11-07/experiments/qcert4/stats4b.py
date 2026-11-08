#!/usr/bin/env python3
"""qcert4: extra statistics for REPORT.md -- the killed key certified without any joint row, J1 dependence by key /
claim, the 74 J1 certificates, multiplier sizes, partial-certificate summary."""
import json
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent
d = json.load(open(HERE / 'CERTIFICATES_CASES75_B4.json'))
bykey = {}
for e in d['certificates']: bykey.setdefault(tuple(e['key']), []).append(e)
killed = [tuple(k) for k in d['killed_keys']]
nj = [k for k in killed if not any(e['joint_rows_used'] for e in bykey[k])]
print('killed keys certified without any joint row:', nj, [(e['A'], e['qD']) for k in nj for e in bykey[k]])
j1keys = [k for k in killed if any(e['uses_J1'] for e in bykey[k])]
print('killed keys whose coverage uses J1:', len(j1keys), 'by q', sorted(Counter(k[4] for k in j1keys).items()), 'by ori', dict(Counter(k[3] for k in j1keys)))
j1c = [e for e in d['certificates'] if e['uses_J1']]
print('J1 certificates:', len(j1c), 'by (q, A)', sorted(Counter((e['key'][4], e['A']) for e in j1c).items()), '; whole hub case', sum(1 for e in j1c if e['qD'] is None))
mx = sorted((max(e['weights']) for e in d['certificates']), reverse=True)
print('largest multipliers:', mx[:5], '; certificates with max multiplier > 10^6:', sum(1 for m in mx if m > 10 ** 6), '; median max', mx[len(mx) // 2])
print('without LIM (LP scan): survivors', d['counts']['survivors_without_LIM'], '; of the 789 excluded', d['counts']['newly_excluded_without_LIM'])
cl_free = {(tuple(s), o) for s, o in d['claims_excluded_without_LIM']}
print('claims excluded without LIM by ori:', dict(Counter(o for s, o in cl_free)))
p = json.load(open(HERE / 'CERTIFICATES_PARTIAL75_B4.json'))
print('partial:', p['counts'])
ol = {tuple(k): v for k, v in p['open_leaves']}
print('surviving keys by number of open leaves:', sorted(Counter(len(v) for v in ol.values()).items())[:12], '...')
print('open leaves by A value:', sorted(Counter(a for v in ol.values() for a, dd in v).items()))
print('open leaves with A = 0:', sum(1 for v in ol.values() for a, dd in v if a == 0), '; surviving keys open only at A = 0:', sum(1 for v in ol.values() if all(a == 0 for a, dd in v)))
