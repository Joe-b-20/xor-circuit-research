"""Truth tables: bitsliced evaluation, reference functions and exact equivalence.

A truth table of a Boolean function of n inputs is one int of 2^n bits: bit j is the value at
the input assignment j, where bit i of j is input i.  Gates become word operations on these ints
(XOR ``^``, AND ``&``, NOT ``^ ALL``), so a whole 8-input circuit is evaluated in a few hundred
256-bit operations, and equality of tables is exact Boolean equivalence (complete, not sampled).

A ``Function`` is a target: n inputs and one table per output bit.  ``aes_sbox()`` and
``aes_inv_sbox()`` are computed from FIPS-197's definition (inversion in GF(2^8) modulo
x^8+x^4+x^3+x+1, then the affine map with constant 0x63), not copied from a table, and checked
against the three table entries everyone knows.

Bit conventions.  A circuit file names its inputs in some order (``U0:U7`` or ``x0:x7``) without
saying which is the most significant bit of the byte.  ``match`` tries both orders for inputs
and for outputs and returns the orders under which the circuit equals the function, so the
convention of each file is a verified fact, not an assumption.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .ncff import NONLINEAR

AES_POLY = 0x11B
AES_AFFINE_CONST = 0x63


# --------------------------------------------------------------------------------------------
# Tables
# --------------------------------------------------------------------------------------------
def all_ones(n):
    """The constant-1 table of n inputs."""
    return (1 << (1 << n)) - 1


def input_tables(n):
    """Tables of the n inputs: bit j of table i is bit i of j."""
    tables = []
    size = 1 << n
    for i in range(n):
        half = 1 << i
        period = half << 1
        pattern = ((1 << half) - 1) << half
        reps = size // period
        tables.append(pattern * (((1 << (reps * period)) - 1) // ((1 << period) - 1)))
    return tables


def gate_table(op, args, ones):
    """Table of one gate from its operand tables; ``ones`` is ``all_ones(n)``."""
    if op == 'XOR':
        return args[0] ^ args[1]
    if op == 'XNOR':
        return args[0] ^ args[1] ^ ones
    if op == 'AND':
        return args[0] & args[1]
    if op == 'NAND':
        return (args[0] & args[1]) ^ ones
    if op == 'OR':
        return args[0] | args[1]
    if op == 'NOR':
        return (args[0] | args[1]) ^ ones
    if op == 'NOT':
        return args[0] ^ ones
    raise ValueError('unknown gate ' + op)


def evaluate(circuit, tables=None):
    """Table of every wire of a circuit, ``{name: table}``.

    ``tables`` may give the inputs' tables (default: ``input_tables(n)`` in file order).
    """
    n = circuit.n_inputs
    ones = all_ones(n)
    if tables is None:
        tables = input_tables(n)
    if len(tables) != n:
        raise ValueError('%d input tables for %d inputs' % (len(tables), n))
    val = dict(zip(circuit.inputs, tables))
    val['0'], val['1'] = 0, ones            # literal constant operands
    for g in circuit.gates:
        val[g.out] = gate_table(g.op, [val[a] for a in g.args], ones)
    return val


def truth_tables(circuit):
    """Tables of the circuit's outputs, in file order."""
    val = evaluate(circuit)
    return [val[o] for o in circuit.outputs]


def table_from_values(n, values):
    """Table of a single-bit function given as ``values[j]`` for j in 0..2^n-1."""
    t = 0
    for j, v in enumerate(values):
        if v & 1:
            t |= 1 << j
    return t


