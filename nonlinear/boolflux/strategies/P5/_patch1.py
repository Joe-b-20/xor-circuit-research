p = "invskel.py"; s = open(p).read()
s = s.replace("""    ap.add_argument('--out')
    a = ap.parse_args()""", """    ap.add_argument('--out')
    ap.add_argument('--prefix', default='', help='fixed first ANDs: lev:L1:L2,... (hex tables)')
    ap.add_argument('--maxcost', type=int, default=99, help='keep leaves with cost <= this')
    a = ap.parse_args()""")
s = s.replace("""    levspans = [S0] * (D + 1)
    dfs([], S0, levspans, NA - r0, None)""", """    levspans = [S0] * (D + 1)
    chosen = []; S = S0; h = NA - r0; key = None
    for item in filter(None, a.prefix.split(',')):
        lev, x, y = item.split(':'); lev = int(lev); L1, L2 = sorted((int(x, 16), int(y, 16)))
        assert L1 in levspans[lev - 1] and L2 in levspans[lev - 1], item
        P = L1 & L2
        if not any((P ^ t) in S for t in T if t): h -= 1
        S = span_add(S, P); levspans = list(levspans)
        for l in range(lev, D + 1): levspans[l] = span_add(levspans[l], P)
        chosen.append((lev, L1, L2, P)); key = (lev, L1, L2)
    print('prefix', len(chosen), 'helpers left', h, flush=True)
    dfs(chosen, S, levspans, h, key)""")
s = s.replace("""        results.append((cost + NA, exact,""", """        if cost + NA > a.maxcost: return
        results.append((cost + NA, exact,""")
open(p, "w").write(s)
