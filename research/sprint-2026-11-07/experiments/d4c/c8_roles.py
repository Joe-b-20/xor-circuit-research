"""c8_roles.py -- (a) role table of the 89's 22 level-2 gates and 9 helpers (who uses them);
(b) for every helper mask over P89 (strict): pend_max7(s) = number of weight-7 outputs it can serve
WITHOUT a second helper (partner in V2 or a weight-5 output), and the same over all outputs."""
import re, os, sys, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c2_model as M
pc = M.pc; T = M.T; TSET = M.TSET; W = M.W; TI = M.TI
C89 = os.path.join(M.REPO, "circuits/aes-mixcolumns/aes-mixcolumns-xor89-depth4.circ.txt")
vals = {f"x{j}": 1 << j for j in range(32)}; lev = {f"x{j}": 0 for j in range(32)}; gates = []
for line in open(C89):
    m = re.match(r"^XOR\s+(\S+)\s+(\S+)\s+(\S+)", line.strip())
    if m:
        o, a, b = m.groups(); vals[o] = vals[a] ^ vals[b]; lev[o] = 1 + max(lev[a], lev[b]); gates.append((o, a, b))
users = collections.defaultdict(list)
for o, a, b in gates:
    users[a].append(o); users[b].append(o)
def desc(n):
    v = vals[n]; k = "y" if v in TSET else ("x" if lev[n] == 0 else "t")
    return f"{n}(w{pc(v)},L{lev[n]})"
print("(a) 89 level-2 gates: mask weight, operands, users")
for o, a, b in gates:
    if lev[o] == 2:
        print(f"   {o}: w{pc(vals[o])} = {desc(a)} + {desc(b)}  -> users {[desc(u) for u in users[o]]}")
print("    89 level-3 helpers:")
for o, a, b in gates:
    if lev[o] == 3 and vals[o] not in TSET:
        print(f"   {o}: w{pc(vals[o])} = {desc(a)} + {desc(b)}  -> users {[desc(u) for u in users[o]]}")
print("    89 level-4 outputs:")
for o, a, b in gates:
    if lev[o] == 4:
        print(f"   {o}: = {desc(a)} + {desc(b)}")
print("    89 level-3 outputs:")
for o, a, b in gates:
    if lev[o] == 3 and vals[o] in TSET:
        print(f"   {o}: = {desc(a)} + {desc(b)}")
# (b)
U = M.Universe(M.P89, strict=True)
pm7 = collections.Counter(); pmall = collections.Counter(); two7 = []
for s, outs in U.fan.items():
    if s in TSET: continue
    k7 = [i for i in outs if W[i] == 7 and ((T[i] ^ s) in U.V2 or (T[i] ^ s) in TSET)]
    ka = [i for i in outs if (T[i] ^ s) in U.V2 or (T[i] ^ s) in TSET]
    pm7[len(k7)] += 1; pmall[len(ka)] += 1
    if len(k7) >= 2: two7.append((s, pc(s), k7, ["V2" if (T[i] ^ s) in U.V2 else "y" for i in k7]))
print("(b) pend_max over weight-7 outputs (partner in V2 or a weight-5 output):", sorted(pm7.items()))
print("    pend_max over all outputs:", sorted(pmall.items()))
print("    helpers with pend_max7 >= 2:", len(two7), two7[:40])
json.dump({"pend_max7_hist": sorted(pm7.items()), "two7": [(s, w, k, t) for s, w, k, t in two7]}, open(os.path.join(M.HERE, "c8_roles.json"), "w"))
