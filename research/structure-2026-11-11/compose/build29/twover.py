"""Two-version lift of the 28-gate Q_3 circuit to the chain of three sheets.

Ring blocks (rho, rho+1, rho+2) -> (b1, b2, *), * = b3 in version B, * = b0 (free) in version F.
A ring gate g with nonzero ring-block-* part in its value has two distinct chain versions gB, gF
(gB = aB + bB, gF = aF + bF; an input x_c.* is the b3 unit in B and the free unit in F); a gate whose
value has zero *-part has one value, computable from both-B or both-F operands (a gate whose operands
have zero *-part has only one way).  Chain sheet 1 needs the F version of ring sheet rho's outputs,
chain sheet 3 the B version of ring sheet rho+2's.  Propagate the needs; a zero-*-part gate whose
operands have nonzero *-part ('closer') is computed in one chosen version: every combination of these
few binary choices is listed (a two- or four-case analysis of one fixed circuit, not a search over
circuits).  Prints the gate count of each lift and writes the cheapest as a vchain.py circuit.
"""
import itertools
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "review-pair"))
import rlib as R  # noqa: E402


def main():
    model = R.qm_model(3)
    n, gates = R.read_qm(os.path.join(R.QDIR, "q3_28.txt"))
    vals = R.values(n, gates)
    outs = {v: k for k, v in model["rows"].items()}
    best = None
    for rho in range(3):
        star = (rho + 2) % 3
        blk = lambda v: R.nib(model, v, star)
        closers = [g for g in range(n, len(vals)) if blk(vals[g]) == 0 and
                   any(blk(vals[o]) for o in gates[g - n] if o >= n or o // 4 == star)]
        for choice in itertools.product("BF", repeat=len(closers)):
            ch = dict(zip(closers, choice))
            need = set()  # (g, ver) with ver in B/F, or (g, '1') for zero-* gates

            def want(g, ver):
                if g < n:
                    return
                if blk(vals[g]) == 0:
                    ver = "1"
                if (g, ver) in need:
                    return
                need.add((g, ver))
                sub = ch.get(g, ver) if ver == "1" else ver
                if sub == "1":
                    sub = "B"
                for o in gates[g - n]:
                    want(o, sub)
            for g in range(n, len(vals)):
                if vals[g] in outs:
                    c, j = outs[vals[g]]
                    sh = (j - rho) % 3 + 1
                    want(g, {1: "F", 2: "1", 3: "B"}[sh])
            cnt = len(need)
            dup = sorted(g for g in range(n, len(vals)) if (g, "B") in need and (g, "F") in need)
            print("rho %d closers %s choice %s: %d gates; doubled: %s" % (
                rho, ["g%d" % g for g in closers], "".join(choice), cnt, " ".join("g%d" % g for g in dup)))
            if best is None or cnt < best[0]:
                best = (cnt, rho, ch, need)
    cnt, rho, ch, need = best
    star = (rho + 2) % 3
    blk = lambda v: R.nib(model, v, star)
    own = {rho: 1, (rho + 1) % 3: 2}

    def nm(o, ver):
        if o < n:
            j, c = o // 4, o % 4
            if j == star:
                return ("x3%d" % c) if ver == "B" else ("f" + "".join("1" if i == c else "0" for i in range(4)))
            return "x%d%d" % (own[j], c)
        if blk(vals[o]) == 0:
            return "g%d" % o
        return "g%d%s" % (o, ver)
    lines = []
    for g in range(n, len(vals)):
        for ver in ("1", "B", "F"):
            if (g, ver) in need:
                sub = ch.get(g, "B") if ver == "1" else ver
                a, b = gates[g - n]
                name = "g%d" % g if ver == "1" else "g%d%s" % (g, ver)
                lines.append("%s = %s + %s" % (name, nm(a, sub), nm(b, sub)))
    out = os.path.join(HERE, "lift_best.txt")
    open(out, "w").write("# two-version lift of q3_28 (rho %d), %d gates\n" % (rho, cnt) + "\n".join(lines) + "\n")
    print("best: rho %d, %d gates -> %s" % (rho, cnt, out))


if __name__ == "__main__":
    main()
