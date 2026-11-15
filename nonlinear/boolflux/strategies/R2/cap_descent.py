#!/usr/bin/env python3
"""Cap-respecting A descent with the aslack window move (agent R2).

    python3 cap_descent.py ARCHIVE_CAMPAIGN OUTDIR SEED SECONDS POLISH_S CAPS(A,AD,G,GD goal) ID ...

From each start: windows (aslack.Window/products/pick/rebuild), accept a rebuilt circuit only if
AD <= cap, GD <= cap (hard) and (A, G) lexicographically lower than the current (A first; equal A needs
lower G; 10% sideways moves at equal (A, G) for diversity).  Then the gate kernel (lex a,ad,cost,gd) with
caps (current A, AD cap, GD cap) for POLISH_S seconds.  A circuit meeting the goal (G <= G cap too) is
checked with aes_check and saved to OUTDIR/found with a JSON sidecar.  log: OUTDIR/descent.jsonl."""
import hashlib, json, random, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
PKG_PARENT = next(q for q in HERE.parents if (q / 'boolflux' / 'core.py').exists())
sys.path.insert(0, str(PKG_PARENT)); sys.path.insert(0, str(PKG_PARENT / 'boolflux' / 'campaigns'))
from boolflux import core                         # noqa: E402
from boolflux.hub.archive import Archive          # noqa: E402
from boolflux.hub.common import metrics, sbox     # noqa: E402
from boolflux.hub import ops as HO                # noqa: E402
import aslack as AS                               # noqa: E402
import aes_check                                  # noqa: E402

camp, outd, seed, secs, psecs = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
gA, gAD, gG, gGD = (int(x) for x in sys.argv[6].split(','))
ids = sys.argv[7:]
outd.mkdir(parents=True, exist_ok=True); (outd / 'found').mkdir(exist_ok=True)
md5 = {f: hashlib.md5((HERE / f).read_bytes()).hexdigest() for f in ('aslack.py', 'cap_descent.py')}
ar = Archive(camp); rng = random.Random(seed); log = open(outd / 'descent.jsonl', 'a')


def save(c, tag, parent):
    m = metrics(c); kt = core.to_kernel(c)
    name = 'R2-%s-a%d-ad%d-g%d-gd%d-%s' % (tag, *m, hashlib.sha1(kt.encode()).hexdigest()[:8])
    p = outd / 'found' / (name + '.bfx'); p.write_text(kt)
    r = aes_check.check(str(p))
    (outd / 'found' / (name + '.json')).write_text(json.dumps({'metrics': m, 'parent': parent, 'seed': seed, 'op': 'aslack cap_descent + kernel',
        'goal_caps': [gA, gAD, gG, gGD], 'code_md5': md5, 'time_utc': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
        'aes_check_ok': r.get('ok'), 'new_point': r.get('new_point')}, indent=1, default=str))
    return str(p), r.get('ok'), r.get('new_point')


for sid in ids:
    c = core.from_kernel(Path(sid).read_text(), Path(sid).stem) if sid.endswith('.bfx') else ar.circuit(sid); m = metrics(c); start = m; t0 = time.time(); acc = 0; wins = 0; I = AS.Info(c)
    while time.time() - t0 < secs:
        S = AS.choose_S(I, rng, kmax=rng.choice([5, 5, 8]))
        if S is None: break
        try:
            W = AS.Window(I, S, rng.choice(['wide', 'wide', 'local']), rng, ddepth=rng.choice([None, 1, 2, 2, 3]))
            pr = W.products(rng, exhaustive_dim=10)
            ch = W.pick(pr, rng, noise=rng.choice([0.5, 1.5])) if pr else None
            if ch is None: continue
            rows = W.target_rows(ch, rng)
            nc = AS.rebuild(W, ch, rows, rng) if rows else None
        except Exception:
            continue
        wins += 1
        if nc is None or tuple(nc.value_table()) != sbox(): continue
        m2 = metrics(nc)
        if m2[1] > gAD or m2[3] > gGD: continue
        if (m2[0], m2[2]) < (m[0], m[2]) or ((m2[0], m2[2]) == (m[0], m[2]) and rng.random() < 0.1):
            c, m = nc, m2; I = AS.Info(c); acc += 1
    raw = m
    pd = outd / ('k-%s-%d' % (Path(sid).stem, seed)); pd.mkdir(exist_ok=True)
    pc, info = HO._kernel(c, {'A': m[0], 'AD': gAD, 'GD': gGD}, 'a,ad,cost,gd', rng.randrange(1, 1 << 30), psecs, pd, str(outd))
    fin = c
    for x in pc:
        mx = metrics(x)
        if mx[0] <= m[0] and mx[1] <= gAD and mx[3] <= gGD and (mx[0], mx[2]) <= (m[0], m[2]): fin, m = x, mx
    row = {'start': sid, 'start_m': start, 'windows': wins, 'accepted': acc, 'raw_end': raw, 'final': m, 'secs': round(time.time() - t0, 1)}
    if m[0] < start[0] or m[2] < start[2]:
        row['file'], row['aes_check_ok'], row['new_point'] = save(fin, 'desc', sid)
    if m[0] <= gA and m[1] <= gAD and m[2] <= gG and m[3] <= gGD:
        row['GOAL_HIT'] = True
    log.write(json.dumps(row, default=str) + '\n'); log.flush()
