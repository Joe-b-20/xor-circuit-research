src = open("trb.py").read()
a = src.index("                if cst:")
b = src.index("                tmap[s] = g")
new = """                if cst:
                    if x >= len(leaves):      # a new XOR root: emit an XNOR twin (the XOR dies if unused)
                        u, v = sig_gate[x]
                        gates.append((XNOR, bsig(u), bsig(v))); g = n + len(gates) - 1
                    else:
                        gates.append((NOT, g, g)); g = n + len(gates) - 1
"""
src = src[:a] + new + src[b:]
open("trb.py", "w").write(src)
