"""H2 helpers: finite fields, truth-table linear algebra, exact small product-cover search,
and a naive XAG -> NCFF circuit builder.

Truth tables are Python ints over 2^n points (bit p = value at point p).
"""
from __future__ import annotations
import itertools, sys
from pathlib import Path

# ---------------------------------------------------------------- GF(2^8), AES polynomial
def gmul(a, b, poly=0x11B, deg=8):
    r = 0
    while b:
        if b & 1: r ^= a
        b >>= 1; a <<= 1
        if a >> deg: a ^= poly
    return r


def gpow(a, e, poly=0x11B, deg=8):
    r = 1
    while e:
        if e & 1: r = gmul(r, a, poly, deg)
        a = gmul(a, a, poly, deg); e >>= 1
    return r


INV = [0] + [gpow(a, 254) for a in range(1, 256)]
SBOX = []
for _x in range(256):
    _v = INV[_x]; _o = 0
    for _i in range(8):
        _bit = ((_v >> _i) ^ (_v >> ((_i + 4) % 8)) ^ (_v >> ((_i + 5) % 8)) ^ (_v >> ((_i + 6) % 8))
                ^ (_v >> ((_i + 7) % 8)) ^ (0x63 >> _i)) & 1
        _o |= _bit << _i
    SBOX.append(_o)
assert SBOX[0] == 0x63 and SBOX[1] == 0x7C


def tr8(a):
    """Absolute trace GF(256) -> GF(2)."""
    t = 0; y = a
    for _ in range(8):
        t ^= y; y = gmul(y, y)
    return t & 1


# ---------------------------------------------------------------- truth tables
def table(n, f):
    """Truth table of f: range(2^n) -> {0,1}."""
    t = 0
    for p in range(1 << n):
        if f(p) & 1: t |= 1 << p
    return t


def var_tables(n):
    """Tables of the n coordinate bits: var i = bit i of the point."""
    return [table(n, lambda p, i=i: (p >> i) & 1) for i in range(n)]


def ones(n):
    return (1 << (1 << n)) - 1


# ---------------------------------------------------------------- GF(2) linear algebra on ints
class Basis:
    """Echelon basis of a GF(2) space of ints, with optional tags (combination tracking)."""

    def __init__(self, track=False):
        self.rows = {}          # pivot bit -> (vec, tag)
        self.track = track
        self.n = 0

    def reduce(self, v, tag=0):
        while v:
            p = v.bit_length() - 1
            r = self.rows.get(p)
            if r is None: break
            v ^= r[0]; tag ^= r[1]
        return v, tag

    def full_reduce(self, v, tag=0):
        # reduce all bits (not only leading)
        out = 0
        while v:
            p = v.bit_length() - 1
            r = self.rows.get(p)
            if r is None:
                out |= 1 << p; v ^= 1 << p
            else:
                v ^= r[0]; tag ^= r[1]
        return out, tag

    def add(self, v, tag=0):
        v, tag = self.reduce(v, tag)
        if v == 0: return False
        self.rows[v.bit_length() - 1] = (v, tag); self.n += 1
        return True

    def contains(self, v):
        return self.full_reduce(v)[0] == 0

    def copy(self):
        b = Basis(self.track); b.rows = dict(self.rows); b.n = self.n
        return b


def rank(vecs):
    b = Basis()
    for v in vecs: b.add(v)
    return b.n


# ---------------------------------------------------------------- quotient helper
class Quotient:
    """Reduce vectors modulo a fixed space E; returns canonical fully reduced representatives."""

    def __init__(self, E):
        self.B = Basis()
        for v in E: self.B.add(v)

    def __call__(self, v):
        return self.B.full_reduce(v)[0]


