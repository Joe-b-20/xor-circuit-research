"""blocksplice: paid inputs / boundary forms (spec 'boundary', inputs with 'paid')."""
p = "blocksplice.py"; s = open(p).read()
s = s.replace("def build_block(V, ins, ands, targets, tnames):",
              "def build_block(V, ins, ands, targets, tnames, bound=(), U=(), paid=()):")
s = s.replace("    for t, nm in zip(V, ins): avail[t] = nm; lev[t] = 0\n",
"""    for t, nm in zip(V, ins):
        if t not in paid: avail[t] = nm; lev[t] = 0
    btab = {}
    for t, op, x, y in bound: btab[t] = ('XOR', x, y); btab[t ^ ONES] = ('XNOR', x, y)
""")
s = s.replace("""    def try1(f, st):
        if f in avail: return True
""", """    def try1(f, st):
        if f in avail: return True
        if f in btab:
            op, x, y = btab[f]; new(op, x, y, f, 0); return True
""")
# up-front U builds after new() is defined: insert before 'flev = {}'
s = s.replace("""    flev = {}
    for l, x, y in ands:""", """    for u in U:
        if u not in avail:
            op, x, y = btab[u]; new(op, x, y, u, 0)
    flev = {}
    for l, x, y in ands:""")
s = s.replace("""    blk, ren = build_block(V, ins, ands, tg, tn)""", """    bound = [(int(b['table'], 16), b.get('op', 'XOR'), b['a'], b['b']) for b in spec.get('boundary', [])]
    paid = {int(i['table'], 16) for i in spec['inputs'] if i.get('paid')}
    best = None
    for msk in range(1 << len(bound)):
        U = [bound[i][0] for i in range(len(bound)) if msk >> i & 1]
        try:
            r = build_block(V, ins, ands, tg, tn, bound, U, paid)
        except RuntimeError:
            continue
        if best is None or len(r[0]) < len(best[0]): best = r
    blk, ren = best""")
open(p, "w").write(s)
