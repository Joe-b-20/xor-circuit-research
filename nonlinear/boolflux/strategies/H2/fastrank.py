"""Fast rank check of gen13 candidates using full quotient coordinates (T_full = bits 0..7).
usage: fastrank.py PREFIX SOLFILE -> prints indices lines of candidate sets that cover T (all 8 unit vectors)."""
import sys
full = [int(l, 16) for l in open(sys.argv[1] + '.full')]
def covers(ids):
    piv = {}
    def red(v):
        while v:
            h = v.bit_length() - 1
            if h in piv: v ^= piv[h]
            else: return v
        return 0
    for i in ids:
        v = red(full[i])
        if v: piv[v.bit_length() - 1] = v
    return all(red(1 << j) == 0 for j in range(8))
n = good = 0
out = open(sys.argv[2] + '.cov', 'w')
for ln in open(sys.argv[2]):
    if not ln.startswith('SOL'): continue
    n += 1
    ids = list(map(int, ln.split()[2:]))
    if covers(ids): good += 1; out.write(ln)
print('candidates', n, 'covering', good)
