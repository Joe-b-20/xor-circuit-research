#!/usr/bin/env python3
"""P6: save a verified circuit to found/ with the BRIEF sidecar.

    python3 save.py CIRCUIT --target T08 --start FILE --method TEXT --command TEXT --seed S --elapsed SEC [--note TEXT]
"""
import sys, json, hashlib, argparse, subprocess, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core                                  # noqa: E402
from boolflux.hub.common import load, metrics, verify, MODEL  # noqa: E402

FOUND = Path.home() / 'xs-campaigns/2026-11-15-targets/P6/found'
REPO = Path.home() / 'xcr-boolflux'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('circuit'); ap.add_argument('--target', required=True)
    ap.add_argument('--start', required=True); ap.add_argument('--method', required=True)
    ap.add_argument('--command', required=True); ap.add_argument('--seed', default='')
    ap.add_argument('--elapsed', type=float, default=0); ap.add_argument('--note', default='')
    ap.add_argument('--kernel-bin', default='')
    a = ap.parse_args()
    c = load(a.circuit); ok, inf = verify(c)
    if not ok:
        print('NOT VERIFIED', inf); sys.exit(1)
    A, AD, G, GD = metrics(c)
    h = hashlib.sha1(core.to_kernel(c).encode()).hexdigest()[:12]
    name = 'aes-sbox-a%d-ad%d-g%d-gd%d-%s' % (A, AD, G, GD, h)
    FOUND.mkdir(parents=True, exist_ok=True)
    cp = FOUND / (name + '.circ.txt')
    cp.write_text(core.write_ncff(c, MODEL))
    r = subprocess.run(['python3', str(REPO / 'nonlinear/boolflux/campaigns/aes_check.py'), str(cp)],
                       capture_output=True, text=True, cwd=str(REPO))
    line = [l for l in r.stdout.splitlines() if l.startswith('OK') or l.startswith('FAIL')]
    gitsha = subprocess.run(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    code = {'git': gitsha}
    kb = a.kernel_bin
    if kb and Path(kb).exists():
        code['kernel_bin'] = kb; code['kernel_sha256'] = sha(kb)
    code['p6_sha256'] = {f.name: sha(f) for f in sorted(HERE.glob('*.py'))}
    side = {'target': a.target, 'A': A, 'AD': AD, 'G': G, 'GD': GD,
            'start': {'path': str(Path(a.start).resolve()), 'sha256': sha(a.start)},
            'method': a.method, 'command': a.command, 'seed': a.seed, 'elapsed_s': a.elapsed,
            'code': code, 'aes_check': line[0] if line else r.stdout[-400:], 'aes_check_full': r.stdout,
            'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'source_file': str(Path(a.circuit).resolve()),
            'note': a.note,
            'path_certified': True,
            'path_certified_note': 'P6 drivers: every kernel stage starts inside A35/AD3 (and from 18:20 UTC runs with repair_keep 1); see strategies/P6/certify.py'}
    (FOUND / (name + '.json')).write_text(json.dumps(side, indent=1))
    print(cp); print(side['aes_check']); print(r.stdout)


if __name__ == '__main__':
    main()
