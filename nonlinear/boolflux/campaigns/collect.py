"""Collect verified campaign results into nonlinear/boolflux/results/ and print ledger rows.

    python3 nonlinear/boolflux/campaigns/collect.py RUN_DIR [RUN_DIR ...] [--copy]

For every RUN_DIR/summary.json (searched recursively), re-verify the best circuit with both
verifiers (cli.verify_file), and print one markdown row: target, model, objective, caps, start,
start metrics, result (G, counts by type, A, GD, AD, cost), wall time, CPU time (sum of job wall
times), seeds, iterations.  With --copy the circuit is copied to
results/<target>/<target>-<model>-<objective>-<caps>-g<G>-a<A>-gd<GD>-ad<AD>.circ.txt and its
summary next to it (.summary.json); an existing results file with that name and another content
is never overwritten (the row says so).  "Improved" = the result ranks before the start under the
run's objective and caps (objective.rank: feasible first, then cap excess, then the keys in order).
"""
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
sys.path.insert(0, str(PKG.parent))
sys.path.insert(0, str(PKG))
import cli   # noqa: E402
from boolflux import objective   # noqa: E402


def caps_str(c):
    return ','.join('%s<=%s' % (k, v) for k, v in c.items() if v is not None) or '-'


def counts_str(c):
    return ' '.join('%s %d' % kv for kv in c.items())


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    unknown = [a for a in sys.argv[1:] if a.startswith('-') and a != '--copy']
    if unknown or not args:
        print(__doc__.strip())
        return 0 if set(unknown) <= {'-h', '--help'} and unknown else 2
    copy = '--copy' in sys.argv
    rows = []
    for d in args:
        for sj in sorted(Path(d).rglob('summary.json')):
            if 'results' in sj.parts: continue
            s = json.loads(sj.read_text())
            b = s['best']
            caps = {k: v for k, v in s['caps'].items()}
            v = cli.verify_file(b['file'], s['target'], s['model'], caps)
            m = v['metrics']; sm = s['start_metrics']
            feas = all(c is None or m[k] <= c for k, c in caps.items())
            ok = v['core_ok'] and v['independent_ok'] and v['library_ok'] and feas
            # review5 P15: the same ranking as everything else (the weighted sum with weights
            # 1, 1e-4, 1e-8 lets a later key outvote an earlier one when it differs by >= 10^4)
            improved = ok and (not objective.feasible(sm, caps) or
                               objective.rank(m, caps, s['objective'])[3:] < objective.rank(sm, caps, s['objective'])[3:])
            cpu = sum(r.get('wall_s', 0) for r in s['runs'])
            start = Path(s['start']).name.replace('.circ.txt', '') if s['start'] != 'anf' else 'ANF (naive)'
            row = {'target': s['target'], 'model': s['model'], 'objective': s['objective'],
                   'caps': caps_str(s['caps']), 'start': start,
                   'start_metrics': '%g (A%d GD%d AD%d)' % (sm['cost'], sm['A'], sm['GD'], sm['AD']),
                   'result': '%g (A%d GD%d AD%d)' % (m['cost'], m['A'], m['GD'], m['AD']),
                   'G': m['G'], 'counts': counts_str(m['counts']), 'verified': ok, 'improved': improved,
                   'wall_s': s.get('wall_s'), 'cpu_s': round(cpu, 1), 'seeds': '%d-%d' % (min(s['seeds']), max(s['seeds'])),
                   'iters': s['iters'], 'rounds': s.get('rounds', 1), 'command': s['command'], 'dir': str(sj.parent)}
            rows.append(row)
            if copy and improved:
                dest = PKG / 'results' / s['target']
                dest.mkdir(parents=True, exist_ok=True)
                cp = ('-'.join(('%s%s' % (k.lower(), v)) for k, v in s['caps'].items() if v is not None) or 'nocap')
                nm = '%s-%s-%s-%s-g%d-a%d-gd%d-ad%d' % (s['target'], s['model'], s['objective'].replace(',', '_'),
                                                        cp, m['G'], m['A'], m['GD'], m['AD'])
                tgt = dest / (nm + '.circ.txt')
                if tgt.exists() and tgt.read_bytes() != Path(b['file']).read_bytes():
                    row['file'] = 'NOT COPIED: %s exists with another circuit' % tgt.name
                    print('NOT COPIED: %s exists with another content (from %s)' % (tgt, b['file']), file=sys.stderr)
                    continue
                shutil.copy(b['file'], tgt)
                slim = {k: s[k] for k in s if k != 'runs'}
                slim['jobs'] = [{k: r.get(k) for k in ('tag', 'seed', 'kernel_seed', 'metrics', 'wall_s', 'final', 'skel')}
                                for r in s['runs']]
                (dest / (nm + '.summary.json')).write_text(json.dumps(slim, indent=1, default=str) + '\n', encoding='utf-8')
                row['file'] = str((dest / (nm + '.circ.txt')).relative_to(PKG.parents[1]))
    print('| target | model | objective | caps | start | start | result | gates by type | verified | wall s | CPU s | seeds x iters x rounds |')
    print('|---|---|---|---|---|---|---|---|---|---|---|---|')
    for r in rows:
        print('| %s | %s | %s | %s | %s | %s | **%s** | %s | %s | %s | %s | %s x %s x %s |' % (
            r['target'], r['model'], r['objective'], r['caps'], r['start'], r['start_metrics'], r['result'],
            r['counts'], ('both' if r['verified'] else 'NO (function, library, metrics or caps)') + ('' if r['improved'] else ', no gain'), r['wall_s'], r['cpu_s'], r['seeds'], r['iters'], r['rounds']))



if __name__ == '__main__':
    sys.exit(main())
