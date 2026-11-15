"""P4: split an AES S-box circuit into top / middle / bottom linear layers and write the layer maps.

    python3 layers.py CIRC OUTDIR

top    = XOR gates whose symbolic form uses only x atoms
bottom = XOR gates whose form uses only 'output-product' atoms (ANDs not read by any AND)
middle = the rest
Writes OUTDIR/bottom.mat.txt (rows = y0..y7 over the output products, XORFlux format) and
OUTDIR/top.mat.txt (rows = the distinct non-trivial x-only AND operands), plus layers.json.
"""
import json
import sys
from pathlib import Path

import circ


def split(gates):
    s = circ.symbolic(gates)
    readers = {}
    for op, o, ins in gates:
        for i in ins:
            readers.setdefault(i, []).append(op)
    ands = [o for op, o, _ in gates if op == 'AND']
    used = set()
    for op, o, ins in gates:
        if op == 'AND':
            for i in ins:
                used |= s[i][0]
    outprod = [a for a in ands if a not in used]
    xs = {f'x{i}' for i in range(8)}
    top, mid, bot = [], [], []
    for op, o, ins in gates:
        if op == 'AND':
            continue
        atoms = s[o][0]
        if atoms <= xs:
            top.append(o)
        elif atoms <= set(outprod):
            bot.append(o)
        else:
            mid.append(o)
    return s, ands, outprod, top, mid, bot


def main():
    path, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    gates = circ.read(path)
    s, ands, outprod, top, mid, bot = split(gates)
    ys = [f'y{i}' for i in range(8)]
    rows = [[1 if p in s[y][0] else 0 for p in outprod] for y in ys]
    consts = [s[y][1] for y in ys]
    with open(out / 'bottom.mat.txt', 'w', newline='\n') as f:
        f.write(f'1\n{len(rows)} {len(outprod)}\n')
        for r in rows:
            f.write(' '.join(map(str, r)) + '\n')
    xs = [f'x{i}' for i in range(8)]
    topforms = []
    gmap = {o: (op, ins) for op, o, ins in gates}
    for op, o, ins in gates:
        if op == 'AND':
            for i in ins:
                at = s[i][0]
                if at <= set(xs) and len(at) > 1 and at not in [s[t][0] for t in topforms]:
                    topforms.append(i)
    with open(out / 'top.mat.txt', 'w', newline='\n') as f:
        f.write(f'1\n{len(topforms)} 8\n')
        for t in topforms:
            f.write(' '.join('1' if x in s[t][0] else '0' for x in xs) + '\n')
    info = dict(file=path, ands=ands, outprod=outprod, top=top, mid=mid, bot=bot, topforms=topforms,
                counts=dict(top=len(top), mid=len(mid), bot=len(bot)), consts=consts,
                metrics=circ.metrics(gates))
    (out / 'layers.json').write_text(json.dumps(info, indent=1))
    print(json.dumps(info['counts']), 'outprod', len(outprod), 'topforms', len(topforms), info['metrics'])


if __name__ == '__main__':
    main()
