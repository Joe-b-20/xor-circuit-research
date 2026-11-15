#!/usr/bin/env python3
"""P1 exact LNS recombination over a whole AND span (SAT), v2 of unionsat.py.

All archived circuits whose 1 + 8 inputs + 28 AND truth tables span the same 37-dim space as the
start circuit are pooled, even when their AND functions differ (unionsat.py v1 needed identical
AND functions).  Every signal of every pooled circuit is a coordinate vector over the start's basis
[1, x0..x7, z1..z28]; templates:
  linear  f = a ^ b (XOR when the constant coordinates cancel, XNOR otherwise), f = a ^ 1 (NOT),
          from the pooled circuits plus (closure) every XOR/XNOR of two pooled forms that is itself a
          pooled form;
  AND     product p = AND(L, R) for every AND gate seen, plus the free variants (L, L^R^1), (L^R^1, R).
SAT model: availability a(f, l) = "form f computed at gate level <= l" (unit gate delay), every
output at level <= D, at most 28 AND templates selected (hard A cap), at most K templates in all
(K = current G - 1 for an improving query, = G for a sideways query that must drop one freed
template).  LNS: the start's templates outside a random neighbourhood are forced; the solver may
use any pooled template inside it.  Every SAT answer is decoded, verified on all 256 inputs and
accepted only with A <= cap-a, AD <= cap-ad, GD <= D.  [C, per query]: UNSAT = no circuit made of
the forced templates plus pooled templates has G <= K and GD <= D.

    python3 unionsat2.py --lns START --starts starts_fam.json [--extra DIR] --D 20 --cap-ad 5 \
        --seconds 900 --lns-sec 20 --seed 1 --out BEST.circ.txt --outdir OUTDIR [--closure 1]
"""
import argparse
import hashlib
import json
import random
import sys
import threading
import time
from pathlib import Path

PKG = Path('/home/joebachir20/xcr-boolflux/nonlinear/boolflux')
sys.path.insert(0, str(PKG.parent))
from boolflux import core, targets   # noqa: E402
from pysat.formula import IDPool     # noqa: E402
from pysat.card import CardEnc, EncType, ITotalizer   # noqa: E402
from pysat.solvers import Solver     # noqa: E402

AND, XOR, XNOR, NOT = 8, 6, 9, 3
TAB = tuple(targets.aes_sbox())
ONES = (1 << 256) - 1


def load(p):
    t = Path(p).read_text()
    return core.from_kernel(t) if str(p).endswith('.bfx') else core.read_ncff(t)


class Span:
    def __init__(self, vecs):
        self.ech = {}          # pivot bit -> (vec, combo)
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


def basis_of(c):
    tabs = c.tables(); n = c.n
    return [ONES] + tabs[:n] + [tabs[n + j] for j, (op, a, b) in enumerate(c.gates) if op == AND]


def forms_of(c, sp):
    tabs = c.tables()
    F = []
    for t in tabs:
        f = sp.coords(t)
        if f is None: return None
        F.append(f)
    return F


