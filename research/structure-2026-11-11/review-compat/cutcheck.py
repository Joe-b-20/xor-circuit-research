"""CHECK (reviewer's own classification): at primal block k of circuit FILE.json report
near = f + h, far = |P| + e, e, exits, distinct labels, rank of labels, dim W, whether span(labels) >= W,
and whether a sub-basis of dim W labels spans W (tau_min = dim W then)."""
import json, sys
from mycheck import rows

def rank(vs):
    b = {}
    for v in vs:
        while v:
            h = v.bit_length() - 1
            if h in b: v ^= b[h]
            else: b[h] = v; break
    return len(b)

g = json.load(open(sys.argv[1])); k = int(sys.argv[2])
bk = sum(1 << (8 * c + k) for c in range(4))
v = [1 << i for i in range(32)]
for a, b in g: v.append(v[a] ^ v[b])
om = lambda x: v[x] & bk
seen = {v[i] & bk for i in range(32) if v[i] & bk}
f = h = e = P = ex = 0; labs = []
for gi, (a, b) in enumerate(g):
    x = 32 + gi
    if om(x) == 0:
        P += 1
        if om(a) or om(b): ex += 1
    elif (om(a) == 0) != (om(b) == 0):
        e += 1; labs.append(v[a] if om(a) == 0 else v[b])
    elif om(x) in seen: h += 1
    else: seen.add(om(x)); f += 1
R = rows()
W = [r & ~bk for r in R if r & bk]
dW = rank(W)
L = sorted(set(labs))
span_ok = rank(L + W) == rank(L)
print("block %d: f %d h %d near %d | P %d e %d far %d | exits %d | labels %d distinct %d rank %d | dimW %d | span(labels)>=W %s"
      % (k, f, h, f + h, P, e, P + e, ex, len(labs), len(L), rank(L), dW, span_ok))
if span_ok and len(L) == dW:
    print("  tau_min = dim W = %d, sigma = e - tau_min = %d" % (dW, e - dW))
