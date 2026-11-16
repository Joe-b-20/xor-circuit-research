#!/usr/bin/env python3
"""satlns: span-pooled SAT LNS as a method script for any target (ops/common.py target()), under the
operator contract of ops/common.py:

    python3 search/nonlinear/boolflux/ops/satlns.py --in START.circ.txt --target REF \
        --seed S --seconds T --out DIR [--cpus 1] [--gd D] [--profile fast|basic] [...]

Method (each SAT query is exact; the search around them is a heuristic):
  * span pool: every indexed circuit (span index, see --build-index) whose 1 + 8 inputs + AND
    truth tables span the same space as the start's is pooled; every signal is a coordinate vector
    over the start's basis.  Templates: the pooled gates (XOR / XNOR / NOT / AND with the two free
    AND variants (L, L^R^1), (L^R^1, R)), a closure (XOR of two pooled forms that is a pooled form,
    at most --closure-max) and a rotation closure of the start (re-bracketed XOR pairs).
  * SAT model (glucose4): availability a(f, l) = form f at gate level <= l, outputs at level <= D
    (= the GD cap of the query), at most A_cap AND templates, at most K templates (ITotalizer).
  * LNS: the current circuit's templates outside a neighbourhood are forced.  Query kinds:
      side   K = G, at least one freed template dropped ("sideways": same or smaller G, other
             structure; a SAT answer with G' < G is an improvement found sideways);
      imp    K = G - 1;
      focus  K = G - 1 on the region a just-accepted sideways move changed (its new templates
             plus 1-2 hops of fan-in / fan-out);
    restriction level rl: 0 = whole pool, 1 = only templates that produce a freed form or read two
    current forms, 2 = also forms one step from the current forms.
  * every SAT answer is decoded, checked on all 256 inputs and accepted as the new walk state only
    if A <= A_cap, GD <= D and (unless --walk-ad-free) AD <= AD_cap.  Circuits recorded in DIR must
    pass aes_check.py and be inside the target's hard limits (A <= ref A, AD <= ref AD) and be
    Pareto-new in (G, GD) for this run (start tuple included).
  * optional short kernel polish (bfx, repair_keep 1, caps A/AD/D) every --polish-every accepted
    sideways moves; an improving polish result starts a new epoch (model rebuilt around it).
  * epochs: every --epoch seconds the model is rebuilt around the current walk state (new
    rotation closure).
  * excursions (--excursion N; search states may exceed the caps, recorded circuits never do): after N
    accepted sideways moves the walk continues at GD cap D + --exc-up for --exc-moves moves, then
    "pull" queries at cap D (K = G; free = gates deeper than D - w plus 5 % random) bring it back;
    after --pull-tries failures the walk reverts to the state before the excursion.
  * time per query: timer interrupt plus a propagation budget (--prop-rate x limit).  Unrestricted
    (rl 0) and pull queries still overrun their limit now and then (up to 162 s at 8 s); restricted
    queries (plan S1, focus) never did, so in the last 90 s only rl-1 queries run (contract: exit <= T + 60;
    observed wall <= T + 27 s in 28 runs before this rule).
  * plan time budgets (--budget): a query plan above its share of the SAT time is re-drawn.

Profile fast (default): weighted query plans (PLANS below; S = sideways, I = improving, the digit = the
restriction level), tuned on about 27,000 logged queries of earlier runs.  Profile basic: the earlier
fixed mix (--side share of sideways queries, --restrict, --lns-sec per query), kept for comparisons.
Span index: --build-index (incremental; also refreshed at every start unless --no-index-update).
Needs python-sat (pysat).
"""
import argparse
import hashlib
import json
import os
import random
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent              # search/nonlinear/boolflux/ops
PKG = HERE.parent                                   # search/nonlinear/boolflux
REPO = PKG.parents[2]
sys.path.insert(0, str(PKG.parent))
from boolflux import core, targets                  # noqa: E402
from boolflux import objective as OBJ               # noqa: E402
sys.path.insert(0, str(HERE))
import common as OC                                 # noqa: E402  (Recorder, aes_check wrapper, limits)

INDEX_DEFAULT = OC.CACHE / 'spanindex.json'          # aes-sbox; spanindex-<function>.json otherwise
AES_CHECK = PKG / 'aes_check.py'

AND, XOR, XNOR, NOT = 8, 6, 9, 3
TAB = tuple(targets.aes_sbox())                      # set to the process's function in main()
ONES = (1 << 256) - 1
STOP = {'flag': False}


def utc(t=None):
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(t))


