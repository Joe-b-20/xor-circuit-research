"""c1_facts.py -- structural facts for scope C (first layer = P89, level 2 free), used to design the
branching.  Read-only on the repo.  Writes c1_facts.json + stdout.

  U2  = triples x+p / quartets p+p' over P89 (1060);  V2 = inputs u P89 u U2 (1118)
  S   = (U2 + V2) \\ (V2 u {0})  (189,027): every mask a level-3 gate can carry over P89
  per output o:  C3(o) = level-3 constructions {u, v}, u in U2, v in V2, u^v = o
                 R1(o) = {s in S : o^s in V2}      (level-4 recipe with one level-3 operand)
                 R2(o) = {{s,t} in S : s^t = o}    (level-4 recipe with two level-3 operands)
  per s in S:    fan-out f(s) = #outputs o with o^s in S u V2;  f1(s) = #outputs with o^s in V2
"""
import json, os, sys, time, itertools, collections
HERE = os.path.dirname(os.path.abspath(__file__))
D4B = os.path.join(os.path.dirname(HERE), "d4bound")
N = 32; INPUTS = [1 << j for j in range(N)]
pc = lambda v: bin(v).count("1")
F = json.load(open(os.path.join(D4B, "d1_facts.json")))
REPO = os.path.expanduser("~/xor-circuit-research")
MAT = os.path.join(REPO, "circuits/aes-mixcolumns/aes-mixcolumns.mat.txt")
toks = " ".join(l.split("%")[0] for l in open(MAT).read().splitlines()).split()
r, c = int(toks[1]), int(toks[2]); bits = list(map(int, toks[3:3 + r * c]))
T = [sum(bits[i * c + j] << j for j in range(c)) for i in range(r)]; TSET = set(T); W = [pc(t) for t in T]
TI = {t: i for i, t in enumerate(T)}
P = F["P89"]; Pset = set(P)
t0 = time.time()
U2 = set()
for pr in P:
    for x in INPUTS:
        if not (pr & x): U2.add(pr | x)
for a, b in itertools.combinations(P, 2):
    if not (a & b): U2.add(a | b)
U2 = sorted(U2); U2set = set(U2)
base = set(INPUTS) | Pset
V2 = base | U2set; V2l = sorted(V2)
S = set()
cons = collections.defaultdict(list)
for u in U2:
    for v in V2l:
        if v == u: continue
        s = u ^ v
        if s == 0 or s in V2: continue
        S.add(s)
Sl = sorted(S)
print(f"|U2|={len(U2)} |V2|={len(V2)} |S|={len(S)}  {time.time()-t0:.1f}s")
# per-output level-3 constructions over P89
out = {}
C3 = {}
for i, o in enumerate(T):
    L = set()
    for u in U2:
        v = o ^ u
        if v in V2 and v != u:
            L.add((u, v) if v not in U2set or u < v else (v, u))
    C3[i] = sorted(L)
print("level-3 constructions per output (index:weight:count):")
print("  ", [(i, W[i], len(C3[i])) for i in range(32)])
typ = collections.Counter()
for i in range(32):
    for u, v in C3[i]:
        kind = "U2+input" if v in set(INPUTS) else ("U2+pair" if v in Pset else "U2+U2")
        typ[(W[i], kind)] += 1
print("  construction types (weight, kind): ", dict(typ))
cand_u = {i: sorted({x for uv in C3[i] for x in uv if x in U2set}) for i in range(32)}
print("  distinct candidate level-2 parents per output:", [len(cand_u[i]) for i in range(32)])
# recipes
R1 = {}; R2 = {}
fan = collections.defaultdict(set); fan1 = collections.defaultdict(set)
for i, o in enumerate(T):
    r1 = []; r2 = []
    for s in Sl:
        t = o ^ s
        if t in V2:
            r1.append(s); fan[s].add(i); fan1[s].add(i)
        elif t in S:
            fan[s].add(i)
            if s < t: r2.append((s, t))
    R1[i] = r1; R2[i] = r2
print("R1 sizes:", [len(R1[i]) for i in range(32)])
print("R2 sizes:", [len(R2[i]) for i in range(32)])
print(f"  total R1 {sum(map(len, R1.values()))}, R2 {sum(map(len, R2.values()))}  {time.time()-t0:.1f}s")
fh = collections.Counter(len(v) for v in fan.values()); fh[0] = len(S) - len(fan)
f1h = collections.Counter(len(v) for v in fan1.values()); f1h[0] = len(S) - len(fan1)
print("fan-out f(s) histogram (outputs servable by one level-3 mask, via S u V2):", sorted(fh.items()))
print("fan-out f1(s) histogram (via V2 only):", sorted(f1h.items()))
# fan-out restricted to weight-7 outputs and to the 6 never-level-3 outputs
never = [i for i in range(32) if not C3[i]]
print("never-level-3 outputs:", never)
fh7 = collections.Counter(sum(1 for i in v if W[i] == 7) for v in fan.values())
fhN = collections.Counter(sum(1 for i in v if i in set(never)) for v in fan.values())
print("fan-out into weight-7 outputs histogram:", sorted(fh7.items()))
print("fan-out into the 6 never-level-3 outputs histogram:", sorted(fhN.items()))
# masks of high fan-out: list a few
hi = sorted(((len(v), s) for s, v in fan.items()), reverse=True)[:12]
print("highest fan-out masks (f, weight, outputs):", [(f, pc(s), sorted(fan[s])) for f, s in hi])
# which pairs of outputs can share a helper via R1 (both t in V2)
share1 = collections.Counter()
for s, v in fan1.items():
    for a, b in itertools.combinations(sorted(v), 2):
        share1[(a, b)] += 1
print("output pairs sharing some R1-helper:", len(share1), " e.g.", sorted(share1.items())[:10])
# the 89's helpers: their recipes
L3h = F["L3h_89"]
print("89 helpers: weight, fan-out f, f1, outputs:", [(pc(s), len(fan[s]), len(fan1[s]), sorted(fan[s])) for s in L3h])
# weight histogram of S and of fan>=1 masks
print("weight histogram of S:", sorted(collections.Counter(pc(s) for s in S).items()))
print("weight histogram of masks with f(s)>=1:", sorted(collections.Counter(pc(s) for s in fan).items()))
print("weight histogram of masks with f(s)>=2:", sorted(collections.Counter(pc(s) for s, v in fan.items() if len(v) >= 2).items()))
json.dump({"never": never, "C3_count": [len(C3[i]) for i in range(32)], "cand_u": {i: cand_u[i] for i in range(32)},
           "R1_count": [len(R1[i]) for i in range(32)], "R2_count": [len(R2[i]) for i in range(32)],
           "fan_hist": sorted(fh.items()), "fan1_hist": sorted(f1h.items()), "fan7_hist": sorted(fh7.items()),
           "fanN_hist": sorted(fhN.items())}, open(os.path.join(HERE, "c1_facts.json"), "w"))
print(f"done {time.time()-t0:.1f}s")
