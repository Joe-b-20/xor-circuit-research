import sys, json
sys.path.insert(0, '.'); sys.path.insert(0, '../../..')
import build47 as B, invdesign as D, inv6 as I
from rank2 import load, analyse, ONES
from coversearch import TSpan, huff
from boolflux import core, skeleton
d = json.loads(open('/tmp/t4d38.jsonl').readline())
c = load(sys.argv[1]); n = 8
T, lg, la, fa, ba, V, X0 = analyse(c)
sk0 = skeleton.extract(c)
ands_sig = [n + j for j, g in enumerate(c.gates) if g[0] in core.NONLINEAR_OPS]
lvl1 = [k for k, s in enumerate(ands_sig) if la[s] == 1]
X = core.input_tables(8)
st1 = [sk0['ands'][k] for k in lvl1]
P = [T[ands_sig[k]] for k in lvl1]
ts = TSpan()
for i, v in enumerate([ONES] + X + P): ts.add(v, 1 << i)
st1lev = [lg[ands_sig[k]] for k in lvl1]
Nx = [I.p256(x, 17) for x in range(256)]
def lift(f16): return sum(((f16 >> I.IDX[Nx[x]]) & 1) << x for x in range(256))
def alev(f16):
    if f16 in (0, I.ONE): return 0
    tag = ts.express(lift(f16))
    terms = [0] * bin((tag >> 1) & 0xff).count('1') + [st1lev[j] for j in range(9) if (tag >> (9 + j)) & 1]
    return huff(terms, tag & 1)
print('stage-1 levels', st1lev)
for f in sorted(set(x & ~0 for x in I.AFF)):
    if f in (0, I.ONE): continue
    print(hex(f), alev(f), end='; ')
print()
real = D.realise(d['A2'])
for al in sorted(real):
    print('alpha', al)
    for r in real[al][:40]:
        print('   p %s r %s res %s' % (hex(r['p']), hex(r['r']), r['res']))
print('-----')
qs = d['A2']
a2lev = []
for q in qs:
    a2lev.append(1 + min(max(alev(a), alev(b)) for a in I.NONC for b in I.NONC if a < b and a & b == q))
print('a2lev', a2lev)
def l6(f):
    for i, q in enumerate(qs):
        if f == q: return a2lev[i]
        if f == q ^ I.ONE: return a2lev[i] + 1
    return alev(f)
def rl(res):
    k = res[0]
    if k == 'aff': return [alev(res[1])] if res[1] not in (0, I.ONE) else []
    if k == 'A2+aff': return [a2lev[res[1]]] + ([alev(res[2])] if res[2] not in (0, I.ONE) else [])
    return [a2lev[res[1]], a2lev[res[2]]]
for opt in d['all7']:
    print('option four', opt['four'], 'fifth', opt['fifth'], 'share5', opt['share5'])
    for al in opt['four']:
        L = sorted(((huff([1 + max(l6(x['p']), l6(x['r']))] + rl(x['res'])), 1 + max(l6(x['p']), l6(x['r'])), str(x['res'])) for x in real[al]))
        print('   alpha', al, L[:6])
