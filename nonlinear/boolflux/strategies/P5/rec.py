#!/usr/bin/env python3
"""P5 recorder: run aes_check.py on a circuit; if OK and A <= 32, AD <= --capad, copy it to
~/xs-campaigns/2026-11-15-targets/P5/found/ with the BRIEF sidecar.  Gate-identical files are
saved once (the name carries a hash of the gate list).

  rec.py --circ F --start S --tag T --capad K --method M --command C --seed N --elapsed E [--kernel K]
"""
import argparse, hashlib, json, subprocess, sys, time
from pathlib import Path

BF = Path.home() / 'xcr-boolflux/nonlinear/boolflux'
FOUND = Path.home() / 'xs-campaigns/2026-11-15-targets/P5/found'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    for k in ('circ', 'start', 'tag', 'method', 'command', 'kernel'): ap.add_argument('--' + k, default='')
    ap.add_argument('--capad', type=int, required=True)
    ap.add_argument('--seed', default=''); ap.add_argument('--elapsed', default='')
    a = ap.parse_args()
    p = subprocess.run([sys.executable, str(BF / 'campaigns/aes_check.py'), a.circ], capture_output=True,
                       text=True, cwd=str(BF.parents[1]))
    line = p.stdout.splitlines()[0] if p.stdout else ''
    if not line.startswith('OK'):
        print('FAIL', a.circ, line); return 1
    A, AD, G, GD = [int(x) for x in line.split('=')[1].split()[:4]]
    if A > 32 or AD > a.capad:
        print('OUTSIDE LIMITS', a.circ, A, AD, G, GD); return 2
    sys.path.insert(0, str(BF.parent))
    from boolflux import core
    c = core.read_ncff(a.circ)
    h = hashlib.sha256(repr((c.gates, c.outputs)).encode()).hexdigest()[:10]
    name = 'p5-%s-a%d-ad%d-g%d-gd%d-%s' % (a.tag, A, AD, G, GD, h)
    if any(FOUND.glob('*-%s.circ.txt' % h)):
        print('DUP', name); return 0
    FOUND.mkdir(parents=True, exist_ok=True)
    (FOUND / (name + '.circ.txt')).write_bytes(Path(a.circ).read_bytes())
    git = subprocess.run(['git', '-C', str(BF.parents[1]), 'rev-parse', '--short', 'HEAD'],
                         capture_output=True, text=True).stdout.strip()
    side = {'target': 'T05', 'A': A, 'AD': AD, 'G': G, 'GD': GD,
            'start': {'path': a.start, 'sha256': sha(a.start) if a.start and Path(a.start).exists() else None},
            'method': a.method, 'command': a.command, 'seed': a.seed, 'elapsed_s': a.elapsed,
            'code': {'git': git + ' + uncommitted strategies/P5', 'kernel_sha256': sha(a.kernel) if a.kernel else None},
            'aes_check': ' '.join(line.split()), 'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            "file": name + ".circ.txt", "path_certified": True if "repair_keep 1" in a.method else "unknown"}
    if 'ad4-113-20-p3' in a.start:
        side['path_certified'] = False
        side['path_note'] = 'own stage certified (repair_keep 1); inherited from P3 113/20 (not certified)'
    if 'ad5-104-29' in a.start or 'ad6-104-31' in a.start:
        side['path_certified'] = 'unknown'
        side['path_note'] = 'own stage certified (repair_keep 1); lineage starts at an archive circuit (E polish 104/29 or hub 3f7a2fec7b7d) whose search path is not certified'
    (FOUND / (name + '.json')).write_text(json.dumps(side, indent=1) + '\n')
    print('SAVED', name)
    return 0


if __name__ == '__main__':
    sys.exit(main())
