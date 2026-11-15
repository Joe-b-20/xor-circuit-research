#!/usr/bin/env python3
"""T3: greedy distance-reduction SLP (Boyar-Peralta style) over 256-bit truth tables with a large free
base: targets T, base B (existing signals, free). Each step adds one XOR of two available signals:
  1. any target at distance 1 is built at once;
  2. otherwise the pair sum e (in B+B) with the largest total distance reduction over the targets
     (distance = number of XORs needed from the current set, exact up to 3, 4 = 'more'), ties random.
Values are taken up to complement (XNOR is free). Returns the XOR count and the gate list.
"""
import random

ONES = (1 << 256) - 1
norm = lambda v: min(v, v ^ ONES)


class SLP2:
    def __init__(self, base, rng=None):
        self.B = []; self.Bs = set(); self.P = {}
        self.rng = rng or random.Random(1)
        self.gates = []          # (new, u, v) in norm values
        for b in base: self._add(norm(b), record=False)

    def _add(self, e, record=True, uv=None):
        if e in self.Bs: return
        for u in self.B:
            w = norm(u ^ e)
            if w not in self.P: self.P[w] = (u, e)
        self.B.append(e); self.Bs.add(e)
        if record: self.gates.append((e,) + uv)

    def d(self, t):
        if t in self.Bs: return 0
        if t in self.P: return 1
        for b in self.B:
            if norm(t ^ b) in self.P: return 2
        for p in self.P:
            if norm(t ^ p) in self.P: return 3
        return 4

    def run(self, targets):
        T = [norm(t) for t in targets]
        cost = 0
        while True:
            todo = [t for t in T if t not in self.Bs]
            if not todo: return cost
            ones = [t for t in todo if t in self.P]
            if ones:
                t = ones[0]; self._add(t, uv=self.P[t]); cost += 1; continue
            dist = {t: self.d(t) for t in todo}
            if getattr(self, 'verbose', False): print('step', cost, 'B', len(self.B), 'P', len(self.P), sorted(dist.values()), flush=True)
            gain = {}
            for t in todo:
                dt = dist[t]
                # e with t^e in B -> new distance 1
                for b in self.B:
                    e = norm(t ^ b)
                    if e in self.P and e not in self.Bs:
                        gain[e] = gain.get(e, 0) + (dt - 1)
                if dt >= 3:
                    for p in self.P:
                        e = norm(t ^ p)
                        if e in self.P and e not in self.Bs:
                            gain[e] = gain.get(e, 0) + (dt - 2) * 0.999
            if not gain:
                # far targets: take any pair sum that brings the nearest target closer (fallback)
                t = min(todo, key=lambda x: dist[x])
                # build toward t: any pair sum e with d(t^e) smallest
                best = None
                for e in self.P:
                    if e in self.Bs: continue
                    for b in self.B[:64]:
                        pass
                    best = e; break
                self._add(best, uv=self.P[best]); cost += 1; continue
            g = max(gain.values())
            best = [e for e, v in gain.items() if v >= g - 1e-9]
            e = self.rng.choice(best)
            self._add(e, uv=self.P[e]); cost += 1
