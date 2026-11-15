#!/usr/bin/env python3
"""Re-verify every BoolFlux circuit we report or keep, and print one summary.

    taskset -c 0 python3 nonlinear/boolflux/campaigns/verify_all.py [--json OUT.json]
        [--campaigns DIR ...] [--no-campaigns] [--no-nist] [--quiet]

Sections (each circuit is checked independently; nothing is trusted from file names or sidecars):

  results      every results/<target>/*.circ.txt (not nist-format/, not _superseded/): target, model
               and caps from its .summary.json; cli.verify_file = core (bitsliced, targets.py) and
               independent/verify.py (exhaustive per-input evaluation, own AES/table code, library
               and cap check), whose G, A, GD, AD, cost and counts must agree; plus the file's
               sha256 against results/MANIFEST.json.
  nist-format  results/nist-format/*.circ.txt (explicit NOT gates): aes_check.check (both verifiers,
               NIST library {AND, XOR, XNOR, NOT}) and nonlinear/check.py (boolcirc, a third
               implementation, which also recomputes the metrics in the file name).
  campaigns    every circuit under DIR/*/found/ (recursively) and DIR/best/ for each campaign DIR
               (default ~/xs-campaigns/2026-11-13-aes), plus the other candidate sources of
               best_table.py (main/**/best.circ.txt, track E's admitted/ pools): *.circ.txt (except
               *.check.*) and kernel .bfx files (converted to NCFF in a temporary directory, never
               written next to the source); aes_check.check on each.  Campaign folders are only read.
  nist         the pinned reference nonlinear/nist/: sha256 of every file against
               nonlinear/nist/MANIFEST.json, and nonlinear/check.py over the folder (function under
               the folder's target, metrics against the NIST file names).

The summary also gives the AES (A, AD, G, GD) tuples that no pinned NIST forward circuit
dominates (all four <=, equality counts as dominated) and, among those, the ones no other circuit
of ours strictly dominates (the same rule as best_table.py).  Exit status 1 if anything fails.
Read-only except for the temporary directory and the optional --json file.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

os.environ['BOOLFLUX_NO_CACHE'] = '1'      # this tool re-verifies the pinned set itself (aes_check cache off)

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
REPO = PKG.parents[1]
sys.path.insert(0, str(PKG.parent)); sys.path.insert(0, str(PKG)); sys.path.insert(0, str(HERE))
import cli                                   # noqa: E402
import aes_check as AC                       # noqa: E402
from boolflux import core                    # noqa: E402

DEFAULT_CAMPAIGNS = [Path.home() / 'xs-campaigns' / '2026-11-13-aes']
# found/ and best/ of every track, plus the other places best_table.py collects candidates from
CAMPAIGN_GLOBS = ['*/found/**/*', 'best/*.circ.txt', 'main/**/best.circ.txt',
                  'E/long1/*/admitted/*.bfx', 'E/low1/**/admitted/*.bfx']


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def le(p, q):
    return all(a <= b for a, b in zip(p, q))


def short(p):
    s = str(p)
    for root, name in ((str(REPO) + '/', ''), (str(Path.home()), '~')):
        if s.startswith(root):
            return name + s[len(root):]
    return s


def check_results(rows, aes_tuples):
    man = {}
    mp = PKG / 'results' / 'MANIFEST.json'
    if mp.exists():
        man = {e['file']: e for e in json.loads(mp.read_text()).get('entries', [])}
    for f in sorted((PKG / 'results').glob('*/*.circ.txt')):
        if f.parent.name == 'nist-format' or f.parent.name.startswith('_'):
            continue
        r = {'section': 'results', 'file': short(f)}
        try:
            s = json.loads(f.with_suffix('').with_suffix('.summary.json').read_text())
            v = cli.verify_file(f, s['target'], s['model'], s['caps'])
            m = v['metrics']
            r.update(target=s['target'], model=s['model'],
                     tuple=[m['A'], m['AD'], m['G'], m['GD']], core_ok=v['core_ok'],
                     independent_ok=v['independent_ok'], library_ok=v['library_ok'],
                     metrics_agree=v['metrics_agree'])
            e = man.get(str(f.relative_to(REPO)))
            r['manifest'] = 'absent' if e is None else ('sha256 ok' if e['sha256'] == sha(f) else 'SHA256 MISMATCH')
            r['ok'] = v['core_ok'] and v['independent_ok'] and v['library_ok'] and v['metrics_agree'] \
                and r['manifest'] != 'SHA256 MISMATCH'
            if s['target'] == 'aes' and s['model'] == 'nist' and r['ok']:
                aes_tuples.append((tuple(r['tuple']), short(f)))
        except Exception as ex:                      # a missing sidecar is a failure too
            r.update(ok=False, error=repr(ex))
        rows.append(r)


def check_aes_file(path, label, section, rows, aes_tuples, tmp):
    r = {'section': section, 'file': label}
    try:
        p = Path(path)
        if p.suffix == '.bfx':
            c = core.from_kernel(p.read_text(), name=p.stem)
            q = Path(tmp) / ('%s-%s.circ.txt' % (p.parent.name, p.stem))
            q.write_text(core.write_ncff(c, core.Model.load('nist')))
            p = q
        res = AC.check(p)
        r.update(ok=res['ok'], tuple=list(res['tuple']), core_ok=res['core_ok'],
                 independent_ok=res['independent_ok'], library_ok=res['library_ok'],
                 metrics_agree=res['metrics_agree'])
        if res['ok']:
            r['new_on_pinned_set'] = res['new_point']
            aes_tuples.append((tuple(res['tuple']), label))
        else:
            r['error'] = str(res.get('errors'))[:300]
    except Exception as ex:
        r.update(ok=False, error=repr(ex))
    rows.append(r)


def run_boolcirc(path):
    pr = subprocess.run([sys.executable, str(REPO / 'nonlinear' / 'check.py'), str(path)],
                        capture_output=True, text=True)
    last = pr.stdout.strip().splitlines()[-1] if pr.stdout.strip() else pr.stderr[-300:]
    return pr.returncode == 0, last


def main():
    args = sys.argv[1:]
    known = {'--json', '--campaigns', '--no-campaigns', '--no-nist', '--quiet'}
    if any(a.startswith('-') and a not in known for a in args):       # review5 P16: -h used to start the full run
        print(__doc__.strip())
        return 0 if all(a in ('-h', '--help') or a in known or not a.startswith('-') for a in args) else 2
    out_json = None
    if '--json' in args:
        i = args.index('--json'); out_json = args[i + 1]; del args[i:i + 2]
    camps = []
    if '--campaigns' in args:
        i = args.index('--campaigns'); j = i + 1
        while j < len(args) and not args[j].startswith('--'):
            camps.append(Path(args[j]).expanduser()); j += 1
        del args[i:j]
    if not camps:
        camps = DEFAULT_CAMPAIGNS
    if '--no-campaigns' in args:
        camps = []
    quiet = '--quiet' in args
    t0 = time.time()
    rows, aes_tuples, extra = [], [], {}

    check_results(rows, aes_tuples)

    nf = PKG / 'results' / 'nist-format'
    with tempfile.TemporaryDirectory() as tmp:
        for f in sorted(nf.glob('*.circ.txt')):
            check_aes_file(f, short(f), 'nist-format', rows, [], tmp)
        if nf.exists():
            ok, last = run_boolcirc(nf)
            extra['nist-format boolcirc'] = {'ok': ok, 'result': last}
        for d in camps:
            if not d.exists():
                extra['campaign %s' % short(d)] = {'ok': False, 'result': 'folder missing'}
                continue
            files = sorted({f for g in CAMPAIGN_GLOBS for f in d.glob(g)
                            if f.is_file() and '.check.' not in f.name
                            and (f.name.endswith('.circ.txt') or f.suffix == '.bfx')})
            for f in files:
                check_aes_file(f, short(f), 'campaigns', rows, aes_tuples, tmp)

    if '--no-nist' not in args:
        nist = REPO / 'nonlinear' / 'nist'
        man = json.loads((nist / 'MANIFEST.json').read_text())
        bad = [e['folder'] + '/' + e['file'] for e in man['files']
               if not (nist / e['folder'] / e['file']).exists() or sha(nist / e['folder'] / e['file']) != e['sha256']]
        extra['nist pin %s: sha256 of %d files' % (man['commit'][:7], len(man['files']))] = {
            'ok': not bad, 'result': 'all match' if not bad else 'MISMATCH: %s' % ', '.join(bad[:10])}
        ok, last = run_boolcirc(nist)
        extra['nist pin boolcirc (nonlinear/check.py)'] = {'ok': ok, 'result': last}
        pub = AC.published()
        extra['nist pin forward AES set used for dominance'] = {
            'ok': True, 'result': '%d circuits, %d distinct (A, AD, G, GD) tuples (independent verifier)'
            % (len(pub), len({u for u, _ in pub}))}

    # Pareto status of every verified AES circuit of ours (results/aes + campaigns)
    pub = [u for u, _ in AC.published()]
    tuples = {}
    for t, lab in aes_tuples:
        tuples.setdefault(t, []).append(lab)
    new = {t for t in tuples if not any(le(u, t) for u in pub)}
    pareto = sorted((t for t in new if not any(u != t and le(u, t) for u in new)), key=lambda t: (t[3], t[2], t))

    # report
    secs = ['results', 'nist-format', 'campaigns']
    fails = [r for r in rows if not r['ok']]
    print('BoolFlux verify_all  (%s, %.0f s)' % (time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime()), time.time() - t0))
    print('%-12s %8s %8s %8s %s' % ('section', 'checked', 'passed', 'failed', 'notes'))
    for s in secs:
        sr = [r for r in rows if r['section'] == s]
        note = ''
        if s == 'results':
            note = 'manifest sha256: %d ok, %d absent' % (sum(r.get('manifest') == 'sha256 ok' for r in sr),
                                                          sum(r.get('manifest') == 'absent' for r in sr))
        if s == 'campaigns':
            note = '%d new on the pinned set (per file); roots: %s' % (
                sum(bool(r.get('new_on_pinned_set')) for r in sr), ', '.join(short(d) for d in camps) or 'none')
        print('%-12s %8d %8d %8d %s' % (s, len(sr), sum(r['ok'] for r in sr), sum(not r['ok'] for r in sr), note))
    for k, v in extra.items():
        print('%-4s %s: %s' % ('ok' if v['ok'] else 'FAIL', k, v['result']))
    print('AES tuples of ours (verified): %d distinct; %d not dominated by the pinned set; %d of those Pareto among ours'
          % (len(tuples), len(new), len(pareto)))
    if not quiet:
        print('Pareto tuples (A AD G GD), by gate depth: ' + ', '.join('%d/%d/%d/%d' % t for t in pareto))
    for r in fails:
        print('FAIL [%s] %s: %s' % (r['section'], r['file'], r.get('error') or
              {k: r.get(k) for k in ('core_ok', 'independent_ok', 'library_ok', 'metrics_agree', 'manifest')}))
    all_ok = not fails and all(v['ok'] for v in extra.values())
    print('RESULT: %s' % ('ALL OK' if all_ok else 'FAILURES: %d circuit(s), %d other check(s)'
                          % (len(fails), sum(not v['ok'] for v in extra.values()))))
    if out_json:
        Path(out_json).write_text(json.dumps({'rows': rows, 'checks': extra, 'pareto': pareto,
                                              'new_on_pinned_set': sorted(new),
                                              'tuples': {'%d/%d/%d/%d' % t: v for t, v in sorted(tuples.items())}},
                                             indent=1) + '\n', encoding='utf-8')
    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
