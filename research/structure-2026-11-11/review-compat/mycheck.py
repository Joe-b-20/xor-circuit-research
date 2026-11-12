"""CHECK (reviewer's own code, no repo imports): MixColumns rows, circuit validity, reducedness, waste at block k.
usage: python3 mycheck.py FILE.json [k ...]  (gate list of pairs of signal indices, inputs 0..31)."""
import json, sys

def gmul(a, b):
    r = 0
    while b:
        if b & 1: r ^= a
        a <<= 1
        if a & 0x100: a ^= 0x11b
        b >>= 1
    return r

def rows():
    out = []
    M = [[2, 3, 1, 1], [1, 2, 3, 1], [1, 1, 2, 3], [3, 1, 1, 2]]
    for i in range(4):
        for t in range(8):
            m = 0
            for c in range(4):
                for j in range(8):
                    if gmul(1 << j, M[i][c]) >> t & 1: m |= 1 << (8 * c + j)
            out.append(m)
    return out

def run(g, ks):
    v = [1 << i for i in range(32)]
    for a, b in g:
        assert a < len(v) and b < len(v)
        v.append(v[a] ^ v[b])
    R = rows()
    ok = all(r in set(v[32:]) for r in R)
    red = 0 not in v and len(set(v)) == len(v)
    print("n=%d computes=%s reduced=%s" % (len(g), ok, red))
    for k in ks:
        bk = sum(1 << (8 * c + k) for c in range(4))
        triv = {0} | {(1 << i) for i in range(32) if not (1 << i) & bk}
        new = {x & ~bk for x in v[32:]} - triv
        print("  block %d: waste %d, R %d" % (k, len(g) - len(new), len(new)))
    return v

if __name__ == "__main__":
    g = json.load(open(sys.argv[1]))
    run(g, [int(x) for x in sys.argv[2:]] or range(8))
