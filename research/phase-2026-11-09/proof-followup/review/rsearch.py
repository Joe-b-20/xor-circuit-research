#!/usr/bin/env python3
"""rsearch.py -- reviewer's own exhaustive depth-first realization search for a skeleton (roles (r, L), slot statuses),
written independently of enum_q3.py.  Differences from the pilot by design:
  * STATIC order; r = 0, u >= 2 roles are placed as soon as they touch a concrete slot and may CREATE labels (the pilot
    defers them and enumerates a second root instead);
  * the joint family uses a PATH spanning tree per label in placement order (the pilot uses a star);
  * GF(2) basis keyed on the highest bit, copied per node (no undo);
  * the root slot is the bright slot of largest W of the first role chosen (own rule); rotation reduction (orbit minimum,
    own rotation) on that first root only, optional (use_rot=False enumerates every label).
Pruning: R1 (masks new / odd / not in B, labels new), R3 (#triples >= r, r = 3 full), (D-b) ends in B, rank(C_l) >= W_l for
bright labels ((D-l), necessary), R7 incremental.  Identical roles (same (r, L), |L| = 1) in increasing mask (optional).
mode 'exclude': r = 0, u = 1 roles and free components are dropped (sound: a sub-object of a valid object is valid).
mode 'full': nothing dropped (to build complete witnesses).
"""
import itertools, time
import rgeo


def components(roles, nslots=3):
    parent = list(range(nslots))

    def f(x):
        while parent[x] != x: x = parent[x]
        return x
    for r, L in roles:
        for s in L[1:]: parent[f(s)] = f(L[0])
    comps = {}
    for s in range(nslots): comps.setdefault(f(s), set()).add(s)
    out = []
    for cs in comps.values():
        ro = [i for i, (r, L) in enumerate(roles) if L[0] in cs]
        anch = [i for i in ro if roles[i][0] >= 1]
        edges = sum(len(roles[i][1]) for i in ro); verts = len(cs) + len(ro)
        out.append(dict(slots=cs, roles=ro, free=(len(anch) <= 1 and edges == verts - 1)))
    return out


