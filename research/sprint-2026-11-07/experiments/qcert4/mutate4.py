#!/usr/bin/env python3
"""qcert4: mutation tests of the independent checker (check_cases4.py) on CERTIFICATES_CASES75_B4.json.

Certificate mutations (every certificate unless SAMPLE is given):
  negate      w_i -> -w_i on every nonzero entry                       must always be rejected (nonnegativity)
  zero        w_i -> 0 on every nonzero entry                          rejected unless the row is redundant (survivors re-verified)
  plus_one    w_i -> w_i + 1 on every nonzero entry                    rejected unless the combination still works (survivors re-verified)
  swap_key    the certificate against a neighbouring key (q+1, z+1, other orientation, h+1), same case
  swap_case   the certificate against a neighbouring case of the same key (A = a +- 1; q_D = d +- 1 with the same row count)
  rhs_plus / coef_flip   one used row's constant + 1 / one used coefficient's sign flipped
Mutations of the NEW rows (every certificate in a hub case that uses the row):
  joint_const_<row>  that joint row's constant + 1 (e.g. LIM: two limit hubs allowed when a < q, i.e. J1 / Lemma 4.6 dropped)
  joint_drop_<row>   that joint row deleted (its multiplier zeroed): rejected iff the certificate rests on it
  pk_bound           the packing constants Pk(a), Pk(q-a) of P4 replaced by the Johnson bound without the parity step
  h2_widen           the m-interval upper end widened from min(u, 3-r) to min(u, 4-r) (finite fact H2 weakened to H1's
                     capacity) in the joint rows: coefficients recomputed (columns kept as the case's)
  exact_split        a certificate of case A = 0 or A = 1 checked in the merged case "A <= 1" of batch 3 (joint rows of
                     the case removed): rejected iff it needs the exact split or a joint row
Coverage mutations:
  drop_case   for EVERY killed key with case certificates: one case certificate removed -> coverage must fail
  drop_cert   for every claim: one referenced certificate removed -> verify must fail
  k_minus / l_minus / k_plus  claim bounds moved by one
usage: python3 mutate4.py [seed] [SAMPLE]
"""
import json, random, sys, time
sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_cases4 as chk      # noqa: E402
c3 = chk.c3

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / 'CERTIFICATES_CASES75_B4.json').read_text())
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
        rec('negate', rejects(lambda: c3.check_weights(m, [0] * len(m), [])))
