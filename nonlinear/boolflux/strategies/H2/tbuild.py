"""Build a real AES S-box circuit from a tower-model solution: umizame's 9 early products, BMP
5-AND inversion of D, and a list of last-layer members (lam, mu) acting on v = Q + gamma D.
x -> (L, R) by umizame's Appendix A masks (H = W G)."""
import sys, json, os
from pathlib import Path
import tower as TW
from tower import m4, tau, W, W2, MUL, INV16, norm, g16
import tsearch as TS
import a28parse as AP
from h2lib import build_circuit

# masks over U_j (bit j selects U_j, U_0 = msb of the byte)
LM = [0x41, 0xc6, 0x69, 0xe7]   # L bits: A0.x0, A0.x1, A1.x0, A1.x1
RM = [0x74, 0x86, 0x59, 0xd9]


def ubit(x, j): return (x >> (7 - j)) & 1


def mval(mask, x):
    s = 0
    for j in range(8):
        if mask >> j & 1: s ^= ubit(x, j)
    return s


def LR(x):
    L = sum(mval(LM[i], x) << i for i in range(4)); R = sum(mval(RM[i], x) << i for i in range(4))
    return L, R


def T256(f):
    t = 0
    for x in range(256):
        if f(x) & 1: t |= 1 << x
    return t


def build(gamma, members, name='h2-tower'):
    ands = []
    # early
    for a, b, c in TS.ROWS:
        for r in (1, W, W2):
            ands.append((T256(lambda x, a=a, r=r: tau(m4(r, TS.lam_val(a, *LR(x))))),
                         T256(lambda x, b=b, r=r: tau(m4(r, TS.lam_val(b, *LR(x)))))))
    Dx = [norm(*LR(x)) for x in range(256)]
    db = [TS.d_bits(Dx[x]) for x in range(256)]
    d = [T256(lambda x, i=i: db[x][i]) for i in range(4)]
    d0, d1, d2, d3 = d
    m1 = d0 ^ d1, d2 ^ d3
    ands.append(m1); M1 = m1[0] & m1[1]
    ands.append((d1, d2 ^ M1)); M2 = d1 & (d2 ^ M1)
    ands.append((d0 ^ M1, d3)); M3 = (d0 ^ M1) & d3
    ands.append((d2, M1 ^ M3)); M4 = d2 & (M1 ^ M3)
    ands.append((d0 ^ M2, d2 ^ M1 ^ M4))
    Qx = [INV16[D] for D in Dx]
    vx = [Qx[x] ^ MUL[gamma][Dx[x]] for x in range(256)]
    for lc, mc in members:
        lc = tuple(lc); mc = tuple(mc)
        ands.append((T256(lambda x: tau(TS.lam_val(lc, *LR(x))) ^ tau(m4(W, TS.mu_val(mc, vx[x])))),
                     T256(lambda x: tau(m4(W, TS.lam_val(lc, *LR(x)))) ^ tau(TS.mu_val(mc, vx[x])))))
    return build_circuit(8, ands, AP.Stabs, name)


if __name__ == '__main__':
    spec = json.load(open(sys.argv[1]))
    c = build(spec['gamma'], spec['members'], spec.get('name', 'h2-tower'))
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from boolflux import core
    out = sys.argv[2]
    Path(out).write_text(core.write_ncff(c, core.Model.load('nist')), encoding='utf-8')
    print('written', out, c.metrics())
