#!/usr/bin/env python3
"""selbuild: AES S-box with direction bit (aes-sbox-sel: inputs c x0..x7, x0 msb; outputs y0..y7; c = 0
S-box, c = 1 inverse S-box; NIST's .fn.json in seeds/aes-sbox-sel/) from ONE S-box or inverse S-box
circuit, sharing its whole middle; only the first and last linear layers are muxed.

    python3 search/nonlinear/boolflux/ops/selbuild.py --in CIRC [--maps L:K,...|best] [--top N]
        [--runs N] [--seed S] --out DIR

Mathematics.  ops/transport.py maps(src, lam, k) gives byte maps (In, cin, Out, cout) with
    other(v) = Out(src(In v + cin)) + cout    on all 256 v        (src = S or S^-1, other = the other one)
For a circuit F of src and D_in = In + I, D_out = Out + I:
  src = S:     u = v + c (D_in v + cin),         y = w + c (D_out w + cout),          w = F(u)
  src = S^-1:  u = In v + cin + c (D_in v + cin), y = Out w + cout + c (D_out w + cout)
give S(v) at c = 0 and S^-1(v) at c = 1.  c (D v + k) needs one AND per dimension of the row space of D:
with a basis f_1..f_r, c D v = sum_i E_i (c AND f_i v); c k is a XOR with c.  So
    A(sel) = A(F) + rank(D_in) + rank(D_out),   AND depth AD(F) + 2.
Over all 2040 (lam, k) min rank(D_in) + rank(D_out) = 8 (4 + 4), reached by 3 maps per source
(aes-sbox: 31:0, 95:0, 174:0; aes-invsbox: 23:0, 178:0, 210:0).  Restricted negative: only for this
construction (linear muxes of the first and last layers around an unchanged middle).

Build (gate count; depth not considered): top = BP (randomised Boyar-Peralta; bp_base is conj_lib/bp.py's
bp_run with an arbitrary initial base) for the r forms f_i v over x, r ANDs m_i = c f_i v, then BP for F's
top linear forms rewritten over (x, c, m) with the stage-1 signals in the base; bottom = BP for the forms
g_i w over F's outputs, r ANDs, BP for y over (w, c, m') with the stage-1 signals in the base.  Each basis
of each row space (840 for rank 4) is scored with one BP run; the --top best of each side get --runs runs.
Every written circuit computes aes-sbox-sel on all 512 inputs by both verifiers (core evaluation, and
independent/verify.py with its own FIPS 197 tables); circuits/check.py checks it again (the NIST .fn.json
beside the file).  Records in --out: run.json + events.jsonl.gz (runlog), <circuit>.json beside each
circuit (start, map, bases, modes, seed, checks, run summary), result.json.
"""
from __future__ import annotations

import argparse
import heapq
import itertools
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
sys.path.append(str(HERE / 'conj_lib'))
import transport as T                                 # noqa: E402
sys.path.insert(0, str(HERE.parent / 'independent'))
from boolflux import aesfn, core, runlog              # noqa: E402
import verify as IV                                   # noqa: E402

AND, XOR, XNOR, NOT = 8, 6, 9, 3


def sel_table():
    """value table of aes-sbox-sel: index c * 256 + x"""
    return list(aesfn.table('aes-sbox')) + list(aesfn.table('aes-invsbox'))


# ---- linear algebra over GF(2) ------------------------------------------------------------------

def span(vs):
    out = {0}
    for v in vs:
        out |= {x ^ v for x in out}
    return out


def rank(vs):
    b = []
    for v in vs:
        for x in b: v = min(v, v ^ x)
        if v: b.append(v)
    return len(b)


def bases(rows):
    """every unordered basis of the row space of `rows` (masks)"""
    r = rank(rows); sp = sorted(span(rows) - {0})
    for comb in itertools.combinations(sp, r):
        if rank(list(comb)) == r: yield list(comb)


def coords(v, basis):
    """coefficient mask of v in `basis` (bit i = basis[i])"""
    for c in range(1 << len(basis)):
        s = 0
        for i in range(len(basis)):
            if c >> i & 1: s ^= basis[i]
        if s == v: return c
    raise ValueError('not in span')


