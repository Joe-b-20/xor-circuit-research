"""CHECK (not a proof): primal and mirror cut statistics over a sample of the kste MixColumns corpus.

usage: python3 corpus_mc.py STRIDE [MAXN]
Primal single-block cut k: omega = part on input block k; an exit across it is a gate with zero block-k
part whose operands have equal nonzero block-k parts = a gate that cancels block k. Labels = the
non-block-k operand of an entry. For every primal exit: cut block, operand supports, value support,
sheet supports containing the value, sheets it serves (ancestor of an output), honest cost (fewest
earlier labels at that cut summing to the value; None if > 6), near f + h and label rank at that cut.
Mirror (fwd order): exits across arcs of length 1..3, reduced gates outside every row window.
"""
import os
import sys
from collections import Counter
from itertools import combinations

from mirror_mc import WIN, mirror, rank, split, groups, mc

KSTE = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor")


def pat(s):
    return "".join(map(str, sorted(s)))


def honest(labels, v, tmax=6):
    lab = sorted(set(labels))
    for t in range(1, min(len(lab), tmax) + 1):
        for cmb in combinations(lab, t):
            x = 0
            for y in cmb:
                x ^= y
            if x == v:
                return t
    return None


def primal_split(gates, k):
    n = 32
    vals = [1 << i for i in range(n)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    low = mc.BLOCKMASK[k]
    first = set(1 << i for i in range(n) if (1 << i) & low)
    f = e = h = N = 0
    labels, exits = [], []
    seen = set(vals[:n])
    for gi, (a, b) in enumerate(gates):
        v = vals[n + gi]
        if v == 0 or v in seen:
            continue
        seen.add(v)
        om, oa, ob = v & low, vals[a] & low, vals[b] & low
        if om == 0:
            if oa:
                exits.append((gi, a, b))
            else:
                N += 1
        elif om in first:
            if (oa == 0) != (ob == 0):
                e += 1
                labels.append((gi, vals[a] if oa == 0 else vals[b]))
            else:
                h += 1
        else:
            first.add(om)
            f += 1
    return vals, dict(f=f, e=e, h=h, N=N), labels, exits


def serves(gates, vals):
    n = 32
    first = {}
    for i in range(n, len(vals)):
        first.setdefault(vals[i], i)
    anc = {}
    for oi, t in enumerate(mc.TARGETS):
        o = first[t]
        stack, seen = [o], set()
        while stack:
            s = stack.pop()
            if s < n or s in seen:
                continue
            seen.add(s)
            stack.extend(gates[s - n])
        for g in seen:
            anc.setdefault(g, set()).add(oi % 8)
    return anc


def main():
    stride = int(sys.argv[1])
    maxn = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 9
    stats = Counter()
    pex = Counter()
    mex = Counter()
    examples = {}
    nl = done = 0
    for fn in ("circuits_1.txt", "circuits_2.txt", "circuits_3.txt", "circuits_depth5.txt"):
        p = os.path.join(KSTE, fn)
        if not os.path.exists(p):
            continue
        for line in open(p):
            if not line.strip():
                continue
            nl += 1
            if nl % stride:
                continue
            gates = mc.parse_pairs(line)
            r = mc.analyse(gates)
            if r is None or r["distinct"] != len(gates) or r["dead"]:
                stats["skipped"] += 1
                continue
            done += 1
            mono = "mono" if r["monotone"] else "nonmono"
            stats[mono] += 1
            # primal exits at every single-block cut
            anc = None
            npx = 0
            for k in range(8):
                vals, st, labels, exits = primal_split(gates, k)
                for gi, a, b in exits:
                    if anc is None:
                        anc = serves(gates, vals)
                    npx += 1
                    v = vals[32 + gi]
                    sv = mc.blocks(v)
                    insheet = [j for j in range(8) if sv <= mc.SHEET_SUPPORT[j]]
                    lab = [x for i, x in labels if i < gi]
                    key = (mono, k, pat(mc.blocks(vals[a])) + "+" + pat(mc.blocks(vals[b])), pat(sv),
                           "in" + pat(insheet), "serves" + pat(anc.get(32 + gi, ())),
                           "honest%s" % honest(lab, v), "near%d" % (st["f"] + st["h"]), "rank%d" % rank([x for _, x in labels]))
                    pex[key] += 1
                    examples.setdefault(key, (fn, nl))
            stats["%s primal exits %d" % (mono, npx)] += 1
            # mirror
            tot, red, _ = mirror(gates, "fwd")
            outw = sum(1 for g in red if not any(groups(g["v"]) <= w for w in WIN))
            nx = 0
            for rr in (1, 2, 3):
                for k in range(8):
                    S = [(k + t) % 8 for t in range(rr)]
                    st, labels, exits, _ = split(red, S)
                    for idx, g in exits:
                        nx += 1
                        inwin = [k2 for k2, w in enumerate(WIN) if groups(g["v"]) <= w]
                        mex[(mono, pat(S), pat(groups(g["v"])), "win" + "".join(map(str, inwin)))] += 1
            stats["%s mirror exits %d outside-window %d" % (mono, nx, outw)] += 1
            if done >= maxn:
                break
        if done >= maxn:
            break
    print("lines read %d, analysed %d" % (nl, done))
    for kk, v in sorted(stats.items()):
        print("  %s: %d" % (kk, v))
    print("primal exits (block-cancelling gates), by type:")
    for kk, v in pex.most_common(40):
        print("  %5d %s  e.g. %s" % (v, " ".join(map(str, kk)), examples[kk]))
    print("mirror exits by type:")
    for kk, v in mex.most_common(30):
        print("  %5d %s" % (v, " ".join(map(str, kk))))


if __name__ == "__main__":
    main()
