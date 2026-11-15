#!/usr/bin/env python3
"""H3: general-model window re-solve by SAT.

Model: a circuit is an ordered list of ANDs g_1..g_K, g_i = a_i & b_i with a_i, b_i affine in the
inputs and g_<i; the outputs must lie in the affine span of (1, inputs, all g).

Window: a set U of ANDs of a known circuit that is closed under consumers (every AND that reads
a member of U is in U).  Then R = all \\ U is a self-contained sub-circuit (downward closed) whose
AND functions stay fixed.  We delete U and ask for m free ANDs f_1..f_m placed after R, where
f_i's operands are arbitrary linear combinations of (inputs, R, f_<i) (constants are irrelevant
for the span and dropped), such that every output lies in span(1, inputs, R, f).  This is the
complete neighbourhood "same R, any m new ANDs" (any DAG on the f's has a topological order).

Encoding (CaDiCaL via pysat): for each f_i and operand o: coefficient bits over the operand basis,
truth-table bits at all 256 rows (parity of selected fixed tables + products coef & f_l(x));
f_i(x) = a_i(x) & b_i(x).  Outputs: with B = span(1, x, R) and an information set P of rows,
pi(v)_x = v_x + sum_{p in M_x} v_p (x not in P) is the quotient map mod B; we require
pi(y) = sum_l d_{y,l} pi(f_l) for a basis of the projected outputs.  Symmetry breaking: the pair
(a_i, b_i) matters only as the 2-dim space it spans (a(a+b) = a + ab), so [a; b] is forced into
reduced row echelon form.
"""
from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, '/home/joebachir20/xcr-boolflux/nonlinear')
from boolflux import core, skeleton  # noqa: E402
from pysat.solvers import Solver  # noqa: E402

NR = 256
ONES = (1 << NR) - 1


# ---------------------------------------------------------------- linear algebra on 256-bit ints
class Span:
    """Echelon basis keyed by the highest set bit."""

    def __init__(self, vecs=()):
        self.b = {}; self.order = []
        for v in vecs: self.add(v)

    def reduce(self, v):
        """Canonical coset representative: zero at every pivot position."""
        for h in self.order:
            if (v >> h) & 1: v ^= self.b[h]
        return v

    def add(self, v):
        v = self.reduce(v)
        if v:
            h = v.bit_length() - 1
            self.b[h] = v
            self.order = sorted(self.b, reverse=True)
            return True
        return False

    def __len__(self): return len(self.b)


def info_set(vecs):
    """Pivot rows P and, for each row x, the set M_x of pivots with v_x = sum_{p in M_x} v_p for all
    v in span(vecs).  Returns (P list, M dict x -> list of pivots) and the rank."""
    rows = []                         # RREF rows as (pivot col, vec)
    for v in vecs:
        for p, w in rows:
            if (v >> p) & 1: v ^= w
        if v:
            p = (v & -v).bit_length() - 1      # lowest set bit as pivot column
            rows = [(q, w ^ v) if (w >> p) & 1 else (q, w) for q, w in rows]
            rows.append((p, v))
    P = [p for p, _ in rows]
    M = {}
    for x in range(NR):
        M[x] = [p for p, w in rows if (w >> x) & 1]
    return P, M, len(rows)


def bits(t): return [x for x in range(NR) if (t >> x) & 1]


# ---------------------------------------------------------------- circuit side
class Base:
    def __init__(self, path):
        self.path = str(path)
        self.c = core.read_ncff(path) if not str(path).endswith('.bfx') else \
            core.from_kernel(Path(path).read_text(), Path(path).stem)
        self.sk = skeleton.extract(self.c)
        self.n = self.sk['n']; self.K = len(self.sk['ands'])
        tab, ft, ones = skeleton._form_tables(self.sk)
        self.tab = tab                      # basis position -> table
        self.ft = ft
        self.out = [ft(f) for f in self.sk['outputs']]
        assert self.out == self.c.output_tables()
        n = self.n
        self.deps = []
        for L, R in self.sk['ands']:
            f = (L | R) >> (1 + n)
            self.deps.append({j for j in range(self.K) if (f >> j) & 1})
        self.level = []
        for k in range(self.K):
            self.level.append(1 + max([self.level[j] for j in self.deps[k]], default=0))
        self.cons = [{k for k in range(self.K) if j in self.deps[k]} for j in range(self.K)]
        self.andtab = [tab[1 + n + k] for k in range(self.K)]

    def closure(self, W):
        U = set(W)
        for k in range(self.K):
            if self.deps[k] & U: U.add(k)
        return U

    def rank_mod(self, U):
        R = [k for k in range(self.K) if k not in U]
        S = Span([ONES] + self.tab[1:1 + self.n] + [self.andtab[k] for k in R])
        T = Span()
        for y in self.out: T.add(S.reduce(y))
        return len(T)


