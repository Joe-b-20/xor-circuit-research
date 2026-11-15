#!/usr/bin/env python3
"""X1b patch 2 (03:25 UTC): every new U is saved to found/ (polished within --npolish, else the rebuilt
circuit), U recomputed after polish, names carry -NU / -NU-C9; known-U 9-coverable sightings are pooled
(at most 2 per run) but not polished."""
import shutil
p = "x1b_camp.py"; shutil.copy(p, "x1b_camp.py.v2"); s = open(p).read()
def rep(a, b):
    global s
    assert a in s, a[:80]
    s = s.replace(a, b)
rep("""            if newU or cov or (bool(uj) and 'error' in uj): promising.append((m, nc, fi, uj))
            if newU: KU.add(uj['U'])
            if newU or cov or npool < 2:""", """            if newU or (bool(uj) and 'error' in uj): promising.append((m, nc, fi, uj))
            if newU: KU.add(uj['U'])
            if newU or npool < 2:""")
a = s.index("        for m, nc, fi, uj in promising[:npol]:\n")
b = s.index("        with open(out / ('runs-%d.jsonl' % shard), 'a') as rf:")
new = '''        promising.sort(key=lambda x: (not (x[3] or {}).get('cover9') is True, x[0][1], x[0][2]))
        for k, (m, nc, fi, uj) in enumerate(promising):
            best = nc; polished = False
            if k < npol and time.time() < t_end - pol - 10:
                sd = out / 'polish' / ('%s-%s' % (tag, fi['span'])); sd.mkdir(parents=True, exist_ok=True)
                try:
                    cs, info = HO._kernel(nc, {'A': m[0], 'AD': m[1], 'GD': None}, HO.DEFAULT_OBJECTIVE, seed, pol, sd, out)
                    for pc in cs:
                        if tuple(pc.value_table()) == sbox() and metrics(pc) < metrics(best): best = pc; polished = True
                except Exception as e:
                    log('polish error', repr(e))
                for g in sd.glob('*'):
                    if g.name not in ('kernel.log',): g.unlink()
            versions = [(best, polished)]
            if polished:
                try: uj2 = UF.ujunk(c=best)
                except Exception as e: uj2 = {'error': repr(e)}
                if uj2.get('U') != (uj or {}).get('U') or uj2.get('cover9') != (uj or {}).get('cover9'):
                    versions.append((nc, False))          # the polish changed U / the cover verdict: keep the rebuilt one too
            for cc, pol_ in versions:
                m2 = metrics(cc); fi2 = F.analyse_c(cc)
                try: uj2 = UF.ujunk(c=cc)
                except Exception as e: uj2 = {'error': repr(e)}
                mark = ('-NU' if uj2.get('U') and uj2.get('U') not in ureg else '') + ('-C9' if uj2.get('cover9') is True else '')
                name = 'aes-sbox-a%d-ad%d-g%d-gd%d-x1b-span-%s%s%s' % (m2 + (fi2['span'], '' if pol_ else '-raw', mark))
                bp = out / 'found' / (name + '.bfx'); bp.write_text(core.to_kernel(cc))
                r = aes_check.check(str(bp))
                if not r['ok']:
                    bp.rename(out / 'found' / (name + '.FAILED')); log('CHECK FAILED', name); continue
                cc.name = name
                (out / 'found' / (name + '.circ.txt')).write_text(core.write_ncff(cc, MODEL, comments=['agent X1b: new U (bfw sideways walk + U filter)' + (' + kernel polish' if pol_ else ', rebuilt XOR network, not polished')]))
                (out / 'found' / (name + '.json')).write_text(json.dumps({'method': 'x1b_camp: bfw sideways walk (new product span) + x1lib.materialise + U/junk filter (new U)' + (' + hub kernel polish %.0f s, caps A=%d AD=%d' % (pol, m[0], m[1]) if pol_ else ' (not polished)'),
                    'start': f, 'start_metrics': m0, 'params': rec['params'], 'adcap': cap, 'seed': seed, 'rebuilt': m, 'metrics': m2,
                    'span_dumped': fi['span'], 'span': fi2['span'], 'levels': fi2['levels'], 'span_L': fi2['span_L'],
                    'shared_with_refs': {str(Path(REFS[i]).name): F.inter(fi2, q) for i, q in enumerate(refs)},
                    'ujunk_rebuilt': uj, 'ujunk': uj2, 'U_new_vs_registry': uj2.get('U') not in ureg,
                    'aes_check_ok': True, 'new_point_vs_published': bool(r.get('new_point')),
                    'code_version': code_version(), 'time': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}, indent=1))
                rec['polished'].append([fi2['span'], m, m2, pol_, uj2.get('U'), uj2.get('cover9')])
                log('SAVED', name, 'rebuilt', m, 'levels', fi2['levels'], 'U', uj2.get('U'), 'cover9', uj2.get('cover9'), 'from', Path(f).name)
'''
s = s[:a] + new + s[b:]
open(p, "w").write(s)
print("patched")
