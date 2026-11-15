import sys
sys.path.insert(0, '.')
import s1lib as L, s1search
c = L.load(sys.argv[1]); n = c.n
fs, T, lg, la = s1search.coords(c)
ands = [n + j for j, g in enumerate(c.gates) if g[0] in L.core.NONLINEAR_OPS]
g0 = 0
for s in ands[:5]: g0 ^= T[s]
g0n = g0 ^ (L.ONES if g0 & 1 else 0)
print('group a0..a4 in fs:', [g0n == f for f in fs])
for k, f in enumerate(fs):
    print(k, 'deg', L.deg(f), 'quad', format(L.quad(f), '028b'))
print('g0 quad', format(L.quad(g0), '028b'))
for s in ands[:5]:
    op, a, b = c.gates[s - n]
    print(s, lg[s], L.deg(T[a]), L.deg(T[b]), format(L.quad(T[s]), '028b'))
