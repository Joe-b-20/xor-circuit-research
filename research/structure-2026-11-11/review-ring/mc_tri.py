import sys; sys.path.insert(0,"review-pair")
from rlib import *
from itertools import combinations
M=mc_model(); rows=M["rows"]
W=set()
for b in range(8):
  for c in range(4):
    bit=1<<M["idx"](c,b)
    W.add(frozenset(j for (cc,j),v in rows.items() if v&bit))
print("mirror windows",sorted(sorted(w) for w in W))
E={frozenset(p) for w in W for p in combinations(sorted(w),2)}
T=[t for t in combinations(range(8),3) if all(frozenset(p) in E for p in combinations(t,2))]
print(len(T),"triangles; cross-window:",[t for t in T if not any(set(t)<=w for w in W)])
