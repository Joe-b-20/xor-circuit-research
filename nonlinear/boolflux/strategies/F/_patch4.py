s = open("invsyn.py").read()
s = s.replace("""        sup = [a for a in R if a & f == f]""", """        if maxdepth >= 4:      # deep targets (pair sums): linear roots only, bounded memory
            self.dec_cache[key] = out
            return out
        sup = [a for a in R if a & f == f]""")
s = s.replace("""def targets(d1, d2):""", """def targets(d1, d2, sums4=False):""")
s = s.replace("""    if d2 <= d1:""", """    if d2 <= d1 or sums4:""")
open("invsyn.py", "w").write(s)
