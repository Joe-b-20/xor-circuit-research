#!/usr/bin/env python3
"""Task 3(c): planted-object test.
1. Build valid three-label objects by random constructive sampling with the reviewer's own tables (rgeo) and check them
   with the reviewer's own rule check (rcheck: R1-R7, a, d).
2. For each object: put it into the pilot's canonical skeleton form (own computation of the canonical slot permutation,
   cross-checked against the pilot's canonical_skeleton), call the pilot's step G (plan + run_skeleton of a COPY of
   enum_q3.py, no LP / MILP involved) with a guide that admits only the object's own values under each byte rotation
   rho^j, and check that a survivor equal to the object's constrained part is reported for some j.
   Variants: enum_cur (current file, 2026-11-11 fix) and enum_p1h (pass-1 product-phase rider handling restored).
3. Also run the pilot's step S (skeleton_enum) with a dummy row filter that only caps the class counts at the object's
   own counts, and check that the object's canonical skeleton is produced.
4. Also run the reviewer's own search (rsearch, mode 'exclude', guided) on the object (self-test of the reviewer's tool).
usage: t3c_planted.py N seed out.jsonl
"""
import sys, json, random, itertools, time
from collections import Counter
from pathlib import Path
PILOT = Path.home() / 'xs-campaigns/2026-11-10-proof/pilot'
sys.path.insert(1, str(PILOT))
import rgeo, rcheck, rsearch
import enum_cur, enum_p1h

if __name__ == '__main__':
    N = int(sys.argv[1]); seed = int(sys.argv[2]); outp = sys.argv[3]
else:
    N = 0; seed = 0; outp = '/dev/null'
rng = random.Random(seed)
G = rgeo.Geo()
PG = enum_cur.build_geo(); enum_p1h.GEO = PG
assert PG.B == G.B, 'boundary index conventions differ'
LBL = {w: G.labels_ge(w) for w in range(1, 8)}
FULLS = G.fulls


def random_shape():
    a = rng.choice([0, 0, 1, 1, 2]); d = rng.choice([0, 0, 1]) if a + 1 <= 3 else 0
    if a + d > 3: d = 0
    status = ['F'] * a + ['B'] * (3 - a - d) + ['D'] * d
    F = [s for s in range(3) if status[s] == 'F']; Bs = [s for s in range(3) if status[s] == 'B']; Ds = [s for s in range(3) if status[s] == 'D']
    roles = []
    if a == 2 and rng.random() < 0.3: roles.append((3, (0, 1)))
    else:
        for s in F: roles.append((3, (s,)))
    for s in Bs: roles.append((rng.choice([1, 2, 2]), (s,)))
    nextra = rng.choice([0, 1, 2, 2, 3, 3, 4, 5])
    for _ in range(nextra):
        r = rng.choice([0, 0, 1, 1, 2, 2])
        allowed = [s for s in range(3) if (r == 0 or status[s] != 'D')]
        if not allowed: continue
        k = rng.choice([1, 1, 2, 2, 3]) if len(allowed) >= 2 else 1
        k = min(k, len(allowed))
        L = tuple(sorted(rng.sample(allowed, k)))
        roles.append((r, L))
    # merge a 2-label role sometimes: replace a single-slot anchored role by a 2-label one
    if rng.random() < 0.4 and len(Bs) + len(F) >= 2:
        cand = [i for i, (r, L) in enumerate(roles) if r in (1, 2) and len(L) == 1]
        if cand:
            i = rng.choice(cand); r, L = roles[i]
            others = [s for s in range(3) if s not in L and status[s] != 'D']
            if others: roles[i] = (r, tuple(sorted(L + (rng.choice(others),))))
    # R5, B-1, dark has no anchored, bright has no r=3
    for i, k in itertools.combinations(range(len(roles)), 2):
        if len(set(roles[i][1]) & set(roles[k][1])) >= 2: return None
    W = [sum(r for r, L in roles if s in L) for s in range(3)]
    if any(w > 7 for w in W): return None
    for s in range(3):
        if status[s] == 'B' and not any(r >= 1 and s in L for r, L in roles): return None
        if status[s] == 'F' and sum(1 for r, L in roles if r == 3 and s in L) != 1: return None
    return a, d, status, roles, W


def pilot_skeletons():
    import glob
    out = set()
    for fn in glob.glob(str(PILOT / 'results/leaf_*.json')):
        D = json.load(open(fn))
        for e in D['skeleton_list']:
            out.add((D['A'], D['qD'], tuple((r, tuple(L)) for r, L in e['roles'])))
        for ks in D.get('skeletons_milp_killed') or []:
            out.add((D['A'], D['qD'], tuple((r, tuple(L)) for r, L in ks)))
    return sorted(out)


PSK = pilot_skeletons()


