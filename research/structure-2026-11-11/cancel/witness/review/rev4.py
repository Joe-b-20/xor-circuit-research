"""Review, part 4: recorded 88/89/97 circuits, charges of C and of transposes under several chain orders.
Direct evaluation only.  usage: python3 rev4.py"""
import os, random
from rev import mixcolumns, analyse, evaluate, transpose

M = mixcolumns()
bm = {j: sum(1 << (8 * k + j) for k in range(4)) for j in range(8)}
MT = {(k, b): sum(1 << (8 * c + j) for (c, j) in M if M[(c, j)] >> (8 * k + b) & 1) for k in range(4) for b in range(8)}
D = os.path.expanduser("~/xor-circuit-research/circuits/aes-mixcolumns")

def parse(fn):
    G = [l.split()[1:] for l in open(fn) if l.startswith("XOR ")]
    node = {"x%d" % i: i for i in range(32)}
    gates, todo = [], G[:]
    while todo:
        rest = []
        for o, a, b in todo:
            if a in node and b in node:
                gates.append((node[a], node[b])); node[o] = 31 + len(gates)
            else:
                rest.append((o, a, b))
        assert len(rest) < len(todo); todo = rest
    return gates, node

for f in ["aes-mixcolumns-xor88-depth5.circ.txt", "aes-mixcolumns-xor89-depth4.circ.txt", "aes-mixcolumns-xor97-depth3.circ.txt"]:
    gates, node = parse(os.path.join(D, f))
    vals = evaluate(32, gates)
    # interface: y_(8b+r) = bit r of byte b
    assert all(vals[node["y%d" % (8 * c + j)]] == M[(c, j)] for c in range(4) for j in range(8)), "interface"
    r, *_ = analyse(32, gates, M, bm, given={(c, j): node["y%d" % (8 * c + j)] for c in range(4) for j in range(8)})
    out = [f[:22], "C: G %d union %d live %s" % (r["G"], r["union"], r["fully_live"])]
    onl = [node["y%d" % p] for p in range(32)]
    for pol in ["reader", "reverse", "outfirst"] + ["rand%d" % s for s in range(4)]:
        tg, tout = transpose(32, gates, onl, pol, random.Random(int(pol[4:]) if pol.startswith("rand") else 0))
        rT, *_ = analyse(32, tg, MT, bm, given={(k, b): tout[8 * k + b] for k in range(4) for b in range(8)})
        out.append("%s:%d" % (pol, rT["union"]))
    print(" ".join(out))
