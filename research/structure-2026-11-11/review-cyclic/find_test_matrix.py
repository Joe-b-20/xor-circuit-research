"""Find 7x7 matrices X with X and X^T 'clean' (rows and columns odd, weight >= 3) and L_cyc(X) < L(X).
Method: random 10-gate circuits computing an invertible B; X = B^-1; exact L, L_cyc of X via ./lmin."""
import random, subprocess, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
n = 7
def rank_f2(rows):
    basis = {}; r = 0
    for v in rows:
        while v:
            h = v.bit_length() - 1
            if h in basis: v ^= basis[h]
            else: basis[h] = v; r += 1; break
    return r
def inverse(B):
    # Gauss-Jordan on rows: [B | I]
    rows = [(B[i], 1 << i) for i in range(n)]
    for c in range(n):
        p = next(i for i in range(c, n) if (rows[i][0] >> c) & 1)
        rows[c], rows[p] = rows[p], rows[c]
        for i in range(n):
            if i != c and (rows[i][0] >> c) & 1:
                rows[i] = (rows[i][0] ^ rows[c][0], rows[i][1] ^ rows[c][1])
    return [rows[i][1] for i in range(n)]
def transpose(A):
    return [sum(((A[i] >> j) & 1) << i for i in range(n)) for j in range(n)]
def clean(X):
    for r in X + transpose(X):
        w = bin(r).count('1')
        if w % 2 == 0 or w < 3: return False
    return True
rng = random.Random(int(sys.argv[1]) if len(sys.argv) > 1 else 5)
found = 0; tried = 0
while found < int(sys.argv[2] if len(sys.argv) > 2 else 2) and tried < 400:
    sig = [1 << i for i in range(n)]
    while len(sig) < n + 10:
        a, b = rng.sample(sig, 2)
        v = a ^ b
        if v not in sig: sig.append(v)
    gates = sig[n:]
    B = rng.sample(gates, n)
    if rank_f2(B) < n: continue
    X = inverse(B)
    if not clean(X): continue
    tried += 1
    out = subprocess.run([os.path.join(HERE, 'lmin'), str(n), '3', '-1'] + [str(x) for x in X],
                         capture_output=True, text=True).stdout
    cyc = circ = None
    for line in out.splitlines():
        if line.startswith('k='):
            d = dict(kv.split('=') for kv in line.split())
            if cyc is None and int(d['cyclic']) > 0: cyc = int(d['size'])
            if circ is None and int(d['circuit']) > 0: circ = int(d['size'])
    if cyc is not None and circ is None:
        found += 1
        print("FOUND X =", X, "L_cyc =", cyc, "L > 10", flush=True)
print("tried", tried)
