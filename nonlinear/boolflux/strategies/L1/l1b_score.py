#!/usr/bin/env python3
"""L1b: score tonight's work (2026-11-15 study) beyond tonight.py.

    python3 l1b_score.py [--budget SECONDS] [--until HH:MM]     (run tonight.py first until 'pending 0')

Reads tonight.py's cache (every circuit file of the agents, verified with boolflux.core on 256 inputs)
and adds, all as counts [C] over the files / logs named:
  1. goal distances A-G: A = smallest A (and distinct AND spans at A28 / A29); B-G = min G + GD excess
     over the goal box among circuits inside the goal's A and AD caps (no 6/4 window), and the best
     key (G excess, GD excess) per goal, baseline (long archive at 01:30 + pin) vs now.
  2. front points of tonight against baseline + earlier tonight (time order), V = L1 value model.
  3. MOVE-level reductions (child vs its own start, not vs the front): A lowered, AD lowered at equal or
     lower A; from hub-style run records (target_metrics vs every candidate's metrics), T1 job logs,
     R2 fixed-target log, found/ sidecars (parent_metrics / source_metrics / src file name).
  4. AND spans: every tonight circuit with A <= 29, span(1, x, AND outputs) id vs the baseline spans.
  5. CPU-h: hub-style runs by operator (cpu_s), T1 by operator, allocated CPU-h per agent (CPU map x wall).
Snapshot directories (name contains 'snap') are skipped. Smoke-test directories are reported but flagged.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

HOME = Path.home()
sys.path.insert(0, str(HOME / 'xcr-boolflux' / 'nonlinear'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from boolflux import core                                                  # noqa: E402
from l1_lib import GOALS, tier, improvement, leq, fmt, table              # noqa: E402

STUDY = HOME / 'xs-campaigns' / '2026-11-15-study'
LONG = HOME / 'xs-campaigns' / '2026-11-14-hub' / 'long' / 'archive'
PIN = HOME / 'xcr-boolflux' / 'nonlinear' / 'nist' / 'aes-sbox'
AGENTS = ['T1', 'T2', 'T3', 'T4', 'X1', 'X2', 'R1', 'R2', 'H2', 'H3', 'H4']
CACHE = STUDY / 'L1' / 'tonight-cache.json'
SPANC = STUDY / 'L1' / 'l1b-span-cache.json'
STRUCT = STUDY / 'L1' / 'struct.json'
ONES = (1 << 256) - 1
# CPU map (BRIEF-COMMON / ADDENDUM-0135): agent -> (CPUs, start UTC hh:mm)
ALLOC = {'T1': (3, '01:35'), 'T2': (3, '01:35'), 'T3': (2, '01:35'), 'T4': (2, '01:35'), 'X1': (1, '01:35'),
         'X2': (1, '01:35'), 'H2': (1, '00:10'), 'H3': (2, '00:10'), 'H4': (1, '00:10'), 'R1': (2, '00:20'),
         'R2': (1, '00:20')}
TUP = re.compile(r'a(\d+)-ad(\d+)-g(\d+)(?:-gd(\d+))?')


def utc_ts(hhmm):
    import calendar
    return calendar.timegm(time.strptime('2026-11-15 ' + hhmm, '%Y-%m-%d %H:%M'))


def rref_id(tabs):
    rows = []
    for t in tabs:
        for p, r in rows:
            if (t >> p) & 1: t ^= r
        if t:
            p = t.bit_length() - 1
            rows = [(q, r ^ t if (r >> p) & 1 else r) for q, r in rows]
            rows.append((p, t)); rows.sort(key=lambda x: -x[0])
    return hashlib.sha1(b''.join(r.to_bytes(32, 'big') for p, r in rows)).hexdigest()[:8]


def span_of(c):
    tabs = c.tables(); n = c.n
    ands = [tabs[n + j] for j, g in enumerate(c.gates) if g[0] in core.NONLINEAR_OPS]
    return rref_id([ONES] + tabs[:n] + ands)


def load_circ(p):
    p = Path(p)
    return core.from_kernel(p.read_text(), p.stem) if p.suffix == '.bfx' else core.read_ncff(str(p))


def gdist(m, g):
    _, A, AD, G, GD = g
    if m[0] > A or m[1] > AD: return None
    return (max(0, m[2] - G) + max(0, m[3] - GD), max(0, m[2] - G), max(0, m[3] - GD))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--budget', type=float, default=70)
    a = ap.parse_args()
    t0 = time.time(); now = time.time()
    cache = json.loads(CACHE.read_text())
    long_ids = {f.stem for f in LONG.glob('*.bfx')}

    # ---------------- baseline -----------------------------------------------------------------
    from boolflux.hub.common import published
    base = [tuple(p) for p in published()]
    for f in LONG.glob('*.json'):
        if f.name == 'cells.json': continue
        r = json.loads(f.read_text()); base.append((r['A'], r['AD'], r['G'], r['GD']))
    base = sorted(set(base))

    # ---------------- tonight's distinct verified circuits (earliest file per id) ---------------
    by_id = {}
    for path, e in cache.items():
        if e.get('dup_long') or 'err' in e or not e.get('ok'): continue
        if e['id'] not in by_id or e['mtime'] < by_id[e['id']][1]['mtime']: by_id[e['id']] = (path, e)
    now_pts = base + [tuple(e['m']) for p, e in by_id.values()]

    out = []
    P = out.append
    P('# L1b score, %s UTC (tonight-cache: %d files, %d distinct verified new circuits)' % (
        time.strftime('%H:%M', time.gmtime(now)), len(cache), len(by_id)))

    # ---------------- 1. goal distances ---------------------------------------------------------
    P('\n## 1. Goal distances, baseline (long archive at stop + pin) vs now [C]')
    rows = []
    amin_b = min(p[0] for p in base); amin_n = min(p[0] for p in now_pts)
    rows.append(['A <=27', 'min A %d' % amin_b, 'min A %d' % amin_n, 'excess %d -> %d' % (amin_b - 27, amin_n - 27), ''])
    for g in GOALS:
        def best(S):
            ds = [(gdist(p, g), p) for p in S]
            ds = [(d, p) for d, p in ds if d is not None]
            if not ds: return None, []
            md = min(d[0] for d, p in ds)
            return md, sorted({p for d, p in ds if d[0] == md})[:4]
        db, pb = best(base); dn, pn = best(now_pts)
        newpts = sorted({tuple(e['m']) for p, e in by_id.values() if gdist(e['m'], g) is not None and gdist(e['m'], g)[0] <= (db if db is not None else 999)})
        rows.append(['%s %d/%d/%d/%d' % g, '%s at %s' % (db, ' '.join(fmt(p) for p in pb)), '%s at %s' % (dn, ' '.join(fmt(p) for p in pn)),
                     'MET' if dn == 0 else ('closer by %d' % (db - dn) if dn < db else 'unchanged'),
                     ' '.join(fmt(p) for p in newpts[:6]) or '-'])
    P(table(rows, ['goal', 'baseline: min(G excess + GD excess) at', 'now', 'change', 'tonight circuits at <= baseline distance']))
    # first circuits inside the (A, AD, GD) caps of a goal, ignoring G
    P('\nInside the A, AD and GD caps of the goal (G free), lowest G: baseline vs now')
    rows = []
    for g in GOALS:
        _, A, AD, G, GD = g
        fb = [p for p in base if p[0] <= A and p[1] <= AD and p[3] <= GD]
        fn = [tuple(e['m']) for p, e in by_id.values() if e['m'][0] <= A and e['m'][1] <= AD and e['m'][3] <= GD]
        bb = min(fb, key=lambda p: (p[2], p[3])) if fb else None
        bn = min(fn, key=lambda p: (p[2], p[3])) if fn else None
        tag = '' if not bn else (' (first)' if not bb else (' (lower G)' if bn[2] < bb[2] else (' (tie)' if bn[2] == bb[2] else ' (higher)')))
        rows.append([g[0], fmt(bb) if bb else 'none', (fmt(bn) + tag) if bn else 'none', len(fn)])
    P(table(rows, ['goal', 'baseline lowest G in (A, AD, GD) caps', 'tonight lowest G there', 'tonight circuits there']))

    # ---------------- 2. front points ------------------------------------------------------------
    P('\n## 2. Front points of tonight (not dominated by baseline or by an earlier circuit of tonight) [C]')
    pts = [p for p in base if not any(q != p and leq(q, p) for q in base)]
    rows = []; vtot = defaultdict(float); nfront = Counter()
    for i, (path, e) in sorted(by_id.items(), key=lambda kv: kv[1][1]['mtime']):
        m = tuple(e['m']); imp = improvement(m, pts)
        if imp:
            V = tier(m[0], m[1]) * imp[1]; vtot[e['agent']] += V; nfront[e['agent']] += 1
            rows.append([time.strftime('%H:%M', time.gmtime(e['mtime'])), e['agent'], fmt(m), imp[0], imp[2], '%.1f' % V,
                         path.replace(str(STUDY) + '/', '')])
            pts.append(m)
    P(table(rows, ['time', 'agent', 'A/AD/G/GD', 'kind', 'delta', 'V', 'file']) if rows else '(none)')

    # ---------------- 3. move-level reductions ---------------------------------------------------
    P('\n## 3. Move-level A / AD reductions (result vs its own start; not front gains) [C]')
    MV = defaultdict(lambda: defaultdict(float))     # (agent, source, op) -> stats
    examples = defaultdict(list)

    def credit(key, pm, ms, cpu=0.0, job=True):
        s = MV[key]
        if job: s['jobs'] += 1
        s['cpu'] += cpu
        ared = [m for m in ms if m[0] < pm[0]]
        adred = [m for m in ms if m[1] < pm[1] and m[0] <= pm[0]]
        if ared:
            s['jobs A-red'] += 1; s['min A'] = min(s.get('min A', 99), min(m[0] for m in ared))
            best = min(ared, key=lambda m: (m[0], m[1], m[2], m[3]))
            if best[0] <= 31: s['A-red to A<=31'] += 1
            examples[key].append('%s->%s' % (fmt(pm), fmt(best)))
        if adred:
            s['jobs AD-red'] += 1
            best = min(adred, key=lambda m: (m[1], m[0], m[2], m[3]))
            examples[key].append('%s->%s (AD)' % (fmt(pm), fmt(best)))
        nd = [m for m in ms if not any(leq(q, tuple(m)) for q in base)]
        if nd: s['jobs w/ result not dominated by baseline'] += 1

    hubdirs = []
    for ag in AGENTS:
        for dp, dn, fn in os.walk(STUDY / ag):
            dn[:] = [d for d in dn if d not in ('archive', 'jobs', 'funcbank', 'bin', '__pycache__', 'runs')]
            d = Path(dp)
            if (d / 'runs').is_dir() and (d / 'archive').is_dir() and 'snap' not in d.name:
                hubdirs.append((ag, d))
    for ag, d in hubdirs:
        src = str(d.relative_to(STUDY))
        smoke = any(w in src for w in ('smoke', 'test', 'dev', 'stuck', 'aborted', 'jobtest'))
        for rf in d.glob('runs/*.json'):
            try: r = json.loads(rf.read_text())
            except Exception: continue
            tm = r.get('target_metrics')
            ms = [tuple(o['metrics']) for o in r.get('outcome', []) if o.get('metrics')]
            key = (ag, src + (' [test]' if smoke else ''), r.get('operator'))
            if tm: credit(key, tuple(tm), [m for m in ms if m], r.get('cpu_s') or 0.0)
            else: MV[key]['jobs'] += 1; MV[key]['cpu'] += r.get('cpu_s') or 0.0
            MV[key]['admitted'] += r.get('admitted') or 0
            st = (r.get('op_info') or {}).get('stats') or {}
            if 'a_red' in st: MV[key]['raw a_red windows (op_info)'] += st['a_red']
    # T1 job logs
    for jf in sorted((STUDY / 'T1').glob('*/w*.jobs.jsonl')):
        for line in jf.read_text().splitlines():
            try: j = json.loads(line)
            except Exception: continue
            if 'op' not in j or 'pm' not in j: continue
            ms = [tuple(o[0]) for o in j.get('outs', []) if o and o[0]]
            credit(('T1', str(jf.parent.relative_to(STUDY)), j['op']), tuple(j['pm']), ms, j.get('cpu') or 0.0)
    # R2 fixed-target log
    ff = STUDY / 'R2' / 'fixed' / 'fixed.jsonl'
    if ff.exists():
        for line in ff.read_text().splitlines():
            try: j = json.loads(line)
            except Exception: continue
            key = ('R2', 'fixed (fixed-target aslack)', 'aslack')
            credit(key, tuple(j['tuple']), [tuple(j['best'])] if j.get('best') else [], j.get('secs') or 0.0)
            MV[key]['raw a_red windows (op_info)'] += (j.get('stats') or {}).get('a_red', 0)
    # found/ sidecars with a parent / source
    for ag in AGENTS:
        for sj in (STUDY / ag).rglob('*.json'):
            if 'found' not in sj.parts and 'found' not in str(sj.parent.name): continue
            if 'archive' in sj.parts or sj.name.endswith('.check.json'): continue
            try: s = json.loads(sj.read_text())
            except Exception: continue
            if not isinstance(s, dict): continue
            m = s.get('metrics') or [s.get(k) for k in ('A', 'AD', 'G', 'GD')]
            if isinstance(m, dict): m = [m.get(k) for k in ('A', 'AD', 'G', 'GD')]
            if not m or None in m[:2]:
                mm = TUP.search(sj.name); m = [int(x) if x else 99 for x in mm.groups()] if mm else None
            pm = s.get('parent_metrics') or s.get('source_metrics')
            if not pm and s.get('src'):
                mm = TUP.search(str(s['src'])); pm = [int(x) if x else 99 for x in mm.groups()] if mm else None
            if not pm or not m: continue
            meth = str(s.get('method') or s.get('operator') or s.get('how') or '?')[:40]
            credit((ag, 'found/ sidecars', meth), tuple(pm), [tuple(m)], 0.0)
    # files whose name carries the id of a long-archive circuit they were made from (R1 mc1-<id>-*, X1 *-from-<id>)
    longm = {}
    for f in LONG.glob('*.json'):
        if f.name == 'cells.json': continue
        r = json.loads(f.read_text()); longm[r['id']] = (r['A'], r['AD'], r['G'], r['GD'])
    HEX = re.compile(r'(?<![0-9a-f])([0-9a-f]{12})(?![0-9a-f])')
    for i, (path, e) in by_id.items():
        p = Path(path)
        ids = [h for h in HEX.findall(p.name) if h in longm and h != p.stem]
        if not ids: continue
        meth = re.split(r'[-_]', p.name)[0]
        credit((e['agent'], 'files named after a long-archive source', meth), longm[ids[0]], [tuple(e['m'])], 0.0)
    rows = []
    for key in sorted(MV, key=lambda k: (k[0], k[1], str(k[2]))):
        s = MV[key]
        rows.append([key[0], key[1], key[2], int(s['jobs']), '%.2f' % (s['cpu'] / 3600), int(s['admitted']),
                     int(s['jobs A-red']), int(s['A-red to A<=31']), s.get('min A', '-'), int(s['jobs AD-red']),
                     int(s['raw a_red windows (op_info)']) or '', int(s['jobs w/ result not dominated by baseline']),
                     '; '.join(sorted(set(examples[key]))[:4])])
    P(table(rows, ['agent', 'source', 'op / method', 'jobs', 'CPU-h', 'admitted', 'jobs A-red', 'to A<=31', 'min A reached',
                   'jobs AD-red', 'raw A-red windows', 'jobs non-dominated', 'examples (start -> result)']))
    # per operator totals over real (non-test) hub dirs + T1 + R2 fixed
    tot = defaultdict(lambda: defaultdict(float))
    for key, s in MV.items():
        if '[test]' in key[1] or key[1] == 'found/ sidecars': continue
        for k, v in s.items():
            if k == 'min A': tot[key[2]][k] = min(tot[key[2]].get(k, 99), v)
            else: tot[key[2]][k] += v
    P('\nPer operator, all non-test logged jobs together:')
    P(table([[op, int(s['jobs']), '%.2f' % (s['cpu'] / 3600), int(s['jobs A-red']), int(s['A-red to A<=31']), s.get('min A', '-'),
              int(s['jobs AD-red']), int(s['jobs w/ result not dominated by baseline'])]
             for op, s in sorted(tot.items(), key=lambda kv: -kv[1]['cpu'])],
            ['op', 'jobs', 'CPU-h', 'jobs A-red', 'to A<=31', 'min A', 'jobs AD-red', 'jobs non-dominated']))

    # ---------------- 4. AND spans at A <= 29 ----------------------------------------------------
    P('\n## 4. AND spans of A <= 29 circuits: baseline vs tonight [C]')
    st = json.loads(STRUCT.read_text()) if STRUCT.exists() else {}
    spc = json.loads(SPANC.read_text()) if SPANC.exists() else {}
    bspan = defaultdict(set)
    for f in LONG.glob('*.json'):
        if f.name == 'cells.json': continue
        i = f.stem
        r = json.loads(f.read_text())
        if r['A'] > 29: continue
        sid = st.get(i, {}).get('span') or spc.get('long:' + i)
        if sid is None and time.time() - t0 < a.budget:
            sid = span_of(core.from_kernel((LONG / (i + '.bfx')).read_text(), i)); spc['long:' + i] = sid
        if sid: bspan[(r['A'], r['AD'])].add(sid)
    for f in PIN.glob('*.circ.txt'):
        mm = TUP.search(f.name)
        if not mm or int(mm.group(1)) > 29: continue
        k = 'pin:' + f.name
        if k not in spc: spc[k] = span_of(core.read_ncff(str(f)))
        bspan[(int(mm.group(1)), int(mm.group(2)))].add(spc[k])
    allb = set().union(*bspan.values()) if bspan else set()
    tspan = defaultdict(lambda: defaultdict(list)); pend = 0
    for i, (path, e) in by_id.items():
        if e['m'][0] > 29: continue
        k = 'id:' + i
        if k not in spc:
            if time.time() - t0 > a.budget: pend += 1; continue
            try: spc[k] = span_of(load_circ(path))
            except Exception as ex: spc[k] = 'err'
        tspan[(e['m'][0], e['m'][1])][spc[k]].append((e['agent'], tuple(e['m']), path))
    SPANC.write_text(json.dumps(spc))
    rows = []
    for cl in sorted(set(bspan) | set(tspan)):
        new = {s: v for s, v in tspan[cl].items() if s not in allb and s != 'err'}
        byag = defaultdict(list)
        for s, v in sorted(new.items()):
            for ag in sorted({x[0] for x in v}):
                byag[ag].append((min(x[1][2:] for x in v if x[0] == ag), s, min((x for x in v if x[0] == ag), key=lambda x: x[1][2:])[2]))
        ex = []
        for ag, L in sorted(byag.items()):
            L.sort()
            ex.append('%s: %d spans, lowest G %s (%s)' % (ag, len(L), '%d@%d' % L[0][0], L[0][2].replace(str(STUDY) + '/', '')))
        rows.append(['%d/%d' % cl, len(bspan[cl]), len(tspan[cl]), len(new), '; '.join(ex)])
    P(table(rows, ['A/AD', 'baseline spans', 'tonight spans', 'tonight spans new (not in any baseline A<=29 span)', 'new spans by agent: count, lowest G@GD (file)']))
    if pend: P('PENDING span computations: %d (rerun)' % pend)

    # ---------------- 5. CPU and per-agent summary ----------------------------------------------
    P('\n## 5. Per agent: allocated CPU-h, front points, V (L1 value model) [C counts; CPU-h = CPU map x wall, an upper bound]')
    rows = []
    stop = min(now, utc_ts('06:45'))
    for ag in AGENTS:
        n, h = ALLOC[ag]; cpuh = n * max(0, stop - utc_ts(h)) / 3600
        nd = sum(1 for p, e in by_id.values() if e['agent'] == ag)
        rows.append([ag, n, h, '%.1f' % cpuh, nd, nfront[ag], '%.1f' % vtot[ag], '%.2f' % (vtot[ag] / cpuh) if cpuh else '-'])
    P(table(rows, ['agent', 'CPUs', 'since', 'CPU-h alloc', 'distinct new circuits', 'front points', 'V', 'V / CPU-h']))
    txt = '\n'.join(out)
    print(txt)
    (STUDY / 'L1' / ('l1b-score-%s.txt' % time.strftime('%H%M', time.gmtime(now)))).write_text(txt + '\n')


if __name__ == '__main__':
    main()