def tkey(op, F, a, b, f):
    if op == AND:
        L, R = sorted((F[a], F[b])); return ('A', f, L, R)
    if op == NOT: return ('L', f, F[a], F[a])
    x, y = sorted((F[a], F[b])); return ('L', f, x, y)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lns', required=True); ap.add_argument('--starts', required=True)
    ap.add_argument('--extra', action='append', default=[]); ap.add_argument('--D', type=int, required=True)
    ap.add_argument('--cap-ad', type=int, required=True); ap.add_argument('--cap-a', type=int, default=28)
    ap.add_argument('--closure', type=int, default=1); ap.add_argument('--seconds', type=float, default=900)
    ap.add_argument('--lns-sec', type=float, default=20); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--side', type=float, default=0.6); ap.add_argument('--out'); ap.add_argument('--outdir')
    ap.add_argument('--solver', default='glucose4'); ap.add_argument('--maxcirc', type=int, default=600)
    ap.add_argument('--closure-max', type=int, default=6000); ap.add_argument('--log')
    ap.add_argument('--restrict', type=int, default=3)
    ap.add_argument('--final'); ap.add_argument('--rot', type=int, default=1); ap.add_argument('--rot-extra', action='append', default=[]); ap.add_argument('--side-every', type=int, default=200)
    a = ap.parse_args()
    T0 = time.time(); M = core.Model.load('nist'); rng = random.Random(a.seed)
    start = load(a.lns); ms = start.metrics(M)
    assert tuple(start.value_table()) == TAB and ms['A'] <= a.cap_a and ms['AD'] <= a.cap_ad and ms['GD'] <= a.D
    sp = Span(basis_of(start)); n = start.n
    files = [r['path'] for r in json.loads(Path(a.starts).read_text())]
    for d in a.extra:
        files += [str(p) for p in sorted(Path(d).glob('*.bfx')) + sorted(Path(d).glob('*.circ.txt'))]
    circs = [start]; seen = {hashlib.sha1(core.to_kernel(start).encode()).hexdigest()}
    pool_files = [(a.lns, hashlib.sha256(Path(a.lns).read_bytes()).hexdigest())]
    for p in files:
        try: c = load(p)
        except Exception: continue
        h = hashlib.sha1(core.to_kernel(c).encode()).hexdigest()
        if h in seen: continue
        seen.add(h)
        if sum(1 for g in c.gates if g[0] == AND) > a.cap_a: continue
        if tuple(c.value_table()) != TAB: continue
        F = forms_of(c, sp)
        if F is None: continue
        circs.append(c); pool_files.append((p, hashlib.sha256(Path(p).read_bytes()).hexdigest()))
        if len(circs) >= a.maxcirc: break
    tmpl = set(); outs = None
    for c in circs:
        F = forms_of(c, sp)
        o = [F[s] for s in c.outputs]
        if outs is None: outs = o
        assert o == outs
        for j, (op, x, y) in enumerate(c.gates):
            f = F[n + j]; t = tkey(op, F, x, y, f); tmpl.add(t)
            if op == AND:
                _, _, L, R = t
                tmpl.add(('A', f) + tuple(sorted((L, L ^ R ^ 1)))); tmpl.add(('A', f) + tuple(sorted((L ^ R ^ 1, R))))
    forms = {t[1] for t in tmpl} | {t[2] for t in tmpl} | {t[3] for t in tmpl} | set(outs)
    inputs = {1 << (1 + i) for i in range(n)}
    forms |= inputs
    base_t = len(tmpl)
    nrot = 0
    if a.rot:
        # v2.4 rotation closure: for every linear gate f = x ^ y (const absorbed) of the start circuit
        # (and of --rot-extra circuits) whose operand x is itself a linear gate x = u ^ v, add the
        # re-bracketed forms v ^ y and u ^ y with templates (v^y, v, y), (f, u, v^y), (u^y, u, y),
        # (f, v, u^y): new forms that no pooled circuit has, enabling XOR-tree rebalancing.
        rc = [start] + [load(p) for p in a.rot_extra]
        for _lvl in range(a.rot):
            new_t = set()
            for c in rc:
                F = forms_of(c, sp)
                if F is None: continue
                kind = {}
                for j, (op, x, y) in enumerate(c.gates):
                    if op in (XOR, XNOR): kind[n + j] = (x, y)
                for j, (op, x, y) in enumerate(c.gates):
                    if op not in (XOR, XNOR): continue
                    f = F[n + j]
                    for xx, yy in ((x, y), (y, x)):
                        if xx not in kind: continue
                        u, v = kind[xx]
                        for p_, q_ in ((u, v), (v, u)):
                            g = F[q_] ^ F[yy]
                            if g & ~1 == 0: continue
                            g &= ~1          # pure form; the constant is absorbed by the outer XNOR
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
    info = {'circuits': len(circs), 'forms': len(forms), 'templates_pooled': base_t, 'templates': len(tmpl),
            'and_templates': sum(1 for t in tmpl if t[0] == 'A'), 'D': a.D, 'closure': a.closure, 'rot_templates': nrot, 'start': a.lns}
    info['argv'] = [sys.executable, str(Path(__file__).resolve())] + sys.argv[1:]
    print(json.dumps(info), flush=True)
    if a.outdir:
        Path(a.outdir).mkdir(parents=True, exist_ok=True)
        Path(a.outdir, 'pool.json').write_text(json.dumps({'start': a.lns, 'pool_files': pool_files, 'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}))
    by_f = {}
    for t in tmpl: by_f.setdefault(t[1], []).append(t)
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
    D = a.D
    pool = IDPool(); cl = []

    def av(f, l):
        if f in inputs: return True
        if l < lev[f] or l > D: return False
        return pool.id(('a', f, l))
    sel = {}

    def S(t):
        if t not in sel: sel[t] = pool.id(('s', t))
        return sel[t]
    for f in forms:
        if f in inputs or lev[f] > D: continue
        for l in range(lev[f], D + 1):
            v = av(f, l)
            if l < D: cl.append([-v, av(f, l + 1)])
            alts = []
            for t in by_f.get(f, ()):
                ax, ay = av(t[2], l - 1), av(t[3], l - 1)
                if ax is False or ay is False: continue
                w = pool.id(('w', t, l)); alts.append(w)
                cl.append([-w, S(t)])
                if ax is not True: cl.append([-w, ax])
                if ay is not True: cl.append([-w, ay])
            cl.append([-v] + alts)
    for o in outs:
        v = av(o, D)
        if v is False: print(json.dumps({'result': 'UNSAT-trivial'})); return
        if v is not True: cl.append([v])
    svars = list(sel.values()); avars = [sel[t] for t in sel if t[0] == 'A']
    cardA = CardEnc.atmost(lits=avars, bound=a.cap_a, vpool=pool, encoding=EncType.seqcounter)
    ub = min(len(svars), ms['G'] + 2)
    # ITotalizer numbers its auxiliary variables from top_id + 1: they must not collide with the pool
    # (bug in the first version: default top_id = max(lits) -> collisions -> spurious UNSAT)
    tot = ITotalizer(lits=svars, ubound=ub, top_id=pool.top)
    pool.top = max(pool.top, tot.top_id)
    print(json.dumps({'vars': pool.top, 'clauses': len(cl), 'cardA': len(cardA.clauses), 'tot': len(tot.cnf.clauses),
                      'sel': len(svars), 'sel_and': len(avars), 't_build': round(time.time() - T0, 1)}), flush=True)
    s = Solver(name=a.solver, bootstrap_with=cl + cardA.clauses + tot.cnf.clauses)

    def decode(model):
        minlev = {}
        for f in forms:
            if f in inputs: minlev[f] = 0; continue
            for l in range(lev[f], D + 1):
                v = av(f, l)
                if v is not False and v is not True and v in model: minlev[f] = l; break
        just = {}; need = list(outs)
        while need:
            f = need.pop()
            if f in inputs or f in just: continue
            l = minlev[f]; ch = None
            for t in by_f.get(f, ()):
                k = pool.obj2id.get(('w', t, l))
                if k is not None and k in model and sel.get(t) in model: ch = t; break
            assert ch is not None, 'no justification'
            just[f] = ch; need += [ch[2], ch[3]]
        order = sorted(just, key=lambda f: minlev[f])
        sig = {1 << (1 + i): i for i in range(n)}; gates = []
        for f in order:
            t = just[f]; x, y = t[2], t[3]
            if t[0] == 'A': gates.append((AND, sig[x], sig[y]))
            elif x == y: gates.append((NOT, sig[x], sig[x]))
            else: gates.append((XNOR if (x ^ y ^ f) == 1 else XOR, sig[x], sig[y]))
            sig[f] = n + len(gates) - 1
        return core.Circuit(n, len(outs), gates, [sig[o] for o in outs], 'unionsat2').live()

    def tset(c):
        F = forms_of(c, sp); ts = []; lg = [0] * n
        for j, (op, x, y) in enumerate(c.gates):
            lg.append(1 + max(lg[x], lg[y]))
            ts.append((tkey(op, F, x, y, F[n + j]), lg[-1], n + j))
        return ts
    cur = start; cur_ts = tset(cur)
    assert all(t in sel for t, _, _ in cur_ts)
    gbest = ms['G']; steps = 0; stats = {}; nside = 0
    print(json.dumps({'lns_start': a.lns, 'G': ms['G'], 'GD': ms['GD'], 'AD': ms['AD']}), flush=True)
    # self-test: the start itself must satisfy the encoding (all its templates forced, count <= G)
    r0 = s.solve(assumptions=[sel[t] for t, _, _ in cur_ts] + [-tot.rhs[len(cur_ts)]])
    print(json.dumps({'selftest_forced_card': r0}), flush=True)
    if not r0: raise RuntimeError('encoding rejects the start circuit')
    deadline = T0 + a.seconds
    while time.time() < deadline - 1:
        steps += 1
        kind = rng.choice(['rand', 'rand', 'level', 'cone', 'and'])
        N_ = len(cur_ts)
        rlev = rng.choice([0, 1, 1, 2, 2]) if a.restrict >= 3 else a.restrict   # v2.3: mix incl. unrestricted queries
        sc = 1 if rlev == 0 else rng.choice([1, 1, 2, 3])   # v2.2 scale; v2.5: unrestricted queries stay small
        if kind == 'rand':
            p = sc * rng.choice([0.06, 0.1, 0.15, 0.2]); free = {i for i in range(N_) if rng.random() < p}
        elif kind == 'level':
            w = sc - 1 + rng.choice([1, 2, 2, 3]); l0 = rng.randint(1, max(1, D - w))
            free = {i for i, (t, l, sgi) in enumerate(cur_ts) if l0 <= l < l0 + w}
        elif kind == 'and':
            # a few ANDs plus their operand cones and their direct readers
            ands = [i for i, (t, l, sgi) in enumerate(cur_ts) if t[0] == 'A']
            pick = set(rng.sample(ands, min(len(ands), sc * rng.choice([1, 2, 3]))))
            free = set(pick)
            idx = {sgi: i for i, (t, l, sgi) in enumerate(cur_ts)}
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
        else:
            idx = {sgi: i for i, (t, l, sgi) in enumerate(cur_ts)}
            free = set()
            for _ in range(sc * rng.choice([1, 2, 3])):
                st = [rng.choice(list(idx))]
                for _d in range(rng.choice([2, 3, 4])):
                    nx = []
                    for sgi in st:
                        if sgi in idx and idx[sgi] not in free:
                            free.add(idx[sgi]); op, x, y = cur.gates[sgi - n]; nx += [x, y]
                    st = nx
        if not free: continue
        side = rng.random() < a.side
        Kq = N_ - (0 if side else 1)
        if Kq >= ub: continue
        kept = {t for i, (t, l, sgi) in enumerate(cur_ts) if i not in free}
        assum = [sel[t] for t in kept] + [-tot.rhs[Kq]]
        nallowed = None
        if rlev:
            # v2.1: only templates that produce a freed form, or whose operands are both current forms
            # (one-step new forms); everything else is assumed unselected (tractable queries)
            cur_forms = {t[1] for t, l, sgi in cur_ts} | inputs
            free_forms = {cur_ts[i][0][1] for i in free}
            rl = (rng.choice([1, 1, 2]) if a.restrict == 2 else rlev) if rlev else 0
            if rl == 2:   # v2.2: two-step new forms
                one = {t[1] for t in sel if t[2] in cur_forms and t[3] in cur_forms}
                cur_forms = cur_forms | one
            allowed = [t for t in sel if t in kept or t[1] in free_forms or (t[2] in cur_forms and t[3] in cur_forms)]
            aset = set(allowed); nallowed = len(aset)
            assum += [-v for t, v in sel.items() if t not in aset]
        if side:
            act = pool.id(('act', steps))
            s.add_clause([-act] + [-sel[cur_ts[i][0]] for i in free]); assum.append(act)
        rem = min(a.lns_sec, deadline - time.time())
        timer = threading.Timer(rem, lambda: s.interrupt()); timer.start()
        t1 = time.time()
        r = s.solve_limited(assumptions=assum, expect_interrupt=True)
        timer.cancel(); s.clear_interrupt()
        rs = {True: 'SAT', False: 'UNSAT', None: 'UNKNOWN'}[r]
        st_ = stats.setdefault('%s/%s' % (kind, side), {'SAT': 0, 'UNSAT': 0, 'UNKNOWN': 0}); st_[rs] += 1
        rec = {'el': round(time.time() - T0, 1), 'step': steps, 'kind': kind, 'sc': sc, 'rl': rlev, 'side': side, 'free': len(free), 'allowed': nallowed, 'Kq': Kq, 'r': rs, 't': round(time.time() - t1, 1)}
        if r:
            model = set(x for x in s.get_model() if x > 0)
            c = decode(model); m = c.metrics(M)
            if tuple(c.value_table()) != TAB: raise RuntimeError('decoded circuit is wrong')
            rec.update({'G': m['G'], 'A': m['A'], 'GD': m['GD'], 'AD': m['AD']})
            if m['AD'] > a.cap_ad or m['A'] > a.cap_a:
                rec['REJECT'] = 'outside hard limits'
            elif m['G'] <= N_ and m['GD'] <= D:
                cur = c; cur_ts = tset(c)
                nside = nside + 1 if side else nside
                if a.outdir and (m['G'] < gbest or (side and nside % a.side_every == 0)):
                    Path(a.outdir).mkdir(parents=True, exist_ok=True)
                    Path(a.outdir, 'us2-a%d-ad%d-g%d-gd%d-s%d-%d.circ.txt' % (m['A'], m['AD'], m['G'], m['GD'], a.seed, steps)).write_text(
                        core.write_ncff(c, M, comments=['P1 unionsat2 LNS D %d seed %d step %d from %s' % (D, a.seed, steps, a.lns)]))
                if m['G'] < gbest:
                    gbest = m['G']; rec['IMPROVED'] = True
                    if a.out: Path(a.out).write_text(core.write_ncff(c, M, comments=['P1 unionsat2 LNS D %d seed %d step %d from %s' % (D, a.seed, steps, a.lns)]))
        print(json.dumps(rec), flush=True)
    if a.final:
        Path(a.final).write_text(core.write_ncff(cur, M, comments=['P1 unionsat2 LNS final current circuit D %d seed %d from %s' % (D, a.seed, a.lns)]))
    res = {'lns_done': steps, 'best_G': gbest, 'stats': stats, 't_total': round(time.time() - T0, 1)}
    res.update(info)
    print(json.dumps(res), flush=True)
    if a.log:
        with open(a.log, 'a') as fh: fh.write(json.dumps(res) + chr(10))


if __name__ == '__main__':
    main()
