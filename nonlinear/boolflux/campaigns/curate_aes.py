#!/usr/bin/env python3
"""Copy new verified AES Pareto points from the AES-push campaign into results/aes/, with provenance.

    taskset -c 0 python3 nonlinear/boolflux/campaigns/curate_aes.py [--dry-run]

Selection is best_table.py's: every candidate it collects (results/aes, each track's found/, the
main track's best.circ.txt, track E's admitted pools), first circuit per (A, AD, G, GD) tuple, kept
when no pinned NIST forward circuit has all four metrics <= (equality counts as dominated) and no
other candidate strictly dominates it.  In addition, a distinct circuit at a surviving tuple is kept
once per track (so a tuple reached independently by two tracks is recorded twice).  Tuples already
in results/aes are skipped.  Each selected circuit is re-verified (aes_check: both verifiers, all
256 inputs) and written as

    results/aes/aes-nist-<track>-<mechanism>-g<G>-a<A>-gd<GD>-ad<AD>.circ.txt   (NCFF, NOT as XNOR t a 0)
    ...summary.json    fields read by manifest.py (target, model, objective, caps, start, command,
                       seeds, iters, rounds, code_sha256_12, wall_s, best) plus parents, mechanism,
                       time_to_result_s, reproduction, run_record, campaign_source (+ sha256),
                       code_version, curated_utc
    ...campaign.json   the campaign's own sidecar, copied verbatim (when there is one)

Campaign folders are only read.  Run campaigns/manifest.py afterwards.
"""
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
REPO = PKG.parents[1]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(PKG.parent))
import aes_check as AC                     # noqa: E402
import best_table as BT                    # noqa: E402
from boolflux import core                  # noqa: E402

C = BT.C
RES = PKG / 'results' / 'aes'
MODEL = core.Model.load('nist')
HOME = str(Path.home())
E_KERNEL = 'kernel/bfx.c at git 0659eb9 (copy strategies/E/bfx_new), lex cost,gd'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def tilde(p):
    s = str(p)
    if s.startswith(str(REPO) + '/'):
        return s[len(str(REPO)) + 1:]
    return s.replace(HOME, '~')


def file_sha(p):
    p = Path(str(p).replace('~', HOME, 1))
    return sha(p.read_bytes()) if p.exists() else None


def strategy_version(track, names):
    """strategies/ is not committed: record the sha256 of the scripts as they are now."""
    d = PKG / 'strategies' / track
    return {n: (sha((d / n).read_bytes())[:12] if (d / n).exists() else None) for n in names}


def load_circuit(f):
    return core.from_kernel(f.read_text()) if f.suffix == '.bfx' else core.read_ncff(str(f))


def track_of(f):
    s = str(f)
    if s.startswith(str(RES)):
        return 'results'
    rel = Path(s).relative_to(C)
    return rel.parts[0]


# ---- track E memetic runs: resolve a pool hash to its origin ------------------------------
_runs = {}
BASENAMES = {}


def memetic_run(rdir):
    rdir = Path(rdir)
    if rdir in _runs:
        return _runs[rdir]
    nodes = {}
    for x in json.loads((rdir / 'frontier.json').read_text()):
        nodes[x['h']] = {'m': x['m'], 'origin': x['origin']}
    for j in (rdir / 'admitted').glob('*.json'):
        d = json.loads(j.read_text())
        nodes[j.stem] = {'m': d['metrics'], 'origin': d['origin']}
    ev = [json.loads(l) for l in (rdir / 'log.jsonl').read_text().splitlines() if l.strip()]
    t0 = next(e['ts'] for e in ev if e['ev'] == 'start')
    admit_ts = {}
    for e in ev:
        if e['ev'] == 'admit':
            admit_ts.setdefault(e['h'], e['ts'] - t0)
        if e['ev'] == 'polished' and e.get('admitted'):
            admit_ts.setdefault(('polish', e['h'], tuple(e['m'])), e['ts'] - t0)
    # inputs that left the frontier: hash every file of the run's input list as memetic.py does
    fl = rdir.parent / 'files.list'
    if fl.exists():
        for ln in fl.read_text().split():
            p = Path(ln)
            BASENAMES.setdefault(p.name, str(p))
            try:
                c = core.from_kernel(p.read_text()) if p.suffix == '.bfx' else core.read_ncff(str(p))
            except Exception:
                continue
            h = hashlib.sha1(core.to_kernel(c).encode()).hexdigest()[:16]
            if h not in nodes:
                m = c.metrics(MODEL)
                nodes[h] = {'m': [m['A'], m['AD'], m['G'], m['GD']], 'origin': {'kind': 'input', 'file': str(p)}}
    _runs[rdir] = (nodes, admit_ts)
    return _runs[rdir]


