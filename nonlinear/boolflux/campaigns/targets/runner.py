#!/usr/bin/env python3
"""Sequential overnight runner for the target operators (ops/<name>.py, BRIEF2.md operator contract).

    python3 nonlinear/boolflux/campaigns/targets/runner.py --plan PLAN.json [--root DIR] [--fresh]
                                                           [--check]  (validate the plan and exit)

Run it unattended as ONE systemd unit with all CPUs listed, e.g.
    ~/xs-campaigns/guard/xsrun P 0-19 night-runner ~/xs-campaigns/2026-11-16-night/runner.log -- \
        python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/campaigns/targets/runner.py --plan PLAN.json
Stop:   systemctl --user stop xs-P-night-runner   (running jobs then end by their own --seconds;
        `runner.py --plan PLAN --stop-jobs` stops them at once).
Restart after a stop/crash: the same command; it resumes from ROOT/STATE.json (done blocks are skipped,
the running block continues with its original end time, running jobs are re-adopted).  --fresh ignores it.

Plan (JSON; ~ is expanded; times UTC):
{
 "name": "night-2026-11-16",
 "root": "~/xs-campaigns/2026-11-16-night",      results: ROOT/<Txx>/found/, runs: ROOT/<Txx>/runs/<block>/
 "deadline_utc": "2026-11-16T13:30:00Z",         hard stop for everything (jobs are clipped to it)
 "cpus": "0-19",                                  CPUs the jobs may use (one busy process per CPU)
 "track": "P", "unit_prefix": "night",            job units xs-P-night-<block>-<n> (via guard/xsrun)
 "mem": "1500M",                                  XS_MEM per job (operators may override with "mem")
 "status_every_s": 120, "poll_s": 10, "min_job_s": 120,
 "ledger": true,                                  run `ledger.py run` after each block (or a command list)
 "carry": "next" | "flagged",                     leftover minutes go to the next block, or to the next
                                                  block with "takes_carry": true (pool otherwise kept)
 "max_per_start": 2,                              at most 2 running jobs per start (unless CPUs would idle)
 "blocks": [
  {"id": "T03a", "target": "T03", "minutes": 120, "takes_carry": false,
   "starts": ["ref", "ledger:frontier_G_GD:6", "found:4", "found:4:T01", "tuple:28/5/127/22[:N]",
              "file:/abs/x.circ.txt", "glob:/abs/*.circ.txt"],
            (tuple: files with exactly that tuple from ROOT found/, LEDGER.json, best-1400, hub archive;
             .bfx starts are converted to verified NCFF copies in ROOT/starts/)
   "starts_outside_ok": false,                    default: starts outside the target's A/AD are dropped
   "operators": [
     {"op": "conjpull", "cpus": 14, "job_seconds": 1200,
      "starts": [...],                            optional: this operator's own starts (else the block's)
      "flags": ["--schedule", "g:31:200,m:27:200,m:25:200"],
      "grid": [["--conj", "rank:1"], ["--conj", "rank:2"]],          alternatives; default [[]]
      "drop_start": {"within_gates": 1, "gd_slack": 2},
      "rechain": true, "rechain_gd_max": 99, "rechain_grid": [["--conj", "id", "--schedule", "m:+0:300,m:-1:300"]]},
     {"op": "satlns", "cpus": 6, "job_seconds": 900, "flags": [], "mem": "2G"}
   ],
   "rechain": {"max_starts": 16},                 new block-local (A, AD, G, GD) frontier points become starts
   "early_stop": {"classes": ["strict"], "grace_minutes": 15,       stop after a grace period once a point
                                                                    of these classes beyond the known front appears
                  "first_minutes": 45, "stall_minutes": 40}         no new point beyond the known front in the
                                                                    first 45 min, or 40 min after the last one
  }
 ]
}
Job queue per operator: rechained starts first (their rechain_grid, else grid), then rounds over
(start x grid point) with a fresh seed every job, so no CPU idles while the block runs.  A job's
--seconds is min(job_seconds, block end - now - 30 s, deadline - now - 60 s); no job starts with less
than min_job_s left.  "Beyond known" = a recorded point not weakly dominated in (A, AD, G, GD) by the
LEDGER.json fronts of the target, ROOT/<T>/found at block start, or an earlier beyond point of the block.  Results: every file a job writes (circuit + sidecar; the operator checked it) is
re-checked with aes_check, filtered to the target's hard limits, skipped if weakly dominated in
(A, AD, G, GD) by a file already in found/ (at most 2 structures per tuple), and copied with its sidecar
(plus a 'night' field: block, job, unit) to ROOT/<Txx>/found/.
STATUS.md: one line per block, then the frontier per target; STATE.json: machine state for restarts.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'ops'))
import common as CM                                         # noqa: E402

XSRUN = Path.home() / 'xs-campaigns/guard/xsrun'
LEDGER = HERE / 'ledger.py'
LEDGER_JSON = Path.home() / 'xs-campaigns/2026-11-15-targets/LEDGER.json'
BEST1400 = Path.home() / 'xs-campaigns/2026-11-15-study/best-1400'
HUBARCH = Path.home() / 'xs-campaigns/2026-11-14-hub/long/archive'


def now():
    return time.time()


def parse_utc(s):
    return dt.datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=dt.timezone.utc).timestamp()


def hm(ts):
    return time.strftime('%H:%M:%S', time.gmtime(ts))


def cpu_list(spec):
    if isinstance(spec, list): return [int(x) for x in spec]
    out = []
    for part in str(spec).split(','):
        if '-' in part:
            a, b = part.split('-'); out += list(range(int(a), int(b) + 1))
        elif part.strip():
            out.append(int(part))
    return out


def ex(p):
    return Path(os.path.expanduser(str(p)))


def env_for_units():
    e = dict(os.environ)
    uid = os.getuid()
    e.setdefault('XDG_RUNTIME_DIR', '/run/user/%d' % uid)
    e.setdefault('DBUS_SESSION_BUS_ADDRESS', 'unix:path=/run/user/%d/bus' % uid)
    return e


def active_units(track, prefix):
    try:
        r = subprocess.run(['systemctl', '--user', 'list-units', '--all', '--no-legend', '--plain',
                            'xs-%s-%s-*' % (track, prefix)], capture_output=True, text=True, timeout=60, env=env_for_units())
    except Exception:
        return None
    act = set()
    for ln in r.stdout.splitlines():
        p = ln.split()
        if len(p) >= 4 and p[2] in ('active', 'activating', 'deactivating', 'reloading'):
            act.add(p[0].replace('.service', ''))
    return act


def stop_units(units):
    if units:
        subprocess.run(['systemctl', '--user', 'stop'] + ['%s.service' % u for u in units],
                       capture_output=True, text=True, timeout=300, env=env_for_units())


class Runner:
    def __init__(self, plan_path, root=None, fresh=False):
        self.plan_path = Path(plan_path).resolve()
        self.plan = json.loads(self.plan_path.read_text())
        P = self.plan
        self.root = ex(root or P.get('root', '~/xs-campaigns/2026-11-16-night'))
        self.root.mkdir(parents=True, exist_ok=True)
        self.deadline = parse_utc(P.get('deadline_utc', '2026-11-16T13:30:00Z'))
        self.cpus = cpu_list(P.get('cpus', '0-19'))
        self.track = P.get('track', 'P'); self.prefix = P.get('unit_prefix', 'night')
        self.mem = P.get('mem', '1500M'); self.poll = float(P.get('poll_s', 10))
        self.status_every = float(P.get('status_every_s', 120)); self.min_job = float(P.get('min_job_s', 120))
        # a second plan on the same ROOT (same found/ folders) keeps its own state / status / event files
        self.statef = self.root / P.get('state_file', 'STATE.json'); self.statusf = self.root / P.get('status_file', 'STATUS.md')
        self.logf = open(self.root / P.get('events_file', 'runner.events.log'), 'a')
        self.found_idx = {}            # tid -> list of {'tuple', 'skey', 'path'}
        st = None
        if self.statef.exists() and not fresh:
            st = json.loads(self.statef.read_text())
            if st.get('plan_sha256') != CM.sha256(self.plan_path):
                self.log('STATE.json is from another plan version (sha differs); resuming by block id anyway')
        self.state = st or {'plan': str(self.plan_path), 'plan_sha256': CM.sha256(self.plan_path), 'name': P.get('name'),
                            'started_utc': CM.utc(), 'blocks': {}, 'carry_s': 0.0, 'job_counter': 0}
        self.state['plan_sha256'] = CM.sha256(self.plan_path)
        self.state.setdefault('restarts', []).append(CM.utc()) if st else None
        self.last_status = 0

    # ---- logging / state ------------------------------------------------------------------------
    def log(self, *x):
        self.logf.write('%s %s\n' % (CM.utc(), ' '.join(map(str, x)))); self.logf.flush()
        print(CM.utc(), *x, flush=True)

    def save(self):
        CM.write_json(self.statef, self.state)

    # ---- found/ index -----------------------------------------------------------------------------
    def found_dir(self, tid):
        d = self.root / tid / 'found'; d.mkdir(parents=True, exist_ok=True); return d

    def index(self, tid):
        if tid not in self.found_idx:
            L = []
            for j in sorted(self.found_dir(tid).glob('*.json')):
                try:
                    m = json.loads(j.read_text())
                    L.append({'tuple': tuple(m[k] for k in ('A', 'AD', 'G', 'GD')), 'skey': m.get('night', {}).get('skey'),
                              'path': str(j.with_name(j.name[:-5] + '.circ.txt')), 'class': m.get('class'),
                              'utc': m.get('utc')})
                except Exception:
                    pass
            self.found_idx[tid] = L
        return self.found_idx[tid]

    def harvest_file(self, tid, circ, side, blk, job):
        """Copy one operator result into ROOT/<tid>/found if it passes the filters; returns the record or None."""
        try:
            m = json.loads(side.read_text())
            t = tuple(m[k] for k in ('A', 'AD', 'G', 'GD'))
        except Exception as e:
            self.log('harvest: unreadable sidecar', side, repr(e)); return None
        if not CM.in_limits(t, tid):
            return None
        idx = self.index(tid)
        if any(all(a <= b for a, b in zip(r['tuple'], t)) and r['tuple'] != t for r in idx):
            return None
        same = [r for r in idx if r['tuple'] == t]
        if len(same) >= 2:
            return None
        c = CM.load(circ); skey = CM.structure_key(c)
        if any(r['skey'] == skey for r in same):
            return None
        ok, vt, line, full = CM.check(circ)
        if not ok or tuple(vt) != t:
            self.log('harvest: aes_check FAILED or tuple mismatch', circ, line); return None
        fd = self.found_dir(tid)
        dst = fd / circ.name
        if dst.exists():
            return None
        shutil.copyfile(circ, dst)
        m['night'] = {'runner': str(Path(__file__).resolve()), 'plan': str(self.plan_path), 'block': blk['id'],
                      'job': job['name'], 'unit': job['unit'], 'job_dir': job['dir'], 'source_file': str(circ),
                      'skey': skey, 'runner_aes_check': line, 'harvest_utc': CM.utc()}
        m['aes_check'] = line.replace(str(circ), str(dst)) if m.get('aes_check') else line
        m['class'] = CM.classify(t, tid)
        CM.write_json(fd / (dst.name[:-len('.circ.txt')] + '.json'), m)
        rec = {'tuple': t, 'skey': skey, 'path': str(dst), 'class': m['class'], 'utc': CM.utc()}
        idx.append(rec)
        return rec

    # ---- starts -----------------------------------------------------------------------------------
    def resolve_starts(self, blk):
        tid = blk['target']; out = []
        def add(p):
            p = ex(p)
            if p.exists(): out.append(p.resolve())
            else: self.log('start not found:', p)
        led = None
        for rule in blk.get('starts', ['ref']):
            parts = str(rule).split(':')
            if rule == 'ref':
                add(CM.reference_file(tid))
            elif parts[0] == 'file':
                add(':'.join(parts[1:]))
            elif parts[0] == 'glob':
                import glob
                for g in sorted(glob.glob(os.path.expanduser(':'.join(parts[1:])))): add(g)
            elif parts[0] == 'ledger':
                key = parts[1]; n = int(parts[2]); src = parts[3] if len(parts) > 3 else tid
                if led is None:
                    try: led = json.loads(LEDGER_JSON.read_text())
                    except Exception as e: self.log('LEDGER.json unreadable', repr(e)); led = {}
                rows = ((led.get('targets') or {}).get(src) or {}).get(key) or []
                rows = sorted(rows, key=lambda r: (r['tuple'][2], r['tuple'][3]))
                for r in rows[:n]: add(r['file'])
            elif parts[0] == 'tuple':
                # tuple:A/AD/G/GD[:N]: up to N (default 1) files with exactly this tuple, from ROOT found/,
                # LEDGER.json (every target's lists + campaign results) and the best-1400 archive names
                want = tuple(int(x) for x in parts[1].split('/')); n = int(parts[2]) if len(parts) > 2 else 1
                if led is None:
                    try: led = json.loads(LEDGER_JSON.read_text())
                    except Exception as e: self.log('LEDGER.json unreadable', repr(e)); led = {}
                cand = []
                for t2 in [b['target'] for b in self.plan['blocks']]:
                    cand += [r['path'] for r in self.index(t2) if tuple(r['tuple']) == want]
                for tg in (led.get('targets') or {}).values():
                    for v in tg.values():
                        if isinstance(v, list):
                            cand += [r['file'] for r in v if isinstance(r, dict) and tuple(r.get('tuple') or ()) == want]
                cand += [r['path'] for r in led.get('campaign_results') or [] if tuple(r.get('tuple') or ()) == want and r.get('ok')]
                import glob
                cand += sorted(glob.glob(str(BEST1400 / ('aes-sbox-a%d-ad%d-g%d-gd%d-*' % want))))
                if not hasattr(self, '_hub'):                 # hub long archive records (id.json + id.bfx)
                    self._hub = {}
                    for j in sorted(HUBARCH.glob('*.json')):
                        try:
                            r = json.loads(j.read_text())
                            self._hub.setdefault(tuple(int(r[k]) for k in ('A', 'AD', 'G', 'GD')), []).append(str(j.with_suffix('.bfx')))
                        except Exception:
                            pass
                cand += [p for p in self._hub.get(want, []) if Path(p).exists()]
                got = []
                for p in cand:
                    if p not in got: got.append(p)
                if not got: self.log('no file for start rule', rule)
                for p in got[:n]: add(p)
            elif parts[0] == 'found':
                n = int(parts[1]); src = parts[2] if len(parts) > 2 else tid
                fr = CM.pareto2([r['tuple'] for r in self.index(src)])
                byt = {}
                for r in self.index(src): byt.setdefault(r['tuple'], r['path'])
                for t in fr[:n]: add(byt[t])
            else:
                add(rule)
        seen = set(); res = []
        for p in out:
            h = CM.sha256(p)
            if h in seen: continue
            seen.add(h)
            try:
                t = CM.metrics(CM.load(p))
            except Exception as e:
                self.log('start unreadable', p, repr(e)); continue
            if not blk.get('starts_outside_ok') and not CM.in_limits(t, tid):
                self.log('start outside %s hard limits, dropped:' % tid, p, t); continue
            if p.suffix == '.bfx':
                # every operator gets NCFF: verified copy ROOT/starts/<id>-a..-ad..-g..-gd...circ.txt (+ .src.json)
                sd = self.root / 'starts'; sd.mkdir(exist_ok=True)
                q = sd / ('%s-a%d-ad%d-g%d-gd%d.circ.txt' % ((p.stem,) + tuple(t)))
                if not q.exists():
                    c = CM.load(p)
                    CM.atomic_write(q, CM.core.write_ncff(c, CM.MODEL, comments=['converted from %s (sha256 %s) by runner.py' % (p, h)]))
                    ok, vt, line, full = CM.check(q)
                    if not ok or tuple(vt) != tuple(t):
                        self.log('start conversion FAILED', p, line); q.unlink(); continue
                    CM.write_json(q.with_name(q.name[:-len('.circ.txt')] + '.src.json'),
                                  {'source': str(p), 'source_sha256': h, 'tuple': list(t), 'aes_check': line, 'utc': CM.utc()})
                p = q
            res.append(str(p))
        return res

    def known_front(self, tid):
        """(A, AD, G, GD) tuples known at block start: LEDGER.json fronts ((G, GD), (A, AD, G, GD), strict,
        tradeoff; the ledger baseline + every scanned campaign/night file) + ROOT found."""
        pts = [r['tuple'] for r in self.index(tid)]
        try:
            led = json.loads(LEDGER_JSON.read_text())['targets'].get(tid) or {}
            for key in ('frontier_G_GD', 'frontier_A_AD_G_GD', 'strict_frontier', 'tradeoff_frontier'):
                pts += [tuple(r['tuple']) for r in led.get(key) or []]
        except Exception as e:
            self.log('LEDGER.json unreadable for known front', repr(e))
        return [list(t) for t in pts]

    # ---- block ------------------------------------------------------------------------------------
    def block_state(self, blk):
        S = self.state['blocks'].setdefault(blk['id'], {'state': 'pending'})
        return S

    def make_ops(self, blk, S):
        """Per operator: CPU ids, queue state (pending explicit jobs, round, cursor)."""
        cp = list(self.cpus); ops = []
        for i, o in enumerate(blk['operators']):
            n = int(o.get('cpus', 1))
            mine, cp = cp[:n], cp[n:]
            q = S.setdefault('queues', {}).setdefault(str(i), {'pending': [], 'round': 0, 'cursor': 0})
            ops.append({'i': i, 'spec': o, 'cpus': mine, 'q': q})
        return ops

    def tup(self, path):
        c = getattr(self, '_tups', None)
        if c is None: c = self._tups = {}
        if path not in c:
            try: c[path] = CM.metrics(CM.load(path))
            except Exception: c[path] = None
        return c[path]

    def room_ok(self, o, t):
        """operator options gd_room / g_any_gd: GD <= gd_room, or any GD when G <= g_any_gd"""
        if t is None or 'gd_room' not in o: return True
        return t[3] <= int(o['gd_room']) or ('g_any_gd' in o and t[2] <= int(o['g_any_gd']))

    def expand(self, o, flags, path):
        """{GD}, {GD+1}, {GD-1} ... in an operator's flags -> the start's GD (+/- n).  With gd_room, a grid
        point whose substituted value exceeds gd_room is skipped (None) unless start G <= g_any_gd."""
        import re
        out = []; t = None
        for x in list(o.get('flags', [])) + list(flags):
            x = str(x)
            m = re.fullmatch(r'\{GD([+-]\d+)?\}', x)
            if m:
                t = t or self.tup(path)
                if t is None: return None
                v = t[3] + int(m.group(1) or 0)
                if 'gd_room' in o and v > int(o['gd_room']) and not ('g_any_gd' in o and t[2] <= int(o['g_any_gd'])):
                    return None
                x = str(v)
            out.append(x)
        return out                      # full flag list: operator flags + grid point, substituted

    def next_job(self, blk, S, op):
        q = op['q']; o = op['spec']
        dropped0 = set(S.get('dropped', {}).get(str(op['i']), []))
        while q['pending']:
            j = q['pending'].pop(0)
            if j['start'] not in dropped0: return j
        starts = S['starts']                      # list of {'path', 'kind': initial|rechain, 'ops': [i..] or None}
        combos = []
        dropped = set(S.get('dropped', {}).get(str(op['i']), []))
        seen = set()
        for si, s in enumerate(starts):
            if s['path'] in dropped: continue
            if s.get('ops') is not None and op['i'] not in s['ops']: continue
            grid = o.get('rechain_grid') if (s['kind'] == 'rechain' and o.get('rechain_grid')) else o.get('grid') or [[]]
            for g in grid:
                fl = self.expand(o, g, s['path'])
                if fl is None or json.dumps([s['path'], fl]) in seen: continue
                seen.add(json.dumps([s['path'], fl]))
                combos.append((si, 0, [fl]))
        if not combos: return None
        # at most max_per_start running jobs per start (block-wide); if every start is at the limit, take the
        # next combo anyway (no idle CPU)
        lim = int(blk.get('max_per_start', self.plan.get('max_per_start', 0)) or 0)
        busy = {}; inflight = set()
        for J in S.get('running', []):
            busy[J['start']] = busy.get(J['start'], 0) + 1
            inflight.add(json.dumps([J['start'], J['flags'], J['opi']]))
        key = lambda c: json.dumps([starts[c[0]]['path'], list(c[2][c[1]])])
        taken = set(q.setdefault('taken', []))
        for _ in range(2):
            todo = [c for c in combos if key(c) not in taken]
            if todo: break
            q['round'] += 1; q['taken'] = []; taken = set()       # every combo ran this round: next round
        ok = [c for c in todo if not lim or busy.get(starts[c[0]]['path'], 0) < lim]
        if not ok:          # every start at its limit: no idle CPU, but avoid an identical job in flight
            ok = [c for c in todo if json.dumps([starts[c[0]]['path'], list(c[2][c[1]]), op['i']]) not in inflight] or todo
        si, gi, grid = ok[0]
        q['taken'].append(key(ok[0]))
        return {'start': starts[si]['path'], 'flags': list(grid[gi]), 'round': q['round'], 'full': True}

    def launch(self, blk, S, op, cpu, job, secs):
        tid = blk['target']; o = op['spec']
        self.state['job_counter'] += 1
        n = self.state['job_counter']
        seed = int(hashlib.sha1(('%s-%s-%d' % (self.plan.get('name'), blk['id'], n)).encode()).hexdigest()[:6], 16) % 900000 + 1000
        name = '%s-%d' % (o['op'], n)
        rd = self.root / tid / 'runs' / blk['id']; rd.mkdir(parents=True, exist_ok=True)
        jd = rd / name
        unit = '%s-%s-%d' % (self.prefix, ''.join(ch if ch.isalnum() else '_' for ch in blk['id']), n)
        opfile = ex(o['file']) if o.get('file') else HERE / 'ops' / ('%s.py' % o['op'])
        cmd = [sys.executable, str(opfile), '--in', job['start'], '--target', tid, '--seed', str(seed),
               '--seconds', str(int(secs)), '--out', str(jd)] + \
              ([str(x) for x in job['flags']] if job.get('full') else [str(x) for x in o.get('flags', [])] + [str(x) for x in job['flags']])
        env = env_for_units(); env['XS_MEM'] = str(o.get('mem', self.mem))
        r = subprocess.run([str(XSRUN), self.track, str(cpu), unit, str(rd / (name + '.out')), '--'] + cmd,
                           capture_output=True, text=True, env=env, cwd=str(CM.REPO), timeout=120)
        J = {'name': name, 'unit': 'xs-%s-%s' % (self.track, unit), 'cpu': cpu, 'op': o['op'], 'opi': op['i'],
             'dir': str(jd), 'start': job['start'], 'flags': job['flags'], 'seed': seed, 'seconds': int(secs),
             't_launch': now(), 'cmd': cmd, 'seen': [], 'round': job.get('round')}
        if job.get('round') == 0:
            st = S.setdefault('start_stats', {}).setdefault('%d|%s' % (op['i'], job['start']), {'launched': 0, 'done': 0, 'hit': False})
            st['launched'] += 1
        if r.returncode != 0:
            self.log('LAUNCH FAILED', name, r.stdout[-300:], r.stderr[-300:])
            J['failed'] = True; J['t_end'] = now()
            S.setdefault('failed', []).append(J); S['n_failed'] = S.get('n_failed', 0) + 1
            return None
        S['running'].append(J); self.save()
        self.log('launch', blk['id'], name, 'cpu', cpu, 'seed', seed, 'secs', int(secs), Path(job['start']).name, ' '.join(map(str, job['flags'])))
        return J

    def harvest_job(self, blk, S, J):
        jd = Path(J['dir'])
        if not jd.is_dir(): return []
        new = []
        for side in sorted(jd.glob('*.json')):
            if side.name == 'result.json' or side.name in J['seen']: continue
            circ = side.with_name(side.name[:-5] + '.circ.txt')
            if not circ.exists(): continue
            J['seen'].append(side.name)
            rec = self.harvest_file(blk['target'], circ, side, blk, J)
            if rec: new.append(rec)
        for rec in new:
            self.on_new_point(blk, S, rec, J)
        return new

    def on_new_point(self, blk, S, rec, J):
        t = rec['tuple']; tid = blk['target']
        S['n_new'] = S.get('n_new', 0) + 1
        loc = [tuple(x) for x in S.setdefault('local_points', [])]
        local_front = not any(all(a <= b for a, b in zip(p, t)) for p in loc)     # block-local (A, AD, G, GD)
        S['local_points'].append(list(t))
        if local_front:
            S['t_last_front'] = S['t_last_front_pt'] = now()
        known = [tuple(x) for x in S.get('known', [])]
        beyond = not any(all(a <= b for a, b in zip(k, t)) for k in known)     # (A, AD, G, GD) weak dominance
        cls = rec['class']
        self.log('NEW', tid, '/'.join(map(str, t)), cls, 'beyond-known' if beyond else '', 'local-front' if local_front else '', Path(rec['path']).name)
        if beyond:
            S.setdefault('beyond', []).append({'tuple': list(t), 'class': cls, 'file': rec['path'], 'utc': CM.utc()})
            S['known'].append(list(t))            # "another" new point must beat this one too
            S['t_last_beyond'] = now()
        es = blk.get('early_stop') or {}
        classes = es.get('classes', [])
        if beyond and any(cls == c or cls.startswith(c + ':') for c in classes) and not S.get('stop_at'):
            S['stop_at'] = now() + 60 * float(es.get('grace_minutes', 15))
            self.log('EARLY-STOP armed', blk['id'], 'by', '/'.join(map(str, t)), cls, 'stop at', hm(S['stop_at']))
        rc = blk.get('rechain', {'max_starts': 16})
        if rc is not False and local_front and rc.get('on', True):
            def wants(o):      # operator options "rechain_gd_max" and gd_room / g_any_gd (e.g. SAT walks at a cap)
                return o.get('rechain', True) and t[3] <= int(o.get('rechain_gd_max', 999)) and self.room_ok(o, t)
            rops = [op['i'] for op in self.cur_ops if wants(op['spec'])]
            S['starts'].append({'path': rec['path'], 'kind': 'rechain', 'tuple': list(t), 'ops': rops})
            mx = int(rc.get('max_starts', 16))
            base = [s for s in S['starts'] if s['kind'] != 'rechain']
            rech = [s for s in S['starts'] if s['kind'] == 'rechain']
            # keep the newest rechained starts that are still block-local frontier points
            pts = [tuple(s['tuple']) for s in rech]
            rech = [s for s in rech if not any(all(a <= b for a, b in zip(p, s['tuple'])) and tuple(p) != tuple(s['tuple']) for p in pts)]
            S['starts'] = base + rech[-max(1, mx - len(base)):] if len(base) < mx else base + rech[-1:]
            for op in self.cur_ops:
                if wants(op['spec']):
                    grid = op['spec'].get('rechain_grid') or op['spec'].get('grid') or [[]]
                    for g in reversed(grid):
                        fl = self.expand(op['spec'], g, rec['path'])
                        if fl is not None:
                            op['q']['pending'].insert(0, {'start': rec['path'], 'flags': fl, 'round': -1, 'full': True})
                    # newest first; keep at most 3 x CPUs pending rechain jobs per operator
                    del op['q']['pending'][max(len(grid), 3 * len(op['cpus'])):]

    def start_stat(self, blk, S, J):
        """M1 rule (operator option "drop_start": {"within_gates": 1, "gd_slack": 2}): once all round-0 jobs
        of an initial start (one per grid point) are done, drop the start for this operator if no job
        recorded a point with G <= start G + within_gates at GD <= start GD + gd_slack."""
        if J.get('round') != 0: return
        o = self.plan['blocks'][[b['id'] for b in self.plan['blocks']].index(blk['id'])]['operators'][J['opi']]
        rule = o.get('drop_start')
        key = '%d|%s' % (J['opi'], J['start'])
        st = (S.get('start_stats') or {}).get(key)
        if st is None: return
        st['done'] += 1
        try:
            s = CM.metrics(CM.load(J['start']))
        except Exception:
            return
        w = int((rule or {}).get('within_gates', 1)); gs = int((rule or {}).get('gd_slack', 2))
        for p in (J.get('result') or {}).get('pareto') or []:
            if p[2] <= s[2] + w and p[3] <= s[3] + gs: st['hit'] = True
        ngrid = len(o.get('grid') or [[]])
        if rule and st['done'] >= ngrid and st['launched'] >= ngrid and not st['hit']:
            S.setdefault('dropped', {}).setdefault(str(J['opi']), []).append(J['start'])
            self.log('DROP start for op', J['opi'], Path(J['start']).name, 'no round-0 result within', w, 'gates (GD slack', gs, ')')

    def run_block(self, bi, blk):
        S = self.block_state(blk)
        if S['state'] in ('done', 'early-stopped', 'skipped'):
            return
        tid = blk['target']
        if S['state'] == 'pending':
            takes = blk.get('takes_carry', self.plan.get('carry', 'next') == 'next')
            S.update({'state': 'running', 't_start': now(), 'utc_start': CM.utc(), 'running': [], 'done_jobs': 0,
                      'planned_s': 60 * float(blk['minutes']),
                      'carry_in_s': self.state.get('carry_s', 0.0) if takes else 0.0})
            S['t_end'] = min(now() + S['planned_s'] + S['carry_in_s'], self.deadline - 60)
            # block starts go to the operators without their own "starts"; an operator's own starts only to it
            gen = [i for i, o in enumerate(blk['operators']) if 'starts' not in o]
            S['starts'] = []
            if gen:
                S['starts'] += [{'path': p, 'kind': 'initial', 'ops': gen} for p in self.resolve_starts(blk)]
            for i, o in enumerate(blk['operators']):
                if 'starts' in o:
                    sub = dict(blk); sub['starts'] = o['starts']
                    S['starts'] += [{'path': p, 'kind': 'initial', 'ops': [i]} for p in self.resolve_starts(sub)]
            S['known'] = self.known_front(tid)
            S['t_last_front'] = now()
            if takes: self.state['carry_s'] = 0.0
            self.log('BLOCK START', blk['id'], tid, 'until', hm(S['t_end']), 'starts', len(S['starts']))
            if not S['starts']:
                self.log('BLOCK has no legal start; skipped', blk['id'])
                S['state'] = 'skipped'; S['t_stop'] = now()
                self.state['carry_s'] = self.state.get('carry_s', 0.0) + max(0.0, S['t_end'] - now()); self.save(); return
        else:
            self.log('BLOCK RESUME', blk['id'], tid, 'until', hm(S['t_end']), 'running jobs', len(S['running']))
        ops = self.make_ops(blk, S); self.cur_ops = ops
        self.save()
        # block option "pre_cmds": commands run once at block start (and on resume), e.g. the satlns span-index
        # rebuild; "refresh_every_s": re-run them in the background that often while the block runs
        for c in blk.get('pre_cmds', []):
            t0 = now()
            try:
                with open(self.root / 'pre-cmds.log', 'a') as lf:
                    lf.write('\n== %s block %s: %s\n' % (CM.utc(), blk['id'], ' '.join(map(str, c)))); lf.flush()
                    rc = subprocess.run([os.path.expanduser(str(x)) for x in c], stdout=lf, stderr=subprocess.STDOUT,
                                        cwd=str(CM.REPO), timeout=600).returncode
                self.log('pre_cmd exit', rc, '%.0f s' % (now() - t0), ' '.join(map(str, c))[:120])
            except Exception as e:
                self.log('pre_cmd failed', repr(e))
        last_refresh = now(); refresh = None
        busy_cpu = {J['cpu'] for J in S['running']}
        stopping = False
        while True:
            t = now()
            end = S['t_end']
            if S.get('stop_at'): end = min(end, S['stop_at'])
            es = blk.get('early_stop') or {}
            # stall rule: no new point (beyond the known frontier, default; or block-local frontier with
            # "stall_on": "local") within first_minutes of the block start, then stall_minutes after the last one
            on_local = es.get('stall_on') == 'local'
            last = S.get('t_last_front_pt') if on_local else S.get('t_last_beyond')
            win = None
            if last is None and float(es.get('first_minutes', 0)) > 0:
                last, win = S['t_start'], float(es['first_minutes'])
            elif float(es.get('stall_minutes', 0)) > 0:
                last, win = (last if last is not None else S['t_start']), float(es['stall_minutes'])
            if win is not None and t - last > 60 * win:
                if not S.get('stall_fired'):
                    S['stall_fired'] = True; self.log('STALL stop', blk['id'], 'no new point for %.0f min' % win); S['stop_at'] = t
                end = min(end, S['stop_at'])
            act = active_units(self.track, self.prefix)
            # finished jobs
            for J in list(S['running']):
                if act is None:        # systemctl failed this poll: judge by time (contract: exit within T + 60 s)
                    alive = t - J['t_launch'] < J['seconds'] + 90
                else:
                    alive = J['unit'] in act or (t - J['t_launch'] < 8)
                self.harvest_job(blk, S, J)
                if not alive:
                    S['running'].remove(J); busy_cpu.discard(J['cpu'])
                    J['t_end'] = t; S['done_jobs'] += 1
                    try:
                        r = json.loads((Path(J['dir']) / 'result.json').read_text())
                        J['result'] = {'status': r.get('status'), 'pareto': [p['tuple'] for p in r.get('pareto_G_GD', [])],
                                       'wall_s': r.get('wall_s')}
                    except Exception:
                        J['result'] = {'status': 'no result.json'}
                    self.log('done', J['name'], J['result'])
                    if J['result'].get('status') == 'not-applicable':     # operator says this start cannot work
                        S.setdefault('dropped', {}).setdefault(str(J['opi']), []).append(J['start'])
                        self.log('DROP start for op', J['opi'], Path(J['start']).name, '(operator: not-applicable)')
                    elif (J['result'].get('wall_s') or 0) < 5 and J['result'].get('status') in ('error', 'no result.json'):
                        S['fast_fail'] = S.get('fast_fail', 0) + 1
                        key = '%d|%s' % (J['opi'], J['start'])
                        ff = S.setdefault('fast_fail_by', {}); ff[key] = ff.get(key, 0) + 1
                        if ff[key] >= 3:                    # three instant failures: stop feeding this start
                            S.setdefault('dropped', {}).setdefault(str(J['opi']), []).append(J['start'])
                            self.log('DROP start for op', J['opi'], Path(J['start']).name, '(3 instant failures)')
                    self.start_stat(blk, S, J)
                    rule = blk['operators'][J['opi']].get('drop_if_result')
                    if rule:            # e.g. {"key": "satlns.pool.n_pooled", "lt": 30} (M4: small span pools)
                        try:
                            v = json.loads((Path(J['dir']) / 'result.json').read_text())
                            for k in rule['key'].split('.'): v = v[k]
                            if float(v) < float(rule['lt']):
                                S.setdefault('dropped', {}).setdefault(str(J['opi']), []).append(J['start'])
                                self.log('DROP start for op', J['opi'], Path(J['start']).name, '(%s = %s < %s)' % (rule['key'], v, rule['lt']))
                        except Exception:
                            pass
                    S.setdefault('finished', []).append({k: J[k] for k in ('name', 'cpu', 'op', 'start', 'flags', 'seed', 'seconds', 'result')})
                    S['finished'] = S['finished'][-400:]
                elif t - J['t_launch'] > J['seconds'] + 150:
                    self.log('overdue, stopping', J['name']); stop_units([J['unit'].replace('.service', '')])
            if t >= end or t >= self.deadline - 60:
                if not stopping:
                    stopping = True
                    self.log('BLOCK END reached', blk['id'], 'stopping', len(S['running']), 'jobs')
                    stop_units([J['unit'] for J in S['running']])
                if not S['running']:
                    break
            elif not stopping:
                # fill idle CPUs
                for op in ops:
                    for cpu in op['cpus']:
                        if cpu in busy_cpu: continue
                        rem = min(end - t - 30, self.deadline - 60 - t - 30)
                        if rem < self.min_job: continue
                        job = self.next_job(blk, S, op)
                        if job is None: continue
                        secs = min(float(op['spec'].get('job_seconds', 900)), rem)
                        if self.launch(blk, S, op, cpu, job, secs): busy_cpu.add(cpu)
            if blk.get('refresh_every_s') and blk.get('pre_cmds') and t - last_refresh > float(blk['refresh_every_s']) \
                    and (refresh is None or refresh.poll() is not None):
                lf = open(self.root / 'pre-cmds.log', 'a')
                lf.write('\n== %s refresh block %s\n' % (CM.utc(), blk['id'])); lf.flush()
                c = blk['pre_cmds'][0]
                refresh = subprocess.Popen([os.path.expanduser(str(x)) for x in c], stdout=lf, stderr=subprocess.STDOUT, cwd=str(CM.REPO))
                last_refresh = t
            if t - self.last_status > self.status_every:
                self.status(); self.save(); self.last_status = t
            if stopping and t > end + 300:
                self.log('jobs did not stop in 300 s; leaving', [J['unit'] for J in S['running']]); break
            time.sleep(self.poll)
        S['t_stop'] = now(); S['utc_stop'] = CM.utc()
        S['state'] = 'early-stopped' if (S.get('stop_at') and S['t_stop'] < S['t_end'] - 5) else 'done'
        S['leftover_s'] = max(0.0, S['t_end'] - S['t_stop']) if S['state'] == 'early-stopped' else 0.0
        self.state['carry_s'] = self.state.get('carry_s', 0.0) + S['leftover_s']
        self.log('BLOCK', S['state'], blk['id'], 'jobs', S['done_jobs'], 'new', S.get('n_new', 0), 'carry %.0f s' % self.state['carry_s'])
        self.save(); self.status()
        self.ledger(blk)
        self.status(); self.save()

    def ledger(self, blk, wait=False):
        """`ledger.py run` after a block, in the background (the next block starts at once); if the previous
        ledger run is still going, this one is skipped (the next block's run covers it).  wait=True (end
        of the plan): start one if none runs, then wait for it (at most 30 min)."""
        L = self.plan.get('ledger', True)
        if not L: return
        cmd = L if isinstance(L, list) else [sys.executable, str(LEDGER), 'run']
        p = getattr(self, 'ledger_proc', None)
        if p is not None and p.poll() is None:
            self.log('ledger still running from the previous block; not started again after', blk['id'])
        else:
            if p is not None:
                self.log('previous ledger run exit', p.returncode)
            lf = open(self.root / 'ledger-runs.log', 'a')
            lf.write('\n== %s after block %s: %s\n' % (CM.utc(), blk['id'], ' '.join(cmd))); lf.flush()
            try:
                self.ledger_proc = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT, cwd=str(CM.REPO))
                self.block_state(blk)['ledger'] = {'started_utc': CM.utc(), 'pid': self.ledger_proc.pid}
                self.log('ledger run started after', blk['id'], 'pid', self.ledger_proc.pid)
            except Exception as e:
                self.log('ledger run failed to start', repr(e)); return
        if wait:
            try:
                rc = self.ledger_proc.wait(timeout=1800)
                self.log('final ledger run exit', rc)
            except Exception as e:
                self.log('final ledger run not finished in 30 min', repr(e))

    # ---- status -----------------------------------------------------------------------------------
    def status(self):
        L = ['# Overnight runner status', '',
             'Updated %s. Plan `%s` (%s). Root `%s`. Deadline %s UTC (hard stop). Runner pid %d. '
             'Leftover pool %.1f min (carry mode %s).' % (
                 CM.utc(), self.plan_path, self.plan.get('name'), self.root, hm(self.deadline), os.getpid(),
                 self.state.get('carry_s', 0.0) / 60, self.plan.get('carry', 'next')), '',
             '| block | target | state | planned min | start | end/stop | jobs done | running | new files | beyond known (class) |',
             '|---|---|---|---|---|---|---|---|---|---|']
        tids = []
        for blk in self.plan['blocks']:
            S = self.state['blocks'].get(blk['id'], {'state': 'pending'})
            if blk['target'] not in tids: tids.append(blk['target'])
            bey = S.get('beyond') or []
            bt = ', '.join('%s (%s)' % ('/'.join(map(str, b['tuple'])), b['class']) for b in sorted(bey, key=lambda b: (b['tuple'][2], b['tuple'][3]))[:4])
            L.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
                blk['id'], blk['target'], S['state'], blk['minutes'],
                S.get('utc_start', '-')[11:19] if S.get('utc_start') else '-',
                hm(S['t_stop']) if S.get('t_stop') else (hm(min(S['t_end'], S.get('stop_at') or 1e18)) if S.get('t_end') else '-'),
                S.get('done_jobs', 0), len(S.get('running', [])), S.get('n_new', 0), bt or '-'))
        L += ['', '## Frontier per target (ROOT/<T>/found, (G, GD) Pareto within the hard limits; class by TARGETS.json)', '']
        for tid in tids:
            idx = self.index(tid)
            fr = CM.pareto2([r['tuple'] for r in idx])
            ref = CM.limits(tid)
            L.append('- %s (ref %d/%d/%d/%d): %d files; frontier %s' % (
                tid, ref['A'], ref['AD'], ref['G'], ref['GD'], len(idx),
                ', '.join('%d@%d%s' % (t[2], t[3], {'strict': ' strict'}.get(CM.classify(t, tid), ' tradeoff' if CM.classify(t, tid).startswith('tradeoff') else '')) for t in fr) or '-'))
        CM.atomic_write(self.statusf, '\n'.join(L) + '\n')

    def stop_all_jobs(self):
        units = []
        for S in self.state['blocks'].values():
            units += [J['unit'] for J in S.get('running', [])]
        stop_units(units); self.log('stopped', units)

    def check_plan(self):
        P = self.plan; errs = []
        ids = set()
        for blk in P['blocks']:
            if blk['id'] in ids: errs.append('duplicate block id %s' % blk['id'])
            ids.add(blk['id'])
            try: CM.target(blk['target'])
            except KeyError as e: errs.append(str(e))
            n = sum(int(o.get('cpus', 1)) for o in blk['operators'])
            if n > len(self.cpus): errs.append('block %s asks %d CPUs, plan has %d' % (blk['id'], n, len(self.cpus)))
            for o in blk['operators']:
                f = ex(o['file']) if o.get('file') else HERE / 'ops' / ('%s.py' % o['op'])
                if not f.exists(): errs.append('block %s: operator file missing %s' % (blk['id'], f))
        tot = sum(float(b['minutes']) for b in P['blocks'])
        return errs, tot

    def run(self):
        errs, tot = self.check_plan()
        if errs:
            for e in errs: self.log('PLAN ERROR', e)
            raise SystemExit(2)
        self.log('runner start', self.plan_path, 'blocks', len(self.plan['blocks']), 'planned %.0f min' % tot,
                 'deadline', hm(self.deadline), 'cpus', self.cpus)
        self.state['runner_pid'] = os.getpid(); self.save()
        for bi, blk in enumerate(self.plan['blocks']):
            if now() >= self.deadline - 60 - self.min_job:
                S = self.block_state(blk)
                if S['state'] == 'pending':
                    S['state'] = 'skipped'; S['note'] = 'deadline'
                continue
            self.run_block(bi, blk)
        last = self.plan['blocks'][-1]
        p = getattr(self, 'ledger_proc', None)
        if p is not None and p.poll() is None:
            self.log('waiting for the running ledger, then one final ledger run')
            try: p.wait(timeout=1800)
            except Exception: pass
        self.ledger(dict(last, id='final'), wait=True)
        self.state['finished_utc'] = CM.utc(); self.save(); self.status()
        self.log('runner finished')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plan', required=True); ap.add_argument('--root', default=None)
    ap.add_argument('--fresh', action='store_true'); ap.add_argument('--check', action='store_true')
    ap.add_argument('--stop-jobs', action='store_true')
    a = ap.parse_args()
    R = Runner(a.plan, a.root, a.fresh)
    if a.check:
        errs, tot = R.check_plan()
        print('plan', a.plan, 'blocks', len(R.plan['blocks']), 'minutes %.0f' % tot, 'errors', errs or 'none')
        for blk in R.plan['blocks']:
            print(' ', blk['id'], blk['target'], blk['minutes'], 'min, block starts:',
                  [Path(p).name for p in R.resolve_starts(blk)] if any('starts' not in o for o in blk['operators']) else '-')
            for i, o in enumerate(blk['operators']):
                st = R.resolve_starts(dict(blk, starts=o['starts'])) if 'starts' in o else None
                print('    op %d %s cpus %s grid %d%s' % (i, o['op'], o.get('cpus', 1), len(o.get('grid') or [[]]),
                                                     ', own starts: %s' % [Path(p).name for p in st] if st is not None else ''))
        return 1 if errs else 0
    if a.stop_jobs:
        R.stop_all_jobs(); return 0
    R.run()
    return 0


if __name__ == '__main__':
    sys.exit(main())
