#!/usr/bin/env python3
"""Record one circuit of a P1 run: verify (hub verify + 256 inputs), enforce the target's hard limits, copy
into DATA/shared (start pool for LNS / workers), and if no reference tuple dominates or equals it, save it
to DATA/found/ with the BRIEF sidecar and an aes_check run.

    p1rec.py --circ F --target T03 --start S --method M --command C --seed K --elapsed E [--kernel BIN]
"""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

PKG = Path('/home/joebachir20/xcr-boolflux/nonlinear/boolflux')
sys.path.insert(0, str(PKG.parent))
from boolflux import core, targets   # noqa: E402
from boolflux.hub.common import verify  # noqa: E402
DATA = Path('/home/joebachir20/xs-campaigns/2026-11-15-targets/P1')
LIM = {'T01': (28, 4, 132, 22), 'T03': (28, 5, 128, 20)}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    for k in ('--circ', '--target', '--start', '--method', '--command', '--seed', '--elapsed', '--kernel'):
        ap.add_argument(k)
    a = ap.parse_args()
    M = core.Model.load('nist')
    t = Path(a.circ).read_text()
    c = core.from_kernel(t) if a.circ.endswith('.bfx') else core.read_ncff(t)
    m = c.metrics(M); tup = (m['A'], m['AD'], m['G'], m['GD'])
    ok, _ = verify(c)
    if not ok or tuple(c.value_table()) != tuple(targets.aes_sbox()):
        print('VERIFY FAIL', a.circ, tup); sys.exit(1)
    A, AD, G, GD = LIM[a.target]
    if tup[0] > A or tup[1] > AD:
        print('OUTSIDE HARD LIMITS', tup); sys.exit(0)
    cid = hashlib.sha1(core.to_kernel(c).encode()).hexdigest()[:12]
    sh = DATA / 'shared'
    if not (sh / (cid + '.bfx')).exists():
        (sh / (cid + '.bfx')).write_text(core.to_kernel(c))
        (sh / (cid + '.json')).write_text(json.dumps({'id': cid, 'm': tup, 'origin': 'p1rec', 't': time.time(),
                                                       'lineage': {'root': a.start, 'root_sha256': sha(a.start) if a.start else None,
                                                                   'chain': [{'op': a.method, 'command': a.command}]}}))
    ref = set(tuple(x) for x in json.loads((DATA / 'reftuples.json').read_text()))
    if any(all(x <= y for x, y in zip(q, tup)) for q in ref):
        print('known/dominated', tup); return
    fd = DATA / 'found'
    if len(list(fd.glob('P1-%s-a%d-ad%d-g%d-gd%d-*.circ.txt' % ((a.target,) + tup)))) >= 3:
        print('tuple already saved 3x', tup); return
    nm = 'P1-%s-a%d-ad%d-g%d-gd%d-%s' % ((a.target,) + tup + (cid,))
    p = fd / (nm + '.circ.txt')
    if p.exists(): print('exists', p); return
    p.write_text(core.write_ncff(c, M, comments=['P1 %s' % a.method]))
    r = subprocess.run([sys.executable, str(PKG / 'campaigns' / 'aes_check.py'), str(p), '--json', str(fd / (nm + '.check.json'))],
                       capture_output=True, text=True)
    okl = [x for x in r.stdout.splitlines() if 'OK' in x][:1]
    cls = 'strict' if (tup[2] <= G and tup[3] <= GD and (tup[2] < G or tup[3] < GD)) else (
        'tradeoff' if a.target == 'T01' and GD < tup[3] <= 24 and tup[2] <= G - 3 else 'other')
    git = subprocess.run(['git', '-C', str(PKG.parents[1]), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    side = {'target': a.target, 'class_vs_ref': cls, 'A': tup[0], 'AD': tup[1], 'G': tup[2], 'GD': tup[3],
            'start': {'path': a.start, 'sha256': sha(a.start) if a.start else None},
            'method': a.method, 'command': a.command, 'seed': a.seed, 'elapsed_s': a.elapsed,
            'code': {'git': git, 'kernel_bin': a.kernel, 'kernel_sha256': sha(a.kernel) if a.kernel else None},
            'aes_check': okl[0] if okl else None, 'aes_check_rc': r.returncode,
            'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    (fd / (nm + '.json')).write_text(json.dumps(side, indent=1))
    print('FOUND', cls, p, okl)


if __name__ == '__main__':
    main()