# ---------------------------------------------------------------- CNF
class CNF:
    def __init__(self):
        self.nv = 0; self.cl = []

    def var(self):
        self.nv += 1; return self.nv

    def vars(self, k): return [self.var() for _ in range(k)]

    def and2(self, a, b):
        z = self.var()
        self.cl += [[-z, a], [-z, b], [z, -a, -b]]
        return z

    def _xor_small(self, lits, rhs):
        # all assignments of lits with parity != rhs are forbidden
        k = len(lits)
        for mask in range(1 << k):
            par = bin(mask).count('1') & 1
            if par != rhs:
                # forbid assignment where lit i = (mask>>i)&1
                self.cl.append([(-l if (mask >> i) & 1 else l) for i, l in enumerate(lits)])

    def xor_eq(self, lits, rhs, chunk=4):
        """XOR of lits (positive var ids) == rhs (0/1)."""
        lits = list(lits)
        if not lits:
            if rhs: self.cl.append([])         # contradiction
            return
        while len(lits) > chunk:
            head = lits[:chunk - 1]; lits = lits[chunk - 1:]
            t = self.var()
            self._xor_small(head + [t], 0)      # t = xor(head)
            lits.append(t)
        self._xor_small(lits, rhs)

    def xor_def(self, lits, const=0):
        """New var = XOR(lits) ^ const."""
        z = self.var()
        self.xor_eq(list(lits) + [z], const)
        return z


def build(base: Base, U, m, opts=None):
    opts = opts or {}
    n = base.n
    R = [k for k in range(base.K) if k not in U]
    fixed_ops = base.tab[1:1 + n] + [base.andtab[k] for k in R]   # operand basis (no constant)
    nf = len(fixed_ops)
    rowsel = [[t for t in range(nf) if (fixed_ops[t] >> x) & 1] for x in range(NR)]
    cnf = CNF()
    F = []           # F[l][x] var
    coef = []        # coef[i] = (alpha list, gamma list), length nf + i
    for i in range(m):
        L = nf + i
        al = cnf.vars(L); ga = cnf.vars(L)
        coef.append((al, ga))
        tabs = []
        for cv in (al, ga):
            T = []
            for x in range(NR):
                lits = [cv[t] for t in rowsel[x]]
                for l in range(i):
                    lits.append(cnf.and2(cv[nf + l], F[l][x]))
                T.append(cnf.xor_def(lits))
            tabs.append(T)
        F.append([cnf.and2(tabs[0][x], tabs[1][x]) for x in range(NR)])
        # echelon form of [al; ga] (positions in order 0..L-1), both nonzero
        za = [None] * (L + 1); zb = [None] * (L + 1)
        cnf.cl.append(al[:]); cnf.cl.append(ga[:])
        # za[t] true iff al[0..t-1] all zero
        za[0] = cnf.var(); cnf.cl.append([za[0]])
        zb[0] = cnf.var(); cnf.cl.append([zb[0]])
        for t in range(L):
            za[t + 1] = cnf.and2(za[t], -al[t])
            zb[t + 1] = cnf.and2(zb[t], -ga[t])
        for t in range(L):
            # lead(a)=t -> b zero on 0..t
            cnf.cl.append([-za[t], -al[t], zb[t + 1]])
            # lead(b)=t -> a[t]=0
            cnf.cl.append([-zb[t], -ga[t], -al[t]])
    # outputs
    B = [ONES] + base.tab[1:1 + n] + [base.andtab[k] for k in R]
    P, M, rk = info_set(B)
    Pset = set(P)
    nonpiv = [x for x in range(NR) if x not in Pset]
    S = Span(B)
    proj = []
    T = Span()
    for y in base.out:
        r = S.reduce(y)
        if T.add(r): proj.append(y)
    r = len(proj)
    PI = []
    for l in range(m):
        PI.append({x: cnf.xor_def([F[l][x]] + [F[l][p] for p in M[x]]) for x in nonpiv})
    D = []
    for y in proj:
        d = cnf.vars(m); D.append(d)
        for x in nonpiv:
            rhs = ((y >> x) & 1) ^ (sum((y >> p) & 1 for p in M[x]) & 1)
            cnf.xor_eq([cnf.and2(d[l], PI[l][x]) for l in range(m)], rhs)
    info = {'R': R, 'nf': nf, 'r': r, 'proj': proj, 'B': B}
    return cnf, F, coef, D, info


