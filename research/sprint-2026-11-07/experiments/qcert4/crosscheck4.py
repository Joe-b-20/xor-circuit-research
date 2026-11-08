#!/usr/bin/env python3
"""qcert4 cross-checks (no LP):
 1. the generator's system (gen_certs4.ext_system4 = gen_certs3.ext_system + the closed-form joint rows) and the
    independent checker's system (check_cases4.matrix = check_cases3's hand-written rows + the brute-force joint rows)
    are IDENTICAL matrices (rows, order, constants, column set, coefficients) on every case node of every killed key
    and of every key carrying a case certificate: (None, None), every (('eq', a), None), every leaf (('eq', a), d) and
    every (None, d);
 2. key and claim sets: batch-3 survivors 789 = qcert3 = qhubcheck; new survivors 686 with identical (k, l) = qjoint
    (qj_lp.py JOINTLIM) = qjointcheck (verbatim recount JOINTLIM and own rows JCLIM); the 103 claims = the difference;
    the scan's LP-feasible (814) and load-bearing (483) keys = qjoint = qjointcheck (both variants); of qcert3's 551
    load-bearing keys the 388 still feasible = qjoint / qjointcheck (JOINTLIM, JCLIM) and, without LIM, the 452 = qjoint /
    qjointcheck (JOINT, JC); the batch-3 bounds in the certificate file = qcert3's; every killed key certified.
"""
import json, sys, time
sys.dont_write_bytecode = True
from pathlib import Path
SPRINT = Path.home() / 'xs-campaigns/2026-11-07-sprint'
HERE = SPRINT / 'qcert4'
sys.path.insert(0, str(HERE))
import gen_certs4 as gen        # noqa: E402  (imports the package copy through gen_certs3_copy; no LP is run here)
import check_cases4 as chk      # noqa: E402

t0 = time.time()
data = json.load(open(HERE / 'CERTIFICATES_CASES75_B4.json'))
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
    types, aux, A, B, names, n_pkg, n_b1, n_flat = gen.ext_system4(key, hub, dark)
    b2, cols, n_pkg2, n_b12, n_flat2 = chk.matrix(key, hub, dark)
    assert (n_pkg, n_b1, n_flat) == (n_pkg2, n_b12, n_flat2), (key, hub, dark)
    assert B == b2, ('constants differ', key, hub, dark, [(i, x, y) for i, (x, y) in enumerate(zip(B, b2)) if x != y][:5], len(B), len(b2))
    labels = [lab for lab, _ in cols]
    assert labels == types + aux, ('column sets differ', key, hub, dark)
    for j, (lab, col) in enumerate(cols):
        gcol = [row[j] for row in A]
        assert gcol == col, ('column differs', key, hub, dark, lab, [(i, names[i], x, y) for i, (x, y) in enumerate(zip(gcol, col)) if x != y])
        ncoef += len(col)
    n += 1
    if n % 20000 == 0: print(f'  {n} nodes, {time.time()-t0:.0f}s', flush=True)
print(f'systems identical on {n} (key, case) nodes of {len(killed | case_keys)} keys ({ncoef} coefficients and every row constant), {time.time()-t0:.0f}s', flush=True)

conv = lambda k: (k[0], k[1], k[2], k[5], k[3], k[4])      # their key files use the order (h,y,F,q,z,ori)
scan = json.load(open(HERE / 'scan_cases4.json'))
sb3 = {(tuple(st), o) for st, o in scan['batch3_survivors']}; sf = {(tuple(st), o) for st, o in scan['new_survivors']}
kl = {(tuple(st), o): (k, l) for st, o, k, l in scan['new_survivor_bounds']}
s3 = json.load(open(SPRINT / 'qcert3/scan_cases3.json'))
assert sb3 == {(tuple(st), o) for st, o in s3['full_survivors']} and len(sb3) == 789
qhc = json.load(open(SPRINT / 'qhubcheck/lp_qhc_scan_GstarN1HUB2DARKPKFM.json'))
assert sb3 == {(tuple(st), o) for st, o, k, l in qhc}
refs = {'qjoint JOINTLIM': SPRINT / 'qjoint/lp_qhc_scan_GstarN1HUB2DARKPKFMJOINTLIM.json',
        'qjointcheck JOINTLIM (recount)': SPRINT / 'qjointcheck/lp_qhc_scan_GstarN1HUB2DARKPKFMJOINTLIM.json',
        'qjointcheck JCLIM (own rows)': SPRINT / 'qjointcheck/lp_qhc_scan_GstarN1HUB2DARKPKFMJCLIM.json'}
