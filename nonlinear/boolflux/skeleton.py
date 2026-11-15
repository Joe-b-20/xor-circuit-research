"""AND skeletons: extraction from a circuit, the skel kernel's file format, synthesis back to gates.

Basis positions: 0 = constant 1, 1+i = input x_i, 1+n+k = AND k.  A form is a Python int whose
bit p selects basis position p.  Every nonlinear two-input gate is ((a^p) & (b^q)) ^ r for
constants p, q, r, so any circuit over the libraries here becomes a skeleton whose AND count is
the circuit's nonlinear gate count.
"""
from __future__ import annotations

from .core import Circuit, OPS, NONLINEAR_OPS

MW = 8          # 64-bit words per form in the kernel's file format


def nl_decompose(op):
    """(p, q, r) with op(a,b) = ((a^p) & (b^q)) ^ r."""
    ones = [i for i in range(4) if (op >> i) & 1]
    if len(ones) == 1:
        idx = ones[0]; r = 0
    else:
        idx = [i for i in range(4) if not (op >> i) & 1][0]; r = 1
    return 1 - (idx >> 1), 1 - (idx & 1), r


def extract(c: Circuit):
    n = c.n
    form = [1 << (1 + i) for i in range(n)]
    ands = []
    for op, a, b in c.gates:
        fa, fb = form[a], form[b]
        if op == OPS['XOR']: f = fa ^ fb
        elif op == OPS['XNOR']: f = fa ^ fb ^ 1
        elif op == OPS['NOT']: f = fa ^ 1
        elif op in NONLINEAR_OPS:
            p, q, r = nl_decompose(op)
            ands.append((fa ^ p, fb ^ q))
            f = (1 << (1 + n + len(ands) - 1)) ^ r
        else:
            raise ValueError('op %d' % op)
        form.append(f)
    return {'n': n, 'm': c.m, 'ands': ands, 'outputs': [form[s] for s in c.outputs]}


def _hexwords(x, nw):
    return ' '.join('%016x' % ((x >> (64 * i)) & ((1 << 64) - 1)) for i in range(nw))


def _fromwords(toks):
    return sum(int(t, 16) << (64 * i) for i, t in enumerate(toks))


MAXK = 480      # the skel kernel's limit on the number of ANDs (kernel/skel.c)


