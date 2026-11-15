"""P4: verify a circuit with aes_check and save it to found/ with the BRIEF sidecar.

    python3 save_found.py FILE NAME --start START --method M --command CMD --seed S --elapsed T
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

REPO = Path.home() / 'xcr-boolflux'
FOUND = Path.home() / 'xs-campaigns/2026-11-15-targets/P4/found'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file')
    ap.add_argument('name')
    ap.add_argument('--start', required=True)
    ap.add_argument('--method', required=True)
    ap.add_argument('--command', required=True)
    ap.add_argument('--seed', default='none (deterministic)')
    ap.add_argument('--elapsed', type=float, default=0.0)
    ap.add_argument('--target', default='T05')
    ap.add_argument("--path-certified", default="true", help="true: every kernel stage ran with repair_keep 1 or started inside all caps")
    ap.add_argument("--kernel", default=None)
    a = ap.parse_args()
    r = subprocess.run(['python3', str(REPO / 'nonlinear/boolflux/campaigns/aes_check.py'), a.file],
                       capture_output=True, text=True, cwd=str(REPO))
    line = r.stdout.splitlines()[0] if r.stdout else r.stderr
    if r.returncode != 0 or not line.startswith('OK'):
        print('NOT SAVED:', line)
        return 1
    FOUND.mkdir(parents=True, exist_ok=True)
    dst = FOUND / f'{a.name}.circ.txt'
    shutil.copy(a.file, dst)
    import re
    m = re.search(r'A AD G GD = (\d+) (\d+) (\d+) (\d+)', line)
    git = subprocess.run(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    side = dict(target=a.target, file=dst.name, aes_check=line, start=dict(path=a.start, sha256=sha(a.start)),
                method=a.method, command=a.command, seed=a.seed, elapsed_s=a.elapsed,
                code=dict(xcr_boolflux_git=git + ' + uncommitted strategies/P4',
                          p4_files={p.name: sha(p) for p in sorted((REPO / "nonlinear/boolflux/strategies/P4").glob("*.py"))},
                          kernel=dict(path=a.kernel, sha256=sha(a.kernel)) if a.kernel else None),
                path_certified=(a.path_certified == "true") if a.path_certified in ("true", "false") else a.path_certified,
                utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    if m:
        side.update(A=int(m.group(1)), AD=int(m.group(2)), G=int(m.group(3)), GD=int(m.group(4)))
    (FOUND / f'{a.name}.json').write_text(json.dumps(side, indent=1))
    print('SAVED', dst, line)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
