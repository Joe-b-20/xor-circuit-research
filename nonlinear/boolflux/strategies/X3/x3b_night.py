#!/usr/bin/env python3
"""X3b overnight driver: stage-1-free window re-solve of 9+5+14 (and other three-stage A28) circuits.
    python3 x3b_night.py SHARD NSHARDS [--kmax 5] [--ov] [--maxwin N] [--files GLOB ...]
For every file (sorted; file i belongs to shard i % NSHARDS): minimal slack windows W (k <= kmax top products
whose removal leaves d_b <= k - 1 missing output dims with stage 1 free, x3b_dropk.py), then x3b_cand3.py
(O2 = span(1, x, N, n, middle); every operand l, all m; exact U' per completion; 9/10-cover; any completion
with predicted total <= 27 is BUILT with G build_tables and aes_check'ed into strategies/X3/found/ + sidecar).
With --ov the d = 1 windows are also run with OV = aff(x) + all functions of N (2^24 l, ~15 min each).
Log: ~/xs-campaigns/2026-11-15-study/X3/night/shard<SHARD>.log (one block per window);
success = a line 'BUILT ... OK' with A <= 27 (grep BUILT)."""
import ast, glob, subprocess, sys, time
from pathlib import Path
S = Path.home() / 'xcr-boolflux/nonlinear/boolflux/strategies'
a = sys.argv[1:]
shard, nsh = int(a[0]), int(a[1])
def opt(name, d): return type(d)(a[a.index(name) + 1]) if name in a else d
kmax = opt('--kmax', 5); maxwin = opt('--maxwin', 1000); ov = '--ov' in a
if '--files' in a:
    files = sorted(sum((glob.glob(g) for g in a[a.index('--files') + 1:]), []))
else:
    files = sorted(glob.glob(str(S / 'H2/found/h2-*-a28.circ.txt')) +
                   glob.glob(str(Path.home() / 'xs-campaigns/2026-11-15-study/X1/x1b/*/found/aes-sbox-a28-*.circ.txt')))
out = Path.home() / 'xs-campaigns/2026-11-15-study/X3' / opt('--tag', 'night'); out.mkdir(parents=True, exist_ok=True)
log = open(out / ('shard%d.log' % shard), 'a')
def say(s):
    log.write(s + '\n'); log.flush(); print(s, flush=True)
say('== X3b night shard %d/%d start %s, %d files total' % (shard, nsh, time.strftime('%H:%M:%S UTC', time.gmtime()), len(files)))
cwd = str(Path.home() / 'xcr-boolflux/nonlinear/boolflux')
for i, f in enumerate(files):
    if i % nsh != shard: continue
    r = subprocess.run([sys.executable, str(S / 'X3/x3b_dropk.py'), f, str(kmax), 'min'], capture_output=True, text=True, cwd=cwd)
    wins = []
    for ln in r.stdout.splitlines():
        if 'minimal slack windows' in ln:
            wins += ast.literal_eval(ln.split(':', 1)[1].strip())
    say('# %s: %d minimal slack windows %s' % (Path(f).name, len(wins), wins[:20]))
    for W, d in wins[:maxwin]:
        runs = ['O2'] + (['OV'] if ov and d == 1 else [])
        for O in runs:
            t0 = time.time()
            try:
                rr = subprocess.run([sys.executable, str(S / 'X3/x3b_cand3.py'), f, ','.join(map(str, W)), O, '20', '3000000'],
                                    capture_output=True, text=True, cwd=cwd, timeout=3600)
                body = rr.stdout + (rr.stderr[-400:] if rr.returncode else '')
            except subprocess.TimeoutExpired:
                body = 'TIMEOUT 3600 s'
            say('## %s W=%s d=%d O=%s (%.0f s)\n%s' % (Path(f).name, W, d, O, time.time() - t0, body.strip()))
say('== shard %d done %s' % (shard, time.strftime('%H:%M:%S UTC', time.gmtime())))
