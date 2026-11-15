#!/usr/bin/env python3
"""Stage-1 span key and stage counts for circuits (H2's a28parse stages L/M/F).
key1 = canonical hash of span(1, x, stage-L products); key2 = same with stage-M products added.
usage: prefix_key.py FILE...   -> one line per file: L M F key1 key2 name"""
import sys, os, hashlib
sys.path.insert(0, os.path.expanduser('~/xcr-boolflux/nonlinear/boolflux/strategies/H2'))
import a28parse as AP


def canon(vecs):
    rows = []
    for v in vecs:
        for r in rows:
            if v ^ r < v:
                v ^= r
        if v:
            rows.append(v)
    # full RREF
    rows.sort(reverse=True)
    for i in range(len(rows)):
        for j in range(len(rows)):
            if i != j and (rows[j] >> (rows[i].bit_length() - 1)) & 1:
                rows[j] ^= rows[i]
    rows = sorted(rows)
    return hashlib.sha1(','.join('%x' % r for r in rows).encode()).hexdigest()[:12], len(rows)


for f in sys.argv[1:]:
    try:
        _, ANDS = AP.load(f)
    except Exception as e:
        print('ERR', os.path.basename(f), repr(e)[:80]); continue
    st = ''.join(A['stage'] for A in ANDS)
    base = [AP.ONE] + AP.BITS
    L = [A['out'] for A in ANDS if A['stage'] == 'L']
    M = [A['out'] for A in ANDS if A['stage'] == 'M']
    k1, d1 = canon(base + L)
    k2, d2 = canon(base + L + M)
    print(st.count('L'), st.count('M'), st.count('F'), k1, k2, f)
