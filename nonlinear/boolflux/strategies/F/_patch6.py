s = open("invsyn.py").read()
old = """        viol = sum(max(0, D(f) - d) for f, d in self.tg)
        viol += sum(max(0, D(f) - d) for f, d in req.items())
        return len(req), viol, req
"""
new = """        viol = sum(max(0, D(f) - d) for f, d in self.tg)
        viol += sum(max(0, D(f) - d) for f, d in req.items())
        extra, _ = self.complete(req)
        return len(req) + extra, viol, req

    def complete(self, req):
        \"\"\"Late (depth-4) linear targets: free if already present, one XOR/XNOR of two present
        signals (depth <= 3) if possible, else 3 (penalty: built as a chain).\"\"\"
        late = getattr(self, 'late', [])
        if not late: return 0, []
        avail = set(req) | self.base
        cost = 0; gates = []
        for t in late:
            if t in avail: continue
            done = False
            for a in avail:
                if (t ^ a) in avail: gates.append((6, t, a, t ^ a)); cost += 1; done = True; break
                if (t ^ a ^ M) in avail: gates.append((9, t, a, t ^ a ^ M)); cost += 1; done = True; break
            if not done:
                cost += 3; gates.append((None, t, None, None))
        return cost, gates
"""
assert old in s
s = s.replace(old, new)
open("invsyn.py", "w").write(s)
