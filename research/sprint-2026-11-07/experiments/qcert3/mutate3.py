#!/usr/bin/env python3
"""qcert3: mutation tests of the independent checker (check_cases3.py) on CERTIFICATES_CASES75_B3.json.

Certificate mutations:
  negate     w_i -> -w_i   (EVERY certificate, every nonzero entry)   must always be rejected (nonnegativity)
  zero       w_i -> 0      (a random sample of SAMPLE certificates, every nonzero entry)  rejected unless the row is redundant
  plus_one   w_i -> w_i+1  (same sample)                               rejected unless the perturbed combination still works
  swap_key   the certificate checked against a neighbouring key (q+1, z+1, other orientation, h+1), same case (sample)
  swap_case  the certificate checked against a neighbouring case of the same key (dark d-1 / d+1 with the same row
             count, hub ("eq", a+-1), ("eq", 2) <-> ("le", 1)) (sample; shape changes count as rejections)
System mutations (the matrix the checker builds):
  rhs_plus   b_i -> b_i + 1 on one used row i: rejected iff the weighted right-hand side reaches 0 (sample)
  coef_flip  A[i][j] -> -A[i][j] for one used row i and one column j with A[i][j] != 0 (sample)
  fm_const   the FM7 chord constants raised by 1 (the finite fact FM weakened by one rank) on every certificate using an FM row
  pk_const   PK4 / PK5 constant + 1 on every certificate using the PK row
  hub_cap    the HUB2 column deletion weakened to Lemma H1's (u > 4 + q - a): the certificate re-checked over the
             larger column set (every certificate in a case ("eq", a))
Coverage mutations:
  drop_case  for EVERY killed key with case certificates: one of its case certificates removed -> coverage must fail
  drop_cert  for every claim: one referenced certificate of one referenced key removed -> verify must fail
  k_minus / l_minus / k_plus  claim bounds moved by one: rejected iff the final test fails / a new key is referenced
For every survivor of 'zero' and 'plus_one' the mutated vector is re-verified as a genuine certificate (no false
acceptance).  usage: python3 mutate3.py [seed] [SAMPLE]
"""
import json, random, sys, time
from pathlib import Path
import check_cases3 as chk

HERE = Path(__file__).parent
data = json.loads((HERE / 'CERTIFICATES_CASES75_B3.json').read_text())
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
SAMPLE = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 9
rng = random.Random(seed)
stats = {}
def rec(name, rejected):
    a = stats.setdefault(name, [0, 0]); a[0] += 1; a[1] += int(rejected)
def rejects(fn):
    try:
        fn(); return False
    except AssertionError:
        return True

t0 = time.time()
certs = data['certificates']
def case_of(e): return (tuple(e['hub']) if e.get('hub') else None, e.get('dark'))
for e in certs:
    w = e['weights']
    for i in [i for i, v in enumerate(w) if v]:
        m = list(w); m[i] = -m[i]
        rec('negate', rejects(lambda: chk.check_weights(m, [0] * len(m), [])))   # the sign test alone is decisive
sample = rng.sample(certs, min(SAMPLE, len(certs)))
for e in sample:
    key = tuple(e['key']); hub, dark = case_of(e); w = e['weights']
    b, cols, n_pkg, n_b1, n_flat = chk.matrix(key, hub, dark)
    nz = [i for i, v in enumerate(w) if v]
    for i in nz:
        m = list(w); m[i] = 0
        rj = rejects(lambda: chk.check_weights(m, b, cols)); rec('zero', rj)
        if not rj: rec('zero_survivor_is_valid_certificate', not rejects(lambda: chk.check_certificate(key, hub, dark, m)))
        m = list(w); m[i] += 1
        rj = rejects(lambda: chk.check_weights(m, b, cols)); rec('plus_one', rj)
        if not rj: rec('plus_one_survivor_is_valid_certificate', not rejects(lambda: chk.check_certificate(key, hub, dark, m)))
    h, y, F, ori, q, z = key
    for nk in ((h, y, F, ori, q + 1, z), (h, y, F, ori, q, z + 1), (h, y, F, 'Mt' if ori == 'M' else 'M', q, z), (h + 1, y, F, ori, q, z)):
        if hub is not None and not chk.legal_case(nk, hub, dark): continue
        rec('swap_key', rejects(lambda: chk.check_certificate(nk, hub, dark, w)))
    neigh = []
    if dark is not None:
        for d2 in (dark - 1, dark + 1):
            if 0 < d2 < q and 0 < dark < q: neigh.append((hub, d2))        # same row count (no Fb = 0 / Fd = 0 row)
    if hub is not None and hub[0] == 'eq':
        for a2 in (hub[1] - 1, hub[1] + 1):
            if 2 <= a2 <= q: neigh.append((('eq', a2), dark))
        if hub[1] == 2: neigh.append((('le', 1), dark))
    if hub is not None and hub[0] == 'le': neigh.append((('eq', 2), dark))
    for hub2, dark2 in neigh:
        rec('swap_case', rejects(lambda: chk.check_certificate(key, hub2, dark2, w)))
    i = rng.choice(nz)
    b2 = list(b); b2[i] += 1
    rec('rhs_plus', rejects(lambda: chk.check_weights(w, b2, cols)))
    cand = [j for j, (lab, col) in enumerate(cols) if col[i] != 0]
    if cand:
        j = rng.choice(cand); cols2 = [(lab, list(col)) for lab, col in cols]; cols2[j][1][i] = -cols2[j][1][i]
        rec('coef_flip', rejects(lambda: chk.check_weights(w, b, cols2)))
    # finite-fact mutations: FM constants + 1 on the FM rows the certificate uses; PK constant + 1; HUB2 deletion weakened to H1's
    fm_start = n_pkg + n_b1 + (1 if q in (4, 5) else 0); fm_rows = [i for i in range(fm_start, n_pkg + n_b1 + n_flat) if w[i]]
    if fm_rows:
        b3 = list(b)
        for i in fm_rows:
            if (i - fm_start) % 2 == 0: b3[i] += 1          # FM7 chords only (FM9 chords coincide with L9)
        if b3 != b: rec('fm_const', rejects(lambda: chk.check_weights(w, b3, cols)))
    if q in (4, 5) and w[n_pkg + n_b1]:
        b4 = list(b); b4[n_pkg + n_b1] += 1
        rec('pk_const', rejects(lambda: chk.check_weights(w, b4, cols)))
    if hub is not None and hub[0] == 'eq':
        a = hub[1]
        extra = [(r, u, v) for r in range(3) for u in range(q + 1) for v in range(min(2 * z, max(0, h - 1)) + 1)
                 if r + u + v >= 3 and chk.KR[r] + q - a < u <= 4 + q - a]
        if extra:
            cols5 = cols + [((r, u, v), chk.type_column(key, hub, dark, r, u, v)) for r, u, v in extra]
            rec('hub_cap', rejects(lambda: chk.check_weights(w, b, cols5)))
