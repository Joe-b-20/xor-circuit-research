#!/usr/bin/env python3
"""qcert4: per-case certificates for the SURVIVING batch-3-feasible keys (the keys of CERTIFICATES_CASES75_B4.json's
'surviving_keys': LP-feasible under the batch-3 system and still LP-feasible under the new one).  For each such key
the whole case tree is walked: every hub case (A = a, dark = none) and, where that is LP-feasible, every leaf (A = a,
q_D = d); each (key, case) the new system kills gets an exact integer Farkas certificate, each LP-feasible leaf is
listed as open.  Nothing here excludes a key (each has an open leaf); the file documents WHICH cases of the
surviving keys are dead.  Same system and certificate machinery as gen_certs4.py.
usage: PYTHONDONTWRITEBYTECODE=1 nice -n 8 python3 gen_partial4.py   (writes CERTIFICATES_PARTIAL75_B4.json)
"""
import sys, json, time
sys.dont_write_bytecode = True
from pathlib import Path
from collections import Counter
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen_certs4 as gen        # noqa: E402
g3 = gen.g3

t0 = time.time()
main = json.load(open(HERE / 'CERTIFICATES_CASES75_B4.json'))
surv = [tuple(k) for k in main['surviving_keys']]
certs = []; open_leaves = {}; fails = []; nlp = 0
for i, key in enumerate(surv):
    q = key[4]; ol = []
    st, ints = g3.farkas_int(key, None, None, 'all'); nlp += 1
    assert st == 'feasible', ('a surviving key with a (None, None) certificate?', key, st)
    for hc in gen.hub_cases4(q):
        st, ints = g3.farkas_int(key, hc, None); nlp += 1
        if st == 'cert': certs.append((key, hc, None, ints)); continue
        if st != 'feasible': fails.append((key, hc, None, st)); continue
        for d in range(q + 1):
            st, ints = g3.farkas_int(key, hc, d); nlp += 1
            if st == 'cert': certs.append((key, hc, d, ints))
            elif st == 'feasible': ol.append([hc[1], d])
            else: fails.append((key, hc, d, st))
    assert ol or any(f[0] == key for f in fails), ('surviving key without an open leaf', key)
    open_leaves[key] = ol
    if (i + 1) % 200 == 0: gen.log(f'  partial: {i+1}/{len(surv)} keys, {len(certs)} certificates, {nlp} Farkas LPs, {time.time()-t0:.0f}s')
out = []; max_rhs = -10 ** 9
for key, hub, dark, ints in certs:
    types, aux, A, B, names, n_pkg, n_b1, n_flat = gen.ext_system4(key, hub, dark)
    assert g3.exact_ok(ints, A, B)
    max_rhs = max(max_rhs, sum(w * b for w, b in zip(ints, B)))
    used = [names[j].split()[0] for j in range(len(names)) if ints[j] and names[j].split()[0] in gen.JOINT_NAMES]
    out.append({'key': list(key), 'kind': 'partial', 'hub': list(hub), 'A': hub[1], 'qD': dark, 'dark': dark, 'weights': ints, 'joint_rows_used': used})
nleaves = sum((k[4] + 1) ** 2 for k in surv); nopen = sum(len(v) for v in open_leaves.values())
res = {'gates': 75, 'surviving_keys': [list(k) for k in surv], 'certificates': out,
       'open_leaves': [[list(k), v] for k, v in sorted(open_leaves.items())], 'uncertified_nonfeasible': [[list(k), list(h), d, s] for k, h, d, s in fails],
       'counts': {'surviving_keys': len(surv), 'certificates': len(out), 'hub_only': sum(1 for c in out if c['dark'] is None),
                  'leaves': nleaves, 'open_leaves': nopen, 'farkas_lps': nlp, 'largest_rhs': max_rhs, 'failed': len(fails),
                  'joint_row_use': dict(Counter(r for c in out for r in c['joint_rows_used']))}}
json.dump(res, open(HERE / 'CERTIFICATES_PARTIAL75_B4.json', 'w'))
gen.log(f'partial certificates: {len(surv)} surviving keys, {len(out)} certificates ({res["counts"]["hub_only"]} for a whole hub case), '
        f'{nleaves} leaves of which {nopen} LP-feasible (open), {len(fails)} LP failures; largest rhs {max_rhs}; {nlp} Farkas LPs; {time.time()-t0:.0f}s')