def write_skel(sk, out_tables):
    n = sk['n']; W = max(1, (1 << n) // 64)
    if len(sk['ands']) > MAXK or 1 + n + len(sk['ands']) > 64 * MW:
        # review5 P17: a form beyond 64*MW basis positions was cut off without a word
        raise ValueError('skeleton with %d ANDs: the skeleton kernel takes at most %d' % (len(sk['ands']), min(MAXK, 64 * MW - 1 - n)))
    lines = ['n %d m %d k %d mw %d w %d' % (n, sk['m'], len(sk['ands']), MW, W)]
    for L, R in sk['ands']:
        lines.append(_hexwords(L, MW) + ' ' + _hexwords(R, MW))
    for t in out_tables:
        lines.append(_hexwords(t, W))
    return '\n'.join(lines) + '\n'


def read_skel(text):
    rows = [ln.split() for ln in text.splitlines() if ln.strip() and not ln.startswith('#')]
    h = rows[0]; n, m, k = int(h[1]), int(h[3]), int(h[5])
    ands = [(_fromwords(r[:MW]), _fromwords(r[MW:2 * MW])) for r in rows[1:1 + k]]
    yi = [i for i, r in enumerate(rows) if r == ['Y']]
    outs = [_fromwords(r) for r in rows[yi[0] + 1:yi[0] + 1 + m]] if yi else None
    return {'n': n, 'm': m, 'ands': ands, 'outputs': outs}


def _form_tables(sk):
    """Truth tables of the skeleton's basis positions (constant, inputs, ANDs)."""
    from .core import input_tables
    n = sk['n']; ones = (1 << (1 << n)) - 1
    tab = [ones] + input_tables(n)

    def ft(f):
        t = 0; i = 0
        while f:
            if f & 1: t ^= tab[i]
            f >>= 1; i += 1
        return t
    for L, R in sk['ands']:
        tab.append(ft(L) & ft(R))
    return tab, ft, ones


def parent_forms(sk, parent):
    """For every signal of the parent circuit, its affine form over the skeleton's basis, or None.
    Inputs map to inputs; a parent nonlinear gate maps to the skeleton AND with the same core truth
    table (the gate is ((a^p)&(b^q))^r); a linear gate maps when its operands do.  Matching is by
    complete truth table, so a mapped signal computes exactly its form."""
    n = sk['n']
    tab, ft, ones = _form_tables(sk)
    by_table = {}
    for k in range(len(sk['ands'])):
        by_table.setdefault(tab[1 + n + k], k)
    ptab = parent.tables()
    form = [1 << (1 + i) for i in range(n)]
    for j, (op, a, b) in enumerate(parent.gates):
        fa, fb = form[a], form[b]
        if op in NONLINEAR_OPS:
            p_, q_, r_ = nl_decompose(op)
            core_t = ptab[n + j] ^ (ones if r_ else 0)
            k = by_table.get(core_t)
            form.append(None if k is None else (1 << (1 + n + k)) ^ r_)
        elif fa is None or (op != OPS['NOT'] and fb is None):
            form.append(None)
        elif op == OPS['XOR']: form.append(fa ^ fb)
        elif op == OPS['XNOR']: form.append(fa ^ fb ^ 1)
        elif op == OPS['NOT']: form.append(fa ^ 1)
        else: form.append(None)
    return form


def synthesize(sk, ops, name='skel', use_paar=True, paar_outputs=True, parent=None):
    """Gates for a skeleton: each needed form is built greedily from already computed signals
    (largest overlap first), constants become XNOR/NOT, ANDs use AND (or ANDN/NOR when a
    complemented operand can be absorbed and the library has them).

    With ``parent`` (the circuit the skeleton came from, possibly before skeleton moves), the
    parent's gates are carried over first wherever their exact function still exists in the new
    skeleton: every linear gate whose operands carry over, and every AND whose core truth table is
    one of the new ANDs (with its own operands, when those carry over).  Only what the skeleton
    moves broke is synthesized from forms; unused copies are swept at the end."""
    n = sk['n']; gates = []
    have = {}                                  # form without constant -> signal
    for i in range(n): have[1 << (1 + i)] = i
    pos_sig = {1 + i: i for i in range(n)}

    def g(op, a, b):
        gates.append((op, a, b)); return n + len(gates) - 1

    pf = parent_forms(sk, parent) if parent is not None else None
    psig = ([i for i in range(n)] + [None] * len(parent.gates)) if parent is not None else None
    and_from_parent = {}                       # new AND index -> parent gate index (plain AND)
    if parent is not None:
        for j, (op, a, b) in enumerate(parent.gates):
            f = pf[n + j]
            if op == OPS['AND'] and f is not None and not (f & 1):
                and_from_parent.setdefault((f.bit_length() - 1) - 1 - n, j)

    def absorb():
        """Copy every parent linear gate whose operands are available (one pass, parent order)."""
        if parent is None: return
        for j, (op, a, b) in enumerate(parent.gates):
            sj = n + j
            if psig[sj] is not None or pf[sj] is None or op in NONLINEAR_OPS: continue
            if psig[a] is None or (op != OPS['NOT'] and psig[b] is None): continue
            f = pf[sj]
            if f in have: psig[sj] = have[f]; continue
            if op not in ops: continue
            sig = g(op, psig[a], psig[a] if op == OPS['NOT'] else psig[b])
            have[f] = sig; psig[sj] = sig

    def build(f):
        """Signal computing form f (constant bit 0 must be clear)."""
        if f == 0: raise ValueError('zero form')
        if f in have: return have[f]
        parts = []; rest = f
        while rest:
            best = None; bestgain = 0
            for fm, s in have.items():
                if fm & 1: continue                       # complemented forms are not terms
                gain = bin(rest).count('1') - bin(rest ^ fm).count('1')
                if gain > bestgain or (gain == bestgain and gain > 0 and best is not None and fm < best[0]):
                    best, bestgain = (fm, s), gain
            if best is None or bestgain <= 0:
                p = (rest & -rest).bit_length() - 1
                best = (1 << p, have[1 << p] if (1 << p) in have else pos_sig[p])
            parts.append(best); rest ^= best[0]
        acc_f, acc_s = parts[0]
        for fm, s in parts[1:]:
            acc_f ^= fm
            acc_s = have[acc_f] if acc_f in have else g(OPS['XOR'], acc_s, s)
            have.setdefault(acc_f, acc_s)
        return acc_s

    def build_affine(f, allow_free_not=False):
        """(signal, complemented?) for an affine form."""
        c = f & 1; base = f & ~1
        if base == 0: raise ValueError('constant form')
        return build(base), c

    def materialize(sig, comp, fform):
        if not comp: return sig
        key = fform
        if key in have: return have[key]
        # complement: XNOR rewrite of the last XOR if possible, else NOT
        if OPS['XNOR'] in ops and sig >= n and gates[sig - n][0] == OPS['XOR']:
            op, a, b = gates[sig - n]; s = g(OPS['XNOR'], a, b)
        elif OPS['NOT'] in ops: s = g(OPS['NOT'], sig, sig)
        elif OPS['XNOR'] in ops: raise ValueError('need a constant operand for XNOR-NOT')
        elif OPS['NAND'] in ops: s = g(OPS['NAND'], sig, sig)
        else: raise ValueError('no complement available')
        have[key] = s
        return s

    def paar(forms):
        """Paar's heuristic: while some pair of terms occurs in two or more of the forms, XOR
        the most frequent pair once and substitute it (a new pseudo-term) everywhere.  Pair counts
        are kept incrementally with a lazy max-heap (ties: smallest term ids first, the same order
        as a full recount), so each substitution costs only the rows it touches."""
        import heapq
        nxt = max([1 + n + len(sk['ands'])] + [f.bit_length() for f in forms])
        rows = []
        for f in forms:
            r = f & ~1
            if r and r & (r - 1):
                rows.append({i for i in range(r.bit_length()) if (r >> i) & 1})
        cnt = {}; where = {}
        for ri, r in enumerate(rows):
            bs = sorted(r)
            for x in range(len(bs)):
                for y in range(x + 1, len(bs)):
                    k = (bs[x], bs[y]); cnt[k] = cnt.get(k, 0) + 1; where.setdefault(k, set()).add(ri)
        heap = [(-c, k[0], k[1]) for k, c in cnt.items()]; heapq.heapify(heap)
        term_form = {}

        def bump(k, d, ri):
            c = cnt.get(k, 0) + d
            if c: cnt[k] = c
            else: cnt.pop(k, None)
            if d > 0: where.setdefault(k, set()).add(ri)
            else: where.get(k, set()).discard(ri)
            if c: heapq.heappush(heap, (-c, k[0], k[1]))
        while heap:
            negc, a, b = heapq.heappop(heap)
            if cnt.get((a, b), 0) != -negc: continue          # stale entry
            if -negc < 2: break
            fa = term_form.get(a, 1 << a); fb = term_form.get(b, 1 << b)
            sa = have[fa] if fa in have else pos_sig[a]
            sb = have[fb] if fb in have else pos_sig[b]
            f = fa ^ fb
            if f not in have: have[f] = g(OPS['XOR'], sa, sb)
            t = nxt; nxt += 1; term_form[t] = f
            for ri in list(where.get((a, b), ())):
                r = rows[ri]
                others = [x for x in r if x != a and x != b]
                bump((a, b), -1, ri)
                for x in others:
                    bump((min(a, x), max(a, x)), -1, ri); bump((min(b, x), max(b, x)), -1, ri)
                r.discard(a); r.discard(b)
                if others:
                    for x in others: bump((x, t), +1, ri)       # t is larger than every x
                    r.add(t)
                else:
                    r.clear()

    # Paar over the operand forms of each AND level, then build the ANDs of that level
    lvl = []
    for k, (L, R) in enumerate(sk['ands']):
        deps = [j for j in range(k) if ((L | R) >> (1 + n + j)) & 1]
        lvl.append(1 + max([lvl[j] for j in deps], default=0))
    done_level = set()
    for k in sorted(range(len(sk['ands'])), key=lambda j: (lvl[j], j)):
        L, R = sk['ands'][k]
        absorb()
        if lvl[k] not in done_level:
            done_level.add(lvl[k])
            if use_paar: paar([f for j, (L2, R2) in enumerate(sk['ands']) if lvl[j] == lvl[k] for f in (L2, R2)])
        j = and_from_parent.get(k)
        if j is not None and psig[parent.gates[j][1]] is not None and psig[parent.gates[j][2]] is not None:
            s = g(OPS['AND'], psig[parent.gates[j][1]], psig[parent.gates[j][2]])
            p = 1 + n + k
            pos_sig[p] = s; have[1 << p] = s; psig[n + j] = s
            continue
        sl, cl = build_affine(L); sr, cr = build_affine(R)
        if not cl and not cr: s = g(OPS['AND'], sl, sr)
        elif cl and not cr and OPS['ANDN'] in ops: s = g(OPS['ANDN'], sr, sl)
        elif cr and not cl and OPS['ANDN'] in ops: s = g(OPS['ANDN'], sl, sr)
        elif cl and cr and OPS['NOR'] in ops: s = g(OPS['NOR'], sl, sr)
        else:
            a = materialize(sl, cl, L); b = materialize(sr, cr, R)
            s = g(OPS['AND'], a, b)
        p = 1 + n + k
        pos_sig[p] = s; have[1 << p] = s
        if parent is not None:                 # a parent AND with this table now maps here
            for jj, (op, a, b) in enumerate(parent.gates):
                if psig[n + jj] is None and pf[n + jj] == (1 << p): psig[n + jj] = s
    absorb(); absorb()
    outs = []
    if paar_outputs: paar(list(sk['outputs']))
    for f in sk['outputs']:
        s, c = build_affine(f)
        outs.append(materialize(s, c, f))
    return Circuit(n, sk['m'], gates, outs, name).live()