def rows_of(cols):
    """byte map by columns (cols[j] = image of byte bit j) -> rows[b] = mask over byte bits j"""
    return [sum(1 << j for j in range(8) if cols[j] >> b & 1) for b in range(8)]


# ---- BP with an arbitrary initial base ----------------------------------------------------------

def bp_base(m, base, tl, rng, p_norm=0.5, max_steps=300):
    """conj_lib/bp.py bp_run with initial base `base` (masks over m variables): gate list (pairs of base
    indices; the new element is their XOR), or None past max_steps"""
    S = list(base); inS = set(S); gates = []
    idx_all = np.arange(1 << m, dtype=np.int64)
    d = np.full(1 << m, 127, dtype=np.int64); d[0] = 0
    for c in S:
        d = np.minimum(d, d[idx_all ^ c] + 1)
    while True:
        rest = [t for t in tl if t not in inS]
        if not rest: return gates
        if len(gates) > max_steps: return None
        quick = [t for t in rest if d[t] == 2]
        if quick:
            t = rng.choice(quick)
            idx = {v: i for i, v in enumerate(S)}
            pr = None
            for i, v in enumerate(S):
                w = t ^ v
                if w in idx and idx[w] != i: pr = (min(i, idx[w]), max(i, idx[w])); break
            S.append(t); inS.add(t); gates.append(pr)
            d = np.minimum(d, d[idx_all ^ t] + 1); continue
        n = len(S)
        D0 = np.array([int(d[t]) - 1 for t in rest], dtype=np.int64)
        Tr = np.array(rest, dtype=np.int64)
        Sa = np.array(S, dtype=np.int64)
        ii, jj = np.triu_indices(n, 1)
        C = Sa[ii] ^ Sa[jj]
        keep = ~np.isin(C, Sa) & (C != 0)
        ii, jj, C = ii[keep], jj[keep], C[keep]
        if C.size == 0: return None
        dn = np.minimum(D0[None, :], d[Tr[None, :] ^ C[:, None]])
        s1 = dn.sum(axis=1); s2 = -(dn * dn).sum(axis=1)
        cs = np.flatnonzero(s1 == s1.min())
        if rng.random() < p_norm:
            m2 = s2[cs].min(); cs = cs[s2[cs] == m2]
        x = int(cs[rng.randrange(len(cs))])
        c = int(C[x])
        S.append(c); inS.add(c); gates.append((int(ii[x]), int(jj[x])))
        d = np.minimum(d, d[idx_all ^ c] + 1)


def best_bp(m, base, tl, rng, runs):
    bs = set(base)
    tl = [t for t in dict.fromkeys(tl) if t not in bs]
    if not tl: return []
    best = None
    for _ in range(max(1, runs)):
        g = bp_base(m, base, tl, rng)
        if g is not None and (best is None or len(g) < len(best)): best = g
    if best is None: raise RuntimeError('BP failed')
    return best


class Net:
    def __init__(self, n):
        self.n = n; self.gates = []; self.cache = {}; self.lv = [0] * n; self.trees = {}

    def add(self, op, a, b):
        self.gates.append((op, a, b)); self.lv.append(1 + max(self.lv[a], self.lv[b]))
        return self.n + len(self.gates) - 1

    def tree(self, leaves, cst):
        """balanced XOR tree (earliest two first) over the signals `leaves` (a set), constant on the
        last gate (XNOR) or a NOT for one leaf; equal (leaves, cst) share one tree"""
        key = (frozenset(leaves), cst)
        if key in self.trees: return self.trees[key]
        h = sorted((self.lv[t], t) for t in leaves)
        if not h: raise ValueError('constant form')
        heapq.heapify(h)
        if len(h) == 1:
            s = h[0][1]
            r = self.add(NOT, s, s) if cst else s
        else:
            while len(h) > 1:
                _, a = heapq.heappop(h); _, b = heapq.heappop(h)
                s = self.add(XNOR if (not h and cst) else XOR, a, b)
                heapq.heappush(h, (self.lv[s], s))
            r = h[0][1]
        self.trees[key] = r; return r

    def emit_bp(self, base_sig, base_mask, gl):
        sig = list(base_sig); msk = list(base_mask)
        for p, q in gl:
            sig.append(self.add(XOR, sig[p], sig[q])); msk.append(msk[p] ^ msk[q])
        return dict(zip(msk, sig)), list(zip(msk, sig))

    def const(self, s, cst):
        """signal + constant: s itself, an XNOR twin of s's XOR gate, or NOT s"""
        if not cst: return s
        if s in self.cache: return self.cache[s]
        if s >= self.n and self.gates[s - self.n][0] == XOR:
            _, a, b = self.gates[s - self.n]; t = self.add(XNOR, a, b)
        else:
            t = self.add(NOT, s, s)
        self.cache[s] = t; return t


