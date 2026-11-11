"""Section 3 algebra checks for MixColumns (standard library only).

Input index 8c + j = bit j of byte c; a mask mu acts on an input vector b by the bit dot product.
"""
from lib import CIRC, read_matrix, par, wt, Span

rows, n = read_matrix(CIRC / "aes-mixcolumns/aes-mixcolumns.mat.txt")


def gmul(a, b):
    r = 0
    while b:
        if b & 1:
            r ^= a
        a <<= 1
        if a & 0x100:
            a ^= 0x11B
        b >>= 1
    return r


def vec_to_bytes(v):
    return [(v >> (8 * c)) & 0xFF for c in range(4)]


def bytes_to_vec(bs):
    return sum(b << (8 * c) for c, b in enumerate(bs))


def rmul(a, b):
    """Product in F_256[y]/(y^4 + 1); elements are coefficient lists [a0, a1, a2, a3]."""
    r = [0, 0, 0, 0]
    for i in range(4):
        for k in range(4):
            r[(i + k) % 4] ^= gmul(a[i], b[k])
    return r


def matrix_of(f):
    """Rows of the 32x32 matrix of the F_2-linear map f on 32-bit ints (row o = output bit o)."""
    cols = [f(1 << i) for i in range(32)]
    return [sum(((cols[i] >> o) & 1) << i for i in range(32)) for o in range(32)]


# 1. field-arithmetic MixColumns equals the repository matrix
def mc(v):
    b = vec_to_bytes(v)
    return bytes_to_vec([gmul(2, b[c]) ^ gmul(3, b[(c + 1) % 4]) ^ b[(c + 2) % 4] ^ b[(c + 3) % 4] for c in range(4)])


M = matrix_of(mc)
print("1. field-arithmetic MixColumns == repository matrix:", M == rows)

# 2. formula (3.1)
def blk(j, pattern):
    return sum(1 << (8 * c + j) for c in range(4) if pattern[c])


def E(c):
    return [0 if k == c else 1 for k in range(4)]


def s(c):
    return [1 if k in (c, (c + 1) % 4) else 0 for k in range(4)]


formula = []
for c in range(4):
    for j in range(8):
        v = blk(j, E(c))
        if j >= 1:
            v ^= blk(j - 1, s(c))
            if j in (1, 3, 4):
                v ^= blk(7, s(c))
        else:
            v ^= blk(7, s(c))
        formula.append(v)
print("2. formula (3.1) equals the repository row for all 32 outputs:", formula == rows,
      "; mismatching rows:", [i for i in range(32) if formula[i] != rows[i]])

# 3. ring element: which a(y) gives M, under the two byte <-> R conventions
def mult_map(a, rev):
    def f(v):
        b = vec_to_bytes(v)
        poly = [b[(-c) % 4] for c in range(4)] if rev else b  # rev: b(y) = sum b_c y^(-c)
        p = rmul(a, poly)
        out = [p[(-c) % 4] for c in range(4)] if rev else p
        return bytes_to_vec(out)
    return f


for a, name in (([2, 3, 1, 1], "2+3y+y^2+y^3"), ([2, 1, 1, 3], "2+y+y^2+3y^3")):
    for rev in (False, True):
        ok = matrix_of(mult_map(a, rev)) == rows
        print(f"3. M == multiplication by {name} with b(y) = sum b_c y^({'-' if rev else ''}c): {ok}")

one_plus_y = [1, 1, 0, 0]
p = [1, 0, 0, 0]
for _ in range(4):
    p = rmul(p, one_plus_y)
