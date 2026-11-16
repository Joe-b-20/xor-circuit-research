"""The AND skeleton of a circuit: every signal as an affine form over inputs and AND outputs.

Because XOR, XNOR and NOT are affine, every wire of a circuit over {XOR, XNOR, AND, NOT} is an
affine function of the inputs x_0..x_{n-1} and of the outputs a_1..a_k of its AND gates.
Writing each wire as ``(mask, const)`` over the basis ``x_0..x_{n-1}, a_1..a_k`` (bit i of the
mask is basis element i, ``const`` is the XNOR/NOT bit) gives the *skeleton*:

    AND i:   a_i = L_i(x, a_<i) . R_i(x, a_<i)       (two affine forms over earlier basis bits)
    output:  y_r = O_r(x, a)                           (an affine form)

Convention for the other nonlinear gates (fixed here, because the skeleton depends on it): a
gate g(u, v) with g in {AND, NAND, OR, NOR} contributes the AND ``a_i = u . v`` of its
*uncorrected* operands, and its wire is ``a_i + c_g`` with ``c_AND = 0``, ``c_NAND = 1``,
``c_OR = u + v``, ``c_NOR = u + v + 1`` (the correction is on the output; NAND and OR cannot be
written as a product of affine forms at all, so an operand-side convention does not exist).
With the gate order and operand order of the source circuit the skeleton is unique.

The skeleton fixes the function of the circuit and does not depend on how the XORs were
arranged; XOR trees, sharing and gate order are not in it.  What is left for an XOR search
is the *linear sub-problem*: realise the forms L_i, R_i, O_r from the basis signals, where
each a_i only exists once L_i and R_i do (its *arrival*), and where a gate-depth target gives
every form a *deadline*.  ``linear_problem`` writes that sub-problem out; ``matrix_text`` writes
the forms as one matrix in this repository's ``.mat.txt`` format (with constants), which the
linear search can read as a map with no ordering constraint (a relaxation).

``tables`` evaluates a skeleton directly (AND outputs as new variables, forms as XORs of
tables), independently of the gate list it came from, so a circuit can be checked twice: by
its gates (``truth.evaluate``) and by its skeleton.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .gf2 import Basis
from .ncff import Circuit, Gate
from .truth import all_ones, degree, input_tables


def form_table(form, basis, ones):
    """Truth table of a form from the tables of the basis signals (``ones`` = all_ones(n))."""
    t = ones if form.const else 0
    m = form.mask
    while m:
        low = m & -m
        t ^= basis[low.bit_length() - 1]
        m ^= low
    return t


@dataclass(frozen=True)
class Form:
    """An affine form: XOR of the basis signals in ``mask``, plus ``const``."""
    mask: int
    const: int

    def __xor__(self, other):
        return Form(self.mask ^ other.mask, self.const ^ other.const)

    def flipped(self):
        return Form(self.mask, self.const ^ 1)

    @property
    def weight(self):
        return self.mask.bit_count()


@dataclass
class Skeleton:
    """Skeleton of a circuit over basis ``x_0..x_{n-1}, a_1..a_k`` (see the module docstring).

    ``ands[i] = (L_i, R_i)``; AND i's output is basis bit ``n_inputs + i``.
    ``outputs[r]`` is the form of output r.  ``and_names`` are the wires of the AND outputs,
    ``and_depth`` the gate depth at which each AND fires in the source circuit (its output's
    depth) and ``and_level`` its AND depth; ``forms`` maps every wire to its form.
    """
    n_inputs: int
    ands: list
    outputs: list
    input_names: list = field(default_factory=list)
    output_names: list = field(default_factory=list)
    and_names: list = field(default_factory=list)
    and_depth: list = field(default_factory=list)
    and_level: list = field(default_factory=list)
    forms: dict = field(default_factory=dict)
    name: str = ''
    output_depth: list = field(default_factory=list)

    @property
    def n_ands(self):
        return len(self.ands)

    @property
    def n_basis(self):
        return self.n_inputs + len(self.ands)

    def basis_name(self, bit):
        if bit < self.n_inputs:
            return self.input_names[bit] if self.input_names else 'x%d' % bit
        i = bit - self.n_inputs
        return self.and_names[i] if self.and_names else 'a%d' % (i + 1)

    def describe(self, form):
        """Readable text of a form, e.g. ``x0 + a3 + 1``."""
        terms = [self.basis_name(b) for b in range(self.n_basis) if form.mask >> b & 1]
        if form.const:
            terms.append('1')
        return ' + '.join(terms) if terms else '0'

    def targets(self):
        """Every form the linear sub-problem must realise, in order: ``(kind, index, form)``
        with kind ``'L'``/``'R'`` (AND i's operands) or ``'Y'`` (output r)."""
        out = []
        for i, (l, r) in enumerate(self.ands):
            out.append(('L', i, l))
            out.append(('R', i, r))
        for r, f in enumerate(self.outputs):
            out.append(('Y', r, f))
        return out

    def degenerate(self):
        """ANDs whose product is affine in earlier signals: an operand constant, both operands
        equal, or operands differing by a constant (``a . (a+1) = 0``)."""
        bad = []
        for i, (l, r) in enumerate(self.ands):
            if l.mask == 0 or r.mask == 0:
                bad.append((i, 'constant operand'))
            elif l.mask == r.mask:
                bad.append((i, 'equal operands' if l.const == r.const else 'complementary operands'))
        return bad

    def distinct_target_masks(self):
        """Distinct masks of weight >= 2 among the targets: each needs at least one XOR/XNOR gate
        of its own, so their number is a lower bound on #XOR + #XNOR for this skeleton."""
        return {f.mask for _, _, f in self.targets() if f.weight >= 2}

    def basis_tables(self, inputs=None):
        """Truth tables of the basis signals ``x_0..x_{n-1}, a_1..a_k`` computed from the
        skeleton alone (default inputs: ``input_tables(n)``, file input i = bit i)."""
        n = self.n_inputs
        ones = all_ones(n)
        basis = list(inputs if inputs is not None else input_tables(n))
        for l, r in self.ands:
            basis.append(form_table(l, basis, ones) & form_table(r, basis, ones))
        return basis

    def tables(self, inputs=None):
        """Output truth tables computed from the skeleton alone, from the given input tables
        (default ``input_tables(n)``: file input i is bit i of the assignment)."""
        basis = self.basis_tables(inputs)
        ones = all_ones(self.n_inputs)
        return [form_table(f, basis, ones) for f in self.outputs]

    def redundant(self):
        """ANDs whose output is an affine function of the earlier basis signals (as functions),
        i.e. ``a_i`` in ``W_{i-1} = span(1, x, a_1..a_{i-1})``; a skeleton with none is
        *nonredundant*: its forms are then in bijection with the functions they evaluate to."""
        n = self.n_inputs
        basis = self.basis_tables()
        space = Basis([all_ones(n)] + basis[:n])
        bad = []
        for i in range(self.n_ands):
            if not space.add(basis[n + i]):
                bad.append(i)
        return bad

    def degrees(self):
        """Algebraic degree of every AND output."""
        n = self.n_inputs
        return [degree(t, n) for t in self.basis_tables()[n:]]

    def and_levels_from_masks(self):
        """AND level of every AND from the forms alone (1 + the highest level among the AND
        bits of its operands): what ``and_level`` must be after a skeleton is edited."""
        n = self.n_inputs
        levels = []
        for l, r in self.ands:
            m = (l.mask | r.mask) >> n
            top = 0
            while m:
                low = m & -m
                top = max(top, levels[low.bit_length() - 1])
                m ^= low
            levels.append(top + 1)
        return levels

    def with_and(self, i, left, right):
        """A copy with AND i's operands replaced by the forms ``left``, ``right`` (over basis bits
        below ``n_inputs + i``); levels recomputed, depths dropped (they belong to a circuit).
        Whether the copy still computes the same function is for ``tables`` to decide."""
        limit = 1 << (self.n_inputs + i)
        if left.mask >= limit or right.mask >= limit:
            raise ValueError('operands of AND %d may only use earlier basis signals' % i)
        ands = list(self.ands)
        ands[i] = (left, right)
        s = Skeleton(self.n_inputs, ands, list(self.outputs), list(self.input_names),
                     list(self.output_names), list(self.and_names), [], [], {}, self.name, [])
        s.and_level = s.and_levels_from_masks()
        return s

    def linear_problem(self, gate_depth=None):
        """The linear sub-problem as a dict: ``n_inputs``, ``n_ands``, ``rows`` (masks),
        ``consts``, ``kinds`` (``[kind, index]`` per row), ``arrival`` (level of every basis
        signal: 0 for inputs, the AND's depth in the source circuit for AND outputs) and
        ``deadline`` per row (an AND operand: the AND's depth - 1; an output: ``gate_depth``,
        default the source circuit's)."""
        if gate_depth is None:
            gate_depth = max(self.output_depth) if self.output_depth else None
        rows, consts, kinds, deadline = [], [], [], []
        for kind, i, f in self.targets():
            rows.append(f.mask)
            consts.append(f.const)
            kinds.append([kind, i])
            if kind in ('L', 'R'):
                deadline.append(self.and_depth[i] - 1 if self.and_depth else None)
            else:
                deadline.append(gate_depth)
        arrival = [0] * self.n_inputs + list(self.and_depth)
        return {'name': self.name, 'n_inputs': self.n_inputs, 'n_ands': self.n_ands,
                'n_basis': self.n_basis, 'rows': rows, 'consts': consts, 'kinds': kinds,
                'arrival': arrival, 'deadline': deadline}

    def matrix_text(self):
        """The target forms as one matrix in ``circuits/*.mat.txt`` format (``1``, ``rows cols``,
        0/1 rows, then the constants line), columns = basis signals, rows = targets."""
        tg = self.targets()
        lines = ['1', '%d %d' % (len(tg), self.n_basis)]
        for _, _, f in tg:
            lines.append(' '.join('1' if f.mask >> b & 1 else '0' for b in range(self.n_basis)))
        lines.append(' '.join(str(f.const) for _, _, f in tg))
        return '\n'.join(lines) + '\n'


def skeleton(circuit):
    """Skeleton of a validated circuit (gate depths are recomputed here)."""
    n = circuit.n_inputs
    forms = {w: Form(1 << i, 0) for i, w in enumerate(circuit.inputs)}
    forms['0'], forms['1'] = Form(0, 0), Form(0, 1)          # literal constant operands
    depth = {w: 0 for w in circuit.inputs + ['0', '1']}
    adepth = dict(depth)
    ands, names, and_depth, and_level = [], [], [], []
    for g in circuit.gates:
        a = [forms[x] for x in g.args]
        d = 1 + max(depth[x] for x in g.args)
        ad = max(adepth[x] for x in g.args)
        if g.op == 'XOR':
            f = a[0] ^ a[1]
        elif g.op == 'XNOR':
            f = (a[0] ^ a[1]).flipped()
        elif g.op == 'NOT':
            f = a[0].flipped()
        else:
            bit = 1 << (n + len(ands))
            ands.append((a[0], a[1]))
            names.append(g.out)
            and_depth.append(d)
            ad += 1
            and_level.append(ad)
            f = Form(bit, 0)
            if g.op == 'NAND':
                f = f.flipped()
            elif g.op in ('OR', 'NOR'):
                f = Form(bit ^ a[0].mask ^ a[1].mask, a[0].const ^ a[1].const ^ (g.op == 'NOR'))
        forms[g.out] = f
        depth[g.out] = d
        adepth[g.out] = ad
    return Skeleton(n, ands, [forms[o] for o in circuit.outputs], list(circuit.inputs),
                    list(circuit.outputs), names, and_depth, and_level, forms, circuit.name,
                    [depth[o] for o in circuit.outputs])


def circuit_from_skeleton(skel, name=None, order=None, not_style='xnor0'):
    """A circuit that realises a skeleton with one XOR chain per form (a correct but
    unoptimised realisation: the starting point an XOR search would improve).

    Forms are built in ``order`` (default: AND operands in AND order, then outputs) from the
    basis signals; a form of weight 1 reuses the basis wire (plus a complement when its constant
    is set, written NIST's way as ``XNOR t u 0`` so that it counts in X, or as a ``NOT`` gate
    with ``not_style='not'``); the constant of a larger form is folded into its last gate as
    an XNOR.
    """
    n = skel.n_inputs
    inputs = list(skel.input_names) or ['x%d' % i for i in range(n)]
    gates = []
    wire_of_bit = {i: inputs[i] for i in range(n)}
    out_names = list(skel.output_names) or ['y%d' % r for r in range(len(skel.outputs))]
    taken = set(inputs) | set(skel.and_names) | set(out_names)
    counter = [0]

    def fresh(prefix='t'):
        while True:
            counter[0] += 1
            name = '%s%d' % (prefix, counter[0])
            if name not in taken:
                taken.add(name)
                return name

    def build(form, out_name=None):
        bits = [b for b in range(skel.n_basis) if form.mask >> b & 1]
        if not bits:                           # a constant: a literal operand, or x ^ x for an output
            if out_name is None:
                return '1' if form.const else '0'
            w = fresh('y_') if out_name in assigned else out_name
            gates.append(Gate('XNOR' if form.const else 'XOR', w, (inputs[0], inputs[0])))
            assigned.add(w)
            return w
        if len(bits) == 1 and not form.const:
            return wire_of_bit[bits[0]]        # a bare basis signal (an output may be one)
        if out_name is not None and out_name in assigned:
            out_name = fresh('y_')             # the name already belongs to an AND wire
        if len(bits) == 1:
            w = out_name or fresh()
            if not_style == 'not':
                gates.append(Gate('NOT', w, (wire_of_bit[bits[0]],)))
            else:
                gates.append(Gate('XNOR', w, (wire_of_bit[bits[0]], '0')))
            assigned.add(w)
            return w
        acc = wire_of_bit[bits[0]]
        for k, b in enumerate(bits[1:], 1):
            last = k == len(bits) - 1
            w = (out_name or fresh()) if last else fresh()
            op = 'XNOR' if last and form.const else 'XOR'
            gates.append(Gate(op, w, (acc, wire_of_bit[b])))
            assigned.add(w)
            acc = w
        return acc

    assigned = set(inputs)
    for i, (l, r) in enumerate(skel.ands):
        lw = build(l)
        rw = build(r)
        aw = skel.and_names[i] if skel.and_names else 'a%d' % (i + 1)
        gates.append(Gate('AND', aw, (lw, rw)))
        assigned.add(aw)
        wire_of_bit[n + i] = aw
    outputs = []
    for r, f in enumerate(skel.outputs):
        outputs.append(build(f, out_names[r]))
    c = Circuit(name or (skel.name + '-from-skeleton'), inputs, outputs, gates)
    return c.validate()
