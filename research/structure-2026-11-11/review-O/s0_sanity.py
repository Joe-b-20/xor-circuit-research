import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "review-pair"))
import olib, rlib
R = os.path.expanduser("~/xor-circuit-research/circuits/aes-mixcolumns/")
toks = open(R + "aes-mixcolumns.mat.txt").read().split()
r, c = int(toks[1]), int(toks[2]); bits = [int(t) for t in toks[3:3 + r * c]]
T = [sum(bits[i * c + j] << j for j in range(c)) for i in range(r)]
print("matrix == mat.txt:", T == olib.ROWS)
m = rlib.mc_model(); print("matrix == rlib mc_model:", all(m["rows"][(cc, j)] == olib.ROWS[8 * cc + j] for cc in range(4) for j in range(8)))
for f in ("xor88-depth5", "xor89-depth4", "xor97-depth3"):
    g = olib.parse_ncff(R + "aes-mixcolumns-%s.circ.txt" % f)
    print(f, len(g), olib.check(g, olib.ROWS))
    for order in ("fwd", "rev"):
        Tm, Tops, outs = olib.transpose(g, olib.ROWS, order=order)
        ok = all(Tm[outs[i]] == olib.MROWS[i] for i in range(32))
        rv, rops, rg = olib.reduce_mirror(Tm, Tops)
        print("  mirror", order, len(Tm) - 32, "reduced", len(rg), "computes M^T", ok, olib.check(rg, olib.MROWS))
