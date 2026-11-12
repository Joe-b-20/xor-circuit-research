"""CHECK: block-monotone kste circuits closest to a given one on the local region.

usage: python3 nearest_local.py FILE LINE [TOP]
Local region = gate values with support inside {0,1,2,7} that meet block 1 or 2. Byte rotation
c -> c+r (a symmetry of MixColumns, inputs and outputs rotate together) is applied to the candidate.
"""
import os, sys
from show_tri import KSTE, desc, load, mc
from nearest_mono import FILES, valset

REG = mc.BLOCKMASK[0] | mc.BLOCKMASK[1] | mc.BLOCKMASK[2] | mc.BLOCKMASK[7]
MEET = mc.BLOCKMASK[1] | mc.BLOCKMASK[2]

def rot(v, r):
    return ((v << (8 * r)) | (v >> (32 - 8 * r))) & 0xFFFFFFFF if r else v

def local(V):
    return set(v for v in V if not (v & ~REG) and (v & MEET))

def main():
    fn, ln = sys.argv[1], int(sys.argv[2]); top = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    A = local(valset(load(fn, ln)))
    best = []
    for f in FILES:
        for i, line in enumerate(open(os.path.join(KSTE, f)), 1):
            g = mc.parse_pairs(line)
            res = mc.analyse(g)
            if res is None or not res["monotone"]:
                continue
            V0 = valset(g)
            for r in range(4):
                L = local(set(rot(v, r) for v in V0))
                best.append((len(A ^ L), len(L), f, i, r, L, g))
            best.sort(key=lambda x: x[:2]); best = best[:400]
    shown = 0
    for d, n, f, i, r, L, g in best:
        res = mc.analyse(g)
        if res is None or not res["monotone"]:
            continue
        print("%s line %d rot %d: local sym diff %d (given %d local, mono %d local)" % (f, i, r, d, len(A), n))
        print("  only given:", "; ".join(sorted(desc(v) for v in A - L)))
        print("  only mono :", "; ".join(sorted(desc(v) for v in L - A)))
        shown += 1
        if shown >= top: break

main()