# ---- the source circuit -------------------------------------------------------------------------

def top_forms(c):
    """form[s] (bit 0 = constant, bit 1+i = input i) of every AND-free signal, and the readers: the
    AND-free signals read by a gate outside the top region or as outputs"""
    n = c.n
    form = {i: 1 << (1 + i) for i in range(n)}
    for j, (op, a, b) in enumerate(c.gates):
        s = n + j
        if op == AND or a not in form or b not in form: continue
        form[s] = form[a] ^ 1 if op == NOT else form[a] ^ form[b] ^ (1 if op == XNOR else 0)
    readers = []
    for j, (op, a, b) in enumerate(c.gates):
        if n + j in form: continue
        for x in (a, b):
            if x in form and x not in readers: readers.append(x)
    for o in c.outputs:
        if o in form and o not in readers: readers.append(o)
    return form, readers


class Plan:
    """the maps of one (src, lam, k): per byte bit b, u_b = Bin_b v + bin_b + c (Din_b v + cin_b),
    y_b = Bout_b w + bout_b + c (Dout_b w + cout_b)"""

    def __init__(self, src, lam, k):
        In, cin, Out, cout = T.maps(src, lam, k)
        I = [1 << j for j in range(8)]
        self.src, self.lam, self.k = src, lam, k
        self.Din = rows_of([In[j] ^ I[j] for j in range(8)]); self.cin = cin
        self.Dout = rows_of([Out[j] ^ I[j] for j in range(8)]); self.cout = cout
        if src == 'aes-sbox':
            self.Bin, self.bin0, self.Bout, self.bout0 = rows_of(I), 0, rows_of(I), 0
        else:
            self.Bin, self.bin0, self.Bout, self.bout0 = rows_of(In), cin, rows_of(Out), cout
        self.r = (rank(self.Din), rank(self.Dout))


def xb(bytemask):
    """mask over byte bits -> mask over x variables (x_i = byte bit 7-i)"""
    return sum(1 << (7 - j) for j in range(8) if bytemask >> j & 1)


def var_sig(L, xsig, msig):
    """signals of the variables in BP mask L (0..7 = x_i, 8 = c, 9.. = m_i)"""
    out = [xsig[i] for i in range(8) if L >> i & 1]
    if L >> 8 & 1: out.append(0)
    out += [msig[i] for i in range(len(msig)) if L >> (9 + i) & 1]
    return out


