"""Random 7x7 matrices B computed by a 10-gate circuit, with all rows and columns of odd weight >= 3.
Prints B and its exact L_cyc / L (k <= 3 extras) so that audit_test.py can use B and B^T."""
import random, subprocess, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
n = 7
def transpose(A):
    return [sum(((A[i] >> j) & 1) << i for i in range(n)) for j in range(n)]
def clean(X):
    if len(set(X)) < n: return False
    for r in X + transpose(X):
        w = bin(r).count('1')
        if w % 2 == 0 or w < 3: return False
    return len(set(transpose(X))) == n
rng = random.Random(int(sys.argv[1]))
want = int(sys.argv[2])
got = 0
while got < want:
    sig = [1 << i for i in range(n)]
    while len(sig) < n + 10:
        a, b = rng.sample(sig, 2)
        v = a ^ b
        if v not in sig: sig.append(v)
    B = rng.sample(sig[n:], n)
    if not clean(B): continue
    out = subprocess.run([os.path.join(HERE, 'lmin'), str(n), '3', '3'] + [str(x) for x in B],
                         capture_output=True, text=True).stdout
    res = {}
    ncirc_min = nnon_min = 0
    for line in out.splitlines():
        if line.startswith('k='):
            d = dict(kv.split('=') for kv in line.split())
            res[int(d['k'])] = (int(d['cyclic']), int(d['circuit']))
    lc = next((k for k in sorted(res) if res[k][0] > 0), None)
    l = next((k for k in sorted(res) if res[k][1] > 0), None)
    noncirc3 = sum(1 for line in out.splitlines() if line.startswith('C') and line.endswith('noncirc'))
    print("B =", ' '.join(map(str, B)), " kmin_cyc =", lc, " kmin_circ =", l, " noncircuit cyclic sets at k=3:", noncirc3, flush=True)
    got += 1
