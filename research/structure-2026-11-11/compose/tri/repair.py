"""CHECK: hand repair of circuits_2.txt line 20: replace g77, g78 (the triangle route to output (1,1)) by
p1 = x1 + x9 [1:s0], p2 = g70 + p1 [1:E1], p3 = g63 + p2, p4 = p3 + g40 = (1,1); readers of g78 read p4.
Verifies the function, size and block-monotonicity of the result."""
from show_tri import load, mc
g = load("circuits_2.txt", 20)
old = list(g); i77, i78 = 77 - 32, 78 - 32
# build new list with wire renumbering
newg, mp = [], {i: i for i in range(32)}
for gi, (a, b) in enumerate(old):
    w = 32 + gi
    if gi == i77:
        continue
    if gi == i78:
        base = 32 + len(newg)
        newg += [(1, 9), (mp[70], base), (mp[63], base + 1), (base + 2, mp[40])]
        mp[w] = base + 3
        continue
    newg.append((mp[a], mp[b])); mp[w] = 32 + len(newg) - 1
r = mc.analyse(newg)
print("computes MixColumns:", r is not None, "G =", len(newg), "monotone =", r and r["monotone"], "dead =", r and r["dead"])
r0 = mc.analyse(old); print("original: G =", len(old), "monotone =", r0["monotone"], "violating gates =", r0["violating"])
