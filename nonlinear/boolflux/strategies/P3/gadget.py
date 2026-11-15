#!/usr/bin/env python3
"""Exact SAT search for the cheapest 'trick block' of a 17-AND bottom (the 5 mixed products of NIST 117).

The bottom of CIRC is split into standard terms (Y-form * X-form) and the block (every term with a mixed
operand).  The block's contribution R_o (output o; exact quadratic polynomial over (1, X, Y), from the
total minus the standard terms) is the target.  A gadget is k ANDs L_j * R_j (affine over const + Z + Y,
Z = basis of the X-forms the block and the level-1 ANDs live in), output masks w_j, corrections c_fo
(level-1 AND f XORed into output o), such that for every output and every degree-2 monomial
    sum_j w_jo [m](L_j R_j) + sum_f c_fo [m](Q_f) = [m](R_o)
(linear monomials are free: they become XORs of existing linear signals).  Cost = operands that are not
an existing front signal (each needs >= 1 XOR).  [C] for this model: an UNSAT answer means no gadget
with k ANDs and <= budget new operands exists over this Z, Y and these corrections.

    gadget.py REF CIRC --k 5 --budget B [--nsol 20] [--budget-conf N] [--yfull]
"""
import itertools, json, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import bottom as BT, flip as FL, qflip as QF, rank_sat as RS  # noqa
from pysat.solvers import Solver  # noqa
from pysat.card import CardEnc, EncType  # noqa


def arg(a, k, d, f=str):
    return f(a[a.index(k) + 1]) if k in a else d