def lineage(rdir, h, depth=0):
    nodes, _ = memetic_run(rdir)
    n = nodes.get(h)
    if n is None:
        return {'hash': h, 'unresolved': True}
    o = dict(n['origin'])
    out = {'hash': h, 'metrics_A_AD_G_GD': n['m'], 'kind': o.get('kind')}
    if o.get('kind') == 'input':      # frontier.json stores some inputs by base name only
        out['file'] = tilde(o['file'] if '/' in o['file'] else BASENAMES.get(o['file'], o['file']))
        return out
    if depth > 12:
        out['truncated'] = True
        return out
    if o.get('kind') == 'splice':
        out.update(LX=o.get('LX'), LY=o.get('LY'), interface_gates=o.get('interface'),
                   front=lineage(rdir, o['front'], depth + 1), back=lineage(rdir, o['back'], depth + 1))
    elif o.get('kind') == 'polish':
        out.update(seed=o.get('seed'), seconds=o.get('seconds'), caps=o.get('caps'),
                   time_to_result_s=o.get('time_to_result_s'), parent=lineage(rdir, o['from'], depth + 1))
    return out


def polish_caps(rdir, origin):
    if origin.get('caps'):
        return {k: origin['caps'].get(k) for k in ('GD', 'AD', 'A')}
    nodes, _ = memetic_run(rdir)
    p = nodes.get(origin['from'])
    if p:
        A, AD, G, GD = p['m']
        return {'GD': GD, 'AD': AD, 'A': A}
    return {'GD': None, 'AD': None, 'A': None}


def describe_memetic(rdir, h, m):
    nodes, admit_ts = memetic_run(rdir)
    o = nodes[h]['origin']
    arm = rdir.parent.name + '/' + rdir.name
    launch = {'long1': 'strategies/E/long.sh long1 9.3 120 (memetic.py --arm %s --hours 9.3 --polish 120; stopped 17:28 UTC)',
              'low1': 'strategies/E/low.sh low1 8.8 120 (memetic.py --arm splice --amax 31 --gd-pull 0.5 --polish 120; stopped 17:28 UTC)'}
    cmd = launch.get(rdir.parent.name, 'memetic.py').replace('%s', rdir.name)
    lin = lineage(rdir, h)
    s = {'command': cmd, 'run_record': tilde(rdir) + ' (log.jsonl, admitted/, frontier.json; run log ' + tilde(rdir.parent / (rdir.name + '.log')) + ')',
         'parents': [lin], 'seeds': [], 'iters': None, 'rounds': None,
         'code_version': {'kernel': E_KERNEL, 'strategies/E (uncommitted, sha256 now)': strategy_version('E', ['memetic.py', 'splice2.py', 'erun.py', 'common.py'])}}
    if o['kind'] == 'splice':
        s.update(mechanism='join: stage transplant at an interface (splice2.py; front of one pool circuit, back of another, interface rebuilt as affine combinations of the front signals), arm %s' % arm,
                 objective='construction (admitted if Pareto-new vs pool + pinned set)', caps={'GD': None, 'AD': None, 'A': None},
                 time_to_result_s={'since_run_start_s': round(admit_ts.get(h, float('nan')), 1)},
                 reproduction='deterministic construction from its two parents (re-running splice2 on the same pair and cut levels gives the same circuit); not re-run')
        s['start'] = (lin['front'].get('file') or 'pool hash ' + o['front'])
        s['mech_short'] = 'join'
    else:
        caps = polish_caps(rdir, o)
        pull = bool((o.get('caps') or {}).get('tag', '').startswith('gd'))
        s.update(mechanism=('depth pull: gate kernel with the gate-depth cap lowered below the parent\'s (A cap = parent\'s, AD free), 120 s, arm %s' if pull
                            else 'polish: gate kernel under the parent\'s own caps, 120 s, arm %s') % arm,
                 objective='cost,gd', caps=caps, seeds=[o.get('seed')],
                 time_to_result_s={'within_job_s': o.get('time_to_result_s'),
                                   'since_run_start_s': round(admit_ts.get(('polish', o['from'], tuple(m)), float('nan')), 1)},
                 reproduction='one-off: 120 s time-budgeted kernel job (not bit-reproducible); not re-run')
        par = lin.get('parent', {})
        s['start'] = par.get('file') or 'pool hash %s (%s)' % (o['from'], par.get('kind'))
        s['mech_short'] = 'pull' if pull else 'polish'
    return s