def build_top(F, P, basis, net, rng, runs, mode='bp'):
    """the top of the sel circuit; returns (mp, form): mp maps F's top readers (mode wrap: F's inputs)
    to sel signals, form = F's top region (gates not copied).  bp: BP for all of F's top forms over
    (x, c, m); wrap: BP for the 8 muxed inputs u, then F's own top network; flat: one balanced tree per
    top form over (x, c, m), no sharing (a depth-aware start)"""
    ri = len(basis)
    base0 = [1 << i for i in range(8)]
    fm = [xb(f) for f in basis]
    if mode in ('flat', 'xdelta'):
        fs = [net.tree([1 + i for i in range(8) if f >> i & 1], 0) for f in fm]
        msig = [net.add(AND, 0, f) for f in fs]
    else:
        g1 = best_bp(8, base0, fm, rng, runs)
        tab1, lst1 = net.emit_bp([1 + i for i in range(8)], base0, g1)
        msig = [net.add(AND, 0, tab1[f]) for f in fm]
    lin = {}                                        # F input i -> (mask over BP vars, constant)
    for b in range(8):
        L = xb(P.Bin[b])
        if P.Din[b]:
            cc = coords(P.Din[b], basis)
            for i in range(ri):
                if cc >> i & 1: L |= 1 << (9 + i)
        if P.cin >> b & 1: L |= 1 << 8
        lin[7 - b] = (L, P.bin0 >> b & 1)
    if mode == 'wrap':
        base2 = [msk for msk, _ in lst1] + [1 << 8] + [1 << (9 + i) for i in range(ri)]
        sig2 = [sg for _, sg in lst1] + [0] + msig
        g2 = best_bp(9 + ri, base2, [lin[i][0] for i in range(8)], rng, runs)
        tab2, _ = net.emit_bp(sig2, base2, g2)
        return {i: net.const(tab2[lin[i][0]], lin[i][1]) for i in range(8)}, {}
    form, readers = top_forms(F)
    if mode == 'xdelta':
        # F's own top network on x' = Bin v + bin0 (x' = x for an S-box source), then each top form
        # that the mux changes gets one XOR with a shared tree over its (c, m) terms
        xsig = [1 + i for i in range(8)]
        sigx = {}
        for i in range(8):
            b = 7 - i
            L = xb(P.Bin[b])
            sigx[i] = net.tree(var_sig(L, xsig, []), P.bin0 >> b & 1)
        for j, (op, a, b) in enumerate(F.gates):
            t = F.n + j
            if t in form: sigx[t] = net.add(op, sigx[a], sigx[b])
        mp = {}
        for t in readers:
            f = form[t]; dl = 0
            for i in range(8):
                if f >> (1 + i) & 1: dl ^= lin[i][0] & ~0xFF
            mp[t] = sigx[t] if not dl else net.add(XOR, sigx[t], net.tree(var_sig(dl, xsig, msig), 0))
        return mp, form
    want = {}
    for s in readers:
        f = form[s]; L, k = 0, f & 1
        for i in range(8):
            if f >> (1 + i) & 1: L ^= lin[i][0]; k ^= lin[i][1]
        if L == 0: raise ValueError('constant top form')
        want[s] = (L, k)
    if mode == 'flat':
        xsig = [1 + i for i in range(8)]
        return {s: net.tree(var_sig(L, xsig, msig), k) for s, (L, k) in want.items()}, form
    base2 = [msk for msk, _ in lst1] + [1 << 8] + [1 << (9 + i) for i in range(ri)]
    sig2 = [sg for _, sg in lst1] + [0] + msig
    g2 = best_bp(9 + ri, base2, [L for L, _ in want.values()], rng, runs)
    tab2, _ = net.emit_bp(sig2, base2, g2)
    return {s: net.const(tab2[L], k) for s, (L, k) in want.items()}, form


def build_bottom(wsig, P, basis, net, rng, runs):
    """the bottom: wsig[o] = signal of F's output o (byte bit 7-o); returns the 8 sel output signals"""
    ro = len(basis)
    base0 = [1 << j for j in range(8)]
    g3 = best_bp(8, base0, list(basis), rng, runs)
    tab3, lst3 = net.emit_bp([wsig[7 - j] for j in range(8)], base0, g3)
    msig = [net.add(AND, 0, tab3[g]) for g in basis]
    ytar = []
    for b in range(8):
        L = P.Bout[b]
        if P.Dout[b]:
            cc = coords(P.Dout[b], basis)
            for i in range(ro):
                if cc >> i & 1: L |= 1 << (9 + i)
        if P.cout >> b & 1: L |= 1 << 8
        ytar.append((L, P.bout0 >> b & 1))
    base4 = [msk for msk, _ in lst3] + [1 << 8] + [1 << (9 + i) for i in range(ro)]
    sig4 = [sg for _, sg in lst3] + [0] + msig
    g4 = best_bp(9 + ro, base4, [L for L, _ in ytar], rng, runs)
    tab4, _ = net.emit_bp(sig4, base4, g4)
    return [net.const(tab4[ytar[7 - o][0]], ytar[7 - o][1]) for o in range(8)]


