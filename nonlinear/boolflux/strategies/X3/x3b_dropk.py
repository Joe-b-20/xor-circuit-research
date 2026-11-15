"""X3b x3b_dropk.py FILE KMAX: for every set W of k <= KMAX top products, d_b(W) = missing output dims after
dropping W with stage 1 free (base span(1, x, N, n, middle, all x-quadratics) + rest). A window with
d_b(W) <= k - 1 is a slack window: replacing W by d_b(W) products would save k - d_b(W) ANDs.
Prints, per k, the histogram of d_b and the slack windows."""
import sys, itertools
from pathlib import Path
S = Path.home() / 'xcr-boolflux/nonlinear/boolflux/strategies'
for d in ('G', 'C', 'H1'):
    sys.path.insert(0, str(S / d))
import xag, gf
from xag import ONES, AFFX, NC, nC
QUAD = [gf.X[i] & gf.X[j] for i in range(8) for j in range(i + 1, 8)]
T = [gf.bit_table(gf.INV, k) for k in range(8)]
f = sys.argv[1]; KMAX = int(sys.argv[2])
c, ands, outs, otabs = xag.parse(f)
roles = [xag.role(A) for A in ands]
mid = [A['tab'] for A, r in zip(ands, roles) if r == 'MID']
top = [A['tab'] for A, r in zip(ands, roles) if r not in ('S1', 'MID')]
# reduce everything modulo the fixed base once, then work in the quotient (small ints)
B = {}
def red(v):
    for h in sorted(B, reverse=True):
        if (v >> h) & 1: v ^= B[h]
    return v
for v in [ONES] + list(gf.X) + list(NC) + list(nC) + mid + QUAD:
    v = red(v)
    if v: B[v.bit_length() - 1] = v
tq = [red(t) for t in top]; Tq = [red(t) for t in T]
def rank(vs):
    b = {}
    for v in vs:
        while v:
            h = v.bit_length() - 1
            if h in b: v ^= b[h]
            else: b[h] = v; break
    return len(b)
assert rank(tq + Tq) == rank(tq)
print(Path(f).name, 'top', len(top))
MIN = {}
for k in range(1, KMAX + 1):
    hist = {}; slack = []
    for W in itertools.combinations(range(len(top)), k):
        X = [t for i, t in enumerate(tq) if i not in W]
        d = rank(X + Tq) - rank(X)
        hist[d] = hist.get(d, 0) + 1
        if d <= k - 1: slack.append((W, d))
        if d <= k - 2: print("  slack-2 window", W, d)
    print(' k=%d d_b histogram %s; slack windows (d_b <= k-1): %d %s' % (k, dict(sorted(hist.items())), len(slack), slack[:12]))
    # minimal slack windows: no proper sub-window is a slack window of the same slack
    if len(sys.argv) > 3:
        prev = MIN.setdefault('all', [])
        mins = [(W, d) for W, d in slack if not any(set(V) < set(W) and (len(W) - d) <= (len(V) - e) for V, e in prev)]
        prev.extend(slack)
        print('   minimal slack windows k=%d: %s' % (k, mins))
