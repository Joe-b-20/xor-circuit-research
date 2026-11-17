#!/usr/bin/env python3
"""transport: turn an AES S-box circuit into an inverse S-box circuit (and back), then staged-pull it.

    python3 search/nonlinear/boolflux/ops/transport.py --in START --target REF --seed S \
        --seconds T --out DIR [--cpus 1]
        [--function auto|aes-sbox|aes-invsbox]  the function to BUILD; auto (default) = the other one of START
        [--maps ITEMS]        comma list of transports, all built: id (lam 1 k 0), L:K, screen:N (the N best
                              non-identity (lam, k) by the screen below), depth:N (the N lowest-GD flat transports
                              over all 2040, then fewest G); default id,188:0,189:0,screen:3
        [--ladder LIST]       gate-depth caps of the synthesis, relative to START's GD; default -1,0,1,2
        [--synth-seeds N]     randomised rebuilds per region and cap (trb Paar with Kraft deadlines); default 6
        [--bp-runs N]         Boyar-Peralta runs of the final top re-synthesis per cap; default 6
        [--build-seconds S]   time for the builds (the rest goes to the pulls); default min(300, T/4)
        [--pull SCHEDULE]     conjpull schedule for the staged pull of the chosen builds ('' = no pull);
                              default g:+0:150,m:+0:150,m:-1:170; a cap s / s+N / s-N = START's GD (+/- N)
        [--pull-deep SCHED]   schedule for a build deeper than START's GD + --deep-margin (default 1);
                              default g:+0:120,m:s+2:150,m:s:200 ('' = --pull for every build)
        [--pull-n N]          builds pulled (fewest G, then lowest GD, then by G+GD); default 2
        [--screen-runs N]     BP runs per (lam, k) in the screen; default 2

Mathematics (inv = GF(2^8) inversion, Aff(w) = A w + 0x63, S = Aff o inv, S^-1 = inv o Aff^-1, inv an
involution, inv = G' o inv o G for G(z) = lam z^(2^k), G'(w) = (lam w)^(2^(8-k)), conj_lib/conj.py):
    S^-1(y) = G'(Aff^-1(F(G(Aff^-1 y))))       for any circuit F of S         (to aes-invsbox)
    S(x)    = Aff(G'(I(Aff(G x))))             for any circuit I of S^-1      (to aes-sbox)
So every circuit gives 2040 circuits of the other function with the same AND gates, the same AND depth
and the same middle linear layers: only the inputs (an affine map In, cin) and the outputs (Out, cout)
change.  maps() computes (In, cin, Out, cout) from these formulas and checks the identity on all 256
values before anything is built.

Synthesis (depth-aware; the linear maps are folded into the circuit's own first and last linear layers):
  1. input side: F with balanced XOR trees for u = In y + cin in front (function F o In, not yet the target);
     its whole top linear region (the new trees + F's own AND-free gates) is rebuilt by trb (randomised
     Paar with Kraft deadlines, hub/trb_impl.py) at gate-depth cap D, --synth-seeds seeds, fewest gates kept;
  2. output side: balanced XOR trees for Out w + cout behind it; its whole bottom linear region (the new
     trees + F's own gates after the last AND level) is rebuilt the same way at cap D;
  3. alternating trb top / trb bottom / Boyar-Peralta top (conj_lib/bp.py) passes at the reached GD, each
     kept only if it lowers G (or GD at equal G) and keeps A and AD; checked on all 256 inputs.
  Every built circuit (each cap of the ladder and each map) is offered to the recorder (common.Recorder:
  aes_check = core evaluation + independent verifier on all 256 inputs, metrics agreement, NIST library).
Screen of the (lam, k): the conj3 proxies (conj_lib/conj3.py: BP gate count of the new top forms + Paar
count of the new output forms), with the largest top form weight as tie-break.
Staged pull: conjpull.py --conj id --schedule SCHEDULE on each chosen build (a child process with its own
run record, DIR/pull-<i>/); its recorded circuits are listed in DIR/result.json ("pulls").
Search states may exceed the caps; recorded circuits are inside the target's A and AD (the AND gates of
the start are kept, so A and AD of every transport equal the start's).
"""
from __future__ import annotations

import argparse
import heapq
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as CM                                  # noqa: E402

sys.path.append(str(HERE / 'conj_lib'))
from boolflux import aesfn, core                     # noqa: E402
from boolflux.hub.common import clean                # noqa: E402

