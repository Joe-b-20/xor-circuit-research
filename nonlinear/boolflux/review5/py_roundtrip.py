"""Round trip of every pinned NIST circuit and every results/ circuit through both formats.

read_ncff -> write_ncff (file's own names, NIST model) -> read_ncff must give the same gate
list and outputs; to_kernel -> from_kernel likewise; the independent verifier's metrics on the
ORIGINAL file must equal core's.  Prints the exceptions.
"""
import sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'nonlinear')); sys.path.insert(0, str(REPO / 'nonlinear' / 'boolflux' / 'independent'))
import verify as V
from boolflux import core

nist = core.Model.load('nist')
files = sorted((REPO / 'nonlinear' / 'nist').glob('*/*.circ.txt')) + sorted((REPO / 'nonlinear' / 'nist').glob('*/*.slp')) \
    + sorted((REPO / 'nonlinear' / 'boolflux' / 'results').glob('*/*.circ.txt'))
bad = 0; n = 0
for f in files:
    try:
        c = core.read_ncff(str(f))
    except Exception as e:
        print('READ FAIL', f.relative_to(REPO), repr(e)[:200]); bad += 1; continue
    n += 1
    for model in (nist, None):
        try:
            t = core.write_ncff(c, model)
            c2 = core.read_ncff(t)
            if (c2.gates, c2.outputs, c2.in_names, c2.out_names) != (c.gates, c.outputs, c.in_names, c.out_names):
                print('NCFF ROUND TRIP DIFFERS', f.relative_to(REPO), model and model.name); bad += 1
        except Exception as e:
            print('WRITE FAIL', f.relative_to(REPO), repr(e)[:200]); bad += 1
    k = core.from_kernel(core.to_kernel(c))
    if (k.gates, k.outputs) != (c.gates, c.outputs):
        print('KERNEL ROUND TRIP DIFFERS', f.relative_to(REPO)); bad += 1
    im = V.compute_metrics(V.parse_file(str(f)))
    cm = c.metrics()
    if any(im[x] != cm[x] for x in ('G', 'A', 'GD', 'AD')):
        print('METRICS DIFFER', f.relative_to(REPO), {x: (cm[x], im[x]) for x in ('G', 'A', 'GD', 'AD')})
print('%d files read, %d problems' % (n, bad))
