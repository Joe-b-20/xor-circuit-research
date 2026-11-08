#!/usr/bin/env python3
"""qcert4: statistics for REPORT.md (standard library; reads the certificate, scan and key files and the checker module)."""
import json, sys
sys.dont_write_bytecode = True
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_cases4 as chk      # noqa: E402
c3 = chk.c3
data = json.load(open(HERE / 'CERTIFICATES_CASES75_B4.json'))
scan = json.load(open(HERE / 'scan_cases4.json'))
kf = json.load(open(HERE / 'keysfull4.json'))
kf3 = json.load(open(HERE.parent / 'qcert3/keysfull3.json'))
cl = {(tuple(c['state']), c['orientation']): c for c in scan['claims']}
P = lambda *a: print(*a, flush=True)
# ---- claims
excl = [(tuple(c['state']), c['orientation']) for c in data['claims']]
P('newly excluded claims', len(excl), dict(Counter(o for s, o in excl)))
fail = Counter(); short = Counter(); rose = Counter()
for c in data['claims']:
    st = tuple(c['state']); a, b, Y, V, ha, hb, la, lb, Sa, Sb, budget = st
    k, l = c['lower_even'], c['lower_odd']; kb, lb3 = c['batch3_lower_even'], c['batch3_lower_odd']
    fail['k+l>budget' if k + l > budget and k <= Sa and l <= Sb else ('k>S_e' if k > Sa else 'l>S_o')] += 1
    short[budget - (kb + lb3)] += 1
    rose['even k' if k > kb else 'odd l'] += 1
P('how they fail (k + l > budget only / k > S_e / l > S_o):', dict(fail))
P('their batch-3 shortfall budget - (k + l):', sorted(short.items()))
P('which bound rose:', dict(rose))
surv = [(tuple(st), o, k, l) for st, o, k, l in scan['new_survivor_bounds']]
P('remaining 686: by ori', dict(Counter(o for _, o, _, _ in surv)), '; shortfall', sorted(Counter(st[10] - (k + l) for st, o, k, l in surv).items()))
# ---- keys
killed = [tuple(k) for k in data['killed_keys']]
feas859 = {tuple(k) for k in kf3['feasible']}; lb551 = {tuple(k) for k in kf3['load_bearing']}
P('killed keys', len(killed), 'by ori', dict(Counter(k[3] for k in killed)), 'by q', sorted(Counter(k[4] for k in killed).items()))
P('  of them in the batch-3 scan LP-feasible 859:', sum(1 for k in killed if k in feas859), '; in the 551 load-bearing:', sum(1 for k in killed if k in lb551),
  '; load-bearing killed by q', sorted(Counter(k[4] for k in killed if k in lb551).items()), 'by ori', dict(Counter(k[3] for k in killed if k in lb551)))
lb388 = {tuple(k) for k in kf['lb551_still_feasible']}; lb452 = {tuple(k) for k in kf['lb551_still_feasible_without_LIM']}
P('  load-bearing 551 -> 452 (P1-P5) -> 388 (+LIM); killed by P1-P5 alone', len(lb551 - lb452), ', by LIM in addition', len(lb452 - lb388))
bykey = {}
for e in data['certificates']: bykey.setdefault(tuple(e['key']), []).append(e)
need = Counter(); nojoint = 0; ncert = []; leaves_with_joint = 0; leaves_total = 0
for k in killed:
    es = bykey[k]; ncert.append(len(es))
    used = set(r for e in es for r in e['joint_rows_used'])
    for r in used: need[r] += 1
    if not used: nojoint += 1
P('killed keys: certificates per key min/max/total', min(ncert), max(ncert), sum(ncert), '; keys whose certificates use the joint row:', dict(need),
  '; keys using no joint row at all:', nojoint)
ref = set()
for c in data['claims']:
    st = tuple(c['state']); ori = c['orientation']; a, b, Y, V, ha, hb, la, lb, Sa, Sb, budget = st
    other = 'Mt' if ori == 'M' else 'M'
    for h, y, F, o, low, cap, bound in ((ha, Y, V, ori, la, Sa, c['lower_even']), (hb, V, Y, other, lb, Sb, c['lower_odd'])):
        for total in range(low, min(cap, bound - 1) + 1):
            for z in range(total + 1):
                q = total - z
                if 2 * h + y + z + c3.c2(q) < 32: continue
                key = (h, y, F, o, q, z)
                if not c3.geometric_exclusion(key): ref.add(key)
kinds = Counter()
for k in ref:
    es = bykey[k]
    kinds[es[0]['kind'] if len(es) == 1 and es[0]['hub'] is None else 'case'] += 1
P('referenced keys', len(ref), 'by certificate kind', dict(kinds), '; of them killed (batch-3-feasible) keys', len(ref & set(killed)))
cases = [e for e in data['certificates'] if e['kind'] == 'case']
P('case certificates by A:', sorted(Counter(e['A'] for e in cases).items()), '; hub-only (dark = none):', sum(1 for e in cases if e['qD'] is None))
P('case certificates using LIM by A = q / A < q:', sum(1 for e in cases if 'LIM' in e['joint_rows_used'] and e['A'] == e['key'][4]),
  sum(1 for e in cases if 'LIM' in e['joint_rows_used'] and e['A'] < e['key'][4]))
P('LIM certificates with A <= q-2 / A = q-1 / A = q:', sum(1 for e in cases if 'LIM' in e['joint_rows_used'] and e['A'] <= e['key'][4] - 2),
  sum(1 for e in cases if 'LIM' in e['joint_rows_used'] and e['A'] == e['key'][4] - 1), sum(1 for e in cases if 'LIM' in e['joint_rows_used'] and e['A'] == e['key'][4]))
mx = max(max(e['weights']) for e in data['certificates']); nz = sum(sum(1 for w in e['weights'] if w) for e in data['certificates'])
P('multipliers total / nonzero / largest:', sum(len(e['weights']) for e in data['certificates']), nz, mx,
  '; rows per certificate', min(len(e['weights']) for e in data['certificates']), '-', max(len(e['weights']) for e in data['certificates']))
P('killed keys by q in the 551 vs not:', sorted(Counter((k[4], k[3], k in lb551) for k in killed).items()))