OP = 'transport'
AND, XOR, XNOR, NOT = 8, 6, 9, 3
OTHER = {'aes-sbox': 'aes-invsbox', 'aes-invsbox': 'aes-sbox'}


# ---- the maps ------------------------------------------------------------------------------------

def maps(src, lam=1, k=0):
    """(In, cin, Out, cout) with  dst(v) = Out(src(In v + cin)) + cout  on all 256 v, for the transport
    src -> OTHER[src] combined with the GF(2^8) symmetry (lam, k).  Byte maps as conj.py: columns
    M[j] = image of byte bit j.  Checked on all 256 values (AssertionError otherwise)."""
    import conj as CJ
    gm, gp, ap = CJ.gmul, CJ.gpow, CJ.apply
    G = lambda z: gm(lam, gp(z, 1 << k))
    Gp = lambda w: gp(gm(lam, w), 1 << ((8 - k) % 8))
    aff = lambda w: ap(CJ.A, w) ^ 0x63
    affi = lambda w: ap(CJ.Ainv, w ^ 0x63)
    if src == 'aes-sbox':               # S^-1 = G' o Aff^-1 o F o G o Aff^-1
        fin = lambda y: G(affi(y)); fout = lambda w: Gp(affi(w))
    elif src == 'aes-invsbox':          # S = Aff o G' o I o Aff o G
        fin = lambda x: aff(G(x)); fout = lambda w: aff(Gp(w))
    else:
        raise ValueError(src)
    cin, cout = fin(0), fout(0)
    In = [fin(1 << j) ^ cin for j in range(8)]
    Out = [fout(1 << j) ^ cout for j in range(8)]
    S, D = aesfn.table(src), aesfn.table(OTHER[src])
    # the tables are msb-first circuit values = the byte itself (aesfn tables are byte -> byte)
    assert all(ap(Out, S[ap(In, v) ^ cin]) ^ cout == D[v] for v in range(256)), 'transport map %d:%d wrong' % (lam, k)
    return In, cin, Out, cout


# ---- circuit construction ------------------------------------------------------------------------

def _tree(gates, n, terms, lv, cst):
    """balanced XOR tree (earliest two first) over signals `terms` with levels lv; constant on the last
    gate (XNOR) or a NOT for a single term.  Returns the root signal."""
    h = [(lv[t], i, t) for i, t in enumerate(terms)]
    heapq.heapify(h); q = len(h)
    if len(h) == 1:
        s = h[0][2]
        if cst:
            gates.append((NOT, s, s)); s = n + len(gates) - 1; lv[s] = lv[h[0][2]] + 1
        return s
    while len(h) > 1:
        l1, _, a = heapq.heappop(h); l2, _, b = heapq.heappop(h)
        last = not h
        gates.append((XNOR if (last and cst) else XOR, a, b)); s = n + len(gates) - 1
        lv[s] = max(l1, l2) + 1; q += 1
        heapq.heappush(h, (lv[s], q, s))
    return h[0][2]


def wrap(c, In=None, cin=0, Out=None, cout=0):
    """circuit  v -> Out(c(In v + cin)) + cout  with balanced XOR trees (no sharing); In/Out None = identity.
    Circuit input i is byte bit 7-i (aesfn / core.value_table are msb-first)."""
    n = c.n; gates = []; lv = {i: 0 for i in range(n)}
    if In is None:
        u = list(range(n))
    else:
        u = [_tree(gates, n, [7 - j for j in range(8) if In[j] >> (7 - i) & 1], lv, cin >> (7 - i) & 1) for i in range(8)]
    mp = {i: u[i] for i in range(n)}
    for j, (op, a, b) in enumerate(c.gates):
        gates.append((op, mp[a], mp[b])); s = n + len(gates) - 1
        lv[s] = 1 + max(lv[mp[a]], lv[mp[b]]); mp[n + j] = s
    old = [mp[s] for s in c.outputs]
    if Out is None:
        outs = old
    else:
        outs = [_tree(gates, n, [old[7 - j] for j in range(8) if Out[j] >> (7 - i) & 1], lv, cout >> (7 - i) & 1) for i in range(8)]
    return core.Circuit(n, c.m, gates, outs).live()


