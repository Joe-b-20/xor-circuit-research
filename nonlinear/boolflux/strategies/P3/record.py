#!/usr/bin/env python3
"""Verify a circuit with aes_check.py and, if OK and inside the T04 hard limits (A<=32, AD<=4),
save it to ~/xs-campaigns/2026-11-15-targets/P3/found/<name>.circ.txt with the brief's sidecar.

  record.py --circ FILE --start FILE --method STR --command STR --seed N --elapsed S
            [--kernel PATH] [--tag TAG] [--min-keep-gd 99]
Prints the aes_check line and the saved path (or why not saved)."""
import argparse, datetime, hashlib, json, shutil, subprocess, sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[2]
REPO = PKG.parents[1]
FOUND = Path.home() / 'xs-campaigns/2026-11-15-targets/P3/found'
REF = (32, 4, 117, 19)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def classify(A, AD, G, GD):
    if A > 32 or AD > 4:
        return 'outside-hard-limits'
    if G <= 117 and GD <= 19 and (G < 117 or GD < 19):
        return 'strict'
    if 19 < GD <= 21 and G <= 117 - 3:
        return 'tradeoff:gates_for_depth'
    return 'other'


def main():
    ap = argparse.ArgumentParser()
    for k in ('circ', 'start', 'method', 'command'):
        ap.add_argument('--' + k, required=True)
    ap.add_argument('--seed', default=None); ap.add_argument('--elapsed', type=float, default=None)
    ap.add_argument('--kernel', default=None); ap.add_argument('--tag', default='p3')
    ap.add_argument('--keep-other', action='store_true')
    ap.add_argument('--path-certified', default='unknown')
    ap.add_argument('--reproduces', default=None)
    a = ap.parse_args()
    r = subprocess.run([sys.executable, str(PKG / 'campaigns/aes_check.py'), a.circ],
                       capture_output=True, text=True)
    line = (r.stdout.splitlines() or [''])[0]
    print(line)
    if not line.startswith('OK'):
        print('NOT SAVED: aes_check failed'); return 1
    A, AD, G, GD = map(int, line.split('= ')[1].split()[:4])
    cls = classify(A, AD, G, GD)
    if cls == 'outside-hard-limits':
        print('NOT SAVED: outside T04 hard limits'); return 2
    if cls == 'other' and not a.keep_other:
        print('NOT SAVED: class other (%d %d %d %d); circuit stays in its run dir' % (A, AD, G, GD)); return 0
    FOUND.mkdir(parents=True, exist_ok=True)
    def body(p):
        return '\n'.join(l for l in Path(p).read_text().splitlines() if not l.strip().startswith('%'))
    mine = body(a.circ)
    for q in FOUND.glob('*.circ.txt'):
        if body(q) == mine:
            print('ALREADY SAVED (same gates)', q); return 0
    h = sha(a.circ)
    name = 'p3-%s-a%d-ad%d-g%d-gd%d-%s' % (a.tag, A, AD, G, GD, h[:10])
    dst = FOUND / (name + '.circ.txt')
    if dst.exists():
        print('ALREADY SAVED', dst); return 0
    shutil.copyfile(a.circ, dst)
    git = subprocess.run(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    code = {'git': git, 'tree': 'xcr-boolflux + uncommitted strategies/P3 (and F/T2 as used)'}
    if a.kernel:
        code['kernel'] = a.kernel; code['kernel_sha256'] = sha(a.kernel)
    side = {'target': 'T04', 'A': A, 'AD': AD, 'G': G, 'GD': GD, 'class': cls,
            'reference': 'aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt',
            'start': {'path': str(Path(a.start).resolve()), 'sha256': sha(a.start)},
            'method': a.method, 'command': a.command,
            'seed': (int(a.seed) if a.seed not in (None, '') and str(a.seed).isdigit() else a.seed),
            'elapsed_s': a.elapsed, 'code': code, 'aes_check': line.strip(),
            'aes_check_full': r.stdout, 'circuit_sha256': h,
            'path_certified': {'true': True, 'false': False}.get(a.path_certified, 'unknown'),
            'reproduces': a.reproduces,
            'utc': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}
    (FOUND / (name + '.json')).write_text(json.dumps(side, indent=1) + '\n')
    print('SAVED', dst, cls)
    return 0


if __name__ == '__main__':
    sys.exit(main())
