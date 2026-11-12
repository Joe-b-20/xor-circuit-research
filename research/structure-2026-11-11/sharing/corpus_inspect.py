"""A handful of non-block-monotone 88-gate MixColumns circuits, read in the sheet language (read-only).

usage: python3 corpus_inspect.py

Picks the first kste circuit of each cancellation pattern (operand supports -> result support of its
block-cancelling gates) and the two hunt records named in review-83, and prints for each:
  charges per sheet, sum of mu, over-charge (sum of (|D_j| - 10)), uncharged gates, excess;
  the gates with mu >= 2 and the uncharged gates, with masks;  the block-cancelling gates with operands;
  the sizes of the eight families F_j of RECORD 9.2 and of their union (83 - overlaps);
  support-closure of the value set: U2 = values not derivable step by step from inputs using only operands
  supported inside the value's own support; U1 = values that are not the sum of two members of the value set
  (or inputs) supported inside their own support at all.
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "rotation", "mc"))
import mc  # noqa: E402

KSTE = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor")
HUNT = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/hunt")
NAMES = {0b0011: "s0", 0b0110: "s1", 0b1100: "s2", 0b1001: "s3", 0b0101: "d0", 0b1010: "d1", 0b1111: "t",
         0b0001: "e0", 0b0010: "e1", 0b0100: "e2", 0b1000: "e3",
         0b1110: "E0", 0b1101: "E1", 0b1011: "E2", 0b0111: "E3"}


def nib(v, j):
    return sum(((v >> (8 * c + j)) & 1) << c for c in range(4))


def desc(v):
    return " ".join(f"{j}:{NAMES[nib(v, j)]}" for j in range(8) if nib(v, j)) or "0"


def pat(s):
    return "".join(map(str, sorted(s)))


def study(gates, title):
    n = 32
    vals = [1 << i for i in range(n)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    first = {}
    for i in range(n, len(vals)):
        first.setdefault(vals[i], i)
    sup = [mc.blocks(v) for v in vals]
    anc = [set() for _ in range(8)]
    viol = set()
    for oi, t in enumerate(mc.TARGETS):
        o = first[t]
        seen, stack = set(), [o]
        while stack:
            s = stack.pop()
            if s < n or s in seen:
                continue
            seen.add(s)
            stack.extend(gates[s - n])
        anc[oi % 8] |= seen
        viol |= {g for g in seen if not sup[g] <= sup[o]}
    G = len(gates)
    ch = {g: [j for j in range(8) if j in sup[g] and g in anc[j]] for g in range(n, n + G)}
    charges = [sum(1 for g in ch if j in ch[g]) for j in range(8)]
    excess = sum(max(0, len(c) - 1) for c in ch.values())
    unch = [g for g in ch if not ch[g]]
    over = sum(c - 10 for c in charges)
    print(f"== {title}: G = {G}, violating gates {len(viol)}")
    print(f"   charges {charges}  sum mu {sum(charges)}  = 80 + over {over};  G = 80 + over + uncharged - excess = "
          f"80 + {over} + {len(unch)} - {excess} = {80 + over + len(unch) - excess}")
    for g in ch:
        if len(ch[g]) >= 2:
            a, b = gates[g - n]
            print(f"   mu>=2  g{g}: [{desc(vals[a])}] + [{desc(vals[b])}] = [{desc(vals[g])}]  charged to {ch[g]}; "
                  f"serves sheets {[j for j in range(8) if g in anc[j]]}")
    for g in unch:
        print(f"   mu=0   g{g}: [{desc(vals[g])}]  serves sheets {[j for j in range(8) if g in anc[j]]}")
    for g in range(n, n + G):
        a, b = gates[g - n]
        if (sup[a] | sup[b]) - sup[g]:
            print(f"   cancel g{g}: [{desc(vals[a])}] + [{desc(vals[b])}] = [{desc(vals[g])}]   ({pat(sup[a])}+{pat(sup[b])}->{pat(sup[g])})")
    # families of 9.2
    F = []
    for j in range(8):
        Fj = {g for g in anc[j] if j in sup[g]}
        if j == 3:
            Fj |= {g for g in anc[3] if 2 in sup[g] and 7 in sup[g]}
        F.append(Fj)
    union = set().union(*F)
    print(f"   families |F_j| = {[len(x) for x in F]} sum {sum(len(x) for x in F)}  union {len(union)}  "
          f"gates in two families: {sum(1 for g in union if sum(1 for x in F if g in x) >= 2)}  gates in none: {G - len(union)}")
    # support closure of the value set
    S = set(vals[n:])
    units = {1 << i for i in range(n)}
    pool = S | units
    U1 = []
    for v in S:
        bm = sum(mc.BLOCKMASK[j] for j in mc.blocks(v))
        inside = [a for a in pool if a != v and not (a & ~bm)]
        ins = set(inside)
        if not any((a ^ v) in ins for a in inside):
            U1.append(v)
    avail = set(units)
    pending = set(S)
    progress = True
    while pending and progress:
        progress = False
        for v in list(pending):
            bm = sum(mc.BLOCKMASK[j] for j in mc.blocks(v))
            cands = [a for a in avail if not (a & ~bm)]
            cs = set(cands)
            if any((a ^ v) in cs for a in cands):
                avail.add(v)
                pending.discard(v)
                progress = True
    print(f"   value set: U1 (no decomposition inside own support) = {len(U1)}: {['[' + desc(v) + ']' for v in U1]}")
    print(f"              U2 (outside the support closure) = {len(pending)}: {['[' + desc(v) + ']' for v in sorted(pending)]}")
    wide = [v for v in S if not any(mc.blocks(v) <= s for s in mc.SHEET_SUPPORT)]
    print(f"              values in no sheet support: {['[' + desc(v) + ']' for v in wide]}")
    # necessary condition for a block-monotone wiring: each sheet derivable from values inside its own support
    bad = []
    for j in range(8):
        bm = sum(mc.BLOCKMASK[b] for b in mc.SHEET_SUPPORT[j])
        av = {1 << i for i in range(32) if (1 << i) & bm}
        pend = {v for v in S if not (v & ~bm)}
        prog = True
        while pend and prog:
            prog = False
            for v in list(pend):
                if any((a ^ v) in av for a in av):
                    av.add(v)
                    pend.discard(v)
                    prog = True
        miss = [c for c in range(4) if mc.TARGETS[8 * c + j] not in av]
        if miss:
            bad.append((j, miss))
    print(f"              sheets whose outputs are not derivable from values inside the sheet support: {bad}"
          f"  -> block-monotone wiring {'impossible' if bad else 'not excluded by this test'}")


def main():
    seen_pat = {}
    nl = 0
    for fn in ("circuits_1.txt", "circuits_2.txt", "circuits_3.txt", "circuits_depth5.txt"):
        p = os.path.join(KSTE, fn)
        if not os.path.exists(p):
            continue
        for line in open(p):
            if not line.strip():
                continue
            nl += 1
            gates = mc.parse_pairs(line)
            if len(gates) != 88:
                continue
            r = mc.analyse(gates)
            if r is None or r["monotone"] or r["distinct"] != 88 or r["dead"]:
                continue
            vals = [1 << i for i in range(32)]
            for a, b in gates:
                vals.append(vals[a] ^ vals[b])
            key = []
            for gi, (a, b) in enumerate(gates):
                sa, sb, sg = mc.blocks(vals[a]), mc.blocks(vals[b]), mc.blocks(vals[32 + gi])
                if (sa | sb) - sg:
                    key.append("+".join(sorted([pat(sa), pat(sb)])) + "->" + pat(sg))
            key = " ; ".join(sorted(key))
            if key not in seen_pat:
                seen_pat[key] = (fn, nl, gates)
    order = sorted(seen_pat.items(), key=lambda kv: kv[1][1])
    for key, (fn, ln, gates) in order[:9]:
        study(gates, f"kste {fn} line {ln}  pattern {key}")
    for f in sorted(glob.glob(os.path.join(HUNT, "runs/*/workers/*/records/g88-*.json"))):
        if "d1a7d70c18e1b7cf" in f or "4d178ce621827217" in f:
            if f.endswith(".verification.json"):
                continue
            study([tuple(x) for x in json.load(open(f))["gates"]], "hunt " + os.path.basename(f))


if __name__ == "__main__":
    main()
