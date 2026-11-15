#!/usr/bin/env python3
"""T4: generalised rank-2 merge scan for any AD-4 circuit whose last-level ANDs are
(Y-side of AND level 3) x (x-affine side).  A merge of two products U_a w_a + U_b w_b of the same
output (both used by that output only) is (U_a + w_b)(U_b + w_a) with junk U_a U_b + w_a w_b.
Merges in different outputs whose x-junk is equal modulo the front span share one x-junk AND.
Lists residue classes with >= 2 merges from distinct outputs, d-junk status (U_a U_b in front span).
    python3 genscan.py FILE"""
import sys, itertools, json, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from rank2 import Span, load, analyse, ONES  # noqa
from chain import lin, wedge, qform, Red  # noqa
from boolflux import core  # noqa


def products_by_output(c, T, la, AD):
    n = c.n; res = []
    users = collections.Counter()
    per = []
    for o in c.outputs:
        cone = set(); st = [o]; prods = []
        while st:
            s = st.pop()
            if s < n or s in cone: continue
            cone.add(s)
            op, a, b = c.gates[s - n]
            if op in core.NONLINEAR_OPS:
                if la[s] == AD: prods.append(s)
                continue
            st += [a, b]
        per.append(prods)
        for s in set(prods): users[s] += 1
    return per, users


if __name__ == '__main__':
    c = load(sys.argv[1]); n = c.n
    T, lg, la, fa, ba, V, X = analyse(c)
    AD = max(la[o] for o in c.outputs)
    per, users = products_by_output(c, T, la, AD)
    S1 = Red([qform(T[s]) for s in fa if la[s] == 1])
    merges = []
    for k, prods in enumerate(per):
        own = [s for s in prods if users[s] == 1]
        info = []
        for s in own:
            op, a, b = c.gates[s - n]
            if la[a] == AD - 1 and la[b] < AD - 1: y, w = a, b
            elif la[b] == AD - 1 and la[a] < AD - 1: y, w = b, a
            else: continue
            info.append((s, T[y], lin(T[w]), lg[y]))
        for (s1, y1, w1, l1), (s2, y2, w2, l2) in itertools.combinations(info, 2):
            q = wedge(w1, w2)
            merges.append({'k': k, 'p': (s1, s2), 'res': S1.red(q), 'dfree': (y1 & y2) in V, 'ylev': (l1, l2)})
    byres = collections.defaultdict(list)
    for mg in merges: byres[mg['res']].append(mg)
    print('outputs', len(per), 'products per output', [len(p) for p in per], 'shared products', sum(1 for s, u in users.items() if u > 1))
    print('merges', len(merges))
    for r, L in byres.items():
        ks = {m_['k'] for m_ in L}
        if len(ks) >= 2:
            print(json.dumps({'outputs': sorted(ks), 'merges': [(m_['k'], m_['p'], m_['dfree'], m_['ylev']) for m_ in L]}))
