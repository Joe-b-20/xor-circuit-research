# Check (not a proof): a block-monotone primal pair circuit whose mirror,
# for one summation order, has an exit across the cut (FRAMEWORK sec. 2 claim
# "Block-monotone circuits have none").
# Inputs: a0..a3 (block 0, free), x0..x3 (block 1), y0..y3 (block 2).
names = ['a0','a1','a2','a3','x0','x1','x2','x3','y0','y1','y2','y3']
idx = {n:i for i,n in enumerate(names)}
mask = {n:1<<i for i,n in enumerate(names)}
ops = {}
def g(name, p, q):
    assert name not in mask
    mask[name] = mask[p]^mask[q]; ops[name] = (p,q)
def vec(*ns):
    v = 0
    for n in ns: v ^= mask[n]
    return v
# x-block gates
g('r1','x0','x1'); g('r2','x0','x2'); g('w1','r1','r2'); g('w2','w1','x3')
g('s','x1','x3'); g('r3','r1','s')
# a-parts (free in the local model)
for c in range(4): g('A%d'%c, 'a%d'%c, 'a%d'%((c+1)%4))
# other sheet-1 x-parts, built without touching r1, r2, w1
g('k01','x0','x1'); g('E2x','k01','x3'); g('E3x','k01','x2')
g('k02','x0','x2'); g('E1x','k02','x3')
g('T1_0','w2','A0'); g('T1_1','E1x','A1'); g('T1_2','E2x','A2'); g('T1_3','E3x','A3')
# y-block
g('q','y2','y3'); g('Ey0','y1','q'); g('Ey1','y0','q'); g('q2','y0','y1'); g('Ey2','q2','y3'); g('Ey3','q2','y2')
g('T2_0','r1','Ey0'); g('T2_3','r3','Ey3')
g('p12','x1','x2'); g('T2_1','p12','Ey1'); g('p23','x2','x3'); g('T2_2','p23','Ey2')
targets = ['T1_%d'%c for c in range(4)] + ['T2_%d'%c for c in range(4)]
def E(c, blk): return sum(1<<idx['%s%d'%(blk,i)] for i in range(4) if i != c)
def S(c, blk): return (1<<idx['%s%d'%(blk,c)]) ^ (1<<idx['%s%d'%(blk,(c+1)%4)])
for c in range(4):
    assert mask['T1_%d'%c] == E(c,'x') ^ S(c,'a'), c
    assert mask['T2_%d'%c] == E(c,'y') ^ S(c,'x'), c
print('all 8 targets correct')
blocks = {'a':0x00f, 'x':0x0f0, 'y':0xf00}
def blks(m): return {b for b,bm in blocks.items() if m & bm}
order = list(names) + list(ops)
# ancestors
anc = {n:set() for n in order}
for n in ops:
    p,q = ops[n]; anc[n] = anc[p] | anc[q] | {p,q}
bm = all(blks(mask[v]) <= blks(mask[t]) for t in targets for v in anc[t] if v in ops)
print('block-monotone (gates):', bm)
# adjoints: formal influence on targets, as a set (mod 2) of targets
readers = {n:[] for n in order}
for n,(p,q) in ops.items(): readers[p].append(n); readers[q].append(n)
adj = {}
for n in reversed(order):
    v = 0
    for r in readers[n]: v ^= adj[r]
    if n in targets: v ^= 1 << targets.index(n)
    adj[n] = v
def show(v): return '{'+','.join(t for i,t in enumerate(targets) if v>>i&1)+'}'
SH1 = 0x0f  # sheet-1 targets = mirror group 1
print('readers of x0:', readers['x0'])
for r in ('r1','r2'): print('adj(%s) ='%r, show(adj[r]), ' omega =', show(adj[r]&SH1))
e = adj['r1'] ^ adj['r2']
print('partial sum adj(r1)+adj(r2) =', show(e), ' omega =', show(e&SH1),
      ' exit across cut 1:', (adj['r1']&SH1)==(adj['r2']&SH1)!=0 and e!=0)
