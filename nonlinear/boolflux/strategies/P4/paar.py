"""P4: randomized Paar heuristic (cancellation-free greedy pair extraction) for XOR count of a
GF(2) matrix (rows = targets as sets of column indices).  Used only as a fast screening estimate [H]."""
import random


def paar(rows, ncols, rng=None, restarts=1):
    best = None
    for r in range(restarts):
        R = [set(x) for x in rows]
        nxt = ncols
        g = 0
        while True:
            cnt = {}
            for row in R:
                if len(row) < 2:
                    continue
                el = sorted(row)
                for i in range(len(el)):
                    for j in range(i + 1, len(el)):
                        p = (el[i], el[j])
                        cnt[p] = cnt.get(p, 0) + 1
            if not cnt:
                break
            m = max(cnt.values())
            if m < 2:
                g += sum(len(row) - 1 for row in R if len(row) > 1)
                break
            cands = [p for p, c in cnt.items() if c == m]
            p = rng.choice(cands) if rng else cands[0]
            for row in R:
                if p[0] in row and p[1] in row:
                    row.discard(p[0]); row.discard(p[1]); row.add(nxt)
            nxt += 1
            g += 1
        if best is None or g < best:
            best = g
    return best
