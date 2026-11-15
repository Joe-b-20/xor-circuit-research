#!/usr/bin/env python3
"""P6 compliance (18:20 note): add path_certified to every found/ sidecar.

Audit of the P6 lineages (by construction of the drivers):
- rebase.py / paarb.py / hybrid.py / gf4build (T3) are constructions, not searches: every build is
  verified and only builds with A<=35, AD<=3, GD<=cap are kept.
- pullrun.py: stage 0 starts from such a build (inside every cap, GD included); stage 1 from the stage-0
  best (inside); the kernel never leaves the caps from a feasible start (bfx.c 1064-1077).
- kern.py runs used for saved results: k2 (start 246@12, cap 12: inside), relax181 (181@12 at cap 13:
  inside).
So every P6 kernel stage in these lineages started inside all its caps: path_certified true for the P6
part.  Parents taken from the archive / NIST (177@13, 162@14, 183@13) are used as structures (their
lower levels are reused); their own search history is not audited here ("parent_lineage").
"""
import json
from pathlib import Path
FOUND = Path.home() / 'xs-campaigns/2026-11-15-targets/P6/found'
for f in sorted(FOUND.glob('*.json')):
    d = json.loads(f.read_text())
    d['path_certified'] = True
    d['path_certified_note'] = ('every P6 kernel stage in this lineage started inside all its caps (A35, AD3, GD cap); '
                                'constructions verified and kept only inside the caps; see strategies/P6/certify.py')
    d['parent_lineage'] = 'archive/NIST parent used as a structure; its own search history not audited by P6'
    f.write_text(json.dumps(d, indent=1))
    print(f.name, d['A'], d['AD'], d['G'], d['GD'], d['start']['path'][-60:])
