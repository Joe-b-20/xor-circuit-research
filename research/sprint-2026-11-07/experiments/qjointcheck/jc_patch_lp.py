#!/usr/bin/env python3
"""jc_patch_lp.py -- builds two scripts in qjointcheck/ (everything outside qjointcheck/ stays untouched):
  qj_lp_recount.py : verbatim qjoint/qj_lp.py with OUT redirected to qjointcheck/ (the recount of 686 / 452 / 388)
  lp_qjc.py        : qhubcheck/lp_qhc.py plus MY implementation of Lemma P rows P1-P5 and row LIM (variant substring
                     JC / JCLIM), written from the statements of qjoint/REPORT.md section 4 with a brute-force
                     minimisation over the integer interval m in [max(0, u-(q-a)), min(u, 3-r)] instead of closed
                     forms, and a packing number D(a,3,2) computed by exhaustive search for a <= 9 (formula above)."""
import ast, shutil
from pathlib import Path
SP = Path.home()/'xs-campaigns/2026-11-07-sprint'
OUTD = SP/'qjointcheck'
# ---- 1. recount copy
s = (SP/'qjoint/qj_lp.py').read_text()
assert "OUT = SPRINT/'qjoint'" in s
s = s.replace("OUT = SPRINT/'qjoint'", "OUT = SPRINT/'qjointcheck'")
ast.parse(s); (OUTD/'qj_lp_recount.py').write_text(s)
for o in ('M', 'Mt'): shutil.copy(SP/'qjoint'/f'fm_tab_{o}.json', OUTD/f'fm_tab_{o}.json')
# ---- 2. own rows on lp_qhc.py
s = (SP/'qhubcheck/lp_qhc.py').read_text()
assert 'jc_rows' not in s
s = s.replace("OUT = SPRINT/'qhubcheck'", "OUT = SPRINT/'qjointcheck'")
NEW = '''def pack3(a):
    """D(a,3,2): the largest family of 3-subsets of an a-set pairwise meeting in <= 1 element.  Exhaustive
    branch-and-bound for a <= 9 (cached), the Schoenheim/Spencer formula beyond (and cross-checked below)."""
    if a < 3: return 0
    if a in PACK: return PACK[a]
    trip = list(itertools.combinations(range(a), 3))
    comp = [[len(set(t) & set(s)) <= 1 for s in trip] for t in trip]
    best = [0]
    def rec(i, chosen):
        if len(chosen) + (len(trip) - i) <= best[0]: return
        if i == len(trip):
            best[0] = max(best[0], len(chosen)); return
        if all(comp[i][j] for j in chosen): rec(i + 1, chosen + [i])
        rec(i + 1, chosen)
    if a <= 9: rec(0, []); PACK[a] = best[0]
    else:
        v = (a * ((a - 1) // 2)) // 3; PACK[a] = v - 1 if a % 6 == 5 else v
    return PACK[a]
PACK = {}

def jc_rows(types, q, a, ori, vec, lim_row):
    """Lemma P rows (P1-P5) and row LIM in the exact hub case A = a, my implementation.
    Non-full type (r, u, v): m = #full-met labels ranges over the integers of [max(0, u - (q - a)), min(u, 3 - r)];
    each term is replaced by its minimum over that interval (brute force).  Full type: all u labels are full-met."""
    def interval(r, u):
        lo = max(0, u - (q - a)); hi = min(u, 3 - r)
        assert lo <= hi, (r, u, q, a)
        return range(lo, hi + 1)
    def tmin(r, u, fn): return min(fn(m) for m in interval(r, u))
    top = fm_table(ori)[0]
    rows = [
        (vec(lambda r, u, v: comb(u, 2) if r == 3 else tmin(r, u, lambda m: comb(m, 2))), comb(a, 2)),                 # P1
        (vec(lambda r, u, v: 0 if r == 3 else tmin(r, u, lambda m: m * (u - m))), a * (q - a)),                        # P2
        (vec(lambda r, u, v: 0 if r == 3 else tmin(r, u, lambda m: comb(u - m, 2))), comb(q - a, 2)),                  # P3
        (vec(lambda r, u, v: (1 if u >= 3 else 0) if r == 3 else tmin(r, u, lambda m: 1 if m >= 3 else 0)), pack3(a)), # P4 full-met
        (vec(lambda r, u, v: 0 if r == 3 else tmin(r, u, lambda m: 1 if u - m >= 3 else 0)), pack3(q - a)),            # P4 hub-only
        (vec(lambda r, u, v: 0 if r == 3 else tmin(r, u, lambda m: r * m)), top[a] - 3 * a),                           # P5
    ]
    if lim_row:
        def is_lim(r, u): return r < 3 and u == (3 - r) + (q - a)
        if a == q: rows.append((vec(lambda r, u, v: u if is_lim(r, u) else 0), q))      # limit hubs label-disjoint
        else: rows.append((vec(lambda r, u, v: 1 if is_lim(r, u) else 0), 1))           # at most one limit hub
    return rows

def ucap(variant, r, slack):'''
s = s.replace('def ucap(variant, r, slack):', NEW, 1)
s = s.replace('import sys, json, time', 'import sys, json, time, itertools', 1)
s = s.replace("""    if hub:
        A_row = vec(lambda r, u, v: u if r == 3 else 0)
        if hub[0] == 'eq': EQ.append((A_row, hub[1]))
        else: LE.append((A_row, hub[1]))""", """    if hub:
        A_row = vec(lambda r, u, v: u if r == 3 else 0)
        if hub[0] == 'eq': EQ.append((A_row, hub[1]))
        else: LE.append((A_row, hub[1]))
        if 'JC' in variant and hub[0] == 'eq':
            LE.extend(jc_rows(types, q, hub[1], ori, vec, 'LIM' in variant))""")
