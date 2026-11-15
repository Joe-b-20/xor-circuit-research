"""Shape (B) of a 12-member GF(4)-norm layer (NOTES 7.2), filter 1 (agent H1).

Shape (B): all 5 classes, d = dim(sum D_P) = 2, sum (n_P - 1) = 7, every n_P <= 3, free class f of
Pi(gamma) with n_f in {1, 2}. D = sum D_P; by z -> lambda z (which preserves the n-block
conditions) D = <1, t>. D_P = D for n_P = 3, <delta_P> (delta_P in D \ 0) for n_P = 2, 0 for n_P = 1.
Necessary (NOTES 7.2): Y(w) = sum zeta_P^-1 w_P is injective on W0 = {(w_P) in (+)D_P :
sum w_P = 0} (dim 5). This script counts the (gamma-group, t, size assignment, deltas) passing.
usage: python3 shapeB.py"""
import itertools
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from nfast import MU5, mul, echelon
from xag import gf

FREE = {'0': 0, '17': 2, '34': 4, '51': 1, '68': 3}      # free class per gamma group (parity.txt)


def sizes_list(f):
    out = []
    for ns in itertools.product((1, 2, 3), repeat=5):
        if ns[f] not in (1, 2): continue
        if sum(n - 1 for n in ns) != 7: continue
        out.append(ns)
    return out


def main():
    inv = [gf.INV[z] for z in MU5]
    seen = set(); Ds = []
    for t in range(2, 256):
        key = frozenset((1, t, 1 ^ t))
        if key not in seen: seen.add(key); Ds.append(t)
    total = 0; passed = 0; examples = []
    for g, f in FREE.items():
        for ns in sizes_list(f):
            for t in Ds:
                Dpts = [1, t, 1 ^ t]
                small = [P for P in range(5) if ns[P] == 2]
                for deltas in itertools.product(Dpts, repeat=len(small)):
                    dl = dict(zip(small, deltas))
                    # basis of (+)D_P as list of (P, element)
                    basis = []
                    for P in range(5):
                        if ns[P] == 3: basis += [(P, 1), (P, t)]
                        elif ns[P] == 2: basis.append((P, dl[P]))
                    # W0 = kernel of sum map; compute kernel vectors as combos, then Y images
                    rows = []; kern = []
                    for i, (P, e) in enumerate(basis):
                        v, tag = e, 1 << i
                        for rv, rt in rows:
                            if v ^ rv < v: v ^= rv; tag ^= rt
                        if v: rows.append((v, tag)); rows.sort(reverse=True)
                        else: kern.append(tag)
                    Ys = []
                    for tag in kern:
                        y = 0
                        for i, (P, e) in enumerate(basis):
                            if tag >> i & 1: y ^= mul(inv[P], e)
                        Ys.append(y)
                    total += 1
                    if len(kern) == 5 and len(echelon(Ys)) == 5:
                        passed += 1
                        if len(examples) < 5: examples.append((g, ns, t, dl))
    print('shape (B) filter 1: tested %d, passed %d; examples %s' % (total, passed, examples))


if __name__ == '__main__':
    main()
