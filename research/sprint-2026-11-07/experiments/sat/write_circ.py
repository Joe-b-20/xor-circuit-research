"""Write a found circuit (found/found_*.json, field order = list of (v, a, b)) as NCFF .circ.txt
next to it, then verify with the repo's check.py (needs the .mat.txt beside it: copied) and by
evaluating on the 32 unit vectors here.  usage: python3 write_circ.py found/found_X.json"""
import sys, os, json, shutil, subprocess, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sat87

src = sys.argv[1]
d = json.load(open(src))
order = [tuple(x) for x in d["order"]]
# trim dead gates / duplicates: keep first occurrence, drop values no target needs
seen, trimmed = set(), []
for v, a, b in order:
    if v in seen or v in set(sat87.INPUTS):
        continue
    seen.add(v); trimmed.append((v, a, b))
users = sat87.dependents(trimmed)
live = set(sat87.TARGETS)
stack = list(live)
byv = {v: (a, b) for v, a, b in trimmed}
while stack:
    v = stack.pop()
    for o in byv.get(v, ()):
        if o in byv and o not in live:
            live.add(o); stack.append(o)
trimmed = [g for g in trimmed if g[0] in live]
gates, depth, nd = sat87.check_circuit(trimmed)
print("gates", gates, "depth", depth, "distinct", nd)
name = "aes-mixcolumns-xor%d-depth%d" % (gates, depth)
outdir = os.path.join(os.path.dirname(src), name)
os.makedirs(outdir, exist_ok=True)
shutil.copy(sat87.MAT, outdir)
# names
nm = {1 << j: "x%d" % j for j in range(32)}
tidx = {t: i for i, t in enumerate(sat87.TARGETS)}
ti = 0
lines = []
for v, a, b in trimmed:
    if v in tidx:
        nm[v] = "y%d" % tidx[v]
    else:
        ti += 1; nm[v] = "t%d" % ti
    lines.append("XOR %s %s %s" % (nm[v], nm[a], nm[b]))
hdr = ["%NCFF-0.1-2026 (NIST Circuit File Format)", "", "## File source",
       "  % Timestamp (UTC): " + time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
       "  % Not a NIST-issued circuit", "  % Found by: scoped SAT (sprint 2026-11-07, sat/), scope " + d.get("scope", "?") + " of " + d.get("circuit", "?"),
       "", "## Index of circuits (circuitName numOutputs numInputs)",
       "  % %s 32 32   %% AES MixColumns; 32-bit column; 2-input XOR basis" % name, "",
       "## Circuit", "begin circuit " + name, "",
       "  % Interface: x_(8b+r) and y_(8b+r) are bit r (LSB=0) of byte b, b=0:3",
       "  % Tally of gates (%d): %d XOR" % (gates, gates), "  % Gate depth %d" % depth, "",
       "Inputs: x0:x31", "Outputs: y0:y31", "Internal: t1:t%d" % ti, "GateSyntax: GateName Output Inputs", "",
       "begin SLP"]
path = os.path.join(outdir, name + ".circ.txt")
open(path, "w").write("\n".join(hdr + lines + ["end SLP", "end circuit", ""]))
print("wrote", path)
r = subprocess.run(["python3", os.path.join(sat87.REPO, "circuits/check.py"), path], capture_output=True, text=True)
print("check.py:", r.stdout.strip(), r.stderr.strip())
# unit-vector evaluation
ok = True
for j in range(32):
    val = {1 << i: int(i == j) for i in range(32)}
    for v, a, b in trimmed:
        val[v] = val[a] ^ val[b]
    for i, t in enumerate(sat87.TARGETS):
        if val[t] != (t >> j) & 1:
            ok = False
print("unit-vector evaluation ok:", ok)
