"""Classify all single-product fixes for AD4L + AD5M + AD4F (missing 1 dim)."""
import glob, sys
import a28parse as AP
from fix1 import search, dedupe_O
D = '../../../nist/aes-sbox/'
files = sorted(glob.glob(D + 'aes-sbox-a28-ad4-*')) + sorted(glob.glob(D + 'aes-sbox-a28-ad5-*'))
_, A5 = AP.load(sorted(glob.glob(D + 'aes-sbox-a28-ad5-g124*'))[0])
M5 = [A['out'] for A in A5 if A['stage'] == 'M']
Obase = dedupe_O([AP.ONE] + AP.BITS + AP.Ntabs + AP.ntabs)
O2 = dedupe_O(Obase + M5)
for f in files[:11]:
    _, A4 = AP.load(f)
    L4 = [A['out'] for A in A4 if A['stage'] == 'L']
    F4 = [A['out'] for A in A4 if A['stage'] == 'F']
    for oname, O in (('O', Obase), ('O2', O2)):
        d, sols = search(L4 + M5 + F4, O, maxsol=10**9, verbose=False)
        cls = {}
        for l, m, lt, mt in sols:
            xl = bool(l & 0x1fe); xm = bool(m & 0x1fe)
            key = ('x' if xl else '') + ('N' if l >> 9 else '') + '*' + ('x' if xm else '') + ('N' if m >> 9 else '')
            cls[key] = cls.get(key, 0) + 1
        print(f.split('/')[-1][:32], oname, 'miss', d, 'nsol', len(sols), cls, flush=True)
