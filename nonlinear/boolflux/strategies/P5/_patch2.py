p = "invskel.py"; s = open(p).read()
old = s[s.index("    def dfs(chosen, S, levspans, helpers_left, last_key):"):s.index("    levspans = [S0] * (D + 1)\n    chosen = []")]
new = '''    TG = set(tg)

    def lb_of(chosen):
        B = set(V) | {c[3] for c in chosen}
        F = set()
        for c in chosen:
            for L in (c[1], c[2]):
                if L not in B: F.add(L)
        need = F | (TG - B)
        rem = NA - len(chosen)
        return len(need) - min(rem, len(TG - B - F)), B, F

    def dfs(chosen, S, levspans, helpers_left, last_key):
        stats['nodes'] += 1
        r = r_of(S)
        k = len(chosen)
        if r == 0 and k == NA:
            leaf(chosen); return
        if k == NA: return
        if r > NA - k: return
        lb, B, F = lb_of(chosen)
        slack = a.maxcost - NA - lb
        if slack < 0: return
        curlev = chosen[-1][0] if chosen else 1
        for lev in range(curlev, D + 1):
            src = levspans[lev - 1]
            low = levspans[lev - 2] if lev >= 2 else set()
            forms = sorted(f for f in src if f not in (0, ONES))
            free = [f for f in forms if f in B or f in F or f in TG]
            if slack >= 2:
                pairs = ((forms[i], L2) for i in range(len(forms)) for L2 in forms[i + 1:])
            elif slack == 1:
                seen = set()
                def gen1():
                    for L1 in free:
                        for L2 in forms:
                            if L2 == L1: continue
                            pr = (L1, L2) if L1 < L2 else (L2, L1)
                            if pr in seen: continue
                            seen.add(pr); yield pr
                pairs = gen1()
            else:
                pairs = ((free[i], L2) for i in range(len(free)) for L2 in free[i + 1:])
            for L1, L2 in pairs:
                if lev >= 2 and L1 in low and L2 in low: continue
                key = (lev, L1, L2)
                if lev == curlev and chosen and key <= last_key: continue
                P = L1 & L2
                if P in S: continue          # useless AND (already in span)
                lowers = any((P ^ t) in S for t in T if t)
                h = helpers_left
                if not lowers:
                    if h == 0: continue
                    h -= 1
                ch2 = chosen + [(lev, L1, L2, P)]
                if NA + lb_of(ch2)[0] > a.maxcost: continue
                S2 = span_add(S, P)
                ls2 = list(levspans)
                for l in range(lev, D + 1): ls2[l] = span_add(ls2[l], P)
                dfs(ch2, S2, ls2, h, key)

'''
s = s.replace(old, new)
open(p, "w").write(s)
