"""Verifier and accountant for hand-designed local circuits of the chain of three sheets.

Circuit text: one gate per line, "name = A + B"; operands: xKC = unit C of block b_K (K = 1..3, C = 0..3),
fBBBB = free vector on b_0 written as 4 bits b0 b1 b2 b3 (e.g. f1100 = units 0,1), or an earlier gate
name.  '#' starts a comment.  Values are 16-bit: nibble k = block b_k, bit c = unit c.
Targets T(k,c) = E_c on b_k + s_c on b_(k-1), s_c = units c, c+1 mod 4.

Reports: gate count, missing targets; the charged sets D_k (ancestors of a sheet-k target, targets
included, nonzero on b_k), over = sum(|D_k| - 10), unch, excess, so that G = 30 + over + unch - excess;
the pair unions |D1 u D2|, |D2 u D3|; and, via ../../chain/chain3.py, the mirror T (cleaned) with the
peel counts at both cuts (f, D, N, entries, odd labels, exits).  Checks one given circuit; no search.
usage: python3 vchain.py circuit.txt
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "review-pair"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "chain"))
import rlib as R  # noqa: E402
import chain3 as C  # noqa: E402


def E4(c):
    return 15 ^ (1 << (c % 4))


def S4(c):
    return (1 << (c % 4)) | (1 << ((c + 1) % 4))


def target(k, c):
    return (E4(c) << (4 * k)) | (S4(c) << (4 * (k - 1)))


def nibs(v):
    return " ".join(format((v >> (4 * k)) & 15, "04b")[::-1] for k in range(4))


def parse(path):
    gates, names = [], {}
    for line in open(path):
        line = line.split("#")[0].strip()
        if not line:
            continue
        lhs, rhs = line.split("=")
        a, b = [t.strip() for t in rhs.split("+")]
        ops = []
        for t in (a, b):
            if t[0] == "x" and len(t) == 3 and t[1:].isdigit():
                k, c = int(t[1]), int(t[2])
                assert 1 <= k <= 3 and 0 <= c <= 3, t
                ops.append(("u", 4 * (k - 1) + c))
            elif t[0] == "f" and len(t) == 5 and set(t[1:]) <= set("01"):
                ops.append(("f", sum(int(t[1 + i]) << i for i in range(4))))
            else:
                assert t in names, "unknown operand %s" % t
                ops.append(("g", names[t]))
        names[lhs.strip()] = len(gates)
        gates.append(tuple(ops))
    return gates, names


def opv(o, vals):
    if o[0] == "u":
        return 1 << (4 + o[1])
    if o[0] == "f":
        return o[1]
    return vals[o[1]]


def main():
    gates, names = parse(sys.argv[1])
    inv = {i: n for n, i in names.items()}
    vals = []
    for a, b in gates:
        vals.append(opv(a, vals) ^ opv(b, vals))
    print("gates: %d" % len(gates))
    tg, missing = [], []
    for k in (1, 2, 3):
        for c in range(4):
            t = target(k, c)
            hit = [i for i, v in enumerate(vals) if v == t]
            if hit:
                tg.append(hit[0])
            else:
                missing.append((k, c))
    if missing:
        print("MISSING targets:", missing)
        for i, v in enumerate(vals):
            print("  %-6s %s" % (inv[i], nibs(v)))
        return
    print("all 12 targets computed")
    # charged sets
    Dk = {}
    for k in (1, 2, 3):
        st = [tg[4 * (k - 1) + c] for c in range(4)]
        anc = set()
        while st:
            g = st.pop()
            if g in anc:
                continue
            anc.add(g)
            st.extend(o[1] for o in gates[g] if o[0] == "g")
        Dk[k] = set(g for g in anc if (vals[g] >> (4 * k)) & 15)
    mu = [sum(1 for k in Dk if g in Dk[k]) for g in range(len(gates))]
    over = sum(len(Dk[k]) - 10 for k in Dk)
    unch = sum(1 for m in mu if m == 0)
    exc = sum(max(m - 1, 0) for m in mu)
    print("|D1| %d |D2| %d |D3| %d  over %d unch %d excess %d  -> 30 + %d + %d - %d = %d" % (
        len(Dk[1]), len(Dk[2]), len(Dk[3]), over, unch, exc, over, unch, exc, 30 + over + unch - exc))
    print("|D1 u D2| %d  |D2 u D3| %d  |D1 n D3| %d" % (len(Dk[1] | Dk[2]), len(Dk[2] | Dk[3]),
                                                       len(Dk[1] & Dk[3])))
    # pair sets: W12 (b3 killed), W23 (b0 killed); distinct restricted values
    anc_of = {}
    for k in (1, 2, 3):
        st = [tg[4 * (k - 1) + c] for c in range(4)]
        anc = set()
        while st:
            g = st.pop()
            if g in anc:
                continue
            anc.add(g)
            st.extend(o[1] for o in gates[g] if o[0] == "g")
        anc_of[k] = anc
    W12 = [g for g in anc_of[1] | anc_of[2] if (vals[g] >> 4) & 0xFF]
    W23 = [g for g in anc_of[2] | anc_of[3] if (vals[g] >> 8) & 0xFF]
    v12 = set(vals[g] & 0x0FFF for g in W12)
    v23 = set(vals[g] & 0xFFF0 for g in W23)
    I = set(W12) & set(W23)

    def dups(W, mask):
        order = sorted(W)
        seen = set(1 << (4 * k + c) & mask for k in (1, 2, 3) for c in range(4))
        d = 0
        for g in order:
            v = vals[g] & mask
            if v in seen:
                d += 1
            seen.add(v)
        return d
    d12, d23 = dups(W12, 0x0FFF), dups(W23, 0xFFF0)
    U = set(g for g in range(len(gates)) if mu[g] == 0)
    w12 = set(W12) - Dk[1] - Dk[2]
    w23 = set(W23) - Dk[2] - Dk[3]
    e13 = len(Dk[1] & Dk[3])
    e123 = len(Dk[1] & Dk[2] & Dk[3])
    o2 = len(Dk[2]) - 10
    terms = dict(o2=o2, dup12=d12, dup23=d23, U_w12_w23=len(U & w12 & w23), w12_D3=len(w12 & Dk[3]),
                 w23_D1=len(w23 & Dk[1]), e13_minus_e123=e13 - e123)
    bound = 30 - o2 + d12 + d23 - terms["U_w12_w23"] - terms["w12_D3"] - terms["w23_D1"] - (e13 - e123)
    print("two-pair bound: G >= 30 - o2 + dup12 + dup23 - |U n w12' n w23'| - |w12' n D3| - |w23' n D1|"
          " - (e13 - e123) = %d   %s" % (bound, terms))
    assert bound <= len(gates)
    print("W12: %d gates, %d distinct (b3 killed); W23: %d gates, %d distinct (b0 killed); |W12 n W23| = %d"
          % (len(W12), len(v12), len(W23), len(v23), len(I)))
    for g in range(len(gates)):
        sh = [k for k in Dk if g in Dk[k]]
        tag = ""
        if g in tg:
            k = tg.index(g)
            tag = " T(%d,%d)" % (k // 4 + 1, k % 4)
        if len(sh) != 1 or "-v" in sys.argv:
            print("   %-6s %s  D%s%s" % (inv[g], nibs(vals[g]), "".join(map(str, sh)) or "-", tag))
    # mirror
    lc = [tuple(o if o[0] != "f" else ("f", o[1]) for o in g) for g in gates]
    lc2, tg2 = R.clean(lc, tg) if hasattr(R, "clean") else (lc, tg)
    M = C.mirror(lc2, tg2)
    C.check_mirror_form(M)
    red = C.reduce_T(M["Tm"], M["Tops"])
    zetas = [M["Tm"][M["adj"][("z", t)]] for t in range(M["tau"])]
    tau = len(set(z for z in zetas if z))
    p3 = C.peel(red, 0xFF, 8)
    p1 = C.peel(red, 0x0F, 4)
    print("mirror: K %d tau %d |T| %d reduced |T| %d (+tau %d = %d)" % (
        M["K"], M["tau"], len(M["Tm"]) - 12, len(red), tau, len(red) + tau))
    print("  cut 2 (groups 1,2 | 3): f %(f)d D %(D)d N %(N)d entries %(e)d odd %(odd)d exits %(exits)d "
          "nonentry %(nonentry)d" % p3)
    print("  cut 1 (group 1 | 2,3): f %(f)d D %(D)d N %(N)d entries %(e)d odd %(odd)d exits %(exits)d "
          "nonentry %(nonentry)d" % p1)


if __name__ == "__main__":
    main()
