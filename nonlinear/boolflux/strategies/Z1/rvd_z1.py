"""Verify/minimise/build real-model gen13 solutions.  usage: rvd.py PREFIX SOLFILE [maxbuild]"""
import sys, os, pickle, json, subprocess, time
sys.path.insert(0, os.path.expanduser("~/xcr-boolflux/nonlinear/boolflux/strategies/H2"))
from pathlib import Path
from h2lib import Basis, build_circuit
import tsearch as TS, tbuild as TB, a28parse as AP
from tower import m4, tau, W, MUL, INV16, norm

prefix, solfile = sys.argv[1], sys.argv[2]; maxbuild = int(sys.argv[3]) if len(sys.argv) > 3 else 2
P = pickle.load(open(prefix + '.pkl', 'rb'))
cands = P['cands']; early = P['early_ops']
LRx = [TB.LR(x) for x in range(256)]; Dx = [norm(*lr) for lr in LRx]
T256 = TB.T256
db = [TS.d_bits(Dx[x]) for x in range(256)]
d0, d1, d2, d3 = [T256(lambda x, i=i: db[x][i]) for i in range(4)]
M1 = (d0 ^ d1) & (d2 ^ d3); M2 = d1 & (d2 ^ M1); M3 = (d0 ^ M1) & d3; M4 = d2 & (M1 ^ M3)
mid = [(d0 ^ d1, d2 ^ d3), (d1, d2 ^ M1), (d0 ^ M1, d3), (d2, M1 ^ M3), (d0 ^ M2, d2 ^ M1 ^ M4)]
if P.get('mid_ops'): mid = P['mid_ops']
FB = Basis()
for f in [AP.ONE] + AP.BITS + [a & b for a, b in early] + [a & b for a, b in mid]: FB.add(f)
def ops(c):
    if c[0] == 's':
        from h2lib import gmul as _gm, gpow as _gp
        import gmap as _GM
        _, g, th, sz, fa = c[:5]
        Nr = [_gp(x, 17) for x in range(256)]; nnr = [_gp(x, 238) for x in range(256)]
        gr = [k for k in range(256) if k in set(Nr) and _GM.tower_gamma(k) == g][0] if g else 0
        vr = [nnr[x] ^ _gm(gr, Nr[x]) for x in range(256)]
        nbidx = []; _B = Basis()
        for i in range(8):
            if _B.add(T256(lambda x, i=i: nnr[x] >> i & 1)): nbidx.append(i)
        xl = lambda u: T256(lambda x: bin(u & x).count('1') & 1)
        vl = lambda m: T256(lambda x: sum(((vr[x] >> nbidx[j]) & 1) for j in range(4) if m >> j & 1) & 1)
        if len(fa) == 1: return (xl(fa[0][0]), vl(fa[0][1]))
        (l1, m1), (l2, m2) = fa
        return (xl(l1) ^ vl(m2), xl(l2) ^ vl(m1))
    kind, g, lc, mc = c
    vx = [INV16[Dx[x]] ^ MUL[g][Dx[x]] for x in range(256)]
    lv = [TS.lam_val(lc, *LRx[x]) for x in range(256)]
    if kind == 'm':
        return (T256(lambda x: tau(lv[x]) ^ tau(m4(W, TS.mu_val(mc, vx[x])))),
                T256(lambda x: tau(m4(W, lv[x])) ^ tau(TS.mu_val(mc, vx[x]))))
    return (T256(lambda x: tau(lv[x])), T256(lambda x: tau(TS.mu_val(mc, vx[x]))))
cache = {}
def tabof(i):
    if i not in cache:
        a, b = ops(cands[i]); cache[i] = a & b
    return cache[i]
def covers(ids):
    B = FB.copy()
    for i in ids: B.add(tabof(i))
    return all(B.contains(t) for t in AP.Stabs)
sols = [list(map(int, ln.split()[2:])) for ln in open(solfile) if ln.startswith('SOL')]
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from boolflux import core
found = Path(os.path.expanduser("~/xs-campaigns/2026-11-15-targets/Z1/found"))
seen = set(); nb = 0; bad = 0; spans_built = set()
for si, ids in enumerate(sols):
    if not covers(ids): bad += 1; continue
    cur = list(ids)
    for i in list(ids):
        trial = [x for x in cur if x != i]
        if covers(trial): cur = trial
    key = tuple(sorted(cur))
    if key in seen: continue
    seen.add(key)
    tot = len(early) + len(mid) + len(cur)
    print('sol', si, 'minimal k', len(cur), 'total ANDs', tot, flush=True)
    SB = Basis()
    for i in cur: SB.add(FB.full_reduce(tabof(i))[0])
    vs = [r[0] for r in SB.rows.values()]
    pv = [v.bit_length() - 1 for v in vs]
    for a_ in range(len(vs)):
        for b_ in range(len(vs)):
            if a_ != b_ and (vs[b_] >> pv[a_]) & 1: vs[b_] ^= vs[a_]
    skey = tuple(sorted(vs))
    if skey in spans_built: continue
    if nb < maxbuild:
        spans_built.add(skey)
        nb += 1
        ands = list(early) + mid + [ops(cands[i]) for i in cur]
        c = build_circuit(8, ands, AP.Stabs, 'h2-real')
        m = c.metrics()
        import hashlib
        hh = hashlib.md5((str(P['early']) + str(P['gammas'])).encode()).hexdigest()[:8]
        tag = '%s-%s-s%d' % (os.path.basename(prefix), hh, si)
        fn = found / ("z1g13-%s-a%d.circ.txt" % (tag, m["A"]))
        fn.write_text(core.write_ncff(c, core.Model.load('nist')), encoding='utf-8')
        r = subprocess.run(['python3', os.path.expanduser("~/xcr-boolflux/nonlinear/boolflux/campaigns/aes_check.py"), str(fn)], capture_output=True, text=True)
        chk = (r.stdout or r.stderr).strip().splitlines()[0]
        print(chk)
        if os.environ.get('H2_BUILDLIST') and r.returncode == 0:
            open(os.environ['H2_BUILDLIST'], 'a').write(str(fn) + chr(10))
        json.dump({'how': 'H2 gen13 exact dense-subspace search, real model', 'early': P['early'], 'gammas': P['gammas'],
                   'cands': [cands[i] for i in cur], 'metrics': m, 'aes_check': chk, 'aes_check_ok': r.returncode == 0, 'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())},
                  open(str(fn) + '.json', 'w'), indent=1)
print('candidates', len(sols), 'non-covering', bad, 'distinct covering minimal', len(seen))
