"""export.py FUNCTION RUN_DIR ID... : copy verified circuits of an A/B arm to found/ with their records.
For each id: NCFF file (msb/msb), aes_check (core + independent verifier, all 256 inputs), circuits/check.py
(the repository's own checker: gate list and AND skeleton truth tables), lineage (join parents with their source
files, cut level, every kernel job dir of that candidate: start.bfx, kernel.cfg, kernel.log, bests), the arm's
events of that lineage, and a run record (boolflux.runlog RunLog, kind ops.planexec-export) with git state and diff."""
import json, os, shutil, subprocess, sys, pickle
from pathlib import Path
fn, run = sys.argv[1], Path(sys.argv[2]); ids = sys.argv[3:]
os.environ['BOOLFLUX_FUNCTION'] = fn
sys.path.insert(0, os.path.expanduser('~/xcr-idea-03/search/nonlinear'))
from boolflux import core, runlog
from boolflux.hub.common import metrics, verify, MODEL
D = Path(os.path.expanduser('~/xs-campaigns/2026-11-17-ideas/03'))
REPO = Path(os.path.expanduser('~/xcr-idea-03'))
ev = [json.loads(l) for l in open(run / 'events.jsonl')]
start = [e for e in ev if e['ev'] == 'start'][0]
pool = pickle.load(open(start['args']['pool'], 'rb'))
byid = {T.id: T for T in pool}
for i in ids:
    c = core.from_kernel((run / 'circuits' / (i + '.bfx')).read_text())
    m = metrics(c)
    e = [x for x in ev if x['ev'] == 'circuit' and x['id'] == i][0]
    src = e['src']
    name = '%s-a%d-ad%d-g%d-gd%d-%s' % (fn, m[0], m[1], m[2], m[3], i)
    out = D / 'found' / name; out.mkdir(parents=True, exist_ok=True)
    txt = core.write_ncff(c, MODEL, comments=['planned join (idea 03, stageplan/planexec): front %s, back %s above AND level %s; %s' % (src['X'], src['Y'], src['LY'], src.get('kind')),
                                               'then kernel %s; arm %s, run %s' % (e['how'], src['arm'], run)])
    (out / (name + '.circ.txt')).write_text(txt)
    ok, info = verify(c)
    chk = subprocess.run([sys.executable, str(REPO / 'circuits' / 'check.py'), str(out / (name + '.circ.txt'))], capture_output=True, text=True)
    ac = subprocess.run([sys.executable, str(REPO / 'search/nonlinear/boolflux/aes_check.py'), '--function', fn, str(out / (name + '.circ.txt'))],
                        capture_output=True, text=True)
    # lineage: the parents and every kernel job of this candidate (same src)
    lin = out / 'lineage'; lin.mkdir(exist_ok=True)
    for role in ('X', 'Y'):
        T = byid.get(src[role])
        if T is not None:
            (lin / ('%s-%s.bfx' % (role, src[role].replace('@', '_')))).write_text(core.to_kernel(T.c))
    same = [x for x in ev if x.get('src') == src]
    kdirs = sorted((run / 'k').glob('*'))
    kj = [x for x in same if x['ev'] == 'kernel']
    for k in kdirs:
        cfg = (k / 'kernel.cfg').read_text() if (k / 'kernel.cfg').exists() else ''
        if any(('seed %d' % x['seed']) in cfg for x in kj):
            shutil.copytree(k, lin / k.name, dirs_exist_ok=True)
    with open(lin / 'events.jsonl', 'w') as f:
        for x in same: f.write(json.dumps(x) + '\n')
    log = runlog.RunLog(str(out), 'ops.planexec-export', argv=sys.argv, seeds={'arm_seed': start['args']['seed'], 'kernel_seeds': [x['seed'] for x in kj]},
                        config={'arm': start['args'], 'src': src}, function=fn)
    log.add_start(str(lin / ('X-%s.bfx' % src['X'].replace('@', '_'))), label='join front')
    log.add_start(str(lin / ('Y-%s.bfx' % src['Y'].replace('@', '_'))), label='join back')
    log.finish('ok', best=list(m))
    (out / 'checks.txt').write_text('hub verify: %s %s\ncircuits/check.py rc %d\n%s%s\naes_check rc %d\n%s%s\n' % (ok, info, chk.returncode, chk.stdout, chk.stderr, ac.returncode, ac.stdout, ac.stderr))
    print(name, 'verify', ok, 'check.py rc', chk.returncode, 'aes_check rc', ac.returncode, chk.stdout.strip().splitlines()[-1:] if chk.stdout else '')
