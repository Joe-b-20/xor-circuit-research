#!/usr/bin/env python3
"""Rewrite / complete the JSON sidecars of Z1 found/ circuits to the targets-brief format
(target, A AD G GD, start + sha256, method, command, seed, elapsed_s, code, aes_check, utc),
keeping existing fields.  Re-runs aes_check.py on the circuit.  usage: sidecar.py CIRC.circ.txt..."""
import sys, os, json, hashlib, subprocess, re, time
HOME = os.path.expanduser('~')
CHK = HOME + '/xcr-boolflux/nonlinear/boolflux/campaigns/aes_check.py'
Z1 = HOME + '/xcr-boolflux/nonlinear/boolflux/strategies/Z1'
H2 = HOME + '/xcr-boolflux/nonlinear/boolflux/strategies/H2'
CASES = HOME + '/xs-campaigns/2026-11-15-targets/Z1/runs/g13/cases.log'


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def git_sha():
    r = subprocess.run(['git', '-C', HOME + '/xcr-boolflux', 'rev-parse', 'HEAD'], capture_output=True, text=True)
    return r.stdout.strip()


for f in sys.argv[1:]:
    jf = f + '.json'
    d = json.load(open(jf)) if os.path.exists(jf) else {}
    name = os.path.basename(f)
    m = re.match(r'z1g13-(.+)-[0-9a-f]{8}-s(\d+)-a(\d+)\.circ\.txt$', name)
    case = m.group(1) if m else None
    line = None
    if case:
        for ln in open(CASES):
            if (' %s early=' % case) in ln:
                line = ln
    r = subprocess.run(['python3', CHK, f], capture_output=True, text=True)
    ok = [l for l in (r.stdout + r.stderr).splitlines() if l.startswith('OK')]
    met = d.get('metrics') or {}
    early = d.get('early', '')
    start = early[5:] if early.startswith('file:') else early
    elapsed = None; cmd = None
    if line:
        em = re.search(r'\| (\d+)s\s*$', line.strip())
        elapsed = int(em.group(1)) if em else None
        g = re.search(r' (\S+) early=(\S+) gamma=(\S+) K=(\d+) gen=(\S) extra=(.*?) rc=', line)
        if g:
            cmd = 'bash %s/g13case.sh %s %s %s %s %s %s' % (Z1, g.group(1), g.group(2), g.group(3), g.group(4), g.group(5), g.group(6).strip())
    d.update({
        'target': 'Z',
        'A': met.get('A'), 'AD': met.get('AD'), 'G': met.get('G'), 'GD': met.get('GD'),
        'start': {'path': start, 'sha256': sha(start) if start and os.path.exists(start) else None,
                  'note': 'stage-1 span (and middle if midfile) taken from this file; positive-control rebuild'},
        'method': {'engine': 'H2 gen13 exact dense-subspace search (real model) via Z1 g13case.sh',
                   'mode': 'rprep -> gen13 -> fastrank -> rvd_z1 (minimise, build_circuit, aes_check)',
                   'case': case, 'cases_log_line': line.strip() if line else None},
        'command': cmd,
        'seed': 'none (deterministic exhaustive search)',
        'elapsed_s': elapsed,
        'code': {'git': git_sha(), 'gen13_sha256': sha(H2 + '/gen13'), 'rvd_z1_sha256': sha(Z1 + '/rvd_z1.py')},
        'aes_check': ok[0] if ok else (r.stdout + r.stderr).strip()[:300],
        'aes_check_ok': r.returncode == 0,
        'utc': d.get('time') or time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'path_certified': True,
        'path_note': 'no kernel / no search states: exact gen13 enumeration + direct build (build_circuit) of the covering layer; nothing retained above the stated A',
        'role': 'Z result' if (met.get('A') or 99) <= 27 else 'positive control of the exact pipeline (A = 28 > 27, not a Z result)',
        'sidecar_rewritten_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    })
    json.dump(d, open(jf, 'w'), indent=1)
    print(name, d['A'], d['AD'], d['G'], d['GD'], 'aes_check_ok', d['aes_check_ok'], 'cmd', bool(cmd), 'elapsed', elapsed)
