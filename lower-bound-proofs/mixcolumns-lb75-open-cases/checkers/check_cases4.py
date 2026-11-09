#!/usr/bin/env python3
"""qcert4: INDEPENDENT checker for CERTIFICATES_CASES75_B4.json (G = 75): per-case Farkas certificates for the batch-3
local systems with the exact integer hub split A = a (a = 0..q, every q) and, in each hub case, the rows of Lemma P
(P1-P5) and row LIM (PROOF_ADDENDUM_4.md D.4-D.7); the case-enumerating coverage check of the killed keys and of the
claims.

Standard library only.  Nothing is imported from the generator (gen_certs4.py / gen_certs3), from qjoint, qjointcheck
or the package programs.  The package, batch-1, flat (PK, FM chords), hub (A = a as two inequalities) and DARK rows are
the hand-written rows of qcert3's independent checker, imported from the unmodified copy check_cases3_copy.py
(standard library only, every constant and coefficient written out column by column).  New here, written from the
statements of PROOF_ADDENDUM_4.md, not from the generator:
  * the case tree: hub cases ('eq', a) for a = 0..q for EVERY q (q <= 1 included), dark cases 0..q; (q+1)^2 leaves;
  * the joint rows of the hub case A = a, appended after all other rows, in the order P1, P2, P3, P4f, P4h, P5, LIM:
      full type (r = 3):    every one of its u labels is full-met (Lemma 4.5):  P1 C(u,2), P4f [u >= 3], else 0;
      non-full type (r<=2): m = number of full-met labels ranges over the integers of I = [max(0, u-(q-a)), min(u, 3-r)]
                            (Lemma H2, row HUB2); EVERY coefficient is the minimum over m in I, computed by brute force:
                            P1 C(m,2), P2 m(u-m), P3 C(u-m,2), P4f [m >= 3], P4h [u-m >= 3], P5 r m;
                            LIM: the type is a limit type iff I forces m = 3 - r (min I = 3 - r): coefficient 1
                            (a < q) or u (a = q), else 0;
      constants:            C(a,2), a(q-a), C(q-a,2), Pk(a), Pk(q-a), top(a) - 3a, 1 (a < q) or q (a = q),
    with top(a) = sum of the a largest ranks of the PINNED FM histogram (check_cases3's FM_RANKS) and Pk(a) the
    packing bound of D.5 computed here by its proof (not by the closed formula): N = floor(a floor((a-1)/2) / 3), then
    for odd a lowered while C(a,2) - 3N is 1 or 2 (an even-degree leave graph has 0 or >= 3 edges).
For each certificate (key, hub, dark, lambda): the case is legal; lambda is a list of nonnegative integers of the
right length; lambda^T b < 0; lambda^T A >= 0 in every column of the case.  The file's 'A' / 'qD' fields must equal
the case.  Coverage: a key is excluded iff every leaf (('eq', a), d) has a certificate for it, for (('eq', a), None)
or for (None, None) (or (None, d)).  Claims: as check_cases3 (admissible state, every referenced key covered, final test).
usage: python3 check_cases4.py [CERTIFICATES_CASES75_B4.json] ['{}' to skip the pinned counts]
"""
import json, sys, itertools
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_cases3_copy as c3      # noqa: E402  (unmodified copy of qcert3/check_cases3.py; standard library only)

G = 75
c2 = c3.c2
NJ = 7
JOINT = ['P1', 'P2', 'P3', 'P4f', 'P4h', 'P5', 'LIM']


