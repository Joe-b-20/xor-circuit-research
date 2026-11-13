"""Machine review: list the events (whole-block cancellations) of the five named corpus lines with operand
supports and the sheets the event feeds. Read-only measurement of existing circuits. usage: python3 rv_events.py"""
from rv_measure import MCB, MCROWS, MCSHEET, evalc, read_kste

blk = lambda v: "".join(str(j) for j in range(8) if v & MCB[j])
for fn, ln in (("circuits_3.txt", 1451), ("circuits_3.txt", 3001), ("circuits_3.txt", 7451),
               ("circuits_3.txt", 7651), ("circuits_2.txt", 783)):
    g = read_kste(fn, ln)
    v = evalc(32, g)
    N = len(v)
    desc = [set() for _ in range(N)]
    for i in range(len(g) - 1, -1, -1):
        node = 32 + i
        if v[node] in MCSHEET:
            desc[node].add(MCSHEET[v[node]])
        for p in g[i]:
            desc[p] |= desc[node]
    for i, (a, b) in enumerate(g):
        e = v[32 + i]
        C = [c for c in range(8) if v[a] & MCB[c] and not e & MCB[c]]
        if C:
            print("%s:%d gate %d = %d{%s} + %d{%s} -> {%s}, cancels %s, output %s, feeds sheets %s"
                  % (fn, ln, 32 + i, a, blk(v[a]), b, blk(v[b]), blk(e), C, e in MCSHEET,
                     sorted(desc[32 + i])))
