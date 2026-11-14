#!/usr/bin/env python3
"""aes_check every admitted circuit of a memetic run that is non-dominated among the run's admissions,
the published set and the team results; write NCFF + check + sidecar (origin, parents) to found/.
python3 verify_run.py RUNDIR TAG [AMAX]"""
import json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import core, metrics, correct, MODEL, PKG   # noqa: E402
from export_splices import team_points, FOUND   # noqa: E402
sys.path.insert(0, str(PKG / 'campaigns'))
import aes_check   # noqa: E402

d = Path(sys.argv[1]); tag = sys.argv[2]; amax = int(sys.argv[3]) if len(sys.argv) > 3 else 999
pub = [u for (u, n) in aes_check.published()]
team = [u for (u, n) in team_points() if not n.startswith('E-' + tag)]
items = []
for f in (d / 'admitted').glob('*.bfx'):
    c = core.from_kernel(f.read_text(), f.stem)
    j = json.loads(f.with_suffix('.json').read_text())
    items.append((tuple(metrics(c)), f.stem, c, j))
allm = [m for m, *_ in items]
def leq(u, m): return all(a <= b for a, b in zip(u, m))
out = []
for m, h, c, j in sorted(items):
    if m[0] > amax: continue
    if any(leq(u, m) for u in pub) or any(leq(u, m) for u in team): continue
    if any(u != m and leq(u, m) for u in allm): continue
    if m in [o[0] for o in out]: continue
    assert correct(c)
    name = 'E-%s-a%d-ad%d-g%d-gd%d' % (tag, m[0], m[1], m[2], m[3])
    c.name = name
    nf = FOUND / (name + '.circ.txt')
    nf.write_text(core.write_ncff(c, MODEL, comments=['Track E %s, admitted %s, origin %s' % (tag, h, json.dumps(j['origin'])[:400])]))
    chk = subprocess.run([sys.executable, str(PKG / 'campaigns' / 'aes_check.py'), str(nf)], capture_output=True, text=True)
    (FOUND / (name + '.check.txt')).write_text(chk.stdout + chk.stderr)
    (FOUND / (name + '.json')).write_text(json.dumps({'run': str(d), 'hash': h, 'metrics': m, 'origin': j['origin']}, indent=1) + '\n')
    ok = chk.stdout.startswith('OK') and 'new Pareto point on pinned set: YES' in chk.stdout
    out.append((m, ok))
    print('%-14s %s %s' % ('/'.join(map(str, m)), 'CHECK-OK-NEW' if ok else 'CHECK-FAIL', json.dumps(j['origin'])[:160]))
print('%d points written' % len(out))