def _slp(rows, rng, runs):
    """shortest straight-line program (Boyar-Peralta heuristic, conj_lib/bp.py bp_run, best of `runs`) for
    the 8 linear forms `rows` (bit masks over 8 variables).  Returns (gates [(p, q)] over the ids 0..7 =
    variables and 8 + i = gate i, signal id of every row)."""
    import bp
    tl = sorted({r for r in rows if bin(r).count('1') >= 2})
    best = None
    for _ in range(max(1, runs)):
        g = bp.bp_run(8, tl, rng, 0.5)
        if g is not None and (best is None or len(g) < len(best)): best = g
    vec = [1 << i for i in range(8)]
    for p, q in best or []: vec.append(vec[p] ^ vec[q])
    return best or [], [vec.index(r) for r in rows]


def wrap_slp(c, In=None, cin=0, Out=None, cout=0, rng=None, runs=8):
    """as wrap(), but the input and output networks are shared straight-line programs (_slp): fewest
    gates, depth not considered"""
    rng = rng or random.Random(1)
    n = c.n; gates = []

    def net(rows, cst, base):
        g, ids = _slp(rows, rng, runs)
        sig = list(base)
        for p, q in g:
            gates.append((XOR, sig[p], sig[q])); sig.append(n + len(gates) - 1)
        res = []
        for i, s in enumerate(ids):
            if cst >> (7 - i) & 1:
                if s >= 8:                         # constant on the root: an XNOR twin of the root gate
                    p, q = g[s - 8]; gates.append((XNOR, sig[p], sig[q]))
                else:
                    gates.append((NOT, sig[s], sig[s]))
                res.append(n + len(gates) - 1)
            else:
                res.append(sig[s])
        return res
    # rows over 8 variables: variable v = circuit input v (In side) or old output v (Out side)
    if In is None:
        u = list(range(n))
    else:
        u = net([sum(1 << (7 - j) for j in range(8) if In[j] >> (7 - i) & 1) for i in range(8)], cin, list(range(8)))
    mp = {i: u[i] for i in range(n)}
    for j, (op, a, b) in enumerate(c.gates):
        gates.append((op, mp[a], mp[b])); mp[n + j] = n + len(gates) - 1
    old = [mp[s] for s in c.outputs]
    if Out is None:
        outs = old
    else:
        outs = net([sum(1 << (7 - j) for j in range(8) if Out[j] >> (7 - i) & 1) for i in range(8)], cout, old)
    return core.Circuit(n, c.m, gates, outs).live()


def _levels(c):
    lg = [0] * c.n; la = [0] * c.n
    for op, a, b in c.gates:
        lg.append(1 + max(lg[a], lg[b])); la.append((1 if op == AND else 0) + max(la[a], la[b]))
    return lg, la


def flat_top(c, In=None, cin=0):
    """c with its top linear region (AND-free gates) replaced by one balanced XOR tree per top form, the
    forms first composed with u = In v + cin (In None = identity).  Top forms = the AND-free signals read
    by an AND, by a gate below the top, or as outputs.  No sharing, so every tree root is read only outside
    the region: trb's deadlines (struct, computed through the circuit) are then the exact ones."""
    n = c.n
    if In is None:
        uf = [1 << (1 + i) for i in range(n)]
    else:
        uf = []
        for i in range(8):
            f = cin >> (7 - i) & 1
            for j in range(8):
                if In[j] >> (7 - i) & 1: f ^= 1 << (1 + 7 - j)
            uf.append(f)
    form = {i: uf[i] for i in range(n)}
    for j, (op, a, b) in enumerate(c.gates):
        s = n + j
        if op == AND or a not in form or b not in form: continue
        form[s] = form[a] ^ form[b] ^ (1 if op == XNOR else 0) if op != NOT else form[a] ^ 1
    readers = []
    for j, (op, a, b) in enumerate(c.gates):
        if n + j in form: continue
        for x in (a, b):
            if x in form and x not in readers: readers.append(x)
    for o in c.outputs:
        if o in form and o not in readers: readers.append(o)
    gates = []; lv = {i: 0 for i in range(n)}; mp = {}; byform = {}
    for s in readers:
        f = form[s]
        if f not in byform:
            terms = [i for i in range(n) if f >> (1 + i) & 1]
            if not terms: raise ValueError('constant top form')
            byform[f] = _tree(gates, n, terms, lv, f & 1)
        mp[s] = byform[f]
    for i in range(n): mp.setdefault(i, i)
    for j, (op, a, b) in enumerate(c.gates):
        s = n + j
        if s in form: continue
        gates.append((op, mp[a], mp[b])); mp[s] = n + len(gates) - 1
    return core.Circuit(n, c.m, gates, [mp[o] for o in c.outputs]).live()


