"""Library for the rotation model Q_m (and Q_T).  Imported by the other scripts in this directory.

Indexing: input (c, j) = bit 4*j + c  (c = byte index mod 4, j = block index mod m).
Output (c, j) has index 4*j + c and mask  E_c on block j  +  s_c on block j-1,
  E_c = the three inputs of the block other than c,  s_c = inputs c and c+1 of the block.
Q_T (T an m x m 0/1 matrix given as a list of row masks): o(c,j) = E_c on block j + s_c on every
block k with T[j][k] = 1.  Q_m = Q_T for T = the cyclic shift (T[j][j-1] = 1).
Standard library only.
"""


def bit(c, j):
    return 1 << (4 * j + (c % 4))


def E(c, j):
    return bit(c + 1, j) | bit(c + 2, j) | bit(c + 3, j)


def s(c, j):
    return bit(c, j) | bit(c + 1, j)


def shift_T(m):
    return [1 << ((j - 1) % m) for j in range(m)]


def rows_T(T):
    m = len(T)
    out = []
    for j in range(m):
        for c in range(4):
            v = E(c, j)
            for k in range(m):
                if (T[j] >> k) & 1:
                    v ^= s(c, k)
            out.append(v)
    return out


def rows(m):
    return rows_T(shift_T(m))


def popcount(v):
    return bin(v).count("1")


def rank(vecs):
    basis = {}
    r = 0
    for v in vecs:
        while v:
            h = v.bit_length() - 1
            if h in basis:
                v ^= basis[h]
            else:
                basis[h] = v
                r += 1
                break
    return r


def inverse(rws, n):
    """Inverse of the n x n matrix with the given row masks (rows of the inverse as masks)."""
    a = list(rws)
    inv = [1 << i for i in range(n)]
    for col in range(n):
        p = next(i for i in range(col, n) if (a[i] >> col) & 1)
        a[col], a[p] = a[p], a[col]
        inv[col], inv[p] = inv[p], inv[col]
        for i in range(n):
            if i != col and (a[i] >> col) & 1:
                a[i] ^= a[col]
                inv[i] ^= inv[col]
    return inv


def transpose(rws, n):
    return [sum(((rws[i] >> j) & 1) << i for i in range(len(rws))) for j in range(n)]


# ---------------------------------------------------------------- circuits
def read_circuit(path):
    """Text format: first non-comment line 'n k'; then k lines 'a b' (operand signal indices;
    signals 0..n-1 are the inputs, signal n+i is gate i). '#' starts a comment."""
    lines = []
    with open(path) as f:
        for line in f:
            line = line.split("#")[0].strip()
            if line:
                lines.append(line)
    n, k = map(int, lines[0].split())
    gates = [tuple(map(int, l.split()[:2])) for l in lines[1:1 + k]]
    assert len(gates) == k
    return n, gates


def write_circuit(path, n, gates, header=""):
    with open(path, "w", newline="\n") as f:
        for h in header.splitlines():
            f.write("# " + h + "\n")
        f.write(f"{n} {len(gates)}\n")
        for a, b in gates:
            f.write(f"{a} {b}\n")


def masks(n, gates):
    vals = [1 << i for i in range(n)]
    for a, b in gates:
        assert a < len(vals) and b < len(vals)
        vals.append(vals[a] ^ vals[b])
    return vals


def computes(n, gates, targets):
    vals = set(masks(n, gates))
    return all(t in vals for t in targets)


def profile(n, gates, targets):
    """x (odd+odd), y (even+even), h (odd gates that are not outputs), number of blocks of the final
    partition, p (even signals on no odd-graph edge), rho (sum over labels of (multiplicity-1)+)."""
    vals = masks(n, gates)
    par = [popcount(v) & 1 for v in vals]
    tset = set(targets)
    x = y = oe = 0
    label_count = {}
    for gi, (a, b) in enumerate(gates):
        g = n + gi
        if par[a] and par[b]:
            x += 1
            label_count[g] = label_count.get(g, 0) + 1
        elif not par[a] and not par[b]:
            y += 1
        else:
            oe += 1
            lab = a if not par[a] else b
            label_count[lab] = label_count.get(lab, 0) + 1
    odd_gates = [n + i for i in range(len(gates)) if par[n + i]]
    h = sum(1 for g in odd_gates if vals[g] not in tset)
    evens = [n + i for i in range(len(gates)) if not par[n + i]]
    p = sum(1 for g in evens if g not in label_count)
    rho = sum(max(0, label_count.get(g, 0) - 1) for g in evens)
    # final partition
    basis = {}
    for g in evens:
        v = vals[g]
        while v:
            hb = v.bit_length() - 1
            if hb in basis:
                v ^= basis[hb]
            else:
                basis[hb] = v
                break

    def inspan(v):
        while v:
            hb = v.bit_length() - 1
            if hb not in basis:
                return False
            v ^= basis[hb]
        return True

    blocks, seen = [], set()
    for i in range(n):
        if i in seen:
            continue
        blk = [j for j in range(n) if j == i or inspan((1 << i) ^ (1 << j))]
        seen.update(blk)
        blocks.append(blk)
    return dict(G=len(gates), x=x, y=y, h=h, c=len(blocks), p=p, rho=rho, blocks=blocks)
