#!/usr/bin/env python3
"""Long run (Track E): splice + polish generations vs polish-only control, on the 4-D (A, AD, G, GD) frontier.

    python3 memetic.py --arm splice|control --out DIR --hours H --cpus 7,8 --polish 120 FILE.list

Pool = the input circuits (pinned NIST forward circuits + team results) plus every admitted circuit.
Frontier = tuples of the pool not dominated by another pool tuple or a published tuple (equal counts as
dominated unless it is the same circuit).  Loop until the deadline:
  - splice arm only: for every pool member not yet spliced, splice2 transplants with every other pool
    member in both roles (all cut levels); admit results that are non-dominated (vs pool + published);
  - polish: up to len(cpus) concurrent gate-kernel jobs (bfx_new, lex cost,gd, caps = the circuit's own
    A, AD, GD), each on the frontier member with the fewest polishes; admit a result if non-dominated.
Every admission is written to DIR/admitted/ with its origin; DIR/log.jsonl records every event.
Both arms use the same code path except the splice step; same CPUs count, same polish seconds.
"""
import argparse, hashlib, json, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import core, load, metrics, correct, levels, MODEL, PKG   # noqa: E402
from splice2 import Front, splice   # noqa: E402
from erun import DEFAULTS, weights   # noqa: E402
sys.path.insert(0, str(PKG / 'campaigns'))
import aes_check   # noqa: E402


def leq(u, m): return all(a <= b for a, b in zip(u, m))


class Pool:
    def __init__(self, out, pub):
        self.out = out; self.pub = pub; self.items = {}   # hash -> dict
        (out / 'admitted').mkdir(parents=True, exist_ok=True)

    def dominated(self, m, h=None):
        if any(leq(u, m) for u in self.pub): return True
        return any(leq(it['m'], m) for hh, it in self.items.items() if hh != h)

    def add(self, c, origin, initial=False):
        k = core.to_kernel(c); h = hashlib.sha1(k.encode()).hexdigest()[:16]
        if h in self.items: return None
        m = tuple(metrics(c))
        if not initial and self.dominated(m): return None
        it = {'h': h, 'c': c, 'm': m, 't': c.tables(), 'l': levels(c), 'origin': origin, 'polished': 0,
              'spliced': False, 'initial': initial, 'time': time.time()}
        self.items[h] = it
        if not initial:
            (self.out / 'admitted' / (h + '.bfx')).write_text(k)
            (self.out / 'admitted' / (h + '.json')).write_text(json.dumps({'metrics': m, 'origin': origin}) + '\n')
        return it

    def frontier(self):
        """members not strictly dominated (ties kept, so published circuits are polish targets too)"""
        allm = set(self.pub) | {it['m'] for it in self.items.values()}
        return [it for it in self.items.values() if not any(u != it['m'] and leq(u, it['m']) for u in allm)]


def log(out, **kw):
    kw['ts'] = round(time.time(), 1)
    with open(out / 'log.jsonl', 'a') as f: f.write(json.dumps(kw) + '\n')


def splice_member(pool, it, out):
    """transplants of `it` with every other pool member in both roles"""
    adm = 0; tried = 0
    X = it
    others = [o for o in pool.items.values() if o is not it]
    for a, b in [(X, o) for o in others] + [(o, X) for o in others]:
        fr = {}
        for LY in range(1, b['m'][1]):
            for LX in sorted({min(LY, a['m'][1] - 1), a['m'][1] - 1}):
                if LX < 1: continue
                if LX not in fr: fr[LX] = Front(a['c'], a['t'], a['l'], LX)
                tried += 1
                c, nint = splice(fr[LX], b['c'], b['t'], b['l'], LY)
                if c is None: continue
                m = tuple(metrics(c))
                if pool.dominated(m): continue
                if not correct(c): raise SystemExit('BUG splice')
                r = pool.add(c, {'kind': 'splice', 'front': a['h'], 'back': b['h'], 'LX': LX, 'LY': LY, 'interface': nint})
                if r:
                    adm += 1; log(out, ev='admit', kind='splice', h=r['h'], m=m, front=a['h'], back=b['h'])
    it['spliced'] = True
    return tried, adm


