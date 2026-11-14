s = open("invsyn.py").read()
a = s.index("    def complete(self, req):")
b = s.index("    def init(self):")
new = '''    def complete(self, req):
        """Late linear targets self.late = [(table, depth)] with depth 4 or 5: free if present,
        else one XOR/XNOR of two available signals of depth <= depth-1, else 3 (penalty)."""
        late = getattr(self, 'late', [])
        if not late: return 0, []
        avail = {f: 3 for f in req}
        for f in self.base: avail[f] = 0
        cost = 0; gates = []
        for t, d in sorted(late, key=lambda x: x[1]):
            if t in avail: continue
            done = False
            ok = [f for f, dd in avail.items() if dd <= d - 1]
            oks = set(ok)
            for a in ok:
                if (t ^ a) in oks: gates.append((6, t, a, t ^ a)); done = True; break
                if (t ^ a ^ M) in oks: gates.append((9, t, a, t ^ a ^ M)); done = True; break
            if done: cost += 1; avail[t] = d
            else: cost += 3; gates.append((None, t, None, None))
        return cost, gates

'''
s = s[:a] + new + s[b:]
open("invsyn.py", "w").write(s)
t = open("invlate.py").read()
t = t.replace("""    tg = [(COMBO[k], 3) for k in early]""", """    FAST = {'y0', 'y1', 'y2', 'y3', 'y0^y2', 'y1^y3'}
    dep = {k: (3 if k in early else 4) if k in FAST else (4 if k in early else 5) for k in COMBO}
    tg = [(COMBO[k], 3) for k in COMBO if dep[k] == 3]""")
t = t.replace("""        syn.late = [COMBO[k] for k in late]""", """        syn.late = [(COMBO[k], dep[k]) for k in COMBO if dep[k] > 3]""")
open("invlate.py", "w").write(t)
