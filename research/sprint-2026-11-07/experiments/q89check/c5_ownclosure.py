"""c5_ownclosure.py: remove1-neutral closure of the repo 89@4 at cap 4 under the OWN value-set model (c2d),
no pes_lib. Reports closure size, neutral/down counts per state, and comparison with pes_lib's L0 (c3_L0.json)."""
import json, os, sys, time
from collections import Counter, deque
OUT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, OUT)
import c2d_ownmodel as M

S0 = frozenset(M.D["repo_helpers"])
L0 = {frozenset(s) for s in json.load(open(f"{OUT}/c3_L0.json"))["L0"]}
t0 = time.time()
seen = {S0}; q = deque([S0]); per = Counter(); downs = 0; expanded = 0
while q and expanded < 300:
    S = q.popleft()
    out, st = M.own_remove1(S, 4)
    expanded += 1
    neu = [K for K, dg in out.items() if dg == 0 and K != S]
    dn = [K for K, dg in out.items() if dg < 0]
    downs += len(dn)
    per[len(neu)] += 1
    for K in neu:
        if K not in seen:
            seen.add(K); q.append(K)
    if expanded % 20 == 0:
        print("expanded", expanded, "reached", len(seen), f"{time.time()-t0:.0f}s", flush=True)
print(f"OWN-MODEL cap-4 closure: {len(seen)} states, complete={not q}, expanded {expanded}, neutral per state {dict(per)}, down moves {downs}, "
      f"equals pes_lib L0: {seen == L0}, {time.time()-t0:.0f}s")
