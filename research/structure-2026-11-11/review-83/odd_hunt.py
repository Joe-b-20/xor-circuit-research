"""The non-monotone hunt records without a cross-window cancellation: what makes them non-monotone."""
import glob, json, os
import families as F

NAMES = {0b0011: "s0", 0b0110: "s1", 0b1100: "s2", 0b1001: "s3", 0b0101: "d0", 0b1010: "d1", 0b1111: "t",
         0b0001: "e0", 0b0010: "e1", 0b0100: "e2", 0b1000: "e3",
         0b1110: "E0", 0b1101: "E1", 0b1011: "E2", 0b0111: "E3"}
def nib(v, j):
    return sum(((v >> (8 * c + j)) & 1) << c for c in range(4))
def desc(v):
    return " ".join("%d:%s" % (j, NAMES[nib(v, j)]) for j in range(8) if nib(v, j))

for f in sorted(glob.glob(os.path.join(F.HUNT, "runs/*/workers/*/records/g88-*.json"))):
    if f.endswith(".verification.json"):
        continue
    gates = [tuple(g) for g in json.load(open(f))["gates"]]
    r = F.analyse(gates)
    if r is None or r["mono"] or any(c[1] for c in r["canc"]):
        continue
    print("==", f.split("hunt/")[1], "window-local", r["winloc"], "F", r["F"], "overlap", r["overlap"])
    vals = [1 << i for i in range(32)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    sp = [F.supp(v) for v in vals]
    # ancestors per output and violations
    n = 32
    for o in range(n, len(vals)):
        if vals[o] not in F.TSET:
            continue
        st, seen = [o], set()
        while st:
            x = st.pop()
            if x < n or x in seen:
                continue
            seen.add(x); st.extend(gates[x - n])
        bad = [g for g in seen if not sp[g] <= sp[o]]
        if bad:
            print("  output %d (sheet %d, %s) has ancestors outside its support:" % (o, F.TSET[vals[o]], desc(vals[o])),
                  ["%d:[%s]" % (g, desc(vals[g])) for g in sorted(bad)])
    for g, cross, C, u, tris in r["canc"]:
        a, b = gates[g - n]
        print("  cancelling gate %d: [%s] + [%s] = [%s]  cancelled %s" % (g, desc(vals[a]), desc(vals[b]), desc(vals[g]), sorted(C)))
