"""Targets: the GF(2) linear maps being searched, their loaders, catalog and generators.

Role in the method
------------------
A ``Target`` is the fixed problem a campaign works on: ``n_inputs`` and one row mask per output
(bit j of a row = coefficient of input j).  Every record, dossier and DAG hash carries its
``matrix_sha256`` (SHA-256 of the canonical JSON ``{"input_count": n, "rows": [...]}``, the
hash earlier versions used, so hashes match earlier runs).  Targets also list known circuits
(``seeds``) that workers can start from.

Sources, all reached through ``load_target(spec)``:

* map names (``catalog()``): every ``circuits/<name>/<name>.mat.txt`` of the repository (the
  single definition of each map); its seeds are the circuit JSON files in
  ``search/seeds/<name>/``, if any;
* a path to any matrix text file (NIST ``.mat.txt`` or plain 0/1 rows), or to a target JSON
  (the snapshot format ``Target.to_json`` writes into run directories);
* a generator spec: ``"mixcolumns"``-style names, ``"circulant:m=8,poly=0x11b,coeffs=2/3/1/1"``,
  ``"random:n=8,m=8,density=0.4,seed=1"``, ``"sparse:n=16,m=16,weight=3,seed=2"``, or the same
  as a dict ``{"generator": "circulant", "m": 8, ...}``.

Matrix files: NIST format (a line ``1``, a line ``rows cols``, then the rows of 0/1; row i is
output y_i, column j input x_j).  Extension for affine maps: one optional extra line of ``rows``
0/1 values gives output constants c_i (y_i = row_i . x + c_i); the search works on the linear part.

Bit convention for GF(2^m) maps: input bit ``m*j + s`` is bit s (LSB first) of input element j,
output row ``m*i + r`` is bit r of output element i (FIPS-197).
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field, replace
from pathlib import Path

from .circuit import Circuit, matrix_sha256

PACKAGE_ROOT = Path(__file__).resolve().parents[1]          # search/xorflux/
SEARCH_ROOT = PACKAGE_ROOT.parent                             # search/
REPO_ROOT = SEARCH_ROOT.parent                                # the repository root
CIRCUITS_DIR = REPO_ROOT / 'circuits'                         # circuits/<map>/<map>.mat.txt
SEEDS_DIR = SEARCH_ROOT / 'seeds'                             # search/seeds/<map>/*.json
MATRIX_SUFFIX = '.mat.txt'

AES_POLY = 0x11B
AES_MIX = (2, 3, 1, 1)
AES_INVMIX = (0x0E, 0x0B, 0x0D, 0x09)


# --------------------------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Seed:
    """A known circuit for a target: ``path`` (absolute), declared ``gates``/``depth`` (None if
    unknown), a short ``label`` and the catalog entry's other fields in ``info``."""
    path: str
    gates: int | None = None
    depth: int | None = None
    label: str = ''
    info: dict = field(default_factory=dict, compare=False, hash=False)

    def load(self, n_inputs=None):
        """Read the seed as a ``core.circuit.Circuit``."""
        return Circuit.load(self.path, n_inputs)


