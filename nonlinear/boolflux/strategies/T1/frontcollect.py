#!/usr/bin/env python3
"""Collect T1 results that are new frontier points: every .bfx under the given dirs with A <= 28 whose
(A, AD, G, GD) is not dominated by (or equal to) any hub archive record or pinned NIST circuit and not by
any other collected result; each is aes_check'ed and copied to FOUND/front/ with a JSON sidecar
(source path).  Also new-AND-space bests are not handled here (screen.py saves those).

    python3 frontcollect.py FOUND_DIR [--exclude ID,ID] DIR...
--exclude: circuit ids (last '-' field of the file stem) that are not T1's (e.g. R1 circuits copied in as starts).
"""
import json, subprocess, sys
from pathlib import Path
PKG = Path('/home/joebachir20/xcr-boolflux/nonlinear/boolflux')
sys.path.insert(0, str(PKG.parent))
from boolflux.hub.common import core, metrics, published   # noqa: E402
HUBAR = Path('/home/joebachir20/xs-campaigns/2026-11-14-hub/long/archive')
found = Path(sys.argv[1]) / 'front'; found.mkdir(parents=True, exist_ok=True)
args = sys.argv[2:]; excl = set()
if args and args[0] == '--exclude': excl = set(args[1].split(',')); args = args[2:]
leq = lambda q, m: all(a <= b for a, b in zip(q, m))
ref = set(published())
for f in HUBAR.glob('*.json'):
    if f.name == 'cells.json': continue
    r = json.loads(f.read_text()); ref.add((r['A'], r['AD'], r['G'], r['GD']))
cand = {}
for d in args:
    for p in Path(d).rglob('*.bfx'):
        if p.stem.split('-')[-1] in excl: continue
        try: c = core.from_kernel(p.read_text(), p.stem)
        except Exception: continue
        m = metrics(c)
        if m[0] > 28 or any(leq(q, m) for q in ref): continue
        cand.setdefault(m, p)
pts = list(cand)
new = [m for m in pts if not any(q != m and leq(q, m) for q in pts)]
for m in sorted(new):
    p = cand[m]
    name = 'aes-sbox-a%d-ad%d-g%d-gd%d-%s' % (m + (p.stem.split('-')[-1],))
    out = found / (name + '.bfx')
    if not out.exists(): out.write_text(p.read_text())
    r = subprocess.run([sys.executable, str(PKG / 'campaigns' / 'aes_check.py'), str(out), '--json', str(found / (name + '.check.json'))],
                       capture_output=True, text=True)
    sc = found / (name + '.json')
    if not sc.exists():
        json.dump({'tuple': m, 'source': str(p), 'collected_by': 'strategies/T1/frontcollect.py', 'aes_check_rc': r.returncode},
                  open(sc, 'w'), indent=1)
    print(m, 'rc', r.returncode, out)
print('new front points', len(new))
