"""invskel: with paid inputs, try every subset U of boundary forms built up front (cost |U|)."""
p = "invskel.py"; s = open(p).read()
s = s.replace("""        cost, exact = closure_cost(blev, flev, D)
""", """        if not BOUND:
            cost, exact = closure_cost(blev, flev, D)
        else:
            best = None
            for msk in range(1 << len(BOUND)):
                U = [BOUND[i] for i in range(len(BOUND)) if msk >> i & 1]
                bl = dict(blev); fl = dict(flev)
                for u in U:
                    bl[u] = 0; fl.pop(u, None); fl.pop(u ^ ONES, None) if False else None
                c, e = closure_cost(bl, {f: l for f, l in fl.items() if f not in bl}, D)
                c += len(U)
                if best is None or (c, not e) < (best[0], not best[1]): best = (c, e)
            cost, exact = best
""")
s = s.replace("""    for bf in spec.get('boundary', []):""", """    BOUND = [int(bf['table'], 16) for bf in spec.get('boundary', [])]
    for bf in spec.get('boundary', []):""")
open(p, "w").write(s)
