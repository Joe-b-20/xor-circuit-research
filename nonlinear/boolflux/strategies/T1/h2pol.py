#!/usr/bin/env python3
"""Dedicated descent for a new A28 AND structure (h2pol: generalisation of h3pol.py for H2's AD6 builds, 03:20 UTC).

Differences to h3pol.py: AD is free in phase G (caps A 28 only) and the pool keeps AD <= ADMAX (7); phase D
mixes AD repair (AD cap = member AD - 1, no GD cap; p 0.4 while the front has no AD <= 5 member below
G 150, else 0.2) with GD descent (AD cap 5 if the member has AD <= 5, else member AD; GD cap - 1..2).

    python3 h2pol.py START.circ.txt OUTDIR HOURS SEED

Phase G (G first, GD free): kernel caps A 28, AD 5, no GD cap, objective a,cost,gd, 120 s runs chained
from the current best (and from random members of the phase's front), until 4 runs in a row give no
lower G or until 40% of the time.  Phase D (GD descent toward goal C): kernel caps A 28, AD 5, GD =
(GD of a front member) - 1..2, AD cap off with p 0.3, 90 s; polish at caps (28, 5, GD) 60 s; repeat.
Join checks (hub join.py, both roles, all cut levels) of the current front members with every A28 archive
circuit (G <= 145) after phase G and every 30 min: best A28 join results logged.
Everything (A <= 28) verified and kept in OUTDIR/pool/; goal hits (B, C) go through aes_check into
T1/found/ with a JSON sidecar.  Log: OUTDIR/h3pol.jsonl.
"""
import hashlib, json, os, random, signal, subprocess, sys, time
from pathlib import Path
PKG = Path('/home/joebachir20/xcr-boolflux/nonlinear/boolflux')
sys.path.insert(0, str(PKG.parent))
from boolflux.hub import ops as HO                       # noqa: E402
from boolflux.hub import join as J                       # noqa: E402
from boolflux.hub.common import core, metrics, verify, code_version, MODEL   # noqa: E402

