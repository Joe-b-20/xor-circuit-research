"""Verify d13 solutions in the relaxed tower model, minimise, build real circuits, aes_check.
usage: vd13.py PREFIX [maxbuild]     (PREFIX = .../d13/umi-g6 ; reads PREFIX.txt.pkl and PREFIX.sol)"""
import sys, os, pickle, json, subprocess, time
from pathlib import Path
from h2lib import Basis, build_circuit
import tsearch as TS, tbuild as TB, a28parse as AP
from tower import tab, VAR, ONE, m4, tau, W, W2, MUL, INV16, norm

prefix = sys.argv[1]; maxbuild = int(sys.argv[2]) if len(sys.argv) > 2 else 3
P = pickle.load(open(prefix + '.txt.pkl', 'rb'))
mem = P['mem']; g = P['gamma']; ek = P['early']
solfile = sys.argv[3] if len(sys.argv) > 3 else prefix + '.gsol'
sols = [list(map(int, ln.split()[2:])) for ln in open(solfile) if ln.startswith('SOL')]
# relaxed free space
early_x = []      # 256-point (ta, tb) operand pairs for the real build
early_tab = []    # relaxed tables
LRx = [TB.LR(x) for x in range(256)]
inv = {lr: x for x, lr in enumerate(LRx)}
if ek == 'umi':
    for a, b, c in TS.ROWS:
        for r in (1, W, W2):
            early_x.append((TB.T256(lambda x, a=a, r=r: tau(m4(r, TS.lam_val(a, *LRx[x])))),
                            TB.T256(lambda x, b=b, r=r: tau(m4(r, TS.lam_val(b, *LRx[x]))))))
    early_tab = TS.early_products()
else:
    _, ANDS = AP.load(ek[5:])
    for A in ANDS:
        if A['stage'] == 'L':
            early_x.append((A['a'], A['b']))
            o = A['out']; early_tab.append(tab(lambda L, R, v, o=o: (o >> inv[(L, R)]) & 1))
FB = Basis()
for f in [ONE] + VAR + TS.allowed_vquads(g) + early_tab: FB.add(f)
T = TS.targets(g)
mtabs = {}
def mtab(i):
    if i not in mtabs: mtabs[i] = TS.member_table(*mem[i])
    return mtabs[i]
def covers(ids):
    B = FB.copy()
    for i in ids: B.add(mtab(i))
    return all(B.contains(t) for t in T)

def build_real(ids, name):
    ands = list(early_x)
    Dx = [norm(*LRx[x]) for x in range(256)]
    db = [TS.d_bits(Dx[x]) for x in range(256)]
    d0, d1, d2, d3 = [TB.T256(lambda x, i=i: db[x][i]) for i in range(4)]
    ands.append((d0 ^ d1, d2 ^ d3)); M1 = (d0 ^ d1) & (d2 ^ d3)
    ands.append((d1, d2 ^ M1)); M2 = d1 & (d2 ^ M1)
    ands.append((d0 ^ M1, d3)); M3 = (d0 ^ M1) & d3
    ands.append((d2, M1 ^ M3)); M4 = d2 & (M1 ^ M3)
    ands.append((d0 ^ M2, d2 ^ M1 ^ M4))
    vx = [INV16[Dx[x]] ^ MUL[g][Dx[x]] for x in range(256)]
    for i in ids:
        lc, mc = mem[i]
        ands.append((TB.T256(lambda x: tau(TS.lam_val(lc, *LRx[x])) ^ tau(m4(W, TS.mu_val(mc, vx[x])))),
                     TB.T256(lambda x: tau(m4(W, TS.lam_val(lc, *LRx[x]))) ^ tau(TS.mu_val(mc, vx[x])))))
    return build_circuit(8, ands, AP.Stabs, name)

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from boolflux import core
print('solutions to check', len(sols), flush=True)
found = Path(os.path.expanduser('~/xcr-boolflux/nonlinear/boolflux/strategies/H2/found'))
nb = 0; seen = set()
for si, ids in enumerate(sols):
    ok = covers(ids)
    if not ok:
        nbad = globals().get('nbad', 0) + 1; globals()['nbad'] = nbad; continue
    cur = list(ids)
    for i in list(ids):
        trial = [x for x in cur if x != i]
        if covers(trial): cur = trial
    key = tuple(sorted(cur))
    if key in seen: continue
    seen.add(key)
    ne = len(early_x)
    print('sol', si, 'covers; minimal k =', len(cur), 'total ANDs =', ne + 5 + len(cur), flush=True)
    if nb < maxbuild:
        nb += 1
        tag = '%s-s%d' % (os.path.basename(prefix), si)
        c = build_real(cur, 'h2-' + tag)
        m = c.metrics()
        fn = found / ('h2-%s-a%d.circ.txt' % (tag, m['A']))
        fn.write_text(core.write_ncff(c, core.Model.load('nist')), encoding='utf-8')
        r = subprocess.run(['python3', str(Path(__file__).resolve().parents[2] / 'campaigns' / 'aes_check.py'), str(fn)],
                           capture_output=True, text=True)
        print(r.stdout.strip().splitlines()[0] if r.stdout else r.stderr[-500:])
        json.dump({'how': 'H2 d13 exact search, relaxed tower model', 'early': ek, 'gamma_tower': g,
                   'members': [mem[i] for i in cur], 'metrics': m,
                   'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())},
                  open(str(fn) + '.json', 'w'), indent=1)

print('non-covering', globals().get('nbad', 0), 'covering distinct minimal', len(seen))