def flat_bottom(c, Out=None, cout=0):
    """c with its bottom linear region (linear gates at the last AND level) replaced by one depth-optimal
    XOR tree (earliest leaves first) per output, the outputs first composed with Out w + cout (Out None =
    identity)."""
    n = c.n; lg, la = _levels(c)
    AD = max(la[o] for o in c.outputs)
    R = {n + j for j, (op, a, b) in enumerate(c.gates) if op != AND and la[n + j] == AD}
    bf = {}                                   # s -> (frozenset of leaves, constant)
    for j, (op, a, b) in enumerate(c.gates):
        s = n + j
        if s not in R: continue
        fa = bf[a] if a in R else (frozenset([a]), 0)
        if op == NOT: bf[s] = (fa[0], fa[1] ^ 1); continue
        fb = bf[b] if b in R else (frozenset([b]), 0)
        bf[s] = (fa[0] ^ fb[0], fa[1] ^ fb[1] ^ (1 if op == XNOR else 0))
    old = [bf[o] if o in R else (frozenset([o]), 0) for o in c.outputs]
    if Out is None:
        new = old
    else:
        new = []
        for i in range(8):
            L, k = frozenset(), cout >> (7 - i) & 1
            for j in range(8):
                if Out[j] >> (7 - i) & 1: L = L ^ old[7 - j][0]; k ^= old[7 - j][1]
            new.append((L, k))
    gates = []; mp = {i: i for i in range(n)}; lv = {i: 0 for i in range(n)}
    for j, (op, a, b) in enumerate(c.gates):
        s = n + j
        if s in R: continue
        gates.append((op, mp[a], mp[b])); t = n + len(gates) - 1; mp[s] = t; lv[t] = 1 + max(lv[mp[a]], lv[mp[b]])
    outs = []
    for L, k in new:
        if not L: raise ValueError('constant output')
        outs.append(_tree(gates, n, sorted(mp[x] for x in L), lv, k))
    return core.Circuit(n, c.m, gates, outs).live()


def _rebuild_best(c, D, region, seeds, rng, want):
    """best of `seeds` trb rebuilds of `region` at cap D (region flattened first, so the deadlines are
    exact): fewest gates, GD <= D, function `want` (a value table) kept; None if no rebuild meets D"""
    import trb
    best = None
    c = flat_top(c) if region == 'top' else flat_bottom(c) if region == 'bottom' else c
    for _ in range(seeds):
        c2, info = trb.rebuild(c, D, region, random.Random(rng.random()))
        if info.get('skipped'): break                  # infeasible deadlines or empty region: same every seed
        c2 = clean(c2)
        m = c2.metrics()
        if m['GD'] > D or tuple(c2.value_table()) != want: continue
        if best is None or len(c2.gates) < len(best.gates): best = c2
    return best


def _key(c):
    m = c.metrics(); return (m['G'], m['GD'])


def polish(c, seeds, bp_runs, rng, rounds=3, log=lambda *x: None):
    """alternating trb top / trb bottom / BP top passes at the circuit's GD; each kept only if (G, GD)
    improves and A, AD stay"""
    import bp
    want = tuple(c.value_table()); m0 = c.metrics(); A0, AD0 = m0['A'], m0['AD']
    for r in range(rounds):
        before = _key(c)
        D = c.metrics()['GD']
        for region in ('top', 'bottom'):
            c2 = _rebuild_best(c, D, region, seeds, rng, want)
            if c2 is not None and _key(c2) < _key(c) and c2.metrics()['A'] == A0 and c2.metrics()['AD'] == AD0: c = c2
        if bp_runs:
            try:
                c2, info = bp.optimise(c, D, 'top', random.Random(rng.random()), bp_runs, log=lambda *x: None)
            except Exception as e:                      # bp has no failure contract; be safe
                log('bp failed: %r' % (e,)); c2 = None
            if c2 is not None:
                c2 = clean(c2)
                if tuple(c2.value_table()) == want and _key(c2) < _key(c) and c2.metrics()['A'] == A0: c = c2
        if _key(c) >= before: break
    return c


class _Timeout(Exception):
    pass


