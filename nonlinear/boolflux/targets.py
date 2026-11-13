"""Target functions, as value tables ``table[x]`` (msb/msb, see core.py).

Built-in: AES S-box and inverse (FIPS-197), chi (Keccak/Xoodoo-style) of width 3 and 5,
majority, full adder, multiplication and inversion in GF(2^4), and every S-box of
``benchmarks/sboxes.json`` (spec tables with sources).
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SBOX_FILE = HERE / 'benchmarks' / 'sboxes.json'


def gf_mul(a, b, m, poly):
    r = 0
    while b:
        if b & 1: r ^= a
        b >>= 1; a <<= 1
        if a >> m: a ^= poly
    return r


def aes_sbox():
    inv = [0] * 256
    for a in range(1, 256):
        for b in range(1, 256):
            if gf_mul(a, b, 8, 0x11B) == 1: inv[a] = b; break
    out = []
    for x in range(256):
        b = inv[x]; v = 0
        for i in range(8):
            bit = ((b >> i) ^ (b >> ((i + 4) % 8)) ^ (b >> ((i + 5) % 8)) ^ (b >> ((i + 6) % 8))
                   ^ (b >> ((i + 7) % 8)) ^ (0x63 >> i)) & 1
            v |= bit << i
        out.append(v)
    return out


def aes_inv_sbox():
    s = aes_sbox(); inv = [0] * 256
    for x, y in enumerate(s): inv[y] = x
    return inv


def chi(w):
    """b_i = a_i ^ (~a_{i+1} & a_{i+2}); a_i is bit i of the integer (spec convention)."""
    out = []
    for x in range(1 << w):
        a = [(x >> i) & 1 for i in range(w)]
        out.append(sum((a[i] ^ ((1 - a[(i + 1) % w]) & a[(i + 2) % w])) << i for i in range(w)))
    return out


def gf16_mul():
    """8 inputs (a = high nibble, b = low nibble), 4 outputs: a*b mod x^4+x+1."""
    return [gf_mul(x >> 4, x & 15, 4, 0x13) for x in range(256)]


def gf16_inv():
    t = [0] * 16
    for a in range(1, 16):
        for b in range(1, 16):
            if gf_mul(a, b, 4, 0x13) == 1: t[a] = b
    return t


BUILTIN = {
    'aes': (8, 8, aes_sbox, 'AES S-box, FIPS-197 (computed: inversion mod 0x11B, affine 0x63)'),
    'aes-inv': (8, 8, aes_inv_sbox, 'AES inverse S-box, FIPS-197'),
    'maj3': (3, 1, lambda: [1 if bin(x).count('1') >= 2 else 0 for x in range(8)], 'majority of 3'),
    'fulladd': (3, 2, lambda: [bin(x).count('1') for x in range(8)],
                'full adder: output = (carry, sum) = popcount of 3 bits'),
    'gf16-mul': (8, 4, gf16_mul, 'GF(2^4) multiplication mod x^4+x+1, input = a<<4 | b'),
    'gf16-inv': (4, 4, gf16_inv, 'GF(2^4) inversion mod x^4+x+1 (0 -> 0)'),
}


REPO = HERE.parents[1]


def linear_map(name):
    """(n, m, rows) of circuits/<name>/<name>.mat.txt (NIST format: '1', 'rows cols', bit rows);
    output j = XOR of the inputs i with rows[j][i] = 1 (input i = x_i, msb first)."""
    toks = (REPO / 'circuits' / name / (name + '.mat.txt')).read_text().split()
    m, n = int(toks[1]), int(toks[2])
    bits = [int(t) for t in toks[3:3 + m * n]]
    return n, m, [bits[j * n:(j + 1) * n] for j in range(m)]


def load(name):
    """(n, m, table, description) for a target name; 'map:<name>' is a linear map of circuits/."""
    if name.startswith('map:'):
        n, m, rows = linear_map(name[4:])
        if n > 16: raise ValueError('BoolFlux keeps complete truth tables: at most 16 inputs')
        table = []
        for x in range(1 << n):
            xs = [(x >> (n - 1 - i)) & 1 for i in range(n)]
            v = 0
            for j in range(m):
                v = (v << 1) | (sum(r & b for r, b in zip(rows[j], xs)) & 1)
            table.append(v)
        return n, m, table, 'linear map %s (circuits/%s)' % (name[4:], name[4:])
    if name in BUILTIN:
        n, m, f, d = BUILTIN[name]
        return n, m, f(), d
    if SBOX_FILE.exists():
        for s in json.loads(SBOX_FILE.read_text(encoding='utf-8'))['sboxes']:
            if s['name'] == name:
                return s['n'], s['m'], s['table'], s.get('source', '')
    raise KeyError('unknown target %s' % name)


def names():
    out = list(BUILTIN)
    if SBOX_FILE.exists():
        out += [s['name'] for s in json.loads(SBOX_FILE.read_text(encoding='utf-8'))['sboxes']
                if s['name'] not in BUILTIN and 'table' in s]
    return out
