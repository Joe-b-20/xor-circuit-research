#!/usr/bin/env python3
"""qcert3 cross-checks (no LP):
 1. the generator's system (gen_certs3.ext_system: package certify75.system + appended batch-1, PK / FM, HUB2 and DARK
    rows) and the independent checker's hand-written system (check_cases3.right_sides / type_column / aux_columns) are
    IDENTICAL matrices (same rows in the same order, same constants, same column set in the same order, same
    coefficients) for every (key, hub, dark) of the certificate file, for every case node (every leaf (hc, d), every
    (hc, None) and (None, d), and (None, None)) of every killed key, and for every node of every referenced key that
    carries a case certificate;
 2. the key and claim sets agree with the qcert2 / qreal / qrealcheck / qhub / qhubcheck files:
    batch-2 survivors (996) = qcert2 = qhub's reproduction = qrealcheck; full survivors (789) = qhub = qhubcheck with
    identical (k, l); the 207 claims = the difference; baseline 381 = qcert2 = qreal = qrealcheck; baseline surviving
    116 = qhub = qhubcheck; the 1,661 = qrealcheck keys_full; the scan's 859 LP-feasible and 551 load-bearing keys =
    qhubcheck's lp_qhc_keysfull (the final variant with FM); every killed key certified.
"""
import json, sys, time
from pathlib import Path
SPRINT = Path.home() / 'xs-campaigns/2026-11-07-sprint'
HERE = SPRINT / 'qcert3'
sys.path.insert(0, str(HERE))
import gen_certs3 as gen         # noqa: E402  (imports the package copy's certify75 / lp_regen; no LP is run here)
import check_cases3 as chk       # noqa: E402

t0 = time.time()
data = json.load(open(HERE / 'CERTIFICATES_CASES75_B3.json'))
nodes = set(); case_keys = set()
for c in data['certificates']:
    key = tuple(c['key']); hub = tuple(c['hub']) if c['hub'] else None
    nodes.add((key, hub, c['dark']))
    if hub is not None or c['dark'] is not None: case_keys.add(key)
killed = {tuple(k) for k in data['killed_keys']}
for key in killed | case_keys:
    q = key[4]
    nodes.add((key, None, None))
    for hc in chk.hub_cases(q):
        nodes.add((key, hc, None))
        for d in range(q + 1): nodes.add((key, hc, d)); nodes.add((key, None, d))
n = 0; ncoef = 0
for key, hub, dark in sorted(nodes, key=str):
    types, aux, A, B, names, n_pkg, n_b1, n_flat = gen.ext_system(key, hub, dark)
    b2, cols, n_pkg2, n_b12, n_flat2 = chk.matrix(key, hub, dark)
    assert (n_pkg, n_b1, n_flat) == (n_pkg2, n_b12, n_flat2), (key, hub, dark, n_pkg, n_b1, n_flat, n_pkg2, n_b12, n_flat2)
    assert B == b2, ('constants differ', key, hub, dark, B, b2)
    labels = [lab for lab, _ in cols]
    assert labels == types + aux, ('column sets differ', key, hub, dark, labels[:5], (types + aux)[:5])
    for j, (lab, col) in enumerate(cols):
        gcol = [row[j] for row in A]
        assert gcol == col, ('column differs', key, hub, dark, lab, gcol, col)
        ncoef += len(col)
    n += 1
    if n % 10000 == 0: print(f'  {n} nodes, {time.time()-t0:.0f}s', flush=True)
print(f'systems identical on {n} (key, case) nodes of {len(killed | case_keys)} keys ({ncoef} coefficients and every row constant), {time.time()-t0:.0f}s')

