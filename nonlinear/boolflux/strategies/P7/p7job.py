#!/usr/bin/env python3
"""P7 job: one fdrive polish under hard caps, then verification and recording.

    p7job.py --target T09 --start FILE --cap-gd 12 --cap-a 45 --mode gate --seed 1 --seconds 3600 --tag NAME
             [--cap-ad 4] [--lex a,cost,gd] [-- extra fdrive args]

Runs strategies/P7/fdrive_p7.py (kernel bfx-94a75e2c18) into P7/runs/<tag>/, then aes_check on the best
circuit, re-checks the hard caps (A, AD) and the GD cap, and if the circuit differs in (G, GD) from the
start, copies it into P7/found/ with a full sidecar (BRIEF.md "What to save").
"""
import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path

HOME = Path.home()
BF = HOME / 'xcr-boolflux/nonlinear/boolflux'
P7 = HOME / 'xs-campaigns/2026-11-15-targets/P7'
BFX = HOME / "xs-campaigns/2026-11-15-targets/P7/bin/bfx-94a75e2c18"
sys.path.insert(0, str(BF.parent))
from boolflux import core  # noqa: E402
MODEL = core.Model.load(str(core.MODELS / 'nist.json'))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def metr(p):
    m = core.read_ncff(str(p)).metrics(MODEL)
    return m['A'], m['AD'], m['G'], m['GD']


def record(target, circ, start, method, command, seed, elapsed, name, extra=None, caps=None):
    """aes_check + cap check + copy into found/ with a sidecar. Returns (ok, metrics, line)."""
    r = subprocess.run(['python3', str(BF / 'campaigns/aes_check.py'), str(circ)],
                       capture_output=True, text=True, cwd=str(BF))
    line = (r.stdout.splitlines() or [''])[0]
    if not line.startswith('OK'):
        return False, None, line + r.stderr[-300:]
    A, AD, G, GD = metr(circ)
    if caps:
        ca, cad, cgd = caps
        if A > ca or AD > cad or (cgd is not None and GD > cgd):
            return False, (A, AD, G, GD), 'CAPS NOT MET ' + line
    fname = 'p7-%s-a%d-ad%d-g%d-gd%d-%s' % (target.lower(), A, AD, G, GD, name)
    dst = P7 / 'found' / (fname + '.circ.txt')
    dst.write_text(Path(circ).read_text())
    git = subprocess.run(['git', '-C', str(HOME / 'xcr-boolflux'), 'rev-parse', 'HEAD'],
                         capture_output=True, text=True).stdout.strip()
    side = {'target': target, 'A': A, 'AD': AD, 'G': G, 'GD': GD,
            'file': str(dst),
            'start': {'path': str(start), 'sha256': sha(start)},
            'method': method, 'command': command, 'seed': seed, 'elapsed_s': round(elapsed, 1),
            'code': {'xcr-boolflux': git + ' + uncommitted strategies/P7, strategies/F',
                     'kernel': str(BFX), 'kernel_sha256': sha(BFX),
                     'p7_sha256': {f.name: sha(f) for f in sorted((BF / 'strategies/P7').glob('*.py'))}},
            'aes_check': line.strip(), 'sha256': sha(dst),
            'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    if extra: side.update(extra)
    (P7 / 'found' / (fname + '.json')).write_text(json.dumps(side, indent=1) + '\n')
    # COMPLIANCE-1820: path_certified / donor fields for every sidecar (idempotent passes over found/)
    for tool in ('certify.py', 'donor.py'):
        subprocess.run(['python3', str(BF / 'strategies/P7' / tool)], capture_output=True, text=True)
    return True, (A, AD, G, GD), line


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--target', required=True); ap.add_argument('--start', required=True)
    ap.add_argument('--cap-gd', type=int, required=True); ap.add_argument('--cap-a', type=int, required=True)
    ap.add_argument('--cap-ad', type=int, default=4); ap.add_argument('--mode', default='gate')
    ap.add_argument('--seed', type=int, default=1); ap.add_argument('--seconds', type=float, default=3600)
    ap.add_argument('--tag', required=True); ap.add_argument('--lex', default='')
    ap.add_argument('rest', nargs='*')
    a = ap.parse_args()
    out = P7 / 'runs' / a.tag; out.mkdir(parents=True, exist_ok=True)
    cmd = ['python3', str(BF / 'strategies/P7/fdrive_p7.py'), '--start', str(Path(a.start).resolve()),
           '--cap', str(a.cap_gd), '--cap-ad', str(a.cap_ad), '--cap-a', str(a.cap_a), '--mode', a.mode,
           '--seconds', str(a.seconds), '--seed', str(a.seed), '--out', str(out)] + a.rest
    env = dict(os.environ, F_BFX=str(BFX))
    if a.lex: env['F_LEX'] = a.lex
    full = ' '.join(['F_BFX=' + str(BFX)] + (['F_LEX=' + a.lex] if a.lex else []) + cmd)
    (out / 'command.txt').write_text(full + '\n')
    t0 = time.time()
    with open(out / 'fdrive.out', 'w') as fo:
        subprocess.run(cmd, env=env, stdout=fo, stderr=subprocess.STDOUT, cwd=str(BF))
    el = time.time() - t0
    best = out / 'best.circ.txt'
    res = {'tag': a.tag, 'elapsed_s': round(el, 1)}
    if best.exists():
        s = metr(a.start); b = metr(best)
        res.update({'start': s, 'best': b})
        if (b[2], b[3]) != (s[2], s[3]):
            ok, m, line = record(a.target, best, Path(a.start).resolve(),
                                 {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': a.mode,
                                  'caps': {'GD': a.cap_gd, 'AD': a.cap_ad, 'A': a.cap_a}, 'lex': a.lex or 'default (cost, gd)',
                                  'run_dir': str(out)},
                                 full, a.seed, el, a.tag, caps=(a.cap_a, a.cap_ad, a.cap_gd))
            res.update({'recorded': ok, 'check': line})
    (out / 'result.json').write_text(json.dumps(res) + '\n')
    print(json.dumps(res))


if __name__ == '__main__':
    main()