for name, p in refs.items():
    r = {(tuple(st), o): (k, l) for st, o, k, l in json.load(open(p))}
    assert set(r) == sf and all(r[c] == kl[c] for c in sf), ('new survivors or (k, l) differ', name)
assert len(sf) == 686
excl = {(tuple(c['state']), c['orientation']) for c in data['claims']}
assert excl == sb3 - sf and len(excl) == 103
b3c = {(tuple(c['state']), c['orientation']): tuple(c['full'][:2]) for c in s3['claims']}
for c in data['claims']:
    key = (tuple(c['state']), c['orientation'])
    assert (c['batch3_lower_even'], c['batch3_lower_odd']) == b3c[key]
    assert c['lower_even'] >= c['batch3_lower_even']
kf = json.load(open(HERE / 'keysfull4.json'))
feas = {tuple(k) for k in kf['feasible']}; lbn = {tuple(k) for k in kf['load_bearing']}
for name, p in (('qjoint', SPRINT / 'qjoint/lp_qhc_keysfull_GstarN1HUB2DARKPKFMJOINTLIM.json'),
                ('qjointcheck JOINTLIM', SPRINT / 'qjointcheck/lp_qhc_keysfull_GstarN1HUB2DARKPKFMJOINTLIM.json'),
                ('qjointcheck JCLIM', SPRINT / 'qjointcheck/lp_qhc_keysfull_GstarN1HUB2DARKPKFMJCLIM.json')):
    r = json.load(open(p))
    assert feas == {conv(k) for k in r['feasible']} and lbn == {conv(k) for k in r['load_bearing']}, ('key sets differ', name)
assert len(feas) == 814 and len(lbn) == 483
lb388 = {tuple(k) for k in kf['lb551_still_feasible']}; lb452 = {tuple(k) for k in kf['lb551_still_feasible_without_LIM']}
for name, p, mine in (('qjoint JOINTLIM', 'qjoint/lp_qhc_keys_GstarN1HUB2DARKPKFMJOINTLIM.json', lb388),
                      ('qjointcheck JOINTLIM', 'qjointcheck/lp_qhc_keys_GstarN1HUB2DARKPKFMJOINTLIM.json', lb388),
                      ('qjointcheck JCLIM', 'qjointcheck/lp_qhc_keys_GstarN1HUB2DARKPKFMJCLIM.json', lb388),
                      ('qjoint JOINT', 'qjoint/lp_qhc_keys_GstarN1HUB2DARKPKFMJOINT.json', lb452),
                      ('qjointcheck JOINT', 'qjointcheck/lp_qhc_keys_GstarN1HUB2DARKPKFMJOINT.json', lb452),
                      ('qjointcheck JC', 'qjointcheck/lp_qhc_keys_GstarN1HUB2DARKPKFMJC.json', lb452)):
    assert mine == {conv(tuple(k)) for k in json.load(open(SPRINT / p))}, ('load-bearing recount differs', name)
assert len(lb388) == 388 and len(lb452) == 452
b3 = {tuple(k) for k in data['batch3_feasible_keys']}
kf3 = json.load(open(SPRINT / 'qcert3/keysfull3.json')); c3f = json.load(open(SPRINT / 'qcert3/CERTIFICATES_CASES75_B3.json'))
files = {tuple(k) for k in kf3['feasible']} | {tuple(k) for k in c3f['surviving_keys']}
extra = {tuple(k) for k in data['batch3_feasible_extra_keys']}
assert b3 == files | extra and not (files & extra) and len(files) == 1437
assert feas <= b3, 'a key LP-feasible under the new system is missing from the batch-3-feasible set'
lb551 = {tuple(k) for k in kf3['load_bearing']}
assert lb551 - lb388 <= killed and not (killed & feas) and {tuple(k) for k in data['surviving_keys']} >= feas
cert_keys = {tuple(c['key']) for c in data['certificates']}
assert killed <= cert_keys
print(f'batch-3 survivors {len(sb3)} = qcert3 = qhubcheck; new survivors {len(sf)} = qjoint = qjointcheck (recount, own rows) with identical (k, l); '
      f'newly excluded {len(excl)} = difference; scan LP-feasible {len(feas)} / load-bearing {len(lbn)} = qjoint = qjointcheck (both); '
      f'of the 551 load-bearing: {len(lb388)} feasible with LIM, {len(lb452)} without = qjoint = qjointcheck; batch-3-feasible union {len(b3)}; '
      f'all {len(killed)} killed keys certified, none LP-feasible; the {len(lb551 - lb388)} load-bearing keys killed are among them')
print('CROSSCHECK PASSED')
