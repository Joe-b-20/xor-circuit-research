src = open("invsyn.py").read()
old = """    t = [(y0, d1), (y1, d1), (y2, d1), (y3, d1), (y0 ^ y2, d1), (y1 ^ y3, d1),
         (y0 ^ y1, d2), (y2 ^ y3, d2), (y0 ^ y1 ^ y2 ^ y3, d2)]"""
new = """    t = [(y0, d1), (y1, d1), (y2, d1), (y3, d1), (y0 ^ y2, d1), (y1 ^ y3, d1)]
    if d2 <= d1:
        t += [(y0 ^ y1, d2), (y2 ^ y3, d2), (y0 ^ y1 ^ y2 ^ y3, d2)]"""
assert old in src; src = src.replace(old, new)
old = "    syn = Syn(tg, max(a.d1, a.d2) - 1, base, random.Random(a.seed))"
new = "    syn = Syn(tg, max(d for f, d in tg) - 1, base, random.Random(a.seed))"
assert old in src; src = src.replace(old, new)
old = """    print('best cost %d viol %d (extra inputs %s)' % (best[1], best[2], a.extra or '-'))"""
new = """    have = set(best[3])
    y0, y1, y2, y3 = Y
    sums = [s for s in (y0 ^ y1, y2 ^ y3, y0 ^ y1 ^ y2 ^ y3) if s not in have]
    print('best cost %d viol %d (+%d pair-sum XORs = %d) (extra inputs %s)' % (best[1], best[2], len(sums), best[1] + len(sums), a.extra or '-'))"""
assert old in src; src = src.replace(old, new)
open("invsyn.py", "w").write(src)
