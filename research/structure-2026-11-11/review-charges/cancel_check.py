"""How much cancellation do the recorded circuits use?  Counts gates whose operand masks overlap
(cancellation), and of those, how many cancel a whole block component (block present in an operand
but absent from the gate)."""
import os
from common import *

d = os.path.join(ROOT, "circuits/aes-mixcolumns")
for fn in sorted(os.listdir(d)):
    if not fn.endswith(".circ.txt"):
        continue
    gates, _ = read_ncff(os.path.join(d, fn))
    v = masks(gates)
    canc = blockc = 0
    for k, (a, b) in enumerate(gates):
        if v[a] & v[b]:
            canc += 1
            if not (blocks_of(v[a]) | blocks_of(v[b])) <= blocks_of(v[32 + k]):
                blockc += 1
    print(fn, "gates with cancellation:", canc, " gates that drop a whole block:", blockc)
