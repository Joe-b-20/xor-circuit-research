"""Reviewer's own corpus code (independent of rotation/mc/mc.py). Read-only on the corpus.

usage: python3 families.py
"""
import glob
import json
import os
import re
from collections import Counter
from itertools import combinations

HOME = os.path.expanduser("~")
REPO = os.path.join(HOME, "xor-circuit-research")
MAT = os.path.join(REPO, "circuits/aes-mixcolumns/aes-mixcolumns.mat.txt")
KSTE = os.path.join(HOME, "xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor")
HUNT = os.path.join(HOME, "xs-campaigns/2026-11-07-sprint/hunt")

# --- matrix: own parse. Row r = output r; column i = input i.  Assume input i = byte i//8, bit i%8.
lines = [l.split() for l in open(MAT).read().strip().splitlines()]
hdr = [x for l in lines[:2] for x in l]
rows = [l for l in lines if len(l) == 32]
assert len(rows) == 32, len(rows)
TARGET = [sum(int(x) << i for i, x in enumerate(r)) for r in rows]
# cross-check (3.1) independently: out_c = 2b_c + 3b_{c+1} + b_{c+2} + b_{c+3}
def xt(byte):  # bit masks as list of input-sets per bit of 2*byte
    pass
def mc_ref():
    out = []
    for c in range(4):
        for j in range(8):
            m = 0
            # b_{c+1}+b_{c+2}+b_{c+3}, bit j
            for d in (1, 2, 3):
                m ^= 1 << (8 * ((c + d) % 4) + j)
            # 2*(b_c + b_{c+1}) bit j: w_{j-1} plus w_7 if j in 1,3,4; bit 0 = w_7
            def w(k):
                return (1 << (8 * c + k)) ^ (1 << (8 * ((c + 1) % 4) + k))
            if j == 0:
                m ^= w(7)
            else:
                m ^= w(j - 1)
                if j in (1, 3, 4):
                    m ^= w(7)
            out.append(m)
    return out
REF = mc_ref()
print("matrix rows equal to formula (3.1) with output r = (c, j), r = 8c + j:", REF == TARGET)
BM = [sum(1 << (8 * c + j) for c in range(4)) for j in range(8)]
def supp(v):
    return frozenset(j for j in range(8) if v & BM[j])
S = [supp(TARGET[j]) for j in range(8)]
assert all(supp(TARGET[8 * c + j]) == S[j] for c in range(4) for j in range(8))
print("sheet supports:", [sorted(s) for s in S])
TSET = {t: r % 8 for r, t in enumerate(TARGET)}

# --- item 4: block graph triangles
edges = {frozenset(p) for s in S for p in combinations(sorted(s), 2)}
tri = [t for t in combinations(range(8), 3) if all(frozenset(p) in edges for p in combinations(t, 2))]
print("block graph edges:", sorted(tuple(sorted(e)) for e in edges))
print("triangles:", tri, " not inside a single sheet support:",
      [t for t in tri if not any(set(t) <= s for s in S)])
WINDOW = [s for s in S]
def in_window(sp):
    return any(sp <= s for s in S)