def describe(f, m):
    """Provenance of one campaign circuit, from its sidecar."""
    tr = track_of(f)
    side = None
    if f.suffix == '.bfx':
        side = f.with_suffix('.json')
    else:
        j = Path(str(f)[:-len('.circ.txt')] + '.json')
        side = j if j.exists() else None
    sd = json.loads(side.read_text()) if side and side.exists() else {}
    tup = [m['A'], m['AD'], m['G'], m['GD']]
    if tr == 'E' and f.suffix == '.bfx':
        s = describe_memetic(f.parent.parent, f.stem, tup)
    elif tr == 'E' and 'run' in sd and 'hash' in sd:
        s = describe_memetic(Path(sd['run']), sd['hash'], tup)
    elif tr == 'E' and sd.get('mechanism', '').startswith('splice2'):
        s = {'mechanism': 'join: stage transplant at an interface (splice2.py, sp1 sweep over all ordered pairs and cut levels of 150 circuits), front %s (LX %s), back %s (LY %s), %s interface gates' % (sd['front'], sd['LX'], sd['back'], sd['LY'], sd['interface_gates']),
             'mech_short': 'join', 'command': sd['command'], 'run_record': tilde(sd['source']),
             'parents': [{'role': 'front', 'file': sd['front'], 'LX': sd['LX']}, {'role': 'back', 'file': sd['back'], 'LY': sd['LY']}],
             'start': sd['front'], 'objective': 'construction', 'caps': {'GD': None, 'AD': None, 'A': None},
             'seeds': [], 'iters': None, 'rounds': None, 'time_to_result_s': sd.get('time_to_result_s'),
             'code_version': {'strategies/E (uncommitted, sha256 now)': strategy_version('E', ['splice2.py', 'export_splices.py', 'common.py'])},
             'reproduction': 'deterministic construction from its two parents; not re-run'}
    elif tr == 'E':                                     # polish1 (erun.py)
        s = {'mechanism': 'polish: gate kernel (erun.py, %s s) from %s under caps %s' % (sd['seconds'], tilde(sd['start']), sd['caps']),
             'mech_short': 'polish', 'command': tilde(sd['command']), 'run_record': tilde(sd['source_dir']),
             'parents': [{'file': tilde(sd['start']), 'metrics_A_AD_G_GD': sd['start_metrics']}],
             'start': tilde(sd['start']), 'objective': sd['objective'], 'caps': {k: sd['caps'].get(k) for k in ('GD', 'AD', 'A')},
             'seeds': [sd['seed']], 'iters': None, 'rounds': None, 'time_to_result_s': sd.get('time_to_result_s'),
             'code_version': {'kernel': E_KERNEL, 'strategies/E (uncommitted, sha256 now)': strategy_version('E', ['erun.py'])},
             'reproduction': 'one-off: %s s time-budgeted kernel job (not bit-reproducible); not re-run' % sd['seconds']}
    elif tr == 'D':
        s = {'mechanism': sd['mechanism'], 'mech_short': 'kernel', 'command': tilde(sd['command']),
             'run_record': tilde(sd['cycle_dir']), 'parents': [{'file': tilde(sd['start'])}], 'start': tilde(sd['start']),
             'objective': 'cost,a,gd', 'caps': {'GD': 14, 'AD': None, 'A': None}, 'seeds': [sd['seed']],
             'kernel_seed': sd.get('cycle_seed'), 'iters': None, 'rounds': None,
             'time_to_result_s': sd['time_to_result_s'],
             'code_version': {'kernel': 'strategies/D/bfx = kernel/bfx.c at git 0659eb9 (sha256 e3c4ad1a0767), lex cost,a,gd',
                              'strategies/D (uncommitted, sha256 now)': strategy_version('D', ['breathe.py', 'kern.py', 'wresyn.py'])},
             'reproduction': 'one-off: time-budgeted 120 s kernel stage (not bit-reproducible); the same tuple was reached independently by track F (a different circuit)'}
    elif tr == 'F':
        mode = 'trb' if '--mode trb' in sd.get('command', '') else 'gate'
        s = {'mechanism': sd['mechanism'] + ('; ' + sd['config'] if sd.get('config') else ''), 'mech_short': mode,
             'command': tilde(sd['command']), 'run_record': tilde(Path(sd['source']).parent),
             'parents': [{'file': tilde(sd['start'].replace('--start ', ''))}], 'start': tilde(sd['start'].replace('--start ', '')),
             'objective': 'cost,gd', 'caps': {'GD': m['GD'], 'AD': m['AD'] if '--cap-ad' in sd.get('command', '') or 'AD4' in sd.get('config', '') else None, 'A': None},
             'seeds': [sd.get('seed')], 'iters': None, 'rounds': None, 'time_to_result_s': sd.get('time_to_result_s'),
             'code_version': {'kernel': 'F snapshot kernel (bfx.c sha256 7c53f2e4..., ~/xs-campaigns/2026-11-13-aes/F/snap)',
                              'strategies/F (uncommitted, sha256 now)': strategy_version('F', ['fdrive.py', 'trb.py', 'campaign.py'])},
             'reproduction': 'one-off: time-budgeted job (not bit-reproducible); not re-run' +
                             ('' if m['G'] != 121 else '; the same tuple was reached independently by track D (a different circuit)'),
             'recorded_utc': sd.get('recorded_utc')}
    elif tr == 'main':
        rs = json.loads((f.parent / 'summary.json').read_text())
        best_seed = int(rs['best']['origin'].split()[-1])
        run = next(r for r in rs['runs'] if r.get('seed') == best_seed)
        traj = run.get('trajectory') or []
        reach = sum(1 for r in rs['runs'] if r.get('metrics', {}).get('G') == m['G'])
        side = f.parent / 'summary.json'
        s = {'mechanism': 'gate kernel convergence run (cli.py flow --config gate) under the start\'s own caps (main-track queue, campaigns: ~/xs-campaigns/2026-11-13-aes/main/queue.py)',
             'mech_short': 'flow', 'command': rs['command'].replace(HOME, '~'), 'run_record': tilde(f.parent),
             'parents': [{'file': tilde(rs['start'])}], 'start': tilde(rs['start']), 'objective': rs['objective'],
             'caps': rs['caps'], 'seeds': [best_seed], 'iters': None, 'rounds': None,
             'time_to_result_s': {'within_job_s': traj[-1][0] if traj else None, 'job_budget_s': rs['workflow']['seconds']},
             'code_sha256_12': rs['code_sha256_12'], 'code_version': {'snapshot': tilde(rs['code_snapshot'])},
             'reproduction': 'one-off: %d of %d seeds reached G %d (time-budgeted, not bit-reproducible)' % (reach, len(rs['seeds']), m['G'])}
    else:
        raise ValueError('no provenance rule for %s' % f)
    s['campaign_sidecar_src'] = side if side and Path(side).exists() else None
    return s


