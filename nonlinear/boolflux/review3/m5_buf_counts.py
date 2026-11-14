"""review3 M5: a correct circuit whose output is an input, or whose two outputs are the same
signal, is written by core.write_ncff with BUF lines (zero cost); independent/verify.py lists
BUF in its per-type counts, core.metrics does not, so cli.verify_file reports
metrics_agree=False -> independent_ok=False ("VERIFICATION FAILED" in cli, verified=False in
bench.py) although both verifiers accept the function.

    python3 nonlinear/boolflux/review3/m5_buf_counts.py      (from ~/xcr-boolflux)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1])); sys.path.insert(0, str(HERE.parent))
from boolflux import core, targets  # noqa: E402
import cli  # noqa: E402

TMP = HERE / 'tmp' / 'm5'; TMP.mkdir(parents=True, exist_ok=True)
# two test functions, registered in memory only (no repository file is changed)
targets.BUILTIN['r3-wire'] = (2, 2, lambda: [((x >> 1) << 1) | ((x >> 1) & x & 1) for x in range(4)],
                              'y0 = x0 (a wire), y1 = x0 & x1')
targets.BUILTIN['r3-dup'] = (2, 2, lambda: [3 * ((x >> 1) & x & 1) for x in range(4)], 'y0 = y1 = x0 & x1')
cases = {'r3-wire': core.Circuit(2, 2, [(8, 0, 1)], [0, 2]),
         'r3-dup': core.Circuit(2, 2, [(8, 0, 1)], [2, 2])}
model = core.Model.load('xag')
for name, c in cases.items():
    n, m, table, _ = targets.load(name)
    assert c.value_table() == table
    p = TMP / ('%s.circ.txt' % name); p.write_text(core.write_ncff(c, model), encoding='utf-8')
    v = cli.verify_file(p, name, 'xag')
    ind = v['independent']
    print('%s: file has %s' % (name, [l for l in p.read_text().splitlines() if l.startswith('BUF')]))
    print('   core_ok %s, independent verifier ok %s, core counts %s, independent counts %s'
          % (v['core_ok'], ind.get('ok'), v['metrics']['counts'], ind['metrics']['counts']))
    print('   -> metrics_agree %s, independent_ok %s' % (v['metrics_agree'], v['independent_ok']))
