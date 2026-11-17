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
PKG = HUB.parent                       # search/nonlinear/boolflux
REPO = PKG.parents[2]
sys.path.insert(0, str(PKG.parent))
sys.path.insert(0, str(PKG / 'independent'))
from boolflux import aesfn, core, targets   # noqa: E402,F401
import verify as V                      # noqa: E402

MODEL = core.Model.load('nist')
LIB = {'AND', 'XOR', 'XNOR', 'NOT'}
ONES = (1 << 256) - 1
NIST = PKG.parent / 'seeds'
KERNEL_SRC = PKG / 'kernel' / 'bfx.c'


def sbox():
    """Value table of this process's function (aesfn: $BOOLFLUX_FUNCTION, the S-box or its inverse)."""
    return aesfn.table()


def vsbox():
    """The same function for the independent verifier, from its own FIPS-197 code."""
    return _vsbox(aesfn.name())


@lru_cache(None)
def _vsbox(f):
    return (8, 8, V.aes_inv_sbox() if f == 'aes-invsbox' else V.aes_sbox())


def load(path):
    p = Path(path)
    if p.suffix == '.bfx':
        return core.from_kernel(p.read_text(), name=p.stem)
    return core.read_ncff(str(p))


def kernel_text(c):
    return core.to_kernel(c)


def cid(c):
    return hashlib.sha1(core.to_kernel(c).encode()).hexdigest()[:12]


def structure_key(c):
    """Canonical hash of the circuit as a DAG: invariant under gate order and the operand order
    of the symmetric gates.  Two circuits with the same key are the same structure written
    differently (the cell rule keeps K *distinct structures*).  Every gate counts,
    also a dead one (it is part of G), so a circuit and its cleaned copy are different."""
    n = c.n
    h = [b'i%d' % j for j in range(n)] + [None] * len(c.gates)
    live = []
    for j, (op, a, b) in enumerate(c.gates):
        op, a, b = core.canonical(op, a, b)
        x, y = h[a], h[b]
        if op in core.SYMMETRIC and y < x: x, y = y, x
        h[n + j] = hashlib.blake2b(b'%d|' % op + x + b'|' + y, digest_size=12).digest()
        live.append(h[n + j])
    t = hashlib.blake2b(digest_size=12)
    t.update(b'%d %d|' % (n, c.m))
    for x in sorted(live): t.update(x)
    t.update(b'|')
    for o in c.outputs: t.update(h[o]); t.update(b',')
    return t.hexdigest()


def clean(c):
    """Structural-hash cleanup: gates with the same operation and operands (operand order ignored
    for the symmetric gates) are merged into the first one, then gates no output depends on are
    dropped.  The function is unchanged.  Returns c itself when nothing changes.  (Without it,
    join and trb outputs carried duplicate AND gates, so their recorded A was one too high.)"""
    n = c.n; seen = {}; new = list(range(n)); gates = []
    for op, a, b in c.gates:
        op, a, b = core.canonical(op, new[a], new[b])
        if op in core.SYMMETRIC and b < a: a, b = b, a
        k = (op, a, b)
        s = seen.get(k)
        if s is None:
            gates.append(k); s = seen[k] = n + len(gates) - 1
        new.append(s)
    out = core.Circuit(c.n, c.m, gates, [new[o] for o in c.outputs], c.name, c.in_names, c.out_names).live()
    return c if len(out.gates) == len(c.gates) else out


def metrics(c):
    m = c.metrics(MODEL)
    return (m['A'], m['AD'], m['G'], m['GD'])


def verify(c):
    """Admission check: core evaluation on all 256 inputs, independent verifier on the NCFF text,
    NIST library, metrics agreement.  Returns (ok, info).  Never raises: a malformed circuit
    (forward reference, wrong shape, unknown op) is a rejection, not a crash of the caller."""
    try:
        return _verify(c)
    except Exception as e:
        return False, {'error': 'malformed circuit: %r' % (e,)}


def _verify(c):
    info = {}
    if (c.n, c.m) != (8, 8) or len(c.outputs) != 8:
        return False, {'error': 'shape %d -> %d, %d outputs' % (c.n, c.m, len(c.outputs))}
    for j, g in enumerate(c.gates):
        if len(g) != 3 or not (0 <= g[1] < c.n + j and 0 <= g[2] < c.n + j):
            return False, {'error': 'gate %d reads a signal that is not defined before it' % j}
    if any(not (0 <= o < c.n + len(c.gates)) for o in c.outputs):
        return False, {'error': 'output outside the circuit'}
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


