"""Section 4, first bullet: search for a MixColumns circuit that loses fewer than 32 gates on restriction.

Construction: a shared random 'spine' of masks built gate by gate (each new mask = earlier + earlier,
kept only if its restriction is new and nonzero), then every output row r is produced by one more
gate as (spine mask s) + (r + s) when r + s is already available, otherwise by a chain. All masks are
distinct (normalised). Count disappearing gates as in sec4_restrict.py. Verifies the circuit
computes every row.
"""
import random

from lib import CIRC, read_matrix, par
from sec4_restrict import restrict

rows, n = read_matrix(CIRC / "aes-mixcolumns/aes-mixcolumns.mat.txt")


def build(rng, spine_len):
    masks = [1 << i for i in range(32)]
    have = set(masks)
    rseen = {1 << j for j in range(16)}
    gates = []  # (mask, ia, ib)

    def add(a, b):
        m = masks[a] ^ masks[b]
        if m in have or m == 0:
            return None
        have.add(m)
        masks.append(m)
        gates.append((m, a, b))
        return len(masks) - 1

    # spine: random gates whose restriction is new
    tries = 0
    while len(gates) < spine_len and tries < 200000:
        tries += 1
        a, b = rng.randrange(len(masks)), rng.randrange(len(masks))
        m = masks[a] ^ masks[b]
        rm = restrict(m)
        if m in have or rm == 0 or rm in rseen:
            continue
        rseen.add(rm)
        add(a, b)
    idx = {m: i for i, m in enumerate(masks)}
    for r in rows:
        if r in have:
            continue
        # try one gate from two existing masks
        done = False
        for i, m in enumerate(masks):
            if (r ^ m) in idx and idx[r ^ m] != i:
                k = add(i, idx[r ^ m])
                idx[r] = k
                done = True
                break
        if not done:
            # greedy: walk from the closest existing mask by adding inputs
            best = min(range(len(masks)), key=lambda i: bin(masks[i] ^ r).count("1"))
            cur = best
            diff = masks[best] ^ r
            bits = [i for i in range(32) if (diff >> i) & 1]
            for t, bi in enumerate(bits):
                m = masks[cur] ^ (1 << bi)
                if m in idx:
                    cur = idx[m]
                else:
                    cur = add(cur, bi)
                    idx[masks[cur]] = cur
            idx[r] = cur
    assert all(r in have for r in rows)
    seen = {1 << j for j in range(16)}
    gone = 0
    for m, a, b in gates:
        rm = restrict(m)
        if rm == 0 or rm in seen:
            gone += 1
        seen.add(rm)
    return gone, len(gates)


rng = random.Random(3)
best = None
for trial in range(300):
    g = build(rng, rng.choice([40, 80, 120, 200]))
    if best is None or g[0] < best[0]:
        best = g
print("fewest disappearing gates found:", best[0], "in a normalised circuit with", best[1], "gates",
      "(claim needs >= 32)")
