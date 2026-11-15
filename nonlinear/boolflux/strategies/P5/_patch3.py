p = "invskel.py"; s = open(p).read()
a = s.index("def closure_cost(basis, forms):"); b = s.index("def main():")
s = s[:a] + '''def closure_cost(blev, flev, D):
    """Level-aware linear cost.  blev: basis table -> AND level (inputs 0, ANDs their level);
    flev: required form -> highest AND level it may have (operand of a level-l AND: l-1;
    target: D).  Stage l uses signals of level <= l only.  Returns (cost, exact): exact when
    every form is one XOR/XNOR of two signals available at its stage (then cost = #forms,
    a lower bound, so optimal); otherwise a greedy upper bound."""
    avail = {}
    for t, l in blev.items(): avail[t] = l; avail[t ^ ONES] = l
    avail[0] = 0; avail[ONES] = 0
    rem = dict(flev)
    cost = 0; exact = True
    for st in range(0, D + 1):
        changed = True
        while changed:
            changed = False
            al = [g for g, l in avail.items() if l <= st]
            alset = set(al)
            for f in [f for f, l in rem.items() if l >= st]:
                if any((f ^ g) in alset for g in al):
                    del rem[f]; avail[f] = st; avail[f ^ ONES] = st; cost += 1; changed = True
                    al.append(f); al.append(f ^ ONES); alset.add(f); alset.add(f ^ ONES)
        # forms due at this stage that are still missing: 2 gates if f = g^h^k, else 3 (crude)
        for f in [f for f, l in rem.items() if l == st]:
            exact = False
            al = [g for g, l in avail.items() if l <= st]
            alset = set(al)
            two = any((f ^ g ^ h) in alset for g, h in combinations(al, 2))
            cost += 2 if two else 3
            del rem[f]; avail[f] = st; avail[f ^ ONES] = st
    return cost, exact


''' + s[b:]
s = s.replace('''        basis = V + [c[3] for c in chosen]
        bset = set(basis)
        forms = set()
        for c in chosen:
            for L in (c[1], c[2]):
                if L not in bset: forms.add(L)
        for t in tg:
            if t not in bset: forms.add(t)
        cost, exact = closure_cost(basis, forms)''', '''        blev = {v: 0 for v in V}
        for c in chosen: blev[c[3]] = c[0]
        flev = {}
        for c in chosen:
            for L in (c[1], c[2]):
                if L not in blev: flev[L] = min(flev.get(L, D), c[0] - 1)
        for t in tg:
            if t not in blev: flev.setdefault(t, D)
        cost, exact = closure_cost(blev, flev, D)''')
open(p, "w").write(s)