def _child(conn, clauses, solver):
    s = Solver(name=solver, bootstrap_with=clauses)
    res = s.solve()
    conn.send((res, s.get_model() if res else None))
    conn.close()


def solve(cnf, seconds, solver='cadical195'):
    """Solve in a forked child; kill it after ``seconds`` (pysat's interrupt is not honoured by
    CaDiCaL here).  Returns (True/False/None, seconds, model)."""
    import multiprocessing as mp
    ctx = mp.get_context('fork')
    a, b = ctx.Pipe(duplex=False)
    t0 = time.time()
    p = ctx.Process(target=_child, args=(b, cnf.cl, solver)); p.start(); b.close()
    res = None; model = None
    if a.poll(seconds):
        try: res, model = a.recv()
        except EOFError: res = None
    p.kill(); p.join()
    return res, time.time() - t0, model


def decode(base: Base, U, m, F, coef, info, model):
    n = base.n
    val = set(v for v in model if v > 0)
    R = info['R']; nf = info['nf']
    newidx = {k: j for j, k in enumerate(R)}

    def remap(f):
        g = f & ((1 << (1 + n)) - 1)
        for k in R:
            if (f >> (1 + n + k)) & 1: g |= 1 << (1 + n + newidx[k])
        return g
    ands = [(remap(L), remap(Rr)) for k, (L, Rr) in enumerate(base.sk['ands']) if k in newidx]
    for i in range(m):
        forms = []
        for cv in coef[i]:
            f = 0
            for t in range(nf):
                if cv[t] in val:
                    if t < n: f |= 1 << (1 + t)
                    else: f |= 1 << (1 + n + (t - n))
            for l in range(i):
                if cv[nf + l] in val: f |= 1 << (1 + n + len(R) + l)
            forms.append(f)
        ands.append(tuple(forms))
    sk = {'n': n, 'm': base.sk['m'], 'ands': ands, 'outputs': None}
    tab, ft, ones = skeleton._form_tables(sk)
    for l in range(m):   # consistency with the SAT tables
        t = sum(1 << x for x in range(NR) if F[l][x] in val)
        assert t == tab[1 + n + len(R) + l], 'decode mismatch at f%d' % l
    # outputs: express each output over tab (Gaussian elimination with tracking)
    piv = {}
    for pos, t in enumerate(tab):
        v, f = t, 1 << pos
        while v:
            h = v.bit_length() - 1
            if h in piv: v ^= piv[h][0]; f ^= piv[h][1]
            else: piv[h] = (v, f); break
    outs = []
    for y in base.out:
        v, f = y, 0
        while v:
            h = v.bit_length() - 1
            if h not in piv: raise ValueError('output not in span')
            v ^= piv[h][0]; f ^= piv[h][1]
        outs.append(f)
    sk['outputs'] = outs
    c2 = skeleton.synthesize(sk, core.Model.load('nist').ops(), name='h3')
    assert c2.output_tables() == base.out
    return sk, c2