def bottom_region(F):
    """F's bottom region R (linear gates at the last AND level) and the (leaf set, constant) of each
    output over R's leaves (as transport.flat_bottom)"""
    n = F.n; la = [0] * n
    for op, a, b in F.gates: la.append((1 if op == AND else 0) + max(la[a], la[b]))
    AD = max(la[o] for o in F.outputs)
    R = {n + j for j, (op, a, b) in enumerate(F.gates) if op != AND and la[n + j] == AD}
    bf = {}
    for j, (op, a, b) in enumerate(F.gates):
        s = n + j
        if s not in R: continue
        fa = bf[a] if a in R else (frozenset([a]), 0)
        if op == NOT: bf[s] = (fa[0], fa[1] ^ 1); continue
        fb = bf[b] if b in R else (frozenset([b]), 0)
        bf[s] = (fa[0] ^ fb[0], fa[1] ^ fb[1] ^ (1 if op == XNOR else 0))
    return R, [bf[o] if o in R else (frozenset([o]), 0) for o in F.outputs]


def build_bottom_flat(wleaf, P, basis, net):
    """flat bottom: wleaf[o] = (set of sel signals, constant) of F's output o (byte bit 7-o); the forms
    g_i w and the outputs as balanced trees over the leaves (depth-aware, no sharing)"""
    ro = len(basis)

    def comb(mask):                                # sum of the w byte bits in mask
        L, k = frozenset(), 0
        for j in range(8):
            if mask >> j & 1: L = L ^ wleaf[7 - j][0]; k ^= wleaf[7 - j][1]
        return L, k
    msig = []
    for g in basis:
        L, k = comb(g); msig.append(net.add(AND, 0, net.tree(L, k)))
    outs = [None] * 8
    for b in range(8):
        L, k = comb(P.Bout[b]); k ^= P.bout0 >> b & 1; L = set(L)
        if P.Dout[b]:
            cc = coords(P.Dout[b], basis)
            for i in range(ro):
                if cc >> i & 1: L ^= {msig[i]}
        if P.cout >> b & 1: L ^= {0}
        outs[7 - b] = net.tree(L, k)
    return outs


def build_bottom_leafg(wsig, wleaf, P, basis, net):
    """F's own bottom network kept (wsig[o] = its output o); the forms g_i w as balanced trees over the
    bottom leaves (in parallel with w), y_b = w-part XOR a tree over its (c, m') terms"""
    ro = len(basis)

    def comb(mask):
        L, k = frozenset(), 0
        for j in range(8):
            if mask >> j & 1: L = L ^ wleaf[7 - j][0]; k ^= wleaf[7 - j][1]
        return L, k
    msig = []
    for g in basis:
        L, k = comb(g); msig.append(net.add(AND, 0, net.tree(L, k)))
    outs = [None] * 8
    for b in range(8):
        cst = P.bout0 >> b & 1
        if bin(P.Bout[b]).count('1') == 1:
            base = net.const(wsig[7 - (P.Bout[b].bit_length() - 1)], cst)
        else:
            L, k = comb(P.Bout[b]); base = net.tree(L, k ^ cst)
        dl = []
        if P.Dout[b]:
            cc = coords(P.Dout[b], basis)
            dl = [msig[i] for i in range(ro) if cc >> i & 1]
        if P.cout >> b & 1: dl.append(0)
        outs[7 - b] = base if not dl else net.add(XOR, base, net.tree(dl, 0))
    return outs


def build(F, P, bin_, bout, rng, runs, top='bp', bottom='wrap'):
    net = Net(9)
    mp, form = build_top(F, P, bin_, net, rng, runs, top)
    R, wl = bottom_region(F) if bottom in ('flat', 'leafg') else (set(), None)
    for j, (op, a, b) in enumerate(F.gates):
        s = F.n + j
        if s in form or (s in R and bottom == 'flat'): continue
        mp[s] = net.add(op, mp[a], mp[b])
    if bottom == 'flat':
        outs = build_bottom_flat([(frozenset(mp[x] for x in L), k) for L, k in wl], P, bout, net)
    elif bottom == 'leafg':
        outs = build_bottom_leafg([mp[o] for o in F.outputs], [(frozenset(mp[x] for x in L), k) for L, k in wl],
                                  P, bout, net)
    else:
        outs = build_bottom([mp[o] for o in F.outputs], P, bout, net, rng, runs)
    return core.Circuit(9, 8, net.gates, outs, in_names=['c'] + ['x%d' % i for i in range(8)],
                        out_names=['y%d' % i for i in range(8)]).live()