@dataclass(frozen=True)
class Target:
    """A GF(2) linear map to realise with XOR gates.

    ``name`` is the catalog id (e.g. ``"fox_mu8"``); ``rows[i]`` is the input mask of output i
    (repeats, zero rows and unit rows are allowed); ``matrix_sha256`` the canonical hash;
    ``seeds`` known circuits; ``meta`` everything else from the source (title, affine output
    constants, provenance), excluded from equality and hashing.
    """
    name: str
    n_inputs: int
    rows: tuple
    matrix_sha256: str
    seeds: tuple = ()
    meta: dict = field(default_factory=dict, compare=False, hash=False)

    def __post_init__(self):
        if type(self.n_inputs) is not int or self.n_inputs <= 0:
            raise ValueError('target needs a positive input count')
        if not self.rows:
            raise ValueError('target needs at least one row')
        full = (1 << self.n_inputs) - 1
        if any(type(r) is not int or not 0 <= r <= full for r in self.rows):
            raise ValueError('target row outside its input dimension')
        if self.matrix_sha256 != matrix_sha256(self.n_inputs, self.rows):
            raise ValueError('target matrix hash mismatch')

    @classmethod
    def make(cls, name, n_inputs, rows, seeds=(), meta=None):
        """Build a target and compute its hash."""
        rows = tuple(int(r) for r in rows)
        return cls(name, n_inputs, rows, matrix_sha256(n_inputs, rows), tuple(seeds),
                   dict(meta or {}))

    @property
    def n_outputs(self):
        """Number of output rows."""
        return len(self.rows)

    @property
    def min_depth(self):
        """Depth lower bound of the target (``min_depth(rows)``)."""
        return min_depth(self.rows)

    def to_json(self):
        """Target JSON dict (``id``, ``input_count``, ``rows``, ``matrix_sha256``, meta; seeds
        as absolute paths), the snapshot format ``load_target(path)`` reads back."""
        out = {k: v for k, v in self.meta.items() if k != 'title'}
        out.update({'id': self.name, 'input_count': self.n_inputs,
                    'output_count': self.n_outputs, 'rows': list(self.rows),
                    'matrix_sha256': self.matrix_sha256})
        if 'title' in self.meta:
            out['name'] = self.meta['title']
        out['seeds'] = [dict(s.info, path=s.path, gates=s.gates, depth=s.depth)
                        for s in self.seeds]
        return out


def min_depth(rows) -> int:
    """Smallest depth any circuit can reach: a row of weight w needs ceil(log2 w) levels of
    2-input XORs (0 for zero and unit rows).  The one definition used by the target, the root
    constructors and depth repair."""
    return max(((r.bit_count() - 1).bit_length() for r in rows if r), default=0)


# --------------------------------------------------------------------------------------------
# GF(2^m) generators
# --------------------------------------------------------------------------------------------
def gf_mul(a, b, m=8, poly=AES_POLY):
    """Product in GF(2^m) modulo the irreducible ``poly`` (degree m, top bit included)."""
    result = 0
    top = 1 << (m - 1)
    mask = (1 << m) - 1
    for _ in range(m):
        if b & 1:
            result ^= a
        a = ((a << 1) ^ (poly if a & top else 0)) & mask
        b >>= 1
    return result


def matrix_over_gf(matrix, m=8, poly=AES_POLY):
    """GF(2) rows of a k x l matrix over GF(2^m), in the module's bit convention."""
    k = len(matrix)
    cols = len(matrix[0])
    n = m * cols
    rows = []
    for i in range(k):
        for r in range(m):
            row = 0
            for j in range(cols):
                c = matrix[i][j]
                for s in range(m):
                    if (gf_mul(c, 1 << s, m, poly) >> r) & 1:
                        row |= 1 << (m * j + s)
            rows.append(row)
    return n, rows


def circulant(coeffs, m=8, poly=AES_POLY, name=None, meta=None):
    """Target of the circulant matrix M[i][j] = coeffs[(j - i) mod k] over GF(2^m).

    MixColumns is ``circulant((2, 3, 1, 1))``; InvMixColumns ``circulant((14, 11, 13, 9))``.
    """
    coeffs = tuple(int(c) for c in coeffs)
    k = len(coeffs)
    matrix = [[coeffs[(j - i) % k] for j in range(k)] for i in range(k)]
    n, rows = matrix_over_gf(matrix, m, poly)
    info = {'title': 'circulant(%s) over GF(2^%d) mod %s' % (
                ','.join(map(str, coeffs)), m, hex(poly)),
            'generator': {'generator': 'circulant', 'coeffs': list(coeffs), 'm': m,
                          'poly': poly},
            'input_bit_order': 'x_(%d*j+s): bit s (LSB=0) of element j' % m,
            'output_bit_order': 'y_(%d*i+r): bit r (LSB=0) of element i' % m}
    info.update(meta or {})
    return Target.make(name or 'circulant_m%d_%s' % (m, '_'.join(map(str, coeffs))), n, rows,
                       meta=info)


def mixcolumns():
    """AES MixColumns, one column (32 x 32): 20 rows of weight 5 and 12 of weight 7."""
    return circulant(AES_MIX, 8, AES_POLY, 'mixcolumns',
                     {'title': 'AES MixColumns (one column, FIPS LSB-first)'})


