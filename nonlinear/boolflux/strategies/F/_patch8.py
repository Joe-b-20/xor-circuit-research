s = open("invsyn.py").read()
a = s.index("    def complete(self, req):")
b = s.index("    def init(self):")
new = '''    def complete(self, req):
        """Late linear targets self.late = [(table, depth)], depth 4 or 5, in depth order:
        free if present; else one XOR/XNOR of two available signals of depth <= d-1 (cost 1);
        else (u ^ v) ^ w with u, v of depth <= d-2 and w of depth <= d-1 (cost 2, the inner XOR
        becomes available); else penalty 4."""
        late = getattr(self, 'late', [])
        if not late: return 0, []
        dep = getattr(self, '_dep', None)
        avail = {}
        for f in self.base: avail[f] = 0
        # true depths of the needed nodes
        memo = {}
        def D(f):
            if f in self.base: return 0
            if f in memo: return memo[f]
            op, x, y = self._ch[f]
            memo[f] = 1 + max(D(x), D(y)); return memo[f]
        for f in req: avail[f] = D(f)
        cost = 0; gates = []
        for t, d in sorted(late, key=lambda x: x[1]):
            if t in avail and avail[t] <= d: continue
            ok1 = {f for f, dd in avail.items() if dd <= d - 1}
            hit = None
            for x in ok1:
                if (t ^ x) in ok1: hit = (6, x, t ^ x); break
                if (t ^ x ^ M) in ok1: hit = (9, x, t ^ x ^ M); break
            if hit:
                gates.append((hit[0], t, hit[1], hit[2])); avail[t] = d; cost += 1; continue
            ok2 = [f for f, dd in avail.items() if dd <= d - 2]
            done = False
            for i, u in enumerate(ok2):
                for v in ok2[i + 1:]:
                    w = t ^ u ^ v
                    for op, ww in ((6, w), (9, w ^ M)):
                        if ww in ok1:
                            p = u ^ v
                            gates.append((6, p, u, v)); gates.append((op, t, p, ww))
                            avail[p] = d - 1; avail[t] = d; cost += 2; done = True; break
                    if done: break
                if done: break
            if not done:
                cost += 4; gates.append((None, t, None, None))
        return cost, gates

'''
s = s[:a] + new + s[b:]
# eval must expose the current choice to complete()
s = s.replace("""        extra, _ = self.complete(req)""", """        self._ch = choice
        extra, _ = self.complete(req)""")
open("invsyn.py", "w").write(s)
t = open("invlate.py").read()
t = t.replace("""        extra_cost, gates = syn.complete(ch)""", """        syn._ch = ch
        extra_cost, gates = syn.complete(ch)""")
open("invlate.py", "w").write(t)