def template_shape():
    """structured shapes: triangles, groups linked only through r = 0 riders, chains closed by riders, pilot skeletons."""
    t = rng.choice(['tri', 'link', 'chain', 'pilot', 'pilot', 'pilot'])
    if t == 'pilot':
        a, d, roles = rng.choice(PSK); roles = list(roles)
        # sometimes drop or add a single-label role to vary
        if rng.random() < 0.3 and len(roles) > 3:
            roles.pop(rng.randrange(len(roles)))
        status = ['F'] * a + ['B'] * (3 - a - d) + ['D'] * d
    else:
        a = rng.choice([0, 0, 1]); d = rng.choice([0, 1]) if t == 'link' else 0
        status = ['F'] * a + ['B'] * (3 - a - d) + ['D'] * d
        roles = []
        if a: roles.append((3, (0,)))
        if t == 'tri':
            for L in ((0, 1), (0, 2), (1, 2)):
                r = rng.choice([0, 1, 2, 2]) if not set(L) & {s for s in range(3) if status[s] == 'D'} else 0
                roles.append((r, L))
        elif t == 'link':
            for s in range(3):
                if status[s] == 'D': continue
                for _ in range(rng.choice([1, 2, 3])): roles.append((rng.choice([1, 2]), (s,)))
            roles.append((0, rng.choice([(0, 1), (0, 1, 2)]) if d == 0 else (0, 1, 2)))
        else:
            roles += [(rng.choice([1, 2]), (0, 1)), (rng.choice([1, 2]), (1, 2)), (0, (0, 2))]
        for _ in range(rng.choice([0, 1, 2, 3])):
            s = rng.randrange(3)
            r = 0 if status[s] == 'D' else rng.choice([0, 1, 2])
            roles.append((r, (s,)))
    for i, k in itertools.combinations(range(len(roles)), 2):
        if len(set(roles[i][1]) & set(roles[k][1])) >= 2: return None
    W = [sum(r for r, L in roles if s in L) for s in range(3)]
    if any(w > 7 for w in W): return None
    for s in range(3):
        if status[s] == 'B' and (not any(r >= 1 and s in L for r, L in roles) or any(r == 3 and s in L for r, L in roles)): return None
        if status[s] == 'F' and sum(1 for r, L in roles if r == 3 and s in L) != 1: return None
        if status[s] == 'D' and any(r >= 1 and s in L for r, L in roles): return None
    return sum(1 for x in status if x == 'F'), sum(1 for x in status if x == 'D'), status, roles, W


def realize(status, roles, W, tries=200):
    """random constructive realization; returns an object or None."""
    for _ in range(tries):
        lab = [None] * 3; masks = set(); helpers = []; basis = rgeo.Basis(); last = {}
        order = list(range(len(roles))); rng.shuffle(order)
        pending = list(order); ok = True
        while pending and ok:
            touch = [i for i in pending if any(lab[s] is not None for s in roles[i][1])]
            if touch: i = touch[0]
            else:
                anch = [i for i in pending if roles[i][0] >= 1]
                if anch:
                    i = anch[0]; r, L = roles[i]
                    s = rng.choice(L)
                    if r == 3:
                        f = rng.choice(FULLS); b = rng.choice(G.B); l = f ^ b
                    else:
                        l = rng.choice(LBL[max(1, W[s])])
                    if l in lab: ok = False; break
                    lab[s] = l
                else:
                    i = pending[0]; s = roles[i][1][0]
                    lab[s] = rng.choice(LBL[1]) if rng.random() < 0.5 else ((rng.getrandbits(32) & ~1) | 0) & 0xFFFFFFFF
                    if bin(lab[s]).count('1') % 2: lab[s] ^= 1 << 31
                    if lab[s] == 0 or lab[s] in lab[:s] + lab[s + 1:]: ok = False; break
            r, L = roles[i]
            C = [s for s in L if lab[s] is not None]; Nn = [s for s in L if lab[s] is None]
            cands = []
            for b in G.B:
                h = lab[C[0]] ^ b
                if h in G.Bset or h in masks: continue
                T = G.trip.get(h, [])
                if r == 3 and len(T) != 3: continue
                if len(T) < r: continue
                if any((h ^ lab[s]) not in G.Bset for s in C[1:]): continue
                cands.append(h)
            if not cands: ok = False; break
            h = rng.choice(cands); T = G.trip.get(h, [])
            R = list(T) if r == 3 else (rng.sample(T, r) if r else [])
            ends = {s: G.idx[h ^ lab[s]] for s in C}
            for s in Nn:
                choices = [e for e in range(64) if e not in ends.values() and (h ^ G.B[e]) not in lab]
                if status[s] != 'D': choices = [e for e in choices if G.rk(h ^ G.B[e]) >= W[s]]
                if not choices: ok = False; break
                e = rng.choice(choices); lab[s] = h ^ G.B[e]; ends[s] = e
            if not ok: break
            k = len(helpers); Hk = 1 << (64 + k)
            vs = [t | Hk for t in R]
            for s in C:
                if s in last:
                    k2, e2 = last[s]; vs.append(Hk | (1 << (64 + k2)) | (1 << ends[s]) | (1 << e2))
            if not basis.add_all(vs): ok = False; break
            for s in L: last[s] = (k, ends[s])
            masks.add(h); helpers.append(dict(mask=h, r=r, triples=list(R), labels=list(L)))
            pending.remove(i)
        if not ok: continue
        for s in range(3):
            while lab[s] is None:
                v = rng.getrandbits(32)
                if v and bin(v).count('1') % 2 == 0 and v not in lab: lab[s] = v
        obj = dict(labels=[dict(value=lab[s], status=status[s]) for s in range(3)], helpers=helpers)
        return obj
    return None