def anf(table, n):
    """Algebraic normal form by the Möbius transform: bit m set iff monomial x^m is present."""
    t = table
    for i in range(n):
        half = 1 << i
        period = half << 1
        reps = (1 << n) // period
        low = ((1 << half) - 1) * (((1 << (reps * period)) - 1) // ((1 << period) - 1))
        t ^= (t & low) << half
    return t


def quadratic_matrix(table, n):
    """The alternating matrix of the degree-2 part of a function: row i is the int whose bit j
    is the ANF coefficient of x_i x_j (i != j), as a list of n ints."""
    a = anf(table, n)
    rows = [0] * n
    for i in range(n):
        for j in range(i + 1, n):
            if a >> ((1 << i) | (1 << j)) & 1:
                rows[i] |= 1 << j
                rows[j] |= 1 << i
    return rows


def alt_rank(table, n):
    """Rank of the alternating matrix of the quadratic part (always even); a quadratic function
    of alternating rank 2r is a sum of r products of affine forms plus an affine form, and no
    fewer (the symplectic rank)."""
    return _basis_rank(quadratic_matrix(table, n))


def _basis_rank(vectors):
    from .gf2 import rank
    return rank(vectors)


def degree(table, n):
    """Algebraic degree (-1 for the zero function)."""
    a = anf(table, n)
    best = -1
    while a:
        low = a & -a
        best = max(best, (low.bit_length() - 1).bit_count())
        a ^= low
    return best


# --------------------------------------------------------------------------------------------
# Functions
# --------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Function:
    """A target: ``outputs[r]`` is the table of output bit r (bit r of the value)."""
    name: str
    n_inputs: int
    outputs: tuple
    meta: dict = field(default_factory=dict, compare=False, hash=False)

    @property
    def n_outputs(self):
        return len(self.outputs)

    def value(self, x):
        """Function value at input x (bit r of the result = output r at x)."""
        return sum(((t >> x) & 1) << r for r, t in enumerate(self.outputs))

    def table(self):
        """``[value(x) for x in range(2^n)]``."""
        return [self.value(x) for x in range(1 << self.n_inputs)]

    @classmethod
    def from_table(cls, name, n_inputs, n_outputs, table, **meta):
        """Function from a value table ``table[x]`` of 2^n entries."""
        if len(table) != 1 << n_inputs:
            raise ValueError('table needs %d entries' % (1 << n_inputs))
        outputs = tuple(table_from_values(n_inputs, [(v >> r) & 1 for v in table])
                        for r in range(n_outputs))
        return cls(name, n_inputs, outputs, dict(meta))

    @classmethod
    def from_callable(cls, name, n_inputs, n_outputs, f, **meta):
        return cls.from_table(name, n_inputs, n_outputs, [f(x) for x in range(1 << n_inputs)],
                              **meta)


def gf_mul(a, b, m, poly):
    """Product in GF(2^m) modulo ``poly`` (degree m, top bit set)."""
    r = 0
    top = 1 << (m - 1)
    mask = (1 << m) - 1
    while b:
        if b & 1:
            r ^= a
        a = ((a << 1) ^ (poly if a & top else 0)) & mask
        b >>= 1
    return r


def gf_inv(a, m, poly):
    """Multiplicative inverse in GF(2^m) (0 for 0), by exponentiation to 2^m - 2."""
    if a == 0:
        return 0
    r, e, base = 1, (1 << m) - 2, a
    while e:
        if e & 1:
            r = gf_mul(r, base, m, poly)
        base = gf_mul(base, base, m, poly)
        e >>= 1
    return r


def gf_inverse(m, poly, name=None):
    """The inversion map of GF(2^m) (0 -> 0) as a Function; bit i of an element is x^i."""
    name = name or 'gf%d-inv-%s' % (1 << m, hex(poly))
    return Function.from_callable(name, m, m, lambda x: gf_inv(x, m, poly), field_bits=m,
                                  modulus=poly)


def _aes_affine(v, const=AES_AFFINE_CONST):
    rot = lambda x, k: ((x << k) | (x >> (8 - k))) & 0xFF
    return v ^ rot(v, 1) ^ rot(v, 2) ^ rot(v, 3) ^ rot(v, 4) ^ const


def aes_sbox_table():
    """FIPS-197 S-box values, computed: affine(inverse(x))."""
    return [_aes_affine(gf_inv(x, 8, AES_POLY)) for x in range(256)]


def aes_inv_sbox_table():
    s = aes_sbox_table()
    inv = [0] * 256
    for x, y in enumerate(s):
        inv[y] = x
    return inv


def aes_sbox():
    """The AES S-box (FIPS-197) as a Function; bit i of the byte is input/output i."""
    return Function.from_table('aes-sbox', 8, 8, aes_sbox_table(), reference='FIPS-197 5.1.1')


def aes_inv_sbox():
    return Function.from_table('aes-invsbox', 8, 8, aes_inv_sbox_table(),
                               reference='FIPS-197 5.3.2')


_s = aes_sbox_table()
assert _s[0x00] == 0x63 and _s[0x01] == 0x7C and _s[0x53] == 0xED and _s[0xFF] == 0x16
assert sorted(_s) == list(range(256))
del _s


# --------------------------------------------------------------------------------------------
# Equivalence
# --------------------------------------------------------------------------------------------
ORDERS = ('lsb', 'msb')


def _reorder(tables, order):
    """Function-bit order of file-order tables: 'lsb' = file index i is bit i; 'msb' = bit n-1-i."""
    return list(tables) if order == 'lsb' else list(reversed(tables))


def equivalent(circuit, function, in_order='lsb', out_order='lsb'):
    """True iff the circuit computes ``function`` under the given bit orders.

    ``in_order`` says which function input bit each file input is (``'lsb'``: file input i is
    bit i; ``'msb'``: file input i is bit n-1-i), ``out_order`` the same for the outputs.
    """
    if circuit.n_inputs != function.n_inputs or circuit.n_outputs != function.n_outputs:
        return False
    n = circuit.n_inputs
    base = input_tables(n)
    got = evaluate(circuit, _reorder(base, in_order))
    tables = [got[o] for o in circuit.outputs]
    return _reorder(tables, out_order) == list(function.outputs)


def match(circuit, function):
    """All ``(in_order, out_order)`` pairs under which the circuit equals the function."""
    return [(i, o) for i in ORDERS for o in ORDERS if equivalent(circuit, function, i, o)]


def match_evaluator(evaluator, n_inputs, function):
    """``match`` for any evaluator: ``evaluator(input_tables)`` must return the output tables
    (file order) for the given input tables (file order).  Returns the ``(in_order,
    out_order)`` pairs under which it equals the function."""
    if n_inputs != function.n_inputs:
        return []
    base = input_tables(n_inputs)
    found = []
    for i in ORDERS:
        tables = evaluator(_reorder(base, i))
        if len(tables) != function.n_outputs:
            return []
        for o in ORDERS:
            if _reorder(tables, o) == list(function.outputs):
                found.append((i, o))
    return found


def match_tables(tables, function):
    """``match`` for output tables already computed in the lsb input order: the output orders
    (``'lsb'``/``'msb'``) under which they equal the function's."""
    return [o for o in ORDERS if _reorder(tables, o) == list(function.outputs)]


def first_mismatch(circuit, function, in_order='lsb', out_order='lsb'):
    """``(x, expected, got)`` of the first input where the circuit disagrees, or None."""
    n = circuit.n_inputs
    got = evaluate(circuit, _reorder(input_tables(n), in_order))
    tables = _reorder([got[o] for o in circuit.outputs], out_order)
    for x in range(1 << n):
        want = function.value(x)
        have = sum(((t >> x) & 1) << r for r, t in enumerate(tables))
        if want != have:
            return x, want, have
    return None


def nonlinear_count(circuit):
    """Gates of the nonlinear family (AND, NAND, OR, NOR)."""
    return sum(g.op in NONLINEAR for g in circuit.gates)
