#!/usr/bin/env python3
"""qcert4 generator (G = 75): the batch-3 local systems with the HUB2 split replaced by the EXACT integer split A = a,
a = 0..q (every q, including q <= 1), and in each hub case the rows of Lemma P (P1-P5) and row LIM
(PROOF_ADDENDUM_4.md D.4-D.6; qjoint/REPORT.md section 4; variant GstarN1HUB2DARKPKFMJOINTLIM of qjoint/qj_lp.py).

Local system of a key (h, y, F, ori, q, z) and a case (hub, dark):
  columns = as batch 3: the package's helper types (r,u,v), r+u+v >= 3, minus in hub case A = a the types with r <= 2
            and u > (3 - r) + (q - a); + [y0, y1, y2] (+ [y2d, Fb, Fd] in a dark case)
  rows    = 1-3. package rows, batch-1 rows, flat batch-3 rows (PK4/PK5, FM7/FM9 chords), exactly as
            qcert3/gen_certs3.ext_system (imported from the unmodified copy gen_certs3_copy.py);
            4. hub = ('eq', a): sum_{r=3} u n = a (two inequalities);
            5. dark = d: the DARK rows of Addendum B (unchanged);
            6. hub = ('eq', a) only, APPENDED LAST: P1, P2, P3, P4f, P4h, P5, LIM of the hub case A = a
               (closed forms of qjoint/qj_lp.joint_rows; the checker builds them by brute force over the m-interval).
  Cases of a key: hub in {('eq', 0), ..., ('eq', q)}, dark in {0..q}; leaves (q+1)^2.  Lemma C1 of Addendum B applies
  (a (None, None) certificate covers every leaf, (a, None) every (a, d)).
Certificates: Farkas LP (HiGHS), rationalized, scaled to integers, verified in exact integer arithmetic (gen_certs3's
farkas_int / exact_ok).  The LP status never decides an exclusion.  Independent checker: check_cases4.py.
J1-free first (certify_key4): in every hub case a certificate WITHOUT the row LIM is sought first (whole hub case, then
leaf by leaf); LIM is used only where no such certificate exists, so the certificates that use finite fact J1 (LIM in
a case A >= q - 1, field 'uses_J1') are exactly the ones that need it within this search.  At the end the LP scan is
repeated without LIM (what the new rows exclude without J1, by LP status).

Keys certified: (a) every key LP-feasible under the batch-3 system in qcert3's files (keysfull3.json 'feasible' = the
859 LP-feasible keys of the batch-3 scan, and CERTIFICATES_CASES75_B3.json 'surviving_keys' = the 1,177 batch-3
survivors of the 1,713 batch-2-feasible keys), together with every key the NEW scan touched outside these lists that is
batch-3-feasible (new-feasible keys are batch-3-feasible by monotonicity; for the others feasible_b3 evaluates the
unmodified batch-3 system), that the new system kills; (b) every key referenced by the coverage of a claim that the
new system excludes and the batch-3 system does not (789 -> 686).

usage: PYTHONDONTWRITEBYTECODE=1 nice -n 8 python3 gen_certs4.py
       (writes CERTIFICATES_CASES75_B4.json, scan_cases4.json, keysfull4.json, gen_certs4.log)
"""
import sys, json, time
sys.dont_write_bytecode = True
from math import comb
from pathlib import Path
from collections import Counter

SPRINT = Path.home() / 'xs-campaigns/2026-11-07-sprint'
HERE = SPRINT / 'qcert4'
sys.path.insert(0, str(HERE))
import gen_certs3_copy as g3      # noqa: E402  unmodified copy of qcert3/gen_certs3.py (imports the package copy)

G = 75
LOGF = open(HERE / 'gen_certs4.log', 'a')
g3.LOG[0] = LOGF                   # gen_certs3's own log() (LP-status warnings) goes here, never into qcert3/
def log(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True); LOGF.write(s + '\n'); LOGF.flush()