def _timed(seconds, fn, *args, **kw):
    """fn(*args, **kw) with a wall-clock limit (SIGALRM via setitimer; main thread only): raises _Timeout.
    bp.bp_run's exact distance table is 2^leaves entries per step, so a bottom region with 20-22 leaves
    can take minutes."""
    import signal

    def on(sig, frm):
        raise _Timeout()
    old = signal.signal(signal.SIGALRM, on)
    signal.setitimer(signal.ITIMER_REAL, max(0.01, seconds))
    try:
        return fn(*args, **kw)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0); signal.signal(signal.SIGALRM, old)


def build_slp(start, In, cin, Out, cout, seeds, bp_runs, rng, log=lambda *x: None, bp_seconds=20.0):
    """the gate-cheap transport: shared SLP networks for In and Out (wrap_slp), then Boyar-Peralta re-synthesis
    of the top and of the bottom region without a depth cap (each kept if it saves gates; at most bp_seconds
    each), then polish"""
    import bp
    t0 = time.time()
    c = clean(wrap_slp(start, In, cin, Out, cout, rng, max(4, bp_runs)))
    want = tuple(wrap(start, In, cin, Out, cout).value_table())
    assert tuple(c.value_table()) == want
    info = {'variant': 'slp', 'slp': list(CM.metrics(c))}
    for region in ('top', 'bottom'):
        t_r = time.time(); nto = 0
        for r in range(max(1, bp_runs)):                # one BP run per call, each time-limited (a run is
            left_ = bp_seconds - (time.time() - t_r)    # seconds to minutes on 20-22 leaves)
            if left_ <= 0.5: break
            try:
                c2, i2 = _timed(min(left_, bp_seconds / 2), bp.optimise, c, 99, region, random.Random(rng.random()), 1,
                                log=lambda *x: None)
            except _Timeout:
                nto += 1; c2 = None
            except Exception as e:
                log('bp %s failed: %r' % (region, e)); c2 = None; break
            if c2 is not None:
                c2 = clean(c2)
                if tuple(c2.value_table()) == want and len(c2.gates) < len(c.gates) and CM.metrics(c2)[:2] == CM.metrics(c)[:2]: c = c2
        if nto: info['bp_%s_timeouts' % region] = nto
        info['bp_' + region] = list(CM.metrics(c))
    c = polish(c, seeds, bp_runs, rng, log=log)
    info['final'] = list(CM.metrics(c)); info['seconds'] = round(time.time() - t0, 2)
    assert tuple(c.value_table()) == want
    return c, info


def build(start, In, cin, Out, cout, D, seeds, bp_runs, rng, log=lambda *x: None):
    """the depth-aware transport at gate-depth cap D (see the top); returns (circuit, info).  The circuit
    computes Out(start(In v + cin)) + cout; D is raised to the depth of the flat version (one depth-optimal
    tree per top form and per output) when below it."""
    info = {'variant': 'depth', 'cap': D}
    t0 = time.time()
    flat = flat_bottom(flat_top(start, In, cin), Out, cout)     # one depth-optimal tree per top form and output
    want = tuple(wrap(start, In, cin, Out, cout).value_table())
    assert tuple(flat.value_table()) == want
    info['flat'] = list(CM.metrics(flat)); gd_min = flat.metrics()['GD']
    D = max(D, gd_min); info['cap_used'] = D                     # below gd_min no rebuild of these layers exists
    c = flat
    for region in ('top', 'bottom'):
        c2 = _rebuild_best(c, D, region, seeds, rng, want)
        if c2 is not None and _key(c2) < _key(c): c = c2
        info[region] = list(CM.metrics(c))
    c = polish(c, seeds, bp_runs, rng, log=log)
    info['final'] = list(CM.metrics(c)); info['seconds'] = round(time.time() - t0, 2)
    assert tuple(c.value_table()) == want
    return c, info


# ---- screen of the (lam, k) ------------------------------------------------------------------------