def sha256f(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(p):
    t = Path(p).read_text()
    return core.from_kernel(t) if str(p).endswith('.bfx') else core.read_ncff(t)


M = core.Model.load('nist')


def tup(c):
    m = c.metrics(M)
    return (m['A'], m['AD'], m['G'], m['GD'])


def kid(c):
    return hashlib.sha1(core.to_kernel(c).encode()).hexdigest()


# ---------------------------------------------------------------- span index
def basis_of(c):
    tabs = c.tables(); n = c.n
    return [ONES] + tabs[:n] + [tabs[n + j] for j, (op, a, b) in enumerate(c.gates) if op == AND]


def span_key(c):
    piv = {}
    for v in basis_of(c):
        while v:
            h = v.bit_length() - 1
            if h in piv: v ^= piv[h]
            else: piv[h] = v; break
    ks = sorted(piv)
    for i, h in enumerate(ks):
        for h2 in ks[i + 1:]:
            if (piv[h2] >> h) & 1: piv[h2] ^= piv[h]
    return '%d-' % len(ks) + hashlib.sha1(b''.join(piv[h].to_bytes(33, 'big') for h in ks)).hexdigest()[:16]


def index_dirs(extra=()):
    """(dir, recursive) of the circuit sources: our circuits of the function (circuits/aes-sbox/ or
    circuits/aes-invsbox/), NIST's (seeds/aes-sbox/ or seeds/aes-invsbox/), the folders in
    $BOOLFLUX_POOL_DIRS (os.pathsep-separated), plus extra dirs."""
    fi = OC.aesfn.INFO[OC.aesfn.name()]
    out = [(REPO / 'circuits' / fi['circuits_dir'], False), (PKG.parent / 'seeds' / fi['seed_dir'], False)]
    out += [(Path(d), True) for d in os.environ.get('BOOLFLUX_POOL_DIRS', '').split(os.pathsep) if d]
    out += [(Path(d), True) for d in extra]
    return out


def build_index(path, extra=(), quiet=False):
    """Incremental span index {path: {mt, sz, k, m, span}} (bad / non-AES files: {'bad': 1})."""
    path = Path(path)
    old = json.loads(path.read_text()) if path.exists() else {}
    new = {}; n_new = 0; t0 = time.time()
    for d, rec in index_dirs(extra):
        if not d.exists(): continue
        it = d.rglob('*') if rec else d.iterdir()
        for p in it:
            if not (p.is_file() and (p.name.endswith('.circ.txt') or p.name.endswith('.bfx'))): continue
            sp = str(p); st = p.stat()
            o = old.get(sp)
            if o and o.get('mt') == st.st_mtime and o.get('sz') == st.st_size:
                new[sp] = o; continue
            try:
                c = load(p)
                if tuple(c.value_table()) != TAB: raise ValueError('not AES')
                new[sp] = {'mt': st.st_mtime, 'sz': st.st_size, 'k': kid(c)[:16], 'm': list(tup(c)), 'span': span_key(c)}
            except Exception:
                new[sp] = {'mt': st.st_mtime, 'sz': st.st_size, 'bad': 1}
            n_new += 1
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp%d' % os.getpid()); tmp.write_text(json.dumps(new)); os.replace(tmp, path)
    if not quiet:
        spans = {}
        for r in new.values():
            if 'span' in r: spans[r['span']] = spans.get(r['span'], 0) + 1
        print(json.dumps({'index': str(path), 'files': len(new), 'new_or_changed': n_new, 'spans': len(spans),
                          'largest': sorted(spans.values())[-5:], 's': round(time.time() - t0, 1)}), flush=True)
    return new


# ---------------------------------------------------------------- algebra
class Span:
    def __init__(self, vecs):
        self.ech = {}
        for i, v in enumerate(vecs):
            cm = 1 << i
            while v:
                h = v.bit_length() - 1
                if h in self.ech:
                    ev, ec = self.ech[h]; v ^= ev; cm ^= ec
                else:
                    self.ech[h] = (v, cm); break
            else:
                raise ValueError('basis vectors dependent')

    def coords(self, t):
        cm = 0
        while t:
            h = t.bit_length() - 1
            if h not in self.ech: return None
            ev, ec = self.ech[h]; t ^= ev; cm ^= ec
        return cm


def forms_of(c, sp):
    F = []
    for t in c.tables():
        f = sp.coords(t)
        if f is None: return None
        F.append(f)
    return F


def tkey(op, F, a, b, f):
    if op == AND:
        L, R = sorted((F[a], F[b])); return ('A', f, L, R)
    if op == NOT: return ('L', f, F[a], F[a])
    x, y = sorted((F[a], F[b])); return ('L', f, x, y)


class Model:
    """SAT model of all circuits buildable from the pooled templates with GD <= D, A <= cap_a."""

    def __init__(self, start, pool, D, cap_a, a, log):
        T0 = time.time()
        self.start = start; self.D = D; self.cap_a = cap_a
        n = start.n; self.n = n
        try:
            sp = Span(basis_of(start))
        except ValueError:
            raise RuntimeError('start has dependent AND tables (redundant AND): no span basis')
        self.sp = sp
        circs = [start]
        for c in pool:
            if forms_of(c, sp) is not None: circs.append(c)
        tmpl = set(); outs = None
        for c in circs:
            F = forms_of(c, sp)
            o = [F[s] for s in c.outputs]
            if outs is None: outs = o
            if o != outs: continue
            for j, (op, x, y) in enumerate(c.gates):
                f = F[n + j]; t = tkey(op, F, x, y, f); tmpl.add(t)
                if op == AND:
                    _, _, L, R = t
                    tmpl.add(('A', f) + tuple(sorted((L, L ^ R ^ 1)))); tmpl.add(('A', f) + tuple(sorted((L ^ R ^ 1, R))))
        forms = {t[1] for t in tmpl} | {t[2] for t in tmpl} | {t[3] for t in tmpl} | set(outs)
        inputs = {1 << (1 + i) for i in range(n)}
        forms |= inputs
        base_t = len(tmpl); nrot = 0
        if a.rot:
            F = forms_of(start, sp); kind = {}
            for j, (op, x, y) in enumerate(start.gates):
                if op in (XOR, XNOR): kind[n + j] = (x, y)
            new_t = set()
            for j, (op, x, y) in enumerate(start.gates):
                if op not in (XOR, XNOR): continue
                f = F[n + j]
                for xx, yy in ((x, y), (y, x)):
                    if xx not in kind: continue
                    u, v = kind[xx]
                    for p_, q_ in ((u, v), (v, u)):
                        g = F[q_] ^ F[yy]
                        if g & ~1 == 0: continue
                        g &= ~1
                        new_t.add(('L', g) + tuple(sorted((F[q_], F[yy]))))
                        new_t.add(('L', f) + tuple(sorted((F[p_], g))))
            for t in new_t:
                if t not in tmpl: tmpl.add(t); nrot += 1
                forms.add(t[1]); forms.add(t[2]); forms.add(t[3])
        if a.closure:
            fl = sorted(forms); added = 0
            for i, x in enumerate(fl):
                if added > a.closure_max: break
                for y in fl[i + 1:]:
                    s_ = x ^ y
                    if s_ in forms and s_ != x and s_ != y: tmpl.add(('L', s_, x, y)); added += 1
                    if (s_ ^ 1) in forms and (s_ ^ 1) != x and (s_ ^ 1) != y: tmpl.add(('L', s_ ^ 1, x, y)); added += 1
                if (x ^ 1) in forms: tmpl.add(('L', x ^ 1, x, x))
        self.inputs = inputs; self.forms = forms; self.outs = outs
        by_f = {}
        for t in tmpl: by_f.setdefault(t[1], []).append(t)
        self.by_f = by_f
        INF = 10 ** 6
        lev = {f: (0 if f in inputs else INF) for f in forms}
        changed = True
        while changed:
            changed = False
            for f in forms:
                if f in inputs: continue
                b = lev[f]
                for t in by_f.get(f, ()):
                    v = 1 + max(lev[t[2]], lev[t[3]])
                    if v < b: b = v
                if b < lev[f]: lev[f] = b; changed = True
        self.lev = lev
        from pysat.formula import IDPool
        from pysat.card import CardEnc, EncType, ITotalizer
        from pysat.solvers import Solver
        pool_ = IDPool(); cl = []; self.pool = pool_
        sel = {}; self.sel = sel

        def S(t):
            if t not in sel: sel[t] = pool_.id(('s', t))
            return sel[t]
        for f in forms:
            if f in inputs or lev[f] > D: continue
            for l in range(lev[f], D + 1):
                v = self.av(f, l)
                if l < D: cl.append([-v, self.av(f, l + 1)])
                alts = []
                for t in by_f.get(f, ()):
                    ax, ay = self.av(t[2], l - 1), self.av(t[3], l - 1)
                    if ax is False or ay is False: continue
                    w = pool_.id(('w', t, l)); alts.append(w)
                    cl.append([-w, S(t)])
                    if ax is not True: cl.append([-w, ax])
                    if ay is not True: cl.append([-w, ay])
                cl.append([-v] + alts)
        self.trivial_unsat = False
        for o in outs:
            v = self.av(o, D)
            if v is False: self.trivial_unsat = True
            elif v is not True: cl.append([v])
        svars = list(sel.values()); avars = [sel[t] for t in sel if t[0] == 'A']
        cardA = CardEnc.atmost(lits=avars, bound=cap_a, vpool=pool_, encoding=EncType.seqcounter)
        G0 = tup(start)[2]
        self.ub = min(len(svars), G0 + 2)
        # ITotalizer auxiliaries numbered from pool.top + 1 (numbered from 1 they collide with the model's variables)
        self.tot = ITotalizer(lits=svars, ubound=self.ub, top_id=pool_.top)
        pool_.top = max(pool_.top, self.tot.top_id)
        self.s = Solver(name=a.solver, bootstrap_with=cl + cardA.clauses + self.tot.cnf.clauses)
        self.info = {'circuits': len(circs), 'forms': len(forms), 'templates_pooled': base_t, 'templates': len(tmpl),
                     'and_templates': sum(1 for t in tmpl if t[0] == 'A'), 'rot_templates': nrot, 'D': D,
                     'vars': pool_.top, 'clauses': len(cl), 'sel': len(svars), 't_build': round(time.time() - T0, 1)}
        log(dict(event='model', **self.info))

    def av(self, f, l):
        if f in self.inputs: return True
        if l < self.lev[f] or l > self.D: return False
        return self.pool.id(('a', f, l))

    def decode(self, model):
        D = self.D; minlev = {}
        for f in self.forms:
            if f in self.inputs: minlev[f] = 0; continue
            for l in range(self.lev[f], D + 1):
                v = self.av(f, l)
                if v is not False and v is not True and v in model: minlev[f] = l; break
        just = {}; need = list(self.outs)
        while need:
            f = need.pop()
            if f in self.inputs or f in just: continue
            l = minlev[f]; ch = None
            for t in self.by_f.get(f, ()):
                k = self.pool.obj2id.get(('w', t, l))
                if k is not None and k in model and self.sel.get(t) in model: ch = t; break
            assert ch is not None, 'no justification'
            just[f] = ch; need += [ch[2], ch[3]]
        order = sorted(just, key=lambda f: minlev[f])
        n = self.n; sig = {1 << (1 + i): i for i in range(n)}; gates = []
        for f in order:
            t = just[f]; x, y = t[2], t[3]
            if t[0] == 'A': gates.append((AND, sig[x], sig[y]))
            elif x == y: gates.append((NOT, sig[x], sig[x]))
            else: gates.append((XNOR if (x ^ y ^ f) == 1 else XOR, sig[x], sig[y]))
            sig[f] = n + len(gates) - 1
        return core.Circuit(n, len(self.outs), gates, [sig[o] for o in self.outs], 'satlns').live()

    def tset(self, c):
        F = forms_of(c, self.sp)
        if F is None: return None
        n = self.n; ts = []; lg = [0] * n
        for j, (op, x, y) in enumerate(c.gates):
            lg.append(1 + max(lg[x], lg[y]))
            ts.append((tkey(op, F, x, y, F[n + j]), lg[-1], n + j))
        return ts


# ---------------------------------------------------------------- query plans
# (name, side, rl, scale choices, min free, max free, time limit factor) ; weight
# name: S = sideways (K = G), I = improving (K = G - 1), digit = restriction level rl.
# Tuning: a first mix (S1 .60 S2 .10 S0 .08 I1 .14 I2 .08, focus p .5) gave no SAT answer to I1/I2 in 1,484
# queries (130@19 start, 4 x 900 s) but spent 37 % of the SAT time on them; in 15 later runs (32k queries,
# 8,945 SAT-s) every G drop came from focus queries (10.7k queries, 16 % of the time), none from S0 (26 %),
# S2 (14 %) or I1 + I2 (19 %).  S1 moves the walk (14 %).  Hence the weights below.
PLANS = {
    'fast': [(('S1', True, 1, (1, 1, 2, 3), 0, 10 ** 6, 1.0), 0.80),
             (('S2', True, 2, (1, 1, 2), 0, 40, 2.0), 0.08),
             (('S0', True, 0, (1,), 0, 30, 4.0), 0.04),
             (('I1', False, 1, (2, 3, 4), 30, 10 ** 6, 1.5), 0.05),
             (('I2', False, 2, (1, 2), 15, 60, 2.0), 0.03)],
}


def neighbourhood(rng, kind, sc, cur, cur_ts, D):
    N_ = len(cur_ts); n = cur.n
    if kind == 'rand':
        p = sc * rng.choice([0.06, 0.1, 0.15, 0.2]); return {i for i in range(N_) if rng.random() < p}
    if kind == 'level':
        w = sc - 1 + rng.choice([1, 2, 2, 3]); l0 = rng.randint(1, max(1, D - w))
        return {i for i, (t, l, sgi) in enumerate(cur_ts) if l0 <= l < l0 + w}
    idx = {sgi: i for i, (t, l, sgi) in enumerate(cur_ts)}
    free = set()
    if kind == 'and':
        ands = [i for i, (t, l, sgi) in enumerate(cur_ts) if t[0] == 'A']
        pick = set(rng.sample(ands, min(len(ands), sc * rng.choice([1, 2, 3]))))
        free = set(pick)
        for i in pick:
            st = [cur_ts[i][2]]
            for _d in range(rng.choice([2, 3])):
                nx = []
                for sgi in st:
                    if sgi in idx:
                        free.add(idx[sgi]); op, x, y = cur.gates[sgi - n]; nx += [x, y]
                st = nx
            for j, (t, l, sgi) in enumerate(cur_ts):
                op, x, y = cur.gates[sgi - n]
                if cur_ts[i][2] in (x, y): free.add(j)
        return free
    for _ in range(sc * rng.choice([1, 2, 3])):
        st = [rng.choice(list(idx))]
        for _d in range(rng.choice([2, 3, 4])):
            nx = []
            for sgi in st:
                if sgi in idx and idx[sgi] not in free:
                    free.add(idx[sgi]); op, x, y = cur.gates[sgi - n]; nx += [x, y]
            st = nx
    return free


def grow(cur, cur_ts, seeds, hops):
    """seed gate indices (into cur_ts) plus `hops` steps of fan-in and fan-out"""
    n = cur.n; idx = {sgi: i for i, (t, l, sgi) in enumerate(cur_ts)}
    readers = {}
    for i, (t, l, sgi) in enumerate(cur_ts):
        op, x, y = cur.gates[sgi - n]
        for s in (x, y): readers.setdefault(s, []).append(i)
    free = set(seeds); front = set(seeds)
    for _ in range(hops):
        nx = set()
        for i in front:
            sgi = cur_ts[i][2]; op, x, y = cur.gates[sgi - n]
            for s in (x, y):
                if s in idx: nx.add(idx[s])
            nx.update(readers.get(sgi, ()))
        nx -= free; free |= nx; front = nx
    return free


# ---------------------------------------------------------------- kernel polish
def kernel_polish(c, caps, seconds, seed, wdir, kbin, objective='a,cost,gd'):
    wdir.mkdir(parents=True, exist_ok=True)
    sp = wdir / 'start.bfx'; sp.write_text(core.to_kernel(c)); bp = wdir / 'best.bfx'
    if bp.exists(): bp.unlink()
    cfg = {'T0': 0.6, 'Tperiod_it': 20000, 'stall_it': 60000, 'uphill': 1.0, 'max_excess': 8,
           'mv.resub1': 1, 'mv.resub2': 2, 'mv.resub3': 1, 'dmax': 220, 'pdiv': 90,
           'nl_samples': 12, 'cand_cap': 40, 'fraig': 1, 'repair_keep': 1}
    cfg.update(OBJ.weights(objective))
    for op in (8, 6, 9, 3): cfg['cost.%d' % op] = 1
    cfg.update({'cap.a': caps[0], 'cap.ad': caps[1], 'cap.gd': caps[2], 'in': sp, 'out': bp, 'seed': seed, 'seconds': seconds})
    cp = wdir / 'kernel.cfg'; cp.write_text(''.join('%s %s\n' % kv for kv in cfg.items()))
    with open(wdir / 'kernel.log', 'w') as lf:
        try:
            rc = subprocess.run([str(kbin), str(cp)], stdout=lf, stderr=subprocess.STDOUT, timeout=seconds * 1.5 + 20).returncode
        except subprocess.TimeoutExpired:
            rc = 'timeout'
    if rc != 0 or not bp.exists(): return None, rc
    return core.from_kernel(bp.read_text(), 'best'), rc


# ---------------------------------------------------------------- operator
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--in', dest='inp'); ap.add_argument('--target'); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--seconds', type=float, default=600); ap.add_argument('--out'); ap.add_argument('--cpus', type=int, default=1)
    ap.add_argument('--gd', type=int, help='GD cap of the walk (default: the target reference GD)')
    ap.add_argument('--profile', default='fast', choices=['fast', 'basic'])
    ap.add_argument('--qsec', type=float, default=2.0, help='base SAT time limit per query (fast profile)')
    ap.add_argument('--lns-sec', type=float, default=20.0, help='time limit per query (basic profile)')
    ap.add_argument('--side', type=float, default=0.6, help='sideways share (basic profile)')
    ap.add_argument('--restrict', type=int, default=3, help='basic profile restriction level (3 = mix)')
    ap.add_argument('--focus', type=float, default=1.0, help='probability of a focus query after an accepted sideways move (fast)')
    ap.add_argument('--focus-max', type=int, default=60, help='largest focus neighbourhood')
    ap.add_argument('--index', default=None, help='span index file (default: $BOOLFLUX_CACHE/spanindex.json, '
                    'spanindex-aes-invsbox.json for the inverse)'); ap.add_argument('--pool-extra', action='append', default=[])
    ap.add_argument('--no-index-update', action='store_true')
    ap.add_argument('--pool-before', help='only pool files with mtime before this UTC (validation)')
    ap.add_argument('--pool-exclude-better', action='store_true',
                    help='drop pool circuits whose (G, GD) is <= the start (G - 1, D): no leakage (validation)')
    ap.add_argument('--maxcirc', type=int, default=600); ap.add_argument('--closure', type=int, default=1)
    ap.add_argument('--closure-max', type=int, default=6000); ap.add_argument('--rot', type=int, default=1)
    ap.add_argument('--solver', default='glucose4')
    ap.add_argument('--epoch', type=float, default=0, help='rebuild the model around the walk state every S s (0 off)')
    ap.add_argument('--polish-every', type=int, default=0, help='kernel polish after N accepted sideways moves (0 off)')
    ap.add_argument('--polish-share', type=float, default=0.25, help='max share of wall time spent in kernel polishes')
    ap.add_argument('--polish-sec', type=float, default=15); ap.add_argument('--kernel', help='kernel binary (default: built from kernel/bfx.c)')
    ap.add_argument('--walk-ad-free', action='store_true', help='walk states may exceed the AD cap (never recorded)')
    ap.add_argument('--save-walk', type=int, default=0, help='also keep every Nth accepted walk state in DIR/walk/ (.bfx)')
    ap.add_argument('--final', action='store_true', help='record the final walk state too (if inside limits)')
    ap.add_argument('--qlog', type=int, default=1, help='write DIR/queries.jsonl')
    ap.add_argument('--build-index', action='store_true', help='only (re)build the span index and exit')
    ap.add_argument('--excursion', type=int, default=0,
                    help='every N accepted sideways moves walk at GD cap D + --exc-up for --exc-moves moves, then pull back to D (0 off)')
    ap.add_argument('--exc-up', type=int, default=1); ap.add_argument('--exc-moves', type=int, default=12)
    ap.add_argument('--pull-tries', type=int, default=6)
    ap.add_argument('--pull-kernel', type=float, default=10, help='kernel GD-repair seconds before the SAT pulls (0 off)')
    ap.add_argument('--budget', default='S0:0.08,S2:0.10,I1:0.05,I2:0.03',
                    help='max share of SAT time per query plan (fast profile)')
    ap.add_argument("--prop-rate", type=float, default=1.2e7,
                    help='propagation budget per query = time limit x this rate (0 = time limit only)')
    ap.add_argument('--selftest-record', action='store_true', help='test: record the start itself (recording path check)')
    OC.function_arg(ap)
    a = ap.parse_args()
    global TAB
    if a.build_index and a.function == 'auto' and not a.inp:
        a.function = OC.aesfn.name()
    if a.function != 'auto' or a.inp:
        OC.init_function(a)
    TAB = OC.aesfn.table()
    if a.index is None:
        f = OC.aesfn.name()
        a.index = str(INDEX_DEFAULT if f == 'aes-sbox' else OC.CACHE / ('spanindex-%s.json' % f))
    if a.build_index:
        build_index(a.index, a.pool_extra); return 0
    if not (a.inp and a.target and a.out):
        ap.error('--in, --target and --out are required')

    T0 = time.time(); deadline = T0 + a.seconds
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    signal.signal(signal.SIGTERM, lambda *_: STOP.__setitem__('flag', True))
    signal.signal(signal.SIGINT, lambda *_: STOP.__setitem__('flag', True))
    rng = random.Random(a.seed)
    TG = OC.target(a.target)
    if not a.kernel:
        a.kernel = str(OC.kernel_bin())
    capA, capAD = TG['A'], TG['AD']
    D = a.gd if a.gd is not None else TG['GD']
    qf = open(out / 'queries.jsonl', 'a') if a.qlog else None
    events = []

    def log(r):
        r = dict(r); r.setdefault('el', round(time.time() - T0, 2))
        print(json.dumps(r), flush=True)
        if 'event' in r: events.append(r)

    start_path = str(Path(a.inp).resolve()); start_sha = sha256f(start_path)
    start = load(start_path); st = tup(start)
    result = {'op': 'satlns', 'target': a.target, 'in': start_path, 'in_sha256': start_sha, 'start': st, 'seed': a.seed,
              'seconds': a.seconds, 'D': D, 'caps': {'A': capA, 'AD': capAD, 'GD_walk': D}, 'argv': sys.argv,
              'started_utc': utc(T0), 'walk_best': [], 'recorded': [], 'exit': 'running'}
    code = {'git': subprocess.run(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip(),
            'scripts_sha256': {'ops/satlns.py': sha256f(__file__)}}
    if a.polish_every or (a.excursion and a.pull_kernel > 0):
        code['kernel'] = a.kernel; code['kernel_sha256'] = sha256f(a.kernel)
    result['code'] = code
    model_info = None

    method = {'engine': 'ops/satlns.py (span-pooled SAT LNS, pysat %s)' % a.solver,
              'mode': a.profile, 'operators': ['satlns'] + (['kernel-polish'] if a.polish_every else []),
              'caps': {'A': capA, 'AD': capAD, 'GD': D}, 'objective': 'G under GD <= D (walk), A <= A cap in the model'}
    rc = OC.Recorder(out, 'satlns', a.target, start_path, a.seed, 'cd %s && python3 %s' % (os.getcwd(), ' '.join(sys.argv)),
                     method, {k: v for k, v in vars(a).items() if k not in ('inp', 'out')},
                     kernel=a.kernel if (a.polish_every or (a.excursion and a.pull_kernel > 0)) else None, t0=T0,
                     budget_s=a.seconds, seeds={'rng': 'random.Random(seed)'})

    def write_result(status):
        result['exit'] = status; result['wall_s'] = round(time.time() - T0, 1); result['stats'] = stats
        result['queries'] = sum(sum(v.values()) for k, v in stats.items() if not k.startswith('t:'))
        result['events'] = events[-200:]
        rc.finish(status, extra={'satlns': result})

    stats = {}
    if tuple(start.value_table()) != TAB:
        write_result('error: start is not the %s' % OC.aesfn.label()); return 2
    if st[0] > capA or st[1] > capAD:
        log({'event': 'note', 'msg': 'start outside the hard limits (allowed as a search state; never recorded)', 'start': st})
    if st[0] > capA:
        write_result('error: start A %d > cap %d (the SAT model caps A)' % (st[0], capA)); return 2
    if st[3] > D:
        log({'event': 'note', 'msg': 'start GD %d above the walk cap %d: walk cap raised to the start GD' % (st[3], D)})
        D = st[3]; result['D'] = D; method['caps']['GD'] = D

    # ---- pool
    # concurrency: the index is only ever replaced atomically (write to <index>.tmp<pid>, os.replace), so a
    # reader sees the old or the new complete file; concurrent writers each write a complete index (last
    # rename wins; at worst a file added meanwhile is re-scanned by the next build).  Runner use: build once
    # per block (--build-index), jobs with --no-index-update (read-only, no 5-15 s rescan per job).
    if a.no_index_update and Path(a.index).exists():
        idx = json.loads(Path(a.index).read_text())
    else:
        idx = build_index(a.index, a.pool_extra, quiet=True)
    skey = span_key(start)
    cutoff = None
    if a.pool_before:
        import calendar
        cutoff = calendar.timegm(time.strptime(a.pool_before, '%Y-%m-%dT%H:%M'))
    def select_pool(c0, skey):
        rows = []
        for p, r in idx.items():
            if r.get('span') != skey: continue
            if cutoff is not None and r['mt'] >= cutoff: continue
            if a.pool_exclude_better and r['m'][2] < st[2] and r['m'][3] <= D: continue
            rows.append((r['m'][2], r['m'][3], p, r['k']))
        rows.sort()
        seen = {kid(c0)[:16]}; pc = []; pf = []
        for g_, gd_, p, k in rows:
            if k in seen: continue
            seen.add(k)
            try: c = load(p)
            except Exception: continue
            pc.append(c); pf.append(p)
            if len(pc) >= a.maxcirc: break
        return rows, pc, pf
    rows, pool_c, pool_files = select_pool(start, skey)
    pool_key = [skey]
    result['pool'] = {'span': skey, 'n_same_span_files': len(rows), 'n_pooled': len(pool_c), 'files_sample': pool_files[:20],
                      'before': a.pool_before, 'exclude_better': a.pool_exclude_better}
    (out / 'pool.json').write_text(json.dumps({'span': skey, 'files': pool_files}, indent=0))
    log({'event': 'pool', 'span': skey, 'same_span_files': len(rows), 'pooled': len(pool_c)})

    # ---- recording
    rec_pts = [(st[2], st[3])]              # (G, GD) already known in this run (start included)
    hard = lambda t: t[0] <= TG['A'] and t[1] <= TG['AD']

    def record(c, how, extra=None):
        t = tup(c)
        if not hard(t) or tuple(c.value_table()) != TAB: return None
        if any(g <= t[2] and gd <= t[3] for g, gd in rec_pts): return None
        rc.method = dict(method, how=how, model=model_info, pool=result['pool'])
        p = rc.offer(c, how=how, lineage=[{'file': start_path, 'sha256': start_sha, 'tuple': list(st), 'method': 'satlns walk'}])
        if p is None:
            log({'event': 'offer_rejected', 'tuple': t, 'rejected': dict(rc.rejected)}); return None
        rec_pts.append((t[2], t[3]))
        result['recorded'].append({'file': str(p), 'tuple': t, 'how': how, 'el': round(time.time() - T0, 1)})
        log({'event': 'recorded', 'file': str(p), 'tuple': t, 'how': how})
        return p

    def note_best(t):
        b = result['walk_best']
        for e in b:
            if e['G'] == t[2] and e['GD'] == t[3]: return
        b.append({'A': t[0], 'AD': t[1], 'G': t[2], 'GD': t[3], 'el': round(time.time() - T0, 1)})

    # ---- walk
    if a.selftest_record:
        rec_pts.clear(); record(start, 'selftest-record: the start itself'); rec_pts.append((st[2], st[3]))
    cur = start; epoch = 0; nside_acc = 0; nacc = 0; visited = set(); steps = 0
    model_info = None; mdl = None; t_epoch = time.time()
    plan = PLANS.get(a.profile)
    budget = {k: float(v) for k, v in (x.split(':') for x in a.budget.split(',') if x)} if a.budget else {}
    tplan = {}; tsat = [0.0]
    phase = 'main'; Dc = D; saved = None; exc_n = 0; pull_n = 0; main_side = 0
    exc_stats = {'excursions': 0, 'pulled_back': 0, 'reverted': 0, 'pull_better': 0}
    result['excursions'] = exc_stats
    walk_dir = out / 'walk'
    status = 'ok'; mdl_old = None
    try:
        while time.time() < deadline - 2 and not STOP['flag']:
            if mdl is None:
                if mdl_old is not None:
                    try: mdl_old.s.delete()
                    except Exception: pass
                mdl_old = None
                k_ = span_key(cur)
                if k_ != pool_key[0]:
                    # a kernel result with other AND functions: pool the archive circuits of its span instead
                    rows_, pool_c, pf_ = select_pool(cur, k_); pool_key[0] = k_
                    log({'event': 'span_change', 'span': k_, 'same_span_files': len(rows_), 'pooled': len(pool_c)})
                mdl = Model(cur, pool_c, Dc, capA, a, log); model_info = dict(mdl.info, epoch=epoch, phase=phase)
                cur_ts = mdl.tset(cur)
                if cur_ts is None: raise RuntimeError('current circuit outside the span')
                s = mdl.s; sel = mdl.sel; tot = mdl.tot
                if phase != 'pull':
                    if mdl.trivial_unsat or not all(tt in mdl.sel for tt, _, _ in cur_ts):
                        raise RuntimeError('model does not contain the current circuit')
                    r0 = s.solve(assumptions=[sel[tt] for tt, _, _ in cur_ts] + [-tot.rhs[len(cur_ts)]])
                    log({'event': 'selftest', 'ok': bool(r0), 'epoch': epoch, 'phase': phase, 'D': Dc})
                    if not r0: raise RuntimeError('encoding rejects the current circuit')
                t_epoch = time.time(); focus_q = []
            steps += 1
            N_ = len(cur_ts); G_cur = tup(cur)[2]
            # ---- choose query
            pull = phase == 'pull'
            if pull:
                # back from an excursion: free the deep levels (and every template the D model lacks), K = G
                w = rng.choice([2, 3, 3, 4, 5, 6])
                free = {i for i, (tt, l, sgi) in enumerate(cur_ts) if l > Dc - w or tt not in sel}
                free |= {i for i in range(N_) if rng.random() < 0.05}
                qname, side, kind, sc = 'P', False, 'pull', w; rl = rng.choice([1, 1, 2, 0]); tl = a.qsec * (2 if rl == 1 else 4)
            elif focus_q:
                free = focus_q.pop(); qname, side, rl, tl = 'F', False, 1, a.qsec; kind = 'focus'; sc = 0
            elif a.profile == 'basic':
                kind = rng.choice(['rand', 'rand', 'level', 'cone', 'and'])
                rl = rng.choice([0, 1, 1, 2, 2]) if a.restrict >= 3 else a.restrict
                sc = 1 if rl == 0 else rng.choice([1, 1, 2, 3])
                free = neighbourhood(rng, kind, sc, cur, cur_ts, Dc)
                side = rng.random() < a.side; qname = 'basic'; tl = a.lns_sec
                if rl == 2 and a.restrict == 2: rl = rng.choice([1, 1, 2])
            else:
                for _try in range(6):
                    x = rng.random() * sum(w for _, w in plan); acc = 0
                    for (pl, w) in plan:
                        acc += w
                        if x <= acc: break
                    if tsat[0] < 30 or tplan.get(pl[0], 0) <= budget.get(pl[0], 1.0) * tsat[0]: break
                qname, side, rl, scs, fmin, fmax, tf = pl
                kind = rng.choice(['rand', 'rand', 'level', 'cone', 'and']); sc = rng.choice(scs)
                free = neighbourhood(rng, kind, sc, cur, cur_ts, Dc)
                if len(free) > fmax: free = set(rng.sample(sorted(free), fmax))
                if len(free) < fmin:
                    free |= set(rng.sample(range(N_), min(N_, fmin - len(free))))
                tl = a.qsec * tf
            if not free: continue
            if deadline - time.time() < 90 and rl != 1:
                rl = 1       # contract (exit <= T + 60 s): only rl-1 queries near the end (they never overran)
            if phase == 'exc': qname = 'x' + qname
            Kq = N_ - (0 if (side or pull) else 1)
            if Kq >= mdl.ub: continue
            kept = {cur_ts[i][0] for i in range(N_) if i not in free}
            if any(tt not in sel for tt in kept): continue
            assum = [sel[tt] for tt in kept] + [-tot.rhs[Kq]]
            nallowed = None
            if rl:
                cur_forms = {tt[1] for tt, l, sgi in cur_ts} | mdl.inputs
                free_forms = {cur_ts[i][0][1] for i in free}
                if rl == 2:
                    one = {tt[1] for tt in sel if tt[2] in cur_forms and tt[3] in cur_forms}
                    cur_forms = cur_forms | one
                aset = {tt for tt in sel if tt in kept or tt[1] in free_forms or (tt[2] in cur_forms and tt[3] in cur_forms)}
                nallowed = len(aset)
                assum += [-v for tt, v in sel.items() if tt not in aset]
            if side:
                act = mdl.pool.id(('act', epoch, steps))
                s.add_clause([-act] + [-sel[cur_ts[i][0]] for i in free]); assum.append(act)
            rem = min(tl, deadline - 1 - time.time())
            if rem <= 0.05: break
            # the interrupt alone did not bound unrestricted (rl 0) queries: 8 s limits ran 30-127 s in the
            # 00:00-00:42 runs; a propagation budget is added, which made overruns rarer but did NOT remove
            # them (01:00-01:27: up to 162 s at an 8 s limit, rl 0 / pull queries) [H; cause not found]; the
            # plan time budgets (--budget) bound their total share instead
            try: ss0 = s.accum_stats()
            except Exception: ss0 = None
            if a.prop_rate > 0: s.prop_budget(int(rem * a.prop_rate))
            timer = threading.Timer(rem, lambda: s.interrupt()); timer.start()
            t1 = time.time()
            r = s.solve_limited(assumptions=assum, expect_interrupt=True)
            timer.cancel(); s.clear_interrupt()
            dt = time.time() - t1
            try:
                ss1 = s.accum_stats(); props = ss1['propagations'] - ss0['propagations']; confl = ss1['conflicts'] - ss0['conflicts']
            except Exception:
                props = confl = None
            rs = {True: 'SAT', False: 'UNSAT', None: 'UNKNOWN'}[r]
            fb = '<=10' if len(free) <= 10 else '<=20' if len(free) <= 20 else '<=40' if len(free) <= 40 else '<=80' if len(free) <= 80 else '>80'
            q = {'el': round(time.time() - T0, 2), 'step': steps, 'ep': epoch, 'q': qname, 'kind': kind, 'sc': sc, 'rl': rl,
                 'side': side, 'free': len(free), 'allowed': nallowed, 'Kq': Kq, 'r': rs, 't': round(dt, 3),
                 'props': props, 'confl': confl}
            res_key = rs
            if r:
                model = set(v for v in s.get_model() if v > 0)
                c = mdl.decode(model); t = tup(c)
                if tuple(c.value_table()) != TAB: raise RuntimeError('decoded circuit is wrong')
                q.update({'G': t[2], 'A': t[0], 'GD': t[3], 'AD': t[1]})
                if t[2] < G_cur: res_key = 'SAT-drop'
                ok_walk = t[0] <= capA and t[3] <= Dc and (a.walk_ad_free or t[1] <= capAD)
                if not ok_walk:
                    q['REJECT'] = 'outside walk caps'; res_key = 'SAT-reject'
                elif t[2] <= N_:
                    prev_ts = cur_ts; cur = c; cur_ts = mdl.tset(c); nacc += 1
                    h = kid(c)[:16]; q['new'] = h not in visited; visited.add(h)
                    if hard(t): note_best(t)
                    if t[2] < G_cur:
                        q['IMPROVED'] = True; record(c, 'step %d epoch %d query %s' % (steps, epoch, qname))
                    if pull:
                        exc_stats['pulled_back'] += 1; phase = 'main'; saved = None
                        if t[2] < saved_G: exc_stats['pull_better'] += 1
                        log({'event': 'pulled_back', 'tuple': t, 'tries': pull_n})
                    if side and phase == 'main':
                        main_side += 1
                    if side:
                        nside_acc += 1
                        if a.save_walk and nside_acc % a.save_walk == 0 and hard(t):
                            walk_dir.mkdir(exist_ok=True); (walk_dir / ('w-a%d-ad%d-g%d-gd%d-%s.bfx' % (t + (h[:10],)))).write_text(core.to_kernel(c))
                    if a.profile == 'fast' and t[2] == G_cur and rng.random() < a.focus:
                        old = {tt for tt, _, _ in prev_ts}
                        seeds = [i for i, (tt, l, sgi) in enumerate(cur_ts) if tt not in old]
                        if seeds:
                            fz = grow(cur, cur_ts, seeds, rng.choice([1, 2]))
                            if len(fz) > a.focus_max: fz = grow(cur, cur_ts, seeds, 1)
                            if len(fz) > a.focus_max: fz = set(rng.sample(sorted(fz), a.focus_max))
                            focus_q = [fz]
                    if a.polish_every and side and phase == 'main' and nside_acc % a.polish_every == 0 and t[1] <= capAD \
                            and stats.get('t:polish', {}).get('s', 0) <= a.polish_share * (time.time() - T0):
                        ks = min(a.polish_sec, deadline - 5 - time.time())
                        if ks > 3:
                            tk = time.time()
                            kc, krc = kernel_polish(cur, (capA, capAD, D), ks, rng.randrange(1 << 30), out / 'kernel', a.kernel)
                            kt = tup(kc) if kc is not None else None
                            ev = {'event': 'polish', 'from': t, 'to': kt, 'rc': krc, 's': round(time.time() - tk, 1)}
                            stats.setdefault('t:polish', {'n': 0, 's': 0.0}); stats['t:polish']['n'] += 1; stats['t:polish']['s'] += time.time() - tk
                            if kc is not None and tuple(kc.value_table()) == TAB and kt[0] <= capA and kt[1] <= capAD and kt[3] <= D \
                                    and (kt[2], kt[3]) < (t[2], t[3]):
                                ev['adopt'] = True; note_best(kt)
                                record(kc, 'kernel polish after step %d epoch %d' % (steps, epoch))
                                cur = kc; mdl_old = mdl; mdl = None; epoch += 1
                            log(ev)
                elif t[2] > N_:
                    q['REJECT'] = 'G above K (should not happen)'
            k1 = '%s/%s' % (qname, fb)
            stats.setdefault(k1, {}); stats[k1][res_key] = stats[k1].get(res_key, 0) + 1
            stats.setdefault('t:' + qname, {'n': 0, 's': 0.0}); stats['t:' + qname]['n'] += 1; stats['t:' + qname]['s'] += dt
            if qf: qf.write(json.dumps(q) + '\n')
            if q.get('IMPROVED'): log(dict(q, event='improved'))
            tsat[0] += dt; tplan[qname] = tplan.get(qname, 0) + dt
            # ---- phase transitions
            if phase == 'pull' and mdl is not None:
                pull_n += 1
                if pull_n >= a.pull_tries:
                    exc_stats['reverted'] += 1; log({'event': 'pull_failed', 'from': tup(cur), 'revert_to': tup(saved)})
                    cur = saved; saved = None; phase = 'main'; mdl_old = mdl; mdl = None; epoch += 1
            elif phase == 'exc' and side and r and q.get('REJECT') is None:
                exc_n += 1
                if exc_n >= a.exc_moves:
                    Dc = D; phase = 'pull'; pull_n = 0; mdl_old = mdl; mdl = None; epoch += 1
                    if tup(cur)[3] <= D:       # the excursion ended inside the cap: nothing to pull
                        phase = 'main'; saved = None; exc_stats['pulled_back'] += 1
                    elif a.pull_kernel > 0 and deadline - time.time() > a.pull_kernel + 10:
                        # kernel GD repair (repair_keep 1: A / AD excess never grows) before the SAT pulls
                        tk = time.time()
                        kc, krc = kernel_polish(cur, (capA, capAD, D), a.pull_kernel, rng.randrange(1 << 30), out / 'kernel', a.kernel)
                        kt = tup(kc) if kc is not None else None
                        stats.setdefault('t:kpull', {'n': 0, 's': 0.0}); stats['t:kpull']['n'] += 1; stats['t:kpull']['s'] += time.time() - tk
                        ev = {'event': 'kernel_pull', 'from': tup(cur), 'to': kt, 'rc': krc}
                        if kc is not None and tuple(kc.value_table()) == TAB and kt[0] <= capA and kt[1] <= capAD and kt[3] <= D \
                                and kt[2] <= saved_G:
                            ev['adopt'] = True; exc_stats['pulled_back'] += 1; exc_stats['kernel_pulls'] = exc_stats.get('kernel_pulls', 0) + 1
                            if kt[2] < saved_G: exc_stats['pull_better'] += 1
                            note_best(kt); record(kc, 'kernel pull after excursion, step %d' % steps)
                            cur = kc; phase = 'main'; saved = None
                        log(ev)
            elif phase == 'main' and a.excursion and mdl is not None and main_side >= a.excursion and deadline - time.time() > 30:
                main_side = 0; saved = cur; saved_G = tup(cur)[2]; exc_n = 0; exc_stats['excursions'] += 1
                Dc = D + a.exc_up; phase = 'exc'; mdl_old = mdl; mdl = None; epoch += 1
                log({'event': 'excursion', 'from': tup(cur), 'D': Dc})
            if mdl is not None and phase == 'main' and a.epoch and time.time() - t_epoch > a.epoch and deadline - time.time() > 60:
                mdl_old = mdl; mdl = None; epoch += 1
        status = 'stopped' if STOP['flag'] else 'ok'
    except Exception as e:
        import traceback
        status = 'error: %r' % (e,); traceback.print_exc()
    if a.final and cur is not None:
        record(cur, 'final walk state')
    if qf: qf.close()
    result['walk'] = {'steps': steps, 'accepted': nacc, 'side_accepted': nside_acc, 'distinct_states': len(visited), 'epochs': epoch + 1,
                      'final': tup(cur)}
    for k in stats:
        if k.startswith('t:'): stats[k]['s'] = round(stats[k]['s'], 1)
    write_result(status)
    log({'event': 'done', 'status': status, 'walk_best': sorted((e['G'], e['GD']) for e in result['walk_best']),
         'recorded': len(result['recorded']), 'steps': steps})
    return 0 if status in ('ok', 'stopped') else 1


if __name__ == '__main__':
    sys.exit(main())
