"""P4: exact SAT tests on the top linear layer of a circuit.

    python3 top_test.py CIRC STEPS [extra x-vectors as names of signals, e.g. t2,t5]
"""
import json
import os
import sys

import circ
import linslp


def xmask(sym):
    atoms, c = sym
    m = 0
    for a in atoms:
        assert a[0] == 'x'
        m |= 1 << int(a[1:])
    return m


def main():
    path, steps = sys.argv[1], int(sys.argv[2])
    extra = sys.argv[3].split(',') if len(sys.argv) > 3 and sys.argv[3] else []
    budget = int(sys.argv[4]) if len(sys.argv) > 4 else None
    gates = circ.read(path)
    s = circ.symbolic(gates)
    xs = {f'x{i}' for i in range(8)}
    forms = []
    for op, o, ins in gates:
        if op == 'AND':
            for i in ins:
                if s[i][0] <= xs:
                    m = xmask(s[i])
                    if m not in forms:
                        forms.append(m)
    for e in extra:
        m = xmask(s[e])
        if m not in forms:
            forms.append(m)
    base = [1 << i for i in range(8)]
    tg = [f for f in forms if f not in base]
    arrivals = deadlines = None
    if os.environ.get('P4_DEPTH'):
        import block
        gd = int(os.environ['P4_DEPTH'])
        top = [g for g in gates if g[0] != 'AND' and s[g[1]][0] <= xs]
        topn = {g[1] for g in top}
        req = block.required([g for g in gates if g[1] not in topn], gd)
        dl = {}
        for name in list(s):
            if name in topn or name in xs:
                m = xmask(s[name]) if s[name][0] <= xs else None
                if m in tg:
                    dl[m] = min(dl.get(m, 99), req.get(name, 99))
        arrivals = [0] * 8
        deadlines = [dl[t] for t in tg]
        print('deadlines', deadlines, file=sys.stderr)
    st, ch, el = linslp.slp(8, base, tg, steps, budget=budget, arrivals=arrivals, deadlines=deadlines)
    print(json.dumps(dict(status=st, steps=steps, targets=len(tg), elapsed=round(el, 2), chain=ch,
                          values=[bin(v) for v in linslp.values(base, ch)] if ch else None)))


if __name__ == '__main__':
    main()
