import sys, json
sys.path.insert(0, '.'); sys.path.insert(0, '../../..')
from coversearch import bound
d = json.load(open(sys.argv[1]))
sk = {'n': 8, 'm': 8, 'ands': [(int(L, 16), int(R, 16)) for L, R in d['ands']], 'outputs': [int(F, 16) for F in d['outputs']]}
b, arr, ol = bound(sk, 8)
for k in map(int, sys.argv[2:]):
    F = sk['outputs'][k]
    terms = sorted([arr[p] for p in range(1, len(arr)) if (F >> p) & 1], reverse=True)
    print('out', k, 'level', ol[k], 'terms', len(terms), 'levels', terms, 'kraft@11', sum(2.0 ** (t - 11) for t in terms))