s = s.replace("    if 'HUB2X' in variant: return [('eq', a) for a in range(0, q + 1)]",
              "    if 'HUB2X' in variant or 'JC' in variant: return [('eq', a) for a in range(0, q + 1)]")
s = s.replace("       'GstarN1HUB2DARKPKFM': SPRINT/'qhub/scan_GstarN1HUB2DARKMFMPK_q0_g75.json'}",
              "       'GstarN1HUB2DARKPKFM': SPRINT/'qhub/scan_GstarN1HUB2DARKMFMPK_q0_g75.json',\n"
              "       'GstarN1HUB2DARKPKFMJC': SPRINT/'qjoint/lp_qhc_scan_GstarN1HUB2DARKPKFMJOINTLIM.json',\n"
              "       'GstarN1HUB2DARKPKFMJCLIM': SPRINT/'qjoint/lp_qhc_scan_GstarN1HUB2DARKPKFMJOINTLIM.json'}")
s = s.replace("""    if mode == 'keys':
        keys = [tuple(k) for k in json.load(open(SPRINT/'lb76/g75_keys.json'))['feasible']]""",
              """    if mode in ('keys', 'lbkeys'):
        keys = [tuple(k) for k in json.load(open(SPRINT/'lb76/g75_keys.json'))['feasible']] if mode == 'keys' else \\
               [tuple(k) for k in json.load(open(SPRINT/'qhubcheck/lp_qhc_keysfull_GstarN1HUB2DARKPKFM.json'))['load_bearing']]""")
s = s.replace("""        if ref_file and ref_file.exists():
            ref = {tuple(k) for k in json.load(open(ref_file))['keys_still_feasible']}; mine = set(still)""",
              """        if mode == 'keys' and ref_file and ref_file.exists():
            ref = {tuple(k) for k in json.load(open(ref_file))['keys_still_feasible']}; mine = set(still)""")
s = s.replace("""            refd = json.load(open(ref_file))
            ref = {(tuple(s['state']), s['ori']) for s in refd['survivors']}""",
              """            refd = json.load(open(ref_file))
            if isinstance(refd, list): refd = dict(survivors=[dict(state=st, ori=o, k=k, ell=ell) for st, o, k, ell in refd])
            ref = {(tuple(s['state']), s['ori']) for s in refd['survivors']}""")
# the FM tables: lp_qhc reads OUT/fm_tab_{ori}.json -> now qjointcheck/ (copied above from qjoint = qhubcheck's own tables)
ast.parse(s); (OUTD/'lp_qjc.py').write_text(s)
# packing-number cross-check of the formula used by qjoint (D3) against exhaustive search
import importlib.util, sys
spec = importlib.util.spec_from_file_location('lp_qjc', OUTD/'lp_qjc.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
formula = lambda a: 0 if a < 3 else ((a * ((a - 1) // 2)) // 3 - (1 if a % 6 == 5 else 0))
ex = {a: m.pack3(a) for a in range(0, 10)}
print('exhaustive D(a,3,2) a=0..9:', ex, '; formula:', {a: formula(a) for a in range(0, 10)}, '; agree:', all(ex[a] == formula(a) for a in ex))
print('patched ok')
