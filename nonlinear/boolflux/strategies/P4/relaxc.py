"""P4: relaxed-deadline top enumeration with the C enumerator: every (15 forms + H helpers) top
meeting the relaxed deadlines (a level-1 AND only has to reach the pre targets containing it), and
for each the rank of Avail intersected with V = span X (X = x-parts of t30..t33).
A pre of amin + 4 = 14 gates needs that rank to be 4 (any inversion-input basis).

    python3 relaxc.py CIRC GD H
"""
import json
import subprocess
import sys
from pathlib import Path

import block
import circ

HERE = Path(__file__).resolve().parent


def main():
    path, gd, H = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    ref = circ.read(path)
    s = circ.symbolic(ref)
    xs = {f'x{i}' for i in range(8)}
    xm = lambda at: sum(1 << int(t[1:]) for t in at if t[0] == 'x')
    lvl1 = [o for op, o, ins in ref if op == 'AND' and all(s[i][0] <= xs for i in ins)]
    names = ['t30', 't31', 't32', 't33']
    topn = {o for op, o, ins in ref if op != 'AND' and s[o][0] <= xs}
    pren = {o for op, o, ins in ref if op != 'AND' and o not in topn and s[o][0] <= xs | set(lvl1)}
    req = block.required([g for g in ref if g[1] not in topn | pren], gd)
    forms = {}
    for op, o, ins in ref:
        if op != 'AND':
            continue
        ra = (min(req[t] for t in names if o in s[t][0]) - 1) if o in lvl1 else req.get(o, 99)
        for i in ins:
            if s[i][0] <= xs and len(s[i][0]) > 1:
                m = xm(s[i][0])
                forms[m] = min(forms.get(m, 99), ra - 1)
    X = [xm(s[t][0]) for t in names]
    inp = [str(len(forms))] + [f'{m} {d}' for m, d in forms.items()] + [str(H), str(len(X))] + [str(v) for v in X]
    r = subprocess.run([str(HERE / 'topenum_c')], input='\n'.join(inp) + '\n', capture_output=True, text=True)
    ranks = {}
    full = []
    for line in r.stdout.splitlines():
        parts = line.split('|')
        rk = int(parts[2].split()[1])
        ranks[rk] = ranks.get(rk, 0) + 1
        if rk >= 4:
            full.append(line.strip())
    print(json.dumps(dict(H=H, gd=gd, deadlines={str(m): d for m, d in forms.items()}, feasible=sum(ranks.values()),
                          cover_rank_hist=ranks, full_cover=full[:50], note=r.stderr.strip())))


if __name__ == '__main__':
    main()
