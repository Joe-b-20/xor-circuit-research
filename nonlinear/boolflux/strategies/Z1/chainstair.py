#!/usr/bin/env python3
"""Does the output staircase have a NESTED optimal chain (C_1 < C_2 < ... < C_8, |supp C_k| = d_k)?
If so print one: at each step the output combination added and the last-layer ANDs it brings in.
usage: chainstair.py FILE..."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import staircode as SC


def run(f):
    r = SC.core_and_code(f)
    L, cols = r['Lidx'], r['cols']
    prof = SC.code_profile(cols)
    d = prof['d']
    sup = {}
    for c in range(1, 256):
        s = 0
        for j, v in enumerate(cols):
            if bin(c & v).count('1') & 1:
                s |= 1 << j
        sup[c] = s

    def span_add(sp, c):
        return sp | {x ^ c for x in sp} | {c}

    best = None

    def dfs(k, sp, s, path):
        nonlocal best
        if best: return
        if k == 8:
            best = path; return
        for c in range(1, 256):
            if c in sp: continue
            s2 = s | sup[c]
            if bin(s2).count('1') == d[k]:
                dfs(k + 1, span_add(sp, c), s2, path + [(c, s2 & ~s)])
                if best: return
    dfs(0, set(), 0, [])
    name = os.path.basename(f)
    print(name, 'E', r['E'], 'K', len(L), 'd', d)
    if not best:
        print('   no nested optimal chain'); return
    for k, (c, new) in enumerate(best):
        ands = [L[j] for j in range(len(L)) if (new >> j) & 1]
        print('   step %d: add output comb 0x%02x, new ANDs %s (cost %d, total %d)' % (k + 1, c, ands, len(ands), r['E'] + d[k]))


for f in sys.argv[1:]:
    run(f)
