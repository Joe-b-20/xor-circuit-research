#!/usr/bin/env python3
"""P7: build every combination of alternative stage-1 group decompositions (s1pol.py output)
into the circuit with regroup.py and report true metrics.   rgscan.py CIRCUIT ALLDEC.json OUTDIR"""
import itertools, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s1lib as L, s1search, regroup  # noqa
from boolflux import targets
core = L.core
MODEL = core.Model.load(str(core.MODELS / 'nist.json'))
AES = targets.aes_sbox()

def sumsigs(c, f):
    T, lg, la = L.sim(c)
    return [s for s in range(c.n, c.n + len(c.gates)) if c.gates[s - c.n][0] not in core.NONLINEAR_OPS
            and (T[s] == f or T[s] == f ^ L.ONES)]

def main():
    c0 = L.load(sys.argv[1]); D = json.load(open(sys.argv[2])); out = Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
    fs = [int(x, 16) for x in D['fs']]; decs = D['decs']
    res = []
    for ch in itertools.product(*[range(len(d)) for d in decs]):
        c = c0
        try:
            for k, i in enumerate(ch):
                ss = sumsigs(c, fs[k])
                prods = [(l, a, m, b) for (l, a, m, b, g) in decs[k][i]]
                c = regroup.build(c, ss, prods)
        except Exception as e:
            res.append((999, ch, str(e))); continue
        assert c.value_table() == AES
        m = c.metrics(MODEL)
        res.append((m['G'], ch, '%d/%d/%d/%d' % (m['A'], m['AD'], m['G'], m['GD'])))
        if m['GD'] <= 10 and m['G'] <= 159:
            (out / ('rg-%s-g%d.circ.txt' % ('-'.join(map(str, ch)), m['G']))).write_text(core.write_ncff(c, MODEL))
    res.sort()
    for r in res[:15]: print(r)
    print('distribution', sorted(set(r[0] for r in res)))

if __name__ == '__main__':
    main()
