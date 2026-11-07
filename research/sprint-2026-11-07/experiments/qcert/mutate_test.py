#!/usr/bin/env python3
"""qcert: mutation tests of the independent checker (check_ext75.py) on CERTIFICATES_EXT75.json.

Certificate mutations (every certificate, every nonzero entry unless stated):
  negate     w_i -> -w_i                 must always be rejected (nonnegativity)
  zero       w_i -> 0                    rejected unless the row is redundant for this certificate
  plus_one   w_i -> w_i + 1              rejected unless the perturbed combination still works
  swap_key   the certificate is checked against a neighbouring key (q+1 / z+1 / other orientation)
Row-constant mutation (the system seen by the checker):
  rhs_plus   b_i -> b_i + 1 for one used row i: rejected iff it pushes the weighted right-hand side to >= 0
Coefficient-flip mutation (the system seen by the checker):
  coef_flip  A[i][j] -> -A[i][j] for one used row i and one column j with A[i][j] != 0
Claim / coverage mutations (every claim):
  drop_cert  one referenced certificate is removed from the file: must always be rejected (uncovered key)
  k_minus    lower_even -> lower_even - 1 (and lower_odd -> lower_odd - 1): rejected iff the final test fails
  k_plus     lower_even -> lower_even + 1: rejected iff a newly referenced key has no certificate
Mutations that are not guaranteed to be rejected are reported with their rejection rate; for every survivor of
'zero' and 'plus_one' the mutated vector is re-verified as a genuine certificate (so no false acceptance).
usage: python3 mutate_test.py [seed]
"""
import json, random, sys, copy
from pathlib import Path
import check_ext75 as chk

HERE = Path(__file__).parent
data = json.loads((HERE / 'CERTIFICATES_EXT75.json').read_text())
rng = random.Random(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
stats = {}
def rec(name, rejected):
    a = stats.setdefault(name, [0, 0]); a[0] += 1; a[1] += int(rejected)

def rejects(fn):
    try:
        fn(); return False
    except AssertionError:
        return True

certs = data['certificates']
for entry in certs:
    key = tuple(entry['key']); w = entry['weights']
    nz = [i for i, v in enumerate(w) if v]
    for i in nz:
        m = list(w); m[i] = -m[i]; rec('negate', rejects(lambda: chk.check_certificate(key, m)))
        m = list(w); m[i] = 0
        rj = rejects(lambda: chk.check_certificate(key, m)); rec('zero', rj)
        if not rj: rec('zero_survivor_is_valid_certificate', not rejects(lambda: chk.check_certificate(key, m)))
        m = list(w); m[i] += 1
        rj = rejects(lambda: chk.check_certificate(key, m)); rec('plus_one', rj)
    # key swaps (shape may differ: a length mismatch is also a rejection)
    h, y, F, ori, q, z = key
    for nk in ((h, y, F, ori, q + 1, z), (h, y, F, ori, q, z + 1), (h, y, F, 'Mt' if ori == 'M' else 'M', q, z), (h + 1, y, F, ori, q, z)):
        rec('swap_key', rejects(lambda: chk.check_certificate(nk, w)))
    # row-constant +1 and coefficient flip on one used row, through a monkeypatched checker
    i = rng.choice(nz)
    orig_rs = chk.right_sides
    def mutated_rs(k, _i=i, _o=orig_rs):
        b, n = _o(k); b = list(b); b[_i] += 1; return b, n
    chk.right_sides = mutated_rs
    rec('rhs_plus', rejects(lambda: chk.check_certificate(key, w)))
    chk.right_sides = orig_rs
    # coefficient flip: pick a column (a type or y-column) where row i has a nonzero coefficient
    types = [(r, u, v) for r in range(4) for u in range(q + 1) for v in range(min(2 * z, max(0, h - 1)) + 1) if r + u + v >= 3]
    cand = [t for t in types if chk.type_column(key, *t)[i] != 0]
    if cand:
        t = rng.choice(cand); orig_tc = chk.type_column
        def mutated_tc(k, r, u, v, _t=t, _i=i, _o=orig_tc):
            c = list(_o(k, r, u, v))
            if (r, u, v) == _t: c[_i] = -c[_i]
            return c
        chk.type_column = mutated_tc
        rec('coef_flip', rejects(lambda: chk.check_certificate(key, w)))
        chk.type_column = orig_tc

# claim-level mutations
base = chk.verify(data, quiet=True)
assert base['all_checks_passed']
cert_index = {tuple(c['key']): n for n, c in enumerate(certs)}
for ci, claim in enumerate(data['claims']):
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
        kk = rng.choice(refs)
        d2 = {'gates': data['gates'], 'claims': [claim], 'certificates': [c for n, c in enumerate(certs) if n != cert_index[kk]]}
        rec('drop_cert', rejects(lambda: chk.verify(d2, quiet=True)))
    for name, dk, dl in (('k_minus', -1, 0), ('l_minus', 0, -1), ('k_plus', 1, 0)):
        c2_ = dict(claim); c2_['lower_even'] = k + dk; c2_['lower_odd'] = l + dl
        d2 = {'gates': data['gates'], 'claims': [c2_], 'certificates': certs}
        rec(name, rejects(lambda: chk.verify(d2, quiet=True)))

print('mutation test results (mutations, rejected, rate):')
for name, (n, r) in stats.items():
    print(f'  {name:40s} {n:7d} {r:7d}  {100.0*r/n:6.2f}%')
guaranteed = ['negate', 'drop_cert']
ok = all(stats[g][0] == stats[g][1] for g in guaranteed if g in stats) and stats.get('zero_survivor_is_valid_certificate', [0, 0])[0] == stats.get('zero_survivor_is_valid_certificate', [0, 0])[1]
json.dump({k: {'mutations': v[0], 'rejected': v[1]} for k, v in stats.items()}, open(HERE / 'mutate_test.json', 'w'), indent=1)
print('MUTATION TEST', 'PASSED' if ok else 'FAILED', '(every negated weight and every dropped referenced certificate was rejected; every surviving zeroing is itself a valid certificate)' if ok else '')
sys.exit(0 if ok else 1)