class Search:
    def __init__(self, G, roles, status, mode='exclude', use_rot=True, symbreak=True, node_cap=None, time_cap=None,
                 max_found=1, guide=None):
        self.G = G; self.status = status
        self.roles_all = [(r, tuple(L)) for r, L in roles]
        self.W = [sum(r for r, L in self.roles_all if s in L) for s in range(3)]
        keep = list(range(len(self.roles_all)))
        if mode == 'exclude':
            keep = [i for i in keep if not (self.roles_all[i][0] == 0 and len(self.roles_all[i][1]) == 1)]
            sub = [self.roles_all[i] for i in keep]
            comps = components(sub)
            drop = {keep[j] for c in comps if c['free'] for j in c['roles']}
            keep = [i for i in keep if i not in drop]
        self.keep = keep
        self.roles = [self.roles_all[i] for i in keep]
        self.use_rot = use_rot; self.symbreak = symbreak
        self.node_cap = node_cap; self.time_cap = time_cap; self.max_found = max_found
        self.nodes = 0; self.found = []; self.aborted = False; self.t0 = None
        self.guide = guide
        self.order = self.plan()
        self.rootcache = {}

    def plan(self):
        roles = self.roles; W = self.W
        remaining = list(range(len(roles))); concrete = set(); order = []; first = True
        while remaining:
            touch = [i for i in remaining if set(roles[i][1]) & concrete]
            if touch:
                i = max(touch, key=lambda i: (len(set(roles[i][1]) & concrete), roles[i][0], -len(roles[i][1]), -i))
                order.append(('attach', i, None, False))
            else:
                anch = [i for i in remaining if roles[i][0] >= 1]
                if not anch:     # only unanchored roles on dark slots (full mode): the dark label is a free even value
                    i = remaining[0]; s = roles[i][1][0]
                    assert all(self.status[x] == 'D' for x in roles[i][1]), ('unanchored root on a bright slot', roles)
                    order.append(('darkroot', i, s, False))
                    concrete |= set(roles[i][1]); remaining.remove(i); continue
                i = max(anch, key=lambda i: (max(W[s] for s in roles[i][1]), roles[i][0], -i))
                s = max(roles[i][1], key=lambda s: (W[s], -s))
                order.append(('root', i, s, first and self.use_rot)); first = False
            concrete |= set(roles[i][1]); remaining.remove(i)
        # identical predecessors for the symmetry break
        self.prev_same = []
        for k, (_, i, _, _) in enumerate(order):
            r, L = roles[i]
            self.prev_same.append([k2 for k2 in range(k) if roles[order[k2][1]] == (r, L) and len(L) == 1] if self.symbreak else [])
        return order

    def roots(self, w, rot, dark=False):
        if dark:
            return [((1 << a) | (1 << b)) << 0 for a, b in itertools.combinations(range(32), 2)][:200]
        key = (w, rot)
        if key not in self.rootcache:
            L = self.G.labels_ge(max(w, 1))
            if rot: L = [l for l in L if rgeo.orbit_min(l) == l]
            self.rootcache[key] = L
        return self.rootcache[key]

    def run(self):
        self.t0 = time.process_time()
        n = len(self.order)
        st = dict(lab=[None] * 3, masks=set(), labs=set(), hel=[None] * n, last={})
        try:
            self.dfs(0, st, rgeo.Basis())
        except StopIteration:
            pass
        return self

    def tick(self):
        self.nodes += 1
        if self.node_cap and self.nodes > self.node_cap: self.aborted = True; raise StopIteration
        if self.time_cap and (self.nodes & 4095) == 0 and time.process_time() - self.t0 > self.time_cap:
            self.aborted = True; raise StopIteration

    def dfs(self, k, st, basis):
        self.tick()
        if k == len(self.order):
            self.found.append(self.snapshot(st))
            if len(self.found) >= self.max_found: raise StopIteration
            return
        kind, i, s, rot = self.order[k]
        if kind in ('root', 'darkroot'):
            for l in self.roots(self.W[s], rot, dark=(kind == 'darkroot')):
                if l in st['labs']: continue
                if self.guide and not self.guide('label', s, l): continue
                st['lab'][s] = l; st['labs'].add(l)
                self.attach(k, i, st, basis)
                st['labs'].discard(l); st['lab'][s] = None
        else:
            self.attach(k, i, st, basis)

    def attach(self, k, i, st, basis):
        G = self.G; r, L = self.roles[i]; lab = st['lab']
        C = sorted([s for s in L if lab[s] is not None], key=lambda s: (-self.W[s], s))
        N = [s for s in L if lab[s] is None]
        s0 = C[0]; l0 = lab[s0]
        hmin = max((st['hel'][k2][0] for k2 in self.prev_same[k]), default=-1)
        Hk = 1 << (64 + k)
        for b in G.B:
            h = l0 ^ b
            if h in G.Bset or h in st['masks'] or h <= hmin: continue
            if r >= 1:
                T = G.trip.get(h, [])
                if len(T) < r: continue
            ends = {s0: G.idx[b]}; ok = True
            for s in C[1:]:
                e = h ^ lab[s]
                if e not in G.Bset: ok = False; break
                ends[s] = G.idx[e]
            if not ok: continue
            if self.guide and not self.guide('mask', i, h): continue
            Rs = [tuple(T)] if r == 3 else (itertools.combinations(T, r) if r >= 1 else [()])
            for R in Rs:
                if self.guide and not self.guide('helper', i, (h, R)): continue
                nb = basis.copy(); good = True
                for t in R:
                    if not nb.add(t | Hk): good = False; break
                if good:
                    for s in C:
                        if s in st['last']:
                            k2, e2 = st['last'][s]
                            if not nb.add(Hk | (1 << (64 + k2)) | (1 << ends[s]) | (1 << e2)): good = False; break
                if not good: continue
                st['masks'].add(h)
                self.newlabels(k, i, h, R, list(C), N, 0, dict(ends), st, nb)
                st['masks'].discard(h)

    def newlabels(self, k, i, h, R, C, N, j, ends, st, nb):
        G = self.G
        if j == len(N):
            r, L = self.roles[i]
            saved = {s: st['last'].get(s) for s in L}
            for s in L: st['last'][s] = (k, ends[s])
            st['hel'][k] = (h, R, dict(ends), i)
            self.dfs(k + 1, st, nb)
            st['hel'][k] = None
            for s in L:
                if saved[s] is None: del st['last'][s]
                else: st['last'][s] = saved[s]
            return
        s = N[j]; used = set(ends.values())
        for e in range(64):
            if e in used: continue
            l = h ^ G.B[e]
            if l in st['labs']: continue
            if self.status[s] != 'D' and G.rk(l) < self.W[s]: continue
            if self.guide and not self.guide('label', s, l): continue
            st['lab'][s] = l; st['labs'].add(l); ends[s] = e
            self.newlabels(k, i, h, R, C, N, j + 1, ends, st, nb)
            del ends[s]; st['labs'].discard(l); st['lab'][s] = None

    def snapshot(self, st):
        hel = []
        for x in st['hel']:
            h, R, ends, i = x
            r, L = self.roles[i]
            hel.append(dict(mask=h, r=r, triples=list(R), labels=list(L)))
        return dict(labels=[dict(value=st['lab'][s], status=self.status[s]) for s in range(3)], helpers=hel)