def D3(a):
    """packing number D(a,3,2) (qjoint/qj_lp.D3): floor(a floor((a-1)/2) / 3), minus 1 when a = 5 mod 6."""
    if a < 3: return 0
    v = (a * ((a - 1) // 2)) // 3
    return v - 1 if a % 6 == 5 else v


JOINT_NAMES = ['P1', 'P2', 'P3', 'P4f', 'P4h', 'P5', 'LIM']


def joint_rows(key, a, types, lim=True):
    """rows of Lemma P and row LIM in hub case A = a (closed forms of qjoint/qj_lp.joint_rows):
    [(name, coefficients over types, constant)]."""
    h, y, F, ori, q, z = key
    assert 0 <= a <= q
    top = g3.FMTAB[ori][0]; assert len(top) > a
    def mlb(r, u): return max(0, u - (q - a))
    def mub(r, u): return min(u, 3 - r)
    rows = []
    rows.append((f'P1 A={a}', [comb(mlb(r, u), 2) if r < 3 else comb(u, 2) for r, u, v in types], comb(a, 2)))
    rows.append((f'P2 A={a}', [min(mlb(r, u) * (u - mlb(r, u)), mub(r, u) * (u - mub(r, u))) if r < 3 else 0 for r, u, v in types], a * (q - a)))
    rows.append((f'P3 A={a}', [comb(u - mub(r, u), 2) if r < 3 else 0 for r, u, v in types], comb(q - a, 2)))
    rows.append((f'P4f A={a}', [(1 if mlb(r, u) >= 3 else 0) if r < 3 else (1 if u >= 3 else 0) for r, u, v in types], D3(a)))
    rows.append((f'P4h A={a}', [(1 if u - mub(r, u) >= 3 else 0) if r < 3 else 0 for r, u, v in types], D3(q - a)))
    rows.append((f'P5 A={a}', [r * mlb(r, u) if r < 3 else 0 for r, u, v in types], top[a] - 3 * a))
    if lim:
        islim = lambda r, u: r < 3 and u == (3 - r) + (q - a)
        if a == q: rows.append((f'LIM A=q={a}', [u if islim(r, u) else 0 for r, u, v in types], q))
        else: rows.append((f'LIM A={a}<q', [1 if islim(r, u) else 0 for r, u, v in types], 1))
    return rows


ORIG_EXT = g3.ext_system
USE_LIM = [True]


def ext_system4(key, hub=None, dark=None):
    """gen_certs3.ext_system plus, in a hub case ('eq', a), the joint rows appended after all other rows."""
    types, aux, A, B, names, n_pkg, n_b1, n_flat = ORIG_EXT(key, hub, dark)
    if hub is not None:
        assert hub[0] == 'eq' and 0 <= hub[1] <= key[4], hub
        for name, coef, b in joint_rows(key, hub[1], types, USE_LIM[0]):
            A.append(list(coef) + [0] * len(aux)); B.append(b); names.append(name)
    return types, aux, A, B, names, n_pkg, n_b1, n_flat


def hub_cases4(q):
    """the exact integer split: A = sum_{r=3} u n is an integer in 0..q."""
    return [('eq', a) for a in range(q + 1)]


g3.ext_system = ext_system4        # gen_certs3's farkas_int / feas_case / feasible_full / certify_key now use the new system
g3.hub_cases = hub_cases4


B3CACHE = {}
def feasible_b3(key):
    """LP feasibility under the UNMODIFIED batch-3 system (gen_certs3's ext_system and hub split: none for q <= 1,
    A = 2..q and A <= 1 otherwise), same logic as gen_certs3.feasible_full, own cache."""
    import numpy as np
    from scipy.optimize import linprog
    def fc(hub, dark):
        k = (key, hub, dark)
        if k not in B3CACHE:
            types, aux, A, B, names, n_pkg, n_b1, n_flat = ORIG_EXT(key, hub, dark)
            res = linprog(np.zeros(len(A[0])), A_ub=np.array(A, float), b_ub=np.array(B, float), bounds=(0, None), method='highs')
            B3CACHE[k] = res.status != 2
            if res.status not in (0, 2): log('batch-3 LP status', res.status, key, hub, dark)
        return B3CACHE[k]
    if not g3.prefilter(key) or not fc(None, None): return False
    q = key[4]
    for hc in ([None] if q <= 1 else [('eq', a) for a in range(2, q + 1)] + [('le', 1)]):
        if hc is not None and not fc(hc, None): continue
        for d in range(q + 1):
            if fc(hc, d): return True
    return False


def farkas_nolim(key, hub, dark):
    """Farkas LP over the case system WITHOUT the LIM row (the last row of a hub case); a certificate found is padded
    by a zero multiplier on LIM and re-verified over the full case system: such a certificate does not use finite
    fact J1.  (Only farkas_int is called while USE_LIM is off; the feasibility cache is never touched here.)"""
    USE_LIM[0] = False
    try:
        st, ints = g3.farkas_int(key, hub, dark, 'all')
    finally:
        USE_LIM[0] = True
    if st == 'cert':
        ints = ints + [0]
        types, aux, A, B, names, n_pkg, n_b1, n_flat = ext_system4(key, hub, dark)
        assert names[-1].startswith('LIM') and g3.exact_ok(ints, A, B)
    return st, ints


def certify_key4(key):
    """gen_certs3.certify_key's tree with J1-free certificates preferred: package; batch-1; flat; then per hub case
    A = a: (a, none) without LIM; else every leaf (a, d) without LIM; if some leaf needs LIM, (a, none) with LIM;
    else the leaves, each without LIM where possible and with LIM otherwise.  Returns (kind, [(hub, dark, ints)], problem)."""
    q = key[4]
    for rows, kind in (('package', 'package'), ('batch1', 'batch1'), ('all', 'flat')):
        st, ints = g3.farkas_int(key, None, None, rows)
        if st == 'cert': return kind, [(None, None, ints)], None
    if st != 'feasible': return 'fail', [], ('flat', st)
    certs = []
    for hc in hub_cases4(q):
        st, ints = farkas_nolim(key, hc, None)
        if st == 'cert': certs.append((hc, None, ints)); continue
        free = {}
        for d in range(q + 1):
            st, ints = farkas_nolim(key, hc, d)
            if st == 'cert': free[d] = ints
        if len(free) == q + 1:
            certs += [(hc, d, free[d]) for d in range(q + 1)]; continue
        st, ints = g3.farkas_int(key, hc, None)
        if st == 'cert': certs.append((hc, None, ints)); continue
        if st != 'feasible': return 'fail', certs, (hc, None, st)
        for d in range(q + 1):
            if d in free: certs.append((hc, d, free[d])); continue
            st, ints = g3.farkas_int(key, hc, d)
            if st == 'cert': certs.append((hc, d, ints))
            elif st == 'feasible': return 'feasible', certs, (hc, d)
            else: return 'fail', certs, (hc, d, st)
    return 'case', certs, None


def main():
    t0 = time.time()
    states, claims_new, surv_new = g3.lp_regen.run(G)
    sf = {(st, o) for st, o, k, l in surv_new}
    log(f'new scan: scalar states {len(states)}, oriented claims {len(claims_new)}; survivors {len(sf)} (M {sum(1 for s, o in sf if o == "M")}); '
        f'keys touched {len(g3.RECORD)}, LP-feasible {sum(g3.RECORD.values())}; {time.time()-t0:.0f}s')
    s3 = json.load(open(SPRINT / 'qcert3/scan_cases3.json'))
    sb3 = {(tuple(st), o) for st, o in s3['full_survivors']}
    claims_b3 = {(tuple(c['state']), c['orientation']): tuple(c['full']) for c in s3['claims']}
    assert len(sb3) == 789 and sf <= sb3, 'new survivors not a subset of the batch-3 survivors'
    excluded = sorted(sb3 - sf)
    for c in claims_new:
        kb, lb, db = claims_b3[c]; ke, le, de = claims_new[c]
        assert ke >= kb and (ke > kb or le >= lb), (c, claims_b3[c], claims_new[c])
    log(f'batch-3 survivors {len(sb3)} (qcert3); new survivors {len(sf)}; newly excluded claims {len(excluded)} '
        f'(M {sum(1 for s, o in excluded if o == "M")}); bounds monotone on all {len(claims_new)} claims')
    # batch-3-feasible keys known from qcert3's files
    kf3 = json.load(open(SPRINT / 'qcert3/keysfull3.json'))
    c3 = json.load(open(SPRINT / 'qcert3/CERTIFICATES_CASES75_B3.json'))
    feas859 = {tuple(k) for k in kf3['feasible']}; lb551 = {tuple(k) for k in kf3['load_bearing']}
    surv1177 = {tuple(k) for k in c3['surviving_keys']}
    assert len(feas859) == 859 and len(lb551) == 551 and len(surv1177) == 1177
    files = feas859 | surv1177
    # keys the NEW scan touched outside qcert3's lists: new-feasible ones are batch-3-feasible (every new case system is
    # stronger, D.8); for the new-infeasible ones batch-3 feasibility is computed here with the unmodified batch-3 system
    touched = set(g3.RECORD)
    assert all(feasible_b3(k) for k in sorted(files)), 'batch-3 re-evaluation disagrees with qcert3 on a listed key'
    extra = sorted(k for k in touched - files if g3.RECORD[k] or feasible_b3(k))
    log(f'keys touched by the new scan outside qcert3 lists: {len(touched - files)}; batch-3-feasible among them {len(extra)} '
        f'(new-feasible {sum(1 for k in extra if g3.RECORD[k])}); the 1,437 listed keys re-evaluated batch-3-feasible; {time.time()-t0:.0f}s')
    base = sorted(files | set(extra))
    killed = [k for k in base if not g3.feasible_full(k)]
    surviving = [k for k in base if g3.feasible_full(k)]
    lb_still = sorted(k for k in lb551 if g3.feasible_full(k))
    log(f'batch-3-feasible keys: scan 859, batch-3 survivors of the 1,713: 1,177, union {len(base)}; killed by the new system {len(killed)} '
        f'(of the 859: {sum(1 for k in killed if k in feas859)}; of the 551 load-bearing: {sum(1 for k in killed if k in lb551)}), surviving {len(surviving)}; '
        f'load-bearing still feasible {len(lb_still)}; {time.time()-t0:.0f}s')
    # without LIM on the 551 (qjoint's 452)
    USE_LIM[0] = False; g3.CACHE.clear()
    lb_still_nolim = sorted(k for k in lb551 if g3.feasible_full(k))
    USE_LIM[0] = True; g3.CACHE.clear()
    log(f'load-bearing still feasible without LIM (P1-P5 only): {len(lb_still_nolim)}')
    # keys referenced by the coverage of the newly excluded claims
    needed = {}
    for st, ori in excluded:
        a, b, Y, V, he, ho, le_, lo_, Se, So, budget = st
        k, l, dead = claims_new[(st, ori)]
        assert dead and (k > Se or l > So or k + l > budget)
        other = 'Mt' if ori == 'M' else 'M'
        for h, y, F, o, least, greatest, claimed in ((he, Y, V, ori, le_, Se, k), (ho, V, Y, other, lo_, So, l)):
            for s in range(least, min(claimed - 1, greatest) + 1):
                for q in range(s + 1):
                    z = s - q
                    if 2 * h + y + z + comb(q, 2) < 32: continue
                    key = (h, y, F, o, q, z)
                    if g3.certify75.direct_exclusion(key): continue
                    assert not g3.feasible_full(key), ('referenced key feasible?!', key)
                    needed[key] = True
    log(f'coverage of the {len(excluded)} claims references {len(needed)} distinct keys; {time.time()-t0:.0f}s')
    feas = {k for k, v in g3.RECORD.items() if v}
    lbn = set()
    for st, ori, k, ell in surv_new:
        other = 'Mt' if ori == 'M' else 'M'
        for q in range(0, k + 1):
            kk = (st[4], st[2], st[3], ori, q, k - q)
            if kk in feas: lbn.add(kk)
        for q in range(0, ell + 1):
            kk = (st[5], st[3], st[2], other, q, ell - q)
            if kk in feas: lbn.add(kk)
    log(f'scan bookkeeping: keys touched {len(g3.RECORD)}; LP-feasible {len(feas)} (by q {sorted(Counter(k[4] for k in feas).items())}; by ori {dict(Counter(k[3] for k in feas))}); '
        f'load-bearing {len(lbn)} (by q {sorted(Counter(k[4] for k in lbn).items())}; by ori {dict(Counter(k[3] for k in lbn))})')
    json.dump(dict(touched=len(g3.RECORD), feasible=sorted(list(k) for k in feas), load_bearing=sorted(list(k) for k in lbn),
                   lb551_still_feasible=[list(k) for k in lb_still], lb551_still_feasible_without_LIM=[list(k) for k in lb_still_nolim]),
              open(HERE / 'keysfull4.json', 'w'))
    json.dump({'G': G, 'states': [list(s) for s in states],
               'claims': [{'state': list(st), 'orientation': o, 'batch3': list(claims_b3[(st, o)]), 'new': list(claims_new[(st, o)])} for st, o in sorted(claims_new)],
               'batch3_survivors': [[list(st), o] for st, o in sorted(sb3)], 'new_survivors': [[list(st), o] for st, o in sorted(sf)],
               'new_survivor_bounds': [[list(st), o, k, l] for st, o, k, l in sorted(surv_new)]},
              open(HERE / 'scan_cases4.json', 'w'))
    # certificates
    kset = set(killed)
    todo = sorted(kset) + sorted(set(needed) - kset)
    certs = []; failed = []; kinds = {}; max_rhs = -10 ** 9; n_mult = 0; n_coef = 0; per_key = {}
    for i, key in enumerate(todo):
        try:
            kind, kc, problem = certify_key4(key)
        except Exception as ex:                      # noqa: BLE001
            kind, kc, problem = 'fail', [], repr(ex)
        kinds[kind] = kinds.get(kind, 0) + 1
        if kind in ('feasible', 'fail'):
            failed.append([list(key), kind, str(problem)]); log('  NOT CERTIFIED', key, kind, problem)
        else:
            per_key[key] = len(kc)
        for hub, dark, ints in kc:
            types, aux, A, B, names, n_pkg, n_b1, n_flat = ext_system4(key, hub, dark)
            assert g3.exact_ok(ints, A, B)
            if kind == 'package': assert not any(ints[n_pkg:])
            if kind == 'batch1': assert any(ints[n_pkg:n_pkg + n_b1]) and not any(ints[n_pkg + n_b1:])
            if kind == 'flat': assert any(ints[n_pkg + n_b1:n_pkg + n_b1 + n_flat])
            rhs = sum(w * b for w, b in zip(ints, B)); max_rhs = max(max_rhs, rhs)
            n_mult += len(ints); n_coef += len(A[0])
            used = [names[j] for j in range(len(names)) if ints[j]]
            jused = [n.split()[0] for n in used if n.split()[0] in JOINT_NAMES]
            certs.append({'key': list(key), 'kind': kind, 'hub': list(hub) if hub else None, 'A': hub[1] if hub else None, 'qD': dark, 'dark': dark,
                          'weights': ints, 'joint_rows_used': jused,
                          'uses_J1': bool(hub is not None and 'LIM' in jused and hub[1] >= key[4] - 1)})
        if (i + 1) % 200 == 0: log(f'  {i+1}/{len(todo)} keys, {len(certs)} certificates, kinds {kinds}, {time.time()-t0:.0f}s')
    n_case = sum(1 for c in certs if c['kind'] == 'case')
    log(f'keys to certify {len(todo)} (killed {len(killed)}, referenced {len(needed)}, both {len(kset & set(needed))}); kinds {kinds}; '
        f'certificates {len(certs)} ({n_case} per-case); not certified {len(failed)}; largest weighted rhs {max_rhs}; multipliers {n_mult}; '
        f'coefficients {n_coef}; {time.time()-t0:.0f}s')
    kind_of = {}
    for c in certs: kind_of.setdefault(tuple(c['key']), c['kind'])
    log('killed keys by certificate kind:', dict(Counter(kind_of.get(k) for k in killed)))
    out = {
        'gates': G, 'hub_capacity': {'0': 3, '1': 2, '2': 1},
        'fm_hist': {o: {str(k): v for k, v in g3.FM_HIST[o].items()} for o in g3.FM_HIST},
        'fm_top': {o: g3.FMTAB[o][0] for o in g3.FMTAB},
        'packing_D3': {str(a): D3(a) for a in range(0, 21)},
        'system': 'rows 1-5 as qcert3 (package, batch-1, flat PK/FM, hub A = a as two inequalities, dark) with hub case ("eq", a) for '
                  'a = 0..q; then, in a hub case only, the joint rows P1, P2, P3, P4f, P4h, P5, LIM of the case A = a appended last. '
                  'Columns: helper types minus (r <= 2, u > 3 - r + q - a) in a hub case, + y0, y1, y2 (+ y2d, Fb, Fd in a dark case).',
        'cases': 'hub cases A = 0..q (every q); dark cases q_D = 0..q; leaves (q+1)^2.  A certificate with dark = null covers every dark case '
                 'of its hub case; one with hub = null and dark = null covers every leaf (Lemma C1 of Addendum B).',
        'batch3_feasible_keys': [list(k) for k in base],
        'batch3_feasible_keys_sources': {'qcert3_keysfull3_feasible': 859, 'qcert3_surviving_keys': 1177, 'qcert3_lists_union': len(files),
                                         'new_scan_touched_outside_lists_batch3_feasible': len(extra), 'union': len(base)},
        'batch3_feasible_extra_keys': [list(k) for k in extra],
        'killed_keys': [list(k) for k in killed], 'surviving_keys': [list(k) for k in surviving],
        'claims': [{'state': list(st), 'orientation': ori, 'lower_even': claims_new[(st, ori)][0], 'lower_odd': claims_new[(st, ori)][1],
                    'batch3_lower_even': claims_b3[(st, ori)][0], 'batch3_lower_odd': claims_b3[(st, ori)][1]} for st, ori in excluded],
        'certificates': certs, 'uncertified': failed,
        'counts': {'scalar_states': len(states), 'oriented_claims': len(claims_new), 'batch3_survivors': len(sb3), 'new_survivors': len(sf),
                   'newly_excluded_claims': len(excluded), 'batch3_feasible_keys': len(base), 'killed_keys': len(killed), 'surviving_keys': len(surviving),
                   'referenced_keys': len(needed), 'keys_certified': len(per_key), 'key_kinds': kinds, 'certificates': len(certs),
                   'case_certificates': n_case, 'failed': len(failed), 'largest_rhs': max_rhs, 'multipliers': n_mult, 'coefficients': n_coef,
                   'keys_touched': len(g3.RECORD), 'keys_lp_feasible': len(feas), 'keys_load_bearing': len(lbn),
                   'lb551_still_feasible': len(lb_still), 'lb551_still_feasible_without_LIM': len(lb_still_nolim)},
    }
    # the LP scan WITHOUT row LIM (what the new rows exclude without finite fact J1) [measured]
    USE_LIM[0] = False; g3.CACHE.clear(); g3.RECORD.clear(); g3.feasible_for_driver.cache_clear()
    st2, cl2, sv2 = g3.lp_regen.run(G)
    USE_LIM[0] = True; g3.CACHE.clear()
    sf2 = {(st, o) for st, o, k, l in sv2}
    out['counts']['survivors_without_LIM'] = len(sf2)
    out['counts']['newly_excluded_without_LIM'] = len(sb3 - sf2)
    out['claims_excluded_without_LIM'] = [[list(st), o] for st, o in sorted(sb3 - sf2)]
    log(f'scan without LIM: survivors {len(sf2)} (M {sum(1 for s, o in sf2 if o == "M")}); of the 789 excluded without LIM {len(sb3 - sf2)}; '
        f'new survivors subset of these: {sf <= sf2}; {time.time()-t0:.0f}s')
    json.dump(out, open(HERE / 'CERTIFICATES_CASES75_B4.json', 'w'))
    log('written CERTIFICATES_CASES75_B4.json, scan_cases4.json, keysfull4.json; total', f'{time.time()-t0:.0f}s')


if __name__ == '__main__':
    main()
