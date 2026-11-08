#!/usr/bin/env python3
"""qcert2 cross-checks (no LP):
 1. the generator's system (gen_certs2.ext_system: package certify75.system + appended batch-1, HUB and DARK rows)
    and the independent checker's hand-written system (check_cases75.right_sides / type_column / aux_columns) are
    IDENTICAL matrices (same rows in the same order, same constants, same column set in the same order, same
    coefficients) for every (key, hub, dark) of the certificate file AND for every case node (every leaf (hc, d) and
    every (hc, None)) of every killed key and every key referenced by a claim;
 2. the key and claim sets agree with the qreal / qrealcheck files: surviving keys = qreal's 381 (scan_GstarN1HUBDARKM)
    = qrealcheck's lp_qrc_keys_GstarN1HUBDARK; killed = qbound's 681 minus those; the 317 claims = qreal GstarN1
    survivors minus GstarN1HUBDARKM survivors; our full survivors (scan_cases75.json) = qreal's 996 = qrealcheck's,
    with identical (k, l) on every survivor; the batch-1 survivors = qcert's 1,313.
"""
import json, sys, time
from pathlib import Path
SPRINT = Path.home() / 'xs-campaigns/2026-11-07-sprint'
HERE = SPRINT / 'qcert2'
sys.path.insert(0, str(HERE))
import gen_certs2 as gen         # noqa: E402  (imports the package copy's certify75 / lp_regen; no LP is run here)
import check_cases75 as chk      # noqa: E402

t0 = time.time()
data = json.load(open(HERE / 'CERTIFICATES_CASES75.json'))
nodes = set()
for c in data['certificates']:
    nodes.add((tuple(c['key']), tuple(c['hub']) if c['hub'] else None, c['dark']))
keys = {tuple(k) for k in data['killed_keys']}
for claim in data['claims']:
    st, ori = tuple(claim['state']), claim['orientation']
    a, b, Y, V, ha, hb, la, lb, Sa, Sb, budget = st
    other = 'Mt' if ori == 'M' else 'M'
    for h, y, F, o, low, cap, bound in ((ha, Y, V, ori, la, Sa, claim['lower_even']), (hb, V, Y, other, lb, Sb, claim['lower_odd'])):
        for total in range(low, min(cap, bound - 1) + 1):
            for z in range(total + 1):
                keys.add((h, y, F, o, total - z, z))
for key in keys:
    q = key[4]
    nodes.add((key, None, None))
    for hc in chk.hub_cases(q):
        nodes.add((key, hc, None))
        for d in range(q + 1): nodes.add((key, hc, d))
n = 0; ncoef = 0
for key, hub, dark in sorted(nodes, key=str):
    types, aux, A, B, names, n_pkg, n_b1 = gen.ext_system(key, hub, dark)
    b2, cols, n_pkg2, n_b12 = chk.matrix(key, hub, dark)
    assert (n_pkg, n_b1) == (n_pkg2, n_b12), (key, hub, dark, n_pkg, n_b1, n_pkg2, n_b12)
    assert B == b2, ('constants differ', key, hub, dark, B, b2)
    labels = [lab for lab, _ in cols]
    assert labels == types + aux, ('column sets differ', key, hub, dark, labels[:5], (types + aux)[:5])
    for j, (lab, col) in enumerate(cols):
        gcol = [row[j] for row in A]
        assert gcol == col, ('column differs', key, hub, dark, lab, gcol, col)
        ncoef += len(col)
    n += 1
print(f'systems identical on {n} (key, case) nodes of {len(keys)} keys ({ncoef} coefficients and every row constant), {time.time()-t0:.0f}s')

# key / claim sets versus qbound, qreal and qrealcheck
conv = lambda k: (k[0], k[1], k[2], k[5], k[3], k[4])      # their key files use the order (h,y,F,q,z,ori)
qb = json.load(open(SPRINT / 'qbound/scan_GstarN1_q0_g75.json'))
qr = json.load(open(SPRINT / 'qreal/scan_GstarN1HUBDARKM_q0_g75.json'))
qrc_keys = json.load(open(SPRINT / 'qrealcheck/lp_qrc_keys_GstarN1HUBDARK.json'))
qrc_scan = json.load(open(SPRINT / 'qrealcheck/lp_qrc_scan_GstarN1HUBDARK.json'))
b1 = {conv(k) for k in qb['keys_still_feasible']}; final = {conv(k) for k in qr['keys_still_feasible']}; qrcf = {conv(k) for k in qrc_keys}
mine_b1 = {tuple(k) for k in data['batch1_feasible_keys']}; killed = {tuple(k) for k in data['killed_keys']}; surv = {tuple(k) for k in data['surviving_keys']}
assert mine_b1 == b1, (len(mine_b1), len(b1))
assert surv == final == qrcf, (len(surv), len(final), len(qrcf))
assert killed == b1 - final, (len(killed), len(b1 - final))
sb = {(tuple(s['state']), s['ori']) for s in qb['survivors']}; sf = {(tuple(s['state']), s['ori']): (s['k'], s['ell']) for s in qr['survivors']}
excl = {(tuple(c['state']), c['orientation']) for c in data['claims']}
assert excl == sb - set(sf), (len(excl), len(sb - set(sf)))
scan = json.load(open(HERE / 'scan_cases75.json'))
mine_sf = {(tuple(st), o) for st, o in scan['full_survivors']}; mine_sb = {(tuple(st), o) for st, o in scan['batch1_survivors']}
assert mine_sf == set(sf) and mine_sb == sb
qrc_sf = {(tuple(st), o): (k, l) for st, o, k, l in qrc_scan}
assert set(qrc_sf) == set(sf)
mine_kl = {(tuple(c['state']), c['orientation']): tuple(c['full'][:2]) for c in scan['claims']}
assert all(mine_kl[c] == sf[c] == qrc_sf[c] for c in sf), 'survivor bounds (k, l) differ'
qc = json.load(open(SPRINT / 'qcert/scan_ext75.json'))
assert {(tuple(st), o) for st, o in qc['ext_survivors']} == sb
cert_keys = {tuple(c['key']) for c in data['certificates']}
assert killed <= cert_keys
print(f'batch-1-feasible keys {len(b1)} = qbound; surviving {len(surv)} = qreal = qrealcheck; killed {len(killed)} = difference; '
      f'newly excluded claims {len(excl)} = qreal GstarN1 survivors minus GstarN1HUBDARKM survivors; full survivors {len(mine_sf)} identical to '
      f'qreal and qrealcheck with identical (k, l); batch-1 survivors {len(mine_sb)} identical to qcert; all killed keys certified')
print('CROSSCHECK PASSED')
