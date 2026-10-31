"""Reading and writing circuit files: NIST's NCFF (2026) and its 2020 ``.slp`` format.

Both formats are straight-line programs over named wires::

    begin circuit NAME
    Inputs: U0:U7            (ranges expand: U0:U7 = U0 U1 ... U7)
    Outputs: S0:S7
    Internal: a1:a32 t1:t70  (optional)
    GateSyntax: GateName Output Inputs
    begin SLP
    XOR t1 U0 U6
    AND a1 t7 t3
    XNOR S7 t63 t64
    end SLP
    end circuit

Comments start with ``%`` (NCFF) or ``#`` (2020), anywhere on a line.  A file may hold several
circuits.  Every gate keeps its own semantics: ``XOR``, ``XNOR``, ``AND``, ``NAND``, ``OR``,
``NOR`` take two operands, ``NOT`` one; an operand may be the literal constant ``0`` or ``1``
(NIST writes a NOT as ``XNOR t U 0``).  Nothing is rewritten on input: an XNOR stays an XNOR, a
NOT stays a NOT, so a parsed circuit, re-serialised, lists the same gates in the same order.

A parsed program is checked to be a valid straight-line program: inputs distinct, every wire
assigned once, every operand assigned before use, every output assigned.  What it computes is
``truth.evaluate``'s business; what it costs is ``metrics.metrics``'s.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

ARITY = {'XOR': 2, 'XNOR': 2, 'AND': 2, 'NAND': 2, 'OR': 2, 'NOR': 2, 'NOT': 1}
LINEAR = frozenset({'XOR', 'XNOR', 'NOT'})          # affine in their operands
NONLINEAR = frozenset({'AND', 'NAND', 'OR', 'NOR'})  # one AND's worth of nonlinearity each
CONSTANTS = ('0', '1')   # NIST writes a NOT as ``XNOR t U 0``: literal operands are allowed

_RANGE = re.compile(r'^([A-Za-z_][A-Za-z_0-9]*?)(\d+):([A-Za-z_][A-Za-z_0-9]*?)(\d+)$')


class FormatError(ValueError):
    """A circuit file that cannot be read as a straight-line program."""


@dataclass(frozen=True)
class Gate:
    """One instruction: ``out = op(args)``."""
    op: str
    out: str
    args: tuple

    def line(self):
        """The instruction as written in a file."""
        return ' '.join((self.op, self.out) + tuple(self.args))


@dataclass
class Circuit:
    """A named straight-line program over wires.

    ``inputs`` and ``outputs`` are wire names in file order (an output may also be an input
    wire, or the same wire twice).  ``internal`` is the declared ``Internal:`` list, or None.
    ``comments`` keeps the ``%``/``#`` lines met before ``begin SLP`` (the header), verbatim
    without their marker, so provenance notes survive a round trip; ``source`` names the file.
    """
    name: str
    inputs: list
    outputs: list
    gates: list
    internal: list | None = None
    comments: list = field(default_factory=list)
    source: str = ''

    @property
    def n_inputs(self):
        return len(self.inputs)

    @property
    def n_outputs(self):
        return len(self.outputs)

    def wires(self):
        """Every wire name in definition order: inputs, then gate outputs."""
        return list(self.inputs) + [g.out for g in self.gates]

    def validate(self):
        """Raise FormatError unless this is a valid straight-line program."""
        if not self.inputs:
            raise FormatError('%s: no inputs' % self.name)
        if len(set(self.inputs)) != len(self.inputs):
            raise FormatError('%s: repeated input name' % self.name)
        defined = set(self.inputs) | set(CONSTANTS)
        if any(w.isdigit() for w in self.inputs):
            raise FormatError('%s: an input is named like a constant' % self.name)
        for i, g in enumerate(self.gates):
            if g.out.isdigit():
                raise FormatError('%s: gate %d assigns a constant name %s'
                                  % (self.name, i + 1, g.out))
            if g.op not in ARITY:
                raise FormatError('%s: gate %d: unknown gate %s' % (self.name, i + 1, g.op))
            if len(g.args) != ARITY[g.op]:
                raise FormatError('%s: gate %d: %s takes %d operand(s)'
                                  % (self.name, i + 1, g.op, ARITY[g.op]))
            for a in g.args:
                if a not in defined:
                    raise FormatError('%s: gate %d reads %s before it is defined'
                                      % (self.name, i + 1, a))
            if g.out in defined:
                raise FormatError('%s: gate %d assigns %s twice' % (self.name, i + 1, g.out))
            defined.add(g.out)
        for o in self.outputs:
            if o not in defined or o in CONSTANTS:
                raise FormatError('%s: output %s is never assigned' % (self.name, o))
        return self


def expand_names(spec):
    """``'U0:U7 S3 t1:t3'`` -> ``['U0', ..., 'U7', 'S3', 't1', 't2', 't3']``."""
    names = []
    for token in spec.split():
        m = _RANGE.match(token)
        if m and m.group(1) == m.group(3):
            lo, hi = int(m.group(2)), int(m.group(4))
            if hi < lo:
                raise FormatError('descending range ' + token)
            width = len(m.group(2)) if m.group(2).startswith('0') and len(m.group(2)) > 1 else 0
            names += [m.group(1) + str(i).zfill(width) for i in range(lo, hi + 1)]
        elif ':' in token:
            raise FormatError('bad name range ' + token)
        else:
            names.append(token)
    return names


def _strip(line):
    """Drop the comment (from the first ``%`` or ``#``); return (code, comment-or-None)."""
    positions = [p for p in (line.find('%'), line.find('#')) if p >= 0]
    if not positions:
        return line.strip(), None
    pos = min(positions)
    return line[:pos].strip(), line[pos + 1:].strip()


def parse(text, source=''):
    """Every circuit in ``text`` (NCFF or 2020 SLP), validated, in file order."""
    circuits = []
    cur = None
    in_slp = False
    header_comments = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        code, comment = _strip(raw)
        if comment and not in_slp and not comment.startswith('NCFF-'):   # not the magic line
            (header_comments if cur is None else cur.comments).append(comment)
        if not code:
            continue
        low = code.lower()
        if low.startswith('begin circuit'):
            if cur is not None:
                raise FormatError('%s:%d: nested begin circuit' % (source, lineno))
            cur = Circuit(code[len('begin circuit'):].strip(), [], [], [], None, [], source)
            cur.comments = header_comments        # file comments before it, then its own
            header_comments = []
            continue
        if low.startswith('end circuit'):
            if cur is None:
                raise FormatError('%s:%d: end circuit without begin' % (source, lineno))
            if in_slp:
                raise FormatError('%s:%d: end circuit inside an SLP (missing end SLP)'
                                  % (source, lineno))
            circuits.append(cur.validate())
            cur = None
            continue
        if cur is None:
            if low.startswith('begin') or low.startswith('end'):
                raise FormatError('%s:%d: %r outside a circuit' % (source, lineno, code))
            continue                                        # file-level text (none expected)
        if low == 'begin slp':
            in_slp = True
            continue
        if low == 'end slp':
            in_slp = False
            continue
        if not in_slp:
            key, sep, rest = code.partition(':')
            if not sep:
                raise FormatError('%s:%d: unexpected header line %r' % (source, lineno, code))
            key = key.strip().lower()
            if key == 'inputs':
                cur.inputs = expand_names(rest)
            elif key == 'outputs':
                cur.outputs = expand_names(rest)
            elif key == 'internal':
                cur.internal = expand_names(rest)
            elif key == 'gatesyntax':
                if rest.split() != ['GateName', 'Output', 'Inputs']:
                    raise FormatError('%s:%d: unsupported GateSyntax %r' % (source, lineno, rest))
            else:
                raise FormatError('%s:%d: unknown header %r' % (source, lineno, key))
            continue
        parts = code.split()
        op = parts[0].upper()
        if op not in ARITY:
            raise FormatError('%s:%d: unknown gate %s' % (source, lineno, parts[0]))
        if len(parts) != 2 + ARITY[op]:
            raise FormatError('%s:%d: %s needs %d operand(s): %r'
                              % (source, lineno, op, ARITY[op], code))
        cur.gates.append(Gate(op, parts[1], tuple(parts[2:])))
    if cur is not None:
        raise FormatError('%s: missing end circuit' % source)
    if not circuits:
        raise FormatError('%s: no circuit found' % source)
    return circuits


def parse_file(path):
    """Every circuit of a file (``parse`` with the file name as source)."""
    path = Path(path)
    return parse(path.read_text(encoding='utf-8'), str(path))


def load(path):
    """The one circuit of a file; FormatError if the file holds several."""
    found = parse_file(path)
    if len(found) != 1:
        raise FormatError('%s holds %d circuits' % (path, len(found)))
    return found[0]


def format_circuit(circuit, comments=(), levels=None, style='ncff'):
    """Circuit text in NCFF style (``%`` comments) or 2020 style (``#`` comments).

    ``comments`` are header lines written before ``begin circuit``; ``levels`` (optional) maps a
    gate index to a label written as a comment line before that gate (NIST writes gate-level
    separators this way).  The gate list is written exactly as held: same gates, same order.
    """
    mark = '%' if style == 'ncff' else '#'
    out = []
    if style == 'ncff':
        out.append('%NCFF-0.1-2026 (NIST Circuit File Format)')
    for c in comments:
        out.append('%s %s' % (mark, c))
    out.append('')
    out.append('begin circuit ' + circuit.name)
    out.append('')
    out.append('Inputs: ' + _compact(circuit.inputs))
    out.append('Outputs: ' + _compact(circuit.outputs))
    internal = circuit.internal
    if internal is None:
        seen = set(circuit.inputs) | set(circuit.outputs)
        internal = [g.out for g in circuit.gates if g.out not in seen]
    if internal:
        out.append('Internal: ' + _compact(internal))
    out.append('GateSyntax: GateName Output Inputs')
    out.append('')
    out.append('begin SLP')
    for i, g in enumerate(circuit.gates):
        if levels and i in levels:
            out.append('%s%s %s' % (mark, mark * 23, levels[i]))
        out.append(g.line())
    out.append('end SLP')
    out.append('end circuit')
    return '\n'.join(out) + '\n'


def _compact(names):
    """Collapse runs of consecutive numbered names into ranges (the inverse of expand_names)."""
    out = []
    i = 0
    while i < len(names):
        m = re.match(r'^([A-Za-z_][A-Za-z_0-9]*?)(\d+)$', names[i])     # what expand_names reads back
        j = i
        if m and not (m.group(2).startswith('0') and len(m.group(2)) > 1):
            prefix, k = m.group(1), int(m.group(2))
            while j + 1 < len(names) and names[j + 1] == prefix + str(k + (j + 1 - i)):
                j += 1
        if j > i:
            out.append('%s:%s' % (names[i], names[j]))
        else:
            out.append(names[i])
        i = j + 1
    return ' '.join(out)
