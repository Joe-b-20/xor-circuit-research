#!/usr/bin/env python3
"""Harvest unionsat2 LNS outputs: verify, copy into DATA/shared (as kernel-worker starts, with lineage)
and save every circuit that no reference tuple dominates or equals to DATA/found/ with the BRIEF sidecar.

    python3 lnsharvest.py DATA RUNDIR [RUNDIR ...]

RUNDIR = runs/usat2; each <name>.log there names the LNS start (lns_start line), seed (lns2seq log),
and each circuit in <name>-out/ is one accepted LNS step (file name ...-s<seed>-<step>.circ.txt).
"""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

PKG = Path('/home/joebachir20/xcr-boolflux/nonlinear/boolflux')
sys.path.insert(0, str(PKG.parent))
from boolflux import core, targets   # noqa: E402
from boolflux.hub.common import verify  # noqa: E402

M = core.Model.load('nist'); TAB = tuple(targets.aes_sbox())


def main():
    data = Path(sys.argv[1]); ref = set(tuple(x) for x in json.loads((data / 'reftuples.json').read_text()))
    shared = data / 'shared'; found = data / 'found'
    git = subprocess.run(['git', '-C', str(PKG.parents[1]), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    code_sha = hashlib.sha256((PKG / 'strategies/P1/unionsat2.py').read_bytes()).hexdigest()
    n_sh = n_found = 0
    for rd in map(Path, sys.argv[2:]):
        for lg in sorted(rd.glob('*.log')):
            name = lg.stem; od = rd / (name + '-out')
            if not od.exists(): continue
            start = None; info = None; el = {}
            for ln in lg.read_text().splitlines():
                try: r = json.loads(ln)
                except Exception: continue
                if 'lns_start' in r: start = r['lns_start']
                if 'templates' in r and info is None: info = r
                if 'step' in r and 'el' in r: el[r['step']] = r['el']
            for f in sorted(od.glob('*.circ.txt')):
                c = core.read_ncff(f.read_text()); m = c.metrics(M); t = (m['A'], m['AD'], m['G'], m['GD'])
                ok, _ = verify(c)
                if not ok or tuple(c.value_table()) != TAB: print('VERIFY FAIL', f); continue
                cid = hashlib.sha1(core.to_kernel(c).encode()).hexdigest()[:12]
                seed, step = f.name[:-len('.circ.txt')].split('-s')[-1].split('-')
                lin = {'root': start, 'root_sha256': hashlib.sha256(Path(start).read_bytes()).hexdigest() if start else None,
                       'chain': [{'op': 'unionsat2-LNS', 'run': name, 'seed': int(seed), 'step': int(step), 'file': str(f)}]}
                if not (shared / (cid + '.bfx')).exists():
                    (shared / (cid + '.bfx')).write_text(core.to_kernel(c))
                    (shared / (cid + '.json')).write_text(json.dumps({'id': cid, 'm': t, 'origin': 'lnsharvest', 'lineage': lin, 't': time.time()}))
                    n_sh += 1
                if any(all(a <= b for a, b in zip(q, t)) for q in ref): continue
                tgt = 'T01' if m['AD'] <= 4 else 'T03'
                nm = 'P1-%s-a%d-ad%d-g%d-gd%d-%s' % ((tgt,) + t + (cid,))
                p = found / (nm + '.circ.txt')
                if p.exists(): continue
                # at most 3 structures per tuple in found/ (plateau walks make thousands); the rest stay in shared/
                if len(list(found.glob('P1-%s-a%d-ad%d-g%d-gd%d-*.circ.txt' % ((tgt,) + t)))) >= 3: continue
                p.write_text(f.read_text())
                r = subprocess.run([sys.executable, str(PKG / 'campaigns' / 'aes_check.py'), str(p), '--json', str(found / (nm + '.check.json'))],
                                   capture_output=True, text=True)
                okl = [x for x in r.stdout.splitlines() if 'OK' in x][:1]
                RG, RGD = (132, 22) if tgt == 'T01' else (128, 20)
                cls = 'strict' if (t[2] <= RG and t[3] <= RGD and (t[2] < RG or t[3] < RGD)) else (
                    'tradeoff' if tgt == 'T01' and RGD < t[3] <= 24 and t[2] <= RG - 3 else 'other')
                side = {'target': tgt, 'class_vs_ref': cls, 'A': t[0], 'AD': t[1], 'G': t[2], 'GD': t[3],
                        'start': {'path': start, 'sha256': lin['root_sha256']},
                        'method': {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': info,
                                   'operator_chain': lin['chain']},
                        'command': ' '.join(info['argv']) if info and 'argv' in info else
                                   'python3 %s/unionsat2.py --lns %s --starts %s/starts_fam.json --extra %s/shared --D %d --cap-ad %d '
                                   '--seconds S --lns-sec 20 --seed %s (run %s; exact line in runs/usat2/lns2seq*.log)' %
                                   (PKG / 'strategies/P1', start, data, data, t[3] if info is None else info['D'], 5 if m['AD'] > 4 else 4, seed, name),
                        'pool_snapshot': str(od / 'pool.json') if (od / 'pool.json').exists() else
                                   'starts_fam.json rows + DATA/shared files whose json t precedes the run start (pool.json not written by this version)',
                        'seed': int(seed), 'elapsed_s': el.get(int(step)),
                        'code': {'git': git, 'unionsat2_sha256': code_sha},
                        'aes_check': okl[0] if okl else None, 'aes_check_rc': r.returncode,
                        'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
                (found / (nm + '.json')).write_text(json.dumps(side, indent=1, default=str))
                n_found += 1; print('FOUND', p, okl)
    print('shared +%d, found +%d' % (n_sh, n_found))


if __name__ == '__main__':
    main()