def screen(start, src, runs=2, seed=1):
    """rows {lam, k, top, bot, sum, wmax} for all 2040 (lam, k): conj3 proxies of the transported layers
    (BP gate count of the new top forms, Paar count of the new output forms over the bottom leaves) and
    the largest new top-form weight, sorted by (sum, wmax, lam, k)"""
    import conj3 as C3
    top, outs, nl = C3.layers(start)
    rows = []
    for k in range(8):
        for lam in range(1, 256):
            In, cin, Out, cout = maps(src, lam, k)
            urow = [sum(1 << (7 - j) for j in range(8) if In[j] >> (7 - i) & 1) for i in range(8)]
            ntop = []
            for t in top:
                v = 0
                for i in range(8):
                    if t >> i & 1: v ^= urow[i]
                ntop.append(v)
            ct = C3.bp_cost(8, ntop, runs, random.Random(seed * 4096 + lam * 8 + k))
            nouts = []
            for i in range(8):
                v = 0
                for j in range(8):
                    if Out[j] >> (7 - i) & 1: v ^= outs[7 - j]
                nouts.append(v)
            cb = C3.paar(nouts) if nl <= 64 else sum(bin(v).count('1') - 1 for v in nouts)
            wmax = max((bin(v).count('1') for v in ntop), default=0)
            rows.append({'lam': lam, 'k': k, 'top': ct, 'bot': cb, 'sum': (99 if ct is None else ct) + cb, 'wmax': wmax})
    rows.sort(key=lambda r: (r['sum'], r['wmax'], r['lam'], r['k']))
    return rows


def map_list(spec, start, src, a, log):
    items = []; rows = None
    for it in spec.split(','):
        it = it.strip()
        if not it: continue
        if it == 'id':
            items.append((1, 0, 'id'))
        elif it.startswith('depth:'):
            # depth screen: GD (then G) of the flat transport (one depth-optimal tree per top form and per
            # output, middle unchanged) for all 2040 (lam, k); its GD is the least GD any re-synthesis of the
            # two linear layers can reach with this AND structure and these middle layers
            t1 = time.time(); drows = []
            for k in range(8):
                for lam in range(1, 256):
                    In, cin, Out, cout = maps(src, lam, k)
                    m = CM.metrics(flat_bottom(flat_top(start, In, cin), Out, cout))
                    drows.append({'lam': lam, 'k': k, 'GD': m[3], 'G': m[2]})
            drows.sort(key=lambda r: (r['GD'], r['G'], r['lam'], r['k']))
            hist = {}
            for r in drows: hist[r['GD']] = hist.get(r['GD'], 0) + 1
            a._depth_screen = {'seconds': round(time.time() - t1, 1), 'gd_histogram': hist, 'top10': drows[:10],
                               'identity': next(r for r in drows if (r['lam'], r['k']) == (1, 0))}
            log('depth screen of 2040 (lam, k) in %.0f s; flat GD histogram %s; best %s' % (time.time() - t1, sorted(hist.items()), drows[:3]))
            N = int(it[6:]); got = 0
            for r in drows:
                if got >= N: break
                if any((x[0], x[1]) == (r['lam'], r['k']) for x in items): continue
                items.append((r['lam'], r['k'], 'depth rank %d (flat GD %d G %d)' % (got + 1, r['GD'], r['G']))); got += 1
        elif it.startswith('screen:'):
            if rows is None:
                t1 = time.time(); rows = screen(start, src, a.screen_runs, a.seed)
                log('screen of 2040 (lam, k) in %.0f s; best %s' % (time.time() - t1, rows[:3]))
                a._screen = {'seconds': round(time.time() - t1, 1), 'top10': rows[:10],
                             'identity': next(r for r in rows if r['lam'] == 1 and r['k'] == 0)}
            N = int(it[7:]); got = 0
            for r in rows:
                if got >= N: break
                if (r['lam'], r['k']) == (1, 0) or any((x[0], x[1]) == (r['lam'], r['k']) for x in items): continue
                items.append((r['lam'], r['k'], 'screen rank %d (score %s)' % (got + 1, r['sum']))); got += 1
        else:
            lam, k = map(int, it.split(':'))
            if not any((x[0], x[1]) == (lam, k) for x in items): items.append((lam, k, '%d:%d' % (lam, k)))
    return items


def pull_schedule(s, gd_start):
    """conjpull schedule with start-relative caps: a cap 's', 's+N' or 's-N' is START's GD (+/- N) (an
    absolute cap for conjpull); '+N'/'-N' (relative to the stage input) and plain numbers pass unchanged"""
    out = []
    for x in s.split(','):
        x = x.strip()
        if not x: continue
        p = x.split(':')
        if p[1].startswith('s'):
            p[1] = str(gd_start + int(p[1][1:] or 0))
        out.append(':'.join(p))
    return ','.join(out)


# ---- main --------------------------------------------------------------------------------------------

