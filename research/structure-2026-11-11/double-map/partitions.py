"""Valid partitions of the inputs of a double map (Lemma 2.2 of the mixcolumns-lb75 proof).

usage: python3 partitions.py m2 [min_blocks]      (default min_blocks = m - 1)
       python3 partitions.py "1|0|3|02" [min_blocks]

A partition of the 2m inputs is valid if every output row has odd weight on exactly one block; the
final partition of every circuit is valid.  Depth-first search over the pairs (u_k, v_k) in an order in
which the rows become checkable early; a branch is cut when the number of blocks can no longer reach
min_blocks.  Prints the number of valid partitions by number of blocks and lists those with the maximum.
"""
import sys

import dmap
import geom


def valid_partitions(T, min_blocks):
    m = len(T)
    T = dmap.zero_diag(T)
    rows = dmap.dmap_rows(T)
    n = 2 * m
    # order of pairs: greedy so that rows complete early
    order = []
    left = set(range(m))
    done = set()

    def need(j):
        return {j} | {k for k in range(m) if (T[j] >> k) & 1}

    while left:
        best = min(left, key=lambda k: (min(len(need(j) - done - {k}) for j in range(m) if k in need(j)), k))
        order.append(best)
        done.add(best)
        left.discard(best)
    inputs = []
    for k in order:
        inputs += [k, m + k]
    pos = {i: p for p, i in enumerate(inputs)}
    # row r is checkable after position max(pos of its support)
    check_at = [[] for _ in range(n)]
    for r in rows:
        supp = [i for i in range(n) if (r >> i) & 1]
        check_at[max(pos[i] for i in supp)].append(supp)
    block = [None] * n
    out = []

    def rec(p, nblocks):
        if nblocks + (n - p) < min_blocks:
            return
        if p == n:
            out.append((nblocks, tuple(block)))
            return
        i = inputs[p]
        for b in range(nblocks + 1):
            block[i] = b
            ok = True
            for supp in check_at[p]:
                par = {}
                for s in supp:
                    par[block[s]] = par.get(block[s], 0) ^ 1
                if sum(par.values()) != 1:
                    ok = False
                    break
            if ok:
                rec(p + 1, max(nblocks, b + 1))
        block[i] = None

    rec(0, 0)
    return out


def main():
    arg = sys.argv[1]
    T = geom.m2_T() if arg == "m2" else dmap.parse_t(arg)
    m = len(T)
    mb = int(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else m - 1
    vp = valid_partitions(T, mb)
    if "--dump" in sys.argv:
        # file for exh_part: "P n" then one line of block labels per partition; also print the T rows
        path = sys.argv[sys.argv.index("--dump") + 1]
        with open(path, "w", newline="\n") as f:
            f.write(f"{len(vp)} {2 * m}\n")
            for c, bl in vp:
                f.write(" ".join(str(b) for b in bl) + "\n")
        print("rows:", " ".join(str(r) for r in dmap.zero_diag(T)))
    cnt = {}
    for c, _ in vp:
        cnt[c] = cnt.get(c, 0) + 1
    print("T =", dmap.tstr(T), " valid partitions with >=", mb, "blocks, by number of blocks:", dict(sorted(cnt.items())))
    top = max(cnt)
    names = [f"u{k}" for k in range(m)] + [f"v{k}" for k in range(m)]
    shown = 0
    for c, bl in vp:
        if c == top and shown < 40:
            blocks = {}
            for i, b in enumerate(bl):
                blocks.setdefault(b, []).append(names[i])
            print("  ", " | ".join(",".join(v) for v in blocks.values()))
            shown += 1


if __name__ == "__main__":
    main()
