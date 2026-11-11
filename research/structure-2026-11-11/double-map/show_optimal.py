"""Print a few optimal extra-sets of D_T in readable form, with the final partition of each.

usage: python3 show_optimal.py "12|03|013|012" N       (N = number of non-output gates, e.g. m + eps)
Needs ./exh (gcc -O2 -o exh exh.c).  Extras are printed as sums of inputs; "h:" marks a helper.
"""
import re
import subprocess
import sys

import dmap


def name(mask, m):
    return "+".join([f"u{k}" for k in range(m) if (mask >> k) & 1] + [f"v{k}" for k in range(m) if (mask >> (m + k)) & 1])


def main():
    T = dmap.zero_diag(dmap.parse_t(sys.argv[1]))
    m = len(T)
    N = int(sys.argv[2])
    out = subprocess.run(["./exh", str(m), str(N), "1"] + [str(r) for r in T], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if not line.strip().startswith("solution"):
            continue
        toks = line.split(":", 1)[1].split()
        extras = []
        for t in toks:
            helper = t.startswith("h:")
            extras.append((helper, int(t.replace("h:", ""), 16)))
        evens = [e for hlp, e in extras if not hlp]
        basis = []
        for v in evens:
            for b in basis:
                v = min(v, v ^ b)
            if v:
                basis.append(v)

        def inspan(v):
            for b in basis:
                v = min(v, v ^ b)
            return v == 0

        n = 2 * m
        names = [f"u{k}" for k in range(m)] + [f"v{k}" for k in range(m)]
        blocks, seen = [], set()
        for i in range(n):
            if i in seen:
                continue
            blk = [j for j in range(n) if j == i or inspan((1 << i) ^ (1 << j))]
            seen.update(blk)
            blocks.append(",".join(names[j] for j in blk))
        print(line.split(":")[0].strip() + ":")
        for hlp, e in extras:
            print("    ", "helper" if hlp else "label ", name(e, m))
        print("     blocks:", " | ".join(blocks))


if __name__ == "__main__":
    main()
