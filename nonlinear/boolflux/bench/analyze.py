"""Tables from benchmark run files (bench.py output).

    python3 nonlinear/boolflux/bench/analyze.py RUNDIR [RUNDIR ...] > tables.md

Targets were fixed before the runs (TARGETS below).  Success = the final verified circuit meets the
target; time to target = first trajectory point that meets it (wall seconds since the search
started; overhead for start construction is reported separately).
"""
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

# label prefix -> (description, predicate on a metrics dict, ...)
LIN_BEST = {('joltik', '4'): 44, ('joltik', 'none'): 42, ('small-scale-aes', '4'): 44,
            ('small-scale-aes', 'none'): 42, ('klsw17-m-4x4-gf16', '4'): 36, ('klsw17-m-4x4-gf16', 'none'): 32}
NL = {'present': ('BGC <= 14 (best published)', lambda m: m['cost'] <= 14),
      'rectangle': ('BGC <= 12 (best published)', lambda m: m['cost'] <= 12),
      'ascon': ('BGC <= 16 (best published)', lambda m: m['cost'] <= 16),
      'prince': ('BGC <= 16 (best published)', lambda m: m['cost'] <= 16),
      'gf16-mul': ('A <= 9 (bilinear complexity)', lambda m: m['A'] <= 9),
      'aes-anf': ('G <= 600', lambda m: m['G'] <= 600),
      'aes-a36g142': ('G <= 132 (below every published circuit within A36 AD4 GD13)', lambda m: m['G'] <= 132),
      'aes-gd14repair': ('GD <= 14 and G <= 126 (below published 127)', lambda m: m['GD'] <= 14 and m['G'] <= 126),
      'aes-g104': ('G <= 103', lambda m: m['G'] <= 103)}
CHECKPOINTS = [1, 5, 15, 30, 60, 120, 300]


def load(dirs):
    runs = []
    for d in dirs:
        for f in sorted(Path(d).glob('*.json')):
            r = json.loads(f.read_text()); r['_file'] = str(f); runs.append(r)
    return runs


def traj_metrics(row):
    return {'cost': row[1], 'G': row[2], 'A': row[3], 'GD': row[4], 'AD': row[5]}


def first_time(r, pred):
    for row in r['trajectory']:
        m = traj_metrics(row)
        caps = r['run'].get('caps') or {}
        if all(c is None or m[k] <= c for k, c in caps.items()) and pred(m):
            return row[0]
    return None


def best_at(r, t, key='cost'):
    caps = r['run'].get('caps') or {}
    best = None
    for row in r['trajectory']:
        if row[0] > t: break
        m = traj_metrics(row)
        if all(c is None or m[k] <= c for k, c in caps.items()):
            best = m[key] if best is None else min(best, m[key])
    return best


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(st.median(xs), 1) if xs else '-'


def fmt_t(xs, n):
    ok = [x for x in xs if x is not None]
    return '%d/%d, median %s s' % (len(ok), n, round(st.median(ok), 1) if ok else '-')


def linear(runs):
    print('## Linear maps: XORFlux v8 vs XOR-only BoolFlux (same start, same CPU, 120 s each)\n')
    print('Target = the repository\'s best known circuit at that cap (XORFlux records, hours of search).\n')
    print('| map | cap | start | tool | final G (median, best, worst) | reach best known | reach best+2 | best-so-far median at 5/15/60/120 s | peak RSS MB | start-up s |')
    print('|---|---|---|---|---|---|---|---|---|---|')
    groups = defaultdict(list)
    for r in runs:
        lab = r['run']['label']
        if not lab.startswith('L-'): continue
        import re
        mm = re.match(r'^L-(.+)-c(4|none)-(naive|nist)-s(\d+)-(xorflux|boolflux-v\d+)$', lab)
        mp, cap, start, tool = mm.group(1), mm.group(2), mm.group(3), mm.group(5)
        groups[(mp, cap, start, tool)].append(r)
    for (mp, cap, start, tool), rs in sorted(groups.items()):
        tgt = LIN_BEST[(mp, cap)]
        fin = [r['final']['G'] for r in rs if r.get('final') and r.get('verified')]
        bad = [r for r in rs if not r.get('verified')]
        t1 = [first_time(r, lambda m: m['G'] <= tgt) for r in rs]
        t2 = [first_time(r, lambda m: m['G'] <= tgt + 2) for r in rs]
        curve = '/'.join(str(med([best_at(r, t, 'G') for r in rs])) for t in (5, 15, 60, 120))
        ov = [r['overhead'].get('xorflux_startup_s', r['overhead'].get('kernel_startup_s', 0)) + r['overhead'].get('start_s', 0) for r in rs]
        print('| %s | %s | %s | %s | %s, %s, %s%s | %s | %s | %s | %s | %s |' % (
            mp, cap, start, tool, med(fin), min(fin) if fin else '-', max(fin) if fin else '-',
            (' (%d unverified/failed)' % len(bad)) if bad else '', fmt_t(t1, len(rs)), fmt_t(t2, len(rs)), curve,
            med([r['peak_rss_kb'] / 1024 for r in rs]), med(ov)))
    print()


