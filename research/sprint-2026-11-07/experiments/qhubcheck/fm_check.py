#!/usr/bin/env python3
"""qhubcheck/fm_check.py -- independent recomputation of qreal's finite fact FM tables (top, top3), which feed the
FM7 / FM9 chord rows of qh_lp.py (present in every qhub scan variant).  Definitions (qreal/fullmet.py header, F6):
for every full value f and boundary element c the label l = f + c has C_l = span{ E_l + sum_{b in D} B_b : D a 2- or
4-subset of B with XOR l }; rank(C_l) = 1 + rank of the differences of the forms.  top[a] = sum of the a largest
ranks over the DISTINCT labels of the form f + c; top3[a] = sum of the a largest values of min(3, rank - 1).
Row FM7 (qreal): at a full-met label l (met by f through f-c), W_l + Y_l <= rank(C_l) (L7* per label), so
W + y_1 <= 7 (q - A) + top(A); FM9: Z <= 3 (q - A) + top3(A); both linearized by the chords of the concave top tables.
Output: fm_tab_{ori}.json (own tables) and a comparison with qreal/fullmet_{ori}.json.
"""
import sys, json, itertools, time
from collections import defaultdict, Counter
from pathlib import Path
sys.path.insert(0, str(Path.home()/'xs-campaigns/2026-11-07-sprint/qhubcheck'))
from h2_check import boundary, rank_of  # noqa: E402
OUT = Path.home()/'xs-campaigns/2026-11-07-sprint/qhubcheck'
QREAL = Path.home()/'xs-campaigns/2026-11-07-sprint/qreal'

def main(ori):
    t0 = time.time()
    B = boundary(ori)
    trip = Counter()
    for i, j, k in itertools.combinations(range(64), 3): trip[B[i] ^ B[j] ^ B[k]] += 1
    full = sorted(v for v, c in trip.items() if c == 3)
    labels = {f ^ c for f in full for c in B}
    forms = defaultdict(list)
    for i, j in itertools.combinations(range(64), 2):
        v = B[i] ^ B[j]
        if v in labels: forms[v].append((1 << i) | (1 << j))
    for i, j, k, m in itertools.combinations(range(64), 4):
        v = B[i] ^ B[j] ^ B[k] ^ B[m]
        if v in labels: forms[v].append((1 << i) | (1 << j) | (1 << k) | (1 << m))
    rank = {}
    for l in labels:
        fs = forms.get(l, [])
        rank[l] = (1 + rank_of([fs[0] ^ g for g in fs[1:]])) if fs else 0
    hist = Counter(rank.values())
    ranks = sorted(rank.values(), reverse=True)
    top = [0]; top3 = [0]
    for v in ranks: top.append(top[-1] + v)
    for v in sorted((min(3, r - 1) for r in ranks), reverse=True): top3.append(top3[-1] + v)
    top = top[:20]; top3 = top3[:20]
    print(f'{ori}: {len(full)} full values, {len(labels)} distinct labels f + c; rank(C_l) histogram {dict(sorted(hist.items()))}; '
          f'max rank {max(ranks)}; top[:15] {top[:15]}; top3[:15] {top3[:15]}; {time.time()-t0:.0f}s')
    json.dump(dict(ori=ori, hist={str(k): v for k, v in hist.items()}, top=top, top3=top3), open(OUT/f'fm_tab_{ori}.json', 'w'))
    try:
        d = json.load(open(QREAL/f'fullmet_{ori}.json'))
        same = d['top'][:15] == top[:15] and d['top3'][:15] == top3[:15]
        same_h = {int(k): v for k, v in d['hist'].items()} == dict(hist)
        print(f'{ori}: compared with qreal fullmet_{ori}.json: top tables identical {same}; rank histogram identical {same_h} (qreal {d["hist"]})')
    except Exception as e:
        print(f'{ori}: qreal table not compared: {e}')

if __name__ == '__main__':
    for o in (sys.argv[1].split(',') if len(sys.argv) > 1 else ['M', 'Mt']): main(o)