def packing_bound(a):
    """upper bound on the size of a family of distinct >= 3-subsets of an a-set pairwise meeting in <= 1 element
    (PROOF_ADDENDUM_4.md D.5): shrink each set to a 3-subset; an element lies in <= floor((a-1)/2) of the triples, so
    3N <= a floor((a-1)/2); for odd a every vertex of the graph of uncovered pairs has even degree (a-1 minus twice a
    count), so that graph has 0 or >= 3 edges."""
    if a < 3: return 0
    N = (a * ((a - 1) // 2)) // 3
    if a % 2 == 1:
        while c2(a) - 3 * N in (1, 2): N -= 1
    return N


def packing_exact(a):
    """exhaustive maximum (information only: shows the bound is attained for small a)."""
    trip = list(itertools.combinations(range(a), 3)); best = [0]
    def rec(i, chosen):
        if len(chosen) + (len(trip) - i) <= best[0]: return
        if i == len(trip): best[0] = len(chosen); return
        t = set(trip[i])
        if all(len(t & set(trip[j])) <= 1 for j in chosen): rec(i + 1, chosen + [i])
        rec(i + 1, chosen)
    rec(0, []); return best[0]


def hub_cases(q): return [('eq', a) for a in range(q + 1)]


def leaves(q): return [(hc, d) for hc in hub_cases(q) for d in range(q + 1)]


def legal_case(key, hub, dark):
    q = key[4]
    if hub is not None:
        if not (isinstance(hub, (list, tuple)) and len(hub) == 2 and hub[0] == 'eq' and type(hub[1]) is int and 0 <= hub[1] <= q): return False
    if dark is not None and not (type(dark) is int and 0 <= dark <= q): return False
    return True


def m_interval(q, a, r, u):
    lo = max(0, u - (q - a)); hi = min(u, 3 - r)
    assert lo <= hi, ('type should have been deleted', q, a, r, u)
    return range(lo, hi + 1)


def joint_constants(key, a):
    h, y, F, ori, q, z = key
    return [c2(a), a * (q - a), c2(q - a), packing_bound(a), packing_bound(q - a), c3.fm_top(ori, a) - 3 * a, q if a == q else 1]


def joint_column(key, a, r, u, v):
    q = key[4]
    if r == 3:
        return [c2(u), 0, 0, int(u >= 3), 0, 0, 0]
    I = m_interval(q, a, r, u)
    limit = min(I) == 3 - r
    return [min(c2(m) for m in I), min(m * (u - m) for m in I), min(c2(u - m) for m in I),
            min(int(m >= 3) for m in I), min(int(u - m >= 3) for m in I), min(r * m for m in I),
            ((u if a == q else 1) if limit else 0)]


def matrix(key, hub, dark):
    """(b, columns, n_pkg, n_b1, n_flat): check_cases3's hand-written system of the case, plus the joint rows in a hub case."""
    b, cols, n_pkg, n_b1, n_flat = c3.matrix(key, hub, dark)
    if hub is not None:
        a = hub[1]
        b = b + joint_constants(key, a)
        cols = [(lab, col + (joint_column(key, a, *lab) if isinstance(lab, tuple) else [0] * NJ)) for lab, col in cols]
    for lab, col in cols: assert len(col) == len(b)
    return b, cols, n_pkg, n_b1, n_flat


def check_certificate(key, hub, dark, weights):
    h, y, F, ori, q, z = key
    assert ori in ('M', 'Mt') and all(type(v) is int and v >= 0 for v in (h, y, F, q, z))
    assert legal_case(key, hub, dark), ('illegal case', key, hub, dark)
    b, cols, n_pkg, n_b1, n_flat = matrix(key, hub, dark)
    count, wrhs = c3.check_weights(weights, b, cols)
    return count, wrhs, n_pkg, n_b1, n_flat, len(b)


def covered(cases, q):
    if (None, None) in cases: return True
    for hc, d in leaves(q):
        if (hc, None) in cases or (None, d) in cases or (hc, d) in cases: continue
        return False
    return True


STATES = [None]
def claims_check(claims, certs):
    if STATES[0] is None: STATES[0] = c3.scalar_domain()
    states = STATES[0]
    seen = set(); references = 0; direct = 0; distinct = set()
    for claim in claims:
        st, ori = tuple(claim['state']), claim['orientation']
        assert st in states, ('state outside the admissible domain', st)
        assert (st, ori) not in seen; seen.add((st, ori))
        a, b, Y, V, ha, hb, la, lb, Sa, Sb, budget = st
        k, l = claim['lower_even'], claim['lower_odd']
        assert type(k) is int and type(l) is int
        assert la <= k <= Sa + 1 and lb <= l <= Sb + 1, (st, ori, k, l)
        other = 'Mt' if ori == 'M' else 'M'
        for h, y, F, o, low, cap, bound in ((ha, Y, V, ori, la, Sa, k), (hb, V, Y, other, lb, Sb, l)):
            for total in range(low, min(cap, bound - 1) + 1):
                for z in range(total + 1):
                    q = total - z
                    if 2 * h + y + z + c2(q) < 32: continue
                    key = (h, y, F, o, q, z)
                    if c3.geometric_exclusion(key):
                        direct += 1; continue
                    assert key in certs, ('uncovered key', (st, ori), key)
                    assert covered(certs[key], q), ('referenced key not covered in every case', (st, ori), key)
                    references += 1; distinct.add(key)
        assert k > Sa or l > Sb or k + l > budget, ('final test fails', st, ori, k, l)
    return seen, references, direct, distinct


def verify(data, quiet=False):
    assert data['gates'] == G
    for a in range(0, 21):
        assert data['packing_D3'][str(a)] <= packing_bound(a), ('file packing value above the proved bound', a)
    certs = {}; coefficients = 0; rhs_values = []; kinds = {'package': 0, 'batch1': 0, 'flat': 0, 'case': 0}
    hub_hist = {}; dark_hist = {}; case_kinds = {'hub-only': 0, 'hub+dark': 0, 'dark-only': 0}
    joint_use = {n: 0 for n in JOINT}; case_without_joint = 0; flat_rows = {'PK': 0, 'FM': 0}
    lim_cases = {'J1b hub-only (a = q-1)': 0, 'J1a full-met (a = q)': 0, 'Lemma 4.6 only (a <= q-2)': 0}; uses_j1 = set()
    for entry in data['certificates']:
        key = tuple(entry['key']); hub = tuple(entry['hub']) if entry.get('hub') is not None else None; dark = entry.get('dark')
        assert entry.get('A') == (hub[1] if hub else None) and entry.get('qD') == dark, ('A / qD fields disagree with the case', key, hub, dark)
        count, wrhs, n_pkg, n_b1, n_flat, nrows = check_certificate(key, hub, dark, entry['weights'])
        kind = entry.get('kind'); w = entry['weights']; q = key[4]
        if kind == 'package':
            assert hub is None and dark is None and not any(w[n_pkg:])
        elif kind == 'batch1':
            assert hub is None and dark is None and any(w[n_pkg:n_pkg + n_b1]) and not any(w[n_pkg + n_b1:])
        elif kind == 'flat':
            assert hub is None and dark is None and any(w[n_pkg + n_b1:n_pkg + n_b1 + n_flat])
        elif kind == 'case':
            assert hub is not None or dark is not None
            case_kinds['hub+dark' if (hub is not None and dark is not None) else ('hub-only' if hub is not None else 'dark-only')] += 1
            if hub is not None:
                hub_hist[hub[1]] = hub_hist.get(hub[1], 0) + 1
                used = [JOINT[i] for i in range(NJ) if w[nrows - NJ + i]]
                for n in used: joint_use[n] += 1
                if not used: case_without_joint += 1
                assert sorted(used) == sorted(entry.get('joint_rows_used', [])), ('joint_rows_used field wrong', key, hub, dark)
                if 'LIM' in used:
                    j1 = hub[1] >= q - 1            # LIM cases (ii) a = q - 1 and (iii) a = q rest on J1; case (i) on Lemma 4.6 alone
                    lim_cases['J1b hub-only (a = q-1)' if hub[1] == q - 1 else ('J1a full-met (a = q)' if hub[1] == q else 'Lemma 4.6 only (a <= q-2)')] += 1
                    if j1: uses_j1.add((key, hub, dark))
            assert bool(entry.get('uses_J1')) == ((key, hub, dark) in uses_j1), ('uses_J1 field wrong', key, hub, dark)
            if dark is not None: dark_hist[dark] = dark_hist.get(dark, 0) + 1
        else:
            raise AssertionError(('unknown kind', key, kind))
        if q in (4, 5) and w[n_pkg + n_b1]: flat_rows['PK'] += 1
        if any(w[n_pkg + n_b1 + (1 if q in (4, 5) else 0):n_pkg + n_b1 + n_flat]): flat_rows['FM'] += 1
        kinds[kind] += 1
        cs = certs.setdefault(key, set())
        assert (hub, dark) not in cs, ('duplicate certificate', key, hub, dark)
        cs.add((hub, dark)); coefficients += count; rhs_values.append(wrhs)
    b3 = {tuple(k) for k in data['batch3_feasible_keys']}; killed = {tuple(k) for k in data['killed_keys']}; surv = {tuple(k) for k in data['surviving_keys']}
    assert killed | surv == b3 and not (killed & surv), 'killed / surviving keys do not partition the batch-3-feasible keys'
    n_leaves_killed = 0
    for key in sorted(killed):
        assert key in certs and covered(certs[key], key[4]), ('killed key not covered in every case', key)
        n_leaves_killed += len(leaves(key[4]))
    seen, references, direct, distinct = claims_check(data['claims'], certs)
    n_leaves_ref = sum(len(leaves(key[4])) for key in distinct)
    keys_by_kind = {'package': 0, 'batch1': 0, 'flat': 0, 'case': 0}
    first = {}
    for e in data['certificates']:
        if e.get('hub') is None and e.get('dark') is None: first[tuple(e['key'])] = e['weights']
    for key, cs in certs.items():
        if (None, None) in cs:
            b_, n_pkg, n_b1, n_flat = c3.right_sides(key)
            w = first[key]
            keys_by_kind['package' if not any(w[n_pkg:]) else ('batch1' if not any(w[n_pkg + n_b1:]) else 'flat')] += 1
        else: keys_by_kind['case'] += 1
    killed_by_kind = {}
    for key in killed:
        cs = certs[key]
        kk = 'case' if (None, None) not in cs else ('package' if not any(first[key][c3.right_sides(key)[1]:]) else 'flat-or-batch1')
        killed_by_kind[kk] = killed_by_kind.get(kk, 0) + 1
    # what holds WITHOUT finite fact J1: coverage by the certificates that do not use LIM in a case A >= q - 1
    certs_free = {key: {c for c in cs if (key, c[0], c[1]) not in uses_j1} for key, cs in certs.items()}
    killed_free = sum(1 for key in killed if covered(certs_free[key], key[4]))
    claims_free = 0
    for claim in data['claims']:
        try:
            claims_check([claim], certs_free); claims_free += 1
        except AssertionError:
            pass
    result = dict(gates=G, scalar_states=len(STATES[0]), claims_checked=len(seen), certificates=sum(kinds.values()),
                  certificates_package=kinds['package'], certificates_batch1=kinds['batch1'], certificates_flat=kinds['flat'], certificates_case=kinds['case'],
                  case_certificates_hub_only=case_kinds['hub-only'], case_certificates_hub_and_dark=case_kinds['hub+dark'],
                  case_certificates_dark_only=case_kinds['dark-only'], case_certificates_without_joint_rows=case_without_joint,
                  joint_row_use={k: v for k, v in joint_use.items()}, certificates_using_PK=flat_rows['PK'], certificates_using_FM=flat_rows['FM'],
                  keys_with_certificates=len(certs), keys_by_kind=keys_by_kind, killed_keys_by_kind=killed_by_kind,
                  batch3_feasible_keys=len(b3), killed_keys=len(killed), surviving_keys=len(surv),
                  leaf_cases_of_killed_keys=n_leaves_killed, leaf_cases_of_referenced_keys=n_leaves_ref,
                  coefficients_checked=coefficients, largest_right_side=max(rhs_values) if rhs_values else None,
                  certificate_references=references, distinct_referenced=len(distinct), direct_geometric_references=direct,
                  hub_case_histogram={str(k): v for k, v in sorted(hub_hist.items())},
                  dark_case_histogram={str(k): v for k, v in sorted(dark_hist.items())},
                  certificates_using_LIM_by_basis=lim_cases, certificates_using_J1=len(uses_j1),
                  killed_keys_covered_without_J1=killed_free, claims_covered_without_J1=claims_free,
                  packing_bound={str(a): packing_bound(a) for a in range(0, 13)}, all_checks_passed=True)
    if not quiet: print(json.dumps(result, indent=2))
    return result


def verify_partial(pdata, data):
    """CERTIFICATES_PARTIAL75_B4.json: certificates for the killed cases of the SURVIVING batch-3-feasible keys.  Every
    certificate is checked like the others; every leaf of every surviving key must be certified dead (by its leaf or
    its whole hub case) or listed open, never both; every surviving key has an open leaf.  Open leaves are LP-feasible
    by the generator's LP [measured]; nothing is excluded by this file."""
    surv = {tuple(k) for k in data['surviving_keys']}
    assert {tuple(k) for k in pdata['surviving_keys']} == surv and not pdata['uncertified_nonfeasible']
    certs = {}; n = 0; coef = 0; rhs = []; joint = {nm: 0 for nm in JOINT}; whole = 0
    for e in pdata['certificates']:
        key = tuple(e['key']); hub = tuple(e['hub']) if e.get('hub') is not None else None; dark = e.get('dark')
        assert key in surv and hub is not None and e.get('kind') == 'partial' and e.get('A') == hub[1] and e.get('qD') == dark
        count, wrhs, n_pkg, n_b1, n_flat, nrows = check_certificate(key, hub, dark, e['weights'])
        cs = certs.setdefault(key, set()); assert (hub, dark) not in cs; cs.add((hub, dark))
        coef += count; rhs.append(wrhs); n += 1; whole += dark is None
        for i in range(NJ):
            if e['weights'][nrows - NJ + i]: joint[JOINT[i]] += 1
    open_ = {tuple(k): {(('eq', a), d) for a, d in v} for k, v in pdata['open_leaves']}
    assert set(open_) == surv
    n_leaves = n_dead = n_open = 0; keys_all_open = 0
    for key in surv:
        cs = certs.get(key, set())
        assert open_[key], ('surviving key without an open leaf', key)
        if not cs: keys_all_open += 1
        for hc, d in leaves(key[4]):
            dead = (hc, None) in cs or (hc, d) in cs; isopen = (hc, d) in open_[key]
            assert dead != isopen, ('leaf neither certified nor open, or both', key, hc, d)
            n_leaves += 1; n_dead += dead; n_open += isopen
    return dict(partial_certificates=n, partial_certificates_whole_hub_case=whole, partial_keys_with_certificates=len(certs),
                partial_keys_without_any_dead_case=keys_all_open, partial_leaves=n_leaves, partial_leaves_certified_dead=n_dead,
                partial_leaves_open=n_open, partial_largest_right_side=max(rhs) if rhs else None, partial_coefficients=coef, partial_joint_row_use=joint)


EXPECTED = {'scalar_states': 3708, 'claims_checked': 103, 'certificates': 4361, 'certificates_package': 745, 'certificates_batch1': 101,
            'certificates_flat': 9, 'certificates_case': 3506, 'case_certificates_hub_only': 2350, 'case_certificates_hub_and_dark': 1156,
            'case_certificates_dark_only': 0, 'case_certificates_without_joint_rows': 2677,
            'joint_row_use': {'P1': 171, 'P2': 333, 'P3': 285, 'P4f': 35, 'P4h': 76, 'P5': 8, 'LIM': 78},
            'certificates_using_PK': 98, 'certificates_using_FM': 26, 'keys_with_certificates': 1307, 'batch3_feasible_keys': 1679,
            'killed_keys': 375, 'surviving_keys': 1304, 'leaf_cases_of_killed_keys': 14096, 'leaf_cases_of_referenced_keys': 18418,
            'coefficients_checked': 264062, 'largest_right_side': -1, 'certificate_references': 1616, 'distinct_referenced': 980,
            'direct_geometric_references': 188, 'certificates_using_LIM_by_basis': {'J1b hub-only (a = q-1)': 78, 'J1a full-met (a = q)': 0, 'Lemma 4.6 only (a <= q-2)': 0}, 'certificates_using_J1': 78,
            'killed_keys_covered_without_J1': 297, 'claims_covered_without_J1': 65,
            'partial_certificates': 22586, 'partial_leaves': 47987, 'partial_leaves_certified_dead': 44058, 'partial_leaves_open': 3929}
# pinned 2026-11-08 from the J1-free-first run (gen_certs4.py with certify_key4), see REPORT.md; the partial_* counts are
# checked when CERTIFICATES_PARTIAL75_B4.json is present next to the certificate file

if __name__ == '__main__':
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / 'certificates' / 'CERTIFICATES_CASES75_B4.json'
    ex = {a: packing_exact(a) for a in range(0, 8)}
    assert all(ex[a] == packing_bound(a) for a in ex), ex
    print('packing bound attained (exhaustive) for a = 0..7:', ex)
    data = json.loads(src.read_text())
    res = verify(data)
    psrc = src.with_name('CERTIFICATES_PARTIAL75_B4.json')
    if psrc.exists():
        pres = verify_partial(json.loads(psrc.read_text()), data)
        print(json.dumps(pres, indent=2)); res.update(pres)
        print('PARTIAL CERTIFICATES CHECKED')
    exp = json.loads(sys.argv[2]) if len(sys.argv) > 2 else EXPECTED
    if exp:
        for k, v in exp.items():
            if k.startswith('partial_') and not psrc.exists(): continue
            assert res[k] == v, ('expected', k, v, 'got', res[k])
        print('expected counts match:', exp)
    Path(__file__).with_name('CHECKED_CASES75_B4.json').write_text(json.dumps(res, indent=2) + '\n')
    print('INDEPENDENT CHECK PASSED')
