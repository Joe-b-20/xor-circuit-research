#!/usr/bin/env python3
"""Exact window AND removal (R1's mc1: rank test + exhaustive flat products) on published circuit files.
    andrm.py LIST SECONDS SEED OUTDIR
Every verified A-1 rebuild is written (bfx) and logged; summary per start in OUTDIR/andrm.jsonl."""
import json, random, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import mc1lib as M                    # noqa: E402
R = M.R
from boolflux import core              # noqa: E402

lst, secs, seed, out = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), Path(sys.argv[4])
out.mkdir(parents=True, exist_ok=True)
rng = random.Random(seed)
files = [l.strip() for l in open(lst) if l.strip()]
circ = {f: (core.from_kernel(open(f).read()) if f.endswith(".bfx") else core.read_ncff(f)) for f in files}
nets = {f: R.Net(c) for f, c in circ.items()}
log = open(out / 'andrm.jsonl', 'a')
t_end = time.time() + secs; seen = set(); cnt = {}
while time.time() < t_end:
    f = rng.choice(files); c = circ[f]; net = nets[f]
    W = M.windows(net, rng, 10, 16, 6, 4)
    if not W or (f, frozenset(W)) in seen: continue
    seen.add((f, frozenset(W)))
    rr = M.check_window(net, W, 10)
    if rr is None: continue
    det, ctx, prods = rr
    cnt[det['status']] = cnt.get(det['status'], 0) + 1
    det.update({'file': Path(f).name, 'm': M.metrics(c)})
    if prods is not None:
        rb = M.rebuild(net, ctx, prods)
        if rb is not None:
            chain, om = rb
            nc = R.splice(c, net, W, ctx[0], ctx[1], chain, om)
            mc = R.merge_dups(nc)
            if M.metrics(mc) <= M.metrics(nc): nc = mc
            det['ok'] = nc.output_tables() == c.output_tables(); det['m_new'] = M.metrics(nc)
            p = out / ('andrm-%d.bfx' % len(seen)); p.write_text(core.to_kernel(nc)); det['out'] = str(p)
    log.write(json.dumps(det) + '\n'); log.flush()
print(json.dumps({'windows': len(seen), 'status': cnt}))
