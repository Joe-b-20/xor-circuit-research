"""P4: run the C helper-set enumerator (topenum.c -> ./topenum_c) for a per-pair choice c.

    python3 topc.py CIRC GD H C9 [--V]     C9 = 9 digits (0 = A, 1 = B, 2 = C)
Deadline of both forms of pair i = the earlier of the 103's two form deadlines at that GD.
With --V, also reports per helper set the rank of (Avail intersected with V = span X'(c)).
"""
import json
import subprocess
import sys
from pathlib import Path

import pairscan
import topenum

HERE = Path(__file__).resolve().parent


def pair_deadlines(path, gd):
    gates, s, forms, inj = topenum.top_spec(path, gd)
    _, _, lvl1, pairs, X, P = pairscan.setup(path)
    dl = []
    for g, gp in pairs:
        d = min(forms.get(g, 99) if bin(g).count('1') > 1 else 99, forms.get(gp, 99) if bin(gp).count('1') > 1 else 99)
        dl.append(d)
    return pairs, X, P, dl


_PD = {}


def run(path, gd, H, c, wantV=True):
    if (path, gd) not in _PD:
        _PD[(path, gd)] = pair_deadlines(path, gd)
    pairs, X, P, dl = _PD[(path, gd)]
    forms, Xp = pairscan.choice(pairs, X, P, c)
    fd = {}
    for i in range(9):
        for f in forms[2 * i:2 * i + 2]:
            if bin(f).count('1') > 1:
                fd[f] = min(fd.get(f, 99), dl[i])
    inp = [str(len(fd))] + [f'{m} {d}' for m, d in fd.items()] + [str(H)]
    inp += [str(len(Xp) if wantV else 0)] + ([str(v) for v in Xp] if wantV else [])
    r = subprocess.run([str(HERE / 'topenum_c')], input='\n'.join(inp) + '\n', capture_output=True, text=True)
    sets = []
    for line in r.stdout.splitlines():
        parts = line.split('|')
        hs = [int(t) for t in parts[0].split()]
        mx = int(parts[1]) if len(parts) > 1 and parts[1].strip().isdigit() else None
        rk = int(parts[2].split()[1]) if len(parts) > 2 else None
        sets.append((hs, mx, rk))
    return dict(forms=len(fd), rankX=pairscan.preinj.rank(Xp), sets=sets, stderr=r.stderr.strip())


if __name__ == '__main__':
    path, gd, H, c = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), [int(ch) for ch in sys.argv[4]]
    res = run(path, gd, H, c)
    best = max((r for _, _, r in res['sets']), default=None)
    print(json.dumps(dict(c=sys.argv[4], H=H, forms=res['forms'], rankX=res['rankX'], feasible=len(res['sets']),
                          best_cover=best, sample=res['sets'][:5], note=res['stderr'])))