print("4. (1+y)^4 =", p, "(y^4 + 1 = 0 in R, so (1+y)^4 = 0 there; in F_256[y] it equals y^4+1 since char 2)")
lhs = rmul(one_plus_y, [3, 0, 1, 0])
lhs[0] ^= 1
print("5. 1 + (1+y)(3+y^2) =", lhs, "== [2,3,1,1]:", lhs == [2, 3, 1, 1])
inv2 = next(t for t in range(256) if gmul(2, t) == 1)
u = [3, 0, 1, 0]
w = rmul([1, 0, 0, 0], [1, 0, 0, 0])
cand = rmul([inv2, 0, 0, 0], [1 ^ gmul(inv2, 1), 0, gmul(inv2, 1), 0])  # 2^-1 (1 + (1+y)^2 / 2)
print("6. 3+y^2 is a unit: inverse", cand, "check", rmul(u, cand))

# 7. flag
def image_space(a):
    sp = Span()
    f = mult_map(a, False)
    for i in range(32):
        sp.add(f(1 << i))
    return sp


def annihilator(sp):
    # masks mu with mu . v = 0 for all v in sp
    basis = list(sp.basis.values())
    res = Span()
    # brute: solve linear system by Gaussian elimination over 32 unknowns
    rows_ = basis[:]
    # nullspace of the matrix with rows = basis vectors
    pivots = {}
    red = []
    for r in rows_:
        for pc, pr in pivots.items():
            if (r >> pc) & 1:
                r ^= pr
        if r:
            pc = r.bit_length() - 1
            for k in list(pivots):
                if (pivots[k] >> pc) & 1:
                    pivots[k] ^= r
            pivots[pc] = r
    free = [i for i in range(32) if i not in pivots]
    for fcol in free:
        v = 1 << fcol
        for pc, pr in pivots.items():
            if (pr >> fcol) & 1:
                v |= 1 << pc
        res.add(v)
    for b in basis:
        for r in res.basis.values():
            assert not par(b & r)
    return res


powers = {0: [1, 0, 0, 0]}
for j in range(1, 5):
    powers[j] = rmul(powers[j - 1], one_plus_y)
I = {j: image_space(powers[j]) for j in range(5)}
print("7. dim_F2 (1+y)^j R for j = 0..4:", [I[j].dim() for j in range(5)])
A = {j: annihilator(I[j]) for j in range(4)}
print("   dim of masks vanishing on (1+y)^j R, j = 0..3:", [A[j].dim() for j in range(4)])
print("   record's W_k := masks vanishing on (1+y)^(4-k) R has dims k=1,2,3:", [A[4 - k].dim() for k in (1, 2, 3)])


def block_space(allowed):
    sp = Span()
    for j in range(8):
        for pat in allowed:
            sp.add(blk(j, pat))
    return sp


B3 = block_space([[1, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 1]])
B2 = block_space([[1, 0, 1, 0], [0, 1, 0, 1]])
B1 = block_space([[1, 1, 1, 1]])


def same(s1, s2):
    return s1.dim() == s2.dim() and all(v in s2 for v in s1.basis.values())


print("   block descriptions: dims", B1.dim(), B2.dim(), B3.dim())
for k, Bk in ((1, B1), (2, B2), (3, B3)):
    print(f"   block W_{k}: == ann((1+y)^{4 - k} R)? {same(Bk, A[4 - k])};  == ann((1+y)^{k} R)? {same(Bk, A[k])};"
          f"  == (1+y)^{4 - k} R itself? {same(Bk, I[4 - k])}")

# 8. action on quotients, for M (on input vectors) and for the mask action mu -> mu M (= M^T mu)
def apply(rows_, v):
    return sum(par(r & v) << o for o, r in enumerate(rows_))


MT = [sum(((rows[o] >> i) & 1) << o for o in range(32)) for i in range(32)]
full = Span()
for i in range(32):
    full.add(1 << i)
flag = [Span(), B1, B2, B3, full]
for name, mat in (("M", rows), ("M^T (mask action)", MT)):
    res = []
    for k in range(1, 5):
        ok = all((apply(mat, v) ^ v) in flag[k - 1] for v in flag[k].basis.values())
        res.append(ok)
    print(f"8. {name}: (A - 1) W_k subset W_(k-1) for k = 1, 2, 3, 4 (W_4 = all):", res)
