"""The two AES functions of the AES tools (aes_check.py, hub/, ops/): the S-box and its inverse.

    aes-sbox      S(x) = A inv(x) + 0x63 (FIPS-197); NIST set seeds/aes-sbox/, old-2020/aes-sbox-fwd-*,
                  sbox/aes-sbox-fwd-*; our circuits circuits/aes-sbox/
    aes-invsbox   S^-1(y) = inv(A^-1 (y + 0x63)); NIST set seeds/aes-invsbox/, old-2020/aes-sbox-rev-*,
                  sbox/aes-sbox-inv-*; our circuits circuits/aes-invsbox/

The function of a process is $BOOLFLUX_FUNCTION (default aes-sbox). use() sets it, so every child
process (hub operators, method-script workers) works on the same function. detect() names the
function a circuit computes; resolve('auto', start) is the function of a start circuit.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from boolflux import targets

ENV = 'BOOLFLUX_FUNCTION'
DEFAULT = 'aes-sbox'
SEEDS = Path(__file__).resolve().parent.parent / 'seeds'
INFO = {
    'aes-sbox': {'target': 'aes', 'label': 'AES S-box', 'seed_dir': 'aes-sbox', 'circuits_dir': 'aes-sbox',
                 'published': ('aes-sbox/*.circ.txt', 'old-2020/aes-sbox-fwd-*.slp', 'sbox/aes-sbox-fwd-*'),
                 'verify_flag': '--aes'},
    'aes-invsbox': {'target': 'aes-inv', 'label': 'AES inverse S-box', 'seed_dir': 'aes-invsbox',
                    'circuits_dir': 'aes-invsbox',
                    'published': ('aes-invsbox/*.circ.txt', 'old-2020/aes-sbox-rev-*.slp', 'sbox/aes-sbox-inv-*'),
                    'verify_flag': '--aes-inv'},
}
NAMES = tuple(INFO)
CHOICES = NAMES + ('auto',)


def name(function=None):
    """The function `function` (None = this process's: $BOOLFLUX_FUNCTION, default aes-sbox)."""
    f = function or os.environ.get(ENV) or DEFAULT
    if f not in INFO:
        raise ValueError('unknown AES function %r (known: %s)' % (f, ', '.join(NAMES)))
    return f


current = name


def use(function):
    """Make `function` the function of this process and of every child process it starts."""
    f = name(function)
    os.environ[ENV] = f
    return f


@lru_cache(None)
def _table(f):
    return tuple(targets.load(INFO[f]['target'])[2])


def table(function=None):
    """Value table (verifier 1, targets.py) of the function."""
    return _table(name(function))


def label(function=None):
    return INFO[name(function)]['label']


def published_files(function=None):
    """The pinned NIST circuits of the function (search/nonlinear/seeds/, pin in MANIFEST.json)."""
    out = []
    for g in INFO[name(function)]['published']:
        out += sorted(SEEDS.glob(g))
    return out


def detect(c):
    """The function circuit c (or a value table) computes, or None."""
    t = tuple(c if isinstance(c, (list, tuple)) else c.value_table())
    for f in NAMES:
        if t == table(f):
            return f
    return None


def resolve(function, start=None):
    """'auto' -> the function of the start circuit file; otherwise name(function)."""
    if function != 'auto':
        return name(function)
    from boolflux import core
    p = Path(start)
    c = core.from_kernel(p.read_text(), name=p.stem) if p.suffix == '.bfx' else core.read_ncff(str(p))
    f = detect(c)
    if f is None:
        raise SystemExit('%s computes neither the AES S-box nor its inverse (--function auto)' % start)
    return f