def min_cover(T, cands, kmax, extra_max=2, want_all=False, limit=None):
    """Exact: least k <= kmax such that span(T) <= span(some k of cands) (all vectors already
    reduced modulo the free space).  T: list of vectors; cands: list of (vec, label).
    Returns (k, [labels]) or (None, None).  Method: span(P) = S >= T, dim S = k; S = T + W with
    W spanned by k - t candidate images mod T; S must be spanned by the candidates inside it."""
    TB = Basis()
    for v in T: TB.add(v)
    t = TB.n
    cand = [(v, l) for v, l in cands if v]
    img = []
    for v, l in cand:
        r = TB.full_reduce(v)[0]
        img.append(r)
    # distinct nonzero images mod T
    found = []
    for k in range(t, kmax + 1):
        e = k - t
        if e > extra_max: break
        pts = sorted({r for r in img if r})
        idx_by_img = {}
        for i, r in enumerate(img): idx_by_img.setdefault(r, []).append(i)
        seen = set()
        for combo in itertools.combinations(pts, e):
            W = Basis()
            ok = True
            for r in combo:
                if not W.add(r): ok = False; break
            if not ok: continue
            key = tuple(sorted(W.full_reduce(r)[0] for r in combo))
            # canonical W: closure
            Wspan = set([0])
            for r in combo:
                Wspan |= {s ^ r for s in Wspan}
            key = frozenset(Wspan)
            if key in seen: continue
            seen.add(key)
            inside = [i for i, r in enumerate(img) if r in Wspan]
            S = Basis()
            chosen = []
            for i in inside:
                if S.add(cand[i][0]): chosen.append(cand[i][1])
            if S.n == k:
                # S contains T? (S has dim k and maps onto W with kernel inside T: check T in S)
                if all(S.contains(v) for v in T):
                    if not want_all: return k, chosen
                    found.append((k, chosen))
                    if limit and len(found) >= limit: return found
        if want_all and found: return found
    return (None, None) if not want_all else found


# ---------------------------------------------------------------- XAG -> circuit
def build_circuit(n, ands, outs, name='h2'):
    """ands: list of (ta, tb) truth tables (over 2^n points, msb/msb input convention of core:
    input i = bit n-1-i of the point); each operand must be affine in (inputs, earlier ANDs).
    outs: list of truth tables, affine in (inputs, ANDs).  Returns a core.Circuit (naive XOR
    chains).  Raises ValueError if some operand is not affine in what is available."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from boolflux import core
    ONE = ones(n)
    ins = core.input_tables(n)
    sig_t = list(ins)        # truth table of each signal
    gates = []
    B = Basis()
    # tag: bitmask over 'atoms' (signal ids) ; atom list
    atoms = []

    def add_atom(sig):
        atoms.append(sig)
        B.add(sig_t[sig], 1 << (len(atoms) - 1))

    for i in range(n): add_atom(i)
    cache = {}

    def realize(t):
        neg = 0
        r, tag = B.full_reduce(t)
        if r != 0:
            r2, tag2 = B.full_reduce(t ^ ONE)
            if r2 != 0: raise ValueError('not affine in available signals')
            tag = tag2; neg = 1
        key = (tag, neg)
        if key in cache: return cache[key]
        sigs = [atoms[i] for i in range(len(atoms)) if (tag >> i) & 1]
        if not sigs:
            raise ValueError('constant operand')
        cur = sigs[0]
        for s in sigs[1:]:
            gates.append((6, cur, s)); sig_t.append(sig_t[cur] ^ sig_t[s]); cur = n + len(gates) - 1
        if neg:
            gates.append((3, cur, cur)); sig_t.append(sig_t[cur] ^ ONE); cur = n + len(gates) - 1
        cache[key] = cur
        return cur

    for ta, tb in ands:
        a = realize(ta); b = realize(tb)
        gates.append((8, a, b)); sig_t.append(sig_t[a] & sig_t[b])
        add_atom(n + len(gates) - 1)
    osig = [realize(t) for t in outs]
    c = core.Circuit(n, len(outs), gates, osig, name)
    return c.live()