def nonlinear(runs, prefix, title):
    print('## %s\n' % title)
    print('| target | config | runs | target | final cost/G (median, best) | A median | reach target | best-so-far median at checkpoints | overhead s (start, skel, synth) | peak RSS MB |')
    print('|---|---|---|---|---|---|---|---|---|---|')
    groups = defaultdict(list)
    for r in runs:
        lab = r['run']['label']
        if not lab.startswith(prefix + '-'): continue
        import re
        body = re.sub(r'-s\d+-v\d+$', '', lab[len(prefix) + 1:])
        names = sorted(list(NL) + ['aes'], key=len, reverse=True)
        tgt = next(t for t in names if body.startswith(t + '-')); cfg = body[len(tgt) + 1:]
        groups[(tgt, cfg, lab.rsplit('-', 1)[1])].append(r)
    if prefix == 'A':
        print('(an unverified run = no circuit within the caps by the end of the budget)\n')
    for (tgt, cfg, ver), rs in sorted(groups.items()):
        key = tgt if tgt in NL else ('aes-a36g142' if tgt == 'aes' else tgt)
        desc, pred = NL[key]
        fin = [r['final'] for r in rs if r.get('final') and r.get('verified')]
        secs = rs[0]['run']['seconds']
        cps = [t for t in CHECKPOINTS if t <= secs]
        curve = ' / '.join('%ss:%s' % (t, med([best_at(r, t) for r in rs])) for t in cps)
        tt = [first_time(r, pred) for r in rs]
        ov = '%s, %s, %s' % (med([r['overhead'].get('start_s') for r in rs]), med([r['overhead'].get('skel_s') for r in rs]),
                             med([r['overhead'].get('synth_s') for r in rs]))
        errs = [r for r in rs if r.get('error') or not r.get('verified')]
        print('| %s | %s %s | %d%s | %s | %s, %s | %s | %s | %s | %s | %s |' % (
            tgt, cfg, ver, len(rs), (' (%d failed)' % len(errs)) if errs else '', desc,
            med([m['cost'] for m in fin]), min([m['cost'] for m in fin]) if fin else '-', med([m['A'] for m in fin]),
            fmt_t(tt, len(rs)), curve, ov, med([r['peak_rss_kb'] / 1024 for r in rs])))
    print()


def main():
    runs = load(sys.argv[1:])
    errs = [r for r in runs if r.get('error')]
    print('%d runs, %d with errors, %d verified\n' % (len(runs), len(errs), sum(1 for r in runs if r.get('verified'))))
    for r in errs[:10]: print('- error in %s: %s' % (r['run']['label'], r['error'][:200]))
    linear(runs)
    nonlinear(runs, 'N', 'Small nonlinear targets from naive ANF starts (60 s each)')
    nonlinear(runs, 'A', 'AES S-box (NIST model)')
    nonlinear(runs, 'X', 'Gate-kernel ablations (gate config, one mechanism off)')
    nonlinear(runs, 'F', 'Skeleton-level ablations (full config)')


if __name__ == '__main__':
    main()
