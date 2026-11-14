src = open("union.py").read()
old = "        order = [f for f in sorted(range(F), key=lambda f: (arr0[f], rng.random())) if f >= n and arr0[f] < INF]\n"
new = "        order = self.topo(rng)\n"
assert old in src
src = src.replace(old, new)
old2 = "    def min_arrival(self):"
new2 = '''    def topo(self, rng):
        """Topological order of functions in which every edge's operands precede its output;
        edges that would close a cycle are dropped (counted in self.dropped)."""
        if getattr(self, '_topo', None) is not None:
            return self._topo
        n = self.n; F = self.F
        deps = [set() for _ in range(F)]
        for f in range(n, F):
            for op, a, b in self.by_out[f]:
                deps[f].add(a); deps[f].add(b)
        state = [0] * F; order = []; dropped = 0
        for root in range(F):
            if state[root]: continue
            stack = [(root, iter(sorted(deps[root])))]; state[root] = 1
            while stack:
                f, it = stack[-1]
                nxt = None
                for g in it:
                    if state[g] == 0: nxt = g; break
                    if state[g] == 1:   # cycle: drop edges of f that use g
                        before = len(self.by_out[f])
                        self.by_out[f] = [e for e in self.by_out[f] if g not in (e[1], e[2])]
                        dropped += before - len(self.by_out[f])
                if nxt is None:
                    state[f] = 2; order.append(f); stack.pop()
                else:
                    state[nxt] = 1; stack.append((nxt, iter(sorted(deps[nxt]))))
        self.dropped = dropped
        self._topo = [f for f in order if f >= n]
        print('topological order: %d functions, %d edges dropped for cycles' % (len(self._topo), dropped), file=sys.stderr)
        return self._topo

    def min_arrival(self):'''
src = src.replace(old2, new2, 1)
open("union.py", "w").write(src)
