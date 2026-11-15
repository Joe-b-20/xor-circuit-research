#!/usr/bin/env python3
"""X1b patch 1 (03:20 UTC): U / junk filter (X3b criterion) in x1b_camp.py."""
import shutil
p = "x1b_camp.py"; shutil.copy(p, "x1b_camp.py.v1"); s = open(p).read()
def rep(a, b):
    global s
    assert a in s, a[:80]
    s = s.replace(a, b)
rep("""            fi = F.analyse_c(nc)
            nc.name = name
            (out / 'found' / (name + '.circ.txt')).write_text(core.write_ncff(nc, MODEL, comments=['agent X1b flip/split walk (bfw.c), x1b_camp.py']))""",
"""            fi = F.analyse_c(nc)
            try: uj = UF.ujunk(c=nc)
            except Exception as e: uj = {'error': repr(e)}
            nc.name = name
            (out / 'found' / (name + '.circ.txt')).write_text(core.write_ncff(nc, MODEL, comments=['agent X1b flip/split walk (bfw.c), x1b_camp.py']))""")
rep("""                'span': fi['span'], 'levels': fi['levels'], 'span_known': fi['span'] in known(),
                'aes_check_ok'""", """                'span': fi['span'], 'levels': fi['levels'], 'span_known': fi['span'] in known(), 'ujunk': uj,
                'U_known': uj.get('U') in knownU(),
                'aes_check_ok'""")
a = s.index("        for m, nc, fi in fresh:\n")
key = "        for m, nc, fi in sorted(fresh, key=lambda x: (x[0][1], x[0][2]))[:npol]:\n"
b = s.index(key)
new = '''        # U / junk filter (X3b criterion): only a new U, or a 9-coverable U, can lead to a 27 [P]
        KU = knownU(); promising = []; npool = 0
        for m, nc, fi in sorted(fresh, key=lambda x: (x[0][1], x[0][2]))[:nfilt]:
            h = fi['span']
            try: uj = UF.ujunk(c=nc) if m[0] <= ufilt_amax else None
            except Exception as e: uj = {'error': repr(e)}
            newU = bool(uj) and 'U' in uj and uj['U'] not in KU
            cov = bool(uj) and uj.get('cover9') is True
            if newU or cov or (bool(uj) and 'error' in uj): promising.append((m, nc, fi, uj))
            if newU: KU.add(uj['U'])
            if newU or cov or npool < 2:
                (out / 'pool' / ('pool-a%d-ad%d-g%d-gd%d-%s.bfx' % (m + (h,)))).write_text(core.to_kernel(nc)); npool += 1
            row = {'span': h, 'A': m[0], 'm': m, 'levels': fi['levels'], 'span_L': fi['span_L'],
                   'shared_with_refs': [F.inter(fi, q) for q in refs], 'from': f, 'run': tag, 'ujunk': uj, 'newU': newU}
            with open(out / ('spans-%d.jsonl' % shard), 'a') as sf: sf.write(json.dumps(row) + '\\n')
            rec['new_spans'].append([h, m, fi['levels'], row['shared_with_refs'], uj and uj.get('U'), newU, uj and uj.get('cover9')])
            if newU or cov: log('NEWU' if newU else 'COVER9', h, m, fi['levels'], uj, 'from', Path(f).name)
        for m, nc, fi, uj in promising[:npol]:
'''
s = s[:a] + new + s[b + len(key):]
rep("""                'shared_with_refs': {str(Path(REFS[i]).name): F.inter(fi2, q) for i, q in enumerate(refs)},""",
    """                'shared_with_refs': {str(Path(REFS[i]).name): F.inter(fi2, q) for i, q in enumerate(refs)}, 'ujunk_rebuilt': uj,""")
rep("""            log('NEWSPAN', name,""", """            log('POLISHED', name,""")
rep("""x1b_camp: bfw sideways walk (new product span) + x1lib.materialise + hub kernel polish""",
    """x1b_camp: bfw sideways walk (new product span, new U or 9-coverable U) + x1lib.materialise + hub kernel polish""")
rep("import x1lib as X, x1walkc as W, x1b_family as F\n", "import x1lib as X, x1walkc as W, x1b_family as F, x1b_ufilter as UF\n")
rep("""    regf = opt('--registry', ''); seed0 = opt('--seed0', 0)""", """    regf = opt('--registry', ''); seed0 = opt('--seed0', 0); uregf = opt('--uregistry', '')
    nfilt = opt('--nfilter', 6); ufilt_amax = opt('--ufilter-amax', 28)""")
rep("""    Acache = {}""", """    ureg = set(json.loads(Path(uregf).read_text())) if uregf else set()
    def knownU():
        k = set(ureg)
        for sf in out.glob('spans-*.jsonl'):
            for ln in sf.read_text().splitlines():
                try:
                    r = json.loads(ln)
                    if r.get('ujunk') and r['ujunk'].get('U'): k.add(r['ujunk']['U'])
                except Exception: pass
        return k
    Acache = {}""")
open(p, "w").write(s)
print("patched")
