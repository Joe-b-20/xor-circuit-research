"""Stage structure of the published AES circuits: where the intrinsic GF(2^4) interface spaces
(norm N = x^17, N^-1, u = N + N^-1, x^-1) first appear, and how many ANDs/gates precede them."""
import sys
from common import *

VN = fn_tables(lambda x: gpow(x, 17))
VNI = fn_tables(lambda x: gpow(gpow(x, 17), 14) if x else 0)
VU = fn_tables(lambda x: gpow(x, 17) ^ (gpow(gpow(x, 17), 14) if x else 0))
VXI = fn_tables(lambda x: gpow(x, 254))
SPACES = {'N': Span(VN), 'Ninv': Span(VNI), 'u': Span(VU), 'xinv': Span(VXI)}
for k, s in SPACES.items():
    pass

files = [Path(a) for a in sys.argv[1:]] or published_files()
for f in files:
    c = load(f)
    if not correct(c): print('BAD', f.name); continue
    tabs = c.tables(); la = levels(c)
    A, AD, G, GD = metrics(c)
    out = []
    for k, sp in SPACES.items():
        # signals (non-constant) lying in the space; dimension spanned as gates go
        acc = Span(); first_full = None; members = []
        for j in range(len(c.gates)):
            s = c.n + j; t = tabs[s]
            if t in sp and t not in (0, ONES):
                members.append(s)
                acc.add(t)
                if acc.dim() == 5 and first_full is None:
                    first_full = j
        if first_full is None:
            out.append('%s:%d/4' % (k, acc.dim() - 1))
        else:
            ands_before = sum(1 for g in c.gates[:first_full + 1] if g[0] in core.NONLINEAR_OPS)
            out.append('%s:full@g%d(A%d,lvl%d,m%d)' % (k, first_full, ands_before, la[c.n + first_full], len(members)))
    lv = [0] * (AD + 1)
    for j, g in enumerate(c.gates):
        if g[0] in core.NONLINEAR_OPS: lv[la[c.n + j]] += 1
    print('%-48s A%d AD%d G%d GD%d  ands/lvl %s  %s' % (f.name[:48], A, AD, G, GD, lv[1:], ' '.join(out)))
