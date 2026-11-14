#!/usr/bin/env python3
"""make_plan.py OUT.json SECONDS SEEDS CASES ARMS   e.g. plan.json 60 1-5 a36,p104 control,chain
An arm is control | chain | chain:key=v:key=v (chain with overrides; the tag gets a short suffix)."""
import json, sys
from pathlib import Path

NIST = Path.home() / 'xcr-boolflux/nonlinear/nist/aes-sbox'
RES = Path.home() / 'xcr-boolflux/nonlinear/boolflux/results/aes'
CASES = {
    'p103': (NIST / 'aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt', {}),
    'p104': (NIST / 'aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt', {}),
    'a28g124': (NIST / 'aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt', {'A': 28}),
    'a28ad4': (NIST / 'aes-sbox-a28-ad4-g131-gd31-xx103-43.circ.txt', {'A': 28, 'AD': 4}),
    'a33gd15': (NIST / 'aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt', {'GD': 15}),
    'a36': (NIST / 'aes-sbox-a36-ad4-g142-gd13-xx106-19.circ.txt', {'A': 36, 'AD': 4, 'GD': 13}),
    'gd20': (NIST / 'aes-sbox-a32-ad5-g109-gd20-xx77-4.circ.txt', {'GD': 20}),
    # A in [29, 31]: every published circuit with A <= 31 has G >= 124, so G <= 123 there is a new point
    'a28A29': (NIST / 'aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt', {'A': 29}),
    'a28A30': (NIST / 'aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt', {'A': 30}),
    'a28A31': (NIST / 'aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt', {'A': 31}),
    'a28g128A31': (NIST / 'aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt', {'A': 31, 'GD': 20}),
    'a28ad4A31': (NIST / 'aes-sbox-a28-ad4-g131-gd31-xx103-43.circ.txt', {'A': 31, 'AD': 4}),
    'p104A31': (NIST / 'aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt', {'A': 31}),
    'p103A31': (NIST / 'aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt', {'A': 31}),
    'a29g137': (NIST / 'aes-sbox-a29-ad5-g137-gd32-xx108-22.circ.txt', {'A': 29}),
    'a29g137A31': (NIST / 'aes-sbox-a29-ad5-g137-gd32-xx108-22.circ.txt', {'A': 31}),
    'a29ad6': (NIST.parent / 'sbox/aes-sbox-fwd-a29-ad6-g138-gd38-xx109-14.circ.txt', {'A': 29}),
    'a30g147': (NIST / 'aes-sbox-a30-ad4-g147-gd36-xx117-13.circ.txt', {'A': 30}),
}


def seeds(s):
    a, b = s.split('-'); return range(int(a), int(b) + 1)


out, secs, sd, cases, arms = sys.argv[1:6]
plan = []
for s in seeds(sd):
    for case in cases.split(','):
        start, caps = CASES[case]
        for arm in arms.split(','):
            parts = arm.split(':'); base = parts[0]; sets = parts[1:]
            name = base if not sets else base + ''.join(x.split('=')[0][:2] + x.split('=')[1] for x in sets).replace('.', '').replace('_', '')
            plan.append({'tag': '%s-%s-s%d' % (case, name, s), 'start': str(start), 'seed': s, 'seconds': float(secs),
                         'arm': base, 'caps': caps, 'set': sets})
Path(out).write_text(json.dumps(plan, indent=1))
print(len(plan), 'jobs')
