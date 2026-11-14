"""Linear gates per AND level (a linear gate's level = AND level of its output) and, per level, a
simple lower-bound-ish reference: the number of distinct non-trivial forms that level must deliver."""
import sys
from common import *
sys.path.insert(0, str(HERE))
import skeleton_e as skeleton

for f in [Path(a) for a in sys.argv[1:]]:
    c = load(f); la = levels(c); A, AD, G, GD = metrics(c)
    lin = [0] * (AD + 1); ands = [0] * (AD + 1)
    for j, (op, a, b) in enumerate(c.gates):
        L = la[c.n + j]
        if op in core.NONLINEAR_OPS: ands[L] += 1
        else: lin[L] += 1
    sk = skeleton.extract(c)
    # operand forms per AND level and their weights (terms excluding constant)
    n = c.n
    lvl = []
    for k, (L, R) in enumerate(sk['ands']):
        deps = [j for j in range(k) if ((L | R) >> (1 + n + j)) & 1]
        lvl.append(1 + max([lvl[j] for j in deps], default=0))
    w = lambda f: bin(f & ~1).count('1')
    per = {}
    for k, (L, R) in enumerate(sk['ands']):
        per.setdefault(lvl[k], []).extend([w(L), w(R)])
    print('%-46s A%d AD%d G%d GD%d  XOR per level %s  ANDs per level %s' % (f.name[:46], A, AD, G, GD, lin, ands[1:]))
    print('     operand form weights per AND level:', {k: sorted(v) for k, v in sorted(per.items())})
    print('     output form weights:', sorted(w(o) for o in sk['outputs']))
