"""X3b control of G's eval3.cover_sat: U of NIST g124 (dim 7, its own 10 stage-1 products cover it) with l = 9, 10;
U of g131 (dim 6, 9 products) with l = 9."""
import sys, time
from pathlib import Path
S = Path.home() / 'xcr-boolflux/nonlinear/boolflux/strategies'
for d in ('G', 'C', 'H1'):
    sys.path.insert(0, str(S / d))
import xag, eval3
from xag import AFFX, NC, deps
NI = Path.home() / 'xcr-boolflux/nonlinear/nist/aes-sbox'
def U_of(f):
    c, ands, outs, otabs = xag.parse(str(f))
    roles = [xag.role(A) for A in ands]
    s1 = []
    for o in outs:
        t = 0
        for k in deps(o):
            if roles[k] == 'S1': t ^= ands[k]['tab']
        s1.append(t)
    b = {}; Ub = []
    for v in list(AFFX):
        while v:
            h = v.bit_length() - 1
            if h in b: v ^= b[h]
            else: b[h] = v; break
    for t in list(NC) + s1:
        v = t
        while v:
            h = v.bit_length() - 1
            if h in b: v ^= b[h]
            else: b[h] = v; Ub.append(t); break
    return Ub
for name, ls in (('aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt', (9, 10)), ('aes-sbox-a28-ad4-g131-gd31-xx103-43.circ.txt', (9,))):
    Ub = U_of(NI / name)
    for l in ls:
        t0 = time.time(); ok, pairs = eval3.cover_sat(Ub, l, float(sys.argv[1]) if len(sys.argv) > 1 else 50)
        print(name[:24], 'dimU', len(Ub), 'l', l, '->', ok, round(time.time() - t0, 1), 's', flush=True)
