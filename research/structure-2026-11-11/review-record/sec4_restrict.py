"""Section 4, first bullet: restriction of MixColumns circuits to inputs (u, v, u, v).

Restricted mask of mu: u_j-coordinate = mu(0,j) + mu(2,j), v_j-coordinate = mu(1,j) + mu(3,j);
it is zero iff mu lies in W2. For each recorded MixColumns circuit, count the gates that disappear
when the restricted circuit is cleaned up (restricted value zero, equal to a restricted input, or
equal to the restricted value of an earlier signal), split into output duplicates and others.
Also: the section-1 bound for M2 at the all-ones point (minimum weight of the M2 graph code by
full enumeration of 2^16 inputs), which bounds L(M2) from below.
"""
from lib import CIRC, load, par, wt, NAME


def restrict(mu):
    r = 0
    for j in range(8):
        r |= (((mu >> j) & 1) ^ ((mu >> (16 + j)) & 1)) << j
        r |= (((mu >> (8 + j)) & 1) ^ ((mu >> (24 + j)) & 1)) << (8 + j)
    return r


d = CIRC / "aes-mixcolumns"
for circ in sorted(d.glob("*.circ.txt"), key=lambda p: int(NAME.search(p.name).group(1))):
    n, gates, outs, vals, rows = load(circ, d / "aes-mixcolumns.mat.txt")
    outset = set(outs)
    seen = {1 << j for j in range(16)}  # restricted inputs u_j, v_j
    gone_out = gone_zero = gone_other = 0
    for o, a, b in gates:
        r = restrict(vals[o])
        if r == 0:
            gone_zero += 1
        elif r in seen:
            if o in outset:
                gone_out += 1
            else:
                gone_other += 1
        seen.add(r)
    total = gone_out + gone_zero + gone_other
    print(f"{circ.name}: G={len(gates)} disappear={total} (zero/W2: {gone_zero}, duplicate outputs: {gone_out}, "
          f"other duplicates or inputs: {gone_other}); restricted circuit has {len(gates) - total} gates")

# M2 rows (outputs out0 bits, out1 bits) from the repository matrix
_, _, _, _, rows = load(d / "aes-mixcolumns-xor88-depth5.circ.txt", d / "aes-mixcolumns.mat.txt")
m2 = [restrict(r) for r in rows[:16]]
cols = [sum(((m2[o] >> i) & 1) << o for o in range(16)) for i in range(16)]
best = 99
for u in range(1, 1 << 16):
    im = 0
    i, v = 0, u
    while v:
        if v & 1:
            im ^= cols[i]
        v >>= 1
        i += 1
    best = min(best, wt(u) + wt(im))
print("M2: rows odd:", all(par(r) for r in m2), " columns odd:", all(par(c) for c in cols),
      " min graph-code weight:", best, " => c(1) <=", 32 // best,
      " => L(M2) >= 16 + 16 - c(1) =", 32 - 32 // best)
