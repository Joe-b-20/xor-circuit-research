"""P4: bottom matrices for per-pair operand choices (see pairscan.py).

    python3 bottomvar.py CIRC CHOICES.jsonl OUTDIR      (writes OUTDIR/<cstring>.mat.txt)
"""
import json
import sys
from pathlib import Path

import circ
import pairscan


def bottom_columns(path):
    gates, s, lvl1, pairs, X, P = pairscan.setup(path)
    xs = {f'x{i}' for i in range(8)}
    used = set()
    for op, o, ins in gates:
        if op == 'AND':
            for i in ins:
                used |= s[i][0]
    outprod = [o for op, o, ins in gates if op == 'AND' and o not in used]
    ys = [f'y{i}' for i in range(8)]
    col = {}
    for op, o, ins in gates:
        if o in outprod:
            xa = [i for i in ins if s[i][0] <= xs]
            fa = [i for i in ins if not s[i][0] <= xs][0]
            g = pairscan.xmask(s[xa[0]][0])
            pi = next(i for i, (a, b) in enumerate(pairs) if g in (a, b))
            side = 0 if pairs[pi][0] == g else 1
            col[(pi, side)] = sum(1 << j for j, y in enumerate(ys) if o in s[y][0])
    return pairs, col


def matrix(col, c):
    cols = []
    for i in range(9):
        cg, cgp = col[(i, 0)], col[(i, 1)]
        if c[i] == 0:
            cols += [cg, cgp]
        elif c[i] == 1:
            cols += [cg ^ cgp, cgp]
        else:
            cols += [cg ^ cgp, cg]
    return cols


def write_mat(path, cols):
    with open(path, 'w', newline='\n') as f:
        f.write(f'1\n8 {len(cols)}\n')
        for j in range(8):
            f.write(' '.join(str((c >> j) & 1) for c in cols) + '\n')


def main():
    path, chf, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    pairs, col = bottom_columns(path)
    for line in open(chf):
        d = json.loads(line)
        if 'c' not in d:
            continue
        cols = matrix(col, d['c'])
        name = ''.join(map(str, d['c']))
        write_mat(out / f'{name}.mat.txt', cols)
        print(name, sum(bin(c).count('1') for c in cols))


if __name__ == '__main__':
    main()
