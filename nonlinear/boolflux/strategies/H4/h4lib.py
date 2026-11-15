"""H4 toolkit: symbolic GF(2^8) circuits over arbitrary subfield towers / bases.

A *bundle* is a dict {wire: c} with c in F = GF(2^8) (poly 0x11B); its value at input x is
sum_w val_w(x) * c.  Wire 0 is the constant 1.  GF(2)-linear maps (Frobenius, multiplication by a
constant, change of basis) act on the constants only, so they cost nothing; XOR networks are only
materialised for AND operands and for the outputs.  Every AND is created by `Circ.AND` on two
GF(2)-valued bundles (constants in {0,1}).

Input convention (as core.py / NIST): file input i is bit 7-i of the byte x.
"""
from __future__ import annotations

import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PKG.parent))
from boolflux import core  # noqa: E402

POLY = 0x11B
ONES = (1 << 256) - 1


def mul(a, b):
    r = 0
    while b:
        if b & 1: r ^= a
        b >>= 1; a <<= 1
        if a & 0x100: a ^= POLY
    return r


def pw(a, e):
    r = 1
    e %= 255
    while e:
        if e & 1: r = mul(r, a)
        a = mul(a, a); e >>= 1
    return r


def inv(a):
    return pw(a, 254) if a else 0


G = 3
W = pw(G, 85)                       # generator of GF(4)*
GF2 = [0, 1]
Q = [0, 1, W, mul(W, W)]
K = sorted({pw(a, 17) for a in range(256)})
F = list(range(256))
assert len(K) == 16


def frob(c, k=1):
    for _ in range(k): c = mul(c, c)
    return c


# ---------------------------------------------------------------------------------------------
class Circ:
    def __init__(self):
        # wire tables; wire 0 = constant 1, wires 1..8 = x bits (wire 1+k = bit k of x)
        self.tab = [ONES]
        self.kind = [('const',)]
        for k in range(8):
            t = 0
            for p in range(256):
                if (p >> k) & 1: t |= 1 << p
            self.tab.append(t); self.kind.append(('in', 7 - k))   # file input index 7-k
        self.ands = 0
        self.x = {1 + k: 1 << k for k in range(8)}

    # bundles ---------------------------------------------------------------------------------
    @staticmethod
    def add(*bs):
        r = {}
        for b in bs:
            for w, c in b.items():
                v = r.get(w, 0) ^ c
                if v: r[w] = v
                else: r.pop(w, None)
        return r

    @staticmethod
    def scale(b, s):
        r = {}
        for w, c in b.items():
            v = mul(c, s)
            if v: r[w] = v
        return r

    @staticmethod
    def frob(b, k=1):
        return {w: frob(c, k) for w, c in b.items()}

    @staticmethod
    def const(c):
        return {0: c} if c else {}

    def project(self, b, sub):
        """b's value is known to lie in the subfield `sub`: rewrite its constants through a
        GF(2)-linear projection F -> sub that fixes sub (checked on all 256 inputs)."""
        Bs = []; span = {0}
        for e in sorted(sub):
            if e not in span: Bs.append(e); span |= {s ^ e for s in span}
        Ball = list(Bs)
        for e in range(1, 256):
            if e not in span: Ball.append(e); span |= {s ^ e for s in span}
        # coordinates in Ball
        idx = {}
        for c in range(256):
            v = 0
            for i in range(8):
                if (c >> i) & 1: v ^= Ball[i]
            idx[v] = c
        pr = {}
        for c in range(256):
            cc = idx[c]; v = 0
            for i in range(len(Bs)):
                if (cc >> i) & 1: v ^= Bs[i]
            pr[c] = v
        r = {w: pr[c] for w, c in b.items() if pr[c]}
        assert self.value(r) == self.value(b), 'value not in subfield'
        return r

    def value(self, b):
        """value table: list of 256 field elements"""
        out = [0] * 256
        for w, c in b.items():
            t = self.tab[w]
            for p in range(256):
                if (t >> p) & 1: out[p] ^= c
        return out

    def table(self, b):
        """truth table of a GF(2)-valued bundle"""
        t = 0
        for w, c in b.items():
            assert c in (0, 1), 'not GF(2)-valued'
            if c: t ^= self.tab[w]
        return t

    def AND(self, a, b):
        ta, tb = self.table(a), self.table(b)
        self.tab.append(ta & tb); self.kind.append(('and', dict(a), dict(b)))
        self.ands += 1
        return {len(self.tab) - 1: 1}

    def bit(self, b, k):
        """GF(2) bundle: bit k (standard coordinate) of the F-valued bundle b"""
        r = {}
        for w, c in b.items():
            if (c >> k) & 1: r[w] = 1
        return r

    # export ----------------------------------------------------------------------------------
    def to_circuit(self, outs, name='h4'):
        """outs: list of 8 GF(2) bundles = file outputs y0..y7.  Builds XOR chains (cached)."""
        gates = []
        sig = {}
        for w in range(1, 9):
            sig[w] = self.kind[w][1]
        n = 8
        cache = {}

        def emit(op, a, b):
            gates.append((op, a, b)); return n + len(gates) - 1

        def lin(bund):
            ws = sorted(w for w in bund if w != 0)
            cst = bund.get(0, 0)
            key = (tuple(ws), cst)
            if key in cache: return cache[key]
            assert ws, 'constant operand'
            s = sig[ws[0]]
            for j, w in enumerate(ws[1:]):
                op = 9 if (cst and j == len(ws) - 2) else 6
                s = emit(op, s, sig[w])
            if cst and len(ws) == 1:
                s = emit(3, s, s)
            cache[key] = s
            return s

        for w in range(9, len(self.tab)):
            kd = self.kind[w]
            if kd[0] == 'and':
                a = lin(kd[1]); b = lin(kd[2])
                sig[w] = emit(8, a, b)
        outsig = [lin(o) for o in outs]
        return core.Circuit(8, 8, gates, outsig, name).live()


