"""Time of the two core calls that every tool makes per circuit (review5 P18).

    python3 nonlinear/boolflux/review5/py_timing.py

Prints microseconds per call of Circuit.metrics(nist) and Circuit.value_table() on a pinned
113-gate AES circuit, and of read + parse + metrics per file.
"""
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else str(REPO / "nonlinear"))
from boolflux import core   # noqa: E402

f = sorted((REPO / 'nonlinear' / 'nist' / 'aes-sbox').glob('*.circ.txt'))[0]
c = core.read_ncff(str(f)); model = core.Model.load('nist')
for name, fn, reps in (('metrics(nist)', lambda: c.metrics(model), 3000), ('value_table()', lambda: c.value_table(), 1000),
                       ('read_ncff + metrics', lambda: core.read_ncff(str(f)).metrics(model), 500)):
    best = 1e9
    for _ in range(3):
        t = time.process_time()
        for _ in range(reps): fn()
        best = min(best, (time.process_time() - t) / reps)
    print('%-22s %7.1f us  (%s, %d gates)' % (name, 1e6 * best, f.name, len(c.gates)))
