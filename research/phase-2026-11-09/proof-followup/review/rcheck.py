#!/usr/bin/env python3
"""rcheck.py -- reviewer's own rule checks R1-R7 for a label configuration, and R8 / R8-int (LP / MILP on the checker's
case matrix with exact count rows).  Imports only rgeo (own) and the repository checker check_combined75 (for the rows).

Object format: dict(labels=[{'value', 'status'}], helpers=[{'mask', 'r', 'triples', 'labels'}]) (the pilot's witness
format; triples are 64-bit subsets of B indices, labels are slot indices).
"""
import itertools, sys
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.optimize import linprog, milp, LinearConstraint, Bounds
import rgeo

CHK = Path.home() / 'xor-circuit-research/lower-bound-proofs/mixcolumns-lb75-open-cases/checkers'
sys.path.insert(0, str(CHK))
import check_combined75 as CC  # noqa: E402

par = lambda v: bin(v).count('1') & 1


def family(obj, G, tree='path'):
    H = obj['helpers']; L = obj['labels']
    vs = []
    for i, hp in enumerate(H):
        for T in hp['triples']: vs.append(T | (1 << (64 + i)))
    for j, lab in enumerate(L):
        car = [i for i, hp in enumerate(H) if j in hp['labels']]
        if len(car) < 2: continue
        end = {i: G.idx[H[i]['mask'] ^ lab['value']] for i in car}
        if tree == 'path':
            car = sorted(car, key=lambda i: H[i]['mask'])
            edges = list(zip(car, car[1:]))
        else:   # star at the LAST carrier
            c0 = car[-1]; edges = [(c0, c) for c in car[:-1]]
        for i, k in edges:
            vs.append((1 << (64 + i)) | (1 << (64 + k)) | (1 << end[i]) | (1 << end[k]))
    return vs


def check(obj, G, a=None, d=None):
    H = obj['helpers']; L = obj['labels']; Bset = G.Bset
    out = {}
    masks = [hp['mask'] for hp in H]; vals = [lab['value'] for lab in L]
    out['R1'] = (len(set(masks)) == len(masks) and all(par(m) == 1 and m not in Bset and 0 < m < 2**32 for m in masks)
                 and len(set(vals)) == len(vals) and all(v != 0 and par(v) == 0 and v < 2**32 for v in vals))
    ok = all(len(set(hp['labels'])) == len(hp['labels']) and len(hp['labels']) >= 1 for hp in H)
    ok = ok and all((hp['mask'] ^ vals[j]) in Bset for hp in H for j in hp['labels'])
    out['R2'] = ok
    ok = True
    for hp in H:
        T = list(hp['triples']); r = hp['r']
        if len(T) != r or len(set(T)) != r or not (0 <= r <= 3): ok = False; continue
        for t in T:
            if bin(t).count('1') != 3: ok = False; continue
            x = 0
            for k in range(64):
                if t >> k & 1: x ^= G.B[k]
            if x != hp['mask']: ok = False
        if r == 3 and sorted(T) != sorted(G.trip.get(hp['mask'], [])): ok = False
    out['R3'] = ok
    full = [i for i, hp in enumerate(H) if hp['r'] == 3]
    atf = Counter(j for i in full for j in H[i]['labels'])
    ok = all(c <= 1 for c in atf.values())
    ok = ok and all((lab['status'] == 'F') == (atf.get(j, 0) == 1) for j, lab in enumerate(L))
    if a is not None: ok = ok and sum(lab['status'] == 'F' for lab in L) == a
    out['R4'] = ok
    out['R5'] = all(len(set(H[i]['labels']) & set(H[k]['labels'])) <= 1 for i, k in itertools.combinations(range(len(H)), 2))
    ok = True
    for j, lab in enumerate(L):
        anch = [i for i, hp in enumerate(H) if j in hp['labels'] and hp['r'] >= 1]
        if (lab['status'] == 'D') != (not anch): ok = False
        if lab['status'] == 'B' and atf.get(j, 0): ok = False
    if d is not None: ok = ok and sum(lab['status'] == 'D' for lab in L) == d
    out['R6'] = ok
    f1 = family(obj, G, 'path'); f2 = family(obj, G, 'star')
    out['R7'] = rgeo.rank(f1) == len(f1) and rgeo.rank(f2) == len(f2)
    out['R7_size'] = len(f1)
    out['all_R1_R7'] = all(out[k] for k in ('R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7'))
    return out


def counts_of(obj):
    return Counter((hp['r'], len(hp['labels'])) for hp in obj['helpers'])


class Rows:
    def __init__(self, key, a, d):
        b, cols, *_ = CC.matrix(tuple(key), ('eq', a), d)
        self.labels = [lab for lab, _ in cols]
        self.A = np.array([c for _, c in cols], dtype=float).T
        self.b = np.array(b, dtype=float)
        self.cls = {}
        for j, lab in enumerate(self.labels):
            if isinstance(lab, tuple) and lab[1] >= 1:
                self.cls.setdefault((lab[0], lab[1]), []).append(j)

    def count_rows(self, counts, exact=True):
        """returns (Aeq, beq) or None if a positive count sits on a class without columns."""
        n = len(self.labels); Ae = []; be = []
        allc = set(self.cls) | set(counts)
        for c in sorted(allc):
            v = counts.get(c, 0)
            if c not in self.cls:
                if v: return None
                continue
            if not exact and c not in counts: continue
            row = np.zeros(n); row[self.cls[c]] = 1.0; Ae.append(row); be.append(float(v))
        return Ae, be

    def lp(self, counts, exact=True):
        cr = self.count_rows(counts, exact)
        if cr is None: return 'deleted-class'
        Ae, be = cr
        n = len(self.labels)
        if exact:
            res = linprog(np.zeros(n), A_ub=self.A, b_ub=self.b, A_eq=np.array(Ae) if Ae else None, b_eq=np.array(be) if be else None,
                          bounds=[(0, None)] * n, method='highs')
        else:
            Aub = np.vstack([self.A] + [-np.array(r) for r in Ae]) if Ae else self.A
            bub = np.concatenate([self.b, -np.array(be)]) if Ae else self.b
            res = linprog(np.zeros(n), A_ub=Aub, b_ub=bub, bounds=[(0, None)] * n, method='highs')
        return int(res.status)

    def milp(self, counts, time_limit=60.0):
        cr = self.count_rows(counts, True)
        if cr is None: return 'deleted-class', None
        Ae, be = cr
        n = len(self.labels)
        cons = [LinearConstraint(self.A, -np.inf, self.b)]
        if Ae: cons.append(LinearConstraint(np.array(Ae), np.array(be), np.array(be)))
        res = milp(np.zeros(n), constraints=cons, integrality=np.ones(n), bounds=Bounds(np.zeros(n), np.full(n, np.inf)),
                   options=dict(time_limit=time_limit))
        viol = None
        if res.x is not None:
            x = np.round(res.x)
            viol = int(np.sum(self.A @ x > self.b + 1e-9))
            if Ae: viol += int(np.sum(np.abs(np.array(Ae) @ x - np.array(be)) > 1e-9))
        return int(res.status), viol
