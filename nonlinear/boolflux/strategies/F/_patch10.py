s = open("linres.py").read()
old_a = s[s.index("    outsig = d[\x27outputSignals\x27]"):s.index("    tmap = {}")]
new_a = """    outsig = d[\x27outputSignals\x27]
    # polarity: every XOR gate may be an XNOR; give each target root the polarity its constant asks for
    want = {}
    for t in tg:
        f = form[t]; lin = f & ~1
        if bin(lin).count(\x271\x27) > 1: want.setdefault(outsig[rowidx[lin]], set()).add(f & 1)
    pol = {j: 0 for j in range(L)}
    for k, (a, b) in enumerate(newgates):
        sgl = L + k; w = want.get(sgl, {0})
        pol[sgl] = 1 if w == {1} else 0
    built = {}
    mp = {i: i for i in range(n)}
    def xf(s):
        if s < L: return mp_get(leaves[s])
        if s in built: return built[s]
        a, b = newgates[s - L]
        x, y = xf(a), xf(b)
        op = XNOR if (pol[s] ^ pol[a] ^ pol[b]) else XOR
        gates.append((op, x, y)); built[s] = n + len(gates) - 1
        return built[s]
"""
s = s.replace(old_a, new_a)
old_b = s[s.index("            if bin(lin).count(\x271\x27) == 1:\n                j = lin.bit_length() - 2; g = mp_get(leaves[j])"):s.index("            tmap[s] = g; return g")]
new_b = """            if bin(lin).count(\x271\x27) == 1:
                j = lin.bit_length() - 2; g = mp_get(leaves[j]); p = 0
            else:
                xs = outsig[rowidx[lin]]; g = xf(xs); p = pol[xs]
            if cst != p:
                gates.append((NOT, g, g)); g = n + len(gates) - 1
"""
s = s.replace(old_b, new_b)
open("linres.py", "w").write(s)
