#!/usr/bin/env python3
"""qcert cross-checks (no LP):
 1. the generator's system (gen_certs.ext_system: package certify75.system + appended rows) and the independent
    checker's hand-written system (check_ext75.right_sides / type_column / aux_columns) are IDENTICAL matrices
    (same rows in the same order, same constants, same column coefficients) for every key in the certificate file
    and for every key touched by the coverage of the 195 claims;
 2. the key sets agree with the qbound / qcheck files: killed keys = baseline-feasible minus
    scan_GstarN1 keys_still_feasible (453); newly excluded claims = base survivors minus GstarN1 survivors (195);
    the extended survivors of scan_ext75.json equal qbound's and qcheck's 1,313.
"""
import json, sys
from pathlib import Path
SPRINT = Path.home() / 'xs-campaigns/2026-11-07-sprint'
HERE = SPRINT / 'qcert'
sys.path.insert(0, str(HERE))
import gen_certs as gen          # noqa: E402  (imports the package copy's certify75/lp_regen; no LP is run here)
import check_ext75 as chk        # noqa: E402

data = json.load(open(HERE / 'CERTIFICATES_EXT75.json'))
keys = {tuple(c['key']) for c in data['certificates']}
# all keys the coverage of the claims touches (certified, direct or (4.4)-excluded)
for claim in data['claims']:
    st, ori = tuple(claim['state']), claim['orientation']
    a, b, Y, V, ha, hb, la, lb, Sa, Sb, budget = st
    other = 'Mt' if ori == 'M' else 'M'
    for h, y, F, o, low, cap, bound in ((ha, Y, V, ori, la, Sa, claim['lower_even']), (hb, V, Y, other, lb, Sb, claim['lower_odd'])):
        for total in range(low, min(cap, bound - 1) + 1):
            for z in range(total + 1):
                keys.add((h, y, F, o, total - z, z))
n = 0
for key in sorted(keys):
    types, A, B, names = gen.ext_system(key, True)
    b2, n_pkg = chk.right_sides(key)
    assert B == b2, ('constants differ', key, B, b2)
    cols = [chk.type_column(key, r, u, v) for r, u, v in types] + chk.aux_columns(key, n_pkg)
    assert len(cols) == len(A[0]), key
    for j, col in enumerate(cols):
        gcol = [row[j] for row in A]
        assert gcol == col, ('column differs', key, j, types[j] if j < len(types) else ('y0', 'y1', 'y2')[j - len(types)], gcol, col)
    n += 1
print(f'systems identical on {n} keys (every row constant and every column coefficient)')

# key / claim sets versus qbound and qcheck
qb_base = json.load(open(SPRINT / 'qbound/scan_base_q0_g75.json')); qb_ext = json.load(open(SPRINT / 'qbound/scan_GstarN1_q0_g75.json'))
conv = lambda k: (k[0], k[1], k[2], k[5], k[3], k[4])      # qbound / qcheck key files use the order (h,y,F,q,z,ori)
kb = {conv(k) for k in qb_base['keys_still_feasible']}; ke = {conv(k) for k in qb_ext['keys_still_feasible']}
killed_ref = kb - ke
killed = {tuple(k) for k in data['killed_keys']}
assert killed == killed_ref, (len(killed), len(killed_ref))
sb = {(tuple(s['state']), s['ori']) for s in qb_base['survivors']}; se = {(tuple(s['state']), s['ori']) for s in qb_ext['survivors']}
excl = {(tuple(c['state']), c['orientation']) for c in data['claims']}
assert excl == sb - se, (len(excl), len(sb - se))
scan = json.load(open(HERE / 'scan_ext75.json'))
mine_se = {(tuple(st), o) for st, o in scan['ext_survivors']}; mine_sb = {(tuple(st), o) for st, o in scan['base_survivors']}
assert mine_se == se and mine_sb == sb
qc = {(tuple(st), o) for st, o, k, l in json.load(open(SPRINT / 'qcheck/lp_indep_scan_GstarN1.json'))}
assert qc == se
qc_keys = {conv(k) for k in json.load(open(SPRINT / 'qcheck/lp_indep_keys_GstarN1.json'))}
assert qc_keys == ke
cert_keys = {tuple(c['key']) for c in data['certificates']}
assert killed <= cert_keys
print(f'killed keys {len(killed)} = qbound base minus GstarN1 feasible keys; newly excluded claims {len(excl)} = base survivors minus GstarN1 survivors; '
      f'extended survivors {len(mine_se)} identical to qbound and qcheck; all killed keys certified')
print('CROSSCHECK PASSED')
