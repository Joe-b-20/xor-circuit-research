"""Review, part 3: who reads the global gates in the witness files; an order where a remainder reuses an
already-built output; deduplicated transposes. Direct evaluation only.  usage: python3 rev3.py"""
import json, os, random
from rev import mixcolumns, construct, analyse, evaluate, transpose, WIT
from rev2 import prune, M, bm, unit, blk, K, H

for fn in ["witness_mc_wire.json", "witness_mc_block.json"]:
    g = [tuple(x) for x in json.load(open(os.path.join(WIT, fn)))]
    r, vals, outnode, F = analyse(32, g, M, bm)
    outs = set(outnode.values()); glob = set(range(32, 66))
    rd = [(t + 32) for t, (a, b) in enumerate(g) if (a in glob or b in glob) and t + 32 not in glob and t + 32 not in outs]
    print(fn, "first 34 gates are z/H:", all(32 + t < 66 for t in range(34)), "non-global non-output gates reading a global:", len(rd))
# remainder reusing an already built output (row kk built before row k)
keys = sorted(M)
inc = [(k, kk) for k in M for kk in M if k != kk and (M[kk] & ~(H[k[0]] ^ M[k])) == 0]
print("inclusions (remainder row, output row):", len(inc))
pair = [p for p in inc if p[1] < p[0]][0]
k, kk = pair
ysup = [w for w in range(32) if M[kk] >> w & 1]
od = lambda key, ws: (ysup + [w for w in sorted(ws) if w not in ysup]) if key == k else sorted(ws, key=lambda w: (w % 8, w // 8))
g, ng, hits = construct(32, unit, blk, M, od)
g = prune(32, g, list(M.values()))
r, *_ = analyse(32, g, M, bm)
print("  r%s reuses earlier output y%s:" % (k, kk), {x: r[x] for x in K})

def dedup(n, gates, outs):
    vals = evaluate(n, gates); first = {}; new = {i: i for i in range(n)}; out = []
    for t, (a, b) in enumerate(gates):
        v = vals[n + t]
        if v in first:
            new[n + t] = first[v]; continue
        out.append((new[a], new[b])); new[n + t] = n + len(out) - 1; first[v] = new[n + t]
    return out, [new[o] for o in outs]

MT = {(k, b): sum(1 << (8 * c + j) for (c, j) in M if M[(c, j)] >> (8 * k + b) & 1) for k in range(4) for b in range(8)}
for fn in ["witness_mc_block.json", "witness_mc_wire.json"]:
    g = [tuple(x) for x in json.load(open(os.path.join(WIT, fn)))]
    r, vals, outnode, F = analyse(32, g, M, bm)
    for pol in ["reader", "reverse"]:
        tg, tout = transpose(32, g, [outnode[k] for k in keys], pol)
        dg, dout = dedup(32, tg, tout)
        dg = prune(32, dg, list(MT.values()))
        rd, *_ = analyse(32, dg, MT, bm)
        print(fn, "transpose", pol, "deduplicated+pruned:", {x: rd[x] for x in K})