# ---------------------------------------------------------------------------------------------
class Level:
    """L_i = sub(basis) : a degree-2 extension of the subfield `sub` with basis (e0, e1)."""
    def __init__(self, sub, field, e0, e1, name):
        self.sub, self.field, self.e = sub, field, (e0, e1)
        self.name = name
        self.dec = {}
        for a in sub:
            for b in sub:
                v = mul(a, e0) ^ mul(b, e1)
                assert v not in self.dec, 'not a basis'
                self.dec[v] = (a, b)
        assert set(self.dec) == set(field)
        # sigma = generator of Gal(L_i / sub): x -> x^{|sub|}
        self.q = len(sub)

    def coords(self, b):
        b0, b1 = {}, {}
        for w, c in b.items():
            c0, c1 = self.dec[c]
            if c0: b0[w] = c0
            if c1: b1[w] = c1
        return b0, b1


def find_elem(field, sub, pred=lambda e: True):
    for e in field:
        if e not in sub and pred(e): return e
    raise ValueError


class Tower:
    """levels[0] = Q over GF(2), levels[1] = K over Q, levels[2] = F over K.
    kind per level: 'poly' -> (1, t) ; 'normal' -> (t, t^q)"""
    def __init__(self, kinds=('normal', 'normal', 'normal'), gens=(None, None, None)):
        subs = [GF2, Q, K, F]
        self.levels = []
        for i in range(3):
            sub, fld = subs[i], subs[i + 1]
            q = len(sub)
            kd = kinds[i]
            t = gens[i]
            if t is None:
                if kd == 'normal':
                    t = find_elem(fld, sub, lambda e: (e ^ pw(e, q)) and (pw(e, q) not in (e,))
                                  and _indep(e, pw(e, q), sub))
                else:
                    t = find_elem(fld, sub)
            if kd == 'normal':
                lv = Level(sub, fld, t, pw(t, q), 'n%d' % i)
            else:
                lv = Level(sub, fld, 1, t, 'p%d' % i)
            self.levels.append(lv)


def _indep(a, b, sub):
    vals = {mul(x, a) ^ mul(y, b) for x in sub for y in sub}
    return len(vals) == len(sub) ** 2


