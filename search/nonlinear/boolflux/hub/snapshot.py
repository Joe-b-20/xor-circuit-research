#!/usr/bin/env python3
"""Rebuild an archive as it was at time T (records admitted at or before T; cells recomputed from them in
admission order) into a new campaign directory, for A/Bs that must start from the same state.

    python3 snapshot.py SRC_CAMPAIGN T_UNIX DST_CAMPAIGN
The function bank is copied as is (it may contain functions admitted after T: extra, never missing)."""
import json, shutil, sys
from pathlib import Path

src, t, dst = Path(sys.argv[1]), float(sys.argv[2]), Path(sys.argv[3])
(dst / 'archive').mkdir(parents=True, exist_ok=True)
n = 0
for f in (src / 'archive').glob('*.json'):
    if f.name == 'cells.json': continue
    r = json.loads(f.read_text())
    if r['t_admit'] <= t:
        shutil.copy(f, dst / 'archive' / f.name); shutil.copy(f.with_suffix('.bfx'), dst / 'archive' / (f.stem + '.bfx')); n += 1
if (src / 'funcbank').exists():
    shutil.copytree(src / 'funcbank', dst / 'funcbank', dirs_exist_ok=True)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from boolflux.hub.archive import Archive   # noqa: E402
ar = Archive(dst); ar._save_cells(); ar.write_index()
print('records', n, 'cells', len(ar.cells), 'front', len(ar.front()))
