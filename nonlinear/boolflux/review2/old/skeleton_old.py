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


def write_skel(sk, out_tables):
    n = sk['n']; W = max(1, (1 << n) // 64)
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


def synthesize(sk, ops, name='skel', use_paar=True, paar_outputs=True):
    """Gates for a skeleton: each needed form is built greedily from already computed signals
    (largest overlap first), constants become XNOR/NOT, ANDs use AND (or ANDN/NOR when a
    complemented operand can be absorbed and the library has them)."""
    n = sk['n']; gates = []
    have = {}                                  # form without constant -> signal
    for i in range(n): have[1 << (1 + i)] = i
    pos_sig = {1 + i: i for i in range(n)}

    def g(op, a, b):
        gates.append((op, a, b)); return n + len(gates) - 1

    def build(f):
        """Signal computing form f (constant bit 0 must be clear)."""
        if f == 0: raise ValueError('zero form')
        if f in have: return have[f]
        parts = []; rest = f
        while rest:
            best = None; bestgain = 0
            for fm, s in have.items():
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
        the most frequent pair once and substitute it (a new pseudo-term) everywhere."""
        nonlocal_next = [max([1 + n + len(sk['ands'])] + [f.bit_length() for f in forms])]
        rows = [f & ~1 for f in forms if (f & ~1) and (f & ~1) & ((f & ~1) - 1)]
        term_form = {}
        while True:
            cnt = {}
            for r in rows:
                bits = [i for i in range(r.bit_length()) if (r >> i) & 1]
                for a in range(len(bits)):
                    for b in range(a + 1, len(bits)):
                        key = (bits[a], bits[b]); cnt[key] = cnt.get(key, 0) + 1
            if not cnt: break
            (a, b), c = max(cnt.items(), key=lambda kv: (kv[1], -kv[0][0], -kv[0][1]))
            if c < 2: break
            fa = term_form.get(a, 1 << a); fb = term_form.get(b, 1 << b)
            sa = have[fa] if fa in have else pos_sig[a]
            sb = have[fb] if fb in have else pos_sig[b]
            f = fa ^ fb
            if f not in have: have[f] = g(OPS['XOR'], sa, sb)
            t = nonlocal_next[0]; nonlocal_next[0] += 1
            term_form[t] = f
            rows = [(r ^ (1 << a) ^ (1 << b) | (1 << t)) if ((r >> a) & 1 and (r >> b) & 1) else r for r in rows]
            rows = [r for r in rows if r & (r - 1)]

    # Paar over the operand forms of each AND level, then build the ANDs of that level
    lvl = []
    for k, (L, R) in enumerate(sk['ands']):
        deps = [j for j in range(k) if ((L | R) >> (1 + n + j)) & 1]
        lvl.append(1 + max([lvl[j] for j in deps], default=0))
    done_level = set()
    for k in sorted(range(len(sk['ands'])), key=lambda j: (lvl[j], j)):
        L, R = sk['ands'][k]
        if lvl[k] not in done_level:
            done_level.add(lvl[k])
            if use_paar: paar([f for j, (L2, R2) in enumerate(sk['ands']) if lvl[j] == lvl[k] for f in (L2, R2)])
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
    outs = []
    if paar_outputs: paar(list(sk['outputs']))
    for f in sk['outputs']:
        s, c = build_affine(f)
        outs.append(materialize(s, c, f))
    return Circuit(n, sk['m'], gates, outs, name).live()
