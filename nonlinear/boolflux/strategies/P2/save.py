#!/usr/bin/env python3
"""P2: verify a circuit with campaigns/aes_check.py and, if OK and within the target's hard
limits, save it to ~/xs-campaigns/2026-11-15-targets/P2/found/ with the BRIEF sidecar.

    python3 save.py TARGET FILE NAME --start START --method M --command C --seed S --elapsed E [--kernel K]

Refuses (exit 3) if A or AD exceeds the target's limits.  Prints the aes_check OK line.
"""
import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

H = Path.home()
REPO = H / 'xcr-boolflux'
LIM = {'T02': (28, 4), 'T06': (34, 4)}
FOUND = H / 'xs-campaigns/2026-11-15-targets/P2/found'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('target'); ap.add_argument('file'); ap.add_argument('name')
    ap.add_argument('--start', required=True); ap.add_argument('--method', required=True)
    ap.add_argument('--command', required=True); ap.add_argument('--seed', default='')
    ap.add_argument('--elapsed', type=float, default=0.0)
    ap.add_argument('--only-better', action='store_true', help='skip unless (G, GD) improves on the start')
    ap.add_argument('--ref', default=None, help='compare with this file instead of the start')
    ap.add_argument('--path-certified', default='unknown', help='true | false | unknown (COMPLIANCE-1820)')
    ap.add_argument('--reproduces', default=None)
    ap.add_argument('--kernel', default=str(H / 'xs-campaigns/2026-11-14-hub/long/bin/bfx-593fa798f5'))
    a = ap.parse_args()
    r = subprocess.run(['python3', str(REPO / 'nonlinear/boolflux/campaigns/aes_check.py'), a.file],
                       capture_output=True, text=True, cwd=str(REPO))
    line = r.stdout.splitlines()[0] if r.stdout else ''
    if r.returncode != 0 or not line.startswith('OK'):
        print('FAILED', r.stdout[-800:], r.stderr[-800:]); sys.exit(1)
    sys.path.insert(0, str(REPO / 'nonlinear'))
    from boolflux import core
    c = core.read_ncff(a.file)
    m = c.metrics()
    A, AD, G, GD = m['A'], m['AD'], m['G'], m['GD']
    la, lad = LIM[a.target]
    if A > la or AD > lad:
        print('REFUSED: outside hard limits', A, AD, G, GD); sys.exit(3)
    if a.only_better:
        s = core.read_ncff(a.ref or a.start).metrics()
        if not (G <= s['G'] and GD <= s['GD'] and (G < s['G'] or GD < s['GD'])):
            print('NOT BETTER than start', A, AD, G, GD, 'start', s['G'], s['GD']); sys.exit(0)
    FOUND.mkdir(parents=True, exist_ok=True)
    name = '%s-a%d-ad%d-g%d-gd%d-%s' % (a.target.lower(), A, AD, G, GD, a.name)
    dst = FOUND / (name + '.circ.txt')
    shutil.copyfile(a.file, dst)
    code = subprocess.run(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    side = {'target': a.target, 'A': A, 'AD': AD, 'G': G, 'GD': GD,
            'file': str(dst), 'sha256': sha(dst),
            'start': {'path': a.start, 'sha256': sha(a.start) if Path(a.start).exists() else None},
            'method': a.method, 'command': a.command, 'seed': a.seed, 'elapsed_s': a.elapsed,
            'code': {'xcr-boolflux': code + ' + uncommitted strategies/P2, strategies/F, strategies/T4',
                     'kernel': a.kernel, 'kernel_sha256': sha(a.kernel) if a.kernel and Path(a.kernel).exists() else None},
            'aes_check': line, 'utc': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'path_certified': {'true': True, 'false': False}.get(a.path_certified, 'unknown')}
    if a.reproduces: side['reproduces'] = a.reproduces
    (FOUND / (name + '.json')).write_text(json.dumps(side, indent=1) + '\n')
    print(line)
    print('saved', dst)


if __name__ == '__main__':
    main()
