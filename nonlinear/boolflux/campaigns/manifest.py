"""Write results/MANIFEST.json and results/nist-format/: provenance and three-way verification.

    python3 nonlinear/boolflux/campaigns/manifest.py

For every results/<target>/*.circ.txt:
  - sha256 of the file; target and how it is defined; model, its permitted gates and costs;
    objective and caps; the starting circuit (path, sha256, and for NIST starts the earliest
    NIST pin it was taken from and whether the file is byte-identical at the current pin);
    command, seeds, iterations, rounds, code hash, wall/CPU time (from summary.json);
  - provenance (added 2026-11-14): mechanism, parents, time to result, reproduction status
    (deterministic command / re-run with identical gate list / one-off), run record, code
    version.  Curated campaign results (campaigns/curate_aes.py) carry these in their
    summary.json; for the older cli.py results they are derived from the command and, when the
    run folder still exists, from the run's own summary.json (else kept from the previous
    MANIFEST.json entry with the same sha256);
  - verification: core (bitsliced) and independent/verify.py (exhaustive, with the model's
    gate list and the caps) must both accept it; their metrics must agree.
For AES results it also writes a NIST-format copy to results/nist-format/ (NOT written as an
explicit NOT gate, named aes-sbox-aA-adAD-gG-gdGD-xxnX-Y-Z as NIST does from e6ac0d0 on, or
-xxX-Y when there is no NOT) and checks it with nonlinear/check.py's boolcirc counter (a third
implementation), which also checks the name against the recount.  Each AES entry also gets its
status on the pinned NIST set (aes_check.check: dominated_by, new_point) and the results of ours
that strictly dominate it (superseded_by_ours); the top-level `aes_pareto` lists the tuples that
are new on the pinned set and not strictly dominated by another result.
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

NEW_PIN = '3d807741f937d29d3bef4f32f142ccda0cda9070'
OLD_PIN = '0876577bc2c9ce214a4c7f84b7f9b9eb02e5092f'
OLD_PIN_REPO_COMMIT = '920fc4a'             # this branch's commit that still held the old import
# every NIST pin of this branch and the branch commit that imported it, oldest first
PINS = [(OLD_PIN, OLD_PIN_REPO_COMMIT), ('e6ac0d03f4816927f1b0e676996e4d075ab8d1c0', 'caa29af'),
        (NEW_PIN, '417e449')]
HOME = str(Path.home())
# runs re-done from scratch to check determinism (LEDGER.md: identical gate lists)
REPRO_RUNS = [Path.home() / 'xs-campaigns' / '2026-11-13-boolflux' / 'repro' / d for d in ('g109', 'gd14')]
EXTRA = ('track', 'mechanism', 'parents', 'time_to_result_s', 'reproduction', 'run_record',
         'campaign_source', 'campaign_sidecar', 'code_version', 'curated_utc', 'job_caps', 'note',
         'kernel_seed', 'recorded_utc')


def sha(b):
    return hashlib.sha256(b).hexdigest()


def git_show(rev, path):
    r = subprocess.run(['git', 'show', '%s:%s' % (rev, path)], cwd=REPO, capture_output=True)
    return r.stdout if r.returncode == 0 else None


def start_info(start):
    if start == 'anf':
        return {'kind': 'naive ANF circuit built by starts.anf from the target table'}
    p = Path(str(start).replace('~', HOME, 1) if str(start).startswith('~') else start)
    rel = str(p) if not p.is_absolute() else str(p.relative_to(REPO)) if str(p).startswith(str(REPO)) else str(p)
    info = {'path': rel.replace(HOME, '~')}
    if rel.startswith('nonlinear/nist/'):
        new = (REPO / rel).read_bytes() if (REPO / rel).exists() else None
        first = next(((pin, b) for pin, b in ((pin, git_show(rc, rel)) for pin, rc in PINS) if b), (None, None))
        info.update({'kind': 'NIST circuit', 'taken_from_nist_commit': first[0],
                     'sha256': sha(first[1]) if first[1] else None,
                     'identical_at_' + NEW_PIN[:7]: (first[1] == new) if first[1] and new else False})
    elif (REPO / rel).exists():
        info.update({'kind': 'BoolFlux result', 'sha256': sha((REPO / rel).read_bytes())})
    elif p.exists():
        info.update({'kind': 'campaign circuit (outside the repository)', 'sha256': sha(p.read_bytes())})
    return info


def derived_provenance(s, f, prev):
    """mechanism / time to result / reproduction for results written by cli.py run/pipe or bench."""
    cmd = s['command']
    if 'bench.py' in cmd:
        mech = 'flow full configuration (bench v3): rebuild-only skeleton stage + gate kernel, adaptive share'
    elif 'cli.py pipe' in cmd:
        mech = 'pipe: AND-skeleton search + synthesis + gate kernel, in rounds over a pool'
    else:
        mech = 'gate kernel (cli.py run: care-set resubstitution moves, annealing, restarts from the best)'
    out = {'mechanism': mech, 'parents': [start_info(s['start'])]}
    run_dir = Path(s['best']['file']).parent if s.get('best', {}).get('file') else None
    rs = None
    if run_dir and (run_dir / 'summary.json').exists():
        rs = json.loads((run_dir / 'summary.json').read_text())
    bench = sorted((Path.home() / 'xs-campaigns' / '2026-11-13-boolflux' / 'bench').glob(
        'v*/%s.json' % s['best'].get('job'))) if 'bench.py' in cmd else []
    if bench:                                   # benchmark run record: trajectory rows [t, cost, G, A, GD, AD]
        br = json.loads(bench[0].read_text())
        out['time_to_result_s'] = {'job': s['best'].get('job'), 'within_job_s': br['trajectory'][-1][0],
                                   'job_budget_s': br['run'].get('seconds')}
        out['run_record'] = str(bench[0]).replace(HOME, '~')
        capped = True
    elif rs and rs.get('runs'):
        tag = s['best'].get('job') or 'r%s-s%s' % (s['best'].get('round'), s['best'].get('seed'))
        job = next((r for r in rs['runs'] if r.get('tag') == tag), None)
        t = (s['best']['metrics'][k] for k in ('A', 'AD', 'G', 'GD'))
        t = tuple(t)
        reach = sorted({r['seed'] for r in rs['runs'] if r.get('metrics') and
                        tuple(r['metrics'][k] for k in ('A', 'AD', 'G', 'GD')) == t})
        imp = (job or {}).get('improvements') or []
        out['time_to_result_s'] = {'job': tag, 'round': (job or {}).get('round'),
                                   'within_job_s': imp[-1]['t'] if imp else 0.0,
                                   'iteration': imp[-1]['it'] if imp else 0,
                                   'job_wall_s': (job or {}).get('wall_s'), 'run_wall_s': rs.get('wall_s')}
        it = s.get('iters')
        capped = any(r.get('time_capped') or (it and (r.get('final') or {}).get('iters', it) < it) for r in rs['runs'])
        out['seeds_reaching_tuple'] = '%d of %d seeds (%s)' % (len(reach), len(rs['seeds']), ','.join(map(str, reach)))
        out['run_record'] = str(run_dir).replace(HOME, '~')
    else:
        capped = None
        for k in ('time_to_result_s', 'seeds_reaching_tuple', 'run_record'):
            if prev and k in prev:
                out[k] = prev[k]
    if s.get('time_budgeted'):
        rep = 'one-off: time-budgeted run, verified, not bit-reproducible'
    elif capped:
        rep = 'not deterministic: a job hit its time cap'
    else:
        rep = 'deterministic command: every job ended on its iteration budget, so the command gives the same circuit'
        own = core.to_kernel(core.read_ncff(str(f)))
        for d in REPRO_RUNS:
            b = d / 'best.circ.txt'
            if b.exists() and core.to_kernel(core.read_ncff(str(b))) == own:
                rep = 'reproduced: re-run from scratch (%s) gave the identical gate list' % str(d).replace(HOME, '~')
        if capped is None and prev and prev.get('reproduction'):
            rep = prev['reproduction']
    out['reproduction'] = rep
    return out


def nist_export(c, model_metrics):
    m = model_metrics; cnt = m['counts']
    nots = cnt.get('NOT', 0); xx = cnt.get('XOR', 0) + cnt.get('XNOR', 0)
    tail = ('xxn%d-%d-%d' % (xx + nots, cnt.get('XNOR', 0), nots)) if nots else ('xx%d-%d' % (xx, cnt.get('XNOR', 0)))
    name = 'aes-sbox-a%d-ad%d-g%d-gd%d-%s' % (m['A'], m['AD'], m['G'], m['GD'], tail)
    c.name = name
    return name, core.write_ncff(c, None, comments=['BoolFlux result, NIST accounting (NOT counted as a gate)'])


def main():
    out = {'nist_baseline_commit': NEW_PIN, 'entries': []}
    mp = PKG / 'results' / 'MANIFEST.json'
    prev = {e['sha256']: e for e in json.loads(mp.read_text()).get('entries', [])} if mp.exists() else {}
    sys.path.insert(0, str(HERE))
    import aes_check                                    # noqa: E402  (pinned-set status of AES entries)
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
        if any(k in s for k in ('mechanism', 'reproduction')):      # curated campaign result
            for k in EXTRA:
                if k in s:
                    e[k] = s[k]
        else:
            e.update(derived_provenance(s, f, prev.get(e['sha256'])))
        if s['target'] == 'aes':
            c = core.read_ncff(str(f))
            name, text = nist_export(c, c.metrics())
            (nf / (name + '.circ.txt')).write_text(text, encoding='utf-8')
            e['nist_format_file'] = 'nonlinear/boolflux/results/nist-format/%s.circ.txt' % name
            if s['model'] == 'nist':
                r = aes_check.check(nf / (name + '.circ.txt'))
                e['pinned_set'] = {'nist_commit': NEW_PIN[:7], 'tuple_A_AD_G_GD': list(r['tuple']),
                                   'new_point': r.get('new_point'), 'dominated_by': r.get('dominated_by'),
                                   'best_published_at_same_A_AD_GD_caps': r.get('best_at_a_ad_gd_caps')}
        out['entries'].append(e)
    # results of ours that strictly dominate an AES entry, and the Pareto set of the AES results
    aes = [e for e in out['entries'] if 'pinned_set' in e]
    tup = lambda e: tuple(e['pinned_set']['tuple_A_AD_G_GD'])
    for e in aes:
        e['pinned_set']['superseded_by_ours'] = sorted(
            {Path(o['file']).name for o in aes if tup(o) != tup(e) and all(a <= b for a, b in zip(tup(o), tup(e)))})
    par = sorted({tup(e) for e in aes if e['pinned_set']['new_point'] and not e['pinned_set']['superseded_by_ours']},
                 key=lambda t: (t[3], t[2], t))
    out['aes_pareto'] = {'rule': 'not dominated by any pinned NIST forward circuit (all four <=, equality counts) '
                                 'and not strictly dominated by another AES result here',
                         'nist_commit': NEW_PIN[:7], 'count': len(par),
                         'tuples_A_AD_G_GD': [list(t) for t in par]}
    # third counter: boolcirc via nonlinear/check.py (function + metrics vs name)
    r = subprocess.run([sys.executable, str(REPO / 'nonlinear' / 'check.py'), str(nf)], capture_output=True, text=True)
    out['nist_format_check'] = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-500:]
    (PKG / 'results' / 'MANIFEST.json').write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
    print('%d entries, %d failing verification; nist-format check: %s' % (len(out['entries']), bad, out['nist_format_check']))
    if r.returncode != 0 or bad:
        print(r.stdout[-3000:]); sys.exit(1)


if __name__ == '__main__':
    main()