def invmixcolumns():
    """AES InvMixColumns, one column (32 x 32); equals ``circuits/aes-invmixcolumns``."""
    return circulant(AES_INVMIX, 8, AES_POLY, 'invmixcolumns',
                     {'title': 'AES Inverse MixColumns (one column, FIPS LSB-first)'})


# --------------------------------------------------------------------------------------------
# Random generators (tests and calibration)
# --------------------------------------------------------------------------------------------
def random_target(n, m, density=0.5, seed=0, min_weight=2, name=None):
    """m random rows over n inputs, each bit set with probability ``density``; rows are
    redrawn until their weight is at least ``min_weight`` (so the target is not trivial)."""
    rng = random.Random(seed)
    if min_weight > n:
        raise ValueError('min_weight larger than n')
    if min_weight > 0 and density <= 0:
        raise ValueError('density must be positive when min_weight > 0')   # would never end
    rows = []
    for _ in range(m):
        while True:
            row = 0
            for j in range(n):
                if rng.random() < density:
                    row |= 1 << j
            if row.bit_count() >= min_weight:
                break
        rows.append(row)
    return Target.make(name or 'random_n%d_m%d_d%g_s%d' % (n, m, density, seed), n, rows,
                       meta={'generator': {'generator': 'random', 'n': n, 'm': m,
                                           'density': density, 'seed': seed,
                                           'min_weight': min_weight}})


def sparse_target(n, m, weight=3, seed=0, name=None):
    """m random rows of exactly ``weight`` ones over n inputs."""
    if not 1 <= weight <= n:
        raise ValueError('weight must be in 1..n')
    rng = random.Random(seed)
    rows = [sum(1 << j for j in rng.sample(range(n), weight)) for _ in range(m)]
    return Target.make(name or 'sparse_n%d_m%d_w%d_s%d' % (n, m, weight, seed), n, rows,
                       meta={'generator': {'generator': 'sparse', 'n': n, 'm': m,
                                           'weight': weight, 'seed': seed}})




def matrix_over_field(matrix, poly):
    """``(n, rows)`` of a byte (element) matrix over GF(2^m) = GF(2)[x] / ``poly`` (m is the
    degree of ``poly``), in the module's bit convention.  Raises ValueError on a bad entry."""
    poly = int(poly)
    m = poly.bit_length() - 1
    if m < 1:
        raise ValueError('the field polynomial must have degree >= 1, got %s' % hex(poly))
    if not matrix or not matrix[0] or any(len(r) != len(matrix[0]) for r in matrix):
        raise ValueError('the element matrix must be a non-empty rectangle')
    for row in matrix:
        for c in row:
            if not 0 <= c < (1 << m):
                raise ValueError('entry %s does not fit GF(2^%d)' % (hex(c), m))
    return matrix_over_gf(matrix, m, poly)


# --------------------------------------------------------------------------------------------
# Text matrices
# --------------------------------------------------------------------------------------------
def _bits(tokens):
    return all(t in ('0', '1') for t in tokens)


