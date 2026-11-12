"""CHECK (not a proof): one kste circuit gate by gate in block coordinates, classified at primal cut block K.

usage: python3 show_tri.py FILE LINE [K=2] [FILTER]   (LINE = the file's own 1-based line number)
Columns: gate wire, operands, value as block:nibble names (s_c = e_c+e_(c+1), d, t, E_c = t+e_c),
class at cut K (first = new block-K part, entry = one operand zero on K (label = that operand),
dup = other repeat of a block-K part, far = zero on K with both operands zero on K, EXIT = zero on K,
operands nonzero on K), output name (c,j) if it is a target (first occurrence), sheets served.
FILTER: 'all' (default) or a comma list of blocks; only gates whose support meets them are printed.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "rotation", "mc"))
import mc  # noqa: E402

KSTE = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor")
PN = {0b0011: "s0", 0b0110: "s1", 0b1100: "s2", 0b1001: "s3", 0b0101: "d0", 0b1010: "d1", 0b1111: "t",
      0b0001: "e0", 0b0010: "e1", 0b0100: "e2", 0b1000: "e3",
      0b1110: "E0", 0b1101: "E1", 0b1011: "E2", 0b0111: "E3"}


def nib(v, j):
    return sum(((v >> (8 * c + j)) & 1) << c for c in range(4))


def desc(v):
    return " ".join("%d:%s" % (j, PN[nib(v, j)]) for j in range(8) if nib(v, j)) or "0"


def load(fn, ln):
    for i, line in enumerate(open(os.path.join(KSTE, fn)), 1):
        if i == ln:
            g = mc.parse_pairs(line)
            r = int(os.environ.get("ROT", "0"))
            f = lambda x: x if x >= 32 else 8 * ((x // 8 + r) % 4) + x % 8
            return [(f(a), f(b)) for a, b in g]


def circuit(gates):
    vals = [1 << i for i in range(32)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    first = {}
    for i in range(32, len(vals)):
        first.setdefault(vals[i], i)
    anc = {}
    for oi, t in enumerate(mc.TARGETS):
        stack, seen = [first[t]], set()
        while stack:
            s = stack.pop()
            if s < 32 or s in seen:
                continue
            seen.add(s)
            stack.extend(gates[s - 32])
        for g in seen:
            anc.setdefault(g, set()).add(oi % 8)
    outname = {first[t]: "(%d,%d)" % divmod(i, 8) for i, t in enumerate(mc.TARGETS)}
    return vals, anc, outname


def classes(gates, vals, K):
    low = mc.BLOCKMASK[K]
    seenK = set(vals[i] & low for i in range(32))
    cl = {}
    for gi, (a, b) in enumerate(gates):
        w = 32 + gi
        v = vals[w]
        om, oa, ob = v & low, vals[a] & low, vals[b] & low
        if om == 0:
            cl[w] = "EXIT" if oa else "far"
        elif om not in seenK:
            seenK.add(om)
            cl[w] = "first"
        elif (oa == 0) != (ob == 0):
            cl[w] = "entry"
        else:
            cl[w] = "dup"
    return cl


def name(w, vals):
    return "x%d" % w if w < 32 else "g%d" % w


def main():
    fn, ln = sys.argv[1], int(sys.argv[2])
    K = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    filt = sys.argv[4] if len(sys.argv) > 4 else "all"
    gates = load(fn, ln)
    r = mc.analyse(gates)
    print("%s line %d: G=%d monotone=%s distinct=%d dead=%d" % (fn, ln, r["G"], r["monotone"], r["distinct"], r["dead"]))
    vals, anc, outname = circuit(gates)
    cl = classes(gates, vals, K)
    keep = None if filt == "all" else set(int(x) for x in filt.split(","))
    from collections import Counter
    print("counts at cut %d:" % K, dict(Counter(cl.values())))
    print("charges", r["charges"], "excess", r["excess"], "uncharged", r["uncharged"], "sum_mu", r["sum_mu"])
    for gi, (a, b) in enumerate(gates):
        w = 32 + gi
        if keep is not None and not (mc.blocks(vals[w]) & keep):
            continue
        opd = lambda x: ("x%d[%s]" % (x, desc(vals[x]))) if x < 32 else "g%d" % x
        print("g%d = %s + %s = [%s] %s %s s%s" % (w, opd(a), opd(b), desc(vals[w]), cl[w], outname.get(w, ""),
                                                 "".join(map(str, sorted(anc.get(w, ()))))))


if __name__ == "__main__":
    main()
