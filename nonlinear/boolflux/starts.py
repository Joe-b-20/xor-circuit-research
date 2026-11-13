"""Naive starting circuits built mechanically from a value table (no optimisation).

``anf``: every output as the XOR of its algebraic-normal-form monomials; each monomial of
degree >= 2 is one AND of the monomial without its highest variable (built the same way,
shared between outputs) and that variable; XOR sums are balanced trees; a constant-1 ANF term
complements the last XOR (XNOR) or adds a NOT.  Uses AND, XOR, XNOR (and NOT).

``anf-or``: the same but every two-input XOR is written with the model's gates when XOR is not
allowed: XOR(a,b) = OR(ANDN(a,b), ANDN(b,a)) or = AND(OR(a,b), NAND(a,b)).  Only used for
libraries without XOR.
"""
from __future__ import annotations

from .core import Circuit, OPS, tables_from_values


def anf_coeffs(t, n):
    """Moebius transform of a truth table int: bit u of the result (an int) = ANF coefficient of
    the monomial with variable set u (pattern-index bits)."""
    N = 1 << n
    # bitset Moebius transform: for each variable bit, XOR the half without it into the half
    # with it (n big-integer operations instead of n * 2^n list operations)
    for i in range(n):
        step = 1 << i
        low = 0
        for x in range(0, N, 2 * step):          # positions with bit i clear
            low |= ((1 << step) - 1) << x
        t ^= (t & low) << step
    return t                                     # bit u = coefficient of monomial u


def anf(n, m, table, model_ops=None, name='anf'):
    outs = tables_from_values(n, m, table)
    gates = []
    sig_of_bit = {1 << (n - 1 - i): i for i in range(n)}   # pattern bit -> input signal
    mono = {}

    def monomial(u):
        if u in mono: return mono[u]
        if u & (u - 1) == 0:
            mono[u] = sig_of_bit[u]; return mono[u]
        hi = 1 << (u.bit_length() - 1)
        a = monomial(u ^ hi); b = sig_of_bit[hi]
        gates.append((OPS['AND'], a, b)); mono[u] = n + len(gates) - 1
        return mono[u]

    def xor_tree(sigs, invert):
        sigs = list(sigs)
        if not sigs:
            raise ValueError('constant output not supported')
        while len(sigs) > 1:
            nxt = []
            for i in range(0, len(sigs) - 1, 2):
                last = invert and len(sigs) == 2
                gates.append((OPS['XNOR'] if last else OPS['XOR'], sigs[i], sigs[i + 1]))
                if last: invert = False
                nxt.append(n + len(gates) - 1)
            if len(sigs) % 2: nxt.append(sigs[-1])
            sigs = nxt
        if invert:
            gates.append((OPS['NOT'], sigs[0], sigs[0])); return n + len(gates) - 1
        return sigs[0]

    out_sigs = []
    for t in outs:
        co = anf_coeffs(t, n)
        terms = []; rest = co & ~1
        while rest:                              # set bits only, in increasing order
            low = rest & -rest; terms.append(monomial(low.bit_length() - 1)); rest ^= low
        out_sigs.append(xor_tree(terms, bool(co & 1)))
    c = Circuit(n, m, gates, out_sigs, name)
    if model_ops is not None and not {g[0] for g in c.gates} <= set(model_ops):
        c = translate(c, model_ops)
    return c.live()


def translate(c, ops):
    """Rewrite XOR/XNOR/NOT/AND into the allowed ops with small fixed templates."""
    X, XN, A, O, NA, NO, AN, ON, NT = (OPS[k] for k in
                                       ('XOR', 'XNOR', 'AND', 'OR', 'NAND', 'NOR', 'ANDN', 'ORN', 'NOT'))
    gates = []; new = list(range(c.n))

    def g(op, a, b):
        gates.append((op, a, b)); return c.n + len(gates) - 1

    def NOT(a):
        if NT in ops: return g(NT, a, a)
        if NA in ops: return g(NA, a, a)
        if NO in ops: return g(NO, a, a)
        raise ValueError('no way to complement')

    def XOR(a, b):
        if X in ops: return g(X, a, b)
        if XN in ops: return g(XN, a, NOT(b))
        if AN in ops and O in ops: return g(O, g(AN, a, b), g(AN, b, a))
        if A in ops and O in ops and NA in ops: return g(A, g(O, a, b), g(NA, a, b))
        if NA in ops:
            t = g(NA, a, b); return g(NA, g(NA, a, t), g(NA, b, t))
        raise ValueError('no way to build XOR')

    def AND(a, b):
        if A in ops: return g(A, a, b)
        if NA in ops: return NOT(g(NA, a, b))
        if NO in ops: return g(NO, NOT(a), NOT(b))
        raise ValueError('no way to build AND')

    for op, a, b in c.gates:
        a2, b2 = new[a], new[b]
        if op in ops: s = g(op, a2, b2)
        elif op == X: s = XOR(a2, b2)
        elif op == XN: s = NOT(XOR(a2, b2)) if XN not in ops else g(XN, a2, b2)
        elif op == A: s = AND(a2, b2)
        elif op == NT: s = NOT(a2)
        else: raise ValueError('cannot translate op %d' % op)
        new.append(s)
    return Circuit(c.n, c.m, gates, [new[s] for s in c.outputs], c.name)
