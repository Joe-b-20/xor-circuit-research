"""P7: dump the GD10 inversion sub-problem (Y tables over the 4 N-coordinates) to JSON."""
import json, sys
sys.path.insert(0, '.')
import s1lib as L, bopt, invsub
c = L.load(sys.argv[1]); fsigs = [int(x) for x in sys.argv[2].split(',')]
T, lg, la, base = bopt.base_front(c)
ys = [b[2] for b in base]
sub = invsub.extract(c, fsigs, ys)
Y = [0] * 4
for r in range(16):
    v = [(r >> k) & 1 for k in range(4)]
    for (op, a, b) in sub.gates:
        v.append(L.core.op_apply(op, v[a], v[b], 1))
    for k, o in enumerate(sub.outputs):
        Y[k] |= v[o] << r
# consistency with the full circuit: for every x, Y_k(f(x)) == T[ys[k]](x)
for x in range(256):
    r = sum(((T[f] >> x) & 1) << k for k, f in enumerate(fsigs))
    for k in range(4):
        assert ((Y[k] >> r) & 1) == ((T[ys[k]] >> x) & 1)
json.dump({'circuit': sys.argv[1], 'fsigs': fsigs, 'ysigs': ys, 'Y': Y}, open(sys.argv[3], 'w'))
print('Y', [format(y, '016b') for y in Y], 'sub G', len(sub.gates))