sample = rng.sample(certs, min(SAMPLE, len(certs)))
for e in sample:
    key = tuple(e['key']); hub, dark = case_of(e); w = e['weights']
    h, y, F, ori, q, z = key
    b, cols, n_pkg, n_b1, n_flat = chk.matrix(key, hub, dark)
    nz = [i for i, v in enumerate(w) if v]
    for i in nz:
        m = list(w); m[i] = 0
        rj = rejects(lambda: c3.check_weights(m, b, cols)); rec('zero', rj)
        if not rj: rec('zero_survivor_is_valid_certificate', not rejects(lambda: chk.check_certificate(key, hub, dark, m)))
        m = list(w); m[i] += 1
        rj = rejects(lambda: c3.check_weights(m, b, cols)); rec('plus_one', rj)
        if not rj: rec('plus_one_survivor_is_valid_certificate', not rejects(lambda: chk.check_certificate(key, hub, dark, m)))
    for nk in ((h, y, F, ori, q + 1, z), (h, y, F, ori, q, z + 1), (h, y, F, 'Mt' if ori == 'M' else 'M', q, z), (h + 1, y, F, ori, q, z)):
        if not chk.legal_case(nk, hub, dark): continue
        rec('swap_key', rejects(lambda: chk.check_certificate(nk, hub, dark, w)))
    neigh = []
    if dark is not None:
        for d2 in (dark - 1, dark + 1):
            if 0 < d2 < q and 0 < dark < q: neigh.append((hub, d2))
    if hub is not None:
        for a2 in (hub[1] - 1, hub[1] + 1):
            if 0 <= a2 <= q and (a2 == q) == (hub[1] == q): neigh.append((('eq', a2), dark))   # same LIM row shape
    for hub2, dark2 in neigh:
        rec('swap_case', rejects(lambda: chk.check_certificate(key, hub2, dark2, w)))
    i = rng.choice(nz)
    b2 = list(b); b2[i] += 1
    rec('rhs_plus', rejects(lambda: c3.check_weights(w, b2, cols)))
    cand = [j for j, (lab, col) in enumerate(cols) if col[i] != 0]
    if cand:
        j = rng.choice(cand); cols2 = [(lab, list(col)) for lab, col in cols]; cols2[j][1][i] = -cols2[j][1][i]
        rec('coef_flip', rejects(lambda: c3.check_weights(w, b, cols2)))
    if hub is None: continue
    a = hub[1]; nrows = len(b); j0 = nrows - chk.NJ
    for t, name in enumerate(chk.JOINT):
        if not w[j0 + t]: continue
        b3 = list(b); b3[j0 + t] += 1
        rec(f'joint_const_{name}', rejects(lambda: c3.check_weights(w, b3, cols)))
        m = list(w); m[j0 + t] = 0
        rec(f'joint_drop_{name}', rejects(lambda: c3.check_weights(m, b, cols)))
    if w[j0 + 3] or w[j0 + 4]:
        jb = lambda x: 0 if x < 3 else (x * ((x - 1) // 2)) // 3
        b4 = list(b); b4[j0 + 3] = jb(a); b4[j0 + 4] = jb(q - a)
        if b4 != b: rec('pk_bound', rejects(lambda: c3.check_weights(w, b4, cols)))
    if any(w[j0:]):
        def widened(lab, col):
            if not isinstance(lab, tuple) or lab[0] == 3: return col
            r, u, v = lab
            I = range(max(0, u - (q - a)), min(u, 4 - r) + 1)
            jc = [min(c3.c2(mm) for mm in I), min(mm * (u - mm) for mm in I), min(c3.c2(u - mm) for mm in I),
                  min(int(mm >= 3) for mm in I), min(int(u - mm >= 3) for mm in I), min(r * mm for mm in I), col[j0 + 6]]
            return col[:j0] + jc
        cols6 = [(lab, widened(lab, col)) for lab, col in cols]
        if cols6 != cols: rec('h2_widen', rejects(lambda: c3.check_weights(w, b, cols6)))
    if a <= 1 and q >= 2:
        # merged batch-3 case "A <= 1": rows A <= 1 in place of A = a, no joint rows, same columns (none deleted for a <= 1)
        bb, cc, _, _, _ = c3.matrix(key, ('le', 1), dark)
        hub_pos = n_pkg + n_b1 + n_flat
        wl = w[:hub_pos] + [w[hub_pos]] + w[hub_pos + 2:j0]      # keep the multiplier of A <= a as A <= 1; drop A >= a and the joint rows
        rec('exact_split', rejects(lambda: c3.check_weights(wl, bb, cc)))
print(f'certificate mutations done, {time.time()-t0:.0f}s', flush=True)

base = chk.verify(data, quiet=True); assert base['all_checks_passed']
by_key = {}
for n, e in enumerate(certs): by_key.setdefault(tuple(e['key']), []).append(n)
index = {key: {case_of(certs[n]) for n in idx} for key, idx in by_key.items()}
for key in [tuple(k) for k in data['killed_keys']]:
    idx = by_key[key]
    if len(idx) == 1 and case_of(certs[idx[0]]) == (None, None): continue
    drop = rng.choice(idx)
    rec('drop_case', not chk.covered({case_of(certs[n]) for n in idx if n != drop}, key[4]))
for claim in data['claims']:
    st, ori = tuple(claim['state']), claim['orientation']
    a_, b_, Y, V, ha, hb, la, lb, Sa, Sb, budget = st
    k, l = claim['lower_even'], claim['lower_odd']
    other = 'Mt' if ori == 'M' else 'M'
    refs = []
    for h, y, F, o, low, cap, bound in ((ha, Y, V, ori, la, Sa, k), (hb, V, Y, other, lb, Sb, l)):
        for total in range(low, min(cap, bound - 1) + 1):
            for z in range(total + 1):
                qq = total - z
                if 2 * h + y + z + c3.c2(qq) < 32: continue
                kk = (h, y, F, o, qq, z)
                if c3.geometric_exclusion(kk): continue
                refs.append(kk)
    if refs:
        kk = rng.choice(refs); drop = rng.choice(by_key[kk])
        index2 = dict(index); index2[kk] = {case_of(certs[n]) for n in by_key[kk] if n != drop}
        rec('drop_cert', rejects(lambda: chk.claims_check([claim], index2)))
    for name, dk, dl in (('k_minus', -1, 0), ('l_minus', 0, -1), ('k_plus', 1, 0)):
        cc_ = dict(claim); cc_['lower_even'] = k + dk; cc_['lower_odd'] = l + dl
        rec(name, rejects(lambda: chk.claims_check([cc_], index)))

print('mutation test results (mutations, rejected, rate):')
for name, (n, r) in stats.items():
    print(f'  {name:40s} {n:8d} {r:8d}  {100.0*r/n:6.2f}%')
guaranteed = ['negate', 'drop_case', 'drop_cert']
ok = all(stats[g][0] == stats[g][1] for g in guaranteed if g in stats)
for s in ('zero_survivor_is_valid_certificate', 'plus_one_survivor_is_valid_certificate'):
    if s in stats: ok = ok and stats[s][0] == stats[s][1]
json.dump({'seed': seed, 'sample': len(sample), 'stats': {k: {'mutations': v[0], 'rejected': v[1]} for k, v in stats.items()}, 'seconds': time.time() - t0},
          open(HERE / 'mutate4.json', 'w'), indent=1)
print('MUTATION TEST', 'PASSED' if ok else 'FAILED', f'({time.time()-t0:.0f}s)')
sys.exit(0 if ok else 1)
