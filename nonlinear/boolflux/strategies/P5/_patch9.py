"""invskel: exact leaf cost up to one helper gate; proven lower bound otherwise.

leaf cost classes:
  exact  : one gate per required form (cost = #forms, optimal for the skeleton)
  exact+1: not closable, but closable with one extra helper form (cost = #forms + 1, optimal)
  lb+2   : neither; true cost >= #forms + 2 (kept only if that bound is within maxcost)
"""
p = "invskel.py"; s = open(p).read()
a = s.index("    def leaf(chosen):"); b = s.index("    TG = set(tg)")
s = s[:a] + '''    def exact_cost(bl, fl):
        """(cost, kind) for basis levels bl and required forms fl (form -> allowed level)."""
        n = len(fl)
        c, e = closure_cost(bl, fl, D)
        if e: return n, 'exact'
        if n + NA + 1 + extra_paid[0] > a.maxcost: return n + 2, 'lb+2'
        sig = list(bl) + list(fl)
        sig += [x ^ ONES for x in sig]
        cand = set()
        for i in range(len(sig)):
            for j in range(i + 1, len(sig)):
                h = sig[i] ^ sig[j]
                if h not in bl and h not in fl and h not in (0, ONES) and (h ^ ONES) not in fl:
                    cand.add(h)
        for h in cand:
            f2 = dict(fl); f2[h] = D
            c, e = closure_cost(bl, f2, D)
            if e: return n + 1, 'exact+1'
        return n + 2, 'lb+2'

    extra_paid = [0]

    def leaf(chosen):
        stats['leaves'] += 1
        blev = {v: 0 for v in VF}
        for c in chosen: blev[c[3]] = c[0]
        flev = {}
        for c in chosen:
            for L in (c[1], c[2]):
                if L not in blev: flev[L] = min(flev.get(L, D), c[0] - 1)
        for t in tg:
            if t not in blev: flev.setdefault(t, D)
        best = None
        masks = range(1 << len(BOUND)) if BOUND else [0]
        for msk in masks:
            U = [BOUND[i] for i in range(len(BOUND)) if msk >> i & 1]
            bl = dict(blev)
            for u in U: bl[u] = 0
            fl = {f: l for f, l in flev.items() if f not in bl}
            extra_paid[0] = len(U)
            c, kind = exact_cost(bl, fl)
            c += len(U)
            if best is None or c < best[0] or (c == best[0] and kind != 'lb+2' and best[1] == 'lb+2'):
                best = (c, kind)
        cost, kind = best
        stats.setdefault(kind, 0); stats[kind] += 1
        if cost + NA > a.maxcost: return
        results.append((cost + NA, kind, [(c[0], c[1], c[2], c[3]) for c in chosen]))

''' + s[b:]
s = s.replace("""    results.sort(key=lambda x: (x[0], not x[1]))""", """    results.sort(key=lambda x: (x[0], x[1] == 'lb+2'))""")
s = s.replace("""    print('nodes %d leaves %d %.1fs' % (stats['nodes'], stats['leaves'], time.time() - t0))""",
              """    print('nodes %d leaves %d %.1fs' % (stats['nodes'], stats['leaves'], time.time() - t0), stats)""")
s = s.replace("""        print('cost', c, 'exact' if e else 'upper', ' '.join(""", """        print('cost', c, e, ' '.join(""")
s = s.replace("""    json.dump([{'cost': c, 'exact': e, 'ands'""", """    json.dump([{'cost': c, 'exact': e == 'exact' or e == 'exact+1', 'kind': e, 'ands'""")
open(p, "w").write(s)
