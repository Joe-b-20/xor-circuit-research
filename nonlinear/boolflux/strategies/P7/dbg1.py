import sys
sys.path.insert(0, '.')
import s1lib as L, bsel
c = L.load(sys.argv[1])
T, lg, la, Ys, Ylev = bsel.front_info(c)
print(len(Ys), Ylev, [L.deg(y) for y in Ys], [bin(y).count('1') for y in Ys])
basis = [Y & L.VAR[l] for Y in Ys for l in range(8)] + [L.ONES]
print('rank-check YX+1 per output:', [bsel.gauss_solve(basis, T[o]) is not None for o in c.outputs])
basis2 = basis + list(Ys) + L.VAR[:8]
# dependencies?
print('dep YX+Y+X+1:', len(basis2), [bsel.gauss_solve(basis2[:k], basis2[k]) is not None for k in range(len(basis2))].count(True))
