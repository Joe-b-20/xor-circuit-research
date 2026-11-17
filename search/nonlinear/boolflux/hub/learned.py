"""Learned launch scores for the hub (--policy learned, 2026-11-17).

One feature function, used both offline (replay of a finished campaign: archive/index.jsonl + runs/*.json) and
online (the scheduler), so the model is trained on exactly what the scheduler sees at a launch.

    state = State(function, ref_points)        # archive replay: cells, front, front-add flags, attempts
    state.add_record(r)                        # every archive record in admission order (seeds included)
    state.add_launch(op, target_id, t)         # every job launch (attempt counts per tuple / structure)
    x = state.features(op, target_id, t)       # the feature vector of a candidate launch (FEATS order)
    m = Model.load(path); m.score(op, x)       # predicted front adds per CPU second

Label of a job (offline): number of its admissions that were "front adds" (not weakly dominated by the front
of all earlier records).  CPU of a job: process CPU from os.wait4 (stats proc_cpu_s)
when logged, else the operator's cpu_s, else wall_s.
The model: one L2 logistic regression per operator for P(job has >= 1 front add), times the operator's mean
adds per adding job, divided by the operator's mean CPU s (all from the training data; see Model).
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

FEATS = ['bias', 'inv', 'newcode', 'a28', 'a29_31', 'a32_35', 'ad3', 'ad5p', 'on_front',
         'dG_class', 'dGD_class', 'n_class', 'log_age', 'age_lt300', 'att1', 'att2', 'att3p', 'log_att_all',
         'satt', 'o_seed', 'o_polish', 'o_pull', 'o_join', 'o_ingest', 'o_trb', 'is_add',
         'log_elapsed', 'log_since_add', 'log_since_class_add', 'frac_polished', 'refdef', 'refdef_none']
KOPS = ('polish', 'pull')


def leq(u, m):
    return all(a <= b for a, b in zip(u, m))


def pareto(pts):
    out = []
    for p in sorted(set(pts)):
        if not any(leq(q, p) for q in out): out.append(p)
    return out


def klass(m, front):
    """front-add class of tuple m against a front: None (weakly dominated), 'A', 'AD', 'G', 'GD'"""
    if any(leq(q, m) for q in front): return None
    A, AD, G, GD = m
    if not any(q[0] <= A and q[1] <= AD for q in front):
        return 'A' if any(q[1] <= AD for q in front) else 'AD'
    box = [q[2] for q in front if q[0] <= A and q[1] <= AD and q[3] <= GD]
    return 'GD' if not box else 'G'


_PAT = re.compile(r'-a(\d+)-ad(\d+)-g(\d+)-gd(\d+)-')


def ref_points(circuits_dir, function):
    """(A, AD, G, GD) of the published circuits of the OTHER direction (the forward set is the inverse
    seeds' reference; transport keeps A and AD).  Parsed from the file names."""
    other = 'aes-sbox' if function == 'aes-invsbox' else 'aes-invsbox'
    out = []
    for f in sorted((Path(circuits_dir) / other).glob('*.circ.txt')):
        m = _PAT.search(f.name)
        if m: out.append(tuple(int(x) for x in m.groups()))
    return out


class State:
    def __init__(self, function='aes-sbox', refs=(), newcode=True):
        self.inv = 1.0 if function == 'aes-invsbox' else 0.0
        self.newcode = 1.0 if newcode else 0.0
        self.refs = list(refs)
        self.cells = {}            # (A, AD, GD) -> min G over all records so far
        self.front = []            # pareto of the cells
        self.rec = {}              # id -> (tuple, t_admit, operator, skey, is_add)
        self.att = {}              # (op, tuple) -> launches
        self.att_all = {}          # tuple -> kernel-op launches
        self.satt = {}             # (op, skey) -> launches
        self.t0 = None             # first launch
        self.last_add = None       # t of the last front add after t0
        self.class_add = {}        # (A, AD) -> t of the last front add
        self.polished = set()      # tuples with >= 1 polish

    def add_record(self, r):
        m = (r['A'], r['AD'], r['G'], r['GD']); t = r.get('t_admit') or 0.0
        c = klass(m, self.front) if r.get('operator') != 'seed' else None
        self.rec[r['id']] = (m, t, r.get('operator') or '?', r.get('skey') or r['id'], c is not None)
        if c is not None and self.t0 is not None and t >= self.t0:
            self.last_add = t; self.class_add[(m[0], m[1])] = t
        k = (m[0], m[1], m[3]); g = self.cells.get(k)
        if g is None or m[2] < g:
            self.cells[k] = m[2]
            self.front = pareto([(a, ad, gg, gd) for (a, ad, gd), gg in self.cells.items()])
        return c

    def add_launch(self, op, tid, t):
        if self.t0 is None: self.t0 = t
        r = self.rec.get(tid)
        if r is None: return
        m = r[0]
        self.att[(op, m)] = self.att.get((op, m), 0) + 1
        if op in KOPS: self.att_all[m] = self.att_all.get(m, 0) + 1
        self.satt[(op, r[3])] = self.satt.get((op, r[3]), 0) + 1
        if op == 'polish': self.polished.add(m)

    def features(self, op, tid, t):
        r = self.rec.get(tid)
        if r is None: return None
        m, ta, origin, sk, is_add = r
        A, AD, G, GD = m
        fr = self.front
        cls = [q for q in fr if q[0] == A and q[1] == AD]
        dG = G - min((q[2] for q in cls), default=G); dGD = GD - min((q[3] for q in cls), default=GD)
        age = max(0.0, t - ta)
        a = self.att.get((op, m), 0)
        t0 = self.t0 if self.t0 is not None else t
        el = max(0.0, t - t0)
        sl = max(0.0, t - (self.last_add if self.last_add is not None else t0))
        sc = max(0.0, t - self.class_add.get((A, AD), t0))
        nfr = max(1, len(fr)); fp = sum(1 for q in fr if q in self.polished) / nfr
        box = [q[2] for q in self.refs if q[0] <= A and q[1] <= AD and q[3] <= GD]
        rd = (max(-10, min(20, G - min(box))) / 10.0) if box else 0.0
        L = lambda v, s=8.0: math.log1p(v) / s
        x = [1.0, self.inv, self.newcode, float(A <= 28), float(29 <= A <= 31), float(32 <= A <= 35),
             float(AD <= 3), float(AD >= 5), float(m in fr),
             min(dG, 40) / 10.0, min(dGD, 10) / 5.0, len(cls) / 10.0, L(age), float(age < 300),
             float(a == 1), float(a == 2), float(a >= 3), L(self.att_all.get(m, 0), 2.0),
             float(self.satt.get((op, sk), 0) > 0),
             float(origin == 'seed'), float(origin == 'polish'), float(origin == 'pull'), float(origin == 'join'),
             float(origin == 'ingest'), float(origin == 'trb'), float(is_add),
             L(el), L(sl), L(sc), fp, rd, float(not box)]
        return x


def sigmoid(z):
    return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))


