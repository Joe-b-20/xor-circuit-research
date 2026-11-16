#!/usr/bin/env python3
"""M1 (phase 2, 2026-11-16): harvest the 2026-11-15-targets logs into two tables.

runs.jsonl   one row per kernel run (fdrive-family log.jsonl, kern.py kernel.log, P1 p1run jobs):
             agent, dir, category, mode, caps, start tuple, wall seconds, start epoch, final best,
             t of first improvement / first feasible, t of last improvement, repair_keep guess.
events.jsonl one row per verified campaign circuit (found/*.json sidecars) that, in time order, was
             not weakly dominated in (G, GD) by the baseline archive (+ pinned NIST) or by an earlier
             campaign circuit of the same target, inside the target's hard A/AD limits.
Read-only on all inputs. Output dir = argv[1].
"""
import json, os, re, sys, glob, time, calendar

ROOT = os.path.expanduser('~/xs-campaigns/2026-11-15-targets')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'phase2/M1/data')
os.makedirs(OUT, exist_ok=True)
TG = {t['id']: t for t in json.load(open(os.path.join(ROOT, 'TARGETS.json')))['targets']}
AGENTS = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7']
T1820 = calendar.timegm((2026, 11, 15, 18, 15, 0))


def category(agent, rel):
    r = rel.lower()
    if agent == 'P1':
        if r.startswith(('usat', 'iter')): return 'sat-lns'
        if r.startswith('conj'): return 'conj'
        if r.startswith('skres'): return 'kernel-skres'
        return 'kernel-p1run'
    if agent == 'P2':
        if 'cj' in r or r.startswith('conj'): return 'conj'
        if r.startswith(('t06rs', 'resyn', 't06bopt', 'ev-t06', 't06resyn', 'build', 'bopt')): return 'bottom-rebuild'
        if 'sp' in r.split('/')[0][3:6] or r.startswith(('t02sp', 't06sp')): return 'skeleton-pull'
        return 'kernel-plain'
    if agent == 'P3':
        if r.startswith(('trb19a',)): return 'kernel-plain'
        if r.startswith(('audit',)): return 'audit'
        if r.startswith(('q16a', 'qa', 'gadget', 'rank', 'pack', 'flip', 'ufix')): return 'other'
        return 'conj'          # cj*, c115*, c116*, pipe-conj*, rk* all descend from conjugate starts
    if agent == 'P4':
        if r.startswith('conj'): return 'conj'
        return 'other'
    if agent == 'P5':
        if r.startswith(('cp4', 'cp-', 'lin', 'ad4rep', 'conj3', 'ctest')): return 'conj'
        if r.startswith(('ad5', 'old')): return 'kernel-plain'
        return 'other'
    if agent == 'P6':
        if r.startswith(('c3-', 'conj', 't07conj', 'polish139', 'p137')): return 'conj'
        if r.startswith(('pull1', 'relax', 'seeds181', 'polish181', 'osc12', 'k1', 'k2', 'hy', 'rb', 'pb', 'fb',
                         'l3scan', 'scanpull')): return 'rebase'
        if r.startswith(('t07basin', 't07loop', 't07rb', 'fd1')): return 'kernel-plain'
        return 'other'
    if agent == 'P7':
        if r.startswith('cj') or r.startswith('conj'): return 'conj'
        if r.startswith(('pol', 'deep', 't09-bopt', 'bopt', 'bsel')): return 'bottom-rebuild'
        if r.startswith(('t10', 't09-mix', 't09-a44', 's1', 'test')): return 'kernel-plain'
        return 'other'
    return 'other'


def target_of(agent, A, AD, cap_gd, rel):
    if agent == 'P1': return 'T01' if AD == 4 and 'T03' not in rel and 't03' not in rel else 'T03'
    if agent == 'P2': return 'T02' if (A or 0) <= 28 else 'T06'
    if agent == 'P3': return 'T04'
    if agent in ('P4', 'P5'): return 'T05'
    if agent == 'P6': return 'T07' if (cap_gd or 99) >= 19 else 'T08'
    if agent == 'P7': return 'T10' if 't10' in rel.lower() else 'T09'


