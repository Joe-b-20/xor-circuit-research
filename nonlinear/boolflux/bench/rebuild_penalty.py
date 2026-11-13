"""Rebuild penalty: gates after skeleton -> circuit synthesis, as a function of skeleton moves.

    python3 nonlinear/boolflux/bench/rebuild_penalty.py OUT.json

For NIST AES circuits: extract the skeleton, run the skeleton kernel for k iterations with
emit_current (k = 0 means no move), and rebuild (a) from forms only (best of the three unseeded
variants) and (b) seeded with the parent circuit.  Records the accepted skeleton moves, the gate
count of each rebuild and the time each step takes.
"""
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from boolflux import core, skeleton, targets   # noqa: E402

KDIR = HERE.parent / 'kernel'
STARTS = ['aes-sbox-a32-ad5-g104-gd30-xx72-5', 'aes-sbox-a36-ad4-g142-gd13-xx106-19',
          'aes-sbox-a28-ad4-g131-gd31-xx103-43']


def main():
    out = Path(sys.argv[1]); tab = targets.aes_sbox(); ops = core.Model.load('nist').ops()
    skel_bin = Path(tempfile.mkdtemp()) / 'skel'
    subprocess.run(['gcc', '-O2', '-o', str(skel_bin), str(KDIR / 'skel.c'), '-lm'], check=True)
    rows = []
    for name in STARTS:
        c = core.read_ncff(str(HERE.parents[1] / 'nist' / 'aes-sbox' / (name + '.circ.txt')))
        t0 = time.time(); sk = skeleton.extract(c); t_extract = time.time() - t0
        outs = core.tables_from_values(8, 8, tab)
        for iters in (0, 1, 2, 5, 10, 30, 100, 300):
            for seed in (1, 2, 3):
                d = Path(tempfile.mkdtemp())
                (d / 'in').write_text(skeleton.write_skel(sk, outs))
                (d / 'cfg').write_text('in %s\nout %s\nseed %d\niters %d\nseconds 600\nemit_current 1\n'
                                       'T0 0.3\nTperiod_it 4000\n' % (d / 'in', d / 'out', seed, iters))
                t0 = time.time()
                r = subprocess.run([str(skel_bin), str(d / 'cfg')], capture_output=True, text=True, check=True)
                t_skel = time.time() - t0
                acc = sum(int(l.split()[5]) for l in r.stdout.splitlines() if l.startswith('move '))
                sk2 = skeleton.read_skel((d / 'out').read_text())
                t0 = time.time()
                un = min((skeleton.synthesize(sk2, ops, use_paar=a, paar_outputs=b) for a, b in
                          ((False, False), (True, False), (True, True))), key=lambda x: x.metrics()['G'])
                t_un = time.time() - t0
                t0 = time.time(); se = skeleton.synthesize(sk2, ops, parent=c); t_se = time.time() - t0
                assert un.value_table() == tab and se.value_table() == tab
                # how many of the parent's ANDs keep their exact function
                pf = skeleton.parent_forms(sk2, c)
                kept = sum(1 for j, g in enumerate(c.gates) if g[0] == core.OPS['AND'] and pf[8 + j] is not None)
                rows.append({'start': name, 'G0': c.metrics()['G'], 'skel_iters': iters, 'seed': seed,
                             'accepted_moves': acc, 'K': len(sk2['ands']), 'ands_kept': kept,
                             'G_unseeded': un.metrics()['G'], 'G_seeded': se.metrics()['G'],
                             't_extract_s': round(t_extract, 4), 't_skel_s': round(t_skel, 3),
                             't_synth_unseeded_s': round(t_un, 3), 't_synth_seeded_s': round(t_se, 3)})
                print(json.dumps(rows[-1]), flush=True)
    out.write_text(json.dumps(rows, indent=1) + '\n')


if __name__ == '__main__':
    main()