def finish(base: Base, R, newforms, name='h3'):
    """Circuit from the kept ANDs R (original order) plus new ANDs given as pairs of forms over the
    positions (const, inputs, R in order, new ANDs in order).  Outputs re-solved over the tables.
    Returns (skeleton, circuit) or raises ValueError if an output is not in the span."""
    n = base.n
    newidx = {k: j for j, k in enumerate(R)}

    def remap(f):
        g = f & ((1 << (1 + n)) - 1)
        for k in R:
            if (f >> (1 + n + k)) & 1: g |= 1 << (1 + n + newidx[k])
        return g
    ands = [(remap(L), remap(Rr)) for k, (L, Rr) in enumerate(base.sk['ands']) if k in newidx]
    ands += [tuple(p) for p in newforms]
    sk = {'n': n, 'm': base.sk['m'], 'ands': ands, 'outputs': None}
    tab, ft, ones = skeleton._form_tables(sk)
    piv = {}
    for pos, t in enumerate(tab):
        v, f = t, 1 << pos
        while v:
            h = v.bit_length() - 1
            if h in piv: v ^= piv[h][0]; f ^= piv[h][1]
            else: piv[h] = (v, f); break
    outs = []
    for y in base.out:
        v, f = y, 0
        while v:
            h = v.bit_length() - 1
            if h not in piv: raise ValueError('output not in span')
            v ^= piv[h][0]; f ^= piv[h][1]
        outs.append(f)
    sk['outputs'] = outs
    c2 = skeleton.synthesize(sk, core.Model.load('nist').ops(), name=name)
    assert c2.output_tables() == base.out
    return sk, c2


def save_circuit(c2, outdir, tag, meta):
    mt = c2.metrics(core.Model.load('nist'))
    name = 'h3-%s-a%d-ad%d-g%d' % (tag, mt['A'], mt['AD'], mt['G'])
    c2.name = name
    p = Path(outdir) / (name + '.circ.txt')
    p.write_text(core.write_ncff(c2, core.Model.load('nist'), comments=[str(meta.get('how', ''))]),
                 encoding='utf-8', newline='\n')
    Path(str(p).replace('.circ.txt', '.json')).write_text(json.dumps(
        dict(meta, A=mt['A'], AD=mt['AD'], G=mt['G'], GD=mt['GD'],
             utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())), indent=1),
        encoding='utf-8', newline='\n')
    return str(p), mt


def run_window(base, U, m, seconds, tag, outdir, log, extra=None):
    U = set(U)
    r = base.rank_mod(U)
    rec = {'tag': tag, 'src': Path(base.path).name, 'U': sorted(U), 'levels': [base.level[k] for k in sorted(U)],
           'k': len(U), 'm': m, 'rank': r}
    if extra: rec.update(extra)
    if r > m:
        rec.update(result='UNSAT-rank', time=0.0)
        log(rec); return rec
    t0 = time.time()
    cnf, F, coef, D, info = build(base, U, m)
    rec.update(nvars=cnf.nv, nclauses=len(cnf.cl), build=round(time.time() - t0, 1))
    res, dt, model = solve(cnf, seconds)
    rec['time'] = round(dt, 1)
    if res is None: rec['result'] = 'TIMEOUT'
    elif res is False: rec['result'] = 'UNSAT'
    else:
        rec['result'] = 'SAT'
        sk, c2 = decode(base, U, m, F, coef, info, model)
        mt = c2.metrics(core.Model.load('nist'))
        A = mt['A']
        name = 'h3-%s-a%d-ad%d-g%d' % (tag, A, mt['AD'], mt['G'])
        c2.name = name
        p = Path(outdir) / (name + '.circ.txt')
        p.write_text(core.write_ncff(c2, core.Model.load('nist'),
                                     comments=['H3 window re-solve from %s, U=%s, m=%d' % (Path(base.path).name, sorted(U), m)]),
                     encoding='utf-8', newline='\n')
        rec.update(file=str(p), A=A, AD=mt['AD'], G=mt['G'])
        Path(str(p).replace('.circ.txt', '.json')).write_text(json.dumps(
            dict(rec, made='strategies/H3/wsat.py window re-solve (CaDiCaL 1.9.5 via pysat)',
                 utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())), indent=1), encoding='utf-8', newline='\n')
    log(rec)
    return rec


def mklog(path):
    def log(rec):
        line = json.dumps(rec)
        print(line, flush=True)
        with open(path, 'a', encoding='utf-8', newline='\n') as fh: fh.write(line + '\n')
    return log
