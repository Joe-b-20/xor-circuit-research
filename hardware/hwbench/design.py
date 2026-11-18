"""Circuit files -> designs: the gate list, the port order and the reference function.

A *design* is one circuit file of NIST's format (ours under ``circuits/``, NIST's under
``search/nonlinear/seeds/`` and ``hardware/nist/``).  Its Verilog ports are buses ``x`` and ``y``
whose integer values are the function's input and output: for the S-boxes ``x`` is the byte (with
the direction bit as bit 8 for ``aes-sbox-sel``), for linear maps bit j of ``x`` is input x_j.

The reference function is never taken from the circuit: S-boxes come from FIPS-197's definition
(``circuits/boolcirc/truth.py`` computes them from GF(2^8) inversion and the affine map), linear
maps from their matrix files (``circuits/<map>/<map>.mat.txt``).  The file's bit order is the one
under which the circuit equals that function (``truth.match``); exactly one order must match.
"""
from __future__ import annotations

import hashlib
import pathlib
import sys
from dataclasses import dataclass, field

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'circuits'))

from boolcirc import metrics as M, ncff, truth  # noqa: E402

# NIST's linear-map files use other basenames than ours.
MATRIX_FOR = {
    'aes-mixcols': 'aes-mixcolumns',
    'aes-mixcolumns': 'aes-mixcolumns',
    'aes-invmixcols': 'aes-invmixcolumns',
    'aes-invmixcolumns': 'aes-invmixcolumns',
}


@dataclass
class Design:
    path: pathlib.Path
    name: str                     # circuit name in the file
    origin: str                   # 'ours' or 'nist'
    kind: str                     # 'boolean' or 'linear'
    function: str                 # aes-sbox, aes-invsbox, aes-sbox-sel, or the matrix name
    circuit: object               # boolcirc.ncff.Circuit
    in_bit: list                  # file input i  -> bit of x
    out_bit: list                 # file output i -> bit of y
    metrics: dict                 # A, AD, G, GD, XOR, XNOR, NOT
    rows: list = field(default_factory=list)     # linear: y_i = parity(rows[i] & x) ^ consts[i]
    consts: list = field(default_factory=list)
    table: list = field(default_factory=list)    # boolean: y = table[x]
    sha256: str = ''

    @property
    def n_in(self):
        return self.circuit.n_inputs

    @property
    def n_out(self):
        return self.circuit.n_outputs

    @property
    def id(self):
        return '%s--%s' % (self.origin, self.name)

    @property
    def label(self):
        m = self.metrics
        if self.kind == 'linear':
            return '%d@%d' % (m['G'], m['GD'])
        return '%d/%d/%d/%d' % (m['A'], m['AD'], m['G'], m['GD'])

    def value(self, x):
        """The reference output for input x (both as bus integers)."""
        if self.kind == 'boolean':
            return self.table[x]
        y = 0
        for i, (r, c) in enumerate(zip(self.rows, self.consts)):
            y |= ((bin(r & x).count('1') & 1) ^ c) << i
        return y


def read_matrix(path):
    """Rows as int masks (bit j = input x_j) and output constants, as circuits/check.py reads them."""
    tokens = ' '.join(l.split('#')[0].split('%')[0] for l in path.read_text().splitlines()).split()
    rows_n, cols_n = int(tokens[1]), int(tokens[2])
    bits = list(map(int, tokens[3:]))
    if len(bits) not in (rows_n * cols_n, rows_n * cols_n + rows_n):
        raise ValueError('%s: not a %dx%d matrix' % (path, rows_n, cols_n))
    rows = [sum(bits[i * cols_n + j] << j for j in range(cols_n)) for i in range(rows_n)]
    consts = bits[rows_n * cols_n:] or [0] * rows_n
    return rows, consts, cols_n


def _origin(path):
    rel = path.resolve().relative_to(REPO).as_posix()
    if rel.startswith('circuits/'):
        return 'ours'
    if rel.startswith(('search/nonlinear/seeds/', 'hardware/nist/')):
        return 'nist'
    raise ValueError('%s: not a circuit of this repository or of NIST (by its folder)' % rel)


def _boolean_function(name):
    if name.startswith('aes-sbox-sel'):
        return truth.aes_sbox_sel()
    if name.startswith(('aes-invsbox', 'aes-sbox-inv')):
        return truth.aes_inv_sbox()
    if name.startswith('aes-sbox'):
        return truth.aes_sbox()
    return None


def _bits(order, n):
    return list(range(n)) if order == 'lsb' else [n - 1 - i for i in range(n)]


def load(path):
    path = pathlib.Path(path).resolve()
    c = ncff.load(path)
    c.validate()
    m = M.metrics(c)
    if m.other:
        raise ValueError('%s: gates other than AND/XOR/XNOR/NOT: %s' % (path, m.other))
    metrics = {'A': m.and_count, 'AD': m.and_depth, 'G': m.gates, 'GD': m.gate_depth,
               'XOR': m.xor, 'XNOR': m.xnor, 'NOT': m.not_count}
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    fn = _boolean_function(c.name)
    if fn is not None:
        orders = truth.match(c, fn)
        if len(orders) != 1:
            raise ValueError('%s: equals %s under %d bit orders %s (need exactly one)'
                             % (path, fn.name, len(orders), orders))
        (io, oo), = orders
        table = fn.table()
        return Design(path, c.name, _origin(path), 'boolean', fn.name, c,
                      _bits(io, c.n_inputs), _bits(oo, c.n_outputs), metrics, table=table, sha256=sha)
    base = c.name.split('-xor')[0]
    mat = MATRIX_FOR.get(base, base)
    mpath = REPO / 'circuits' / mat / (mat + '.mat.txt')
    if not mpath.exists():
        raise ValueError('%s: no reference function (no S-box name, no %s)' % (path, mpath))
    rows, consts, n = read_matrix(mpath)
    d = Design(path, c.name, _origin(path), 'linear', mat, c, list(range(c.n_inputs)),
               list(range(c.n_outputs)), metrics, rows=rows, consts=consts, sha256=sha)
    if n != c.n_inputs or len(rows) != c.n_outputs:
        raise ValueError('%s: %d x %d circuit, %d x %d matrix' % (path, c.n_outputs, c.n_inputs,
                                                                len(rows), n))
    bad = check_linear(d)
    if bad:
        raise ValueError('%s: %s' % (path, bad))
    return d


def check_linear(d):
    """'' if the circuit computes the matrix (it is affine, so inputs 0 and e_j decide it)."""
    for x in [0] + [1 << j for j in range(d.n_in)]:
        if simulate_int(d, x) != d.value(x):
            return 'differs from the matrix at x = %#x' % x
    if any(g.op == 'AND' for g in d.circuit.gates):
        return 'linear map with AND gates'
    return ''


def simulate_int(d, x):
    """Evaluate the circuit on one bus input (reference evaluator for tests and linear checks)."""
    val = {'0': 0, '1': 1}
    for i, w in enumerate(d.circuit.inputs):
        val[w] = (x >> d.in_bit[i]) & 1
    for g in d.circuit.gates:
        a = [val[v] for v in g.args]
        val[g.out] = {'AND': lambda: a[0] & a[1], 'XOR': lambda: a[0] ^ a[1],
                      'XNOR': lambda: 1 ^ a[0] ^ a[1], 'NOT': lambda: 1 ^ a[0]}[g.op]()
    y = 0
    for i, w in enumerate(d.circuit.outputs):
        y |= val[w] << d.out_bit[i]
    return y