def main():
    dry = '--dry-run' in sys.argv
    pub = AC.published()
    cands = BT.candidates()
    seen, per_track = {}, {}
    for f in cands:
        try:
            c = load_circuit(f); m = c.metrics(MODEL)
        except Exception:
            continue
        t = (m['A'], m['AD'], m['G'], m['GD'])
        seen.setdefault(t, (f, c, m))
        k = core.to_kernel(c)
        per_track.setdefault((t, track_of(f)), {}).setdefault(k, (f, c, m))
    new = {t for t in seen if not any(BT.le(u, t) for u, _ in pub)}
    pareto = {t for t in new if not any(u != t and BT.le(u, t) for u in new)}
    have = set()
    for f in RES.glob('*.circ.txt'):
        m = core.read_ncff(str(f)).metrics(MODEL)
        have.add((m['A'], m['AD'], m['G'], m['GD']))
    pick = []
    for (t, tr), circs in sorted(per_track.items()):
        if t not in pareto or tr == 'results' or t in have:
            continue
        pick.append(next(iter(circs.values())))         # first circuit of that track at t
    now = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    print('%d Pareto tuples (best_table rule), %d already in results/aes, %d circuits to add' % (len(pareto), len(pareto & have), len(pick)))
    for f, c, m in sorted(pick, key=lambda x: (x[2]['GD'], x[2]['G'])):
        s = describe(f, m)
        tr = track_of(f)
        caps = s.get('caps') or {}
        if any(v is not None and m[k] > v for k, v in caps.items()):
            # e.g. a polish under cap A31 that stayed at A32: a valid circuit, but not of that job's caps
            s['job_caps'] = caps
            s['caps'] = {'GD': None, 'AD': None, 'A': None}
            s['note'] = 'the job did not meet its caps (job_caps); the circuit is recorded without caps'
        base = 'aes-nist-%s-%s-g%d-a%d-gd%d-ad%d' % (tr, s.pop('mech_short'), m['G'], m['A'], m['GD'], m['AD'])
        dst = RES / (base + '.circ.txt')
        print('  %-48s <- %s' % (dst.name, tilde(f)))
        if dry:
            continue
        side = s.pop('campaign_sidecar_src')
        c.name = base
        c.in_names = ['x%d' % i for i in range(8)]; c.out_names = ['y%d' % i for i in range(8)]
        dst.write_text(core.write_ncff(c, MODEL, comments=[
            'BoolFlux AES S-box result (NIST accounting: AND, XOR, XNOR, NOT written as XNOR t a 0, each 1)',
            'curated %s from %s (sha256 %s)' % (now, tilde(f), file_sha(f)), 'mechanism: %s' % s['mechanism']]), encoding='utf-8')
        r = AC.check(dst)
        if not r['ok'] or tuple(r['tuple']) != (m['A'], m['AD'], m['G'], m['GD']):
            dst.unlink()
            raise SystemExit('verification failed for %s: %s' % (f, r.get('errors')))
        summ = {'target': 'aes', 'target_description': 'AES S-box, FIPS-197 (computed: inversion mod 0x11B, affine 0x63)',
                'model': 'nist', 'track': tr, 'campaign_source': {'file': tilde(f), 'sha256': file_sha(f)},
                'curated_utc': now, 'wall_s': None,
                'best': {'job': tilde(f), 'seed': (s.get('seeds') or [None])[0],
                         'metrics': {k: m[k] for k in ('cost', 'G', 'A', 'GD', 'AD')}},
                'code_sha256_12': s.pop('code_sha256_12', None)}
        summ.update(s)
        if side:
            shutil.copy(side, RES / (base + '.campaign.json'))
            summ['campaign_sidecar'] = base + '.campaign.json'
        (RES / (base + '.summary.json')).write_text(json.dumps(summ, indent=1, default=str) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
