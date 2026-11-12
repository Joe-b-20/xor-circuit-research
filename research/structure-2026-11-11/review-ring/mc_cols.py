import sys; sys.path.insert(0,"review-pair")
from rlib import *
M=mc_model()
rows=M["rows"]
# rows support (sheet j -> blocks)
for j in range(8):
    s=set()
    for c in range(4): s|=support(M,rows[(c,j)])
    print("sheet",j,"blocks",sorted(s))
# columns: unit (c,b) -> sheets whose rows have it
for b in range(8):
    for c in range(4):
        bit=1<<M["idx"](c,b)
        sh=sorted({j for (cc,j),v in rows.items() if v&bit})
        print("unit",c,b,"-> sheets",sh, "rows",sorted((cc,j) for (cc,j),v in rows.items() if v&bit))
