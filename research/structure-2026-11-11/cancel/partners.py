"""CHECK (phase 8, main agent): who closes the cancellations behind double charges.

For every gate g charged to two or more sheets and every charging sheet j whose window misses a block of g's
support, list the exits e (descendants of g, ancestors of a sheet-j row, cancelling a block of
B(g) minus W_j) and classify each operand of e that is NOT a descendant of g ("partner"):
  third  = charged to a sheet other than the charging sheets of g;
  pair   = charged only to sheets that charge g;
  free   = charged to no sheet.
(An exit both of whose operands descend from g is "reconvergent".) Read-only evaluation of given circuits.
usage: python3 partners.py --q FILE M  |  python3 partners.py --mc SPEC [SPEC...]  |  python3 partners.py --mcscan STRIDE
"""
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "joint"))
sys.path.insert(0, os.path.join(HERE, "..", "compose", "compat"))


def study(n, g, vals, rows, bmask, m, verbose):
    blocks = lambda v: frozenset(j for j in range(m) if v & bmask(j))
    idx = {v: i for i, v in enumerate(vals)}
    readers = [[] for _ in vals]
    for gi, (a, b) in enumerate(g):
        readers[a].append(n + gi)
        readers[b].append(n + gi)
    win = {j: blocks(rows[(0, j)]) for j in range(m)}
    A, F = {}, {}
    for j in range(m):
        st, S = [idx[rows[(c, j)]] for c in range(4)], set()
        while st:
            s = st.pop()
            if s < n or s in S:
                continue
            S.add(s)
            st.extend(g[s - n])
        A[j], F[j] = S, {x for x in S if vals[x] & bmask(j)}
    charged = lambda x: frozenset(j for j in range(m) if x in F[j])
    tally = Counter()
    for x in range(n, len(vals)):
        ch = charged(x)
        if len(ch) < 2:
            continue
        desc_, st = set(), [x]
        while st:
            s = st.pop()
            if s in desc_:
                continue
            desc_.add(s)
            st.extend(readers[s])
        for j in ch:
            foreign = blocks(vals[x]) - win[j]
            if not foreign:
                continue
            for e in desc_ & A[j]:
                if e == x:
                    continue
                a, b = g[e - n]
                lost = (blocks(vals[a]) | blocks(vals[b])) - blocks(vals[e])
                if not lost & foreign:
                    continue
                ops = [o for o in (a, b) if o not in desc_]
                if not ops:
                    tally["reconvergent"] += 1
                    kind = "reconvergent"
                for o in ops:
                    co = charged(o)
                    kind = "third" if co - ch else ("pair" if co else "free")
                    tally[kind] += 1
                # Theorem K classification of the off-path operand(s): confined = support inside the window of
                # a sheet whose own block it contains; escape = every such own block is cancelled at e
                for o in [a, b]:
                    Bo = blocks(vals[o])
                    own = [l for l in Bo if Bo <= win[l]]
                    if not own:
                        tally["K:not-confined"] += 1
                    elif all(l in lost for l in own):
                        tally["K:escape"] += 1
                    else:
                        tally["K:confined-nonescape"] += 1
                if verbose:
                    print("   g%d charged %s -> sheet %d: exit g%d cancels %s, partner(s) %s %s" % (
                        x, sorted(ch), j, e, sorted(lost), [(o, sorted(charged(o))) for o in ops], kind))
    return tally


def qfile(path, m, verbose=True):
    ls = [l.split("#")[0].strip() for l in open(path)]
    ls = [l for l in ls if l]
    n, k = map(int, ls[0].split())
    g = [tuple(map(int, l.split()[:2])) for l in ls[1:1 + k]]
    vals = [1 << i for i in range(n)]
    for a, b in g:
        vals.append(vals[a] ^ vals[b])
    E4 = lambda c: 15 ^ (1 << c)
    S4 = lambda c: (1 << c) | (1 << ((c + 1) % 4))
    rows = {(c, j): (E4(c) << (4 * j)) | (S4(c) << (4 * ((j - 1) % m))) for j in range(m) for c in range(4)}
    t = study(n, g, vals, rows, lambda j: 15 << (4 * j), m, verbose)
    print(path, dict(t))


def mcone(spec, verbose):
    from jstats import get
    from clib import ROWS, bm, values
    g = get(spec)
    rows = {(c, j): ROWS[(c, j)] for c in range(4) for j in range(8)}
    return study(32, g, values(g), rows, bm, 8, verbose)


if __name__ == "__main__":
    if sys.argv[1] == "--q":
        qfile(sys.argv[2], int(sys.argv[3]))
    elif sys.argv[1] == "--mc":
        for s in sys.argv[2:]:
            print(s, dict(mcone(s, True)))
    else:
        from clib import KSTE, check
        from jstats import get
        stride = int(sys.argv[2])
        specs = ["r88", "r89", "r97"]
        for fn in sorted(os.listdir(KSTE)):
            if fn.startswith("circuits_"):
                k = sum(1 for l in open(os.path.join(KSTE, fn)) if l.strip())
                specs += ["%s:%d" % (fn, i) for i in range(1, k + 1, stride)]
        tot, per = Counter(), Counter()
        for s in specs:
            if not all(check(get(s))):
                continue
            t = mcone(s, False)
            tot.update(t)
            per[tuple(sorted(t.items()))] += 1
        print("totals:", dict(tot))
        for k, v in per.most_common(10):
            print("   ", k, v)
