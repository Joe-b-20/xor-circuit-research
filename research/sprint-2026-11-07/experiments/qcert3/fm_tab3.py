#!/usr/bin/env python3
"""qcert3/fm_tab3.py -- recomputation of finite fact FM (the rank(C_l) tables for the labels f + c), standard library only.

Definitions (PROOF.md sections 1, 4; F6; qreal/REPORT.md section 3): boundary B = the 32 unit vectors and the 32 rows
(orientation M) or columns (M^T) of the MixColumns matrix, parsed here from the repository's
circuits/aes-mixcolumns/aes-mixcolumns.mat.txt; a *full value* f has exactly three 3-subsets of B with XOR f (F3);
for an even value l the space C_l is spanned by the forms E_l + sum_{b in D} B_b over the 2- and 4-subsets D of B with
XOR l, so rank(C_l) = 1 + rank{D_0 + D : D a form of l} (F6: at most 7).  Finite fact FM: the histogram of rank(C_l)
over the DISTINCT labels l = f + c (f full, c in B), and the tables
    top(a)  = the sum of the a largest ranks,     top3(a) = the sum of the a largest values of min(3, rank(C_l) - 1),
which the chord rows FM7 / FM9 of the local system use.  Own code throughout (matrix parse, GF(2) elimination with
fully reduced rows, form enumeration); the boundary is compared once with the package's stress.BOUNDARY (copy
stress_pkg.py) and the results with qreal/fullmet_{ori}.json and qhubcheck/fm_tab_{ori}.json.
usage: python3 fm_tab3.py            (writes fm_tab3.json)
"""
import sys, json, itertools, time
from collections import Counter, defaultdict
from pathlib import Path
SPRINT = Path.home() / 'xs-campaigns/2026-11-07-sprint'
HERE = SPRINT / 'qcert3'
MAT = Path.home() / 'xor-circuit-research/circuits/aes-mixcolumns/aes-mixcolumns.mat.txt'


def read_boundary(ori):
    lines = [l.split() for l in open(MAT) if l.strip()]
    assert lines[1] == ['32', '32'], lines[:2]
    rows = [[int(x) for x in l] for l in lines[2:34]]
    assert len(rows) == 32 and all(len(r) == 32 and all(x in (0, 1) for x in r) for r in rows)
    if ori == 'M': vecs = [sum(b << j for j, b in enumerate(r)) for r in rows]
    else: vecs = [sum(rows[i][j] << i for i in range(32)) for j in range(32)]
    return [1 << i for i in range(32)] + vecs


class Reduced:
    """GF(2) basis kept in reduced echelon form (every stored vector has zeros at the other pivots)."""
    def __init__(self): self.vecs = []; self.pivs = []
    def reduce(self, v):
        for p, w in zip(self.pivs, self.vecs):
            if (v >> p) & 1: v ^= w
        return v
    def add(self, v):
        v = self.reduce(v)
        if not v: return False
        p = v.bit_length() - 1
        self.vecs = [w ^ v if (w >> p) & 1 else w for w in self.vecs]
        self.vecs.append(v); self.pivs.append(p); return True
    def rank(self): return len(self.vecs)


def rank_of(vectors):
    R = Reduced()
    for v in vectors: R.add(v)
    return R.rank()