def start_polish(it, out, seed, secs, cpu):
    d = out / 'polish'; d.mkdir(exist_ok=True)
    tag = '%s-p%d' % (it['h'], seed)
    sp = d / (tag + '.start.bfx'); sp.write_text(core.to_kernel(it['c']))
    bp = d / (tag + '.best.bfx'); cp = d / (tag + '.cfg')
    cfg = dict(DEFAULTS); cfg.update(weights('cost,gd'))
    for op, cc in MODEL.cost.items(): cfg['cost.%d' % op] = cc
    A, AD, G, GD = it['m']
    cfg.update({'cap.a': A, 'cap.ad': AD, 'cap.gd': GD, 'in': sp, 'out': bp, 'seed': seed, 'seconds': secs})
    cp.write_text(''.join('%s %s\n' % kv for kv in cfg.items()))
    lf = open(d / (tag + '.log'), 'w')
    p = subprocess.Popen(['taskset', '-c', str(cpu), str(HERE / 'bfx_new'), str(cp)], stdout=lf, stderr=subprocess.STDOUT)
    return {'p': p, 'lf': lf, 'it': it, 'bp': bp, 'cpu': cpu, 'tag': tag, 't0': time.time(), 'seed': seed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--arm', required=True, choices=['splice', 'control'])
    ap.add_argument('--out', required=True); ap.add_argument('--hours', type=float, required=True)
    ap.add_argument('--cpus', required=True); ap.add_argument('--polish', type=float, default=120)
    ap.add_argument('files')
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + args.hours * 3600
    pub = [u for (u, nm) in aes_check.published()]
    pool = Pool(out, pub)
    for f in Path(args.files).read_text().split():
        c = load(f)
        if correct(c): pool.add(c, {'kind': 'input', 'file': Path(f).name}, initial=True)
    log(out, ev='start', arm=args.arm, pool=len(pool.items), frontier=len(pool.frontier()))
    cpus = [int(x) for x in args.cpus.split(',')]
    free = list(cpus); running = []
    t_spl = 0.0
    while time.time() < deadline or running:
        # finished polishes
        for r in list(running):
            if r['p'].poll() is None: continue
            r['lf'].close(); running.remove(r); free.append(r['cpu'])
            try:
                c = core.from_kernel(r['bp'].read_text(), r['tag'])
            except Exception:
                continue
            if not correct(c): log(out, ev='wrong', tag=r['tag']); continue
            m = tuple(metrics(c))
            a = pool.add(c, {'kind': 'polish', 'from': r['it']['h'], 'seed': r['seed'], 'seconds': args.polish})
            log(out, ev='polished', h=r['it']['h'], m0=r['it']['m'], m=m, admitted=bool(a), wall=round(time.time() - r['t0'], 1))
        if time.time() >= deadline:
            time.sleep(1); continue
        # splice step
        if args.arm == 'splice':
            todo = [it for it in pool.items.values() if not it['spliced']]
            # new (admitted) members first, then the initial ones
            todo.sort(key=lambda it: (it['initial'], -it['time']))
            if todo and not (free and running == [] and False):
                t0 = time.time()
                tried, adm = splice_member(pool, todo[0], out)
                t_spl += time.time() - t0
                log(out, ev='spliced', h=todo[0]['h'], tried=tried, admitted=adm, secs=round(time.time() - t0, 1))
        # launch polishes
        while free:
            fr = [it for it in pool.frontier() if not any(r['it'] is it for r in running)]
            if not fr: break
            fr.sort(key=lambda it: (it['polished'], it['initial'], -it['time']))
            it = fr[0]; it['polished'] += 1
            running.append(start_polish(it, out, it['polished'], args.polish, free.pop(0)))
        if args.arm == 'control' or not [it for it in pool.items.values() if not it['spliced']]:
            time.sleep(1)
        # status
        if int(time.time()) % 300 < 2:
            fr = pool.frontier()
            (out / 'frontier.json').write_text(json.dumps(sorted([{'m': it['m'], 'h': it['h'], 'origin': it['origin'],
                                                                   'initial': it['initial']} for it in fr], key=lambda d: d['m'])))
    fr = pool.frontier()
    (out / 'frontier.json').write_text(json.dumps(sorted([{'m': it['m'], 'h': it['h'], 'origin': it['origin'],
                                                           'initial': it['initial']} for it in fr], key=lambda d: d['m'])))
    log(out, ev='end', pool=len(pool.items), frontier=len(fr), new=sum(1 for it in fr if not it['initial']), splice_secs=round(t_spl))


if __name__ == '__main__':
    main()
