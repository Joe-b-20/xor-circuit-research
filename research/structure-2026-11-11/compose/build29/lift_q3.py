"""Transplant test: the 28-gate Q_3 circuit read as a chain-of-three circuit.

Ring blocks (rho, rho+1, rho+2) -> chain blocks (b1, b2, b3).  Ring block rho+2 plays two roles: own block
of ring sheet rho+2 (-> b3) and previous block of ring sheet rho (-> b0, free).  Every operand occurrence
o of a ring input x_c.(rho+2) is relabelled either as the b3 unit u_c (beta_o = 1) or as a free b0 vector
f_o (beta_o = 0).  Gate count unchanged (28).  b1, b2 parts are those of the ring circuit; the b3 part of a
gate is sum of u_c(o) over occurrences with beta_o = 1 (formal multiplicity mod 2); the b0 part is sum f_o.
Requirements at the 12 ring outputs (as chain targets) are linear in beta (b3 part) and, for fixed beta,
linear in f (b0 part).  We solve the beta system by elimination and report its consistency and the
offending equations.  No search.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "review-pair"))
import rlib as R  # noqa: E402


def solve(rows, nvar):
    """rows: list of (mask, rhs, tag). Gaussian elimination; return (consistent, conflicts, pivots)."""
    piv = {}
    bad = []
    for mask, rhs, tag in rows:
        m, r, tags = mask, rhs, [tag]
        while m:
            h = m.bit_length() - 1
            if h in piv:
                pm, pr, pt = piv[h]
                m ^= pm
                r ^= pr
                tags = tags + pt
            else:
                piv[h] = (m, r, tags)
                break
        if m == 0 and r:
            bad.append(tags)
    return not bad, bad, piv


def main():
    model = R.qm_model(3)
    n, gates = R.read_qm(os.path.join(R.QDIR, "q3_28.txt"))
    vals = R.values(n, gates)
    outs = {v: k for k, v in model["rows"].items()}
    for rho in range(3):
        last = (rho + 2) % 3
        occ = []  # (gate index, operand position, c)
        form = {}  # signal -> (occurrence mask)
        for i in range(n):
            form[i] = 0
        for gi, (a, b) in enumerate(gates):
            g = n + gi
            m = 0
            for p, o in enumerate((a, b)):
                if o < n and o // 4 == last:
                    occ.append((g, p, o % 4))
                    m ^= 1 << (len(occ) - 1)
                else:
                    m ^= form[o]
            form[g] = m
        rows = []
        for g in range(n, len(vals)):
            if vals[g] not in outs:
                continue
            c, j = outs[vals[g]]
            sheet = (j - rho) % 3 + 1
            for cc in range(4):
                mask = 0
                for k, (_, _, oc) in enumerate(occ):
                    if (form[g] >> k) & 1 and oc == cc:
                        mask |= 1 << k
                need = 0
                if sheet == 3:
                    need = (R.E4(c) >> cc) & 1
                rows.append((mask, need, "g%d(sheet%d,c%d) b3 coord %d" % (g, sheet, c, cc)))
        ok, bad, piv = solve(rows, len(occ))
        print("rho=%d: %d occurrences of ring block %d inputs; beta system consistent: %s; rank %d" % (
            rho, len(occ), last, ok, len(piv)))
        for t in bad[:6]:
            print("   conflict:", " + ".join(t))


if __name__ == "__main__":
    main()
