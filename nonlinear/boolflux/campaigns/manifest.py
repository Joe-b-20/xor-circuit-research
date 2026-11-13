"""Write results/MANIFEST.json and results/nist-format/: provenance and three-way verification.

    python3 nonlinear/boolflux/campaigns/manifest.py

For every results/<target>/*.circ.txt:
  - sha256 of the file; target and how it is defined; model, its permitted gates and costs;
    objective and caps; the starting circuit (path, sha256, and for NIST starts the NIST commit
    it was taken from and whether the file is byte-identical at the pinned commit e6ac0d0);
    command, seeds, iterations, rounds, code hash, wall/CPU time (from summary.json);
  - verification: core (bitsliced) and independent/verify.py (exhaustive, with the model's
    gate list and the caps) must both accept it; their metrics must agree.
For AES results it also writes a NIST-format copy to results/nist-format/ (NOT written as an
explicit NOT gate, named aes-sbox-aA-adAD-gG-gdGD-xxnX-Y-Z as NIST does from e6ac0d0 on, or
-xxX-Y when there is no NOT) and checks it with nonlinear/check.py's boolcirc counter (a third
implementation), which also checks the name against the recount.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
REPO = PKG.parents[1]
sys.path.insert(0, str(PKG.parent)); sys.path.insert(0, str(PKG))
import cli                                  # noqa: E402
from boolflux import core, targets          # noqa: E402

NEW_PIN = 'e6ac0d03f4816927f1b0e676996e4d075ab8d1c0'
OLD_PIN = '0876577bc2c9ce214a4c7f84b7f9b9eb02e5092f'
OLD_PIN_REPO_COMMIT = '920fc4a'             # this branch's commit that still held the old import


def sha(b):
    return hashlib.sha256(b).hexdigest()


def git_show(rev, path):
    r = subprocess.run(['git', 'show', '%s:%s' % (rev, path)], cwd=REPO, capture_output=True)
    return r.stdout if r.returncode == 0 else None


def start_info(start):
    if start == 'anf':
        return {'kind': 'naive ANF circuit built by starts.anf from the target table'}
    p = Path(start)
    rel = str(p) if not p.is_absolute() else str(p.relative_to(REPO)) if str(p).startswith(str(REPO)) else str(p)
    info = {'path': rel}
    if rel.startswith('nonlinear/nist/'):
        old = git_show(OLD_PIN_REPO_COMMIT, rel)
        new = (REPO / rel).read_bytes() if (REPO / rel).exists() else None
        info.update({'kind': 'NIST circuit', 'taken_from_nist_commit': OLD_PIN,
                     'sha256': sha(old) if old else None,
                     'identical_at_' + NEW_PIN[:7]: (old == new) if old and new else False})
    elif (REPO / rel).exists():
        info.update({'kind': 'BoolFlux result', 'sha256': sha((REPO / rel).read_bytes())})
    return info


def nist_export(c, model_metrics):
    m = model_metrics; cnt = m['counts']
    nots = cnt.get('NOT', 0); xx = cnt.get('XOR', 0) + cnt.get('XNOR', 0)
    tail = ('xxn%d-%d-%d' % (xx + nots, cnt.get('XNOR', 0), nots)) if nots else ('xx%d-%d' % (xx, cnt.get('XNOR', 0)))
    name = 'aes-sbox-a%d-ad%d-g%d-gd%d-%s' % (m['A'], m['AD'], m['G'], m['GD'], tail)
    c.name = name
    return name, core.write_ncff(c, None, comments=['BoolFlux result, NIST accounting (NOT counted as a gate)'])


def main():
    out = {'nist_baseline_commit': NEW_PIN, 'entries': []}
    nf = PKG / 'results' / 'nist-format'
    if nf.exists():
        for f in nf.iterdir(): f.unlink()
    nf.mkdir(parents=True, exist_ok=True)
    bad = 0
    for f in sorted((PKG / 'results').glob('*/*.circ.txt')):
        if f.parent.name in ("nist-format",) or f.parent.name.startswith("_"): continue
        s = json.loads(f.with_suffix('').with_suffix('.summary.json').read_text())
        model = core.Model.load(s['model'])
        caps = s['caps']
        v = cli.verify_file(f, s['target'], s['model'], caps)
        ok = v['core_ok'] and v['independent_ok'] and v['library_ok'] and v['metrics_agree']
        bad += not ok
        n, m, table, desc = targets.load(s['target'])
        e = {'file': str(f.relative_to(REPO)), 'sha256': sha(f.read_bytes()), 'target': s['target'],
             'target_definition': desc, 'model': model.name, 'permitted_gates_and_costs': model.gates,
             'objective': s['objective'], 'caps': caps, 'start': start_info(s['start']),
             'command': s['command'], 'seeds': s['seeds'], 'iters': s['iters'], 'rounds': s.get('rounds', 1),
             'code_sha256_12': s.get('code_sha256_12') or s.get('kernel_sha256_12'),
             'job': s['best'].get('job') or 'seed %s round %s' % (s['best'].get('seed'), s['best'].get('round')),
             'wall_s': s.get('wall_s'), 'metrics': v['metrics'],
             'counts_as_written': (v['independent'].get('metrics') or {}).get('counts'),
             'verified': {'core': v['core_ok'], 'independent': v['independent_ok'], 'library': v['library_ok'],
                          'metrics_agree': v['metrics_agree']}}
        if s['target'] == 'aes':
            c = core.read_ncff(str(f))
            name, text = nist_export(c, c.metrics())
            (nf / (name + '.circ.txt')).write_text(text, encoding='utf-8')
            e['nist_format_file'] = 'nonlinear/boolflux/results/nist-format/%s.circ.txt' % name
        out['entries'].append(e)
    # third counter: boolcirc via nonlinear/check.py (function + metrics vs name)
    r = subprocess.run([sys.executable, str(REPO / 'nonlinear' / 'check.py'), str(nf)], capture_output=True, text=True)
    out['nist_format_check'] = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-500:]
    (PKG / 'results' / 'MANIFEST.json').write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
    print('%d entries, %d failing verification; nist-format check: %s' % (len(out['entries']), bad, out['nist_format_check']))
    if r.returncode != 0 or bad:
        print(r.stdout[-3000:]); sys.exit(1)


if __name__ == '__main__':
    main()