def canonical_perm(roles, status):
    best = None; bp = None
    for p in itertools.permutations(range(3)):
        if any(status[p[s]] != status[s] for s in range(3)): continue
        img = tuple(sorted((r, tuple(sorted(p[s] for s in L))) for r, L in roles))
        if best is None or img < best: best = img; bp = p
    return best, bp


def apply_perm(obj, p):
    labs = [None] * 3
    for s in range(3): labs[p[s]] = obj['labels'][s]
    hel = [dict(h, labels=sorted(p[s] for s in h['labels'])) for h in obj['helpers']]
    return dict(labels=labs, helpers=hel)


def rot_obj(obj, j):
    def rj(m):
        for _ in range(j): m = rgeo.rot(m)
        return m
    def rsub(t):   # rotate a boundary subset (indices) through the masks
        out = 0
        for k in range(64):
            if t >> k & 1: out |= 1 << G.idx[rj(G.B[k])]
        return out
    return dict(labels=[dict(value=rj(l['value']), status=l['status']) for l in obj['labels']],
                helpers=[dict(mask=rj(h['mask']), r=h['r'], triples=[rsub(t) for t in h['triples']], labels=list(h['labels'])) for h in obj['helpers']])


class Guide:
    def __init__(self, obj):
        self.lab = {s: l['value'] for s, l in enumerate(obj['labels'])}
        self.masks = Counter(); self.hr = set()
        for h in obj['helpers']:
            role = (h['r'], tuple(h['labels']))
            self.masks[(role, h['mask'])] += 1; self.hr.add((role, h['mask'], frozenset(h['triples'])))
    def ok_root(self, s, l): return self.lab.get(s) == l
    def ok_label(self, s, l): return self.lab.get(s) == l
    def ok_mask(self, role, h): return (tuple((role[0], tuple(role[1]))), h) in self.masks
    def ok_helper(self, role, h, R): return ((role[0], tuple(role[1])), h, frozenset(R)) in self.hr


def constrained_part(obj, pl):
    """the helpers of the object that the pilot's step G branches over (constrained components, not r=0,u=1)."""
    cslots = set(s for c in pl['constrained'] for s in c['slots'])
    keep = [h for h in obj['helpers'] if set(h['labels']) <= cslots and not (h['r'] == 0 and len(h['labels']) == 1)]
    return cslots, keep


def match(snap, obj, cslots, keep):
    got = Counter((h, frozenset(R)) for h, R, ends, i in snap['helpers'])
    want = Counter((x['mask'], frozenset(x['triples'])) for x in keep)
    labs_ok = all(snap['labels'][s] == obj['labels'][s]['value'] for s in cslots)
    return got == want and labs_ok


def pilot_step_G(mod, obj, skel):
    pl = mod.plan(skel)
    cslots, keep = constrained_part(obj, pl)
    res_j = []
    for j in range(4):
        o2 = rot_obj(obj, j)
        cslots, keep = constrained_part(o2, pl)
        g = Guide(o2)
        res = mod.run_skeleton(PG, pl, 10, 10, time.process_time() + 60, guide=g)
        hit = any(match(sn, o2, cslots, keep) for sn in res['snaps'])
        res_j.append((j, res['status'], res['survivors'], hit))
        if hit: break
    return pl, any(x[3] for x in res_j), res_j


class DummyLP:
    """the row filter disabled: every class present, counts capped at the object's own counts (finite step S)."""
    def __init__(self, cap):
        self.cap = cap
        self.ind = {(r, u): None for r in range(4) for u in range(1, 4)}
    def feasible(self, counts, exact):
        return all(n <= self.cap.get(c, 0) for c, n in counts.items())


