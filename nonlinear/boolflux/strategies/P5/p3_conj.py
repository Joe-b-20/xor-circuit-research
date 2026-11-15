#!/usr/bin/env python3
"""Conjugates of an AES S-box circuit by the symmetries of GF(2^8) inversion.

For G(z) = lam * z^(2^k) (lam != 0, k = 0..7) inversion satisfies inv = G' o inv o G with
G'(w) = (lam * w)^(2^(8-k)).  With S = Aff o inv (Aff(w) = A w + 0x63):
    S(x) = Mout * (S(G x) + c) + c,   Mout = A G' A^-1,  c = 0x63.
So from a circuit C for S we get a circuit for S: inputs transformed by G, C unchanged, outputs
transformed by the affine map w -> Mout (w + c) + c.  Its top linear layer (forms of G x) and its bottom
linear layer (Mout applied to the outputs) are re-synthesised with trb.rebuild (track F: randomised Paar
with Kraft depth checks), several seeds; the AND structure and the middle layers are unchanged.  The
result is checked on all 256 inputs.  2040 conjugates (255 x 8) per circuit.

    conj.py FILE --out DIR [--seeds 3] [--lams 1-255] [--ks 0-7] [--save-best 30]
"""
import json, random, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2])); sys.path.append(str(HERE.parent / "F"))
import p3_bottom as BT  # noqa
import trb  # noqa
from boolflux import core, targets  # noqa

AND, XOR, XNOR, NOT = 8, 6, 9, 3
AES = targets.aes_sbox()
MODEL = core.Model.load('nist')


def gmul(a, b):
    r = 0
    while b:
        if b & 1: r ^= a
        a <<= 1
        if a & 0x100: a ^= 0x11B
        b >>= 1
    return r


def gpow(a, e):
    r = 1
    while e:
        if e & 1: r = gmul(r, a)
        a = gmul(a, a); e >>= 1
    return r


def matrix(f):
    """columns: f(1 << j) for j = 0..7 (bit j of the byte)."""
    return [f(1 << j) for j in range(8)]


def apply(M, x):
    r = 0
    for j in range(8):
        if x >> j & 1: r ^= M[j]
    return r


INV = [0] + [gpow(z, 254) for z in range(1, 256)]
assert all(AES[z] == apply(matrix(lambda w: AES[INV[w]] ^ 0x63), INV[z]) ^ 0x63 for z in range(256))
A = matrix(lambda w: AES[INV[w]] ^ 0x63)
Ainv = [0] * 8
for y in range(256):
    v = apply(A, y)
    for j in range(8):
        if v == 1 << j: Ainv[j] = y


def conj_circuit(c, lam, k):
    """Naive conjugate circuit (input XOR network, c, output affine network)."""
    G = matrix(lambda z: gmul(lam, gpow(z, 1 << k)))
    Gp = matrix(lambda w: gpow(gmul(lam, w), 1 << ((8 - k) % 8)))
    Mout = matrix(lambda y: apply(A, apply(Gp, apply(Ainv, y))))
    const = apply(Mout, 0x63) ^ 0x63
    n = c.n
    gates = []
    def sid(): return n + len(gates) - 1
    # circuit input i (x_i) is byte bit (7 - i)
    def xsig(bit): return 7 - bit
    u = []
    for i in range(8):           # u_i = circuit input i of C = byte bit 7-i of G x
        bit = 7 - i
        terms = [xsig(j) for j in range(8) if G[j] >> bit & 1]
        s = terms[0]
        for t in terms[1:]:
            gates.append((XOR, s, t)); s = sid()
        if len(terms) == 1:
            pass
        u.append(s)
    mp = {i: u[i] for i in range(n)}
    for j, (op, a, b) in enumerate(c.gates):
        gates.append((op, mp[a], mp[b])); mp[n + j] = sid()
    old = [mp[s] for s in c.outputs]     # old output i = byte bit 7-i of S(Gx)
    outs = []
    for i in range(8):
        bit = 7 - i
        terms = [old[7 - j] for j in range(8) if Mout[j] >> bit & 1]
        cst = const >> bit & 1
        s = terms[0]
        for q, t in enumerate(terms[1:]):
            last = q == len(terms) - 2
            gates.append((XNOR if (last and cst) else XOR, s, t)); s = sid()
        if cst and len(terms) == 1:
            gates.append((NOT, s, s)); s = sid()
        outs.append(s)
    return core.Circuit(n, 8, gates, outs).live()


def resynth(c, rng, rounds=1):
    m = c.metrics(MODEL); D = m['GD']
    for _ in range(rounds):
        for kind in ('top', 'bottom'):
            c2, info = trb.rebuild(c, D, kind, rng)
            if c2.value_table() == AES and len(c2.gates) <= len(c.gates): c = c2
    return c


def main():
    a = sys.argv[1:]
    f = a[0]; out = Path(a[a.index('--out') + 1]); out.mkdir(parents=True, exist_ok=True)
    seeds = int(a[a.index('--seeds') + 1]) if '--seeds' in a else 3
    def rng_(s):
        lo, hi = map(int, s.split('-')); return range(lo, hi + 1)
    lams = rng_(a[a.index('--lams') + 1]) if '--lams' in a else range(1, 256)
    ks = rng_(a[a.index('--ks') + 1]) if '--ks' in a else range(8)
    save = int(a[a.index('--save-best') + 1]) if '--save-best' in a else 30
    c = BT.load(f)
    assert c.value_table() == AES
    res = []
    t0 = time.time()
    log = open(out / 'conj.jsonl', 'a')
    for k in ks:
        for lam in lams:
            cc = conj_circuit(c, lam, k)
            assert cc.value_table() == AES, (lam, k)
            best = None
            for s in range(seeds):
                r = resynth(cc, random.Random(s), 2)
                m = r.metrics(MODEL)
                key = (m['G'], m['GD'])
                if best is None or key < best[0]: best = (key, r)
            (G, GD), r = best
            rec = {'lam': lam, 'k': k, 'G': G, 'GD': GD, 'A': r.metrics(MODEL)['A']}
            log.write(json.dumps(rec) + '\n'); log.flush()
            res.append((G, GD, lam, k, r))
        print('k %d done %.0fs best so far %s' % (k, time.time() - t0, sorted(res, key=lambda t: t[:2])[0][:4]), flush=True)
    res.sort(key=lambda t: t[:2])
    for G, GD, lam, k, r in res[:save]:
        (out / ('conj-l%d-k%d-g%d-gd%d.circ.txt' % (lam, k, G, GD))).write_text(
            core.write_ncff(r, MODEL, comments=['P3 conj.py of %s, lam %d k %d, trb top/bottom resynthesis' % (f, lam, k)]))
    print('top', [t[:4] for t in res[:15]])


if __name__ == '__main__':
    main()
