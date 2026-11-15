#!/usr/bin/env python3
"""T4: polarity pass on a skeleton: replacing AND(L, R) by AND(L^1, R) / AND(L, R^1) / AND(L^1, R^1)
changes the product by R / L / L^R^1 (free when the complemented operand has >= 2 terms: XNOR).
For every output, the products used by that output only are re-polarised to minimise the output's
Huffman level (then Kraft sum); the change is folded into the output form.
    python3 polpass.py SKEL.json OUT.json"""
import sys, json, itertools, heapq
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from coversearch import bound, huff  # noqa

def kraft(F, arr, L=11):
    return sum(2.0 ** (arr[p] - L) for p in range(1, len(arr)) if (F >> p) & 1)

def polarity_pass(sk, n=8):
    ands = list(sk['ands']); outs = list(sk['outputs'])
    b, arr, ol = bound({'n': n, 'm': 8, 'ands': ands, 'outputs': outs}, n)
    users = {}
    for k, F in enumerate(outs):
        for j in range(len(ands)):
            if (F >> (1 + n + j)) & 1: users.setdefault(j, set()).add(k)
    # an AND also used inside other forms (operands) cannot be changed
    used_in_ops = set()
    for L, R in ands:
        for j in range(len(ands)):
            if ((L | R) >> (1 + n + j)) & 1: used_in_ops.add(j)
    for k in range(len(outs)):
        own = [j for j, u in users.items() if u == {k} and j not in used_in_ops]
        bestF, bestsc, bestv = outs[k], None, None
        def sc(F):
            terms = [arr[p] for p in range(1, len(arr)) if (F >> p) & 1]
            return (huff(terms, F & 1), kraft(F, arr))
        base = sc(outs[k])
        for combo in itertools.product(range(4), repeat=len(own)):
            F = outs[k]
            ok = True
            for j, v in zip(own, combo):
                L, R = ands[j]
                if v == 1: F ^= R
                elif v == 2: F ^= L
                elif v == 3: F ^= L ^ R ^ 1
                # complementing a single-term operand would need a NOT (+1 level): skip
                if v in (1, 3) and bin(L & ~1).count('1') < 2: ok = False
                if v in (2, 3) and bin(R & ~1).count('1') < 2: ok = False
            if not ok: continue
            s = sc(F)
            if bestsc is None or s < bestsc: bestF, bestsc, bestv = F, s, combo
        if bestv and any(bestv):
            for j, v in zip(own, bestv):
                L, R = ands[j]
                if v in (1, 3): L ^= 1
                if v in (2, 3): R ^= 1
                ands[j] = (L, R)
            outs[k] = bestF
    return {'n': n, 'm': 8, 'ands': ands, 'outputs': outs}

if __name__ == '__main__':
    d = json.load(open(sys.argv[1]))
    sk = {'n': 8, 'm': 8, 'ands': [(int(L, 16), int(R, 16)) for L, R in d['ands']], 'outputs': [int(F, 16) for F in d['outputs']]}
    b0, _, ol0 = bound(sk, 8)
    sk2 = polarity_pass(sk)
    b1, arr, ol1 = bound(sk2, 8)
    # verify function
    from boolflux import skeleton, core, targets
    tab, ft, ones = skeleton._form_tables(sk2)
    St = core.tables_from_values(8, 8, targets.aes_sbox())
    for k in range(8):
        if ft(sk2['outputs'][k]) ^ St[k] == ones: sk2['outputs'][k] ^= 1
    ok = all(ft(sk2['outputs'][k]) == St[k] for k in range(8))
    print(json.dumps({'before': [b0, ol0], 'after': [b1, ol1], 'ok': ok, 'kraft6': kraft(sk2['outputs'][6], arr)}))
    json.dump({'ands': [[hex(L), hex(R)] for L, R in sk2['ands']], 'outputs': [hex(F) for F in sk2['outputs']]}, open(sys.argv[2], 'w'))
