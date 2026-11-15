"""Extract the GF(2^4) inversion interface of a tower-field AES S-box circuit (track P5).

Given an NCFF circuit, a list of signal names as block inputs and a list of signal names as
block outputs, check that the outputs are functions of the inputs (over the 256 S-box inputs)
and print their truth tables over the input variables (bit v of the table index = value of
input v, input 0 = least significant bit).

usage: python3 invext.py FILE --ins t30,t31,t32,t33 --outs t36,t39,t40,t43,...
"""
import argparse, sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from boolflux.core import read_ncff  # noqa


def names_of(path):
    """signal name -> signal index, following read_ncff's order (inputs, then gates in file order)."""
    txt = Path(path).read_text()
    body = txt.split('begin SLP')[1].split('end SLP')[0]
    names = ['x%d' % i for i in range(8)]
    for line in body.splitlines():
        line = line.split('%')[0].strip()
        if not line: continue
        names.append(line.split()[1])
    return {nm: i for i, nm in enumerate(names)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file'); ap.add_argument('--ins', required=True); ap.add_argument('--outs', required=True)
    a = ap.parse_args()
    c = read_ncff(a.file)
    idx = names_of(a.file)
    tabs = c.tables()
    ins = a.ins.split(','); outs = a.outs.split(',')
    k = len(ins)
    res = {o: [None] * (1 << k) for o in outs}
    for x in range(256):
        key = sum(((tabs[idx[s]] >> x) & 1) << v for v, s in enumerate(ins))
        for o in outs:
            val = (tabs[idx[o]] >> x) & 1
            if res[o][key] is None: res[o][key] = val
            elif res[o][key] != val:
                print('NOT A FUNCTION', o); return 1
    for o in outs:
        t = res[o]
        if None in t: print(o, 'partial', t); continue
        print(o, '0x%04x' % sum(b << i for i, b in enumerate(t)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
