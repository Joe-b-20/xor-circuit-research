"""Operands of the non-stage-1, non-middle ANDs as  Tr(A x) + g(N)  with g an arbitrary function
on K = GF(16); print A and the univariate spectrum of g on K (support e in 0..15, e = 15 meaning
the v^15 term, i.e. the indicator of v != 0), plus g(0).  usage: python3 fibre.py FILE"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xag
from xag import gf
from decomp import TRX, name

K = list(gf.SUB16)
KSTAR = [v for v in K if v]
LOGK = {}


def split(tab):
    for atab, A in TRX.items():
        r = tab ^ atab
        val = {}; ok = True
        for p in range(256):
            b = (r >> p) & 1
            if val.setdefault(xag.Nv[p], b) != b: ok = False; break
        if ok: return A, val
    return None


def kspec(val):
    """g(v) = sum_{e=0}^{15} c_e v^e on K; return {e: c_e != 0} (c_e in K)."""
    sup = {}
    g0 = val[0]
    for e in range(1, 15):
        s = 0
        for v in KSTAR:
            if val[v]: s ^= gf.power(v, (15 - e) % 15)
        if s: sup[e] = name(s)
    d0 = 0
    for v in KSTAR: d0 ^= val[v]
    if g0: sup[0] = '1'
    if d0 ^ g0: sup[15] = '1'
    return sup


if __name__ == '__main__':
    c, ands, outs, ot = xag.parse(sys.argv[1])
    for k, A in enumerate(ands):
        r = xag.role(A)
        if r in ('S1', 'MID'): continue
        out = []
        for t in (A['Lt'], A['Rt']):
            s = split(t)
            if s is None: out.append('not x+g(N)'); continue
            Ax, val = s
            out.append('A=%s g-spec %s' % (name(Ax), kspec(val)))
        print('a%d %s | %s | %s' % (k + 1, r, out[0], out[1]))