def analyse(gates):
    vals = [1 << i for i in range(32)]
    for a, b in gates:
        if a >= len(vals) or b >= len(vals):
            return None
        vals.append(vals[a] ^ vals[b])
    present = set(vals[32:])
    if not all(t in present for t in TARGET):
        return None
    n = 32
    sp = [supp(v) for v in vals]
    anc = [set() for _ in range(8)]
    mono = True
    for o in range(n, len(vals)):
        if vals[o] not in TSET:
            continue
        j = TSET[vals[o]]
        st, seen = [o], set()
        while st:
            x = st.pop()
            if x < n or x in seen:
                continue
            seen.add(x)
            st.extend(gates[x - n])
        anc[j] |= seen
        if any(not sp[g] <= sp[o] for g in seen):
            mono = False
    F = {}
    for j in range(8):
        if j == 3:
            F[j] = {g for g in anc[3] if 3 in sp[g] or {2, 7} <= sp[g]}
        else:
            F[j] = {g for g in anc[j] if j in sp[g]}
    overl = [(i, j) for i, j in combinations(range(8), 2) if F[i] & F[j]]
    # cancellations
    canc = []
    for gi, (a, b) in enumerate(gates):
        g = n + gi
        u = sp[a] | sp[b]
        C = u - sp[g]
        if C:
            cross = not in_window(u)
            tris = set()
            for j in C:
                if j in sp[a] and j in sp[b]:
                    for i in sp[a] - sp[b]:
                        for k in sp[b] - sp[a]:
                            tris.add(tuple(sorted((i, j, k))))
            canc.append((g, cross, frozenset(C), frozenset(u), frozenset(tris)))
    winloc = all(in_window(sp[g]) for g in range(n, len(vals)))
    # sheet-3 local decomposition (Theorem 9.1 with a = 2, k = 7, b = 3)
    loc = None
    if mono:
        Bg = [g for g in anc[3] if 3 in sp[g]]
        Mg = [g for g in anc[3] if sp[g] == frozenset([2, 7])]
        Ea, Ek, Em, Ms = [], [], [], set()
        for g in Bg:
            a, b = gates[g - n]
            z = [x for x in (a, b) if 3 not in sp[x]]
            if len(z) == 1:
                x = z[0]
                if sp[x] == frozenset([2]):
                    Ea.append(vals[x])
                elif sp[x] == frozenset([7]):
                    Ek.append(vals[x])
                elif sp[x] == frozenset([2, 7]):
                    Em.append(x); Ms.add(x)
                else:
                    raise RuntimeError("entry operand support %s" % sorted(sp[x]))
            elif len(z) == 2:
                raise RuntimeError("B-gate with both operands zero on b")
        def rank(vs):
            basis = []
            for v in vs:
                for bb in basis:
                    v = min(v, v ^ bb)
                if v:
                    basis.append(v)
            return len(basis)
        dA, dK = rank(Ea), rank(Ek)
        loc = dict(B=len(Bg), M=len(Mg), Ea=len(Ea), Ek=len(Ek), s=len(Ms), dA=dA, dK=dK,
                   ok=(len(Bg) >= 10 + len(Ek) and len(Bg) >= 10 + len(Ea) and dA + len(Ms) >= 3
                       and dK + len(Ms) >= 3 and len(Bg) + len(Mg) >= 13))
    return dict(G=len(gates), distinct=len(set(vals[n:])), mono=mono, F={j: len(F[j]) for j in F},
                overlap=overl, total=sum(len(F[j]) for j in F), canc=canc, winloc=winloc, loc=loc,
                dead=sum(1 for g in range(n, len(vals)) if not any(g in anc[j] for j in range(8))))


def parse_ncff(path):
    idx, gates = {}, []
    for line in open(path):
        line = line.split("%")[0].split("#")[0].strip()
        m = re.match(r"^Inputs:\s*([a-z]+)(\d+):[a-z]+(\d+)", line)
        if m:
            for i in range(int(m.group(2)), int(m.group(3)) + 1):
                idx[m.group(1) + str(i)] = i - int(m.group(2))
            continue
        m = re.match(r"^XOR\s+(\S+)\s+(\S+)\s+(\S+)", line)
        if m:
            o, a, b = m.groups()
            gates.append((idx[a], idx[b]))
            idx[o] = 32 + len(gates) - 1
    return gates