def parse_matrix_text(text, name='matrix'):
    """Target from 0/1 matrix text: NIST ``.mat.txt`` (``1``, ``rows cols``, then the bits,
    optionally followed by one line of ``rows`` output constants) or one row per line
    (``0 1 1 0`` or ``0110``; ``#``/``%`` comments).  Column j of a row is input j (bit j of
    the row mask).  Constants, when present and not all zero, go to
    ``meta['affine_output_constants']``."""
    lines = [ln.split('#')[0].split('%')[0].strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    tokens = ' '.join(lines).split()
    # The NIST header needs positive dimensions: without that check the 1-input plain matrix
    # "1 / 0 / 1" read as an empty 0 x 1 NIST matrix.
    if (len(tokens) >= 3 and tokens[0] == '1' and all(t.isdigit() for t in tokens[1:3])
            and int(tokens[1]) > 0 and int(tokens[2]) > 0):
        m, n = int(tokens[1]), int(tokens[2])
        body = 3 + m * n
        if len(tokens) in (body, body + m) and _bits(tokens[3:]):
            bits = list(map(int, tokens[3:body]))
            rows = [sum(bits[i * n + j] << j for j in range(n)) for i in range(m)]
            meta = {'source_format': 'nist-mat'}
            constants = list(map(int, tokens[body:]))
            if any(constants):
                meta['affine_output_constants'] = constants
            return Target.make(name, n, rows, meta=meta)
    rows = []
    n = None
    for ln in lines:
        cells = ln.split() if ' ' in ln or '\t' in ln else list(ln)
        if any(c not in ('0', '1') for c in cells):
            raise ValueError('matrix text may only contain 0/1 cells: %r' % ln)
        if n is None:
            n = len(cells)
        elif len(cells) != n:
            raise ValueError('ragged matrix rows')
        rows.append(sum(1 << j for j, c in enumerate(cells) if c == '1'))
    if not rows:
        raise ValueError('empty matrix text')
    return Target.make(name, n, rows, meta={'source_format': 'rows'})


def format_matrix_text(n_inputs, rows, constants=None):
    """NIST ``.mat.txt`` text of a map (the inverse of ``parse_matrix_text``); the constants
    line is written only when some constant is 1."""
    lines = ['1', '%d %d' % (len(rows), n_inputs)]
    lines += [' '.join(str((r >> j) & 1) for j in range(n_inputs)) for r in rows]
    if constants is not None:
        constants = [int(c) for c in constants]
        if len(constants) != len(rows) or any(c not in (0, 1) for c in constants):
            raise ValueError('need one 0/1 output constant per row')
        if any(constants):
            lines.append(' '.join(map(str, constants)))
    return '\n'.join(lines) + '\n'


def load_matrix_text(path, name=None):
    """``parse_matrix_text`` of a file; the name defaults to the file name before its first
    dot (``aes-mixcolumns.mat.txt`` -> ``aes-mixcolumns``)."""
    path = Path(path)
    stem = path.name.split('.')[0]
    target = parse_matrix_text(path.read_text(), name or stem)
    target.meta['source_path'] = str(path)
    return target


# --------------------------------------------------------------------------------------------
# Maps (circuits/<name>/<name>.mat.txt), seeds and target JSON
# --------------------------------------------------------------------------------------------
def map_path(name, circuits_dir=None):
    """``circuits/<name>/<name>.mat.txt`` (whether or not it exists)."""
    return Path(circuits_dir or CIRCUITS_DIR) / name / (name + MATRIX_SUFFIX)


def catalog():
    """Sorted map names: every ``circuits/<name>/`` holding ``<name>.mat.txt``."""
    if not CIRCUITS_DIR.is_dir():
        return []
    return sorted(p.name for p in CIRCUITS_DIR.iterdir() if map_path(p.name).is_file())


def map_seeds(name):
    """Seeds of a map: every circuit JSON in ``search/seeds/<name>/``, sorted by file name."""
    folder = SEEDS_DIR / name
    if not folder.is_dir():
        return ()
    seeds = []
    for path in sorted(folder.glob('*.json')):
        data = json.loads(path.read_text())
        info = {k: v for k, v in data.get('provenance', {}).items()
                if isinstance(v, (str, int, bool))}
        seeds.append(Seed(str(path), data.get('gateCount'), data.get('depth'),
                          path.name.split('.')[0], info))
    return tuple(seeds)


def load_map(name):
    """The catalog map ``name`` with its seeds."""
    path = map_path(name)
    if not path.is_file():
        raise ValueError('no map %r (expected %s)' % (name, path))
    target = load_matrix_text(path, name)
    return replace(target, seeds=map_seeds(name))


def _seeds_from(entries, root):
    seeds = []
    for entry in entries or ():
        if isinstance(entry, str):
            entry = {'path': entry}
        path = Path(entry['path'])
        if not path.is_absolute():
            path = root / path
        label = entry.get('label') or path.name.split('.')[0]
        info = {k: v for k, v in entry.items() if k not in ('path', 'gates', 'depth', 'label')}
        seeds.append(Seed(str(path), entry.get('gates'), entry.get('depth'), label, info))
    return tuple(seeds)


def from_json(data, seed_root=None, name=None):
    """Target from a target JSON dict (``Target.to_json`` format), or an entry that gives a
    ``generator`` spec instead of ``rows``.  Relative seed paths resolve against ``seed_root``
    (default: the current directory)."""
    if 'rows' in data:
        n = data['input_count']
        rows = tuple(data['rows'])
        if 'output_count' in data and data['output_count'] != len(rows):
            raise ValueError('target output_count differs from its rows')
        target = Target.make(name or data.get('id', 'custom'), n, rows)
    elif 'generator' in data:
        target = generate(data['generator'])
        if name or data.get('id'):
            target = replace(target, name=name or data['id'])
    else:
        raise ValueError('target JSON needs rows or a generator')
    declared = data.get('matrix_sha256')
    if declared is not None and declared != target.matrix_sha256:
        raise ValueError('target matrix hash mismatch for %s' % target.name)
    meta = dict(target.meta)
    meta.update({k: v for k, v in data.items()
                 if k not in ('id', 'name', 'input_count', 'output_count', 'rows',
                              'matrix_sha256', 'seeds', 'generator')})
    if 'name' in data:
        meta['title'] = data['name']
    return Target(target.name, target.n_inputs, target.rows, target.matrix_sha256,
                  _seeds_from(data.get('seeds'), Path(seed_root or Path.cwd())), meta)


def generators():
    """Generator kinds ``generate`` accepts (``kind`` or ``kind:key=value,...``)."""
    return ('mixcolumns', 'invmixcolumns', 'circulant', 'random', 'sparse')


def load_json(path, name=None):
    """Target from a target JSON file (seed paths relative to the file)."""
    path = Path(path).resolve()
    target = from_json(json.loads(path.read_text()), path.parent, name)
    target.meta['target_path'] = str(path)
    return target


def generate(spec):
    """Target from a generator spec string or dict (see the module docstring)."""
    if isinstance(spec, str):
        kind, _, rest = spec.partition(':')
        params = {}
        for item in filter(None, (p.strip() for p in rest.split(','))):
            key, eq, value = item.partition('=')
            if not eq:
                raise ValueError('generator parameter needs key=value: %r' % item)
            params[key.strip()] = value.strip()
        spec = dict(params, generator=kind.strip())
    spec = dict(spec)
    kind = spec.pop('generator')

    def num(key, default=None, cast=int):
        value = spec.get(key, default)
        if value is None:
            raise ValueError('generator %s needs %s' % (kind, key))
        if isinstance(value, str):
            return cast(int(value, 0)) if cast is int else cast(value)
        return cast(value)

    if kind == 'mixcolumns':
        return mixcolumns()
    if kind == 'invmixcolumns':
        return invmixcolumns()
    if kind == 'circulant':
        coeffs = spec.get('coeffs')
        if isinstance(coeffs, str):
            coeffs = [int(c, 0) for c in coeffs.replace(';', '/').split('/')]
        m = num('m', 8)
        poly = num('poly', AES_POLY if m == 8 else None)
        return circulant(coeffs, m, poly, spec.get('name'))
    if kind == 'random':
        return random_target(num('n'), num('m', spec.get('n')), num('density', 0.5, float),
                             num('seed', 0), num('min_weight', 2), spec.get('name'))
    if kind == 'sparse':
        return sparse_target(num('n'), num('m', spec.get('n')), num('weight', 3),
                             num('seed', 0), spec.get('name'))
    raise ValueError('unknown target generator %r' % kind)


def load_target(spec):
    """Target from a ``Target``, a map name, a matrix-text / target-JSON path, or a generator
    spec (string or dict).  See the module docstring for the forms."""
    if isinstance(spec, Target):
        return spec
    if isinstance(spec, dict):
        # {"generator": "circulant", ...} is a generator spec; a dict whose "generator" is
        # itself a spec dict is a target entry.
        if isinstance(spec.get('generator'), str):
            return generate(spec)
        return from_json(spec)
    spec = str(spec)
    if map_path(spec).is_file():
        return load_map(spec)
    path = Path(spec).expanduser()
    if path.is_file():
        if path.suffix == '.json':
            return load_json(path)
        resolved = path.resolve()
        name = resolved.name.split('.')[0]
        if resolved == map_path(name).resolve():       # a catalog map given by its path
            return load_map(name)
        return load_matrix_text(path)
    if spec.partition(':')[0] in generators():
        return generate(spec)
    raise ValueError('unknown map %r; maps in %s: %s; or a .mat.txt path, or a generator (%s)'
                     % (spec, CIRCUITS_DIR, ', '.join(catalog()) or 'none',
                        ', '.join(generators())))