def published():
    """(A, AD, G, GD) of every circuit of this process's function in the pinned NIST collection."""
    return _published(aesfn.name())


@lru_cache(None)
def _published(f):
    sys.path.insert(0, str(PKG))
    import aes_check
    return tuple(u for (u, n) in aes_check.published(f))


def source_files():
    """every source file whose content decides what a hub job computes: the hub and its operators
    (incl. hub/ops libraries and data), the gate and skeleton kernels, and the package modules they import"""
    fs = sorted(HUB.glob('*.py'))
    fs += sorted(f for f in (HUB / 'ops').rglob('*') if f.is_file() and f.suffix in ('.py', '.c', '.txt')
                 and '__pycache__' not in f.parts)
    fs += [KERNEL_SRC, PKG / 'kernel' / 'skel.c'] + [PKG / n for n in ('core.py', 'objective.py', 'targets.py', 'skeleton.py',
                                                                                 'aesfn.py', 'runlog.py')]
    fs += [PKG / 'independent' / 'verify.py', PKG / 'aes_check.py', PKG / 'models' / 'nist.json']
    fs += [PKG / 'ops' / n for n in ('winsat.py', 'winsat_lib.py', 'winsat_andrm.py', 'common.py')]   # hub/ops/op_andrm.py
    return [f for f in fs if f.exists()]


def file_sha(path):
    try:
        return hashlib.sha1(Path(path).read_bytes()).hexdigest()[:10]
    except OSError:
        return None


@lru_cache(None)
def code_version():
    """'<git commit>[-dirty]+<hash>': commit of the worktree, '-dirty' when tracked files under
    search/nonlinear/boolflux differ from it, and a hash of source_files() (so an edit to any of
    them, hub/ops/, core.py or the verifier included, changes the recorded version).  '?' when git is
    not available."""
    commit = '?'
    try:
        r = subprocess.run(['git', '-C', str(REPO), 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            commit = r.stdout.strip()
            d = subprocess.run(['git', '-C', str(REPO), 'status', '--porcelain', '--untracked-files=no', '--',
                                str(PKG)], capture_output=True, text=True)
            if d.returncode == 0 and d.stdout.strip(): commit += '-dirty'
    except Exception:
        pass
    h = hashlib.sha1()
    for f in source_files():
        h.update(str(f.relative_to(PKG)).encode()); h.update(b'\0'); h.update(f.read_bytes())
    return '%s+%s' % (commit, h.hexdigest()[:10])


def atomic_write(path, text):
    path = Path(path); tmp = path.with_name('%s.%d.tmp' % (path.name, os.getpid()))
    with open(tmp, 'w') as f:
        f.write(text); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


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


def interface_spaces():
    return _interface_spaces(aesfn.name())


@lru_cache(None)
def _interface_spaces(f):
    """Spans of the inversion's intrinsic intermediate functions, as functions of the circuit's input: the S-box
    inverts its input (S = Aff o inv), the inverse S-box inverts Aff^-1(input) (S^-1 = inv o Aff^-1, so
    Aff^-1(x) = inv(S^-1(x)), inv the GF(2^8) inverse).  Until 2026-11-16 the inverse used the forward spaces (U7 #7)."""
    inv = lambda y: _gpow(y, 14) if y else 0              # inverse in GF(16), where the norm N takes its values
    tab = aesfn.table(f)
    pre = (lambda x: _gpow(tab[x], 254)) if f == 'aes-invsbox' else (lambda x: x)   # GF(2^8) inverse of S^-1(x)
    N = lambda x: _gpow(pre(x), 17)
    return {'N': Span(_bit_tables(N)), 'Ninv': Span(_bit_tables(lambda x: inv(N(x)))),
            'u': Span(_bit_tables(lambda x: N(x) ^ inv(N(x)))),
            'out': Span(core.tables_from_values(8, 8, list(tab)))}


def interface_tags(t):
    if t in (0, ONES): return []
    return [k for k, sp in interface_spaces().items() if t in sp]
