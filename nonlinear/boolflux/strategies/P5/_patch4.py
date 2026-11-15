p = "blocksplice.py"; s = open(p).read()
a = s.index("def build_block(V, ins, ands, targets, tnames):"); b = s.index("def main():")
s = s[:a] + '''def build_block(V, ins, ands, targets, tnames):
    """Staged build (same rule as invskel.closure_cost): stage l emits the ANDs of level l, then
    builds every pending form allowed at level >= l from signals of level <= l, one XOR/XNOR
    each while possible; forms due at stage l that are still missing get a short chain."""
    avail = {}; lev = {}
    for t, nm in zip(V, ins): avail[t] = nm; lev[t] = 0
    out = []; cnt = [0]
    D = max([l for l, x, y in ands] + [0])

    def new(op, a, b, t, l):
        cnt[0] += 1; nm = 'b%d' % cnt[0]
        out.append((op, nm, [a, b])); avail[t] = nm; lev[t] = l; return nm

    def al_at(st):
        return [(g, gn) for g, gn in avail.items() if lev[g] <= st]

    def try1(f, st):
        if f in avail: return True
        al = al_at(st); d = {g: gn for g, gn in al}
        for g, gn in al:
            h = f ^ g
            if h in d and h != g: new('XOR', gn, d[h], f, st); return True
            h = f ^ g ^ ONES
            if h in d and h != g: new('XNOR', gn, d[h], f, st); return True
        return False

    def chain(f, st):
        al = al_at(st)
        rows = []
        for g, gn in al:
            v, comb = g, {g}
            for rv, rc in rows:
                if v ^ rv < v: v ^= rv; comb = comb ^ rc
            if v: rows.append((v, comb)); rows.sort(reverse=True)
        for target, cmp in ((f, False), (f ^ ONES, True)):
            v, comb = target, set()
            for rv, rc in rows:
                if v ^ rv < v: v ^= rv; comb = comb ^ rc
            if v == 0 and comb:
                terms = sorted(comb)
                acc = terms[0]
                for i, t in enumerate(terms[1:]):
                    last = (i == len(terms) - 2)
                    nt = acc ^ t ^ (ONES if (last and cmp) else 0)
                    if nt not in avail:
                        new('XNOR' if (last and cmp) else 'XOR', avail[acc], avail[t], nt, st)
                    acc = nt
                return True
        raise RuntimeError('form %x not in span at stage %d' % (f, st))

    flev = {}
    for l, x, y in ands:
        for L in (x, y): flev[L] = min(flev.get(L, D), l - 1)
    for t in targets: flev.setdefault(t, D)
    Dall = max(D, max(flev.values()))
    for st in range(0, Dall + 1):
        for l, x, y in ands:
            if l == st:
                new('AND', avail[x], avail[y], x & y, st)
        changed = True
        while changed:
            changed = False
            for f in [f for f, l in flev.items() if l >= st and f not in avail]:
                if try1(f, st): changed = True
        for f in [f for f, l in flev.items() if l == st and f not in avail]:
            chain(f, st)
    names = {nm: avail[t] for nm, t in zip(tnames, targets)}
    return out, names


''' + s[b:]
open(p, "w").write(s)
