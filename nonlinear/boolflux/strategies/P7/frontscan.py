"""P7: front (cone of the four base Y-forms) size, AND count and base Y levels for many circuits."""
import sys, glob, json
sys.path.insert(0, '.')
import s1lib as L, bopt
files = sys.argv[1:]
rows = []
for f in files:
    try:
        c = L.load(f); T, lg, la, base = bopt.base_front(c); n = c.n
        if len(base) < 4: continue
        need = set(); st = [b[2] for b in base]
        while st:
            s = st.pop()
            if s < n or s in need: continue
            need.add(s); op, a, b = c.gates[s - n]; st += [a, b]
        m = c.metrics()
        rows.append((len(need), sum(1 for s in need if c.gates[s - n][0] in L.core.NONLINEAR_OPS), [b[0] for b in base], m['A'], m['G'], m['GD'], f))
    except Exception as e:
        pass
rows.sort(key=lambda r: (max(r[2]), r[0]))
for r in rows[:25]: print(r[0], r[1], r[2], '%d/%d/%d' % (r[3], r[4], r[5]), r[6].split('/')[-1])
