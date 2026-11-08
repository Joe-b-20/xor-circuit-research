#!/usr/bin/env python3
"""patch_qj_lp.py -- turn a verbatim copy of qhubcheck/lp_qhc.py (qj_lp.py) into the qjoint LP: variant substring
JOINT = exact integer hub cases A = a (a = 0..q) and, in each case, the label-class rows P1-P5 and the limit-hub
row LIM of qjoint/REPORT.md section 4.  Run once; idempotent check by the marker string."""
import ast
from pathlib import Path
p = Path.home()/'xs-campaigns/2026-11-07-sprint/qjoint/qj_lp.py'
s = p.read_text()
assert 'joint_rows' not in s, 'already patched'
s = s.replace('"""qhubcheck/lp_qhc.py -- independent LP', '"""qjoint/qj_lp.py -- qhubcheck/lp_qhc.py (rows unchanged) plus the JOINT rows of qjoint/REPORT.md section 4\n'
              '(variant substring JOINT: exact integer hub cases A = a, a = 0..q; in each case the label-class rows P1-P5 and the\n'
              'limit-hub row LIM, see joint_rows()).  Original header follows.\n\nqhubcheck/lp_qhc.py -- independent LP', 1)
s = s.replace("OUT = SPRINT/'qhubcheck'", "OUT = SPRINT/'qjoint'")
NEW = '''def D3(a):
    """largest family of subsets of size >= 3 of an a-set pairwise meeting in <= 1 element = packing number of triples
    D(a,3,2) (a family of >= 3-sets pairwise meeting in <= 1 stays one after shrinking each set to 3 elements):
    Schoenheim/Johnson bound floor(a/3 * floor((a-1)/2)), minus 1 when a = 5 mod 6; exact for all a (Spencer 1968)."""
    if a < 3: return 0
    v = (a * ((a - 1) // 2)) // 3
    return v - 1 if a % 6 == 5 else v

def joint_rows(types, q, a, ori, vec):
    """rows of qjoint/REPORT.md section 4 in the exact hub case A = a (0 <= a <= q).
    For a non-full type (r,u,v): m = number of full-met labels, m in [m_lb, m_ub] = [max(0, u-(q-a)), min(u, 3-r)]
    (row HUB2 / Lemma H2); e = u - m hub-only labels.
    P1: pairs of full-met labels co-occur at most once (Lemma 4.6); a full helper's labels are all full-met.
    P2: (full-met, hub-only) pairs co-occur at most once; m(u-m) is concave in m, minimal at an end of the interval.
    P3: hub-only pairs co-occur at most once.
    P4: the >= 3-subsets of one class carried by distinct helpers pairwise meet in <= 1 element: at most D3(class size).
    P5: at a full-met label l, 3 + sum_{hubs at l} r_i <= rank(C_l) (proof of (L7) / FM7), summed over the a labels.
    LIM: a type with u = (3 - r) + (q - a) is a limit hub: all q - a hub-only labels and 3 - r full-met labels.
         a <= q - 2: two limit hubs would share >= 2 labels (Lemma 4.6): at most one.
         a = q - 1 / a = q: finite fact J1 (qj_limit.py): two limit hubs share no missing label; so at most one when
         q - a = 1, and label-disjoint (sum u n <= q) when a = q."""
    rows = []
    def mlb(r, u): return max(0, u - (q - a))
    def mub(r, u): return min(u, 3 - r)
    nf = lambda r: r < 3
    rows.append((vec(lambda r, u, v: (comb(mlb(r, u), 2) if nf(r) else comb(u, 2))), comb(a, 2)))                       # P1
    rows.append((vec(lambda r, u, v: (min(mlb(r, u) * (u - mlb(r, u)), mub(r, u) * (u - mub(r, u))) if nf(r) else 0)), a * (q - a)))   # P2
    rows.append((vec(lambda r, u, v: (comb(u - mub(r, u), 2) if nf(r) else 0)), comb(q - a, 2)))                        # P3
    rows.append((vec(lambda r, u, v: ((1 if mlb(r, u) >= 3 else 0) if nf(r) else (1 if u >= 3 else 0))), D3(a)))         # P4 full-met
    rows.append((vec(lambda r, u, v: ((1 if u - mub(r, u) >= 3 else 0) if nf(r) else 0)), D3(q - a)))                   # P4 hub-only
    top, top3 = fm_table(ori)
    rows.append((vec(lambda r, u, v: (r * mlb(r, u) if nf(r) else 0)), top[a] - 3 * a))                                  # P5
    if 'LIM' in VARIANT[0]:
        lim = lambda r, u: nf(r) and u == (3 - r) + (q - a)
        if a == q: rows.append((vec(lambda r, u, v: (u if lim(r, u) else 0)), q))                                        # LIM, a = q
        else: rows.append((vec(lambda r, u, v: (1 if lim(r, u) else 0)), 1))                                             # LIM, a < q
    return rows

def ucap(variant, r, slack):'''
s = s.replace('def ucap(variant, r, slack):', NEW, 1)
s = s.replace("""    if hub:
        A_row = vec(lambda r, u, v: u if r == 3 else 0)
        if hub[0] == 'eq': EQ.append((A_row, hub[1]))
        else: LE.append((A_row, hub[1]))""", """    if hub:
        A_row = vec(lambda r, u, v: u if r == 3 else 0)
        if hub[0] == 'eq': EQ.append((A_row, hub[1]))
        else: LE.append((A_row, hub[1]))
        if 'JOINT' in variant and hub[0] == 'eq':
            LE.extend(joint_rows(types, q, hub[1], ori, vec))""")
s = s.replace("    if 'HUB2X' in variant: return [('eq', a) for a in range(0, q + 1)]",
              "    if 'HUB2X' in variant or 'JOINT' in variant: return [('eq', a) for a in range(0, q + 1)]")
s = s.replace("       'GstarN1HUB2DARKPKFM': SPRINT/'qhub/scan_GstarN1HUB2DARKMFMPK_q0_g75.json'}",
              "       'GstarN1HUB2DARKPKFM': SPRINT/'qhub/scan_GstarN1HUB2DARKMFMPK_q0_g75.json',\n"
              "       'GstarN1HUB2DARKPKFMJOINT': SPRINT/'qhubcheck/lp_qhc_scan_GstarN1HUB2DARKPKFM.json',\n"
              "       'GstarN1HUB2DARKPKFMJOINTLIM': SPRINT/'qhubcheck/lp_qhc_scan_GstarN1HUB2DARKPKFM.json'}")
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
ast.parse(s)
p.write_text(s)
print('patched ok')