def main(argv=None):
    ap = CM.contract_args(argparse.ArgumentParser(description=__doc__.split('\n')[0]))
    ap.add_argument('--maps', default='id,188:0,189:0,screen:3')
    ap.add_argument('--ladder', default='-1,0,1,2')
    ap.add_argument('--synth-seeds', type=int, default=6)
    ap.add_argument('--bp-runs', type=int, default=6)
    ap.add_argument('--build-seconds', type=float, default=None)
    ap.add_argument('--pull', default='g:+0:150,m:+0:150,m:-1:170')
    ap.add_argument('--pull-deep', default='g:+0:120,m:s+2:150,m:s:200',
                    help="schedule for a build deeper than START's GD + --deep-margin ('' = --pull for every build)")
    ap.add_argument('--deep-margin', type=int, default=1)
    ap.add_argument('--pull-n', type=int, default=2)
    ap.add_argument('--screen-runs', type=int, default=2)
    ap.add_argument('--kernel', default=None, help='kernel binary for the pulls (default: conjpull\'s)')
    a = ap.parse_args(argv)
    T0 = time.time(); T_END = T0 + a.seconds
    src = aesfn.resolve('auto', a.inp)
    dst = OTHER[src] if a.function in (None, 'auto') else aesfn.name(a.function)
    if dst == src:
        raise SystemExit('--function %s is the function START computes; transport builds the other one' % dst)
    aesfn.use(dst)                                       # the process's function: every check and the NIST set
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    logf = open(out / 'transport.log', 'a')
    def log(*x):
        logf.write('%s %7.1f %s\n' % (time.strftime('%H:%M:%S', time.gmtime()), time.time() - T0, ' '.join(map(str, x)))); logf.flush()
    build_s = a.build_seconds if a.build_seconds is not None else min(300.0, a.seconds / 4)
    ladder = [int(x) for x in a.ladder.split(',') if x.strip()]
    params = {'from': src, 'to': dst, 'maps': a.maps, 'ladder': ladder, 'synth_seeds': a.synth_seeds,
              'bp_runs': a.bp_runs, 'build_seconds': build_s, 'pull': a.pull, 'pull_deep': a.pull_deep,
              'deep_margin': a.deep_margin, 'pull_n': a.pull_n,
              'screen_runs': a.screen_runs}
    command = ' '.join([sys.executable, str(Path(__file__).resolve())] + list(argv if argv is not None else sys.argv[1:]))
    method = ('ops/transport.py: %s -> %s transport (%s), affine maps folded into the first and last linear layers '
              '(trb Paar with Kraft deadlines at gate-depth caps start GD %s, then trb/Boyar-Peralta polish)%s' % (
                  aesfn.label(src), aesfn.label(dst),
                  'S^-1 = Aff^-1 o F o Aff^-1' if src == 'aes-sbox' else 'S = Aff o I o Aff',
                  a.ladder, (', then conjpull staged pull --conj id %s' % a.pull) if a.pull else ''))
    rec = CM.Recorder(out, OP, a.target, a.inp, a.seed, command, method, params, t0=T0, budget_s=a.seconds,
                      seeds={'build_rng': 'random.Random(seed x 100003 + lam x 8 + k) per map',
                             'pull_seed': 'seed x 10 + pull index'})
    rec.skip_start_tuple = False                         # the start computes the other function
    status = 'ok'; builds = []; pulls = []
    try:
        start = CM.load(a.inp)
        assert tuple(start.value_table()) == aesfn.table(src)
        m0 = CM.metrics(start); log('start', src, m0, a.inp)
        items = map_list(a.maps, start, src, a, log)
        rec.log.event('maps', items=[list(x) for x in items], screen=getattr(a, '_screen', None),
                      depth_screen=getattr(a, '_depth_screen', None))
        t_b = time.time()
        for lam, k, label in items:
            if time.time() - t_b > build_s and builds:
                rec.log.event('stop', what='builds', reason='build time over', left=[list(x) for x in items[items.index((lam, k, label)):]])
                break
            In, cin, Out, cout = maps(src, lam, k)
            rng = random.Random(a.seed * 100003 + lam * 8 + k)
            seen = set()
            for dD in [None] + ladder:                   # None = the gate-cheap SLP variant
                if dD is None:
                    c, info = build_slp(start, In, cin, Out, cout, a.synth_seeds, a.bp_runs, rng, log); tag = 'slp'
                else:
                    D = m0[3] + dD
                    c, info = build(start, In, cin, Out, cout, D, a.synth_seeds, a.bp_runs, rng, log)
                    tag = 'cap%d' % info['cap_used']
                    if info['cap_used'] in seen: continue
                    seen.add(info['cap_used'])
                assert tuple(c.value_table()) == aesfn.table(dst)
                lin = ['transport %s -> %s' % (src, dst)] + ([] if (lam, k) == (1, 0) else ['conj lam %d k %d (%s)' % (lam, k, label)]) + \
                      ['synth %s -> %s' % (tag, '/'.join(map(str, CM.metrics(c))))]
                p = rec.offer(c, how='transport %d:%d %s' % (lam, k, tag), lineage=lin, path_certified=True)
                if p is None:                            # keep the build for the pull even when not job-Pareto
                    d = out / 'builds'; d.mkdir(exist_ok=True)
                    p = d / ('build-%d-%d-%s.circ.txt' % (lam, k, tag))
                    p.write_text(core.write_ncff(c, CM.MODEL, comments=['transport build %d:%d %s (not recorded: '
                                                                        'dominated in this job)' % (lam, k, tag)]))
                b = {'lam': lam, 'k': k, 'label': label, 'variant': tag, 'tuple': list(CM.metrics(c)), 'file': str(p),
                     'recorded': rec.points.get(CM.metrics(c), {}).get('file') == str(p), 'info': info}
                builds.append(b)
                rec.log.event('build', **b)
                log('build', label, lam, k, tag, info)
        rec.write_result({'builds': builds})
        # choose the builds to pull: fewest G, lowest GD, then by G + GD
        if a.pull and a.pull_n > 0 and builds:
            chosen = []
            for b in (sorted(builds, key=lambda b: (b['tuple'][2], b['tuple'][3]))[:1] +           # fewest gates
                      sorted(builds, key=lambda b: (b['tuple'][3], b['tuple'][2]))[:1] +           # lowest GD
                      sorted(builds, key=lambda b: (b['tuple'][2] + b['tuple'][3], b['tuple'][2]))):
                if len(chosen) >= a.pull_n: break
                if all(b['tuple'] != x['tuple'] for x in chosen): chosen.append(b)
            for i, b in enumerate(chosen):
                rem = T_END - time.time() - 30
                secs = rem / (len(chosen) - i)
                if secs < 120:
                    rec.log.event('stop', what='pulls', reason='less than 120 s for a pull', done=i, of=len(chosen)); break
                pd = out / ('pull-%d' % i)
                deep = a.pull_deep and b['tuple'][3] > m0[3] + a.deep_margin
                sched = pull_schedule(a.pull_deep if deep else a.pull, m0[3])
                cmd = [sys.executable, str(HERE / 'conjpull.py'), '--in', b['file'], '--target', a.target,
                       '--seed', str(a.seed * 10 + i), '--seconds', str(int(secs)), '--out', str(pd),
                       '--function', dst, '--conj', 'id', '--schedule', sched]
                if a.kernel: cmd += ['--kernel', a.kernel]
                t1 = time.time()
                log('pull', i, b['tuple'], ' '.join(cmd))
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=secs + 120)
                res = {}
                try: res = json.loads((pd / 'result.json').read_text())
                except Exception: pass
                pl = {'index': i, 'from': b['file'], 'from_tuple': b['tuple'], 'dir': str(pd), 'rc': r.returncode,
                      'schedule': sched, 'deep_build': bool(deep), 'variant': b['variant'], 'lam': b['lam'], 'k': b['k'],
                      'seconds': round(time.time() - t1, 1), 'command': cmd,
                      'pareto_A_AD_G_GD': [x['tuple'] for x in res.get('pareto_A_AD_G_GD', [])],
                      'files': [x['file'] for x in res.get('pareto_A_AD_G_GD', [])]}
                if r.returncode != 0: pl['stderr'] = r.stderr[-1500:]
                pulls.append(pl); rec.log.event('pull', **pl)
                log('pull', i, 'rc', r.returncode, pl['pareto_A_AD_G_GD'])
                rec.write_result({'builds': builds, 'pulls': pulls})
    except Exception as e:
        import traceback
        status = 'error'; rec.notes.append(traceback.format_exc()[-1500:]); log('ERROR', repr(e))
    rec.finish(status, {'builds': builds, 'pulls': pulls})
    log('end', status, 'written', len(rec.points))
    return 0 if status == 'ok' else 1


if __name__ == '__main__':
    sys.exit(main())
