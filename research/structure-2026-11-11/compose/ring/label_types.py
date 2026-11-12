"""CHECK: label types at single-group ring cuts of a recorded circuit.
For group k: x = w^(k+1), y = w^(k-1). Each label printed as (x-part, y-part, other groups present?),
with first-gate omegas outside the 8 targets {E_i, p_i} listed.
Usage: python3 label_types.py CIRCUIT M
"""
import sys
from ring_cuts import read, mirror, E4


def main():
    path, M = sys.argv[1], int(sys.argv[2])
    n, gates = read(path)
    _, red = mirror(n, gates, M, "fwd")
    targets = set(E4(c) for c in range(4)) | set((1 << ((c - 1) % 4)) | (1 << c) for c in range(4))
    b = lambda v: format(v, "04b")[::-1]
    for k in range(M):
        low = 15 << (4 * k)
        sh = lambda v, j: (v >> (4 * (j % M))) & 15
        first = set(1 << (4 * k + i) for i in range(4))
        extra, labs = [], []
        for v, a, c in red:
            om, oa, oc = v & low, a & low, c & low
            if om == 0:
                continue
            if om in first:
                if (oa == 0) != (oc == 0):
                    lab = a if oa == 0 else c
                    other = any(sh(lab, j) for j in range(M) if j % M not in ((k + 1) % M, (k - 1) % M))
                    labs.append("%s/%s%s" % (b(sh(lab, k + 1)), b(sh(lab, k - 1)), "+" if other else ""))
            else:
                first.add(om)
                if (om >> (4 * k)) not in targets:
                    extra.append(b(om >> (4 * k)))
        print("group %d: extra first-gate omegas %s; labels x/y: %s" % (k, extra, " ".join(labs)))


if __name__ == "__main__":
    main()
