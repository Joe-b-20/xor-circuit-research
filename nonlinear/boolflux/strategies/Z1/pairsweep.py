#!/usr/bin/env python3
"""Exact pair -> 1 AND sweep over distinct-span A28 layers with a parallel last-layer pair.
For each span key (runs/pairlist-a28.jsonl) one representative: (bfx -> NCFF), pairgen.py with the
chosen operand set, r1enum_v5 over the whole Gray range (only when nv <= NVMAX), log one json line.
A window is valid only if the outputs have rank 1 modulo the kept ANDs (checked: 'rank r 1').
usage: pairsweep.py PAIRLIST.jsonl OPS NVMAX OUT.jsonl"""
import sys, os, json, subprocess, tempfile, time
sys.path.insert(0, os.path.expanduser('~/xcr-boolflux/nonlinear'))
from boolflux import core
Z1 = os.path.dirname(os.path.abspath(__file__))
H3 = os.path.expanduser('~/xcr-boolflux/nonlinear/boolflux/strategies/H3')
pl, ops, nvmax, outp = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
model = core.Model.load('nist')
done = set()
if os.path.exists(outp):
    for ln in open(outp):
        done.add(json.loads(ln)['key'])
reps = {}
for ln in open(pl):
    r = json.loads(ln)
    if 'error' in r or not r['pairs']: continue
    reps.setdefault(r['key'], r)
out = open(outp, 'a')
wd = tempfile.mkdtemp(prefix='z1ps-')
for k, r in reps.items():
    if k in done: continue
    f = r['file']; t0 = time.time()
    path = f
    if f.endswith('.bfx'):
        c = core.from_kernel(open(f).read())
        path = os.path.join(wd, os.path.basename(f) + '.circ.txt')
        open(path, 'w').write(core.write_ncff(c, model))
    pair = r['pairs'][0]
    inp = os.path.join(wd, 'in.txt')
    g = subprocess.run(['python3', os.path.join(Z1, 'pairgen.py'), path, '%d,%d' % tuple(pair), inp, ops],
                       capture_output=True, text=True)
    rec = dict(key=k, file=f, E=r['E'], K=r['K'], pair=pair, ops=ops, gen=g.stdout.strip()[-200:])
    if g.returncode != 0:
        rec['result'] = 'PAIRGEN-FAIL ' + g.stderr.strip()[-200:]
    else:
        toks = g.stdout.split()
        nv = int(toks[toks.index('nv') + 1]); rk = int(toks[toks.index('r') + 1])
        rec['nv'] = nv; rec['rank'] = rk
        if rk != 1:
            rec['result'] = 'NOT-A-PAIR-WINDOW'
        elif nv > nvmax:
            rec['result'] = 'SKIP nv %d' % nv
            keep = os.path.expanduser('~/xs-campaigns/2026-11-15-targets/Z1/runs/pair/todo')
            os.makedirs(keep, exist_ok=True)
            tin = os.path.join(keep, '%s-%d-%d-%s.txt' % (k, pair[0], pair[1], ops))
            subprocess.run(['cp', inp, tin]); rec['input'] = tin
            if path != f:
                subprocess.run(['cp', path, keep]); rec['circ'] = os.path.join(keep, os.path.basename(path))
        else:
            p = subprocess.run([os.path.join(H3, 'r1enum_v5'), '1', '%x' % (1 << (nv - 1)), '100000'],
                               stdin=open(inp), capture_output=True, text=True)
            hits = [l for l in p.stdout.splitlines() if l.startswith('H ')]
            summ = [l for l in p.stdout.splitlines() if l.startswith('DONE')]
            rec['result'] = ('HITS %d' % len(hits)) if hits else 'UNSAT'
            rec['done'] = summ[0] if summ else p.stderr[-200:]
            rec['hits'] = hits[:20]
            if hits:
                keep = os.path.expanduser('~/xs-campaigns/2026-11-15-targets/Z1/runs/pair/HIT-%s' % k)
                os.makedirs(keep, exist_ok=True)
                subprocess.run(['cp', path, inp, keep])
    rec['time_s'] = round(time.time() - t0, 1)
    out.write(json.dumps(rec) + '\n'); out.flush()