def fdrive_runs(agent):
    base = os.path.join(ROOT, agent, 'runs')
    for lp in glob.glob(base + '/**/log.jsonl', recursive=True):
        try:
            ev = [json.loads(l) for l in open(lp) if l.strip().startswith('{')]
        except Exception:
            continue
        st = next((e for e in ev if e.get('kind') == 'start'), None)
        if not st: continue
        d = os.path.dirname(lp); rel = os.path.relpath(d, base)
        tend = max((e.get('t', 0) for e in ev), default=0)
        mt = os.path.getmtime(lp)
        cap = st.get('cap')
        G0, GD0 = st.get('G'), st.get('GD')
        feas0 = GD0 is not None and cap is not None and GD0 <= cap
        bests = [e for e in ev if e.get('kind') == 'best']
        # improvement = a best with lower G inside the cap (or the first feasible one for a pull)
        first_imp = last_imp = None; final = (st.get('A'), st.get('AD'), G0, GD0)
        cur = G0 if feas0 else 10 ** 9
        for e in bests:
            if e.get('GD') is not None and cap is not None and e['GD'] > cap: continue
            if e['G'] < cur:
                cur = e['G']
                if first_imp is None: first_imp = e['t']
                last_imp = e['t']
                final = (e.get('A'), e.get('AD'), e['G'], e['GD'])
        par = [(e.get('G'), e.get('GD'), e.get('t')) for e in ev if e.get('kind') == 'pareto']
        bfx = st.get('bfx') or ''
        cmd = ''
        cp = os.path.join(d, 'command.txt')
        if os.path.exists(cp): cmd = open(cp).read()
        if not bfx:
            m = re.search(r'F_BFX=(\S+)', cmd); bfx = m.group(1) if m else ''
        m = re.search(r'--cap-a (\d+)', cmd); capa = int(m.group(1)) if m else st.get('A')
        m = re.search(r'--cap-ad (\d+)', cmd); capad = int(m.group(1)) if m else st.get('AD')
        t0 = mt - tend
        rk = ('593fa798f5' not in bfx) and t0 >= T1820 - 600
        yield dict(src='fdrive', agent=agent, dir=rel, cat=category(agent, rel), mode=st.get('mode'),
                   cap_gd=cap, cap_a=capa, cap_ad=capad, start=(st.get('A'), st.get('AD'), G0, GD0),
                   start_file=st.get('file'), feas0=feas0, wall=round(tend, 1), t0=round(t0),
                   first_imp=first_imp, last_imp=last_imp, final=final, pareto=par, bfx=os.path.basename(bfx),
                   rk=rk, seed=st.get('seed'), target=target_of(agent, capa, capad, cap, rel))


KL_START = re.compile(r'start cost \S+ G (\d+) A (\d+) GD (\d+) AD (\d+) feas (\d)')
KL_BEST = re.compile(r'best t ([\d.]+) .* G (\d+) A (\d+) GD (\d+) AD (\d+)')
KL_FIN = re.compile(r'final cost \S+ G (\d+) A (\d+) GD (\d+) AD (\d+) .*feas (\d).* seconds ([\d.]+)')


def kernlog_runs(agent):
    base = os.path.join(ROOT, agent, 'runs')
    for kp in glob.glob(base + '/**/kernel.log', recursive=True):
        d = os.path.dirname(kp); rel = os.path.relpath(d, base)
        # skip kernel logs inside fdrive run trees (counted there)
        p = d; inside = False
        while len(p) > len(base):
            if os.path.exists(os.path.join(p, 'log.jsonl')): inside = True; break
            p = os.path.dirname(p)
        if inside: continue
        cfg = {}
        cp = os.path.join(d, 'kernel.cfg')
        if os.path.exists(cp):
            for l in open(cp):
                s = l.split(None, 1)
                if len(s) == 2: cfg[s[0]] = s[1].strip()
        txt = open(kp).read().splitlines()
        st = next((KL_START.search(l) for l in txt if KL_START.search(l)), None)
        fin = next((KL_FIN.search(l) for l in txt if KL_FIN.search(l)), None)
        if not st: continue
        G0, A0, GD0, AD0, f0 = map(int, st.groups())
        capg = int(cfg.get('cap.gd', 999)); capa = int(cfg.get('cap.a', 999)); capad = int(cfg.get('cap.ad', 999))
        first_imp = last_imp = None; cur = G0 if f0 and GD0 <= capg else 10 ** 9
        final = (A0, AD0, G0, GD0)
        for l in txt:
            m = KL_BEST.search(l)
            if not m: continue
            t, G, A, GD, AD = float(m.group(1)), *map(int, m.groups()[1:])
            if GD > capg or A > capa or AD > capad: continue
            if G < cur:
                cur = G; first_imp = t if first_imp is None else first_imp; last_imp = t; final = (A, AD, G, GD)
        wall = float(fin.group(6)) if fin else float(cfg.get('seconds', 0))
        mt = os.path.getmtime(kp)
        yield dict(src='kernlog', agent=agent, dir=rel, cat=category(agent, rel), mode='kern',
                   cap_gd=capg, cap_a=capa, cap_ad=capad, start=(A0, AD0, G0, GD0), feas0=bool(f0 and GD0 <= capg),
                   wall=round(wall, 1), t0=round(mt - wall), first_imp=first_imp, last_imp=last_imp, final=final,
                   rk=cfg.get('repair_keep') == '1', seed=cfg.get('seed'),
                   target=target_of(agent, capa, capad, capg, rel))


def p1jobs():
    base = os.path.join(ROOT, 'P1', 'runs')
    for jp in glob.glob(base + '/*.jobs.jsonl'):
        name = os.path.basename(jp).split('.')[0]
        tgt = None
        for l in open(jp):
            try: e = json.loads(l)
            except Exception: continue
            if e.get('event') == 'start':
                a = e.get('argv', [])
                if '--target' in a: tgt = a[a.index('--target') + 1]
            if 'job' not in e: continue
            outs = e.get('outs') or []
            yield dict(src='p1job', agent='P1', dir=name + '/job%s' % e['job'], cat='kernel-p1run', mode=e.get('op'),
                       start=tuple(e.get('pm') or ()), wall=e.get('wall') or e.get('cpu') or 0,
                       imp=e.get('imp'), outs=[o[0] for o in outs if o], verdicts=[o[1] for o in outs if o],
                       target=tgt, t0=None)


