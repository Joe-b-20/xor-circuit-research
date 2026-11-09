#!/usr/bin/env python3
"""Combined LP scan at G = 75: the sprint's final case systems (qcert4 ext_system4: package + batch-1 + flat PK/FM + exact
hub split A = 0..q with P1-P5 and LIM + dark split q_D = 0..q) PLUS the push5/push6 rows (archive generator
lb76/push6_copy/push6/global_chronology/model_full_cuts.py, read-only, which imports the package certify75.py), with
the package driver lp_regen.run exactly as gen_certs4.py uses it.

Variants (argv[1]):
  sprint        ext_system4 (LIM on)                                -> must reproduce 686 survivors (qcert4)
  push          package + push5 + push6 rows, no case split, lp_regen.run  -> compare with the archive's 509
  combined      ext_system4 + push rows in every case system
  combined_nolim  the same without row LIM (what does not rest on finite fact J1)
  leaves        for the load-bearing keys of the combined scan: which leaves (A = a, q_D = d) are LP-feasible
Each variant writes scan_<variant>.json: every claim's (k, l, dead), the survivors, the LP-feasible and load-bearing keys.
LP status is never a proof; every count here is [measured].

Imports (read-only): qcert4/gen_certs3_copy.py (byte-identical copy of qcert3/gen_certs3.py; imports the package copy's
certify75 and lp_regen), the archive push6 model.  joint_rows / D3 / hub_cases4 / ext_system4 are copied VERBATIM from
qcert4/gen_certs4.py (importing gen_certs4 would open its log file in append mode).  gen_certs3's own log goes to recon/.
"""
import sys, json, time
sys.dont_write_bytecode = True
from math import comb
from pathlib import Path
from collections import Counter
from functools import lru_cache
import numpy as np
from scipy.optimize import linprog

SPRINT = Path.home() / 'xs-campaigns/2026-11-07-sprint'
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(SPRINT / 'qcert4'))
import gen_certs3_copy as g3          # noqa: E402  (sets lp_regen.feasible = its feasible_for_driver at import)
import push_rows as PR                # noqa: E402  (only load_archive_model is used here)
g3.LOG[0] = open(HERE / 'gen_certs3_warnings.log', 'a')
MODEL6 = PR.load_archive_model()
G = 75
LOGF = open(HERE / 'combined_scan.log', 'a')
def log(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True); LOGF.write(s + '\n'); LOGF.flush()


