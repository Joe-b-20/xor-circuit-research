"""Cross-check core.read_ncff/metrics against independent/verify.py on every published NIST AES
(inverse) S-box circuit, and the two AES tables against each other (review script).

    python3 nonlinear/boolflux/review/check_nist.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BF = HERE.parent
REPO = BF.parents[1]
sys.path.insert(0, str(BF.parent)); sys.path.insert(0, str(BF / 'independent'))
from boolflux import core, targets  # noqa: E402
import verify as V  # noqa: E402

assert targets.aes_sbox() == V.aes_sbox(), 'AES tables differ'
assert targets.aes_inv_sbox() == V.aes_inv_sbox(), 'AES inverse tables differ'
model = core.Model.load('nist')
vm = V.load_model(str(BF / 'models' / 'nist.json'))
bad = 0; n = 0
for d, tgt in (('aes-sbox', 'aes'), ('aes-invsbox', 'aes-inv')):
    table = targets.load(tgt)[2]
    for f in sorted((REPO / 'nonlinear' / 'nist' / d).glob('*.circ.txt')):
        n += 1
        c = core.read_ncff(str(f))
        cm = c.metrics(model)
        ok1 = c.value_table() == table
        r = V.verify_file(str(f), (8, 8, table), model=vm)
        im = r['metrics'] or {}
        diff = [k for k in ('G', 'A', 'GD', 'AD', 'cost') if cm.get(k) != im.get(k)]
        if not ok1 or not r['ok'] or diff:
            bad += 1
            print(f.name, 'core_ok', ok1, 'indep_ok', r['ok'], r['errors'][:2], 'metric diffs',
                  {k: (cm.get(k), im.get(k)) for k in diff})
        # round trip through write_ncff
        c.in_names = list(c.in_names); txt = core.write_ncff(c, model)
        r2 = V.verify_text(txt, (8, 8, table), model=vm)
        if not r2['ok'] or any(r2['metrics'][k] != im[k] for k in ('G', 'A', 'GD', 'AD')):
            bad += 1; print('round trip differs', f.name, r2['errors'][:2])
print('%d files, %d problems' % (n, bad))