def dominated(g, gd, pts):
    return any(G <= g and GD <= gd for G, GD in pts)


def nist_tuples():
    out = []
    for p in glob.glob(os.path.expanduser('~/xcr-boolflux/nonlinear/nist/aes-sbox/*.circ.txt')):
        m = re.search(r'-a(\d+)-ad(\d+)-g(\d+)-gd(\d+)', os.path.basename(p))
        if m: out.append(tuple(map(int, m.groups())))
    return out


def events():
    base = json.load(open(os.path.join(ROOT, 'L0/baseline/baseline.json')))['rows']
    bt = [tuple(r['tuple']) for r in base if r.get('ok') and r.get('tuple')] + nist_tuples()
    side = []
    for a in AGENTS:
        for sp in glob.glob(os.path.join(ROOT, a, 'found', '*.json')):
            try: s = json.load(open(sp))
            except Exception: continue
            if not isinstance(s, dict) or 'G' not in s: continue
            tgt = s.get('target')
            u = s.get('utc') or ''
            try: ep = calendar.timegm(time.strptime(u[:19], '%Y-%m-%dT%H:%M:%S'))
            except Exception: ep = os.path.getmtime(sp)
            side.append(dict(agent=a, file=os.path.basename(sp)[:-5], target=tgt, tuple=(s['A'], s['AD'], s['G'], s['GD']),
                             utc=u, ep=ep, method=json.dumps(s.get('method'))[:400], command=str(s.get('command'))[:600],
                             start=(s.get('start') or {}).get('path') if isinstance(s.get('start'), dict) else s.get('start'),
                             cert=s.get('path_certified'), elapsed=s.get('elapsed_s'), seed=s.get('seed'),
                             aes=str(s.get('aes_check'))[:300]))
    side.sort(key=lambda x: x['ep'])
    ev = []; ev4 = []
    for t, spec in TG.items():
        lim = [x for x in bt if x[0] <= spec['A'] and x[1] <= spec['AD']]
        pts = [(x[2], x[3]) for x in lim]
        lim4 = list(lim)
        # AND-depth sub-classes for T05 (AD 6/5/4): per-AD fronts
        sub = {}
        if t == 'T05':
            for ad in (6, 5, 4):
                sub[ad] = [(x[2], x[3]) for x in lim if x[1] <= ad]
        for s in side:
            A, AD, G, GD = s['tuple']
            # every campaign circuit inside the target's hard limits counts, whatever agent / label made it
            if A > spec['A'] or AD > spec['AD']: continue
            rec = None
            if not any(x[0] <= A and x[1] <= AD and x[2] <= G and x[3] <= GD for x in lim4):
                lim4.append((A, AD, G, GD))
                ev4.append(dict(s, ev_target=t))
            if not dominated(G, GD, pts):
                cls = 'frontier'
                if G <= spec['G'] and GD <= spec['GD'] and (G < spec['G'] or GD < spec['GD']): cls = 'strict'
                else:
                    for tr in spec.get('tradeoffs', []):
                        if tr['kind'] == 'gates_for_depth' and spec['GD'] < GD <= tr['GD_max'] and G <= spec['G'] - 3: cls = 'tradeoff'
                        if tr['kind'] == 'depth_for_gates' and GD <= tr['GD_max'] < spec['GD'] and spec['G'] < G <= spec['G'] + 8: cls = 'tradeoff'
                rec = dict(s, cls=cls, sub=None, ev_target=t)
                pts.append((G, GD))
            if t == 'T05':
                for ad in (6, 5, 4):
                    if AD <= ad and not dominated(G, GD, sub[ad]):
                        sub[ad].append((G, GD))
                        if rec is None: rec = dict(s, cls='ad%d-frontier' % ad, sub=ad, ev_target=t)
                        elif rec.get('sub') is None and rec['cls'] == 'frontier': rec['cls'] = 'ad%d-frontier' % ad; rec['sub'] = ad
            if rec: ev.append(rec)
    return ev, side, ev4


def main():
    runs = []
    for a in AGENTS:
        runs += list(fdrive_runs(a)); runs += list(kernlog_runs(a))
    runs += list(p1jobs())
    with open(os.path.join(OUT, 'runs.jsonl'), 'w') as f:
        for r in runs: f.write(json.dumps(r) + '\n')
    ev, side, ev4 = events()
    with open(os.path.join(OUT, 'events4.jsonl'), 'w') as f:
        for r in ev4: f.write(json.dumps(r) + '\n')
    with open(os.path.join(OUT, 'events.jsonl'), 'w') as f:
        for r in ev: f.write(json.dumps(r) + '\n')
    with open(os.path.join(OUT, 'sidecars.jsonl'), 'w') as f:
        for r in side: f.write(json.dumps(r) + '\n')
    print('runs', len(runs), 'events', len(ev), 'sidecars', len(side))


if __name__ == '__main__':
    main()
