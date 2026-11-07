#!/usr/bin/env python3
"""Where does the number 74 enter?  Exact, standard-library arithmetic on the package data.

(1) For every oriented claim at G=74 (CERTIFICATES75.json), which of the three exit conditions
    k > S_e, ell > S_o, k+ell > budget   (budget = a+b+2G-192)
    closes it, and by what margin.  A margin of exactly 1 on the k+ell route means that the same
    local bounds would fail at G=75, where the budget is 2 larger.
(2) For G = 73..77: size of the scalar domain, the initial gap budget-(l_e+l_o) that the local
    systems must close, and how many states cannot be closed by the k+ell route at all because
    S_e+S_o <= budget (then only k>S_e or ell>S_o can work).
"""
import json
from collections import Counter
from math import comb
from pathlib import Path

PKG = Path.home()/'xs-campaigns/2026-11-07-sprint/lb76/pkg_copy/source/lower_bounds/checks'

def low(h, y):
    return next(s for s in range(65) if 2*h+y+max(s, comb(s, 2)) >= 32)

def scalar_states(G):
    for a in range(24, G-44):
        for Y in range(G-31-a):
            he = G-32-a-Y
            for b in range(24, G-31):
                for V in range(Y+1):
                    ho = G-32-b-V
                    if ho < 0 or ho+Y < 13: continue
                    Se = min(3*he+2*V+Y-32, 2*b-a+G-96+V)
                    So = min(3*ho+2*Y+V-32, 2*a-b+G-96+Y)
                    if min(Se, So) < 0: continue
                    le, lo = low(he, Y), low(ho, V); budget = a+b+2*G-192
                    if le <= Se and lo <= So and le+lo <= budget:
                        yield (a, b, Y, V, he, ho, le, lo, Se, So, budget)

def main():
    data = json.loads((PKG/'CERTIFICATES75.json').read_text())
    assert data['gates_excluded'] == 74
    route = Counter(); margin_sum = Counter(); kl_only_margin = Counter()
    both = 0
    for c in data['claims']:
        a, b, Y, V, he, ho, le, lo, Se, So, budget = c['state']
        k, l = c['lower_even'], c['lower_odd']
        r = []
        if k > Se: r.append('k>Se')
        if l > So: r.append('l>So')
        if k+l > budget: r.append('k+l>budget')
        route[tuple(r)] += 1
        if r == ['k+l>budget']:
            kl_only_margin[k+l-budget] += 1
    print('G=74 oriented claims:', len(data['claims']))
    print('exit routes:', dict(route))
    print('margin k+l-budget when ONLY the k+l route closes the claim:', sorted(kl_only_margin.items()))
    # would the same (k,l) still close the claim at budget+2 (one more gate, caps unchanged)?
    still = sum(1 for c in data['claims'] if c['lower_even'] > c['state'][8] or c['lower_odd'] > c['state'][9] or c['lower_even']+c['lower_odd'] > c['state'][10]+2)
    print('claims whose (k,l) would still exceed budget+2 or a cap (naive +1 gate):', still)
    print()
    for G in range(73, 78):
        st = list(scalar_states(G))
        gaps = Counter(s[10]-(s[6]+s[7]) for s in st)
        no_kl = sum(1 for s in st if s[8]+s[9] <= s[10])
        print(f'G={G}: scalar states {len(st)}, oriented claims {2*len(st)}; '
              f'initial gap budget-(le+lo) histogram {sorted(gaps.items())}; '
              f'states where Se+So<=budget (k+l route impossible): {no_kl}')
        ab = Counter((s[0], s[1]) for s in st)
        print('   (a,b) range:', min(ab), '..', max(ab), '; Y range', min(s[2] for s in st), '..', max(s[2] for s in st),
              '; budget range', min(s[10] for s in st), '..', max(s[10] for s in st))

if __name__ == '__main__':
    main()
