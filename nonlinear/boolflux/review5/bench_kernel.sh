#!/bin/bash
# bench_kernel.sh -- clean speed measurement of the gate kernel (review 5, agent C1).
#
#   bash nonlinear/boolflux/review5/bench_kernel.sh            (from anywhere inside the worktree)
#   CPUS="0 1 2 3 4 5 6 7" ITERS=20000 REPS=3 bash .../bench_kernel.sh
#
# Compares kernel/bfx.c of f9fe6f7 (before review 5) with every later commit that touched it, on
# fixed AES workloads with fixed seeds and a fixed iteration count (no wall-clock dependence), so
# the search trajectory can be compared exactly.  Each (workload, seed) group is pinned with taskset
# to one CPU of $CPUS and runs all builds there, interleaved, REPS times; the table reports the
# minimum user CPU time per build.  Groups run in parallel, one per CPU (8 groups).
# Default settings need about 3-5 minutes on 8 idle CPUs (hard limit: MAXMIN minutes, default 12;
# on reaching it the remaining runs are skipped and the table says so).
# Memory: each kernel process uses < 100 MB.  Result: review5/bench_kernel_results.md (overwritten).
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
exec python3 - "$HERE" <<'PY'
import hashlib, os, re, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(sys.argv[1]); PKG = HERE.parent; REPO = PKG.parents[1]
sys.path.insert(0, str(PKG.parent))
from boolflux import core, objective            # noqa: E402

CPUS = os.environ.get('CPUS', '0 1 2 3 4 5 6 7').split()
ITERS = int(os.environ.get('ITERS', 20000)); REPS = int(os.environ.get('REPS', 3))
MAXMIN = float(os.environ.get('MAXMIN', 12)); BASE = os.environ.get('BASE', 'f9fe6f7')
T_START = time.time()
git = lambda *a: subprocess.run(['git', '-C', str(REPO)] + list(a), capture_output=True, text=True, check=True).stdout
KPATH = 'nonlinear/boolflux/kernel/bfx.c'
commits = [BASE] + git('log', '--reverse', '--format=%h', BASE + '..HEAD', '--', KPATH).split()
wd = Path(tempfile.mkdtemp(prefix='bench-kernel-'))
bins = {}
for c in commits:
    src = wd / ('bfx-%s.c' % c); src.write_text(git('show', '%s:%s' % (c, KPATH)))
    subprocess.run(['gcc', '-O3', '-march=native', '-o', str(wd / ('bfx-' + c)), str(src), '-lm'], check=True)   # the hub's flags
    bins[c] = wd / ('bfx-' + c)
subject = {c: git('log', '-1', '--format=%s', c).strip()[:70] for c in commits}

KD = {'T0': 0.6, 'Tperiod_it': 20000, 'stall_it': 60000, 'uphill': 1.0, 'max_excess': 8,
      'mv.resub1': 1, 'mv.resub2': 2, 'mv.resub3': 1, 'dmax': 220, 'pdiv': 90,
      'nl_samples': 12, 'cand_cap': 40, 'fraig': 1}                     # hub polish defaults
NIST = REPO / 'nonlinear' / 'nist' / 'aes-sbox'
WL = {  # name: (start, objective, caps)
    'polish-a29 (a,ad,cost,gd; caps A29 AD5)': ('aes-sbox-a29-ad5-g137-gd32-xx108-22.circ.txt', 'a,ad,cost,gd', {'cap.a': 29, 'cap.ad': 5}),
    'cost-a32 (cost,gd; no caps)': ('aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt', 'cost,gd', {}),
    'descend-a29 (caps A29 AD5 GD20 from G182)': ('aes-sbox-a29-ad5-g182-gd16-xx153-29.circ.txt', 'a,ad,cost,gd', {'cap.a': 29, 'cap.ad': 5, 'cap.gd': 20}),
    'repair-a32 (cap GD24 from GD30)': ('aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt', 'a,ad,cost,gd', {'cap.a': 32, 'cap.ad': 5, 'cap.gd': 24}),
}
SEEDS = (1, 2)


