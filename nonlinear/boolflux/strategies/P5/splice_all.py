"""Splice every skeleton of an invskel.py result file (cost <= --maxcost) into the base circuit,
verify each on all 256 inputs (core evaluation vs the AES table) and print A AD G GD per rank.
Writes OUTDIR/<tag>_r<rank>.circ.txt for the verified ones.  aes_check.py is run separately on
any file that is kept as a result.

usage: python3 splice_all.py BASE SPEC SKEL.json --middle ... --ins ... --outdir DIR --tag T
"""
import argparse, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core, targets  # noqa

AES = targets.aes_sbox()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('base'); ap.add_argument('spec'); ap.add_argument('skel')
    ap.add_argument('--middle', required=True); ap.add_argument('--ins', required=True)
    ap.add_argument('--outdir', required=True); ap.add_argument('--tag', required=True)
    ap.add_argument('--maxcost', type=int, default=99); ap.add_argument('--limit', type=int, default=500)
    a = ap.parse_args()
    sk = json.load(open(a.skel))
    model = core.Model.load('nist')
    rows = []
    for r, s in enumerate(sk[:a.limit]):
        if s['cost'] > a.maxcost: continue
        out = Path(a.outdir) / ('%s_r%d.circ.txt' % (a.tag, r))
        p = subprocess.run([sys.executable, str(HERE / 'blocksplice.py'), a.base, a.spec, a.skel,
                            '--rank', str(r), '--middle', a.middle, '--ins', a.ins, '--out', str(out)],
                           capture_output=True, text=True)
        if p.returncode:
            print(r, 'splice failed', p.stderr.strip().splitlines()[-1]); continue
        c = core.read_ncff(str(out))
        ok = c.value_table() == list(AES) if not isinstance(AES, dict) else None
        m = c.metrics(model)
        rows.append((m['G'], m['GD'], r))
        print(r, 'cost', s['cost'], 'exact' if s['exact'] else 'upper', 'A AD G GD', m['A'], m['AD'], m['G'], m['GD'],
              'OK' if ok else 'FAIL', flush=True)
    rows.sort()
    print('best', rows[:10])


if __name__ == '__main__':
    sys.exit(main())
