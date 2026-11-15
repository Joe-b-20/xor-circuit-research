"""P4: real cost of relaxed inversion skeletons (allM run: all 15 linear forms free) for every
input basis M of span(t30..t33): free signals = the 4 rows of M (as truth tables) + the ANDs;
cost = 5 + closure_cost (P5's invskel model, frozen copy).

    python3 evalkeep.py SPEC.json LOG [LOG ...]       (KEEP lines from invskel_frozen_v2.py)
"""
import itertools
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / 'xs-campaigns/2026-11-15-targets/P4/runs/inv17'))
import invskel_frozen as IS  # noqa: E402


def rank(rows):
    rows = [r for r in rows if r]
    rk = 0
    while rows:
        p = max(rows)
        hb = p.bit_length() - 1
        rows = [r ^ p if (r >> hb) & 1 else r for r in rows if r != p]
        rows = [r for r in rows if r]
        rk += 1
    return rk


def main():
    spec = json.load(open(sys.argv[1]))
    base = [int(i['table'], 16) for i in spec['inputs']][:4]
    tg = [int(t['table'], 16) for t in spec['targets']]
    lin = {}
    for m in range(1, 16):
        t = 0
        for j in range(4):
            if (m >> j) & 1:
                t ^= base[j]
        lin[m] = t
    bases = []
    seen = set()
    for M in itertools.permutations(range(1, 16), 4):
        if rank(list(M)) < 4 or frozenset(M) in seen:
            continue
        seen.add(frozenset(M))
        bases.append(M)
    skels = []
    for lg in sys.argv[2:]:
        for line in open(lg):
            if line.startswith('KEEP'):
                parts = line.split()
                ands = []
                for tok in parts[3:]:
                    mm = re.match(r'L(\d+):([0-9a-f]{4})&([0-9a-f]{4})', tok)
                    ands.append((int(mm.group(1)), int(mm.group(2), 16), int(mm.group(3), 16)))
                skels.append((int(parts[1]), ands))
    print(json.dumps(dict(skeletons=len(skels), bases=len(bases))), flush=True)
    D = 5
    best_all = None
    for si, (rc, ands) in enumerate(skels):
        chosen = [(l, x, y, x & y) for l, x, y in ands]
        best = None
        minlb = None
        for M in bases:
            VF = [lin[m] for m in M]
            blev = {v: 0 for v in VF}
            for c in chosen:
                blev[c[3]] = c[0]
            flev = {}
            for c in chosen:
                for L in (c[1], c[2]):
                    if L not in blev:
                        flev[L] = min(flev.get(L, D), c[0] - 1)
            for t in tg:
                if t not in blev:
                    flev.setdefault(t, D)
            cost, exact = IS.closure_cost(blev, flev, D)
            tot = cost + 5
            lb = 5 + len(flev)
            if best is None or tot < best[0]:
                best = (tot, exact, M)
            if minlb is None or lb < minlb[0]:
                minlb = (lb, M)
        rec = dict(i=si, relaxed=rc, best_real=best[0], exact=best[1], M=list(best[2]), min_lower_bound=minlb[0], lb_M=list(minlb[1]), ands=ands)
        print(json.dumps(rec), flush=True)
        if best_all is None or best[0] < best_all[0]:
            best_all = (best[0], si)
    print(json.dumps(dict(done=True, best=best_all)), flush=True)


if __name__ == '__main__':
    main()
