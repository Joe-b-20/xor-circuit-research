s = open("bottom.py").read()
a = s.index("    def evaluate(self, P):")
b = s.index("def basis_reduce(basis):")
new = '''    def evaluate(self, P):
        vecs = [vec(x, y) for x, y in P]
        basis = {}          # pivot bit -> (vector, mask); fully reduced
        deps = []
        for k, v in enumerate(vecs):
            m = 1 << k; w = v
            for p, (bv, bm) in basis.items():
                if (w >> p) & 1: w ^= bv; m ^= bm
            if not w:
                deps.append(m); continue
            p = w.bit_length() - 1
            for q in list(basis):
                bv, bm = basis[q]
                if (bv >> p) & 1: basis[q] = (bv ^ w, bm ^ m)
            basis[p] = (w, m)
        total_terms = 0; worst = 0.0; sets = []
        nd = min(len(deps), 12)
        for v, cst in self.T:
            w = v; m = 0
            for p, (bv, bm) in basis.items():
                if (w >> p) & 1: w ^= bv; m ^= bm
            if w: return None
            best = None
            for z in range(1 << nd):
                mm = m
                for i in range(nd):
                    if (z >> i) & 1: mm ^= deps[i]
                terms = [P[k] for k in range(len(P)) if (mm >> k) & 1]
                key = (max(0.0, self.kraft(terms) - 1.0), len(terms))
                if best is None or key < best[0]: best = (key, terms)
            sets.append(best[1]); worst = max(worst, best[0][0]); total_terms += len(best[1]) - 1
        newf = len({y & 0xFF for x, y in P} - self.have)
        cost = len(P) + self.wx * total_terms + self.wf * newf
        return cost, worst, sets


'''
s = s[:a] + new + s[b:]
open("bottom.py", "w").write(s)
