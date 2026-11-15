"""Write results/MANIFEST.json and results/nist-format/: provenance and three-way verification.

    python3 nonlinear/boolflux/campaigns/manifest.py
    python3 nonlinear/boolflux/campaigns/manifest.py --check-repro N [--seed S] [--only TEXT]
                                                     [--mode snapshot|head|both]

--check-repro re-runs the winning kernel job of N sampled entries whose runs were iteration-bounded
(--only TEXT: the entries whose file name contains TEXT instead of a sample) and reports which
still give the recorded circuit: `snapshot` = the run's own binary (RUN/bin/bfx) on its own
config and start, `head` = the kernel built from the current source with the config the command
writes today.  Results accumulate in results/REPRO-CHECK.json; the next plain run of manifest.py
copies them into the entries (`reproducibility.checked`) and into the `reproduction` text.  One
job of an AES run is 0.5 to 2 CPU-minutes; run it under taskset / the memory guard like any job.

Reproducibility is recorded per entry in `reproducibility` (review 5, after L2's audit): the
class (deterministic / one-off / construction), the code that RAN (`code_at_run`: the hash in
the run's summary.json, its src/ and bin/ snapshot, the sha256 of the binary), whether the
current source still equals that snapshot (`head_same_source`, compared file by file), and the
re-runs made.  "Deterministic" means: with the run's own snapshot.  The command at the current
code gives the same circuit only if the source is unchanged or a `head` check says so.
For curated campaign results, `code_version_recorded` says whether the code version was taken at
run time or only at curation time, and `code_version_commit_check` compares curation-time script
hashes with the commit that later archived the scripts.  `caps_met` is computed from the metrics
and the job's caps; a job that ended outside its caps says so in `mechanism`.

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
import re
import subprocess
import sys
import time
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
    if not start:      # construction or study-agent result without a single start file (parents list it)
        return {'kind': 'no single start file; see parents and the campaign sidecar'}
    p = Path(str(start).replace('~', HOME, 1) if str(start).startswith('~') else start)
    rel = str(p) if not p.is_absolute() else str(p.relative_to(REPO)) if str(p).startswith(str(REPO)) else str(p)
    info = {'path': rel.replace(HOME, '~')}
    if rel.startswith('nonlinear/nist/'):
        new = (REPO / rel).read_bytes() if (REPO / rel).exists() else None
        first = next(((pin, b) for pin, b in ((pin, git_show(rc, rel)) for pin, rc in PINS) if b), (None, None))
        info.update({'kind': 'NIST circuit', 'taken_from_nist_commit': first[0],
                     'sha256': sha(first[1]) if first[1] else None,
                     'identical_at_' + NEW_PIN[:7]: (first[1] == new) if first[1] and new else False})
    elif not Path(rel).is_absolute() and (REPO / rel).exists():
        # review5 P20: REPO / <absolute path> is that absolute path, so every existing campaign
        # file outside the repository was labelled 'BoolFlux result'
        info.update({'kind': 'BoolFlux result', 'sha256': sha((REPO / rel).read_bytes())})
    elif p.exists():
        info.update({'kind': 'campaign circuit (outside the repository)', 'sha256': sha(p.read_bytes())})
    return info


SCRIPTS_COMMIT = '377b03f'                  # first commit that holds strategies/C-G (made after the curation)
SNAP_FILES = ('bfx.c', 'skel.c', 'cli.py', 'core.py', 'skeleton.py', 'starts.py', 'targets.py', 'objective.py', 'workflow.py')
REPRO_FILE = PKG / 'results' / 'REPRO-CHECK.json'


def expand(p):
    return Path(str(p).replace('~', HOME, 1) if str(p).startswith('~') else str(p))


def code_at_run(run_dir, code_hash=None):
    """What ran: the run folder's source and binary snapshot (cli.snapshot), and whether the current
    source still equals it.  head_same_source is None when the snapshot is gone."""
    out = {'code_sha256_12': code_hash, 'snapshot': None, 'binary_sha256': None, 'head_same_source': None}
    if run_dir is None:
        return out
    src = Path(run_dir) / 'src'; b = Path(run_dir) / 'bin' / 'bfx'
    if b.exists():
        out['binary_sha256'] = sha(b.read_bytes())
    if src.is_dir():
        out['snapshot'] = str(Path(run_dir)).replace(HOME, '~')
        diff = []
        for n in SNAP_FILES:
            cur = PKG / ('kernel/' + n if n.endswith('.c') else n)
            old = src / n
            if not old.exists() or not cur.exists() or old.read_bytes() != cur.read_bytes():
                diff.append(n)
        out['head_same_source'] = not diff
        out['source_files_changed_since'] = diff
    return out


def reproduction_text(rep):
    """One sentence from the structured record.  'deterministic' never means more than: with the
    run's own snapshot (L2's audit: 28/4/133/20 replays byte for byte with its binary, and the
    same command ends at 134 with the code of f9fe6f7)."""
    car = rep.get('code_at_run') or {}
    if rep['class'] != 'deterministic':
        return rep['text']
    if car.get('snapshot'):
        t = ('deterministic with the run\'s own snapshot (%s/src and bin, code %s): every job ended on its iteration budget'
             % (car['snapshot'], car.get('code_sha256_12')))
    else:
        t = 'every job ended on its iteration budget (code %s); the run folder with its snapshot is gone, so this cannot be replayed' % car.get('code_sha256_12')
    if car.get('head_same_source') is True:
        t += '. The package source is unchanged since, so the command gives the same circuit at the current code'
    elif car.get('head_same_source') is False:
        t += ('. The source has changed since (%s), so the command at the current code is NOT known to give this circuit'
              % ', '.join(car.get('source_files_changed_since') or []))
    for d in rep.get('reruns') or []:
        t += '. ' + d
    for mode, c in sorted((rep.get('checked') or {}).items()):
        what = 'snapshot replay' if mode == 'snapshot' else 'current code (%s)' % c.get('code')
        t += '. Checked %s, %s: %s' % (c.get('utc', '')[:10], what, 'identical circuit' if c.get('identical')
                                       else 'could not be run (%s)' % str(c.get('error'))[:80] if c.get('identical') is None
                                       else 'a DIFFERENT circuit with the same A AD G GD' if c.get('same_metrics')
                                       else 'DIFFERENT result %s' % c.get('result_A_AD_G_GD'))
    return t


def caps_status(e):
    """caps_met from the metrics and the caps of the job; a job that ended outside its caps says so
    in the mechanism (two track E entries read "under caps" although the A cap was never met)."""
    jc = e.get('job_caps') or e.get('caps') or {}
    over = ['cap %s %s, circuit %s %s' % (k, v, k, e['metrics'][k]) for k, v in jc.items() if v is not None and e['metrics'][k] > v]
    e['caps_met'] = not over
    if over and 'CAPS NOT MET' not in e.get('mechanism', ''):
        e['mechanism'] = (e.get('mechanism', '') + ' -- CAPS NOT MET by this job (%s): the circuit is the best state of a run '
                          'that never came within its caps, recorded without caps' % '; '.join(over)).strip()


def curated_code_record(e):
    """Was the code version of a curated result recorded when it ran, or only at curation?"""
    cv = e.get('code_version') or {}
    checks = {}; at_run = []
    for k, v in cv.items():
        m = re.match(r'strategies/(\w+) \(', k)
        if m and isinstance(v, dict):
            for name, h in v.items():
                b = git_show(SCRIPTS_COMMIT, 'nonlinear/boolflux/strategies/%s/%s' % (m.group(1), name))
                checks['strategies/%s/%s' % (m.group(1), name)] = (
                    'identical to commit %s' % SCRIPTS_COMMIT if b is not None and h and sha(b)[:len(h)] == h
                    else 'not in commit %s' % SCRIPTS_COMMIT if b is None else 'differs from commit %s' % SCRIPTS_COMMIT)
        elif k.startswith(('hub', 'snapshot')):
            at_run.append(k)
    if checks:
        e['code_version_recorded'] = ('script hashes taken at curation time (%s), not at run time: the campaign did not record '
                                      'a code version per job%s' % (e.get('curated_utc'), '; ' + ', '.join(at_run) + ' recorded at run time' if at_run else ''))
        e['code_version_commit_check'] = checks
    elif at_run or e.get('code_sha256_12'):
        e['code_version_recorded'] = 'at run time (%s)' % (', '.join(at_run) or 'code_sha256_12 from the run\'s summary.json')
    cls = ('construction' if 'construction' in (e.get('reproduction') or '') or 'copied into' in (e.get('reproduction') or '') else 'one-off')
    e['reproducibility'] = {'class': cls, 'text': e.get('reproduction'), 'code_recorded_at_run': not checks}


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
    car = code_at_run(run_dir if run_dir and run_dir.exists() else None, s.get('code_sha256_12') or s.get('kernel_sha256_12'))
    if s.get('time_budgeted'):
        rec = {'class': 'one-off', 'text': 'one-off: time-budgeted run, verified, not bit-reproducible'}
    elif capped:
        rec = {'class': 'one-off', 'text': 'not deterministic: a job hit its time cap'}
    elif capped is None and not (rs and rs.get('runs')):
        # no run record left to tell whether a job was time-capped: keep the earlier statement
        rec = {'class': 'unknown', 'text': (prev or {}).get('reproduction') or 'run record gone: iteration-bounded or not is unknown'}
    else:
        rec = {'class': 'deterministic', 'reruns': []}
        own = core.to_kernel(core.read_ncff(str(f)))
        for d in REPRO_RUNS:
            b = d / 'best.circ.txt'
            if b.exists() and core.to_kernel(core.read_ncff(str(b))) == own:
                dc = json.loads((d / 'summary.json').read_text()).get('code_sha256_12') if (d / 'summary.json').exists() else None
                rec['reruns'].append('Re-run from scratch in %s (code %s) gave the identical gate list' % (str(d).replace(HOME, '~'), dc))
    rec['code_at_run'] = car
    out['reproducibility'] = rec
    out['reproduction'] = reproduction_text(rec)
    return out


# ---- --check-repro ---------------------------------------------------------------------------
def replay(entry, mode, tmp):
    """Re-run the winning kernel job of a deterministic entry.  snapshot: RUN/bin/bfx with the
    job's own config (only the out path changed).  head: the kernel compiled from the current
    source, with the config that cli.kernel_config writes today for the entry's objective, caps,
    iterations, kernel seed and the command's --set options, from the job's recorded start.
    For a job of a later round or of `pipe` this replays that job's gate-kernel stage from its
    recorded start circuit, not the whole command."""
    import argparse
    run = expand(entry['run_record']); tag = entry['time_to_result_s']['job']
    start = run / ('%s.start.bfx' % tag); best = run / ('%s.best.bfx' % tag); cfg0 = run / ('%s.cfg' % tag)
    res = {'mode': mode, 'job': tag, 'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    if not (start.exists() and best.exists() and cfg0.exists()):
        return dict(res, identical=None, error='job files missing in %s' % run)
    out = Path(tmp) / ('%s-%s.out.bfx' % (mode, tag)); cfg = Path(tmp) / ('%s-%s.cfg' % (mode, tag))
    if mode == 'snapshot':
        binary = run / 'bin' / 'bfx'
        lines = []
        for ln in cfg0.read_text().splitlines():
            k = ln.split(None, 1)[0] if ln.strip() else ''
            lines.append('out %s' % out if k == 'out' else 'in %s' % start if k == 'in' else ln)
        cfg.write_text('\n'.join(lines) + '\n')
        res['code'] = entry.get('code_sha256_12')
    else:
        binary = Path(tmp) / 'bfx-head'
        if not binary.exists():
            subprocess.run(['gcc', '-O2', '-o', str(binary), str(PKG / 'kernel' / 'bfx.c'), '-lm'], check=True)
        rs = json.loads((run / 'summary.json').read_text())
        job = next(r for r in rs['runs'] if r.get('tag') == tag)
        caps = entry['caps']
        args = argparse.Namespace(objective=entry['objective'], cap_gd=caps.get('GD'), cap_ad=caps.get('AD'),
                                  cap_a=caps.get('A'), seconds=36000, iters=entry['iters'])
        extra = dict(x.split('=', 1) for x in re.findall(r'--set (\S+=\S+)', entry['command']) if not x.startswith(('skel.', 'synth.')))
        cli.kernel_config(cfg, str(start), str(out), core.Model.load(entry['model']), args, job.get("kernel_seed", job["seed"] + 1000 * job.get("round", 0)), extra)
        res['code'] = cli.kernel_hash()
    t0 = time.time()
    r = subprocess.run([str(binary), str(cfg)], capture_output=True, text=True)
    res['seconds'] = round(time.time() - t0, 1)
    if r.returncode != 0 or not out.exists():
        return dict(res, identical=None, error=(r.stdout + r.stderr)[-300:])
    c = core.from_kernel(out.read_text()); m = c.metrics()
    want = core.read_ncff(str(REPO / entry['file']))
    res['result_A_AD_G_GD'] = [m['A'], m['AD'], m['G'], m['GD']]
    res['identical'] = core.to_kernel(c) == core.to_kernel(want)
    wm = want.metrics()
    res['same_metrics'] = res['result_A_AD_G_GD'] == [wm['A'], wm['AD'], wm['G'], wm['GD']]
    res['identical_to_job_file'] = out.read_bytes() == best.read_bytes()
    return res


def check_repro(argv):
    import random
    import tempfile
    n = int(argv[argv.index('--check-repro') + 1])
    seed = int(argv[argv.index('--seed') + 1]) if '--seed' in argv else 1
    only = argv[argv.index('--only') + 1] if '--only' in argv else None
    mode = argv[argv.index('--mode') + 1] if '--mode' in argv else 'both'
    if mode not in ('snapshot', 'head', 'both'):
        raise SystemExit('--mode snapshot|head|both')
    man = json.loads((PKG / 'results' / 'MANIFEST.json').read_text())
    det = [e for e in man['entries'] if (e.get('reproducibility') or {}).get('class') == 'deterministic'
           or str(e.get('reproduction', '')).startswith(('deterministic command', 'deterministic with', 'reproduced'))]
    det = [e for e in det if e.get('run_record') and (e.get('time_to_result_s') or {}).get('job')]
    pick = [e for e in det if only in e['file']] if only else random.Random(seed).sample(det, min(n, len(det)))
    done = json.loads(REPRO_FILE.read_text()) if REPRO_FILE.exists() else {}
    print('%d deterministic entries with a run record; checking %d (%s)' % (len(det), len(pick), mode))
    bad = 0
    with tempfile.TemporaryDirectory(prefix='repro-') as tmp:
        for e in pick:
            for md in (('snapshot', 'head') if mode == 'both' else (mode,)):
                r = replay(e, md, tmp)
                done.setdefault(e['file'], {'sha256': e['sha256']})[md] = r
                done[e['file']]['sha256'] = e['sha256']
                ok = r.get('identical')
                bad += ok is not True
                print('%-9s %-8s %s  %s  (%s s, code %s)' % (
                    'IDENTICAL' if ok else 'ERROR' if ok is None else 'DIFFERENT', md, Path(e['file']).name,
                    ('another circuit with the same metrics; ' if r.get('same_metrics') and not ok else '') +
                    r.get('error') or 'result A AD G GD %s, recorded %s' % (r.get('result_A_AD_G_GD'), [e['metrics'][k] for k in ('A', 'AD', 'G', 'GD')]),
                    r.get('seconds'), r.get('code')), flush=True)
                REPRO_FILE.write_text(json.dumps(done, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    print('%d check(s) not identical; results in %s (run manifest.py to copy them into MANIFEST.json)' % (bad, REPRO_FILE.relative_to(REPO)))
    return 1 if bad else 0


def nist_export(c, model_metrics):
    m = model_metrics; cnt = m['counts']
    nots = cnt.get('NOT', 0); xx = cnt.get('XOR', 0) + cnt.get('XNOR', 0)
    tail = ('xxn%d-%d-%d' % (xx + nots, cnt.get('XNOR', 0), nots)) if nots else ('xx%d-%d' % (xx, cnt.get('XNOR', 0)))
    name = 'aes-sbox-a%d-ad%d-g%d-gd%d-%s' % (m['A'], m['AD'], m['G'], m['GD'], tail)
    c.name = name
    return name, core.write_ncff(c, None, comments=['BoolFlux result, NIST accounting (NOT counted as a gate)'])


def nist_format_name(nf, name, text, written):
    """File name for a NIST-format copy.  Two different circuits can have the same tuple and gate
    counts, hence the same NIST-style name; the second used to overwrite the first, and both
    entries then pointed at one file (review5 P14).  A different circuit gets -v2, -v3, ...
    (nonlinear/check.py reads the metrics from the front of the name)."""
    k = 1; nm = name
    while nm in written and written[nm] != text:
        k += 1; nm = '%s-v%d' % (name, k)
    written[nm] = text
    (nf / (nm + '.circ.txt')).write_text(text, encoding='utf-8')
    return nm


def main():
    if '--check-repro' in sys.argv[1:] and not any(a in ('-h', '--help') for a in sys.argv[1:]):
        try:
            return check_repro(sys.argv[1:])
        except (IndexError, ValueError):
            print(__doc__.strip()); return 2
    if len(sys.argv) > 1:
        print(__doc__.strip())
        return 0 if sys.argv[1] in ('-h', '--help') else 2
    checks = json.loads(REPRO_FILE.read_text()) if REPRO_FILE.exists() else {}
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
    written = {}                                        # nist-format name -> text
    by_gates = {}                                       # (target, gate list) -> first results file
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
            curated_code_record(e)
        else:
            e.update(derived_provenance(s, f, prev.get(e['sha256'])))
            ck = checks.get(e['file'])
            if ck and ck.get('sha256') == e['sha256'] and e['reproducibility']['class'] == 'deterministic':
                e['reproducibility']['checked'] = {k: v for k, v in ck.items() if k in ('snapshot', 'head')}
                for v in e['reproducibility']['checked'].values():
                    v['same_metrics'] = v.get('result_A_AD_G_GD') == [e['metrics'][k] for k in ('A', 'AD', 'G', 'GD')]
                e['reproduction'] = reproduction_text(e['reproducibility'])
        caps_status(e)
        if s['target'] == 'aes':
            c = core.read_ncff(str(f))
            name, text = nist_export(c, c.metrics())
            name = nist_format_name(nf, name, text, written)
            e['nist_format_file'] = 'nonlinear/boolflux/results/nist-format/%s.circ.txt' % name
            if s['model'] == 'nist':
                r = aes_check.check(nf / (name + '.circ.txt'))
                e['pinned_set'] = {'nist_commit': NEW_PIN[:7], 'tuple_A_AD_G_GD': list(r['tuple']),
                                   'new_point': r.get('new_point'), 'dominated_by': r.get('dominated_by'),
                                   'best_published_at_same_A_AD_GD_caps': r.get('best_at_a_ad_gd_caps')}
        # the same gate list under two result files is one circuit: say so in both entries
        first = by_gates.setdefault((s['target'], core.to_kernel(core.read_ncff(str(f)))), e['file'])
        if first != e['file']:
            e['same_circuit_as'] = first
        out['entries'].append(e)
    out['duplicate_circuits'] = sorted([e['file'], e['same_circuit_as']] for e in out['entries'] if 'same_circuit_as' in e)
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
    for a, b in out['duplicate_circuits']:
        print('same circuit in two result files: %s = %s' % (a, b))
    if r.returncode != 0 or bad:
        print(r.stdout[-3000:]); sys.exit(1)


if __name__ == '__main__':
    sys.exit(main())