# ---------------------------------------------------------------- verbatim from qcert4/gen_certs4.py (lines 52-104)
def D3(a):
    """packing number D(a,3,2) (qjoint/qj_lp.D3): floor(a floor((a-1)/2) / 3), minus 1 when a = 5 mod 6."""
    if a < 3: return 0
    v = (a * ((a - 1) // 2)) // 3
    return v - 1 if a % 6 == 5 else v


JOINT_NAMES = ['P1', 'P2', 'P3', 'P4f', 'P4h', 'P5', 'LIM']


def joint_rows(key, a, types, lim=True):
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
    types, aux, A, B, names, n_pkg, n_b1, n_flat = ORIG_EXT(key, hub, dark)
    if hub is not None:
        assert hub[0] == 'eq' and 0 <= hub[1] <= key[4], hub
        for name, coef, b in joint_rows(key, hub[1], types, USE_LIM[0]):
            A.append(list(coef) + [0] * len(aux)); B.append(b); names.append(name)
    return types, aux, A, B, names, n_pkg, n_b1, n_flat


def hub_cases4(q):
    return [('eq', a) for a in range(q + 1)]
# ---------------------------------------------------------------- end verbatim


USE_PUSH = [False]
F1FREE = [False]          # True: only the push rows whose finite facts were recomputed here (push_rows.py f1free=True)
PUSHSEL = ['all']         # 'all' | 'push5' (push5 rows only) | 'push6' (push6 rows only): ablations, via the verified transcription
PUSHCACHE = {}
def push_block(key):
    """(types0, rows, bounds, names) of the push5+push6 rows of the archive model on the package type list, after an
    assertion that the model's prefix is exactly the package system (certify75.system).  In F1FREE mode the rows come from
    the transcription push_rows.py (identical to the archive generator when f1free=False) with f1free=True."""
    k = (key, F1FREE[0], PUSHSEL[0])
    if k not in PUSHCACHE:
        types0, rows, bounds, names = MODEL6.system(key)
        t0, A0, B0, N0 = g3.certify75.system(key)
        assert types0 == t0 and rows[:len(A0)] == A0 and bounds[:len(B0)] == B0 and names[:len(N0)] == N0, ('prefix', key)
        if F1FREE[0]:
            rr = PR.push_rows(key, types0, dedup=True, f1free=True)
            PUSHCACHE[k] = (types0, [c for _, c, _ in rr], [b for _, _, b in rr], [n for n, _, _ in rr])
        elif PUSHSEL[0] in ('push5', 'push6'):
            rr = PR.push5_rows(key, types0) if PUSHSEL[0] == 'push5' else PR.push6_rows(key, types0, dedup=True)
            PUSHCACHE[k] = (types0, [c for _, c, _ in rr], [b for _, _, b in rr], [n for n, _, _ in rr])
        else:
            PUSHCACHE[k] = (types0, rows[len(A0):], bounds[len(B0):], names[len(N0):])
    return PUSHCACHE[k]


def ext_system_comb(key, hub=None, dark=None):
    """ext_system4 plus, when USE_PUSH, every push row restricted to the case's kept type columns, zero on the aux columns."""
    types, aux, A, B, names, n_pkg, n_b1, n_flat = ext_system4(key, hub, dark)
    if USE_PUSH[0]:
        types0, rows, bounds, pnames = push_block(key)
        idx = {t: j for j, t in enumerate(types0)}
        keep = [idx[t] for t in types]
        for row, b, nm in zip(rows, bounds, pnames):
            A.append([row[j] for j in keep] + [0] * len(aux)); B.append(b); names.append('push ' + nm)
    return types, aux, A, B, names, n_pkg, n_b1, n_flat


g3.ext_system = ext_system_comb
g3.hub_cases = hub_cases4


# ---------------------------------------------------------------- push-only feasibility (no case split)
PUSH_STATUS = Counter(); PUSH_RECORD = {}
@lru_cache(None)
def feasible_push(h, y, F, q, z, ori):
    key = (h, y, F, ori, q, z)
    if g3.certify75.direct_exclusion(key): return False
    if 2 * h + y + z + comb(q, 2) < 32: return False
    types, A, B, names = MODEL6.system(key)
    res = linprog(np.zeros(len(types)), A_ub=np.array(A, float), b_ub=np.array(B, float), bounds=(0, None), method='highs')
    PUSH_STATUS[res.status] += 1
    if res.status not in (0, 2): log('push LP status', res.status, key)
    PUSH_RECORD[key] = res.status != 2
    return res.status != 2


def reset():
    g3.CACHE.clear(); g3.RECORD.clear(); g3.feasible_for_driver.cache_clear(); feasible_push.cache_clear(); PUSH_STATUS.clear(); PUSH_RECORD.clear()


def load_bearing(surv, feas):
    lb = set()
    for st, ori, k, ell in surv:
        other = 'Mt' if ori == 'M' else 'M'
        for q in range(0, k + 1):
            kk = (st[4], st[2], st[3], ori, q, k - q)
            if kk in feas: lb.add(kk)
        for q in range(0, ell + 1):
            kk = (st[5], st[3], st[2], other, q, ell - q)
            if kk in feas: lb.add(kk)
    return lb


def run_variant(variant):
    t0 = time.time(); reset()
    if variant == 'push':
        saved = g3.lp_regen.feasible; g3.lp_regen.feasible = feasible_push
        try:
            states, claims, surv = g3.lp_regen.run(G)
        finally:
            g3.lp_regen.feasible = saved
        feas = {k for k, v in PUSH_RECORD.items() if v}; touched = len(PUSH_RECORD)
    else:
        USE_PUSH[0] = variant.startswith('combined'); USE_LIM[0] = not variant.endswith('nolim'); F1FREE[0] = variant.endswith('f1free')
        PUSHSEL[0] = 'push5' if variant.endswith('push5') else ('push6' if variant.endswith('push6') else 'all')
        states, claims, surv = g3.lp_regen.run(G)
        feas = {k for k, v in g3.RECORD.items() if v}; touched = len(g3.RECORD)
        USE_PUSH[0] = False; USE_LIM[0] = True; F1FREE[0] = False; PUSHSEL[0] = 'all'
    sf = {(st, o) for st, o, k, l in surv}
    out = {'variant': variant, 'G': G, 'scalar_states': len(states), 'oriented_claims': len(claims), 'survivors': len(sf),
           'survivors_M': sum(1 for s, o in sf if o == 'M'), 'survivors_Mt': sum(1 for s, o in sf if o == 'Mt'),
           'claims': [[list(st), o, k, l, dead] for (st, o), (k, l, dead) in sorted(claims.items())],
           'survivor_list': [[list(st), o, k, l] for st, o, k, l in sorted(surv)], 'seconds': round(time.time() - t0)}
    lb = load_bearing(surv, feas)
    out.update(keys_touched=touched, keys_lp_feasible=len(feas), keys_load_bearing=len(lb),
               lp_feasible_keys=sorted(list(k) for k in feas), load_bearing_keys=sorted(list(k) for k in lb),
               lb_by_q=sorted(Counter(k[4] for k in lb).items()), lb_by_ori=dict(Counter(k[3] for k in lb)))
    if variant == 'push': out.update(push_lp_status=dict(PUSH_STATUS))
    json.dump(out, open(HERE / f'scan_{variant}.json', 'w'))
    log(f'[{variant}] states {len(states)} claims {len(claims)} survivors {len(sf)} (M {out["survivors_M"]}, Mt {out["survivors_Mt"]}); '
        f'keys touched {touched}, LP-feasible {len(feas)}, load-bearing {len(lb)} (by q {out["lb_by_q"]}; by ori {out["lb_by_ori"]}); {time.time()-t0:.0f}s')
    return out


def run_leaves():
    """open leaves (A = a, q_D = d) of the combined system for the load-bearing keys of the combined scan [measured]."""
    t0 = time.time(); reset(); USE_PUSH[0] = True; USE_LIM[0] = True
    d = json.load(open(HERE / 'scan_combined.json'))
    keys = [tuple(k) for k in d['load_bearing_keys']]
    res = {}
    for key in keys:
        q = key[4]; open_leaves = []
        if not g3.prefilter(key) or not g3.feas_case(key, None, None): res[str(key)] = []; continue
        for a in range(q + 1):
            if not g3.feas_case(key, ('eq', a), None): continue
            for dd in range(q + 1):
                if g3.feas_case(key, ('eq', a), dd): open_leaves.append([a, dd])
        res[str(key)] = open_leaves
    USE_PUSH[0] = False
    hist_A = Counter(a for v in res.values() for a, dd in v); hist_d = Counter(dd for v in res.values() for a, dd in v)
    only_A0 = sum(1 for v in res.values() if v and all(a == 0 for a, dd in v))
    out = dict(keys=len(keys), open_leaves_total=sum(len(v) for v in res.values()), by_A=sorted(hist_A.items()), by_qD=sorted(hist_d.items()),
               keys_open_only_at_A0=only_A0, keys_with_no_open_leaf=sum(1 for v in res.values() if not v), leaves=res, seconds=round(time.time() - t0))
    json.dump(out, open(HERE / 'scan_leaves.json', 'w'))
    log(f'[leaves] load-bearing keys {len(keys)}: open leaves {out["open_leaves_total"]}, by A {out["by_A"]}, by q_D {out["by_qD"]}, '
        f'keys open only at A=0 {only_A0}, keys with no open leaf {out["keys_with_no_open_leaf"]}; {time.time()-t0:.0f}s')


if __name__ == '__main__':
    for v in sys.argv[1:]:
        if v == 'leaves': run_leaves()
        else: run_variant(v)