DEPTH_MODES = ('flat', 'xdelta', 'leafg')


def score(F, P, rng, top='bp', bottom='wrap'):
    """per side and basis one build of that side alone (BP runs 1); key (G, GD) of the side's gates for
    bp / wrap, (GD, G) of a full build for the depth-aware modes (the other side at a fixed basis):
    [(key, basis)] sorted, per side"""
    Bi = list(bases(P.Din)); Bo = list(bases(P.Dout))

    def full(bi, bo):
        m = build(F, P, bi, bo, rng, 1, top, bottom).metrics(); return (m['GD'], m['G'])
    if top in DEPTH_MODES:
        si = sorted(((full(b, Bo[0]), b) for b in Bi), key=lambda t: t[0])
    else:
        si = []
        for b in Bi:
            net = Net(9); build_top(F, P, b, net, rng, 1, top); si.append(((len(net.gates), 0), b))
        si.sort(key=lambda t: t[0])
    if bottom in DEPTH_MODES:
        so = sorted(((full(si[0][1], b), b) for b in Bo), key=lambda t: t[0])
    else:
        wsig = list(range(1, 9))                  # stand-ins: the wrap bottom's gates do not depend on F
        so = []
        for b in Bo:
            net = Net(9); build_bottom(wsig, P, b, net, rng, 1); so.append(((len(net.gates), 0), b))
        so.sort(key=lambda t: t[0])
    return si, so


def independent_fn():
    """aes-sbox-sel for independent/verify.py from its own FIPS 197 code: 9 inputs c x0..x7 (c the msb),
    c = 0 the S-box, c = 1 the inverse; checked against NIST's .fn.json when the seed mirror has it."""
    fn = IV.validate_fn(9, 8, IV.aes_sbox() + IV.aes_inv_sbox(), 'aes-sbox-sel')
    nist = HERE.parents[1] / 'seeds' / 'aes-sbox-sel' / 'aes-sbox-sel.fn.json'
    if nist.is_file():
        fj = json.loads(nist.read_text(encoding='utf-8'))          # NIST's keys: n_inputs, n_outputs, table
        assert (fj['n_inputs'], fj['n_outputs'], list(fj['table'])) == fn, 'aes-sbox-sel: NIST .fn.json differs from FIPS 197'
    return fn