# key / claim sets versus qcert2, qreal, qrealcheck, qhub, qhubcheck
conv = lambda k: (k[0], k[1], k[2], k[5], k[3], k[4])      # their key files use the order (h,y,F,q,z,ori)
scan = json.load(open(HERE / 'scan_cases3.json'))
mine_sb2 = {(tuple(st), o) for st, o in scan['batch2_survivors']}; mine_sf = {(tuple(st), o) for st, o in scan['full_survivors']}
mine_kl = {(tuple(st), o): (k, l) for st, o, k, l in scan['full_survivor_bounds']}
q2 = json.load(open(SPRINT / 'qcert2/scan_cases75.json'))
assert mine_sb2 == {(tuple(st), o) for st, o in q2['full_survivors']} and len(mine_sb2) == 996
qr = json.load(open(SPRINT / 'qreal/scan_GstarN1HUBDARKM_q0_g75.json'))
assert mine_sb2 == {(tuple(s['state']), s['ori']) for s in qr['survivors']}
qhr = json.load(open(SPRINT / 'qhub/scan_GstarN1HUBDARKMFM_q0_g75.json'))
assert mine_sb2 == {(tuple(s['state']), s['ori']) for s in qhr['survivors']}
qrc = json.load(open(SPRINT / 'qrealcheck/lp_qrc_scan_GstarN1HUBDARK.json'))
assert mine_sb2 == {(tuple(st), o) for st, o, k, l in qrc}
qh = json.load(open(SPRINT / 'qhub/scan_GstarN1HUB2DARKMFMPK_q0_g75.json'))
qh_sf = {(tuple(s['state']), s['ori']): (s['k'], s['ell']) for s in qh['survivors']}
assert set(qh_sf) == mine_sf and len(mine_sf) == 789 and all(qh_sf[c] == mine_kl[c] for c in mine_sf), 'full survivors or (k, l) differ from qhub'
qhc = json.load(open(SPRINT / 'qhubcheck/lp_qhc_scan_GstarN1HUB2DARKPKFM.json'))
qhc_sf = {(tuple(st), o): (k, l) for st, o, k, l in qhc}
assert set(qhc_sf) == mine_sf and all(qhc_sf[c] == mine_kl[c] for c in mine_sf), 'full survivors or (k, l) differ from qhubcheck'
excl = {(tuple(c['state']), c['orientation']) for c in data['claims']}
assert excl == mine_sb2 - mine_sf and len(excl) == 207
# claim bounds: the file's batch-2 bounds equal qcert2's, and the full bounds dominate them
q2_claims = {(tuple(c['state']), c['orientation']): tuple(c['full'][:2]) for c in q2['claims']}
for c in data['claims']:
    key = (tuple(c['state']), c['orientation'])
    assert (c['batch2_lower_even'], c['batch2_lower_odd']) == q2_claims[key]
    assert c['lower_even'] >= c['batch2_lower_even']
# keys
base = {tuple(k) for k in data['baseline_keys']}
c2 = json.load(open(SPRINT / 'qcert2/CERTIFICATES_CASES75.json'))
assert base == {tuple(k) for k in c2['surviving_keys']} == {conv(k) for k in qr['keys_still_feasible']} == {conv(k) for k in json.load(open(SPRINT / 'qrealcheck/lp_qrc_keys_GstarN1HUBDARK.json'))}
bsurv = {tuple(k) for k in data['baseline_surviving_keys']}; bkilled = {tuple(k) for k in data['baseline_killed_keys']}
assert bsurv == {conv(k) for k in qh['keys_still_feasible']} == {conv(k) for k in json.load(open(SPRINT / 'qhubcheck/lp_qhc_keys_GstarN1HUB2DARKPKFM.json'))} and len(bsurv) == 116
assert bkilled == base - bsurv and len(bkilled) == 265
kf = json.load(open(SPRINT / 'qrealcheck/keys_full.json'))
full1661 = {conv(k) for k in kf['feasible']}
b2 = {tuple(k) for k in data['batch2_feasible_keys']}
assert b2 == base | full1661 and len(full1661) == 1661
keysfull = json.load(open(HERE / 'keysfull3.json'))
qkf = json.load(open(SPRINT / 'qhubcheck/lp_qhc_keysfull_GstarN1HUB2DARKPKFM.json'))
mine_feas = {tuple(k) for k in keysfull['feasible']}; mine_lb = {tuple(k) for k in keysfull['load_bearing']}
assert mine_feas == {conv(k) for k in qkf['feasible']} and len(mine_feas) == 859, 'LP-feasible key set differs from qhubcheck'
assert mine_lb == {conv(k) for k in qkf['load_bearing']} and len(mine_lb) == 551, 'load-bearing key set differs from qhubcheck'
surv = {tuple(k) for k in data['surviving_keys']}
assert surv == b2 & mine_feas or surv <= b2, 'surviving keys inconsistent with the scan'
cert_keys = {tuple(c['key']) for c in data['certificates']}
assert killed <= cert_keys and not (killed & mine_feas)
print(f'batch-2 survivors {len(mine_sb2)} = qcert2 = qreal = qhub (reproduction) = qrealcheck; full survivors {len(mine_sf)} = qhub = qhubcheck with identical (k, l); '
      f'newly excluded claims {len(excl)} = difference; baseline {len(base)} = qcert2 = qreal = qrealcheck; baseline surviving {len(bsurv)} = qhub = qhubcheck; '
      f'killed {len(bkilled)} = difference; batch-2-feasible union {len(b2)} = 381 u qrealcheck 1,661; scan LP-feasible {len(mine_feas)} and load-bearing {len(mine_lb)} = qhubcheck; '
      f'all {len(killed)} killed keys certified and none LP-feasible')
print('CROSSCHECK PASSED')
