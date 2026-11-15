"""Where best_table.py spends its time (old code path, staged so that no stage runs long)."""
import sys, time, hashlib
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'nonlinear' / 'boolflux' / 'campaigns')); sys.path.insert(0, str(REPO / 'nonlinear'))
import best_table as BT
import aes_check as AC
from boolflux import core

t = time.time(); files = BT.candidates(); print('glob: %d files, %.1f s' % (len(files), time.time() - t), flush=True)
model = core.Model.load('nist')
t = time.time(); raw = {}
for f in files:
    raw.setdefault(hashlib.sha1(f.read_bytes()).digest(), f)
print('read+sha1 all: %.1f s; distinct contents %d' % (time.time() - t, len(raw)), flush=True)
sample = files[::8]
t = time.time(); tup = set()
for f in sample:
    try:
        c = core.from_kernel(f.read_text()) if f.suffix == '.bfx' else core.read_ncff(str(f))
        m = c.metrics(model)
    except Exception as e:
        continue
    tup.add((m['A'], m['AD'], m['G'], m['GD']))
dt = time.time() - t
print('parse+metrics of %d files: %.1f s (%.2f ms each, est. all %.0f s); distinct tuples in sample %d' % (
    len(sample), dt, 1000 * dt / len(sample), dt * 8, len(tup)), flush=True)
t = time.time(); pub = AC.published(); print('published(): %.1f s, %d circuits' % (time.time() - t, len(pub)), flush=True)
t = time.time()
new = {x for x in tup if not any(BT.le(u, x) for u, _ in pub)}
par = {x for x in new if not any(u != x and BT.le(u, x) for u in new)}
print('dominance on the sample: %.1f s; new %d pareto %d' % (time.time() - t, len(new), len(par)), flush=True)
