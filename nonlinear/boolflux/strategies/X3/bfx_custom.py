"""X3: run the BoolFlux CLI with extra targets (no edit of shared modules):
gfN-inv (N=3..8, x^(2^N-2)), gfN-powE (x^E), aes-bitJ-like single components trN (Tr(1/x) in GF(2^N)).
usage: bfx_custom.py <cli args...>"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", ".."))
from boolflux import targets
import gfinv
for n in range(3, 9):
    targets.BUILTIN['gf%d-inv' % n] = (n, n, (lambda n=n: gfinv.inv_table(n)), 'GF(2^%d) inversion' % n)
    def tr(n=n):
        t = gfinv.inv_table(n); out = []
        for y in t:
            s = 0; z = y
            for _ in range(n): s ^= z; z = gfinv.gmul(z, z, n)
            out.append(s & 1)
        return out
    targets.BUILTIN['gf%d-trinv' % n] = (n, 1, tr, 'Tr(1/x) in GF(2^%d)' % n)
for a in sys.argv:
    if a.startswith('gf') and '-pow' in a:
        n = int(a[2:a.index('-')]); e = int(a.split('pow')[1])
        targets.BUILTIN[a] = (n, n, (lambda n=n, e=e: gfinv.pow_table(n, e)), 'x^%d in GF(2^%d)' % (e, n))
from boolflux import cli
sys.argv = ['boolflux'] + sys.argv[1:]
cli.main()