print(f'certificate mutations done, {time.time()-t0:.0f}s', flush=True)

# ---- coverage mutations
base = chk.verify(data, quiet=True); assert base['all_checks_passed']
by_key = {}
for n, e in enumerate(certs): by_key.setdefault(tuple(e['key']), []).append(n)
index = {key: {case_of(certs[n]) for n in idx} for key, idx in by_key.items()}      # the verified certificate index
killed = [tuple(k) for k in data['killed_keys']]
for key in killed:
    idx = by_key[key]
    if len(idx) == 1 and case_of(certs[idx[0]]) == (None, None): continue
    drop = rng.choice(idx)
    cases = {case_of(certs[n]) for n in idx if n != drop}
    rec('drop_case', not chk.covered(cases, key[4]))
for claim in data['claims']:
    st, ori = tuple(claim['state']), claim['orientation']
    a, b, Y, V, ha, hb, la, lb, Sa, Sb, budget = st
    k, l = claim['lower_even'], claim['lower_odd']
    other = 'Mt' if ori == 'M' else 'M'
    refs = []
    for h, y, F, o, low, cap, bound in ((ha, Y, V, ori, la, Sa, k), (hb, V, Y, other, lb, Sb, l)):
        for total in range(low, min(cap, bound - 1) + 1):
            for z in range(total + 1):
                qq = total - z
                if 2 * h + y + z + chk.c2(qq) < 32: continue
                kk = (h, y, F, o, qq, z)
                if chk.geometric_exclusion(kk): continue
                refs.append(kk)
    if refs:
        kk = rng.choice(refs); drop = rng.choice(by_key[kk])
        index2 = dict(index); index2[kk] = {case_of(certs[n]) for n in by_key[kk] if n != drop}
        rec('drop_cert', rejects(lambda: chk.claims_check([claim], index2)))
    for name, dk, dl in (('k_minus', -1, 0), ('l_minus', 0, -1), ('k_plus', 1, 0)):
        c2_ = dict(claim); c2_['lower_even'] = k + dk; c2_['lower_odd'] = l + dl
        rec(name, rejects(lambda: chk.claims_check([c2_], index)))

print('mutation test results (mutations, rejected, rate):')
for name, (n, r) in stats.items():
    print(f'  {name:40s} {n:8d} {r:8d}  {100.0*r/n:6.2f}%')
guaranteed = ['negate', 'drop_case', 'drop_cert']
ok = all(stats[g][0] == stats[g][1] for g in guaranteed if g in stats)
for s in ('zero_survivor_is_valid_certificate', 'plus_one_survivor_is_valid_certificate'):
    if s in stats: ok = ok and stats[s][0] == stats[s][1]
json.dump({'seed': seed, 'sample': len(sample), 'stats': {k: {'mutations': v[0], 'rejected': v[1]} for k, v in stats.items()}, 'seconds': time.time() - t0},
          open(HERE / 'mutate3.json', 'w'), indent=1)
print('MUTATION TEST', 'PASSED' if ok else 'FAILED', f'({time.time()-t0:.0f}s; every negated weight, every dropped case certificate and every dropped referenced certificate was rejected; every surviving zeroing / +1 is itself a valid certificate)' if ok else '')
sys.exit(0 if ok else 1)