def report(name, rs):
    mono = [r for r in rs if r["mono"]]
    non = [r for r in rs if not r["mono"]]
    print("==", name, "circuits:", len(rs), " monotone:", len(mono), " not:", len(non))
    if mono:
        print("  [mono] min family sizes:", {j: min(r["F"][j] for r in mono) for j in range(8)},
              " min total:", min(r["total"] for r in mono), " total hist:", dict(Counter(r["total"] for r in mono)))
        print("  [mono] F3 hist:", dict(Counter(r["F"][3] for r in mono)),
              " circuits with overlapping families:", sum(1 for r in mono if r["overlap"]))
        print("  [mono] sheet-3 local inequalities all hold:", all(r["loc"]["ok"] for r in mono),
              " (B,M,|Ea|,|Ek|,s) most common:",
              Counter((r["loc"]["B"], r["loc"]["M"], r["loc"]["Ea"], r["loc"]["Ek"], r["loc"]["s"]) for r in mono).most_common(5),
              " min B+M:", min(r["loc"]["B"] + r["loc"]["M"] for r in mono),
              " s hist:", dict(Counter(r["loc"]["s"] for r in mono)))
        print("  [mono] with a block-cancelling gate:", sum(1 for r in mono if r["canc"]),
              " cross-window cancellations in monotone:", sum(1 for r in mono if any(c[1] for c in r["canc"])))
    if non:
        print("  [non] cross-window cancelling gates per circuit:",
              dict(Counter(sum(1 for c in r["canc"] if c[1]) for r in non)))
        print("  [non] all cancelling gates per circuit:", dict(Counter(len(r["canc"]) for r in non)))
        print("  [non] cancelled block sets of cross gates:",
              dict(Counter(tuple(sorted(c[2])) for r in non for c in r["canc"] if c[1])))
        print("  [non] triangles of cross gates:",
              dict(Counter(tuple(sorted(c[4])) for r in non for c in r["canc"] if c[1])))
        print("  [non] union supports of cross gates:",
              dict(Counter(tuple(sorted(c[3])) for r in non for c in r["canc"] if c[1])))
        print("  [non] window-local:", sum(1 for r in non if r["winloc"]))
        print("  [non] non-cross cancel patterns (cancelled, union):",
              dict(Counter((tuple(sorted(c[2])), tuple(sorted(c[3]))) for r in non for c in r["canc"] if not c[1])))
        print("  [non] family totals:", dict(Counter(r["total"] for r in non)),
              " with overlap:", sum(1 for r in non if r["overlap"]),
              " overlap pairs:", dict(Counter(p for r in non for p in r["overlap"])))


def main():
    rs = []
    for f in sorted(glob.glob(os.path.join(REPO, "circuits/aes-mixcolumns/*.circ.txt"))):
        r = analyse(parse_ncff(f))
        print(os.path.basename(f), "G", r["G"], "mono", r["mono"], "F", r["F"], "total", r["total"],
              "overlap", r["overlap"], "loc", r["loc"], "canc", len(r["canc"]))
        rs.append(r)
    ks, why = [], Counter()
    nl = 0
    for fn in sorted(glob.glob(os.path.join(KSTE, "circuits_*.txt"))):
        for line in open(fn):
            if not line.strip():
                continue
            nl += 1
            gates = [(int(a), int(b)) for a, b in re.findall(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)", line)]
            r = analyse(gates)
            if r is None:
                why["not MixColumns / bad"] += 1
                continue
            why[("G", r["G"], "distinct", r["distinct"], "dead", r["dead"])] += 1
            if r["G"] == 88 and r["distinct"] == 88 and r["dead"] == 0:
                ks.append(r)
    print("kste files:", sorted(os.path.basename(f) for f in glob.glob(os.path.join(KSTE, "circuits_*.txt"))),
          "lines", nl, "classes:", dict(why))
    report("kste (G=88, distinct, no dead)", ks)
    hs = []
    for f in sorted(glob.glob(os.path.join(HUNT, "runs/*/workers/*/records/g88-*.json"))):
        if f.endswith(".verification.json"):
            continue
        c = json.load(open(f))
        r = analyse([tuple(g) for g in c["gates"]])
        if r is not None:
            hs.append(r)
    report("hunt records", hs)


if __name__ == "__main__":
    main()