def nist_name(c, base='aes-sbox-sel'):
    '''NIST file name stem <base>-aA-adAD-gG-gdGD-xxX-Y (X = #XOR + #XNOR, Y = #XNOR; NOT counts as XNOR)'''
    m = c.metrics(); k = m['counts']
    xn = k.get('XNOR', 0) + k.get('NOT', 0)
    return '%s-a%d-ad%d-g%d-gd%d-xx%d-%d' % (base, m['A'], m['AD'], m['G'], m['GD'], k.get('XOR', 0) + xn, xn)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--maps', default='best', help="comma list L:K, or 'best' (default) = every (lam, k) with rank 4 + 4")
    ap.add_argument('--top', type=int, default=3, help='bases per side kept from the screen (default 3)')
    ap.add_argument('--runs', type=int, default=8, help='BP runs per region of a kept build (default 8)')
    ap.add_argument('--top-mode', default='bp', choices=['bp', 'wrap', 'flat', 'xdelta'])
    ap.add_argument('--bottom-mode', default='wrap', choices=['wrap', 'flat', 'leafg'])
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    t0 = time.process_time()
    F = core.read_ncff(a.inp)
    vt = list(F.value_table())
    src = next((s for s in ('aes-sbox', 'aes-invsbox') if vt == list(aesfn.table(s))), None)
    assert src, 'the input computes neither the S-box nor its inverse'
    if a.maps == 'best':
        ms = [(lam, kk) for lam in range(1, 256) for kk in range(8) if sum(Plan(src, lam, kk).r) == 8]
    else:
        ms = [tuple(int(t) for t in x.split(':')) for x in a.maps.split(',')]
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    m0 = F.metrics()
    rec = runlog.RunLog(out, 'ops.selbuild', seeds={'seed': a.seed}, function='aes-sbox-sel',
                        config={'in': a.inp, 'src': src, 'maps': a.maps, 'top': a.top, 'runs': a.runs,
                                'top_mode': a.top_mode, 'bottom_mode': a.bottom_mode})
    rec.add_start(a.inp, metrics=[m0[q] for q in ('A', 'AD', 'G', 'GD')], label='start (%s)' % src)
    rec.event('maps', maps=[list(x) for x in ms])
    ifn = independent_fn()
    want = sel_table(); rng = random.Random(a.seed); res = []; best = {}
    status = 'error'
    try:
        for lam, kk in ms:
            P = Plan(src, lam, kk)
            si, so = score(F, P, rng, a.top_mode, a.bottom_mode)
            sc = {'map': [lam, kk], 'ranks': P.r, 'top_screen': [g for g, _ in si[:6]],
                  'bottom_screen': [g for g, _ in so[:6]], 'n_bases': [len(si), len(so)]}
            print(json.dumps(sc), flush=True); rec.event('screen', **sc)
            for (_, bi), (_, bo) in itertools.product(si[:a.top], so[:a.top]):
                c = build(F, P, bi, bo, rng, a.runs, a.top_mode, a.bottom_mode)
                ok = list(c.value_table()) == want
                m = c.metrics()
                r = {'lam': lam, 'k': kk, 'bin': bi, 'bout': bo, 'ok': ok, **{q: m[q] for q in ('A', 'AD', 'G', 'GD')}}
                res.append(r); print(json.dumps(r), flush=True); rec.event('build', **r)
                if not ok: continue
                key = (m['A'], m['AD'], m['G'], m['GD'])
                if key in best: continue
                c.name = nist_name(c)
                p = out / (c.name + '.circ.txt')
                text = core.write_ncff(c, core.Model.load('nist'),
                                       comments=['selbuild from %s, map %d:%d, bases %s / %s, modes %s/%s, seed %d'
                                                 % (Path(a.inp).name, lam, kk, bi, bo, a.top_mode, a.bottom_mode, a.seed)])
                iv = IV.verify_text(text, ifn)            # second verifier: its own parser, evaluator and FIPS 197 tables
                if not iv['ok']:
                    rec.event('rejected', file=p.name, why='independent verifier', errors=iv['errors'][:3])
                    continue
                p.write_text(text, encoding='utf-8')
                best[key] = str(p)
                sha = runlog.sha256_file(p)
                side = {'function': 'aes-sbox-sel', 'A': key[0], 'AD': key[1], 'G': key[2], 'GD': key[3],
                        'method': 'ops/selbuild.py direction-select build', 'start': {'path': str(Path(a.inp).resolve()),
                        'sha256': runlog.sha256_file(a.inp), 'function': src, 'tuple': rec.rec['starts'][0]['metrics']},
                        'map': [lam, kk], 'bases': [bi, bo], 'modes': [a.top_mode, a.bottom_mode], 'seed': a.seed,
                        'checks': {'core': 'all 512 inputs', 'independent': 'all 512 inputs (order %s)' % iv['order']},
                        'circuit_sha256': sha, 'elapsed_s': round(time.time() - rec.t0, 3), 'run': rec.summary(),
                        'utc': runlog.utc()}
                (out / (c.name + '.json')).write_text(json.dumps(side, indent=1, default=str) + '\n', encoding='utf-8')
                rec.improvement({'A': key[0], 'AD': key[1], 'G': key[2], 'GD': key[3]}, 'selbuild', file=p.name,
                                circuit_sha256=sha, map=[lam, kk])
        status = 'ok'
    finally:
        written = best and {'%d/%d/%d/%d' % k: v for k, v in best.items()}
        (out / 'result.json').write_text(json.dumps({'in': a.inp, 'src': src, 'maps': ms, 'seed': a.seed,
                                                     'cpu_s': time.process_time() - t0, 'written': written,
                                                     'run_record': str(rec.path), 'status': status,
                                                     'results': res}, indent=1) + '\n', encoding='utf-8')
        rec.finish(status, written=written, n_builds=len(res))


if __name__ == '__main__':
    main()
