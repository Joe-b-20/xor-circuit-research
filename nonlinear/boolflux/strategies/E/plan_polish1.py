#!/usr/bin/env python3
"""Polish A/B: gate kernel (bfx_new, lex cost,gd) from each splice vs from its two parents, same caps,
same seconds, same seeds.  Writes PLAN.json."""
import json, sys
from pathlib import Path

F = Path.home() / 'xs-campaigns/2026-11-13-aes/E/found'
N = Path.home() / 'xcr-boolflux/nonlinear/nist/aes-sbox'
R = Path.home() / 'xcr-boolflux/nonlinear/boolflux/results/aes'
secs = float(sys.argv[2]); seeds = [int(s) for s in sys.argv[3].split(',')]
cases = [
    # name, splice file, parents, caps
    ('A31gd20', F / 'E-splice-a31-ad5-g119-gd20.circ.txt',
     [N / 'aes-sbox-a32-ad5-g107-gd22-xx75-4.circ.txt', N / 'aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt'], {'A': 31, 'GD': 20}),
    ('A31', F / 'E-splice-a31-ad5-g119-gd20.circ.txt',
     [N / 'aes-sbox-a32-ad5-g107-gd22-xx75-4.circ.txt', N / 'aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt'], {'A': 31}),
    ('A32gd19', F / 'E-splice-a32-ad5-g113-gd19.circ.txt',
     [N / 'aes-sbox-a32-ad4-g127-gd15-xx95-7.circ.txt', N / 'aes-sbox-a32-ad5-g110-gd22-xx78-3.circ.txt'], {'A': 32, 'GD': 19}),
    ('A32gd24', F / 'E-splice-a32-ad5-g106-gd24.circ.txt',
     [N / 'aes-sbox-a32-ad5-g107-gd22-xx75-4.circ.txt', N / 'aes-sbox-a32-ad5-g105-gd26-xx73-5.circ.txt'], {'A': 32, 'GD': 24}),
]
plan = []
for s in seeds:
    for name, sp, parents, caps in cases:
        plan.append({'tag': '%s-splice-s%d' % (name, s), 'start': str(sp), 'seed': s, 'seconds': secs, 'arm': 'control', 'caps': caps})
        for i, p in enumerate(parents):
            plan.append({'tag': '%s-parent%d-s%d' % (name, i + 1, s), 'start': str(p), 'seed': s, 'seconds': secs, 'arm': 'control', 'caps': caps})
Path(sys.argv[1]).write_text(json.dumps(plan, indent=1))
print(len(plan), 'jobs')