def main():
    global made
    out = open(outp, 'w'); stats = Counter(); t0 = time.time(); made = 0; attempts = 0
    while made < N and attempts < 200 * N:
        attempts += 1
        tmpl = rng.random() < 0.7
        sh = template_shape() if tmpl else random_shape()
        if sh is None: continue
        a, d, status, roles, W = sh
        obj = realize(status, roles, W, tries=60)
        if obj is None: stats['realize_failed'] += 1; continue
        chk = rcheck.check(obj, G, a, d)
        if not chk['all_R1_R7']: stats['own_check_failed'] += 1; continue
        made += 1
        canon, p = canonical_perm([(h['r'], tuple(h['labels'])) for h in obj['helpers']], status)
        assert canon == enum_cur.canonical_skeleton([(h['r'], tuple(h['labels'])) for h in obj['helpers']], status)
        objc = apply_perm(obj, p)
        assert rcheck.check(objc, G, a, d)['all_R1_R7']
        Wc = [sum(r for r, L in canon if s in L) for s in range(3)]
        skel = dict(roles=[[r, list(L)] for r, L in canon], status=status, W=Wc)
        rec = dict(i=made, a=a, d=d, roles=skel['roles'], W=Wc, obj=objc, template=tmpl,
                   in_pilot_lists=(a, d, tuple((r, tuple(L)) for r, L in canon)) in set(PSK))
        stats['template' if tmpl else 'random'] += 1
        if rec['in_pilot_lists']: stats['skeleton_in_pilot_lists'] += 1
        for name, mod in (('cur', enum_cur), ('p1', enum_p1h)):
            try:
                pl, hit, rj = pilot_step_G(mod, objc, skel)
            except Exception as ex:
                rec[name] = dict(hit=False, error=repr(ex)[:300]); stats[f'{name}_ERROR'] += 1; continue
            rec[name] = dict(hit=hit, runs=rj, segments=len(pl['segments']), free=[sorted(c['slots']) for c in pl['free']],
                             constrained=[sorted(c['slots']) for c in pl['constrained']], riders=len(pl['riders']), riders2=len(pl['riders2']),
                             inseg_riders=sum(1 for e in pl['order'] if pl['roles'][e[0]][0] == 0) - len(pl['riders2']))
            if name == 'cur':
                if rec[name]['riders2']: stats['has_deferred_r0_u2'] += 1
                if rec[name]['inseg_riders']: stats['has_inseg_r0_u2'] += 1
                if any(len(L) >= 2 and r >= 1 for r, L in canon): stats['anchored_multi_label'] += 1
            stats[f'{name}_hit' if hit else f'{name}_MISS'] += 1
        # step S with the row filter disabled (dummy LP capping counts)
        cap = dict(Counter((r, len(L)) for r, L in canon))
        skels, sst = enum_cur.skeleton_enum(DummyLP(cap), a, d)
        inS = any(tuple((r, tuple(L)) for r, L in s['roles']) == canon for s in skels)
        rec['stepS_contains'] = inS; stats['stepS_hit' if inS else 'stepS_MISS'] += 1
        # reviewer's own search, guided, all four rotations, rotation reduction on
        own = False
        for j in range(4):
            o2 = rot_obj(objc, j); gd = Guide(o2)
            S = rsearch.Search(G, canon, status, mode='exclude', use_rot=True, max_found=50, time_cap=60)
            def gfun(kind, x, y, gd=gd, S=S):
                if kind == 'label': return gd.lab.get(x) == y
                if kind == 'mask': return (S.roles[x], y) in gd.masks
                return (S.roles[x], y[0], frozenset(y[1])) in gd.hr
            S.guide = gfun; S.run()
            keepmask = Counter((x['mask'], frozenset(x['triples'])) for x in o2['helpers'] if not (x['r'] == 0 and len(x['labels']) == 1))
            for f in S.found:
                got = Counter((x['mask'], frozenset(x['triples'])) for x in f['helpers'])
                if all(got[k] <= keepmask[k] for k in got) and sum(got.values()) == len(S.roles): own = True; break
            if own: break
        rec['own_hit'] = own; stats['own_hit' if own else 'own_MISS'] += 1
        shape = Counter()
        if any(len(h['labels']) >= 2 for h in objc['helpers']): shape['two_label_helper'] += 1
        if any(sum(1 for h in objc['helpers'] if s in h['labels']) >= 3 for s in range(3)): shape['label_3plus_carriers'] += 1
        rec['shape'] = dict(shape)
        for k in shape: stats['shape_' + k] += 1
        stats[f'segments_{rec["cur"].get("segments")}'] += 1
        out.write(json.dumps(rec) + '\n'); out.flush()
        if made % 20 == 0: print(made, dict(stats), f'{time.time()-t0:.0f}s', flush=True)
    print('FINAL', made, 'attempts', attempts, dict(stats), f'{time.time()-t0:.0f}s', flush=True)


if __name__ == '__main__':
    main()