HUBAR = Path('/home/joebachir20/xs-campaigns/2026-11-14-hub/long/archive')
FOUND = Path('/home/joebachir20/xs-campaigns/2026-11-15-study/T1/found')
GOALS = {'B': (28, 4, 130, 22), 'C': (28, 5, 127, 19)}
start, out, hours, seed = Path(sys.argv[1]), Path(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
(out / 'pool').mkdir(parents=True, exist_ok=True); (out / 'job').mkdir(exist_ok=True)
ADMAX = 7
JOIN_TO_POOL = os.environ.get('JOIN_TO_POOL', '0') == '1'
rng = random.Random(seed); T0 = time.time(); END = T0 + hours * 3600
log = open(out / 'h3pol.jsonl', 'a'); VER = code_version()
pool = {}      # id -> (circuit, metrics)


def emit(d):
    d['t'] = round(time.time(), 1); log.write(json.dumps(d, default=str) + '\n'); log.flush()


def cid(c): return hashlib.sha1(core.to_kernel(c).encode()).hexdigest()[:12]


def front():
    pts = {v[1] for v in pool.values()}
    return sorted(p for p in pts if not any(q != p and all(a <= b for a, b in zip(q, p)) for q in pts))


def admit(c, origin):
    m = metrics(c)
    if m[0] > 28 or m[1] > ADMAX: return None
    i = cid(c)
    if i in pool: return None
    ok, info = verify(c)
    if not ok: emit({'event': 'verify_fail', 'm': m, 'info': info}); return None
    newf = not any(all(a <= b for a, b in zip(q, m)) for q in {v[1] for v in pool.values()})
    pool[i] = (c, m)
    (out / 'pool' / ('%d-%d-%d-%d-%s.bfx' % (m + (i,)))).write_text(core.to_kernel(c))
    for g, gm in GOALS.items():
        if all(a <= b for a, b in zip(m, gm)): found(c, m, g, origin)
    return 'new_front' if newf else 'pool'


def found(c, m, g, origin):
    name = 'aes-sbox-a%d-ad%d-g%d-gd%d-%s' % (m + (cid(c),))
    p = FOUND / (name + '.bfx')
    if p.exists(): return
    p.write_text(core.to_kernel(c)); (FOUND / (name + '.circ.txt')).write_text(core.write_ncff(c, MODEL))
    r = subprocess.run([sys.executable, str(PKG / 'campaigns' / 'aes_check.py'), str(p), '--json', str(FOUND / (name + '.check.json'))],
                       capture_output=True, text=True)
    json.dump({'goal': g, 'metrics': m, 'origin': origin, 'driver': 'strategies/T1/h3pol.py', 'start': str(start), 'seed': seed,
               'code_version': VER, 'time_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'aes_check_rc': r.returncode,
               'aes_check_out': r.stdout[-2000:]}, open(FOUND / (name + '.json'), 'w'), indent=1, default=str)
    emit({'event': 'FOUND', 'goal': g, 'm': m, 'file': str(p), 'rc': r.returncode})


def kernel(c, caps, sec, tag):
    HO.KDEFAULTS['T0'] = rng.choice([0.3, 0.6, 0.6, 1.0]); HO.KDEFAULTS['max_excess'] = rng.choice([4, 8, 8, 12])
    d = out / 'job' / tag; d.mkdir(exist_ok=True)
    cs, info = HO._kernel(c, caps, 'a,cost,gd', rng.randrange(1 << 30), sec, d, str(out))
    return cs[0] if cs else None


A28 = None
def joincheck(tag):
    global A28
    if A28 is None:
        A28 = {}
        for f in HUBAR.glob('*.json'):
            if f.name == 'cells.json': continue
            r = json.loads(f.read_text())
            if r['A'] == 28 and r['G'] <= 145:
                A28[r['id']] = J.Prepared(core.from_kernel((HUBAR / (r['id'] + '.bfx')).read_text(), r['id']), r['id'])
    mem = [k for k, v in pool.items() if v[1] in set(front())][:6]
    t0 = time.time(); best = {}; n = 0; adm = 0; jbest = {}
    for k in mem:
        X = J.Prepared(pool[k][0], k)
        for P in A28.values():
            for F, B, role in ((X, P, 'h3front'), (P, X, 'h3back')):
                for c, LX, LY, nint in J.join_all(F, B):
                    n += 1; m = metrics(c)
                    if m[0] > 28: continue
                    key = (role,) + m[1:]
                    best[key] = best.get(key, 0) + 1
                    if JOIN_TO_POOL:
                        if admit(c, 'join(%s,%s)' % (F.id, B.id)) == 'new_front': adm += 1
                    elif key not in jbest:      # v2: joins kept apart (own dir), the pool stays in the start's AND space
                        jbest[key] = 1; (out / 'joins').mkdir(exist_ok=True)
                        (out / 'joins' / ('%s-%d-%d-%d-%d-%s.bfx' % ((role,) + m + (cid(c),)))).write_text(core.to_kernel(c)); adm += 1
    pts = {}
    for key in best:
        pts.setdefault(key[0], []).append(key[1:])
    fr = {r: sorted(p for p in v if not any(q != p and all(a <= b for a, b in zip(q, p)) for q in v)) for r, v in pts.items()}
    emit({'event': 'joincheck', 'tag': tag, 'members': mem, 'joins': n, 'secs': round(time.time() - t0), 'front_by_role': fr,
          'new_front_admissions': adm, 'pool_front': front()})


def on_term(signum, frame):          # v3: harvest the running kernel job's best on stop
    try:
        for b in (out / 'job').glob('*/best.bfx'):
            try: admit(core.from_kernel(b.read_text(), 'h'), 'harvest-sigterm:' + b.parent.name)
            except Exception: pass
        emit({'event': 'harvest_sigterm', 'front': front()})
    finally: os._exit(0)


signal.signal(signal.SIGTERM, on_term)
c0 = core.read_ncff(str(start)) if start.suffix != '.bfx' else core.from_kernel(start.read_text())
admit(c0, 'start'); emit({'event': 'start', 'm': metrics(c0), 'file': str(start)})
# ---- phase G -------------------------------------------------------------------------------
cur = c0; stall = 0; k = 0
while time.time() < T0 + 0.4 * (END - T0) and stall < 4:
    k += 1
    src = cur if rng.random() < 0.7 else pool[rng.choice(list(pool))][0]
    x = kernel(src, {'A': 28, 'AD': None, 'GD': None}, 120, 'g')
    r = admit(x, 'G%d' % k) if x is not None else None
    mx = metrics(x) if x is not None else None
    emit({'phase': 'G', 'k': k, 'from': metrics(src), 'to': mx, 'res': r})
    if x is not None and mx[0] <= 28 and mx[1] <= ADMAX and mx[2] < metrics(cur)[2]: cur = x; stall = 0
    else: stall += 1
emit({'event': 'phaseG_done', 'best': metrics(cur), 'front': front()})
joincheck('after_G'); lastj = time.time()
# ---- phase D -------------------------------------------------------------------------------
k = 0
while time.time() < END - 150:
    k += 1
    fr = front()
    # members of the front at AD <= 5; prefer those nearest goal C
    low5 = any(p[1] <= 5 and p[2] < 150 for p in fr)
    if rng.random() < (0.2 if low5 else 0.4):
        cand = [p for p in fr if p[1] > 4] or fr
        tgt = min(cand, key=lambda p: (p[2], rng.random())) if rng.random() < 0.5 else rng.choice(cand)
        mode = 'adrep'; caps = {'A': 28, 'AD': max(4, tgt[1] - 1), 'GD': None}
    else:
        tgt = rng.choices(fr, weights=[2.0 ** -((max(0, p[2] - 127) + max(0, p[3] - 19) + 4 * max(0, p[1] - 5)) / 2) for p in fr])[0]
        gd = tgt[3] - rng.choice([1, 1, 2]) if tgt[3] > 19 else rng.choice([19, 19, 18])
        mode = 'gd'; caps = {'A': 28, 'AD': 5 if tgt[1] <= 5 else tgt[1], 'GD': gd}
    ids = [i for i, v in pool.items() if v[1] == tgt]
    src = pool[rng.choice(ids)][0]
    gd = caps['GD']; adoff = mode
    x = kernel(src, caps, 90, 'd')
    res = []
    if x is not None:
        res.append((metrics(x), admit(x, 'D%d' % k)))
        mx = metrics(x)
        if mx[0] <= 28:
            y = kernel(x, {'A': 28, 'AD': mx[1], 'GD': mx[3]}, 60, 'p')
            if y is not None: res.append((metrics(y), admit(y, 'P%d' % k)))
    emit({'phase': 'D', 'k': k, 'from': tgt, 'gdcap': gd, 'adoff': adoff, 'res': res})
    if time.time() - lastj > 1800 and time.time() < END - 600:
        joincheck('D%d' % k); lastj = time.time()
emit({'event': 'end', 'front': front()})
