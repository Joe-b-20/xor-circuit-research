"""Hub shared helpers: loading, exact verification (two verifiers), metrics, code version, interface spaces."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

HUB = Path(__file__).resolve().parent
PKG = HUB.parent                       # nonlinear/boolflux
REPO = PKG.parents[1]
sys.path.insert(0, str(PKG.parent))
sys.path.insert(0, str(PKG / 'independent'))
from boolflux import core, targets      # noqa: E402
import verify as V                      # noqa: E402

MODEL = core.Model.load('nist')
LIB = {'AND', 'XOR', 'XNOR', 'NOT'}
ONES = (1 << 256) - 1
NIST = REPO / 'nonlinear' / 'nist'
KERNEL_SRC = PKG / 'kernel' / 'bfx.c'


@lru_cache(None)
def sbox():
    return tuple(targets.aes_sbox())


@lru_cache(None)
def vsbox():
    return (8, 8, V.aes_sbox())


def load(path):
    p = Path(path)
    if p.suffix == '.bfx':
        return core.from_kernel(p.read_text(), name=p.stem)
    return core.read_ncff(str(p))


def kernel_text(c):
    return core.to_kernel(c)


def cid(c):
    return hashlib.sha1(core.to_kernel(c).encode()).hexdigest()[:12]


def metrics(c):
    m = c.metrics(MODEL)
    return (m['A'], m['AD'], m['G'], m['GD'])


def verify(c):
    """Admission check: core evaluation on all 256 inputs, independent verifier on the NCFF text,
    NIST library, metrics agreement.  Returns (ok, info)."""
    info = {}
    if {g[0] for g in c.gates} - MODEL.ops():
        return False, {'error': 'gate outside the NIST library'}
    if tuple(c.value_table()) != sbox():
        return False, {'error': 'core: wrong function'}
    txt = core.write_ncff(c, MODEL)
    r = V.verify_text(txt, vsbox())
    im = r.get('metrics') or {}
    m = metrics(c)
    if not r.get('ok'):
        return False, {'error': 'independent verifier: %s' % (r.get('errors') or r.get('mismatch'))}
    if tuple(im.get(k) for k in ('A', 'AD', 'G', 'GD')) != m:
        return False, {'error': 'metrics disagree %s vs %s' % (m, im)}
    if set(im.get('counts', {})) - LIB:
        return False, {'error': 'library %s' % im.get('counts')}
    info['counts'] = im.get('counts')
    return True, info


def leq(u, m):
    return all(a <= b for a, b in zip(u, m))


@lru_cache(None)
def published():
    """(A, AD, G, GD) of every forward AES S-box circuit in the pinned NIST collection."""
    sys.path.insert(0, str(PKG / 'campaigns'))
    import aes_check
    return tuple(u for (u, n) in aes_check.published())


def code_version():
    """git commit of the worktree + hash of the hub sources and the kernel source (dirty state)."""
    try:
        commit = subprocess.run(['git', '-C', str(REPO), 'rev-parse', '--short', 'HEAD'], capture_output=True,
                                text=True).stdout.strip()
    except Exception:
        commit = '?'
    h = hashlib.sha1()
    for f in sorted(HUB.glob('*.py')) + [KERNEL_SRC]:
        h.update(f.name.encode()); h.update(f.read_bytes())
    return '%s+%s' % (commit, h.hexdigest()[:10])


def atomic_write(path, text):
    path = Path(path); tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(text); os.replace(tmp, path)


# ---- GF(2^8) interface spaces (intrinsic: independent of the tower basis) ----------------------
def _gmul(a, b):
    r = 0
    while b:
        if b & 1: r ^= a
        a <<= 1
        if a & 0x100: a ^= 0x11B
        b >>= 1
    return r


def _gpow(a, e):
    r = 1
    while e:
        if e & 1: r = _gmul(r, a)
        a = _gmul(a, a); e >>= 1
    return r


def _bit_tables(f):
    ts = [0] * 8
    for x in range(256):
        v = f(x)
        for j in range(8):
            if (v >> j) & 1: ts[j] |= 1 << x
    return ts


class Span:
    def __init__(self, tabs=(), affine=True):
        self.rows = []
        if affine: self.add(ONES)
        for t in tabs: self.add(t)

    def reduce(self, t):
        for p, r in self.rows:
            if (t >> p) & 1: t ^= r
        return t

    def add(self, t):
        t = self.reduce(t)
        if t:
            self.rows.append((t.bit_length() - 1, t)); self.rows.sort(key=lambda x: -x[0])
            return True
        return False

    def __contains__(self, t):
        return self.reduce(t) == 0


@lru_cache(None)
def interface_spaces():
    inv = lambda y: _gpow(y, 14) if y else 0
    N = lambda x: _gpow(x, 17)
    return {'N': Span(_bit_tables(N)), 'Ninv': Span(_bit_tables(lambda x: inv(N(x)))),
            'u': Span(_bit_tables(lambda x: N(x) ^ inv(N(x)))),
            'out': Span(core.tables_from_values(8, 8, list(sbox())))}


def interface_tags(t):
    if t in (0, ONES): return []
    return [k for k, sp in interface_spaces().items() if t in sp]
