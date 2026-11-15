p = "../../hub/ops/x1_merge.py"
s = open(p).read()
if "CHAIN_S" not in s:
    s = s.replace("BEAM = 6\n", "BEAM = 6\nMAX_A = 80                # larger circuits are not scanned (one 264-AND archive member cost minutes)\nCHAIN_S = 8.0             # time limit of one reduction chain\n")
    old = '    out = {}; level = [(c, [])]\n    for _ in range(rounds):\n        nxt = {}\n        for cc, hist in level:\n'
    new = '    out = {}; level = [(c, [])]; t0 = time.time()\n    if sum(1 for g in c.gates if g[0] == 8) > MAX_A: return []\n    for _ in range(rounds):\n        nxt = {}\n        for cc, hist in level:\n            if time.time() - t0 > CHAIN_S: break\n'
    assert old in s; s = s.replace(old, new)
    open(p, "w").write(s)
print("ok")
