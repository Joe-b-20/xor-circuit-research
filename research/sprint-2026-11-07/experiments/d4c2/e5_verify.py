"""e5_verify.py -- copy of d4c/c5_verify.py using e2_model (so found/ is d4c2/found/): turn a witness json
into a circuit file, check it with the repo's check.py (copied matrix file in found/), and evaluate it
independently on the 32 unit vectors.
usage: python3 e5_verify.py e3_TAG_sol.json
"""
import json, os, sys, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e2_model as M
HERE = M.HERE; FOUND = os.path.join(HERE, "found"); os.makedirs(FOUND, exist_ok=True)
res = json.load(open(sys.argv[1]))
U = M.Universe(M.P89, strict=res.get("strict", True))
recipes = {int(k): [tuple(z) for z in v] for k, v in res["recipes"].items()}
gates = M.witness_to_circuit(U, res["L2"], res["H3"], res["Y3"], recipes)
G = len(gates); D = max(L for *_, L in gates)
name = f"aes-mixcolumns-xor{G}-depth{D}"
path = os.path.join(FOUND, name + ".circ.txt")
M.write_circ(gates, path, name)
shutil.copy(M.MAT, os.path.join(FOUND, "aes-mixcolumns.mat.txt"))
print(f"wrote {path}: {G} gates, depth {D}")
# independent unit-vector evaluation: feed e_j, read the 32 outputs, compare with matrix column j
vals = {}
for j in range(32):
    env = {1 << k: (1 if k == j else 0) for k in range(32)}
    lev = {1 << k: 0 for k in range(32)}
    for mask, a, b, L in gates:
        env[mask] = env[a] ^ env[b]; lev[mask] = 1 + max(lev[a], lev[b])
    for i, t in enumerate(M.T):
        assert env[t] == (t >> j & 1), f"unit vector {j}: output {i} wrong"
    assert all(lev[t] <= 4 for t in M.T)
print("unit-vector evaluation: all 32 outputs correct on all 32 unit vectors, depth <= 4")
out = subprocess.run([sys.executable, os.path.join(M.REPO, "circuits/check.py"), path], capture_output=True, text=True)
print(out.stdout.strip(), out.stderr.strip())
