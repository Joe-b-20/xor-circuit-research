"""Reviewer's own evaluator for MC_l circuit files (independent of mcheck.py / sbcheck.py). A check.
usage: python3 ev2.py L file [extra-line ...]   (extra lines appended, e.g. to override a gate)
Inputs gK_C: group K (1..L) unit C (0..3); bit 4(K-1)+C.
"""
import itertools, sys

L = int(sys.argv[1])
lines = open(sys.argv[2]).read().splitlines() + sys.argv[3:]
val = {}
order = []  # signal names in time order (inputs first)
for k in range(1, L + 1):
    for c in range(4):
        n = f"g{k}_{c}"; val[n] = 1 << (4 * (k - 1) + c); order.append(n)
gates, exports = [], []
over = {}
for ln in lines:
    ln = ln.split('#')[0].strip()
    if not ln: continue
    if ln.startswith('export'):
        exports += ln.split()[1:]; continue
    lhs, rhs = ln.split('=')
    a, b = [t.strip() for t in rhs.split('+')]
    nm = lhs.strip()
    if nm in over or any(g[0] == nm for g in gates):
        over[nm] = (a, b); continue
    gates.append((nm, a, b))
gates = [(n, *over.get(n, (a, b))) for n, a, b in gates]
for n, a, b in gates:
    val[n] = val[a] ^ val[b]; order.append(n)
idx = {n: i for i, n in enumerate(order)}
for n, a, b in gates:
    assert idx[a] < idx[n] and idx[b] < idx[n], n

def grp(v, k): return (v >> (4 * (k - 1))) & 15
def E(c): return 15 ^ (1 << c)
def p(c): return (1 << ((c - 1) % 4)) | (1 << c)
def span(vs):
    s = {0}
    for v in vs: s |= {x ^ v for x in s}
    return s

vals = set(val.values())
# required vectors
req = []
for k in range(1, L + 1):
    for c in range(4):
        v = E(c) << (4 * (k - 1))
        if k < L: v |= p(c) << (4 * k)
        req.append(v)
print("all required present:", all(r in vals for r in req))
evenw1 = [x for x in range(1, 16) if bin(x).count('1') % 2 == 0]
sp = span([val[e] for e in exports])
print("exports", exports, "span contains Even(w1)+0:", all(x in sp for x in evenw1))
# reduced
vl = [val[n] for n in order]
print("reduced (no zero, all distinct):", 0 not in vl and len(set(vl)) == len(vl))
# cut-1 classes
om = lambda n: grp(val[n], 1)
seen_om = set(om(n) for n in order[:4 * L] if om(n))
f1 = h1 = 0; entries = []; exits = []; far = 0
for n, a, b in gates:
    oa, ob = om(a), om(b)
    if oa and ob and oa == ob: exits.append(n)
    elif oa and ob:
        if om(n) in seen_om: h1 += 1
        else: f1 += 1
        seen_om.add(om(n))
    elif oa or ob:
        pi = b if oa else a
        entries.append((n, val[pi] >> 4))
        seen_om.add(om(n))
    else: far += 1
tau = len(exports); e1 = len(entries)
near1 = f1 + h1 + tau; P = far + len(exits)
print(f"f1={f1} h1={h1} tau={tau} near1={near1} e1={e1} exits={exits} |P|={P} far1={P+e1} cost={len(gates)+tau}")
lab = [l for _, l in entries]
print("labels (w2|w3 bits):", [format(l, '08b')[::-1] for l in lab])
print("label rank:", len(span(lab)).bit_length() - 1)
Ev = [x for x in range(1, 16) if bin(x).count('1') % 2 == 0]  # Even(w2)+0, as s-vectors
def contains_E(vs):
    s = span(vs); return all(x in s for x in Ev)
tmin = min(k for k in range(len(lab) + 1) for S in itertools.combinations(lab, k) if contains_E(S))
print("tau_min:", tmin, "sigma:", e1 - tmin)
# L_near for each exit (single, strict staging: labels of entries before exit), exact BFS
for x in exits:
    avail = [l for (n, l) in entries if idx[n] < idx[x]]
    t = val[x] >> 4
    print("exit", x, "value", format(t, '08b')[::-1], "avail labels", len(avail))
    level = {frozenset(avail)}
    for g in range(0, 5):
        if any(t in s for s in level): print("  L_near =", g); break
        level = {s | {u ^ v} for s in level for u in s for v in s if u != v and (u ^ v) not in s}