# ---------------------------------------------------------------------------------------------
# arithmetic on bundles.  lvl: 0 = GF(2) (AND), 1 = Q, 2 = K, 3 = F.
def fmul(C, T, a, b, lvl):
    """product of two bundles valued in field level lvl (Karatsuba per level)"""
    if not a or not b: return {}
    if lvl == 0:
        return C.AND(a, b)
    L = T.levels[lvl - 1]
    e0, e1 = L.e
    a0, a1 = L.coords(a); b0, b1 = L.coords(b)
    p = fmul(C, T, a0, b0, lvl - 1)
    q = fmul(C, T, a1, b1, lvl - 1)
    r = fmul(C, T, C.add(a0, a1), C.add(b0, b1), lvl - 1)
    e01 = mul(e0, e1)
    return C.add(C.scale(p, mul(e0, e0) ^ e01), C.scale(q, mul(e1, e1) ^ e01), C.scale(r, e01))


def smul(C, T, a, s, lvl_a, lvl_s):
    """a in level lvl_a, s in subfield level lvl_s <= lvl_a: coordinatewise."""
    if lvl_a == lvl_s: return fmul(C, T, a, s, lvl_s)
    L = T.levels[lvl_a - 1]
    a0, a1 = L.coords(a)
    r0 = smul(C, T, a0, s, lvl_a - 1, lvl_s)
    r1 = smul(C, T, a1, s, lvl_a - 1, lvl_s)
    return C.add(C.scale(r0, L.e[0]), C.scale(r1, L.e[1]))


def norm(C, T, a, lvl):
    """N_{L_lvl / L_{lvl-1}}(a) = a * a^q with one subfield product"""
    L = T.levels[lvl - 1]
    q = L.q
    e0, e1 = L.e
    a0, a1 = L.coords(a)
    # a^q = a0 e0^q + a1 e1^q (a_i fixed by x->x^q)
    e0q, e1q = pw(e0, q), pw(e1, q)
    # a*a^q = a0^2 e0 e0q + a1^2 e1 e1q + a0 a1 (e0 e1q + e1 e0q)
    p = fmul(C, T, a0, a1, lvl - 1)
    sq = lambda b: C.frob(b, 1)
    # a0^2 as bundle: wires are GF(2)-valued so (sum w c)^2 = sum w c^2
    t0 = C.scale(sq(a0), mul(e0, e0q)) if mul(e0, e0q) else {}
    t1 = C.scale(sq(a1), mul(e1, e1q))
    return C.add(t0, t1, C.scale(p, mul(e0, e1q) ^ mul(e1, e0q)))


def finv(C, T, a, lvl, kinv=None):
    """inverse in level lvl via norm to the subfield: a^-1 = a^q * N(a)^-1"""
    if lvl == 1:
        return C.frob(a, 1)              # GF(4): a^-1 = a^2
    if lvl == 2 and kinv is not None:
        return kinv(C, a)
    L = T.levels[lvl - 1]
    n = norm(C, T, a, lvl)
    ni = finv(C, T, n, lvl - 1, kinv)
    aq = C.frob(a, {1: 1, 2: 2, 3: 4}[lvl])
    return smul(C, T, aq, ni, lvl, lvl - 1)


# ---------------------------------------------------------------------------------------------
# AES output affine map:  S(x) = A x^-1 + 0x63
def aes_affine_bits(C, y):
    """y: F-valued bundle (= x^-1).  Returns the 8 file-output GF(2) bundles y0..y7 (y_j = bit 7-j)."""
    outs = []
    for j in range(8):
        k = 7 - j
        b = {}
        for i in (k, (k + 4) % 8, (k + 5) % 8, (k + 6) % 8, (k + 7) % 8):
            b = C.add(b, C.bit(y, i))
        if (0x63 >> k) & 1: b = C.add(b, {0: 1})
        outs.append(b)
    return outs


def check_inverse(C, y):
    v = C.value(y)
    return all(v[p] == inv(p) for p in range(256))


def save(C, y, path, comments=(), name='h4'):
    outs = aes_affine_bits(C, y)
    c = C.to_circuit(outs, name)
    m = core.Model.load('nist')
    Path(path).write_text(core.write_ncff(c, m, comments), encoding='utf-8', newline='\n')
    return c.metrics(m)
