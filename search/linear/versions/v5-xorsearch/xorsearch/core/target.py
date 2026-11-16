"""Targets: the GF(2) linear maps being searched, their loaders, catalog and generators.

Role in the method
------------------
A ``Target`` is the fixed problem a campaign works on: ``n_inputs`` and one row mask per output
(bit j of a row = coefficient of input j).  Every record, dossier and DAG hash carries its
``matrix_sha256``, computed exactly as ``search/target.py`` does so hashes match earlier runs.
Targets also list known circuits (``seeds``) that workers can start from.

Sources, all reached through ``load_target(spec)``:

* catalog names (``catalog()``): the JSON targets under ``search/targets/`` (joltik, fox_mu4,
  fox_mu8, invmixcolumns, aes_sbox_bottom; their seed paths are relative to ``search/``) and the
  entries under ``xorsearch/targets/`` (e.g. mixcolumns, generated on the fly from GF(2^8)
  arithmetic, seeds relative to the repository root);
* a path to a target JSON in that format, or to a 0/1 matrix text file (NIST ``.mat.txt``
  or plain rows);
* a generator spec: ``"mixcolumns"``-style names, ``"circulant:m=8,poly=0x11b,coeffs=2/3/1/1"``,
  ``"random:n=8,m=8,density=0.4,seed=1"``, ``"sparse:n=16,m=16,weight=3,seed=2"``, or the same
  as a dict ``{"generator": "circulant", "m": 8, ...}``.

Bit convention for generated GF(2^m) maps: input bit ``m*j + s`` is bit s (LSB first) of input
element j, output row ``m*i + r`` is bit r of output element i (FIPS-197, as
``search/targets/import_invmixcolumns.py``).
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field, replace
from pathlib import Path

from .circuit import Circuit, matrix_sha256

PACKAGE_ROOT = Path(__file__).resolve().parents[1]          # xorsearch/
REPO_ROOT = PACKAGE_ROOT.parent
SEARCH_ROOT = REPO_ROOT / 'search'                            # seed paths of search/targets
SEARCH_TARGETS = SEARCH_ROOT / 'targets'
CATALOG_DIR = PACKAGE_ROOT / 'targets'                        # xorsearch catalog entries

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
    def weights(self):
        """Popcount of every row."""
        return tuple(r.bit_count() for r in self.rows)

    @property
    def min_depth(self):
        """Depth lower bound: a row of weight w needs ceil(log2 w) levels of 2-input XORs."""
        return max(((w - 1).bit_length() if w > 1 else 0) for w in self.weights)

    @property
    def min_gates(self):
        """Gate lower bound: each distinct row of weight >= 2 is a different gate output."""
        return len({r for r in self.rows if r.bit_count() >= 2})

    @property
    def free_outputs(self):
        """Rows needing no gate: zero rows and unit vectors (wired from an input)."""
        return sum(1 for r in self.rows if r.bit_count() <= 1)

    def with_seeds(self, seeds):
        """Copy of this target with a different seed tuple."""
        return replace(self, seeds=tuple(seeds))

    def seed(self, which=0):
        """Seed by index or label."""
        if isinstance(which, int):
            return self.seeds[which]
        for s in self.seeds:
            if s.label == which:
                return s
        raise KeyError('no seed %r for %s' % (which, self.name))

    def load_seed(self, which=0):
        """Circuit of a seed (by index or label)."""
        return self.seed(which).load(self.n_inputs)

    def to_json(self):
        """Dict in the ``search/targets/*.json`` format (seeds as absolute paths)."""
        out = {k: v for k, v in self.meta.items() if k != 'title'}
        out.update({'id': self.name, 'input_count': self.n_inputs,
                    'output_count': self.n_outputs, 'rows': list(self.rows),
                    'matrix_sha256': self.matrix_sha256})
        if 'title' in self.meta:
            out['name'] = self.meta['title']
        out['seeds'] = [dict(s.info, path=s.path, gates=s.gates, depth=s.depth)
                        for s in self.seeds]
        return out

    def describe(self):
        """One-line summary."""
        w = self.weights
        return ('%s: %d inputs, %d outputs, row weights %d..%d (total %d), min depth %d, '
                '%d seeds' % (self.name, self.n_inputs, self.n_outputs, min(w), max(w), sum(w),
                              self.min_depth, len(self.seeds)))


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
    """AES InvMixColumns, one column (32 x 32); equals ``search/targets/invmixcolumns.json``."""
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


# --------------------------------------------------------------------------------------------
# Text matrices
# --------------------------------------------------------------------------------------------
def parse_matrix_text(text, name='matrix'):
    """Target from 0/1 matrix text: NIST ``.mat.txt`` (``1``, ``rows cols``, then the bits) or
    one row per line (``0 1 1 0`` or ``0110``; ``#``/``%`` comments).  Column j of a row is
    input j (bit j of the row mask), as ``search/targets/import_nist.py``."""
    lines = [ln.split('#')[0].split('%')[0].strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    tokens = ' '.join(lines).split()
    if (len(tokens) >= 3 and tokens[0] == '1' and all(t.isdigit() for t in tokens[1:3])
            and len(tokens) == 3 + int(tokens[1]) * int(tokens[2])
            and all(t in ('0', '1') for t in tokens[3:])):
        m, n = int(tokens[1]), int(tokens[2])
        bits = list(map(int, tokens[3:]))
        rows = [sum(bits[i * n + j] << j for j in range(n)) for i in range(m)]
        return Target.make(name, n, rows, meta={'source_format': 'nist-mat'})
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


def load_matrix_text(path, name=None):
    """``parse_matrix_text`` of a file; the name defaults to the file stem."""
    path = Path(path)
    stem = path.name.split('.')[0]
    target = parse_matrix_text(path.read_text(), name or stem)
    target.meta['source_path'] = str(path)
    return target


# --------------------------------------------------------------------------------------------
# JSON targets and the catalog
# --------------------------------------------------------------------------------------------
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


def from_json(data, seed_root=SEARCH_ROOT, name=None):
    """Target from a dict in the ``search/targets/*.json`` format, or a catalog entry that
    gives a ``generator`` spec instead of ``rows``.  Relative seed paths resolve against
    ``seed_root`` (``search/`` for the existing files)."""
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
                              'matrix_sha256', 'seeds', 'generator', 'seed_root')})
    if 'name' in data:
        meta['title'] = data['name']
    if data.get('seed_root') == 'repo':
        seed_root = REPO_ROOT
    return Target(target.name, target.n_inputs, target.rows, target.matrix_sha256,
                  _seeds_from(data.get('seeds'), Path(seed_root)), meta)


def _catalog_files():
    files = {}
    if SEARCH_TARGETS.is_dir():
        for path in sorted(SEARCH_TARGETS.glob('*.json')):
            files[path.stem] = path
    if CATALOG_DIR.is_dir():
        for path in sorted(CATALOG_DIR.glob('*.json')):
            files[path.stem] = path          # xorsearch entries win on a name clash
    return files


def catalog():
    """Sorted names ``load_target`` accepts as catalog entries."""
    return sorted(_catalog_files())


def generators():
    """Generator kinds ``generate`` accepts (``kind`` or ``kind:key=value,...``)."""
    return ('mixcolumns', 'invmixcolumns', 'circulant', 'random', 'sparse')


def load_json(path, name=None):
    """Target from a JSON file (seed paths relative to ``search/`` unless the entry says
    ``"seed_root": "repo"``; xorsearch catalog entries use the repository root)."""
    path = Path(path).resolve()
    data = json.loads(path.read_text())
    root = REPO_ROOT if path.parent == CATALOG_DIR.resolve() else SEARCH_ROOT
    target = from_json(data, root, name)
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
    """Target from a ``Target``, a catalog name, a JSON / matrix-text path, or a generator
    spec (string or dict).  See the module docstring for the forms."""
    if isinstance(spec, Target):
        return spec
    if isinstance(spec, dict):
        # {"generator": "circulant", ...} is a generator spec; a dict whose "generator" is
        # itself a spec dict is a catalog entry.
        if isinstance(spec.get('generator'), str):
            return generate(spec)
        return from_json(spec)
    spec = str(spec)
    files = _catalog_files()
    if spec in files:
        return load_json(files[spec], spec)
    path = Path(spec).expanduser()
    for candidate in (path, REPO_ROOT / path, SEARCH_ROOT / path, SEARCH_TARGETS / path):
        if candidate.is_file():
            if candidate.suffix == '.json':
                return load_json(candidate)
            return load_matrix_text(candidate)
    if spec.partition(':')[0] in generators():
        return generate(spec)
    raise ValueError('unknown target %r; catalog: %s; generators: %s'
                     % (spec, ', '.join(catalog()), ', '.join(generators())))
