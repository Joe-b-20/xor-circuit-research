"""P5: like basisneed.py, for skeletons whose pure-linear operand set O has 5 forms: every basis
B of 4 forms inside O (others cost gates), exact cost with only B free.

usage: python3 basisneed5.py SKEL.json SPEC_ALL.json --depth D --maxrelaxed C --out OUT.json
"""
import argparse, itertools, json, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from basisneed import LIN, rank, cost  # noqa


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('skel'); ap.add_argument('spec'); ap.add_argument('--depth', type=int, required=True)
    ap.add_argument('--maxrelaxed', type=int, default=17); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    sk = json.load(open(a.skel)); spec = json.load(open(a.spec))
    dist = Counter(); res = []
    for i, s in enumerate(sk):
        if s['cost'] > a.maxrelaxed: continue
        O = sorted({LIN[int(x, 16)] for l, x, y in s['ands'] for x in (x, y) if int(x, 16) in LIN})
        if len(O) != 5: continue
        for B in itertools.combinations(O, 4):
            if rank(list(B)) < 4: continue
            c, k = cost(s, list(B), spec, a.depth)
            dist[c] += 1
            res.append({'rank': i, 'basis_masks': list(B), 'cost': c, 'kind': k, 'ands': s['ands']})
    res.sort(key=lambda r: r['cost'])
    print('cost distribution over (skeleton, basis)', sorted(dist.items()))
    for r in res[:10]: print(r['cost'], r['kind'], r['basis_masks'], r['ands'])
    json.dump(res, open(a.out, 'w'))


if __name__ == '__main__':
    sys.exit(main())
