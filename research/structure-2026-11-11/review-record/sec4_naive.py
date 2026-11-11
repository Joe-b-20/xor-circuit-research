"""Section 4, first bullet: does every MixColumns circuit lose >= 32 gates under restriction to (u,v,u,v)?

Build normalised 'row chain' circuits (each output row accumulated input by input in a random order,
reusing a signal when its mask already exists, so all masks are distinct), and count the gates that
disappear on restriction (restricted value 0, a restricted input, or a duplicate of an earlier
restricted value). The claim in RECORD section 4 would need >= 16 + 16 for every circuit.
"""
import random

from lib import CIRC, read_matrix
from sec4_restrict import restrict

rows, n = read_matrix(CIRC / "aes-mixcolumns/aes-mixcolumns.mat.txt")
rng = random.Random(1)
best = None
for trial in range(2000):
    have = {1 << i for i in range(32)}
    order = []  # gate masks in order
    for r in rng.sample(rows, 32):
        bits = [1 << i for i in range(32) if (r >> i) & 1]
        rng.shuffle(bits)
        acc = bits[0]
        for b in bits[1:]:
            acc ^= b
            if acc not in have:
                have.add(acc)
                order.append(acc)
    seen = {1 << j for j in range(16)}
    gone = 0
    for m in order:
        rm = restrict(m)
        if rm == 0 or rm in seen:
            gone += 1
        seen.add(rm)
    if best is None or gone < best[0]:
        best = (gone, len(order))
print("row-chain circuits: fewest disappearing gates over 2000 trials =", best[0], "of G =", best[1])