class Model:
    """{op: {'w': [...], 'adds_per_hit': x, 'cpu_s': y, 'base': p}}"""
    def __init__(self, d):
        self.d = d

    @classmethod
    def load(cls, path):
        return cls(json.loads(Path(path).read_text()))

    def ops(self):
        return [o for o in self.d if o in ('polish', 'pull', 'trb', 'join')]

    def prob(self, op, x):
        e = self.d.get(op)
        if e is None or x is None: return 0.0
        return sigmoid(sum(w * v for w, v in zip(e['w'], x)))

    def score(self, op, x, cpu_s=None):
        """predicted front adds per CPU second of a launch"""
        e = self.d.get(op)
        if e is None or x is None: return 0.0
        return self.prob(op, x) * e['adds_per_hit'] / max(1.0, cpu_s or e['cpu_s'])


def fit_logistic(X, y, l2=1.0, iters=50, w0=None):
    """Newton-IRLS for L2 logistic regression (numpy); the bias (column 0) is not penalised"""
    import numpy as np
    X = np.asarray(X, float); y = np.asarray(y, float); n, k = X.shape
    w = np.zeros(k) if w0 is None else np.asarray(w0, float)
    R = np.eye(k) * l2; R[0, 0] = 1e-6
    for _ in range(iters):
        p = 1 / (1 + np.exp(-np.clip(X @ w, -30, 30)))
        g = X.T @ (p - y) + R @ w
        H = (X * (p * (1 - p))[:, None]).T @ X + R
        step = np.linalg.solve(H, g); w -= step
        if np.max(np.abs(step)) < 1e-7: break
    return w.tolist()
