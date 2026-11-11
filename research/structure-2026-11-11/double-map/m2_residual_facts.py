"""Finite facts about M2 used in step 4 of the proof of Theorem D (REPORT.md), printed for inspection.

usage: python3 m2_residual_facts.py

For H = u3 + w7 and H = u3 + w2 (the other two exceptional masks are their images under u3 <-> v3):
  (a) the triples of boundary points with XOR H;
  (b) for every output of sheets 3 and 4, the zero-sum 4-subsets of B + {H} that contain it;
  (c) every difference mask carried by at least three disjoint pairs of B + {H}, with its pairs.
Also (d): the zero-sum 4-subsets of B itself, by type (8 sheet relations, 6 x 4 coincidence relations).
"""
import itertools

import geom

M = 8
T = geom.m2_T()
B = geom.boundary(T)
NAME = {}
for k in range(M):
    NAME[B[k]] = f"u{k}"
    NAME[B[M + k]] = f"v{k}"
    NAME[B[2 * M + k]] = f"o{k}"
    NAME[B[3 * M + k]] = f"o'{k}"


def vname(v):
    """Name of an even mask: element of W as sum of w_k, else hex."""
    lo, hi = v & 0xFF, v >> 8
    if lo == hi:
        return "+".join(f"w{k}" for k in range(M) if (lo >> k) & 1) or "0"
    return f"0x{v:04x}"


def foursets(points):
    idx = {}
    for a, b in itertools.combinations(points, 2):
        idx.setdefault(a ^ b, []).append((a, b))
    out = set()
    for d, lst in idx.items():
        for (p, q) in itertools.combinations(lst, 2):
            s = frozenset(p + q)
            if len(s) == 4:
                out.add(s)
    return out, idx


def main():
    fs, _ = foursets(B)
    sheet = [s for s in fs if len({NAME[x][-1] for x in s}) == 1]
    print(f"(d) zero-sum 4-subsets of B: {len(fs)} = {len(sheet)} sheet relations + {len(fs) - len(sheet)} coincidence relations")
    for label, H in (("u3+w7", B[3] ^ (0x8080)), ("u3+w2", B[3] ^ (0x0404))):
        NAME[H] = "H"
        pts = B + [H]
        print(f"\nH = {label} = 0x{H:04x}")
        triples = [t for t in itertools.combinations(B, 3) if t[0] ^ t[1] ^ t[2] == H]
        print(" (a) triples:", "  ".join("{" + ",".join(NAME[x] for x in t) + "}" for t in triples))
        fs, idx = foursets(pts)
        for out in ("o3", "o'3", "o4", "o'4"):
            o = next(p for p in B if NAME[p] == out)
            sets = [s for s in fs if o in s]
            print(f" (b) 4-subsets containing {out}:", "  ".join("{" + ",".join(sorted(NAME[x] for x in s)) + "}" for s in sets))
        print(" (c) differences with at least three pairwise disjoint pairs:")
        for d, lst in sorted(idx.items()):
            if len(lst) >= 3:
                print(f"      {vname(d):<12}", "  ".join("(" + NAME[a] + "," + NAME[b] + ")" for a, b in lst))
        del NAME[H]


if __name__ == "__main__":
    main()