def main():
    a = sys.argv[1:]
    ref, circ = a[0], a[1]
    K = arg(a, '--k', 5, int); budget = arg(a, '--budget', 7, int); nsol = arg(a, '--nsol', 20, int)
    conf = arg(a, '--budget-conf', 0, int)
    rc, Yt = FL.ref_basis(ref)
    c = BT.load(circ)
    free, fixed, lin = QF.decompose(c, Yt)
    def mixed(f): return (f >> 9) and (f >> 1) & 0xFF
    std = [t for t in free if not mixed(t[0]) and not mixed(t[1])]
    blk = [t for t in free if mixed(t[0]) or mixed(t[1])]
    goal = QF.total(free, fixed, lin)
    stdt = QF.total(std, [], [0] * 8)
    Rq = [[x ^ y for x, y in zip(goal[o][0], stdt[o][0])] for o in range(8)]
    print('block terms', len(blk), 'standard', len(std))
    # Z: span of X-parts of block operands and of the level-1 AND operands
    xs = []
    for L, R, w in blk + [tuple(t) for t in fixed]:
        xs += [(L >> 1) & 0xFF, (R >> 1) & 0xFF]
    Zb = []           # basis of x-forms (8-bit), reduced
    def red(v, B):
        for b in B:
            if v ^ b < v: v ^= b
        return v
    for v in xs:
        r = red(v, sorted(Zb, reverse=True))
        if r:
            Zb.append(r); Zb.sort(reverse=True)
    dz = len(Zb)
    # coordinates of an x-form in Zb (Zb is in echelon form by leading bit after sorting)
    def zco(v):
        co = 0
        for i, b in enumerate(Zb):
            if v >> (b.bit_length() - 1) & 1: v ^= b; co |= 1 << i
        return co if v == 0 else None
    # monomials over variables: z0..z_{dz-1}, y0..y3  (indices 0..dz+3); pairs a<b
    nv = dz + 4
    pairs = [(i, j) for i in range(nv) for j in range(i + 1, nv)]
    # target and corrections in these coordinates: convert 13-bit forms' quadratic rows to pairs over (x,y)
    # first express x-variables x_i in terms of z: only possible for forms inside span(Z); quadratic forms of
    # the target live in span(Z) (x) span(Z) + ... , so map via forms: we test coefficients on (x,y) monomials.
    # Simplest exact route: work in the (x, y) monomial space for the equation, with L, R parameterised by
    # z-coordinates: an operand L = l0 + sum lz_i Z_i + sum ly_i y_i.
    def form13(cst, zc, yc):
        v = 0
        for i in range(dz):
            if zc >> i & 1: v ^= Zb[i]
        return cst | (v << 1) | (yc << 9)
    # existing front signals as 13-bit forms
    T = c.tables(); la, lg = BT.and_levels(c)
    B = FL.basis_for(Yt, c.n)
    E = set()
    for s in range(c.n + len(c.gates)):
        if la[s] <= 3:
            f = B.coords(T[s])
            # exclude mixed forms built for the old bottom (AND level 3 with an X part)
            if f is not None and not (la[s] == 3 and (f >> 1) & 0xFF and f >> 9): E.add(f); E.add(f ^ 1)
    # SAT
    F = RS.CNF()
    Lv = [[F.var() for _ in range(1 + dz + 4)] for _ in range(K)]
    Rv = [[F.var() for _ in range(1 + dz + 4)] for _ in range(K)]
    Wv = [[F.var() for _ in range(8)] for _ in range(K)]
    fixl = [k for k, (L, R, w) in enumerate(fixed) if zco((L >> 1) & 0xFF) is not None and zco((R >> 1) & 0xFF) is not None and not (L >> 9) and not (R >> 9)]
    Cv = {(f, o): F.var() for f in fixl for o in range(8)}
    # variable bit -> 13-bit-form bit mapping is linear: operand form = const + sum z-bits Zb + y-bits.
    # coefficient of monomial (x_p x_q) / (x_p y_r) / (y_r y_s) in L*R: compute via linear maps:
    # L as 13-bit form has x-bit p = XOR_i lz_i Zb_i[p].  Build, per operand, literal-expressions for its
    # 13-bit form bits as XORs of SAT vars.
    def opbits(V):
        bits = [None] * 13
        bits[0] = [V[0]]
        for p in range(8):
            bits[1 + p] = [V[1 + i] for i in range(dz) if Zb[i] >> p & 1]
        for r in range(4):
            bits[9 + r] = [V[1 + dz + r]]
        return bits
    def xor_list(lits):
        if not lits: return None
        acc = lits[0]
        for l in lits[1:]: acc = F.XOR(acc, l)
        return acc
    Lb = []; Rb = []
    for j in range(K):
        Lb.append([xor_list(b) for b in opbits(Lv[j])]); Rb.append([xor_list(b) for b in opbits(Rv[j])])
    # nonzero operands, w nonzero
    for j in range(K):
        F.cl.append(Lv[j][1:]); F.cl.append(Rv[j][1:]); F.cl.append(Wv[j][:])
    def AND_(x, y):
        if x is None or y is None: return None
        return F.AND(x, y)
    # quadratic coefficient of monomial (a,b) a<b over 13-bit var positions 1..12: L_a R_b + L_b R_a
    qpos = [(p, q) for p in range(1, 13) for q in range(p + 1, 13)]
    for o in range(8):
        for (p, q) in qpos:
            terms = []
            for j in range(K):
                t1 = AND_(Lb[j][p], Rb[j][q]); t2 = AND_(Lb[j][q], Rb[j][p])
                cj = xor_list([t for t in (t1, t2) if t is not None])
                if cj is not None: terms.append(F.AND(cj, Wv[j][o]))
            for f in fixl:
                qf, lf = QF.prodfun(*fixed[f][:2])
                row = qf[p - 1]
                if row >> q & 1: terms.append(Cv[(f, o)])
            tgt = Rq[o][p - 1] >> q & 1
            acc = xor_list(terms)
            if acc is None:
                if tgt: print('target monomial unreachable', o, p, q); return
                continue
            F.cl.append([acc] if tgt else [-acc])
    # cost: operand not in E
    newop = []
    for j in range(K):
        for V, Bb in ((Lv[j], Lb[j]), (Rv[j], Rb[j])):
            # indicator m = 1 if operand equals some form in E (restricted to forms in our space)
            eqs = []
            for f in E:
                # f must be representable: x-part in span Z
                zc = zco((f >> 1) & 0xFF)
                if zc is None: continue
                lits = [V[0] if f & 1 else -V[0]]
                lits += [V[1 + i] if zc >> i & 1 else -V[1 + i] for i in range(dz)]
                lits += [V[1 + dz + r] if f >> (9 + r) & 1 else -V[1 + dz + r] for r in range(4)]
                e = F.var()
                for l in lits: F.cl.append([-e, l])
                eqs.append(e)
            n_ = F.var()        # n_ = 1 -> new operand (not in E)
            F.cl.append([n_] + eqs)
            newop.append(n_)
    # linear residual per output: x-part must vanish, a nonzero y-part costs one XOR (counted)
    Rl = [goal[o][1] ^ stdt[o][1] for o in range(8)]
    linc = []
    for o in range(8):
        ys = []
        for p in range(1, 13):
            terms = []
            for j in range(K):
                parts = [AND_(Lb[j][0], Rb[j][p]), AND_(Lb[j][p], Rb[j][0]), AND_(Lb[j][p], Rb[j][p])]
                cj = xor_list([t for t in parts if t is not None])
                if cj is not None: terms.append(F.AND(cj, Wv[j][o]))
            for f in fixl:
                qf, lf = QF.prodfun(*fixed[f][:2])
                if lf >> p & 1: terms.append(Cv[(f, o)])
            acc = xor_list(terms)
            tgt = Rl[o] >> p & 1
            if acc is None:
                e = None if not tgt else 'one'
            else:
                e = acc if not tgt else -acc     # e true <=> residual bit set
            if p <= 8 and '--allow-xlin' in a:
                if e == 'one': ys.append('one')
                elif e is not None: ys.append(e)
            elif p <= 8:
                if e == 'one': print('x-linear residual unavoidable'); return
                if e is not None: F.cl.append([-e])
            else:
                if e == 'one': ys.append('one')
                elif e is not None: ys.append(e)
        if 'one' in ys: z = None; linc.append('one')
        elif ys:
            z = F.var()
            for e in ys: F.cl.append([-e, z])
            linc.append(z)
    wones = [x for j in range(K) for x in Wv[j]]
    costlits = newop + [z for z in linc if z != 'one']
    fixedcost = sum(1 for z in linc if z == 'one')
    lin_budget = arg(a, '--lin-budget', 99, int)
    card = CardEnc.atmost(lits=costlits, bound=max(0, budget - fixedcost), top_id=F.n, encoding=EncType.seqcounter)
    F.n = max(F.n, card.nv)
    cl = F.cl + card.clauses
    wb = arg(a, '--wbudget', 0, int)
    if wb:
        c2 = CardEnc.atmost(lits=wones, bound=wb, top_id=F.n, encoding=EncType.seqcounter)
        F.n = max(F.n, c2.nv); cl += c2.clauses
    print('cost = new operands + outputs with a Y-linear residual <= %d' % budget)
    print('vars', F.n, 'clauses', len(cl), 'dz', dz, 'fixed usable', len(fixl), 'E', len(E), flush=True)
    s = Solver(name='cadical153', bootstrap_with=cl)
    sols = []
    t0 = time.time()
    while len(sols) < nsol:
        if conf: s.conf_budget(conf); r = s.solve_limited()
        else: r = s.solve()
        print('solve ->', r, '%.1fs' % (time.time() - t0), flush=True)
        if not r: break
        M = set(l for l in s.get_model() if l > 0)
        def val(V): return sum(1 << i for i, x in enumerate(V) if x in M)
        prods = []
        for j in range(K):
            lv = val(Lv[j]); rv = val(Rv[j])
            Lf = form13(lv & 1, (lv >> 1) & ((1 << dz) - 1), lv >> (1 + dz))
            Rf = form13(rv & 1, (rv >> 1) & ((1 << dz) - 1), rv >> (1 + dz))
            prods.append((Lf, Rf, val(Wv[j])))
        cors = {f: sum(1 << o for o in range(8) if Cv[(f, o)] in M) for f in fixl}
        nnew = sum(1 for x in newop if x in M)
        nlin = sum(1 for z in linc if z == 'one' or z in M)
        sols.append({'prods': prods, 'cors': cors, 'new_operands': nnew, 'lin_outputs': nlin,
                     'w_ones': sum(1 for x in wones if x in M)})
        print(json.dumps(sols[-1]), flush=True)
        # block this exact assignment of operands + w
        blk_cl = []
        for j in range(K):
            for V in (Lv[j], Rv[j], Wv[j]):
                blk_cl += [-x if x in M else x for x in V]
        s.add_clause(blk_cl)
    Path('gadget-sols.json').write_text(json.dumps(sols))


if __name__ == '__main__':
    main()
