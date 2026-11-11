"""Section 2 extras.

(1) Does (2.1) need normalisation? Append to the recorded MixColumns 88 a duplicate of an output gate,
    a duplicate of an input (x_a + l with l = x_a + x_b ... realised as a translate), an unused even
    gate and a zero gate, and recompute every quantity from the definitions (signals, not masks).
(2) r_p <= 3 'by F3': show that one boundary triple can give two represented edges at one helper
    unless Lemma 4.4 (independence) is used -- we only check that the configuration is consistent
    at the level of masks (a, b, c boundary, b-c and a-c both B-B edges, p = a+b+c).
(3) Minimum weight of the graph code for small-scale-aes and lw16-4x4-gf256-inv-had, giving
    c(1) <= floor(2n / d) and hence a lower bound on x for every circuit of those maps; then
    h + y = G - n - x < n holds for every circuit with G <= the recorded one, minimum or not.
(4) Which map folders were skipped by the survey (no single .mat.txt).
"""
import itertools

from lib import CIRC, all_circuits, load, read_matrix, wt, par
from sec2_identity import analyse


def part1():
    d = CIRC / "aes-mixcolumns"
    n, gates, outs, vals, rows = load(d / "aes-mixcolumns-xor88-depth5.circ.txt", d / "aes-mixcolumns.mat.txt")
    gates = list(gates)
    vals = dict(vals)
    base = analyse(n, gates, outs, vals)
    # duplicate of output gate y0
    o, a, b = next(g for g in gates if g[0] == outs[0])
    extra = [("dupY", a, b)]
    # an even gate x0 + x1 and a translate x0 + (x0+x1) = copy of x1 (duplicate of an input)
    extra += [("ev01", "x0", "x1"), ("dupX1", "x0", "ev01")]
    # an unused even gate and a zero gate
    extra += [("unusedEv", "x2", "x3"), ("zero", "x5", "x5")]
    for g, a, b in extra:
        vals[g] = vals[a] ^ vals[b]
        gates.append((g, a, b))
    mod = analyse(n, gates, outs, vals)
    print("88@5 original :", {k: base[k] for k in ("G", "x", "y", "h", "S", "identity")})
    print("88@5 + 5 junk :", {k: mod[k] for k in ("G", "x", "y", "h", "S", "identity", "one_bb", "simple")})


def part3():
    for name in ("small-scale-aes", "lw16-4x4-gf256-inv-had", "aes-mixcolumns"):
        mat = next((CIRC / name).glob("*.mat.txt"))
        rows, n = read_matrix(mat)
        cols = [sum(((rows[o] >> i) & 1) << o for o in range(len(rows))) for i in range(n)]
        best = None
        for k in range(1, 6):
            for S in itertools.combinations(range(n), k):
                im = 0
                for i in S:
                    im ^= cols[i]
                w = k + wt(im)
                if best is None or w < best:
                    best = w
        dmin = best if best <= 5 + 0 or True else None
        # words of weight <= 5 have input part of weight <= 5, so best is the true minimum if best <= 6
        c_max = (2 * n) // best
        print(f"{name}: n={n}, minimum graph-code weight = {best} (exact if <= 6), so c(1) <= {c_max}, x >= {n - c_max}")


def part4():
    seen = {m for m, _, _ in all_circuits()}
    for d in sorted(p for p in CIRC.iterdir() if p.is_dir()):
        if d.name not in seen and d.name != "__pycache__":
            print("skipped folder:", d.name, [p.name for p in d.iterdir()][:6])


if __name__ == "__main__":
    part1()
    part3()
    part4()
