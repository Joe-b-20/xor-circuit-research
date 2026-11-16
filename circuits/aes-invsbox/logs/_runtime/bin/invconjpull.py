#!/usr/bin/env python3
"""conjpull for the AES INVERSE S-box (campaign 2026-11-16-invsbox, agent SX; not part of the repository).

    python3 invconjpull.py <the arguments of search/nonlinear/boolflux/ops/conjpull.py>

Runs the repository's ops/conjpull.py main() unchanged, in a process where
  * invshim.install() makes every AES check (core + independent verifier, aes_check, ops/common) the
    inverse S-box and the placement set NIST's pinned inverse circuits;
  * the conjugate construction and its screen are replaced by the inverse versions below.

Conjugates of the inverse.  inv = G' o inv o G with G(z) = lam z^(2^k), G'(w) = (lam w)^(2^(8-k)).
The inverse S-box is S^-1(y) = inv(Ainv (y + c)), c = 0x63 (A, Ainv: the FIPS-197 affine matrix and its
inverse, conj_lib/conj.py).  Then
    S^-1(y) = G'( S^-1( L y ) ),   L y = Lin y + cL,  Lin = A G Ainv,  cL = Lin c + c.
So from a circuit C for S^-1: inputs through the affine map L (XOR network; constants as XNOR / NOT),
C unchanged, outputs through the linear map G' (XOR network).  ANDs and middle layers are unchanged;
the build (BP top resynthesis, trb top/bottom passes) and the kernel stages are conjpull's own.
Every conjugate is checked on all 256 inputs before use; every recorded circuit passes aes_check
(both verifiers, inverse table) inside the start's A and AD.
"""
import os
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAMP = HERE.parent
sys.path.insert(0, str(CAMP / 'shim'))
os.environ['XS_INVSBOX'] = '1'
import invshim                                            # noqa: E402
invshim.install()

OPS = invshim.PKG / 'ops'
from boolflux import targets, core                        # noqa: E402
INV_TABLE = targets.aes_sbox()                            # patched: the inverse table
assert INV_TABLE[0] == 0x52

# conj_lib/conj.py asserts the FORWARD decomposition at import: import it with the forward table, then patch
_patched = targets.aes_sbox
targets.aes_sbox = invshim.forward_targets_sbox()
sys.path.insert(0, str(OPS / 'conj_lib'))
try:
    import conj as CJ                                     # noqa: E402
finally:
    targets.aes_sbox = _patched
    sys.path.remove(str(OPS / 'conj_lib'))
CJ.AES = list(INV_TABLE)                                  # resynth()'s function check
AND, XOR, XNOR, NOT = 8, 6, 9, 3


def maps(lam, k):
    G = CJ.matrix(lambda z: CJ.gmul(lam, CJ.gpow(z, 1 << k)))
    Gp = CJ.matrix(lambda w: CJ.gpow(CJ.gmul(lam, w), 1 << ((8 - k) % 8)))
    Lin = CJ.matrix(lambda y: CJ.apply(CJ.A, CJ.apply(G, CJ.apply(CJ.Ainv, y))))
    cL = CJ.apply(Lin, 0x63) ^ 0x63
    return Lin, cL, Gp


def conj_circuit_inv(c, lam, k):
    """Naive conjugate of an inverse-S-box circuit: input affine network L, C, output linear network G'."""
    Lin, cL, Gp = maps(lam, k)
    n = c.n
    gates = []
    def sid(): return n + len(gates) - 1
    u = []
    for i in range(8):                    # C's input i = byte bit 7-i of L y; new circuit input 7-j = byte bit j of y
        bit = 7 - i
        terms = [7 - j for j in range(8) if Lin[j] >> bit & 1]
        cst = cL >> bit & 1
        s = terms[0]
        for q, t in enumerate(terms[1:]):
            last = q == len(terms) - 2
            gates.append((XNOR if (last and cst) else XOR, s, t)); s = sid()
        if cst and len(terms) == 1:
            gates.append((NOT, s, s)); s = sid()
        u.append(s)
    mp = {i: u[i] for i in range(n)}
    for j, (op, a, b) in enumerate(c.gates):
        gates.append((op, mp[a], mp[b])); mp[n + j] = sid()
    old = [mp[s] for s in c.outputs]      # old output i = byte bit 7-i of S^-1(L y)
    outs = []
    for i in range(8):
        bit = 7 - i
        terms = [old[7 - j] for j in range(8) if Gp[j] >> bit & 1]
        s = terms[0]
        for t in terms[1:]:
            gates.append((XOR, s, t)); s = sid()
        outs.append(s)
    cc = core.Circuit(n, 8, gates, outs).live()
    assert cc.value_table() == INV_TABLE, 'inverse conjugate %d:%d wrong function' % (lam, k)
    return cc


CJ.conj_circuit = conj_circuit_inv

sys.path.insert(0, str(OPS))
import conjpull as CP                                      # noqa: E402
assert CP.CM.AES == INV_TABLE, 'ops/common was imported before the shim'


def screen_slice_inv(c, k, top_runs):
    """conjpull.screen_slice with the inverse's maps: top forms f -> f o Lin, outputs through G'."""
    import conj3 as C3
    assert C3.CJ is CJ
    top, outs, nl = C3.layers(c)
    rows = []
    for lam in range(1, 256):
        Lin, cL, Gp = maps(lam, k)
        urow = [sum(1 << (7 - j) for j in range(8) if Lin[j] >> (7 - i) & 1) for i in range(8)]
        ntop = []
        for t in top:
            v = 0
            for i in range(8):
                if t >> i & 1: v ^= urow[i]
            ntop.append(v)
        ct = C3.bp_cost(8, ntop, top_runs, random.Random(lam * 8 + k))
        nouts = []
        for i in range(8):
            bit = 7 - i
            v = 0
            for j in range(8):
                if Gp[j] >> bit & 1: v ^= outs[7 - j]
            nouts.append(v)
        cb = C3.paar(nouts)
        rows.append({'lam': lam, 'k': k, 'top': ct, 'bot': cb, 'sum': (ct or 99) + cb})
    return rows


CP.screen_slice = screen_slice_inv

_Rec = CP.CM.Recorder


class InvRecorder(_Rec):
    def __init__(self, out, op, tid, start, seed, command, method, params, kernel=None, t0=None):
        command = 'XS_INVSBOX=1 PYTHONPATH=%s %s %s %s' % (CAMP / 'shim', sys.executable, Path(__file__).resolve(),
                                                           ' '.join(sys.argv[1:]))
        method = ('AES INVERSE S-box: ' + method + '; run through %s (invshim: inverse-S-box checks and the NIST '
                  'inverse set; inverse conjugates S^-1(y) = G\'(S^-1(Lin y + cL)), Lin = A G Ainv)' % Path(__file__).name)
        params = dict(params, function='aes-invsbox', wrapper=str(Path(__file__).resolve()))
        super().__init__(out, op, tid, start, seed, command, method, params, kernel=kernel, t0=t0)


CP.CM.Recorder = InvRecorder

if __name__ == '__main__':
    sys.exit(CP.main(sys.argv[1:]))
