#!/usr/bin/env python3
"""P1 exact recombination of same-skeleton circuits under a gate-depth cap (SAT).

Circuits of one AND family (identical set of 28 AND truth tables) share a basis: every signal of
every such circuit is an affine form over {1, x0..x7, z_0..z_27} (z_k = the k-th AND function).
The union of their linear gates gives templates f = a ^ b (XOR), f = a ^ b ^ 1 (XNOR), f = a ^ 1
(NOT); with --closure also every XOR / XNOR of two union forms that is itself a union form.  Every
AND k may use any operand pair seen for it (plus the free ODC variants (L, L^R^1), (L^R^1, R)).
SAT question: is there a selection of at most K templates such that, with every gate at level
1 + max(operand levels), every output form is available at level <= D?  (A, AD are those of the
family; G = 28 + number of linear gates used.)  [C, within this case]: UNSAT means no circuit
built only from these templates and operand pairs meets (G <= 28 + K, GD <= D).

    python3 unionsat.py --fam KEY --starts starts_fam.json [--extra DIR ...] --D 20 --K 99 \
        [--closure 1] [--seconds 1800] [--out OUT.circ.txt]
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

PKG = Path('/home/joebachir20/xcr-boolflux/nonlinear/boolflux')
sys.path.insert(0, str(PKG.parent))
from boolflux import core, targets   # noqa: E402
from pysat.formula import IDPool     # noqa: E402
from pysat.card import CardEnc, EncType   # noqa: E402
from pysat.solvers import Solver     # noqa: E402

AND, XOR, XNOR, NOT = 8, 6, 9, 3
TAB = tuple(targets.aes_sbox())


def load(p):
    t = Path(p).read_text()
    return core.from_kernel(t) if str(p).endswith('.bfx') else core.read_ncff(t)


def fam_key(c):
    tabs = c.tables(); n = c.n
    prods = sorted(tabs[n + j] for j, (op, a, b) in enumerate(c.gates) if op == AND)
    return hashlib.sha1(repr(prods).encode()).hexdigest()[:8], prods


def forms_of(c, t2k):
    n = c.n; tabs = c.tables()
    F = [1 << (1 + i) for i in range(n)]
    for j, (op, a, b) in enumerate(c.gates):
        if op == XOR: f = F[a] ^ F[b]
        elif op == XNOR: f = F[a] ^ F[b] ^ 1
        elif op == NOT: f = F[a] ^ 1
        elif op == AND: f = 1 << (1 + n + t2k[tabs[n + j]])
        else: raise ValueError(op)
        F.append(f)
    return F


def collect(circs, t2k, n=8):
    tmpl = set(); pairs = {}; outs = None
    for c in circs:
        F = forms_of(c, t2k)
        o = [F[s] for s in c.outputs]
        if outs is None: outs = o
        assert o == outs, 'outputs differ (input/output order?)'
        for j, (op, a, b) in enumerate(c.gates):
            f = F[n + j]
            if op == AND:
                k = (f.bit_length() - 1) - 1 - n
                L, R = sorted((F[a], F[b]))
                pairs.setdefault(k, set()).update({(L, R), tuple(sorted((L, L ^ R ^ 1))), tuple(sorted((L ^ R ^ 1, R)))})
            elif op == NOT:
                tmpl.add((f, F[a], F[a]))
            else:
                x, y = sorted((F[a], F[b])); tmpl.add((f, x, y))
    return tmpl, pairs, outs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fam', required=True); ap.add_argument('--starts', required=True)
    ap.add_argument('--extra', action='append', default=[]); ap.add_argument('--D', type=int, required=True)
    ap.add_argument('--K', type=int, required=True); ap.add_argument('--closure', type=int, default=1)
    ap.add_argument('--seconds', type=float, default=1800); ap.add_argument('--out')
    ap.add_argument('--solver', default='glucose4'); ap.add_argument('--maxcirc', type=int, default=400)
    ap.add_argument('--log'); ap.add_argument('--K0', type=int, default=140); ap.add_argument('--hint')
    ap.add_argument('--lns', help='LNS mode: start circuit (family member, GD <= D)')
    ap.add_argument('--cap-ad', type=int, default=5); ap.add_argument('--cap-a', type=int, default=28)
    ap.add_argument('--lns-sec', type=float, default=20); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--side', type=float, default=0.3, help='LNS: share of equal-size (sideways) queries')
    ap.add_argument('--outdir', help='LNS: write every improved / sideways circuit here')
    a = ap.parse_args()
    T0 = time.time()
    M = core.Model.load('nist')
    files = [r['path'] for r in json.loads(Path(a.starts).read_text()) if r.get('fam') == a.fam]
    if a.lns: files = [a.lns] + files
    for d in a.extra:
        files += [str(p) for p in sorted(Path(d).glob('*.bfx')) + sorted(Path(d).glob('*.circ.txt'))]
    circs = []; t2k = None; seen = set()
    for p in files:
        try: c = load(p)
        except Exception: continue
        if tuple(c.value_table()) != TAB: continue
        key, prods = fam_key(c)
        if key != a.fam: continue
        h = hashlib.sha1(core.to_kernel(c).encode()).hexdigest()
        if h in seen: continue
        seen.add(h); circs.append(c)
        if t2k is None: t2k = {t: k for k, t in enumerate(prods)}
        if len(circs) >= a.maxcirc: break
    n = 8; K_AND = len(t2k)
    tmpl, pairs, outs = collect(circs, t2k)
    forms = {f for t in tmpl for f in t} | set(outs) | {f for ps in pairs.values() for p in ps for f in p}
    for i in range(n): forms.add(1 << (1 + i))
    for k in range(K_AND): forms.add(1 << (1 + n + k))
    base_t = len(tmpl)
    if a.closure:
        fl = sorted(forms)
        for i, x in enumerate(fl):
            for y in fl[i + 1:]:
                s = x ^ y
                if s in forms and s != x and s != y: tmpl.add((s, x, y))
                if (s ^ 1) in forms and (s ^ 1) != x and (s ^ 1) != y: tmpl.add((s ^ 1, x, y))
            if (x ^ 1) in forms: tmpl.add((x ^ 1, x, x))
    info = {'circuits': len(circs), 'forms': len(forms), 'templates_union': base_t, 'templates': len(tmpl),
            'and_pairs': sum(len(v) for v in pairs.values()), 'D': a.D, 'K': a.K, 'closure': a.closure}
    print(json.dumps(info), flush=True)
    inputs = {1 << (1 + i) for i in range(n)}
    zf = {1 << (1 + n + k): k for k in range(K_AND)}
    by_f = {}
    for t in tmpl: by_f.setdefault(t[0], []).append(t)
    # ASAP levels over the union
    INF = 10 ** 6
    lev = {f: (0 if f in inputs else INF) for f in forms}
    changed = True
    while changed:
        changed = False
        for f in forms:
            if f in inputs: continue
            best = lev[f]
            for (_, x, y) in by_f.get(f, ()):
                v = 1 + max(lev[x], lev[y])
                if v < best: best = v
            if f in zf:
                for (L, R) in pairs.get(zf[f], ()):
                    if L in lev and R in lev:
                        v = 1 + max(lev[L], lev[R])
                        if v < best: best = v
            if best < lev[f]: lev[f] = best; changed = True
    D = a.D
    if any(lev[o] > D for o in outs):
        print(json.dumps({'result': 'UNSAT-trivial', 'why': 'output ASAP > D', 'asap_outs': [lev[o] for o in outs]})); return
    pool = IDPool(); cl = []
    def av(f, l):
        if f in inputs: return True
        if l < lev[f] or l > D: return False
        return pool.id(('a', f, l))
    sel = {}
    def S(t):
        if t not in sel: sel[t] = pool.id(('s',) + t)
        return sel[t]
    for f in forms:
        if f in inputs or lev[f] > D: continue
        for l in range(lev[f], D + 1):
            v = av(f, l)
            if l < D: cl.append([-v, av(f, l + 1)])
            alts = []
            for t in by_f.get(f, ()):
                _, x, y = t
                ax, ay = av(x, l - 1), av(y, l - 1)
                if ax is False or ay is False: continue
                w = pool.id(('w', t, l)); alts.append(w)
                cl.append([-w, S(t)])
                if ax is not True: cl.append([-w, ax])
                if ay is not True: cl.append([-w, ay])
            if f in zf:
                for (L, R) in pairs.get(zf[f], ()):
                    if L not in lev or R not in lev: continue
                    aL, aR = av(L, l - 1), av(R, l - 1)
                    if aL is False or aR is False: continue
                    y_ = pool.id(('y', zf[f], L, R, l)); alts.append(y_)
                    if aL is not True: cl.append([-y_, aL])
                    if aR is not True: cl.append([-y_, aR])
            cl.append([-v] + alts)
    for o in outs:
        v = av(o, D)
        if v is True: continue
        cl.append([v])
    svars = list(sel.values())
    from pysat.card import ITotalizer
    ub = min(len(svars), a.K0)
    tot = ITotalizer(lits=svars, ubound=ub, top_id=pool.top)   # fix: aux ids must not collide with the pool
    pool.top = max(pool.top, tot.top_id)
    print(json.dumps({'vars': pool.top, 'clauses': len(cl), 'card_clauses': len(tot.cnf.clauses), 'sel_vars': len(svars),
                      't_build': round(time.time() - T0, 1)}), flush=True)
    import threading
    s = Solver(name=a.solver, bootstrap_with=cl + tot.cnf.clauses)
    # phase hint: the templates of the given hint circuits (union members) set to true
    if a.hint:
        hc = load(a.hint); HF = forms_of(hc, t2k); ph = []
        for j, (op, x_, y_) in enumerate(hc.gates):
            if op == AND: continue
            f = HF[n + j]
            t = (f, HF[x_], HF[x_]) if op == NOT else (f,) + tuple(sorted((HF[x_], HF[y_])))
            if t in sel: ph.append(sel[t])
        s.set_phases(ph + [-v for v in svars if v not in set(ph)])
    def decode(model):
        minlev = {}
        for f in forms:
            if f in inputs: minlev[f] = 0; continue
            for l in range(lev[f], D + 1):
                v = av(f, l)
                if v is not False and v is not True and v in model: minlev[f] = l; break
        just = {}
        need = list(outs)
        while need:
            f = need.pop()
            if f in inputs or f in just: continue
            l = minlev[f]; ch = None
            for t in by_f.get(f, ()):
                k = pool.obj2id.get(('w', t, l))
                if k is not None and k in model and sel.get(t) in model: ch = ('t', t); break
            if ch is None and f in zf:
                for (L, R) in pairs.get(zf[f], ()):
                    k = pool.obj2id.get(('y', zf[f], L, R, l))
                    if k is not None and k in model: ch = ('and', (L, R)); break
            assert ch is not None, 'no justification'
            just[f] = ch
            need += [ch[1][1], ch[1][2]] if ch[0] == 't' else list(ch[1])
        order = sorted(just, key=lambda f: minlev[f])
        sig = {1 << (1 + i): i for i in range(n)}; gates = []
        for f in order:
            ch = just[f]
            if ch[0] == 'and':
                L, R = ch[1]; gates.append((AND, sig[L], sig[R]))
            else:
                _, x, y = ch[1]
                if x == y: gates.append((NOT, sig[x], sig[x]))
                else: gates.append((XNOR if (x ^ y ^ f) == 1 else XOR, sig[x], sig[y]))
            sig[f] = n + len(gates) - 1
        return core.Circuit(n, len(outs), gates, [sig[o] for o in outs], 'unionsat').live()

    deadline = T0 + a.seconds
    if a.lns:
        import random
        rng = random.Random(a.seed)

        def tset(c):
            F = forms_of(c, t2k); ts = []; lg = [0] * n
            for j, (op, x, y) in enumerate(c.gates):
                lg.append(1 + max(lg[x], lg[y]))
                if op == AND: continue
                f = F[n + j]
                ts.append(((f, F[x], F[x]) if op == NOT else (f,) + tuple(sorted((F[x], F[y]))), lg[-1], n + j))
            return ts, lg
        cur = load(a.lns); mc = cur.metrics(M)
        assert fam_key(cur)[0] == a.fam and mc['GD'] <= D, 'LNS start must be a family member with GD <= D'
        cur_ts, cur_lg = tset(cur)
        assert all(t in sel for t, _, _ in cur_ts), 'start templates missing from the union'
        nbest = len(cur_ts); steps = 0; stats = {}
        print(json.dumps({'lns_start': a.lns, 'G': mc['G'], 'GD': mc['GD'], 'linear': nbest}), flush=True)
        while time.time() < deadline - 1:
            steps += 1
            kind = rng.choice(['rand', 'rand', 'level', 'cone'])
            N_ = len(cur_ts)
            if kind == 'rand':
                p = rng.choice([0.15, 0.25, 0.35, 0.5])
                free = {i for i in range(N_) if rng.random() < p}
            elif kind == 'level':
                w = rng.choice([2, 3, 4, 5]); l0 = rng.randint(1, max(1, D - w))
                free = {i for i, (t, l, sgi) in enumerate(cur_ts) if l0 <= l < l0 + w}
            else:
                # fan-in cones (linear gates only) of 2-4 random signals, depth-limited
                idx = {sgi: i for i, (t, l, sgi) in enumerate(cur_ts)}
                free = set()
                for _ in range(rng.choice([2, 3, 4])):
                    st = [rng.choice(list(idx))]; dep = rng.choice([3, 4, 6])
                    for _d in range(dep):
                        nx = []
                        for sgi in st:
                            if sgi in idx and idx[sgi] not in free:
                                free.add(idx[sgi]); op, x, y = cur.gates[sgi - n]; nx += [x, y]
                        st = nx
            if not free: continue
            side = rng.random() < a.side
            Kq = N_ - (0 if side else 1)
            assum = [sel[t] for i, (t, l, sgi) in enumerate(cur_ts) if i not in free] + [-tot.rhs[Kq]]
            if side:
                act = pool.id(('act', steps))
                s.add_clause([-act] + [-sel[cur_ts[i][0]] for i in free]); assum.append(act)
            rem = min(a.lns_sec, deadline - time.time())
            timer = threading.Timer(rem, lambda: s.interrupt()); timer.start()
            t1 = time.time()
            r = s.solve_limited(assumptions=assum, expect_interrupt=True)
            timer.cancel(); s.clear_interrupt()
            rs = {True: 'SAT', False: 'UNSAT', None: 'UNKNOWN'}[r]
            st_ = stats.setdefault((kind, side), {'SAT': 0, 'UNSAT': 0, 'UNKNOWN': 0}); st_[rs] += 1
            rec = {'step': steps, 'kind': kind, 'side': side, 'free': len(free), 'Kq': Kq, 'r': rs, 't': round(time.time() - t1, 1)}
            if r:
                model = set(x for x in s.get_model() if x > 0)
                c = decode(model); m = c.metrics(M)
                if tuple(c.value_table()) != TAB: raise RuntimeError('decoded circuit is wrong')
                nl = m['G'] - m['A']
                rec.update({'G': m['G'], 'GD': m['GD'], 'AD': m['AD']})
                if m['AD'] > a.cap_ad or m['A'] > a.cap_a:
                    rec['REJECT'] = 'outside hard limits (A %d AD %d)' % (m['A'], m['AD'])
                elif nl <= N_ and m['GD'] <= D:
                    cur = c; cur_ts, cur_lg = tset(c)
                    if a.outdir and (nl < nbest or side):
                        Path(a.outdir).mkdir(parents=True, exist_ok=True)
                        nm = 'us-a%d-ad%d-g%d-gd%d-s%d-%d.circ.txt' % (m['A'], m['AD'], m['G'], m['GD'], a.seed, steps)
                        Path(a.outdir, nm).write_text(core.write_ncff(c, M, comments=['P1 unionsat LNS fam %s D %d seed %d step %d from %s' % (a.fam, D, a.seed, steps, a.lns)]))
                    if nl < nbest:
                        nbest = nl
                        if a.out: Path(a.out).write_text(core.write_ncff(c, M, comments=['P1 unionsat LNS fam %s D %d seed %d step %d from %s' % (a.fam, D, a.seed, steps, a.lns)]))
                        rec['IMPROVED'] = True
            print(json.dumps(rec), flush=True)
        res = {'lns_done': steps, 'best_linear': nbest, 'best_G': nbest + K_AND, 'stats': {'%s/%s' % k: v for k, v in stats.items()},
               't_total': round(time.time() - T0, 1)}
        res.update(info)
        print(json.dumps(res), flush=True)
        if a.log:
            with open(a.log, 'a') as fh: fh.write(json.dumps(res) + chr(10))
        return
    best = None; K = ub; hist = []
    while True:
        rem = deadline - time.time()
        if rem <= 1: hist.append((K, 'TIMEOUT', 0)); break
        timer = threading.Timer(rem, lambda: s.interrupt()); timer.start()
        t1 = time.time()
        assum = [-tot.rhs[K]] if K < ub else []
        r = s.solve_limited(assumptions=assum, expect_interrupt=True)
        timer.cancel(); s.clear_interrupt()
        hist.append((K, {True: 'SAT', False: 'UNSAT', None: 'UNKNOWN'}[r], round(time.time() - t1, 1)))
        if not r:
            print(json.dumps({'K': K, 'r': hist[-1][1], 't': hist[-1][2]}), flush=True); break
        model = set(x for x in s.get_model() if x > 0)
        c = decode(model); m = c.metrics(M)
        ok = tuple(c.value_table()) == TAB
        nl = m['G'] - m['A']
        print(json.dumps({'K': K, 'r': 'SAT', 't': hist[-1][2], 'ok': ok, 'G': m['G'], 'GD': m['GD'], 'AD': m['AD']}), flush=True)
        if not ok: raise RuntimeError('decoded circuit is wrong')
        best = c
        if a.out:
            Path(a.out).write_text(core.write_ncff(c, M, comments=['P1 unionsat fam %s D %d K %d closure %d' % (a.fam, D, K, a.closure)]))
        if nl - 1 < a.K: break
        K = min(nl - 1, ub - 1)
    res = {'result': hist[-1][1], 'hist': hist, 't_total': round(time.time() - T0, 1)}
    if best is not None:
        m = best.metrics(M); res.update({'A': m['A'], 'AD': m['AD'], 'G': m['G'], 'GD': m['GD']})
    res.update(info)
    print(json.dumps(res), flush=True)
    if a.log:
        with open(a.log, 'a') as fh: fh.write(json.dumps(res) + chr(10))

if __name__ == '__main__':
    main()