def main():
    out = {}
    try:
        sys.path.insert(0, str(HERE)); from stress_pkg import BOUNDARY   # noqa: E402
    except Exception:  # noqa: BLE001
        BOUNDARY = None
    for ori in ('M', 'Mt'):
        t0 = time.time()
        B = read_boundary(ori)
        assert len(set(B)) == 64 and all(bin(v).count('1') % 2 == 1 for v in B), 'boundary not 64 distinct odd masks'
        if BOUNDARY is not None: assert BOUNDARY[ori] == B, 'boundary differs from the package stress.BOUNDARY'
        pairs = {}
        for i, j in itertools.combinations(range(64), 2):
            v = B[i] ^ B[j]; assert v not in pairs, 'F2 fails'; pairs[v] = (i, j)
        assert len(pairs) == 2016
        trip = defaultdict(list)
        for i, j, k in itertools.combinations(range(64), 3): trip[B[i] ^ B[j] ^ B[k]].append((i, j, k))
        f3 = Counter(len(t) for t in trip.values())
        full = sorted(v for v, t in trip.items() if len(t) == 3)
        assert len(full) == {'M': 80, 'Mt': 112}[ori], (ori, len(full))
        labels = sorted({f ^ c for f in full for c in B})
        assert all(bin(l).count('1') % 2 == 0 for l in labels)
        L = set(labels)
        forms = defaultdict(list)
        for v, (i, j) in pairs.items():
            if v in L: forms[v].append((1 << i) | (1 << j))
        for S in itertools.combinations(range(64), 4):
            v = B[S[0]] ^ B[S[1]] ^ B[S[2]] ^ B[S[3]]
            if v in L: forms[v].append((1 << S[0]) | (1 << S[1]) | (1 << S[2]) | (1 << S[3]))
        rank = {}
        for l in labels:
            fs = forms[l]; assert fs, 'a label f + c without a form'
            rank[l] = 1 + rank_of([fs[0] ^ g for g in fs[1:]])
        # the three forms T (+/-) {c} of f itself give rank >= 3; F6 gives <= 7
        for f in full:
            for ci, c in enumerate(B):
                l = f ^ c; fl = set(forms[l])
                own = []
                for T in trip[f]:
                    m = (1 << T[0]) | (1 << T[1]) | (1 << T[2]); m ^= (1 << ci)
                    assert m in fl, 'the form T + {c} of f + c is missing'
                    own.append(m)
                assert len(set(own)) == 3 and rank_of([own[0] ^ own[1], own[0] ^ own[2]]) == 2
        assert all(3 <= r <= 7 for r in rank.values())
        hist = Counter(rank.values())
        ranks = sorted(rank.values(), reverse=True)
        top = [0]; top3 = [0]
        for r in ranks[:20]: top.append(top[-1] + r)
        for r in sorted((min(3, r - 1) for r in ranks), reverse=True)[:20]: top3.append(top3[-1] + r)
        per_f_max = Counter(max(rank[f ^ c] for c in B) for f in full)
        per_f_ge4 = Counter(sum(1 for c in B if rank[f ^ c] >= 4) for f in full)
        print(f'{ori}: F3 {dict(sorted(f3.items()))}; {len(full)} full values; {len(labels)} distinct labels f + c; rank(C_l) histogram '
              f'{dict(sorted(hist.items()))}; top[:12] {top[:12]}; top3[:12] {top3[:12]}; per full value: max rank {dict(sorted(per_f_max.items()))}, '
              f'#labels with rank >= 4 {dict(sorted(per_f_ge4.items()))}; {time.time()-t0:.0f}s', flush=True)
        rec = dict(ori=ori, full_values=len(full), labels=len(labels), hist={str(k): v for k, v in sorted(hist.items())}, top=top, top3=top3,
                   per_full_max_rank={str(k): v for k, v in sorted(per_f_max.items())}, per_full_labels_rank_ge4={str(k): v for k, v in sorted(per_f_ge4.items())})
        for name, path in (('qreal', SPRINT / f'qreal/fullmet_{ori}.json'), ('qhubcheck', SPRINT / f'qhubcheck/fm_tab_{ori}.json')):
            d = json.load(open(path)); n = min(len(d['top']), len(top))
            same = ({int(k): v for k, v in d['hist'].items()} == dict(hist)) and d['top'][:n] == top[:n] and d['top3'][:n] == top3[:n]
            print(f'{ori}: compared with {name} {path.name}: histogram and top / top3 identical: {same}')
            assert same, (ori, name)
            rec[f'identical_to_{name}'] = same
        out[ori] = rec
    json.dump(out, open(HERE / 'fm_tab3.json', 'w'), indent=1)
    print('FM TABLES RECOMPUTED: identical to qreal and qhubcheck in both orientations')


if __name__ == '__main__':
    main()
