#!/usr/bin/env python3
"""Screen new-AND-space A28 builds (H2 / X1b): per circuit two chained 120 s kernel runs, caps A 28 only
(AD, GD free), objective a,cost,gd; best result verified, aes_check'ed and saved to T1/found/newspace/
with a JSON sidecar.  Processes the given files, then keeps watching LISTFILE (one path per line,
appended by H2) until HOURS are over.

    python3 screen.py OUTDIR HOURS LISTFILE FILE...
Log: OUTDIR/screen.jsonl (one line per circuit: start metrics, after run 1, after run 2, saved file).
"""
import hashlib, json, random, subprocess, sys, time
from pathlib import Path
PKG = Path('/home/joebachir20/xcr-boolflux/nonlinear/boolflux')
sys.path.insert(0, str(PKG.parent))
from boolflux.hub import ops as HO                       # noqa: E402
from boolflux.hub.common import core, metrics, verify, code_version, MODEL   # noqa: E402

out = Path(sys.argv[1]); hours = float(sys.argv[2]); listfile = Path(sys.argv[3]); files = sys.argv[4:]
FOUND = Path('/home/joebachir20/xs-campaigns/2026-11-15-study/T1/found/newspace'); FOUND.mkdir(parents=True, exist_ok=True)
out.mkdir(parents=True, exist_ok=True)
log = open(out / 'screen.jsonl', 'a'); VER = code_version(); rng = random.Random(7)
END = time.time() + hours * 3600
done = set()
import os
for sk in filter(None, os.environ.get('SCREEN_SKIP', '').split(':')):     # screen.jsonl files of earlier runs
    try:
        for ln in open(sk):
            r = json.loads(ln)
            if r.get('file'): done.add(r['file'])
    except Exception: pass


def emit(d):
    d['t'] = round(time.time(), 1); log.write(json.dumps(d, default=str) + '\n'); log.flush()


def load(p):
    p = Path(p)
    return core.from_kernel(p.read_text(), p.stem) if p.suffix == '.bfx' else core.read_ncff(str(p))


def screen(path):
    try: c = load(path)
    except Exception as ex: emit({'file': path, 'error': repr(ex)}); return
    ok, info = verify(c)
    m0 = metrics(c)
    if not ok or m0[0] > 28: emit({'file': path, 'm': m0, 'skip': 'verify failed or A > 28', 'info': info}); return
    best = c; runs = []
    for r in range(2):
        d = out / 'job'; d.mkdir(exist_ok=True)
        cs, ki = HO._kernel(best, {'A': 28, 'AD': None, 'GD': None}, 'a,cost,gd', rng.randrange(1 << 30), 120, d, str(out))
        x = cs[0] if cs else None
        if x is not None:
            mx = metrics(x); runs.append(mx)
            if mx[0] <= 28 and (mx[2], mx[3]) < (metrics(best)[2], metrics(best)[3]) and verify(x)[0]: best = x
    mb = metrics(best)
    h = hashlib.sha1(core.to_kernel(best).encode()).hexdigest()[:12]
    name = 'aes-sbox-a%d-ad%d-g%d-gd%d-%s-%s' % (mb + (Path(path).name.split('.')[0][-24:], h))
    (FOUND / (name + '.bfx')).write_text(core.to_kernel(best)); (FOUND / (name + '.circ.txt')).write_text(core.write_ncff(best, MODEL))
    rc = subprocess.run([sys.executable, str(PKG / 'campaigns' / 'aes_check.py'), str(FOUND / (name + '.bfx'))], capture_output=True, text=True)
    json.dump({'source': str(path), 'source_metrics': m0, 'runs': runs, 'metrics': mb, 'how': 'screen.py: 2 chained 120 s kernel runs, caps A 28, AD/GD free, objective a,cost,gd',
               'code_version': VER, 'time_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'aes_check_rc': rc.returncode,
               'aes_check_out': rc.stdout[-1500:]}, open(FOUND / (name + '.json'), 'w'), indent=1, default=str)
    emit({'file': path, 'm0': m0, 'runs': runs, 'best': mb, 'saved': name, 'aes_check_rc': rc.returncode})


queue = [f for f in files if f not in done]
while time.time() < END - 260:
    if listfile.exists():
        for ln in listfile.read_text().splitlines():
            ln = ln.strip()
            if ln and not ln.startswith('#') and ln not in done and ln not in queue: queue.append(ln)
    if not queue:
        time.sleep(30); continue
    p = queue.pop(0); done.add(p)
    screen(p)
emit({'event': 'end'})