def group(args):
    (wname, (start, obj, caps)), seed, cpu = args
    g = wd / ('g-%s-%d' % (hashlib.md5(wname.encode()).hexdigest()[:6], seed)); g.mkdir()
    (g / 'in.bfx').write_text(core.to_kernel(core.read_ncff(str(NIST / start))))
    cfg = dict(KD); cfg.update(objective.weights(obj)); cfg.update(caps)
    for op in (8, 6, 9, 3): cfg['cost.%d' % op] = 1
    res = {c: {'t': [], 'traj': None, 'final': ''} for c in commits}
    skipped = 0
    for rep in range(REPS):
        for c in commits:
            if time.time() - T_START > (MAXMIN - 1.5) * 60: skipped += 1; continue
            cfg.update({'in': g / 'in.bfx', 'out': g / ('out-%s.bfx' % c), 'seed': seed, 'iters': ITERS, 'seconds': 100000})
            (g / 'k.cfg').write_text(''.join('%s %s\n' % kv for kv in cfg.items()))
            p = subprocess.run(['/usr/bin/time', '-f', '%U', '-o', str(g / 'time.txt'), 'taskset', '-c', cpu, str(bins[c]), str(g / 'k.cfg')],
                               capture_output=True, text=True)
            out, err = p.stdout, p.stderr
            if p.returncode: res[c]['final'] = 'FAILED rc %d %s' % (p.returncode, err[-100:]); continue
            ft = [x for x in out.splitlines() if x.startswith('final')][0]
            secs = float((g / 'time.txt').read_text().split()[-1])        # user CPU seconds of the kernel process
            res[c]['t'].append(secs)
            traj = re.sub(r' (t|seconds|time) [0-9.]+', '', '\n'.join(x for x in out.splitlines() if x.startswith(('best', 'final', 'move ', 'noop_'))))
            body = '\n'.join(x for x in (g / ('out-%s.bfx' % c)).read_text().splitlines() if not x.startswith('#'))
            res[c]['traj'] = hashlib.md5((traj + body).encode()).hexdigest()[:10]
            res[c]['final'] = ' '.join(ft.split()[3:11])
    return wname, seed, cpu, res, skipped


jobs = [(w, s) for w in WL.items() for s in SEEDS]
jobs = [(w, s, CPUS[i % len(CPUS)]) for i, (w, s) in enumerate(jobs)]
with ThreadPoolExecutor(max_workers=len(CPUS)) as ex:
    results = list(ex.map(group, jobs))

L = ['# Gate kernel speed: %s vs the review-5 commits' % BASE, '',
     'Written by `review5/bench_kernel.sh` on %s UTC.  %d iterations per run, seeds %s, %d repetitions (minimum taken), '
     'gcc -O3 -march=native, one CPU per (workload, seed) group: CPUs %s.  Time = user CPU seconds of the kernel '
     'process (/usr/bin/time); load on the same core or its hyperthread still inflates it, so use idle CPUs.  '
     '"same" = best/final/move lines and the result circuit are identical to %s.' %
     (time.strftime('%Y-%m-%d %H:%M', time.gmtime()), ITERS, ','.join(map(str, SEEDS)), REPS, ' '.join(CPUS), BASE), '',
     '| commit | subject |', '|---|---|'] + ['| %s | %s |' % (c, subject[c]) for c in commits] + ['']
L += ['| workload | seed | ' + ' | '.join('%s s' % c for c in commits) + ' | ' + ' | '.join('%s/%s' % (c, BASE) for c in commits[1:]) + ' | trajectories | final (%s) |' % commits[-1],
      '|---|---|' + '---|' * (2 * len(commits) + 1)]
tot = {c: 0.0 for c in commits}; ok = True; nskip = 0
for wname, seed, cpu, res, skipped in results:
    nskip += skipped
    mins = {c: (min(res[c]['t']) if res[c]['t'] else float('nan')) for c in commits}
    for c in commits: tot[c] += mins[c]
    same = ['same' if res[c]['traj'] == res[BASE]['traj'] else 'DIFFERENT' for c in commits[1:]]
    ok &= all(x == 'same' for x in same)
    L.append('| %s | %d | ' % (wname, seed) + ' | '.join('%.2f' % mins[c] for c in commits) + ' | ' +
             ' | '.join('%.3f' % (mins[c] / mins[BASE]) for c in commits[1:]) + ' | ' + ' '.join(same) + ' | ' + res[commits[-1]]['final'] + ' |')
L.append('| **total** | | ' + ' | '.join('%.2f' % tot[c] for c in commits) + ' | ' + ' | '.join('**%.3f**' % (tot[c] / tot[BASE]) for c in commits[1:]) + ' | %s | |' % ('all same' if ok else 'SEE ROWS'))
L += ['', 'Total wall time of this benchmark: %.0f s.%s' % (time.time() - T_START, '  %d runs skipped at the time limit.' % nskip if nskip else '')]
(HERE / 'bench_kernel_results.md').write_text('\n'.join(L) + '\n')
print('\n'.join(L))
PY
